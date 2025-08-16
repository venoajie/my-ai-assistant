# Advanced Usage Guide

This guide covers advanced workflows for experienced users to maximize productivity and automate complex tasks.

## Building a Prompt Library

To make your common, high-value prompts reusable and reliable, you should store them in a structured library of executable scripts.

1.  **Create Your Library:** In your project root, create a directory.
    ```bash
    mkdir -p prompt_library
    ```

2.  **Create a Reusable Prompt Script:** Create a new file, for example, `prompt_library/audits/01_audit_architecture.sh`, using the robust scripting pattern from the Getting Started guide.

    ```bash
    #!/bin/bash
    set -e

    # --- Configuration ---
    specialist_persona="core/arc-1"
    files_to_review=(
        -f "PROJECT_BLUEPRINT.md"
        -f "src/ai_assistant/kernel.py"
        -f "src/ai_assistant/planner.py"
    )
    query="Review the attached kernel and planner against the project blueprint and identify any architectural deviations."

    # --- Execution ---
    echo "🤖 Starting architectural review..."
    ai --new-session \
       --persona "$specialist_persona" \
       "${files_to_review[@]}" \
       "$query"
    echo "🎉 Review complete."
    ```

3.  **Run Your Prompt:**
    ```bash
    # Make it executable (only once)
    chmod +x prompt_library/audits/01_audit_architecture.sh

    # Run it anytime
    ./prompt_library/audits/01_audit_architecture.sh
    ```

## Expert Mode: Autonomous Operation

This mode allows the assistant to complete an entire task—including making file changes and committing to Git—without asking for your approval at each step.

> **WARNING: Use with extreme caution.** In this mode, the agent can create, modify, and delete files and push to your Git repository without confirmation. Only use it for well-defined tasks where you fully trust the plan.

**Example: Autonomous Refactoring**
```bash
ai --new-session --persona core/csa-1 --autonomous \
  -f src/services/distributor.py \
  "Refactor the 'distributor' service in the attached file to improve its logging and add error handling. When done, commit the changes to a new git branch named 'refactor/distributor-logging'."
```

## Workflow Prerequisite: A Clean Git State
The AI Assistant's automation scripts are powerful but are designed to operate on a clean, known state. If a script fails mid-run, it can leave your local repository in an inconsistent state.

Before running a complex automation script, it is a best practice to ensure your working directory is clean. If you encounter persistent errors, the safest course of action is to perform a hard reset.

**The Standard Cleanup Procedure:**
```bash
# WARNING: These commands will permanently delete all uncommitted changes and untracked files.

# 1. Switch to your main development branch (e.g., 'develop')
git switch develop

# 2. Reset your local files to be an exact match of the last commit
git reset --hard HEAD

# 3. Remove all untracked files and directories (like leftover ai_runs/)
git clean -df
