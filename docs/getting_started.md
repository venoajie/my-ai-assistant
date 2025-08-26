# Getting Started: Your First Project Workflow

This guide will walk you through using the AI Assistant on your own project for the first time.

**Prerequisite:** You must have the AI Assistant installed in your project's virtual environment. If you have not done this, please follow the **[Installation Guide](./installation.md)** first.

---

## The Scenario: Auditing Your Project

Let's perform a common first task: asking an AI specialist to audit a key file against your project's main architectural document.

### Step 1: Ensure Your Environment is Active

All commands must be run from your project's root directory with its virtual environment activated.

```bash
cd /path/to/your/project
source .venv/bin/activate
```

### Step 2: Your First Command (Read-Only Analysis)

Let's ask a specialist persona to review a file. The `-f` flag attaches files to provide the AI with context.

```bash
# This command asks an architect persona to review your main app file
# against your project's blueprint document.
ai --persona core/arc-1 \
  -f src/main.py \
  -f PROJECT_BLUEPRINT.md \
  "Please review the main application file and check for any deviations from the architectural principles described in the blueprint."
```
The assistant will provide a structured analysis without touching your file system. This is the safest way to start.

---

## The Two-Stage Workflow: The Safest Way to Make Changes

For any task that modifies files, the **two-stage workflow is required.** It creates a safe "air gap" between the AI's plan and the execution.

### Stage 1: Generate an Output Package

Use `--output-dir` to have the AI generate a plan and a sandboxed copy of its proposed changes. **No changes will be made to your actual files.**

```bash
ai --persona domains/programming/coder-1 --output-dir ./ai_runs/refactor-01 \
  -f src/my_file.py \
  "<ACTION>Refactor the main function in this file to improve readability.</ACTION>"
```
This creates a reviewable package in the `ai_runs/refactor-01` directory.

### Stage 2: Review and Execute the Plan

Inspect the proposed changes and, if you approve, apply them with the `ai-execute` command.

```bash
# 1. Review the summary
cat ./ai_runs/refactor-01/summary.md

# 2. (Optional) See a diff of the changes
diff src/my_file.py ./ai_runs/refactor-01/workspace/src/my_file.py

# 3. If you approve, apply the changes
ai-execute ./ai_runs/refactor-01 --confirm
```
This process ensures you always have the final say.

---

## Next Steps

You have now mastered the core workflows. To unlock the full power of the assistant, learn how to create project-specific configurations and make the assistant aware of your entire codebase:

- **[➡️ Guide: Project-Specific Configuration](./project_configuration.md)**
- **[➡️ Guide: Setting Up Codebase-Aware RAG](./rag_workflow.md)**
