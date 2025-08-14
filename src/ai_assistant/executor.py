# src/ai_assistant/executor.py
import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
import argparse

class ExecutionError(Exception):
    """Custom exception for execution failures."""
    pass

class ManifestExecutor:
    """
    Executes a plan defined in a manifest.json file from an AI-generated output package.
    This class is designed to be simple, robust, and deterministic.
    """
    def __init__(self, package_dir: Path, dry_run: bool = False):
        self.package_dir = package_dir.resolve()
        self.workspace_dir = self.package_dir / "workspace"
        self.manifest_path = self.package_dir / "manifest.json"
        self.project_root = Path.cwd()
        self.dry_run = dry_run

        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Manifest file not found at {self.manifest_path}")

    def _load_manifest(self) -> dict:
        """Loads and validates the manifest file."""
        print(f"ℹ️  Loading manifest from: {self.manifest_path}")
        with open(self.manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        if "actions" not in manifest or not isinstance(manifest["actions"], list):
            raise ValueError("Manifest is invalid: Missing or malformed 'actions' list.")
        
        return manifest

    def execute_plan(self):
        """Executes all actions in the manifest sequentially."""
        manifest = self._load_manifest()
        actions = manifest.get("actions", [])
        
        print(f"✅ Manifest loaded. Found {len(actions)} actions to execute.")
        if self.dry_run:
            print("\nDRY RUN MODE: No changes will be applied to the file system or Git repository.\n")

        for i, action in enumerate(actions):
            action_type = action.get("type")
            print("-" * 50)
            print(f"▶️  Executing Action {i+1}/{len(actions)}: {action_type}")
            
            try:
                handler = getattr(self, f"_handle_{action_type}", None)
                if not handler:
                    raise ExecutionError(f"No handler found for action type '{action_type}'.")
                
                handler(action)
            except Exception as e:
                print(f"❌ HALT: Action {i+1} failed. Reason: {e}", file=sys.stderr)
                print("🛑 Execution stopped. The system state may be partially modified.", file=sys.stderr)
                sys.exit(1)
        
        print("-" * 50)
        print("✅ Plan executed successfully.")

    def _run_command(self, command: list[str], cwd: Path = None):
        """Helper to run a subprocess command."""
        cwd = cwd or self.project_root
        command_str = ' '.join(command)
        print(f"   - Running command: `{command_str}` in `{cwd}`")
        if self.dry_run:
            print("     (Skipped due to dry-run mode)")
            return

        result = subprocess.run(command, capture_output=True, text=True, cwd=cwd)
        if result.returncode != 0:
            error_details = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            raise ExecutionError(f"Command failed with exit code {result.returncode}.\n{error_details}")
        print("   - ✅ Success.")

    def _handle_create_branch(self, action: dict):
        branch_name = action.get("branch_name")
        if not branch_name:
            raise ValueError("Action 'create_branch' is missing 'branch_name'.")
        print(f"   - Branch to create: {branch_name}")
        self._run_command(["git", "checkout", "-b", branch_name])

    def _handle_apply_file_change(self, action: dict):
        source_rel = action.get("source")
        target_rel = action.get("target")
        if not source_rel or not target_rel:
            raise ValueError("Action 'apply_file_change' is missing 'source' or 'target'.")

        source_path = (self.package_dir / source_rel).resolve()
        target_path = (self.project_root / target_rel).resolve()

        print(f"   - Source: {source_path}")
        print(f"   - Target: {target_path}")

        if not source_path.exists():
            raise FileNotFoundError(f"Source file in workspace not found: {source_path}")

        if self.dry_run:
            print(f"     (Skipped copying file due to dry-run mode)")
            return
        
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
        print(f"   - ✅ Copied file to target destination.")

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
    parser = argparse.ArgumentParser(description="Execute an AI-generated plan from an output package.")
    parser.add_argument("package_dir", type=str, help="Path to the AI output package directory.")
    parser.add_argument("--confirm", action="store_true", help="Confirm and apply the changes. Without this flag, a dry-run is performed.")
    
    args = parser.parse_args()
    
    is_dry_run = not args.confirm
    
    try:
        executor = ManifestExecutor(Path(args.package_dir), dry_run=is_dry_run)
        executor.execute_plan()
    except (FileNotFoundError, ValueError, ExecutionError) as e:
        print(f"\n❌ EXECUTION FAILED: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()