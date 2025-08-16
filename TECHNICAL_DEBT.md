# TECHNICAL_DEBT.md

This document is the canonical tracker for known architectural and implementation shortcomings in the AI Assistant project. It serves as a transparent record of identified issues that should be prioritized in future development cycles.

---

### TD-001: Inconsistent Context Handling in Interactive Mode
-   **Problem:** In one-shot mode, context from files (`-f`) and plugins (`--context`) is prepended directly to the query. In interactive mode, this context is added as a preliminary "user" turn in the history. This can lead to slightly different behavior from the AI between the two modes.
-   **Impact:** This inconsistency can be confusing for users and may cause prompts that work in one mode to be less effective in the other. It violates the principle of least surprise.
-   **Required Action:** Refactor `cli.py` to unify context handling. The recommended approach is to always inject context as a distinct "system" or "context" turn at the beginning of the session history for both modes, ensuring consistent behavior.

### TD-002: Incomplete Plugin Example
-   **Problem:** The example `trading_plugin.py` is a minimal stub. It does not demonstrate key features like being project-aware (e.g., reading a project-specific config file) or providing query-aware context.
-   **Impact:** This hinders new developers who want to extend the system, as there is no clear, practical template to follow for creating a useful plugin.
-   **Required Action:** Fully implement `trading_plugin.py` or create a new, well-documented example plugin that demonstrates best practices, including how to parse files and provide context that is conditional on the user's query.

### TD-003: Lack of a Comprehensive Testing Suite
-   **Problem:** The `tests` directory is present but lacks a comprehensive suite of unit and integration tests.
-   **Impact:** This represents a significant risk to long-term stability and maintainability. There is no automated safety net to prevent regressions when refactoring critical components like the `Planner`, `Kernel`, or `PersonaLoader`.
-   **Required Action:** Implement a testing framework (e.g., `pytest`). Prioritize adding unit tests for critical, non-LLM components, especially the `PersonaValidator`, the `Planner`'s JSON recovery logic, and the security guards in the `RunShellCommandTool`.

### TD-004: Metrics Reporting Does Not Account for All API Calls
-   **Problem:** The `print_summary_metrics` function in `cli.py` only reports on "Planning" and "Synthesis" durations and does not account for the new "Critique" step. The token count is also only for the final API call in the sequence.
-   **Impact:** The metrics reported to the user are incomplete and potentially misleading, hiding the true cost and latency of a multi-step generation.
-   **Required Action:** Refactor `kernel.py` to return a more detailed `timings` dictionary. Refactor `print_summary_metrics` in `cli.py` to correctly display all timings (Planning, Critique, Synthesis) and to aggregate token counts from all API calls made during a single run.