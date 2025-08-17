# Guide: Safe Multi-Stage Refactoring

This guide covers the official, recommended workflow for performing complex, multi-step refactoring tasks that involve modifying the same file more than once. Following this pattern is critical for ensuring safety, reliability, and context accuracy.

## The Golden Rule of AI-Driven Development

> **The file system is the single source of truth. The AI's context must be explicitly synchronized with it before every task.**

Any workflow that violates this rule is considered an anti-pattern because it can lead to "Context State Drift," where the AI's understanding of a file becomes dangerously out of sync with the file's actual content on your disk.

---

## The Anti-Pattern: Using Interactive Mode for File Changes

It is tempting to use the `--interactive` mode for a multi-step refactoring. **Do not do this.**

**Why is it dangerous?**
When you start an interactive session with `-f my_file.py`, the AI reads the file's content **once**. If you then ask it to make a change and it successfully writes to `my_file.py`, the AI's internal context still contains the **original, stale version** of the file. If you ask for a second change, it will work from the old content and may overwrite your first change or produce incorrect code.

---

## The Recommended Workflow: Iterative Two-Stage Execution

The safest and most robust method is to chain together multiple **Two-Stage (Output-First)** commands. Each step is a clean, independent run that guarantees the AI is working with the latest version of the file.

### Scenario: Refactoring `database.py` in Two Steps

**Goal:**
1.  First, add error handling to the `connect()` function.
2.  Second, add logging to the same `connect()` function.

### Step 1: Generate and Apply the First Change (Error Handling)

First, you ask the AI to generate a plan for the initial refactoring using the `--output-dir` flag.

**Command 1-A (Generate):**
```bash
ai --persona core/csa-1 --output-dir ./ai_runs/db-refactor-01 \
  -f src/database.py \
  "<ACTION>Refactor the 'connect' function in the attached file to include a try/except block for connection errors.</ACTION>"
```

Now, apply the change to your file system.

**Command 1-B (Execute):**
```bash
ai-execute ./ai_runs/db-refactor-01 --confirm
```
At this point, `src/database.py` on your disk has been updated with the new error handling.

### Step 2: Generate and Apply the Second Change (Logging)

Now, you start a **new, clean run**. Crucially, you provide the **newly modified `src/database.py`** as the context. This explicitly synchronizes the AI's context with the file system's source of truth.

**Command 2-A (Generate):**
```bash
ai --persona core/csa-1 --output-dir ./ai_runs/db-refactor-02 \
  -f src/database.py \
  "<ACTION>Add logging to the 'connect' function in the attached file. Log a success message on connection and an error message on failure.</ACTION>"
```

And finally, apply the second change.

**Command 2-B (Execute):**
```bash
ai-execute ./ai_runs/db-refactor-02 --confirm
```

### Outcome

Your `src/database.py` file now correctly contains both the error handling from Step 1 and the logging from Step 2. Each step was performed safely and with perfect context.

| Anti-Pattern (`--interactive`) | Recommended Workflow (Iterative `--output-dir`) |
| :--- | :--- |
| ❌ **Unsafe:** High risk of Context State Drift. | ✅ **Safe:** Guarantees context is always synchronized. |
| ❌ **Token Inefficient:** Context grows with each turn. | ✅ **Token Efficient:** Each run is a clean, focused session. |
| ❌ **Not Auditable:** Changes are live and hard to track. | ✅ **Auditable:** Each step produces a reviewable output package. |
| ❌ **Unreliable:** Prone to complex, cascading failures. | ✅ **Reliable:** Simple, repeatable, and deterministic steps. |
```

<!-- FILENAME: docs/index.md -->
```markdown
# AI Assistant Documentation

Welcome to the official documentation for the AI Assistant. This site provides in-depth guides to help you get the most out of the tool, whether you are a new user or an experienced developer looking to contribute.

## For Users

### Core Concepts
-   **[Getting Started](./getting_started.md):** A step-by-step tutorial for new users. Learn how to install the tool, run your first commands, and understand the core two-stage workflow.
-   **[The Persona System](./personas.md):** This is the most important guide for getting high-quality results. Learn how to use the built-in expert personas and how to create your own.
-   **[Prompting Best Practices](./prompting_guide.md):** Discover the tips and tricks for writing effective prompts that lead to reliable, powerful results.

### Advanced Workflows
-   **[Orchestrating Multi-Agent Projects](./orchestrating_projects.md):** A guide to using the Project Manager (`pmo-1`) persona to manage complex, multi-stage projects from start to finish.
-   **[Safe Multi-Stage Refactoring](./multi_stage_refactoring.md):** The official guide for performing complex, multi-step file modifications safely and reliably.
-   **[Advanced Usage](./advanced_usage.md):** For experienced users. Learn how to build a reusable prompt library and use the powerful autonomous mode safely.

## For Developers & Contributors

-   **[Extending with Plugins](./plugins.md):** Learn how to create custom plugins to inject domain-specific knowledge into the assistant.
-   **[Contributing Guide](./contributing.md):** Information on how to contribute to the project, including our persona governance standards and an overview of the system's core data contracts.
