# TECHNICAL_DEBT.md

This document is the canonical tracker for known architectural and implementation shortcomings in the AI Assistant project. It serves as a transparent record of identified issues that should be prioritized in future development cycles.

> **Note:** For planned new features and major architectural evolutions, please see the `PROJECT_ROADMAP.md`.

---

- - -

## Active Issues

### TD-008: Critical Failure in Plan Validation Logic (High Priority)
-   **Problem:** The system's plan validation is critically flawed. The `PersonaLoader` incorrectly handles the `universal_base_persona`, causing it to discard the `allowed_tools` constraint inherited by specialist personas. Furthermore, the validation logic in the `kernel` is fragmented and incomplete, allowing the AI Planner to generate and execute plans that directly violate its core operational protocol (e.g., using forbidden tools like `read_file` and `write_file`).
-   **Impact:** This is a critical security and reliability failure. It means the persona-based safety guardrails are not being enforced, making the system's behavior for modification tasks unpredictable and potentially dangerous.
-   **Required Action:**
    1.  Fix the bug in `persona_loader.py` to ensure `allowed_tools` rules are correctly preserved when the `universal_base_persona` is applied.
    2.  Perform a comprehensive refactoring of the validation logic in `kernel.py` to create a single, unified, and robust validation gate that correctly checks both persona-based rules (`allowed_tools`) and `governance.yml`-based compliance rules before any plan is submitted to the critic or executor.

---

## Resolved Issues

*(This section tracks technical debt that has been addressed in recent development cycles.)*

### RESOLVED (TD-003): Lack of a Comprehensive Testing Suite
 -   **Resolution:** A new testing suite for data contracts was implemented...

### RESOLVED (TD-004): Executor Lacks Filesystem Operation Support
-   **Resolution:** The `kernel.py` and `executor.py` modules were enhanced...

### RESOLVED (TD-002): Incomplete Plugin Example
-   **Resolution:** The stub `trading_plugin.py` was replaced with a comprehensive, well-documented example...

### RESOLVED (TD-005): PersonaLoader Fails to List All Personas
-   **Resolution:** A review of the current `persona_loader.py` confirms this issue has been fixed...
 
### RESOLVED (TD-006): Inconsistent and Orphaned Plugin Architecture
-   **Resolution:** The `trading_plugin.py` was renamed to context.py and moved to pugins/trading folder...

### RESOLVED (TD-007): Improve Plugin Discovery and User Feedback
 -   **Resolution:** The `cli.py` module was enhanced to improve the user experience...
