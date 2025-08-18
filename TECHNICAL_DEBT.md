# TECHNICAL_DEBT.md

This document is the canonical tracker for known architectural and implementation shortcomings in the AI Assistant project. It serves as a transparent record of identified issues that should be prioritized in future development cycles.

---

### TD-002: Incomplete Plugin Example
-   **Problem:** The example `trading_plugin.py` is a minimal stub. It does not demonstrate key features like being project-aware (e.g., reading a project-specific config file) or providing query-aware context.
-   **Impact:** This hinders new developers who want to extend the system, as there is no clear, practical template to follow for creating a useful plugin.
-   **Required Action:** Fully implement `trading_plugin.py` or create a new, well-documented example plugin that demonstrates best practices, including how to parse files and provide context that is conditional on the user's query.

### TD-003: Lack of a Comprehensive Testing Suite
-   **Problem:** The `tests` directory is present but lacks a comprehensive suite of unit and integration tests.
-   **Impact:** This represents a significant risk to long-term stability and maintainability. There is no automated safety net to prevent regressions when refactoring critical components like the `Planner`, `Kernel`, or `PersonaLoader`.
-   **Required Action:** Implement a testing framework (e.g., `pytest`). Prioritize adding unit tests for critical, non-LLM components, especially the `PersonaValidator`, the `Planner`'s JSON recovery logic, and the security guards in the `RunShellCommandTool`.


### TD-004: Executor Lacks Filesystem Operation Support
-   **Problem:** The `executor` system does not support file system operations like `mkdir` or `mv`. This limits the complexity of automated refactorings that can be performed in the "Output-First" mode.
-   **Required Action:** Enhance `kernel.py` and `executor.py` to support `create_directory` and `move_file` actions in the `manifest.json`.

**Prompt to create this fix:**
```bash
ai --persona core/arc-1 --output-dir ai_runs/enhance_executor \
  -f src/ai_assistant/kernel.py \
  -f src/ai_assistant/executor.py \
  "&lt;ACTION&gt;Enhance the executor system. The manifest.json and associated logic should be updated to support 'create_directory' and 'move_file' actions. This will allow the AI to package more complex file system refactorings.&lt;/ACTION&gt;"

### TD-005: PersonaLoader Fails to List All Personas
-   **Problem:** The `PersonaLoader.list_builtin_personas` method fails to recursively scan the packaged data directory, resulting in the omission of personas in subdirectories like `domains/`.
-   **Impact:** Users are unaware of all available specialist personas, limiting the tool's usability.
-   **Required Action:** Refactor `list_builtin_personas` to correctly use `importlib.resources` to perform a full recursive scan.

### TD-006: Overly Aggressive CLI Sanity Checks
-   **Problem:** The `_run_prompt_sanity_checks` function in `cli.py` triggers warnings for informational commands (e.g., `--list-personas`) that do not require a persona.
-   **Impact:** Minor user experience issue, presents confusing warnings.
-   **Required Action:** Refactor the check to only trigger when a user provides a query, not for informational flags.
        </StaticFile>
        <Inject src="docs/system_contracts.yml"/>
        
        <!-- Core Governance Files (Corrected Paths & Content) -->
        <StaticFile path="src/ai_assistant/internal_data/persona_config.yml">
