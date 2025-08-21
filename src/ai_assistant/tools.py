# ai_assistant/tools.py
import asyncio
import os
import re
from pathlib import Path
import shutil
import subprocess
from typing import List, Dict, Any, Tuple

from ._security_guards import SHELL_COMMAND_BLOCKLIST
from .response_handler import ResponseHandler

# --- The base Tool class MUST be defined first and be async ---
class Tool:
    name: str = "Base Tool"
    description: str = "This is a base tool."
    is_risky: bool = False
    async def __call__(self, *args, **kwargs) -> Tuple[bool, str]: raise NotImplementedError
    def to_dict(self) -> Dict[str, Any]: return {"name": self.name, "description": self.description, "is_risky": self.is_risky}

# --- Synchronous Helper Functions (Used by multiple tools) ---

def _run_git_command(command_parts: List[str]) -> Tuple[bool, str]:
    try:
        result = subprocess.run(command_parts, capture_output=True, text=True, check=True, timeout=60)
        command_str = " ".join(command_parts)
        output = f"Success: `{command_str}`"
        if result.stdout: output += f"\nSTDOUT: {result.stdout.strip()}"
        if result.stderr: output += f"\nSTDERR: {result.stderr.strip()}"
        return (True, output)
    except subprocess.CalledProcessError as e:
        command_str = " ".join(command_parts)
        error_message = f"Error running `{command_str}`:\nSTDOUT: {e.stdout.strip()}\nSTDERR: {e.stderr.strip()}"
        return (False, error_message)

# --- Simplifying the AI's job to a single, clear instruction---
class CreateServiceFromTemplateTool(Tool):
    name = "create_service_from_template"
    description = (
        "The mandatory tool for creating new service configurations (like Dockerfile, pyproject.toml) "
        "by using an existing service as a template. Use this instead of manual file operations. "
        "Usage: create_service_from_template(template_service_name: str, new_service_name: str, new_service_path: str)"
    )
    is_risky = True

    async def __call__(self, template_service_name: str, new_service_name: str, new_service_path: str) -> Tuple[bool, str]:
        template_path = Path(f"src/services/{template_service_name}")
        new_path = Path(new_service_path)
        
        if not template_path.is_dir():
            return (False, f"Error: Template service directory not found at '{template_path}'")

        files_to_template = ["Dockerfile", "pyproject.toml"]
        log_messages = []

        try:
            # Create the new directory first
            new_path.mkdir(parents=True, exist_ok=True)
            log_messages.append(f"Created directory '{new_path}'.")

            for filename in files_to_template:
                template_file = template_path / filename
                if not template_file.exists():
                    log_messages.append(f"Warning: Template file '{template_file}' not found, skipping.")
                    continue

                # Read, adapt, and write
                content = template_file.read_text(encoding='utf-8')
                adapted_content = content.replace(template_service_name, new_service_name)
                
                new_file_path = new_path / filename
                new_file_path.write_text(adapted_content, encoding='utf-8')
                log_messages.append(f"Created '{new_file_path}' from template.")
            
            return (True, "\n".join(log_messages))

        except Exception as e:
            return (False, f"An unexpected error occurred during service creation: {e}")
        
# --- Core Asynchronous Tools ---

class RefactorFileContentTool(Tool):
    name = "refactor_file_content"
    description = (
        "Reads a file, applies a set of refactoring instructions to its content, and writes the result back to the same file. "
        "This is a specialized sub-tool, typically called by a larger workflow."
    )
    is_risky = True

    async def __call__(self, path: str, instructions: str) -> Tuple[bool, str]:
        p = Path(path)
        if not p.exists() or not p.is_file():
            return (False, f"Error: File not found at {path}")

        try:
            original_content = p.read_text(encoding='utf-8')

            prompt = f"""You are an expert code refactoring agent. Your sole task is to modify the provided source code based on the user's instructions. You must return only the complete, final, modified code file. Do not add any commentary, explanations, or markdown formatting.

<Instructions>
{instructions}
</Instructions>

<OriginalCode path="{path}">
{original_content}
</OriginalCode>

Modified Code:"""

            handler = ResponseHandler()
            # NOTE: Ensure this model is configured in your default_config.yml
            synthesis_model = "gemini-2.5-pro-latest" 
            result = await handler.call_api(prompt, model=synthesis_model, generation_config={"temperature": 0.0})
            
            modified_content = result["content"].strip()

            if not modified_content:
                return (False, "Error: Refactoring agent returned an empty response. No changes were made.")

            p.write_text(modified_content, encoding='utf-8')
            return (True, f"Successfully refactored and wrote new content to {path}")

        except Exception as e:
            return (False, f"Error refactoring file {path}: {e}")

class ExecuteRefactoringWorkflowTool(Tool):
    name = "execute_refactoring_workflow"
    description = (
        "Executes a complete, safe refactoring workflow for existing code within a new git branch. "
        "It creates a branch, removes specified files, refactors content in other files, and commits all changes. "
        "This is the mandatory tool for any development task that modifies the codebase. "
        "Do NOT use this for creating a new service from a template; use 'create_service_from_template' for that specific task."
    )
    is_risky = True

    async def __call__(self, branch_name: str, commit_message: str, refactoring_instructions: str, files_to_remove: List[str] = None, files_to_refactor: List[str] = None) -> Tuple[bool, str]:
        try:
            # Step 1: Create Branch
            success, result = _run_git_command(["git", "checkout", "-b", branch_name])
            if not success:
                return (False, f"Failed to create branch: {result}")
            print(f"   - ✅ Branched: {branch_name}")

            # Step 2: Remove Files
            if files_to_remove:
                for file_path in files_to_remove:
                    p = Path(file_path)
                    if p.exists():
                        success, result = _run_git_command(["git", "rm", file_path])
                        if not success:
                            return (False, f"Failed to remove file {file_path}: {result}")
                        print(f"   - ✅ Removed: {file_path}")
                    else:
                        print(f"   - ℹ️ Skipped removal (file not found): {file_path}")

            # Step 3: Refactor Files
            if files_to_refactor:
                for path in files_to_refactor:
                    if not path or not refactoring_instructions:
                        return (False, "Invalid arguments. 'path' in files_to_refactor and 'refactoring_instructions' are required.")
                    
                    refactor_tool = RefactorFileContentTool()
                    success, result = await refactor_tool(path, refactoring_instructions)
                    if not success:
                        return (False, f"Failed to refactor file {path}: {result}")
                    print(f"   - ✅ Refactored: {path}")

            # Step 4: Stage All Changes
            success, result = _run_git_command(["git", "add", "."])
            if not success:
                return (False, f"Failed to stage changes: {result}")
            print("   - ✅ Staged all changes.")

            # Step 5: Commit
            success, result = _run_git_command(["git", "commit", "-m", commit_message])
            if not success:
                return (False, f"Failed to commit changes: {result}")
            print("   - ✅ Committed.")

            return (True, f"Workflow completed successfully on branch '{branch_name}'.")

        except Exception as e:
            return (False, f"An unexpected error occurred during the workflow: {e}")

# --- Granular Synchronous Tools (Still useful for simple, one-off tasks) ---

class ReadFileTool(Tool):
    name = "read_file"; description = "Reads the entire content of a specified file. Usage: read_file(path: str)"; is_risky = False
    async def __call__(self, path: str) -> Tuple[bool, str]:
        p = Path(path)
        if not p.exists(): return (False, f"Error: File not found at {path}")
        if not p.is_file(): return (False, f"Error: Path {path} is a directory, not a file.")
        try:
            with open(p, 'r', encoding='utf-8') as f: return (True, f.read())
        except Exception as e: return (False, f"Error: Could not read file {path}: {e}")

class WriteFileTool(Tool):
    name = "write_file"; description = "Writes content to a specified file, overwriting it if it exists. Usage: write_file(path: str, content: str)"; is_risky = True
    async def __call__(self, path: str, content: str) -> Tuple[bool, str]:
        p = Path(path)
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, 'w', encoding='utf-8') as f: f.write(content)
            return (True, f"Successfully wrote {len(content)} characters to {path}")
        except Exception as e: return (False, f"Error: Could not write to file {path}: {e}")

class ListFilesTool(Tool):
    name = "list_files"; description = "Lists all files and directories in a specified path, relative to the project root. Usage: list_files(path: str = '.')"; is_risky = False
    async def __call__(self, path: str = '.') -> Tuple[bool, str]:
        p = Path(path)
        if not p.exists(): return (False, f"Error: Path does not exist: {path}")
        if not p.is_dir(): return (False, f"Error: Path is not a directory: {path}")
        try:
            files = os.listdir(p)
            if not files: return (True, f"Directory '{path}' is empty.")
            return (True, "\n".join(files))
        except Exception as e: return (False, f"Error listing files in {path}: {e}")

class CreateDirectoryTool(Tool):
    name = "create_directory"; description = "Creates a new directory at the specified path. Usage: create_directory(path: str)"; is_risky = True
    async def __call__(self, path: str) -> Tuple[bool, str]:
        p = Path(path)
        try:
            p.mkdir(parents=True, exist_ok=True)
            return (True, f"Successfully created directory at {path}")
        except Exception as e:
            return (False, f"Error: Could not create directory at {path}: {e}")

class MoveFileTool(Tool):
    name = "move_file"; description = "Moves a file or directory from a source to a destination. Usage: move_file(source: str, destination: str)"; is_risky = True
    async def __call__(self, source: str, destination: str) -> Tuple[bool, str]:
        source_path = Path(source)
        dest_path = Path(destination)
        if not source_path.exists():
            return (False, f"Error: Source path does not exist: {source}")
        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source_path), str(dest_path))
            return (True, f"Successfully moved {source} to {destination}")
        except Exception as e:
            return (False, f"Error: Could not move {source} to {destination}: {e}")
        
class RunShellCommandTool(Tool):
    name = "run_shell"
    description = "Executes a shell command in the project's root directory. Usage: run_shell(command: str)"
    is_risky = True
    
    async def __call__(self, command: str) -> Tuple[bool, str]:
        if not isinstance(command, str):
            return (False, "🚫 SECURITY: Command must be a string.")
        command = command.strip()
        if not command:
            return (False, "🚫 ERROR: Empty command provided.")
        
        for pattern in SHELL_COMMAND_BLOCKLIST:
            if re.search(pattern, command, re.IGNORECASE):
                return (False, f"🚫 SECURITY BLOCK: Command '{command}' matches a dangerous pattern.")
        
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, 
                check=False, timeout=60, cwd=Path.cwd()
            )
            stdout = result.stdout[:10000] if result.stdout else ""
            stderr = result.stderr[:10000] if result.stderr else ""
            output = f"STDOUT:\n{stdout}\n\nSTDERR:\n{stderr}"
            if result.returncode == 0:
                return (True, output)
            else:
                return (False, f"Command failed with return code {result.returncode}\n\n{output}")
        except subprocess.TimeoutExpired:
            return (False, f"Error: Command '{command}' timed out after 60 seconds.")
        except Exception as e:
            return (False, f"Error executing command '{command}': {str(e)}")

class GitCreateBranchTool(Tool):
    name = "git_create_branch"; description = "Creates and checks out a new local branch. Usage: git_create_branch(branch_name: str)"; is_risky = True
    async def __call__(self, branch_name: str) -> Tuple[bool, str]:
        return _run_git_command(["git", "checkout", "-b", branch_name])

class GitAddTool(Tool):
    name = "git_add"; description = "Stages a specific file or directory. Usage: git_add(path: str)"; is_risky = True
    async def __call__(self, path: str) -> Tuple[bool, str]:
        return _run_git_command(["git", "add", path])

class GitCommitTool(Tool):
    name = "git_commit"; description = "Creates a commit with the given message. Usage: git_commit(commit_message: str)"; is_risky = True
    async def __call__(self, commit_message: str) -> Tuple[bool, str]:
        return _run_git_command(["git", "commit", "-m", commit_message])

class GitPushTool(Tool):
    name = "git_push"; description = "Pushes the current local branch to the remote 'origin'. Usage: git_push()"; is_risky = True
    async def __call__(self) -> Tuple[bool, str]:
        try:
            result = subprocess.run("git rev-parse --abbrev-ref HEAD", shell=True, capture_output=True, text=True, check=True, timeout=60)
            current_branch = result.stdout.strip()
            return _run_git_command(["git", "push", "--set-upstream", "origin", current_branch])
        except subprocess.CalledProcessError as e:
            return (False, f"Error getting current branch name: {e.stderr.strip()}")

class GitListBranchesTool(Tool):
    name = "git_list_branches"
    description = "Lists all local branches in the repository. Usage: git_list_branches()"
    is_risky = False
    async def __call__(self) -> Tuple[bool, str]:
        try:
            result = subprocess.run(["git", "branch"], capture_output=True, text=True, check=True, timeout=30)
            branches = [line.strip().replace('* ', '') for line in result.stdout.split('\n') if line.strip()]
            return (True, "\n".join(branches))
        except Exception as e:
            return (False, f"Error listing branches: {e}")

class GitCheckoutTool(Tool):
    name = "git_checkout"
    description = "Switches to an existing local branch. Usage: git_checkout(branch_name: str)"
    is_risky = True
    async def __call__(self, branch_name: str) -> Tuple[bool, str]:
        return _run_git_command(["git", "checkout", branch_name])

class GitRemoveFileTool(Tool):
    name = "git_remove_file"
    description = "Removes a file from the working directory and stages the deletion for the next commit. Usage: git_remove_file(path: str)"
    is_risky = True
    async def __call__(self, path: str) -> Tuple[bool, str]:
        p = Path(path)
        if not p.exists():
            # This is not an error in a workflow; the desired state is "file is gone".
            return (True, f"File not found at {path}. No action needed.")
        return _run_git_command(["git", "rm", path])

# --- The Central Registry ---

class ToolRegistry:
    def __init__(self):
        self._tools = {}
        self.register(ReadFileTool())
        self.register(WriteFileTool()) 
        self.register(RunShellCommandTool())
        self.register(ListFilesTool())
        self.register(CreateDirectoryTool())
        self.register(MoveFileTool())
        self.register(GitCreateBranchTool())
        self.register(GitAddTool())
        self.register(GitCommitTool()) 
        self.register(GitPushTool())
        self.register(RefactorFileContentTool())
        self.register(ExecuteRefactoringWorkflowTool())
        self.register(GitListBranchesTool())
        self.register(GitCheckoutTool())
        self.register(GitRemoveFileTool())
        self.register(CreateServiceFromTemplateTool())

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Tool:
        return self._tools.get(name)

    def get_all_tools(self) -> List[Tool]:
        return list(self._tools.values())

    def get_tool_descriptions(self) -> str:
        descriptions = "<Tools>\n"
        for tool in self.get_all_tools():
            descriptions += f"  <Tool name='{tool.name}' signature='{tool.description}' />\n"
        descriptions += "</Tools>"
        return descriptions

TOOL_REGISTRY = ToolRegistry()