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


*   **ID:** `TD-004`
*   **Problem:** The `executor` system does not support file system operations like `mkdir` or `mv`. This limits the complexity of automated refactorings that can be performed in the "Output-First" mode.
*   **Required Action:** Enhance `kernel.py` and `executor.py` to support `mkdir` and `mv` actions in the `manifest.json`.

**Prompt to create this fix:**
```bash
ai --persona core/arc-1 --output-dir ai_runs/enhance_executor \
  -f src/ai_assistant/kernel.py \
  -f src/ai_assistant/executor.py \
  "<ACTION>Enhance the executor system. The manifest.json and associated logic should be updated to support 'create_directory' and 'move_file' actions. This will allow the AI to package more complex file system refactorings.</ACTION>"