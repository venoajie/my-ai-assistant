# Guide: Orchestrating Multi-Agent Projects

This guide covers the most advanced workflow in the AI Assistant: using the **Project Manager & Orchestrator (`pmo-1`)** persona to manage a complex, multi-stage project from start to finish. This workflow graduates the tool from a specialist assistant for discrete tasks to a guided project management platform.

## When to Use This Workflow

Use this workflow for complex goals that cannot be completed in a single step, such as:
-   Building a new feature or a small application from scratch.
-   Performing a multi-stage refactoring that involves design, implementation, and testing.
-   Executing a complex audit that requires multiple specialists.

For simpler, single-focus tasks like "refactor this one file," the standard [Two-Stage Workflow](./getting_started.md) is more appropriate.

## The Core Concepts

This workflow revolves around two key components:

1.  **The Orchestrator (`pmo-1`):** The `core/pmo-1` persona acts as the project manager. It does not write code or perform analysis itself. Its sole job is to maintain the project's state and tell you, the user, which specialist to call next and with what instructions.
2.  **The State File (`PROJECT_STATE.md`):** This file is the single source of truth for the entire project. It contains the project goal, the plan, the dependency chain of tasks, and the current status. The `pmo-1` persona reads and writes to this file to track progress.

You, the user, act as the bridge, executing the commands given by the `pmo-1` and feeding the results back to it.

---

## Walkthrough: Building a "Weather CLI" Tool

Let's walk through an example project: **"Create a command-line tool that fetches and displays the weather for a given city."**

### Step 1: Project Kickoff

You start by giving the high-level goal to the `pmo-1` persona.

**Your Command:**
```bash
ai --persona core/pmo-1 "I want to build a command-line tool that fetches and displays the weather for a given city."
```

**The `pmo-1`'s Response:**
The orchestrator will create the initial `PROJECT_STATE.md` file and give you the command for the next step: defining the requirements with a specialist.

```text
### Next Command
Execute the following command to have the `csa-1` persona define the project requirements:
```bash
ai --persona domains/programming/csa-1 -f PROJECT_STATE.md "Based on the project state, generate a detailed list of functional and non-functional requirements. Update the 'Requirements' section of the attached file with your findings."
```

### Step 2: Defining Requirements & Architecture

You run the command provided by `pmo-1`. The `csa-1` (Collaborative Systems Architect) will generate the requirements and architecture, updating the `PROJECT_STATE.md` file. After it finishes, you check back in with the project manager.

**Your Command:**
```bash
# You provide the updated state file from the previous step
ai --persona core/pmo-1 -f PROJECT_STATE.md "The requirements and architecture are complete. What is the next step?"
```

**The `pmo-1`'s Response:**
The orchestrator sees that the design phase is done, updates the status, and gives you the next command for the implementation phase. **Note that it now hands off the task to a different specialist, the `rce-1` (Refactoring & Code Enhancement) persona, who is an expert in writing code.**

```text
### Analysis & Plan
The project's `PENDING_DESIGN` phase is complete. The next step is `Implementation`. I will update the state file and assign this task to the `rce-1` persona.

---
### Generated Artifacts
<!-- FILENAME: PROJECT_STATE.md -->
```markdown
# Project State: Weather CLI Tool

- **version**: 1.0
- **status**: PENDING_IMPLEMENTATION
- **goal**: "Create a command-line tool that fetches and displays the weather for a given city."

## Project Plan & Dependency Chain
1.  **Phase: Requirements Definition**
    -   **Specialist:** `domains/programming/csa-1`
    -   **Status:** COMPLETE
2.  **Phase: Architectural Design**
    -   **Specialist:** `domains/programming/csa-1`
    -   **Status:** COMPLETE
3.  **Phase: Implementation**
    -   **Specialist:** `domains/programming/rce-1`
    -   **Status:** PENDING
```

---
### Next Command
Execute the following command to have `rce-1` implement the CLI tool. Use the `--output-dir` flag for safety:
```bash
ai --persona domains/programming/rce-1 --output-dir ./ai_runs/weather-cli \
  -f PROJECT_STATE.md \
  "<ACTION>Based on the architecture in the state file, implement the weather CLI tool. Create all necessary files.</ACTION>"
```

### Step 3 and Beyond

You continue this cycle:
1.  Run the command provided by `pmo-1` to have a specialist complete a task.
2.  Take the updated `PROJECT_STATE.md` from the specialist.
3.  Give the updated state file back to `pmo-1` and ask "What's next?".

The `pmo-1` will guide you through the entire project lifecycle until the `status` in the state file is `COMPLETE`.
