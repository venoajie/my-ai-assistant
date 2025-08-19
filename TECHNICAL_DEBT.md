# TECHNICAL_DEBT.md

This document is the canonical tracker for known architectural and implementation shortcomings in the AI Assistant project. It serves as a transparent record of identified issues that should be prioritized in future development cycles.

---

- - -

## Resolved Issues

*(This section tracks technical debt that has been addressed in recent development cycles.)*

+### RESOLVED (TD-003): Lack of a Comprehensive Testing Suite
+ -   **Resolution:** A new testing suite for data contracts was implemented in `tests/test_contract_validation.py`. This suite programmatically enforces the structural integrity of key artifacts, starting with the `Output Package Manifest`. Crucially, the validation schema is no longer a static file but is now generated directly from the canonical documentation in `docs/system_contracts.yml` via the `scripts/generate_schemas.py` script. The CI/CD pipeline has been updated to run these tests and to fail if the generated schemas are not committed, creating a robust, closed-loop system that prevents drift between documentation, tests, and implementation. A modern, reliable packaging strategy for including test data was also established.

### RESOLVED (TD-004): Executor Lacks Filesystem Operation Support
-   **Resolution:** The `kernel.py` and `executor.py` modules were enhanced to support `create_directory` and `move_file` actions. The `ToolRegistry` was updated with the corresponding tools. This was validated in our test scenario.

### RESOLVED (TD-002): Incomplete Plugin Example
-   **Resolution:** The stub `trading_plugin.py` was replaced with a comprehensive, well-documented example that demonstrates best practices, including being project-aware (reading `.ai_config.yml`) and query-aware (conditional context injection).

### RESOLVED (TD-005): PersonaLoader Fails to List All Personas
-   **Resolution:** A review of the current `persona_loader.py` confirms this issue has been fixed. The `list_builtin_personas` method now correctly uses `importlib.resources` and `rglob` to perform a full recursive scan of the packaged personas directory.

### TD-006: Inconsistent and Orphaned Plugin Architecture
-   **Problem:** The `trading_plugin.py` exists as an orphaned file using a deprecated local plugin pattern (`<name>_plugin.py`). It is inconsistent with the modern, entry-point-based domain plugins (e.g., `domains/programming/context.py`) and is currently unreachable dead code as it is not registered in `pyproject.toml`.
-   **Impact:** This creates architectural confusion, makes the system harder to maintain, and leaves a non-functional plugin in the codebase. New developers might copy the wrong pattern, propagating the debt.
-   **Required Action:** Refactor the `trading_plugin.py` to conform to the standard entry-point pattern. This involves moving it to `src/ai_assistant/plugins/domains/trading/context.py`, registering it in `pyproject.toml` under the `"domains-trading"` entry point, and deleting the old file.


### RESOLVED (TD-007): Improve Plugin Discovery and User Feedback
 -   **Resolution:** The `cli.py` module was enhanced to improve the user experience around context plugins. When a plugin is auto-loaded based on a persona's domain, the application now prints a more explicit message, naming both the persona and the loaded plugin (e.g., "Persona 'domains/finance/fa-1' triggered auto-loading of the 'Finance' context plugin."). Additionally, a new command-line flag, `--show-context`, was added. This allows a user to run the entire context-gathering phase (including file attachments and all plugin logic) and view the final context string that would be sent to the agent, without initiating the full, token-consuming agent run. This significantly improves the system's transparency and debuggability.