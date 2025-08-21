# TECHNICAL_DEBT.md

This document is the canonical tracker for known architectural and implementation shortcomings in the AI Assistant project. It serves as a transparent record of identified issues that should be prioritized in future development cycles.

> **Note:** For planned new features and major architectural evolutions, please see the `PROJECT_ROADMAP.md`.

---

- - -

## Active Issues
*(There are currently no active high-priority technical debt items.)*

---

## Resolved Issues

*(This section tracks technical debt that has been addressed in recent development cycles.)*

### RESOLVED (TD-008): Critical Failure in Plan Validation Logic
-   **Resolution:** This critical failure has been comprehensively resolved through a multi-layered refactoring.
    1.  The `PersonaLoader` bug was fixed to correctly preserve `allowed_tools` during inheritance.
    2.  A unified validation gate was implemented in `kernel.py` that checks both persona rules and `governance.yml` compliance rules.
    3.  The Planner was refactored to use the `instructor` library with Pydantic models (`ExecutionPlan`), which provides an additional, powerful layer of automatic validation, guaranteeing that any generated plan is structurally and syntactically correct before it even reaches the validation gate. This makes the system robust against malformed LLM outputs.

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

 
### RESOLVED (TD-009): Inconsistent API Client Usage
-   **Resolution:** This issue has been resolved by creating a centralized, reusable client factory in `src/ai_assistant/llm_client_factory.py`. This factory provides `instructor`-patched clients for any configured model. Both the `Planner` (`planner.py`) and the Adversarial Critic (`kernel.py`) have been refactored to use this factory, eliminating code duplication and ensuring a consistent, modern approach to all structured LLM calls. The legacy `ResponseHandler` is now only used for non-structured synthesis calls.
