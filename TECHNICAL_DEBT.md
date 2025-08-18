# TECHNICAL_DEBT.md

This document is the canonical tracker for known architectural and implementation shortcomings in the AI Assistant project. It serves as a transparent record of identified issues that should be prioritized in future development cycles.

---

### TD-003: Lack of a Comprehensive Testing Suite
-   **Problem:** The `tests` directory is present but lacks a comprehensive suite of unit and integration tests.
-   **Impact:** This represents a significant risk to long-term stability and maintainability. There is no automated safety net to prevent regressions when refactoring critical components like the `Planner`, `Kernel`, or `PersonaLoader`.
-   **Required Action:** Implement a testing framework (e.g., `pytest`). Prioritize adding unit tests for critical, non-LLM components, especially the `PersonaValidator`, the `Planner`'s JSON recovery logic, and the security guards in the `RunShellCommandTool`.

### TD-006: Overly Aggressive CLI Sanity Checks
-   **Problem:** The `_run_prompt_sanity_checks` function in `cli.py` triggers warnings for informational commands (e.g., `--list-personas`) that do not require a persona.
-   **Impact:** Minor user experience issue, presents confusing warnings.
-   **Required Action:** Refactor the check to only trigger when a user provides a query, not for informational flags.

---

## Resolved Issues

*(This section tracks technical debt that has been addressed in recent development cycles.)*

### RESOLVED (TD-004): Executor Lacks Filesystem Operation Support
-   **Resolution:** The `kernel.py` and `executor.py` modules were enhanced to support `create_directory` and `move_file` actions. The `ToolRegistry` was updated with the corresponding tools. This was validated in our test scenario.

### RESOLVED (TD-002): Incomplete Plugin Example
-   **Resolution:** The stub `trading_plugin.py` was replaced with a comprehensive, well-documented example that demonstrates best practices, including being project-aware (reading `.ai_config.yml`) and query-aware (conditional context injection).

### RESOLVED (TD-005): PersonaLoader Fails to List All Personas
-   **Resolution:** A review of the current `persona_loader.py` confirms this issue has been fixed. The `list_builtin_personas` method now correctly uses `importlib.resources` and `rglob` to perform a full recursive scan of the packaged personas directory.