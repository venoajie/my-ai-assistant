# TECHNICAL_DEBT.md

This document is the canonical tracker for known architectural and implementation shortcomings in the AI Assistant project. It serves as a transparent record of identified issues that should be prioritized in future development cycles.

> **Note:** For planned new features and major architectural evolutions, please see the `PROJECT_ROADMAP.md`.

---

- - -

## Active Issues
Of course. Here is a consolidated and organized report of all identified technical debt, combining both sets of findings. The issues have been grouped by theme and arranged by criticality, suitable for a `technical_debts.md` document.

---

# Technical Debt & Architectural Review Findings

This document is a consolidated list of identified technical debt, architectural inconsistencies, and recommended improvements for the AI Assistant project. The findings are grouped by functional area and ordered by criticality to guide remediation efforts.

## 1. RAG Architecture & Data Pipeline

This is the area with the most critical technical debt. The current implementation diverges significantly from the blueprint's architectural goals, impacting portability, user experience, and adherence to the "Single Source of Truth" principle.

### 1.1. Heavy Client Dependencies Contradict Cloud-Cached Design (Critical)

**The Flaw:** The `[client]` optional dependency forces the installation of heavy ML libraries (`sentence-transformers`, `torch`) on every machine that consumes the RAG index. This directly contradicts the blueprint's goal of a "lightweight client" and nullifies the benefits of the cloud-cached design. It increases the installation footprint on all machines (developer laptops, cloud servers), creates a maintenance burden, and forces redundant computation for query embedding and reranking.

**The Fix:** Architecturally pivot to a centralized RAG service model.
1.  Create a dedicated, network-accessible microservice (e.g., using FastAPI) that is the *only* component with `sentence-transformers` and `torch` dependencies. This service will handle all query embedding and reranking.
2.  Secure this service for consumption by the 2 cloud machines and 1 laptop using standard infrastructure patterns (e.g., private networking within the cloud, with VPN or a secure API Gateway for laptop access).
3.  Refactor the client-side `RAGContextPlugin` to make a simple API call to this service, removing all local ML model logic.
4.  Update `pyproject.toml` to make the `[client]` dependency truly lightweight (e.g., `oci`, `aiohttp`) and create a new `[rag-service]` dependency for the new service.

### 1.2. RAG Client-Index Provider Incompatibility (Critical)

**The Flaw:** The client-side `rag_plugin.py` is hard-coded to only support indexes built with the `"local"` embedding provider. If an index is built in a CI/CD environment using the `"openai"` provider (as supported by `indexer.py`), the client will fail to load it. This breaks the portability of indexes and undermines the entire CI/CD-driven RAG architecture.

**The Fix:** The client must dynamically adapt to the embedding provider specified in the downloaded `index_manifest.json`.
*   In `rag_plugin.py`, when parsing the manifest, the client should initialize the correct embedding client. If `provider` is `"openai"`, it must instantiate an OpenAI client to generate the query embedding. If it's `"local"`, it should load the `SentenceTransformer` model. This makes the client compatible with any index the system can produce.

### 1.3. Duplicated Query Expansion Logic (High)

**The Flaw:** The logic for expanding a user's query with high-level context is implemented in two separate places: once in `kernel.py` for the initial planning phase, and again inside the `CodebaseSearchTool` in `tools.py`. This violates the "Single Source of Truth" principle and is a recipe for behavioral drift.

**The Fix:** Centralize the query expansion logic within the `RAGContextPlugin` itself. This ensures that any component requesting context (either the kernel or a tool) gets the benefit of the expansion automatically and consistently. The `CodebaseSearchTool` should be simplified to a direct pass-through call to the plugin.

### 1.4. Unify Configuration for RAG Indexer (Medium)

**The Flaw:** Key parameters in `indexer.py` are hard-coded, such as `EMBEDDING_BATCH_SIZE = 16` and `DEFAULT_IGNORE_PATTERNS`. This prevents environment-specific optimization and violates the "Configuration over Hard-Coding" principle.

**The Fix:** Move these parameters into the `rag` section of `default_config.yml` and `config.py`.
*   Add `embedding_batch_size` and `default_ignore_patterns` keys.
*   Update `indexer.py` to consume these values from `ai_settings.rag`.

---

## 2. Governance & Configuration Centralization

This category covers violations of the "Single Source of Truth" and "Configuration over Hard-Coding" principles, which lead to fragmented rules and increased maintenance complexity.

### 2.1. Hard-Coded Security Rules (High)

**The Flaw:** The critical `SHELL_COMMAND_BLOCKLIST` is defined in `_security_guards.py` as a hard-coded tuple. While intended for security, this isolates a critical rule set from the central `governance.yml` file, making it non-obvious and harder to audit or extend safely.

**The Fix:** Move the blocklist patterns to `governance.yml` under a `security` key. The `RunShellCommandTool` in `tools.py` should dynamically load these rules from the configuration at startup. This centralizes all operational rules in one auditable location.

### 2.2. Fragmented Plan Validation Logic (Medium)

**The Flaw:** Plan validation rules are split between two locations. `plan_validator.py` correctly reads compliance rules from `governance.yml`, but `data_models.py` contains a hard-coded Python list (`VALID_WORKFLOW_TOOLS`) for its own validation logic. This fragmentation makes it difficult to get a complete picture of all validation rules.

**The Fix:** Move the list of valid workflow tools into `governance.yml` (e.g., under a `kernel_workflow_tools` key). Load this list dynamically in `data_models.py` at module startup, ensuring `governance.yml` is the single source of truth for all plan validation.

---

## 3. System Robustness & Error Handling

These issues relate to the system's resilience and predictability, particularly when encountering errors.

### 3.1. Inconsistent and Brittle Error Handling (High)

**The Flaw:** The system lacks a standardized contract for error handling.
1.  **Tools:** Tools in `tools.py` return errors as simple strings within a `(False, str)` tuple. This provides no structured error information.
2.  **Kernel:** The `kernel.py` relies on brittle string matching (`.startswith("❌ ERROR:")`) to detect failures from the `ResponseHandler`, which is a fragile contract.

**The Fix:** Implement a standardized result object for all tool and service calls.
*   Define a `ToolResult` dataclass (e.g., `ToolResult(success: bool, message: str, data: Optional[Any] = None)`). All tools in `tools.py` must return this object.
*   Refactor `ResponseHandler.call_api` to return a tuple `(success: bool, result_dict: Dict)` instead of just a dictionary. This provides an explicit success flag.
*   Update the `kernel.py` to check these explicit success flags instead of parsing strings, making error handling robust and predictable.

### 3.2. Validate Persona Inheritance During Load (Medium)

**The Flaw:** The `persona_loader.py` does not validate that an inherited base persona (`inherits_from`) actually exists at load time. This check is deferred until manifest generation, meaning a runtime call with a misconfigured persona could fail with an unhelpful error.

**The Fix:** Add an existence check within `persona_loader.py`'s recursive loading function. If a persona specified in `inherits_from` cannot be found, it should raise an immediate and clear `FileNotFoundError`, providing faster feedback to developers.

---

## 4. Kernel & Core Logic Extensibility

These items focus on improving the flexibility and future-proofing of the core agent logic.

### 4.1. Enhance Kernel Workflow Expansion for Extensibility (Medium)

**The Flaw:** The Kernel-Driven Workflow Expansion Pattern is a powerful concept, but its implementation in `kernel.py` is hard-coded to only handle the `execute_refactoring_workflow`. Adding a new workflow would require modifying the core orchestration logic.

**The Fix:** Refactor the kernel to use a registry pattern for workflow expanders.
*   Create a dictionary mapping workflow tool names to their expansion functions (e.g., `WORKFLOW_EXPANDERS = {"execute_refactoring_workflow": _expand_refactoring_workflow_plan}`).
*   The kernel's main loop can then dynamically look up and execute the correct expander, allowing new complex workflows to be added without changing the core orchestration code.

### 4.2. Planner's JSON Self-Correction Redundancy (Low)

**The Flaw:** The `planner.py` module includes a fallback mechanism that uses a second LLM call to fix malformed JSON. However, the `llm_client_factory.py` now forces `instructor.Mode.JSON`, which is designed to prevent malformed JSON in the first place. This fallback adds latency and cost and may now be redundant.

**The Fix:** Instrument the JSON self-correction block with metrics/logging to determine its trigger frequency. If it is rarely or never used, simplify the code by removing the fallback logic and relying on `instructor`'s built-in robustness.

---

## 5. Persona & Build System Integrity

This section covers issues that affect the integrity of the persona ecosystem and the scripts that manage it.

### 5.1. Missing Persona Configuration File (Blocking Bug)

**The Flaw:** The `generate_manifest.py` script, which is critical for ensuring persona integrity at runtime, depends on a `persona_config.yml` file. This file was not provided in the artifacts, meaning the manifest generation process is currently broken.

**The Fix:** Create and commit the `persona_config.yml` file in `src/ai_assistant/internal_data/`. This file must define the required validation rules (e.g., required frontmatter keys, structural rules) for all `.persona.md` files.

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
