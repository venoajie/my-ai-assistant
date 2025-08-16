
# Getting Started: Your First Workflow

This guide will walk you through the core concepts and commands you need to start using the AI Assistant effectively.

## The Core Concept: Your First Command

Almost every interaction with the assistant follows a simple structure:

```bash
ai [FLAGS] "Your goal in plain English"
```
-   **`[FLAGS]`**: Optional switches that change the assistant's behavior.
-   **`"Your Goal..."`**: Your instruction to the assistant, enclosed in quotes.

### Your Main Controls: The Core Flags

This table lists the most common flags you will use.

| Flag | What It Does | Why You Use It |
| :--- | :--- | :--- |
| `--new-session` | Starts a brand new, clean conversation. | **Use this for every new task.** It ensures the AI's memory is fresh. |
| `--session <ID>` | Resumes a previous conversation using its unique ID. | **Use this to continue a task** you started earlier. |
| `--persona <ALIAS>` | Makes the AI adopt a specific "expert" personality. | Personas provide expert-level instructions, leading to higher-quality results. **Highly recommended.** |
| `-f, --file <PATH>` | Attaches the content of a file to your request. Can be used multiple times. | Use this when the AI needs to **read, review, or modify one or more files**. |
| `--context <PLUGIN>` | Loads a domain-specific context plugin. | Use this to give the AI **specialized knowledge** about your project's domain. |
| `--output-dir <PATH>` | Generates a reviewable "Output Package" instead of executing live. | For complex or risky tasks, this separates AI analysis from execution, allowing for manual review. |

---

## The Two-Stage Workflow: Analyze then Execute

For any task that involves modifying files or interacting with Git, the recommended approach is the two-stage workflow. This decouples the AI-driven analysis from the deterministic, safe execution of the plan.

### Stage 1: Generate an Output Package

Use the `--output-dir` flag to have the AI analyze your request and generate a self-contained "Output Package". The AI will not perform any live actions.

```bash
# The AI will analyze the request and create a package in './ai_runs/refactor-01'
ai --new-session --persona core/csa-1 --output-dir ./ai_runs/refactor-01 \
  -f src/services/distributor.py \
  "<ACTION>Refactor the 'distributor' service to improve its logging.</ACTION>"
```

This command creates a directory with the following structure:
```
./ai_runs/refactor-01/
├── manifest.json         # A machine-readable JSON plan of all actions.
├── workspace/            # Contains the full, final content of all modified files.
└── summary.md            # A human-readable summary of the proposed changes.
```

### Stage 2: Review and Execute the Plan

Once the package is generated, you can review the proposed changes and then use the `ai-execute` command to apply them.

```bash
# 1. Review the plan (optional but recommended)
cat ./ai_runs/refactor-01/summary.md

# 2. Execute the plan with a dry-run to see what commands will run
ai-execute ./ai_runs/refactor-01

# 3. Apply the changes for real using the --confirm flag
ai-execute ./ai_runs/refactor-01 --confirm
```

---

## Working with Multiple Files & Complex Queries

When your commands become long or involve many files, it's best to save them in a script. This is the most robust and readable method.

**Create a file `my_task.sh`:**
```bash
#!/bin/bash
set -e # Exit immediately if any command fails

# Step 1: Define all file arguments in a clean array.
files=(
    -f src/ai_assistant/cli.py
    -f src/ai_assistant/config.py
)

# Step 2: Define your long, multi-line query safely.
query="Analyze the attached files and describe their relationship."

# Step 3: Execute the command safely.
ai --new-session --persona core/csa-1 "${files[@]}" "$query"
```

**How to run this script:**
```bash
# 1. Make the script executable (you only need to do this once)
chmod +x my_task.sh

# 2. Run it
./my_task.sh
```
```
