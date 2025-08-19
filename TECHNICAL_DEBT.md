# TECHNICAL_DEBT.md

This document is the canonical tracker for known architectural and implementation shortcomings in the AI Assistant project. It serves as a transparent record of identified issues that should be prioritized in future development cycles.

> **Note:** For planned new features and major architectural evolutions, please see the `PROJECT_ROADMAP.md`.

---

- - -

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

### RESOLVED (TD-007): Improve Plugin Discovery and User Feedback
 -   **Resolution:** The `cli.py` module was enhanced to improve the user experience...

## Active Issues

### TD-006: Inconsistent and Orphaned Plugin Architecture
-   **Problem:** The `trading_plugin.py` exists as an orphaned file using a deprecated local plugin pattern...
-   **Impact:** This creates architectural confusion, makes the system harder to maintain...
-   **Required Action:** Refactor the `trading_plugin.py` to conform to the standard entry-point pattern...