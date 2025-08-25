# src/ai_assistant/executor.py
import sys
import json
import shutil
import subprocess
from pathlib import Path
import argparse
from importlib import resources
import jsonschema

import structlog
from .logging_config import setup_logging 

class ExecutionError(Exception):
    """Custom exception for execution failures."""
    pass

class ManifestExecutor:
    """
    Executes a plan defined in a manifest.json file from an AI-generated output package.
    This class is designed to be simple, robust, and deterministic.
    """
    def __init__(self, package_dir: Path, dry_run: bool = False):
        self.logger = structlog.get_logger(self.__class__.__name__)
        self.package_dir = package_dir.resolve()
        self.workspace_dir = self.package_dir / "workspace"
        self.manifest_path = self.package_dir / "manifest.json"
        self.project_root = Path.cwd()
        self.dry_run = dry_run

        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Manifest file not found at {self.manifest_path}")

    def _load_manifest(self) -> dict:
        """Loads and validates the manifest file."""
        
        self.logger.info("Loading and validating manifest", path=self.manifest_path)
        try:
            # 1. Load the manifest instance from disk
            with open(self.manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)

            # 2. Load the canonical schema from package data
            schema_path_traversable = resources.files('ai_assistant').joinpath('internal_data/schemas/output_package_manifest_schema.json')
            with schema_path_traversable.open('r', encoding='utf-8') as f:
                schema = json.load(f)

            # 3. Perform validation
            jsonschema.validate(instance=manifest, schema=schema)
            self.logger.info("Schema validation passed.")

        except json.JSONDecodeError as e:
            raise ValueError(f"Manifest is not valid JSON. Error: {e}")
        except jsonschema.ValidationError as e:
            raise ValueError(f"Manifest failed schema validation. Reason: {e.message}")
        except FileNotFoundError:
            raise FileNotFoundError("Could not locate the canonical manifest schema within the package. The package may be corrupted.")
        
        return manifest

    def execute_plan(self):
        """Executes all actions in the manifest sequentially."""
        manifest = self._load_manifest()
        actions = manifest.get("actions", [])
        
        self.logger.info("Manifest loaded.", action_count=len(actions))
        if self.dry_run:
            self.logger.warning("DRY RUN MODE: No changes will be applied.")

        for i, action in enumerate(actions):
            action_type = action.get("type")

            self.logger.info(
                "Executing action", 
                step=f"{i+1}/{len(actions)}", 
                type=action_type
            )
            
            try:
                handler = getattr(self, f"_handle_{action_type}", None)
                if not handler:
                    raise ExecutionError(f"No handler found for action type '{action_type}'.")
                
                handler(action)
            except Exception as e:
                print(f"❌ HALT: Action {i+1} failed. Reason: {e}", file=sys.stderr)
                print("🛑 Execution stopped. The system state may be partially modified.", file=sys.stderr)
                sys.exit(1)
        
        self.logger.info("Plan executed successfully.")

    def _run_command(self, command: list[str], cwd: Path = None):
        """Helper to run a subprocess command."""
        cwd = cwd or self.project_root
        command_str = ' '.join(command)
        self.logger.info(
            "Running command", 
            command=command_str, 
            cwd=str(cwd),
            )
        if self.dry_run:
            self.logger.info(
                "Skipped command due to dry-run mode", 
                command=command_str,
                )
            return

        result = subprocess.run(command, capture_output=True, text=True, cwd=cwd)
        if result.returncode != 0:
            error_details = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            raise ExecutionError(f"Command failed with exit code {result.returncode}.\n{error_details}")
        self.logger.debug(
            "Command succeeded", 
            command=command_str,
            )

    def _handle_create_branch(self, action: dict):
        branch_name = action.get("branch_name")
        if not branch_name:
            raise ValueError("Action 'create_branch' is missing 'branch_name'.")
        self.logger.info("Creating new branch", branch_name=branch_name)
        self._run_command(["git", "checkout", "-b", branch_name])

    def _handle_apply_file_change(self, action: dict):
        source_rel = action.get("source")
        target_rel = action.get("target")
        if not source_rel or not target_rel:
            raise ValueError("Action 'apply_file_change' is missing 'source' or 'target'.")

        source_path = (self.package_dir / source_rel).resolve()
        target_path = (self.project_root / target_rel).resolve()

        self.logger.debug(
            "Applying file change", 
            source=source_path, 
            target=target_path,
            )

        if not source_path.exists():
            raise FileNotFoundError(f"Source file in workspace not found: {source_path}")

        if self.dry_run:
            self.logger.info(
                "Skipped copying file due to dry-run mode", 
                source=source_path,
                )
            return
        
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
        self.logger.info(
            "Copied file to target destination", 
            target=target_path,
            )

    def _handle_create_directory(self, action: dict):
        path_rel = action.get("path")
        if not path_rel:
            raise ValueError("Action 'create_directory' is missing 'path'.")
        
        target_path = (self.project_root / path_rel).resolve()
        self.logger.info("Creating directory", path=str(target_path))

        if self.dry_run:
            self.logger.info("Skipped directory creation due to dry-run mode", path=str(target_path))
            return
        
        target_path.mkdir(parents=True, exist_ok=True)
        self.logger.info("Created directory successfully.", path=str(target_path))

    def _handle_move_file(self, action: dict):
        source_rel = action.get("source")
        dest_rel = action.get("destination")
        if not source_rel or not dest_rel:
            raise ValueError("Action 'move_file' is missing 'source' or 'destination'.")

        source_path = (self.project_root / source_rel).resolve()
        dest_path = (self.project_root / dest_rel).resolve()

        print(f"   - Source: {source_path}")
        print(f"   - Destination: {dest_path}")

        if not source_path.exists():
            raise FileNotFoundError(f"Source path for move operation not found: {source_path}")

        if self.dry_run:
            print("     (Skipped move operation due to dry-run mode)")
            return
        
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_path), str(dest_path))
        print(f"   - ✅ Moved item successfully.")

    def _handle_git_add(self, action: dict):
        path = action.get("path")
        if not path:
            raise ValueError("Action 'git_add' is missing 'path'.")
        print(f"   - Path to add: {path}")
        self._run_command(["git", "add", path])

    def _handle_git_commit(self, action: dict):
        message = action.get("message")
        if not message:
            raise ValueError("Action 'git_commit' is missing 'message'.")
        print(f"   - Commit message: \"{message[:72]}...\"")
        self._run_command(["git", "commit", "-m", message])

    def _handle_git_push(self, action: dict):
        # Get current branch name to push safely
        result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True)
        current_branch = result.stdout.strip()
        print(f"   - Pushing current branch '{current_branch}' to origin.")
        self._run_command(["git", "push", "--set-upstream", "origin", current_branch])

def main():
    setup_logging()
    logger = structlog.get_logger()
    
    parser = argparse.ArgumentParser(description="Execute an AI-generated plan from an output package.")
    parser.add_argument("package_dir", type=str, help="Path to the AI output package directory.")
    parser.add_argument("--confirm", action="store_true", help="Confirm and apply the changes. Without this flag, a dry-run is performed.")
    args = parser.parse_args()
    
    is_dry_run = not args.confirm
    
    try:
        executor = ManifestExecutor(Path(args.package_dir), dry_run=is_dry_run)
        executor.execute_plan()
    except (FileNotFoundError, ValueError, ExecutionError) as e:
        logger.error("EXECUTION FAILED", error=str(e))
        sys.exit(1) 
    except Exception as e:
        logger.error("An unexpected error occurred", error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()