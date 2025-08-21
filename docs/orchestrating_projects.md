# Guide: Orchestrating Multi-Agent Projects

This guide covers the most advanced workflow in the AI Assistant: using the **Project Management & Orchestrator (`pmo-1`)** persona to manage a complex, multi-stage project from start to finish. This workflow graduates the tool from a specialist assistant for discrete tasks to a guided project management platform.

## When to Use This Workflow

Use this workflow for complex goals that cannot be completed in a single step, such as:
-   Building a new feature or a small application from scratch.
-   Performing a multi-stage refactoring that involves design, implementation, and testing.
-   Executing a complex audit that requires multiple specialists.

## The Core Concepts: PMO-as-Code

This workflow revolves around a structured "Project Management Office as Code" system located in the `.ai_pmo/` directory at your project's root.

1.  **The Orchestrator (`pmo-1`):** The `core/pmo-1` persona acts as the project manager. It does not write code itself. Its sole job is to maintain the project's state and tell you, the user, which specialist to call next and with what instructions.
2.  **The Portfolio Dashboard (`PROGRAM_STATE.md`):** This is the master file providing a high-level view of all active and planned projects.
3.  **The Project Charter (`projects/*.md`):** Each project gets its own detailed charter file. This is the single source of truth for a specific project's goal, plan, dependency chain, and current status.

You, the user, act as the bridge, executing the commands given by the `pmo-1` and feeding the results back to it.

---

## Walkthrough: Building a "Weather CLI" Tool

Let's walk through an example project: **"Create a command-line tool that fetches and displays the weather for a given city."**

### Step 1: Project Kickoff

You start by giving the high-level goal to the `pmo-1` persona.

**Your Command:**
```bash
ai --persona core/pmo-1 --output-dir ./ai_runs/init-weather-cli-project \
  "<ACTION>I want to build a command-line tool that fetches and displays the weather for a given city. Create a new project charter for this in the workspace, and also create the initial PROGRAM_STATE.md dashboard.</ACTION>"
```
After executing the output package, you will have the `.ai_pmo/` directory structure.

### Step 2: Get the Next Action from the Orchestrator

Now that the project is initialized, you ask the orchestrator for the first concrete step.

**Your Command:**
```bash
ai --persona core/pmo-1 \
  -f .ai_pmo/PROGRAM_STATE.md \
  -f .ai_pmo/projects/P-001_WEATHER_CLI.md \
  "The project is initialized. What is the next command I need to run?"
```

**The `pmo-1`'s Response:**
The orchestrator will analyze the project charter, see that the "Requirements" phase is pending, and give you the exact command to execute with the correct specialist.

```text
### Next Command
The 'Requirements Definition' phase is pending. Execute the following command to have the `csa-1` persona define the project requirements:
```bash
ai --persona domains/programming/csa-1 --output-dir ./ai_runs/weather-cli-reqs \
  -f .ai_pmo/projects/P-001_WEATHER_CLI.md \
  "<ACTION>Based on the project charter, generate a detailed list of functional and non-functional requirements. Update the 'Requirements' section of the charter file and place it in the workspace.</ACTION>"
```

### Step 3 and Beyond: The Execution Loop

You continue this cycle for the entire project:
1.  Run the command provided by `pmo-1` to have a specialist complete a task (e.g., writing code, running tests).
2.  Execute the resulting output package to apply the changes.
3.  Commit the code changes and the updated project charter to your feature branch.
4.  Ask `pmo-1` "What's next?" by providing the updated charter file.

The `pmo-1` will guide you through the entire project lifecycle—handing off tasks to different specialists for design, implementation, and testing—until the `status` in the charter is `COMPLETE`.
