# Getting Started: Your First Workflow

This guide will walk you through the core concepts and commands you need to start using the AI Assistant effectively and safely.

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
| `--interactive` | Starts a continuous, stateful chat session. | Use for multi-step **dialogue and analysis**. Avoid for file modifications. |
| `--session <ID>` | Resumes a previous one-shot conversation. | Use this to continue a specific task you started earlier. |
| `--persona <ALIAS>` | Makes the AI adopt a specific "expert" personality. | **This is the key to high-quality results.** Highly recommended. |
| `-f, --file <PATH>` | Attaches the content of a file to your request. | Use when the AI needs to **read, review, or modify one or more files**. |
| `--output-dir <PATH>` | Generates a reviewable "Output Package" instead of executing live. | **This is the required safe mode for any file modifications.** |
| `--context <PLUGIN>` | Loads a domain-specific context plugin. | Use to give the AI **specialized knowledge** about your project's domain. |

---

## The Two-Stage Workflow: The Safest Way to Make Changes

For any task that involves modifying files or interacting with Git, the **two-stage workflow is the required and recommended approach.** It is the foundation of the system's **[Safety Model](./safety_model.md)**.

This workflow decouples the AI-driven analysis from the deterministic, safe execution of the plan.

### Stage 1: Generate an Output Package

Use the `--output-dir` flag to have the AI analyze your request and generate a self-contained "Output Package". The AI will not perform any live actions on your files.

```bash
# The AI will analyze the request and create a package in './ai_runs/refactor-01'
ai --new-session --persona domains/programming/csa-1 --output-dir ./ai_runs/refactor-01 \
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

## Continuous Conversations with Interactive Mode

For tasks that require back-and-forth **dialogue, analysis, or brainstorming**, interactive mode is the best choice. It creates a continuous session that remembers the conversation history.

**To start an interactive session:**
```bash
# Start an interactive session with the Systems Architect persona
ai --interactive --persona domains/programming/csa-1
```
The application will start, and you will be given a prompt (`>`) to enter your queries. The assistant will remember the context of your entire conversation until you type `exit` or `quit`.

> **Warning:** Do not use interactive mode for multi-step file modifications. This can lead to errors where the AI's memory of a file becomes out of sync with the actual file on disk. For this, always use the **[Safe Multi-Stage Refactoring](./multi_stage_refactoring.md)** workflow.

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
ai --new-session --persona domains/programming/csa-1 "${files[@]}" "$query"
```

**How to run this script:**
```bash
# 1. Make the script executable (you only need to do this once)
chmod +x my_task.sh

# 2. Run it
./my_task.sh
