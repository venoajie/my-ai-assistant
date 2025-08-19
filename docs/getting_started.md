# Getting Started: Your First Workflow

This guide will walk you through installing the AI Assistant and performing your first tasks. We'll cover the basics of read-only analysis and the critical **Two-Stage Workflow** for safely making file changes.

## Installation

First, install the tool using pip.

```bash
# For stable use
pip install my-ai-assistant

# For development (from a cloned repository)
pip install -e .
```

## Your First Command: Read-Only Analysis

Let's start with a simple, safe task that doesn't modify any files. We'll ask a specialist persona to review a file for us.

1.  **Find a Persona:** First, list the available experts.
    ```bash
    ai --list-personas
    ```
    You'll see a list of personas, including `core/arc-1`, the Architecture Reviewer.

2.  **Run the Command:** Now, ask the architect to review a file. The `-f` flag attaches the file's content to your request.
    ```bash
    ai --persona core/arc-1 -f path/to/your/file.py "Please provide a brief architectural review of this file."
    ```
The assistant will provide a structured analysis without touching your file system.

---

## The Two-Stage Workflow: The Safest Way to Make Changes

For any task that involves modifying files, the **two-stage workflow is the required and recommended approach.** It is the foundation of the system's **[Safety Model](./safety_model.md)**.

This workflow creates an "air gap" between the AI's "thinking" and the actual execution, giving you full control.

### Stage 1: Generate an Output Package

Use the `--output-dir` flag to have the AI generate a plan and a sandboxed copy of its proposed changes. **No changes will be made to your actual files.**

```bash
# The AI will analyze the request and create a package in './ai_runs/refactor-01'
ai --persona domains/programming/coder-1 --output-dir ./ai_runs/refactor-01 \
  -f src/my_file.py \
  "<ACTION>Refactor the main function in this file to improve readability.</ACTION>"
```

This command creates a directory with the following structure:
```
./ai_runs/refactor-01/
├── manifest.json         # A machine-readable JSON plan of all actions.
├── workspace/            # Contains the full, final content of all modified files.
└── summary.md            # A human-readable summary of the proposed changes.
```

### Stage 2: Review and Execute the Plan

Now, you can inspect the proposed changes.

```bash
# 1. Review the summary
cat ./ai_runs/refactor-01/summary.md

# 2. Compare the proposed changes with your original file
diff src/my_file.py ./ai_runs/refactor-01/workspace/src/my_file.py

# 3. If you approve, apply the changes using the separate ai-execute command
ai-execute ./ai_runs/refactor-01 --confirm
```
This process ensures you always have the final say before any file is modified.

---

## Next Steps: Unlocking Project-Specific Power

You've now mastered the basic workflows. The true power of the AI Assistant comes from teaching it about **your specific project**. You do this by creating project-local experts and knowledge bases.

This is the best-practice workflow used by advanced teams to turn the generic assistant into a specialized co-pilot for their codebase.

-   **First, learn how to create project-specific experts:**
    **[➡️ Guide: The Persona System](./personas.md)**

-   **Then, learn how to inject project-specific knowledge:**
    **[➡️ Guide: Extending with Plugins](./plugins.md)**
