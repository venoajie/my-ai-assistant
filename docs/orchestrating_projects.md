# Guide: Orchestrating Multi-Agent Projects

This guide covers the most advanced workflow in the AI Assistant: using the **Project Manager & Orchestrator (`pmo-1`)** persona to manage a complex, multi-stage project from start to finish. This workflow graduates the tool from a specialist assistant for discrete tasks to a guided project management platform.

## When to Use This Workflow

Use this workflow for complex goals that cannot be completed in a single step, such as:
-   Building a new feature or a small application from scratch.
-   Performing a multi-stage refactoring that involves design, implementation, and testing.
-   Executing a complex audit that requires multiple specialists.

For simpler, single-focus tasks like "refactor this one file" or "review this code," the standard [Two-Stage Workflow](./getting_started.md) is more appropriate.

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
The orchestrator will create the initial `PROJECT_STATE.md` file and give you the command to run for the next step: defining the requirements.

```text
### Analysis & Plan
The project is in the `INITIALIZATION` phase. I will create the initial `PROJECT_STATE.md` file and define the first task, which is to clarify the project requirements. The next step requires the `csa-1` persona.

---
### Generated Artifacts
<!-- FILENAME: PROJECT_STATE.md -->
```markdown
# Project State: Weather CLI Tool

- **version**: 1.0
- **status**: PENDING_REQUIREMENTS
- **goal**: "Create a command-line tool that fetches and displays the weather for a given city."

## Project Plan & Dependency Chain
1.  **Phase: Requirements Definition**
    -   **Specialist:** `core/csa-1`
    -   **Status:** PENDING
2.  **Phase: Architectural Design**
    -   **Specialist:** `core/csa-1`
    -   **Status:** BLOCKED
3.  **Phase: Implementation**
    -   **Specialist:** `core/csa-1`
    -   **Status:** BLOCKED
```

---
### Next Command
Execute the following command to have `csa-1` define the project requirements:
```bash
ai --persona core/csa-1 -f PROJECT_STATE.md "Based on the project state, generate a detailed list of functional and non-functional requirements. Update the 'Requirements' section of the attached file with your findings."
```

### Step 2: Defining Requirements

Now, you run the command provided by `pmo-1`. The `csa-1` persona will generate the requirements and output an updated `PROJECT_STATE.md` file.

After `csa-1` finishes, you check back in with the project manager.

**Your Command:**
```bash
# You provide the updated state file from the previous step
ai --persona core/pmo-1 -f PROJECT_STATE.md "The requirements definition is complete. What is the next step?"
```

**The `pmo-1`'s Response:**
The orchestrator sees that the requirements are done, updates the status, and gives you the next command for the architectural design phase.

```text
### Analysis & Plan
The project's `PENDING_REQUIREMENTS` phase is complete. The next step in the dependency chain is `Architectural Design`. I will update the state file and assign this task to the `csa-1` persona.

---
### Generated Artifacts
<!-- FILENAME: PROJECT_STATE.md -->
```markdown
# Project State: Weather CLI Tool

- **version**: 1.0
- **status**: PENDING_DESIGN
- **goal**: "Create a command-line tool that fetches and displays the weather for a given city."

## Project Plan & Dependency Chain
1.  **Phase: Requirements Definition**
    -   **Specialist:** `core/csa-1`
    -   **Status:** COMPLETE
2.  **Phase: Architectural Design**
    -   **Specialist:** `core/csa-1`
    -   **Status:** PENDING
3.  **Phase: Implementation**
    -   **Specialist:** `core/csa-1`
    -   **Status:** BLOCKED

## Requirements
- The tool must accept a city name as a command-line argument.
- It must fetch weather data from a public API.
- It must display the current temperature, humidity, and wind speed.
- Non-functional: The tool should handle API errors gracefully.
```

---
### Next Command
Execute the following command to have `csa-1` design the application architecture:
```bash
ai --persona core/csa-1 -f PROJECT_STATE.md "Based on the requirements, design a simple architecture for the CLI tool. Specify the main modules, their responsibilities, and any external dependencies. Update the 'Architecture' section of the attached file."
```

### Step 3 and Beyond

You continue this cycle:
1.  Run the command provided by `pmo-1` to have a specialist (`csa-1`, `da-1`, etc.) complete a task.
2.  Take the updated `PROJECT_STATE.md` from the specialist.
3.  Give the updated state file back to `pmo-1` and ask "What's next?".

The `pmo-1` will guide you through the entire project lifecycle—design, implementation, debugging, and finalization—until the `status` in the state file is `COMPLETE`.

This workflow provides a powerful, structured, and repeatable process for tackling large and complex software development tasks with the AI Assistant.
