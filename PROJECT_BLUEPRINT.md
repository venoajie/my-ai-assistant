# PROJECT BLUEPRINT: AI Assistant

<!-- Version: 4.0 -->
<!-- Change Summary (v4.0): The RAG pipeline's data layer has been migrated from local ChromaDB files to a centralized PostgreSQL database with pgvector. The indexer (`ai-index`) is now a database client that populates this central store, enabling a true multi-project RAG ecosystem. -->

## 1. System Overview and Core Purpose

This document is the canonical source of truth for the architectural principles and governance of the AI Assistant ecosystem. It serves as a "constitution" for human developers and a "README for the AI," ensuring that all development and AI-driven actions are aligned with the core design philosophy.

The system is a **Three-Tiered Development Ecosystem** designed to assist with software development. Its primary purpose is to provide a safe, reliable, and extensible framework for leveraging Large Language Models to perform complex, multi-step operations.

The ecosystem consists of:
1.  **The Product:** The target application being developed (e.g., a trading app).
2.  **The Conductor (AI Assistant):** A lightweight, command-line-native agent that orchestrates development tasks.
3.  **The Librarian (RAG Service):** A centralized, production-grade service that provides codebase-aware context to the Conductor.

### 1.1. Ecosystem Glossary

This glossary defines the core components and concepts of the Three-Tiered Development Ecosystem.

-   **Three-Tiered Ecosystem:** The overarching architecture composed of three decoupled components: The Product, The Conductor, and The Librarian.
-   **The Product:** The target application being developed. It is the passive subject of analysis and modification.
-   **The Conductor (AI Assistant):** The lightweight, user-facing CLI tool. It orchestrates development workflows, manages personas, and interacts with LLMs. It is a **thin client** that offloads all RAG operations to the Librarian.
-   **The Librarian (RAG Service):** The centralized, standalone, production-grade service responsible for the entire RAG pipeline. It ingests indexes, loads ML models, and serves codebase-aware context via a secure API.
-   **Index Manifest (`index_manifest.json`):** The immutable integration contract created by the indexer. It is a self-describing file within the index archive that specifies the exact embedding model and collection name used, ensuring perfect compatibility between the index artifact and the Librarian service.
-   **Kernel:** The core logic engine within the Conductor responsible for intercepting high-level workflow steps (e.g., `execute_refactoring_workflow`) and expanding them into a deterministic sequence of granular tool calls.
-   **Index Manifest (`index_manifest.json`):** The immutable integration contract created by the indexer. It is a small, self-describing JSON file stored in OCI Object Storage. It specifies the exact embedding model and **PostgreSQL table name** for a given project and branch, ensuring perfect compatibility and directing the Librarian to the correct data source.
---

## 2. Core Architectural Principles

The architecture is built on four foundational principles:

### 2.1. The Three-Tiered Ecosystem
The system is explicitly designed as three decoupled components with clear responsibilities:
-   **The Product (The Subject):** The application whose source code is being analyzed and modified. It is passive and unaware of the other tiers.
-   **The Conductor (The AI Assistant - This Project):** The user-facing tool. It is a **thin client** responsible for managing personas, orchestrating workflows (Plan -> Critique -> Execute), and interacting with LLMs. It **MUST NOT** contain any direct RAG logic.
-   **The Librarian (The RAG Service):** A separate, standalone service. It is the sole owner of the RAG pipeline, responsible for loading models, managing the index, and serving context via a secure API.

### 2.2. Decoupled Thinking and Doing
A strict separation is maintained between **AI-driven analysis (thinking)** and **deterministic execution (doing)**. This principle is enforced through two primary operational modes within the Conductor:
-   **Live Execution Mode:** The default interactive workflow.
-   **Output-First Mode:** For generating reviewable change packages.

#### 2.2.1. Adversarial Validation
To enhance the safety of the "thinking" phase, the system employs an Adversarial Validation Chain. After an initial execution plan is generated, it is passed to a specialized, skeptical "critic" persona. This critic's sole purpose is to identify potential flaws, unstated assumptions, and risks in the plan. This principle acts as an automated "red team" review for the AI's own logic.

#### 2.2.2. Data Contract Validation
In addition to adversarial validation, all core data contracts, such as the `ExecutionPlan`, are enforced at runtime using Pydantic models. This provides an immediate, deterministic validation layer that rejects malformed plans. The system heavily utilizes the `instructor` library to force the LLM's output to conform to these Pydantic schemas, drastically reducing the likelihood of syntactically invalid plans and increasing overall system robustness.

### 2.3. Explicit Governance
The behavior and structure of the persona ecosystem are governed by a set of explicit, machine-readable rules. This includes persona integrity checks, data contract validation, and deterministic plan validation against rules defined in `governance.yml`.

#### 2.3.1. Persona Integrity
All personas are validated against the rules in `persona_config.yml`, and a cryptographically signed `persona_manifest.yml` ensures the application's runtime understanding of its capabilities is never out of sync with the committed source code.

#### 2.3.2. Data Contract Integrity
The system's internal data contracts are programmatically enforced through a "Documentation-as-Code" pattern, where a central governance file (`governance.yml`) and documentation templates serve as the single source of truth for generating both runtime rules and user-facing documentation.

#### 2.3.3. Deterministic Plan Validation
To mitigate the inherent unreliability of probabilistic AI planners, the system MUST employ a deterministic validation layer. This layer operates between the AI Planner and the Execution Engine. Before planning, a deterministic function analyzes the user's prompt against rules in `governance.yml` to create an "Expected Plan Signature." After the AI generates a plan, a second deterministic function validates the plan against this signature. Non-compliant plans are rejected, and the AI is forced to retry with corrective feedback. This process is further hardened by the use of a structured generation library (`instructor`) in the Planner, which forces the LLM's output to conform to the `ExecutionPlan`'s Pydantic schema, drastically reducing the likelihood of syntactically invalid plans.

### 2.4. Documentation-as-Code
The project mandates a "Documentation-as-Code" pattern to prevent drift between documentation, runtime artifacts, and core configuration. A single, human-readable source of truth (typically a YAML or Markdown file) MUST be used to programmatically generate related artifacts. This is enforced by the CI pipeline.

**Canonical Examples:**
1.  **Data Schemas:** `docs/system_contracts.yml` is used by `scripts/generate_schemas.py` to create the JSON Schema files used for runtime validation by the `executor`.
2.  **User Guides:** `governance.yml` and `default_config.yml` are used by `scripts/generate_docs.py` to inject up-to-date keywords and model names into user-facing documentation like `prompting_guide.md`.
3.  **Persona Manifest:** The individual `.persona.md` files are the source of truth used by `scripts/generate_manifest.py` to create the signed, machine-readable `persona_manifest.yml` used at runtime.


---

## 3. Persona Directory & Chain of Command

The persona ecosystem is a team of specialists with a clear, hierarchical structure.

-   **`_mixins/` & ``_base/` (Foundations):** These are the architectural foundations. `_mixins` provide shared directives (like coding standards), while `_base` personas define the core archetypes for agent behavior.
    -   `_base/bcaa-1` (Base Collaborative Agent): The archetype for interactive, conversational agents that propose plans and seek confirmation.
    -   `_base/btaa-1` (Base Technical Analysis Agent): The archetype for non-interactive, "one-shot" analytical agents.
    -   `_base/developer-agent-1` (Base Professional Developer Agent): A crucial archetype that inherits from `bcaa-1` and adds a non-negotiable protocol for safe software development. All specialist personas that modify code MUST inherit from this base.

-   **`core/` (The Orchestrators & Governors):** This directory is reserved exclusively for "meta-governance" and "orchestration" personas. These are agents that manage the AI Assistant *itself* or the workflow between other agents.

-   **`domains/` (The Specialists):** This is the primary location for all specialist agents that perform concrete, domain-specific tasks. The ecosystem is designed to be scaled by adding new experts to this directory (e.g., `programming/`, `writing/`).

---

## 4. The Kernel-Driven Workflow Expansion Pattern


To ensure maximum reliability and to simplify the AI Planner's task, the system uses a **Kernel-Driven Workflow Expansion Pattern** for all complex, multi-step operations.

Instead of asking the AI to generate a long and potentially fragile sequence of granular tools (e.g., `git_create_branch`, `write_file`, `git_add`), the system instructs the AI to generate a single, high-level "workflow" step (e.g., `execute_refactoring_workflow`).

The `kernel` is designed to **intercept** these specific workflow steps before execution. It then performs the following sequence:
1.  It extracts the high-level intent and arguments from the single step (e.g., "refactor these files with these instructions").
2.  It performs all necessary non-deterministic "thinking" itself. For a refactoring task, this is where it calls the LLM to generate the new, modified code content.
3.  It then **dynamically replaces** the original single workflow step with a new, fully deterministic sequence of granular tool calls (e.g., `git_create_branch`, `write_file` with the newly generated content, `git_add`, `git_commit`).

This pattern provides three major architectural advantages:
-   **Centralized Logic:** All complex, LLM-dependent logic is centralized in the `kernel`, not scattered across various tools.
-   **Consistency:** Live Execution Mode and Output-First Mode are guaranteed to use the exact same code generation logic, eliminating behavioral drift between the two workflows.
-   **Simplified Planning:** The AI Planner's task is simplified to producing a high-level, one-step plan, which is a much easier and more reliable task for an LLM than creating a complex, multi-step sequence.

**Canonical Rule:** Personas responsible for code modification (i.e., those inheriting from `_base/developer-agent-1`) **MUST** be instructed to use the appropriate high-level workflow tool in a single-step plan.
---

## 5. Extensibility: The Knowledge and Context Architecture

The system's knowledge architecture is now fully realized in the Three-Tiered model.

### 5.1. The Context Plugin System (Static Knowledge)
This system is for injecting pre-defined, static knowledge based on simple triggers.

-   **Core Contract:** All plugins MUST inherit from the `ContextPluginBase` class and implement its `get_context` method.
-   **Discovery and Loading:**
    -   **Built-in Plugins:** Registered via `entry_points` in `pyproject.toml`.
    -   **Local Project Plugins:** Discovered at runtime from the `.ai/plugins/` directory within the user's project.
-   **Activation Logic:**
    -   **Automatic Loading:** A persona from `domains/<name>/...` automatically triggers loading of a plugin named `domains-<name>`.
    -   **Manual Override:** The `--context` CLI flag overrides any automatically selected plugin.

### 5.2. The RAG Pipeline (Dynamic Knowledge via The Librarian Service)
This system provides the Conductor with deep, codebase-aware knowledge. The architecture is a **CI/CD-driven, centralized database model.**

-   **Architecture:** The resource-intensive indexing process is decoupled from consumption. A CI/CD pipeline populates a central database, which is then queried by the central Librarian service on behalf of all thin clients.
-   **Indexing (CI/CD via `ai-index`):** The `ai-index` command is executed within a Product's CI/CD pipeline. It scans the source code, generates vector embeddings, and connects to a **central PostgreSQL database** to populate a unique, project-and-branch-specific table. Finally, it uploads a small `index_manifest.json` to a shared cloud object store (OCI).
-   **Retrieval (The Librarian Service):** The standalone Librarian service is the sole query engine.
    1.  **Manifest Consumption:** On startup, it is configured for a specific project/branch and downloads the corresponding `index_manifest.json` from OCI to discover which database table to use.
    2.  **Model Loading:** It loads the necessary embedding and reranking models.
    3.  **API Endpoint:** It exposes a secure `/api/v1/context` endpoint.
    4.  **Query Processing:** It receives API requests from clients, connects to the PostgreSQL database, executes the `pgvector` similarity search, performs reranking, and returns the final context.
-   **Client-Side Consumption (The Conductor):** The Conductor's `RAGContextPlugin` is a lightweight API client. It makes an authenticated HTTP request to the configured Librarian service. It contains **no models or database clients**.
---

## 6. Workflows

The system supports four primary workflows:

### 6.1. Live System Check Workflow
For read-only diagnostics on a live system with real-time user confirmation.

### 6.2. Two-Stage Local Workflow
For making changes to the local file system via a sandboxed "Output Package" and the `ai-execute` script.

### 6.3. Handoff Workflow (Brain-to-Hands)
For preparing changes to be executed by a powerful, external agent.

### 6.4. Codebase-Aware Analysis Workflow (RAG)
The standard flow is now a fully decoupled, multi-project capable, database-centric model:
1.  **Index (Automated per Project):** A developer pushes a commit to a Product repository (e.g., `my-ai-assistant` or `librarian-service`). The CI/CD pipeline in *that specific repository* runs the `ai-index` command. The command connects to the central PostgreSQL database, populates a unique table for that project and branch (e.g., `codebase_collection_librarian_service_develop`), and uploads a small `index_manifest.json` to a shared OCI bucket.
2.  **Serve (Centralized):** The standalone Librarian service is configured to serve a specific project's index. On startup, it downloads the relevant manifest from OCI to discover which table to query in the central database.
3.  **Query (Any Machine):** A developer runs an `ai "..."` command. The `RAGContextPlugin` in the Conductor makes a lightweight API call to the configured Librarian service, which returns the relevant context.

#### 6.5. The RAG Index Data Lifecycle

The lifecycle is now a robust, database-centric ETL (Extract, Transform, Load) process, fully automated by CI/CD. It is split between the Producer (the CI/CD pipeline for a given project) and the Consumer (the central Librarian service).

**Stage 1: Local Development (The Change)**
*   A developer makes changes to the source code of a Product repository (e.g., `my-ai-assistant` or `librarian-service`).
*   This includes adding new files, modifying existing functions, or deleting obsolete code.
*   The developer commits these changes to a local Git branch.

**Stage 2: Git Push (The Trigger)**
*   The developer pushes the commit(s) to a tracked branch on the remote repository (e.g., `git push origin develop`).
*   This push event is the trigger that initiates the entire automated indexing pipeline.

**Stage 3: Indexing (CI/CD Environment)**
*   A CI/CD workflow (e.g., GitHub Actions) in the Product's repository is triggered by the push.
*   The workflow checks out the specific commit of the Product's source code.
*   It runs the `ai-index` command, which connects to the **central PostgreSQL database** via a secure `DATABASE_URL`.
*   The indexer script intelligently compares the current state of the code against its last known state (from a downloaded `state.json` file).
*   It performs targeted `DELETE` and `INSERT` operations to synchronize the data in a project-and-branch-specific table (e.g., `codebase_collection_my_ai_assistant_develop`) with the new state of the codebase.

**Stage 4: Manifest Publication (Cloud Object Storage)**
*   After the database update is complete, the CI/CD workflow generates two critical artifacts:
    1.  `index_manifest.json`: A file containing metadata about the index, most importantly the name of the PostgreSQL table (`db_table_name`).
    2.  `state.json`: A file containing the hashes of all indexed files, used for efficient incremental updates on the next run.
*   These small JSON files are uploaded to a project-and-branch-specific path in the central OCI bucket (e.g., `indexes/my-ai-assistant/develop/latest/`).

**Stage 5: Consumption (Librarian Service)**
*   The central Librarian service is configured to serve a specific project and branch.
*   On startup or restart, it downloads the corresponding `index_manifest.json` from OCI.
*   It reads the `db_table_name` from the manifest, connects to the central PostgreSQL database, and is now ready to serve queries against the correct, up-to-date data for that project.
---

## 7. Data & State Contracts

The system relies on several key data contracts, with detailed schemas defined in `docs/system_contracts.yml`.

### 7.1. The Output Package
A standardized directory (`manifest.json`, `workspace/`, `summary.md`) generated in the Two-Stage Workflow. Its structure is formally defined and programmatically enforced.

### 7.2. The Project State File
The `PROJECT_STATE.md` file is the single source of truth for a long-running, multi-agent project, managed by the `pmo-1` persona.

---

## 8. Build System & Packaging Philosophy

The project adheres to modern Python packaging standards using `pyproject.toml`.

### 8.1. Packaging of Non-Python Data
*(This section remains the same)*

### 8.2. Optional Dependencies for a Decoupled World
The packaging philosophy now reflects the Three-Tiered architecture.
-   **Standard Installation (`pip install .`):** Installs the **thin client** Conductor. It is lightweight and does not include any heavy ML or database libraries. This is the standard for all developers.
-   **`[project.optional-dependencies].indexing`:** This group is for the **CI/CD environment only**. It installs the base Conductor package *plus* all the heavy libraries (`torch`, `sentence-transformers`, `sqlalchemy`, `psycopg2-binary`, `pgvector`, `oci`) required for the `ai-index` command to connect to the database and build the knowledge base.
---

## 9. Project Management & State
**NEW:** To manage a portfolio of complex, multi-phase, AI-driven tasks, the project uses a "PMO-as-Code" (Project Management Office as Code) system.

### 9.1. The PMO Directory
The single source of truth for all project management is the `.ai_pmo/` directory at the project root.

-   **`.ai_pmo/PROGRAM_STATE.md`**: This is the master portfolio dashboard. It provides a high-level, at-a-glance view of all active and planned projects, their status, and their priority.
-   **`.ai_pmo/projects/`**: This directory contains the detailed "Project Charters" for each individual initiative (e.g., `P-001_JULES_INTEGRATION.md`).

### 9.2. The Project Charter
Each project charter is a Markdown file that serves as the complete, version-controlled plan for a specific initiative. It defines the goal, the multi-phase roadmap, the specialist personas assigned to each phase, and the current status.

### 9.3. Control Mechanism
The `core/pmo-1` persona is the designated agent responsible for maintaining the integrity of the PMO system. All status updates to the program dashboard and project charters should be performed by this persona to ensure consistency.

## 10. Governance for the RAG Indexing Pipeline

The CI/CD-driven RAG pipeline is critical infrastructure. Its integrity is paramount. The following governance rules are enforced to prevent silent failures and ensure the completeness of the knowledge base.

### 10.1. Index Scope and Isolation
The indexer's scope MUST be strictly limited to the target project's version-controlled source code. To enforce this:

1.  **Tool Self-Exclusion:** When the AI Assistant's source code is checked out into the target project (the "Tool-in-Project" pattern), its directory (`my-ai-assistant/`) **MUST** be added to the dynamic `.aiignore` file at runtime.
2.  **CI Artifact Exclusion:** All transient files created by the CI workflow itself (e.g., `indexer_run.log`, `index.tar.gz`, `before_state.json`) **MUST** be added to the dynamic `.aiignore` file at runtime to prevent feedback loops.

### 10.2. Curation via `.aiignore` Best Practices
The project-level `.aiignore` file is a powerful tool for curation, but it carries the risk of silent data exclusion.

-   **Favor Specificity:** Broad, ambiguous patterns (e.g., `data/`, `config/`) are forbidden. Patterns MUST be as specific as possible.
-   **Anchor to Root:** For top-level directories, always anchor the pattern with a leading and trailing slash (e.g., `/market_data/`) to avoid accidentally matching subdirectories with the same name.
-   **Use Extension-Based Ignores:** For non-code files scattered throughout the repository (e.g., datasets), prefer ignoring by extension (`*.csv`, `*.parquet`) over directory patterns.

### 10.3. CI Sanity Checks
To protect against silent failures from overly aggressive ignore patterns, the CI workflow **MUST** include a "Sanity Check" step after a successful indexing run. This step will parse the final `state.json` and fail the build if the total number of indexed files falls below a project-specific, reasonable threshold. This ensures that a misconfiguration cannot result in an empty or incomplete knowledge base being deployed.

### 10.4. The Index Manifest as the Integration Contract

To prevent configuration drift between the Producer (CI/CD) and the Consumer (Librarian), the system **MUST** treat the `index_manifest.json` file as the immutable, single source of truth for a given index artifact.

The Producer (`ai-index`) is responsible for writing the following critical metadata into the manifest:
*   `embedding_model`: The exact name of the sentence-transformer model used.
*   `db_table_name`: The exact name of the unique PostgreSQL table containing the data for this project and branch.
*   `branch`: The source control branch the index was built from.

The Consumer (Librarian) **MUST** read these values from the manifest upon startup and use them to configure its runtime behavior.

### 10.5. Data Isolation in the Central Database
To support multiple projects concurrently, data isolation is mandatory.

-   **Table Naming Convention:** The `ai-index` script **MUST** generate a unique table name for each project and each branch. The canonical naming scheme is: `<base_collection_name>_<sanitized_project_name>_<sanitized_branch_name>`.
    -   Example for `my-ai-assistant`'s `develop` branch: `codebase_collection_my_ai_assistant_develop`.
    -   Example for `librarian-service`'s `feature/new-auth` branch: `codebase_collection_librarian_service_feature_new_auth`.
-   **Database Permissions:** It is highly recommended to use a single database user (`llm_app`) with `CREATE` and `USAGE` privileges on the public schema of a dedicated database (`llm_indexing`). This user can manage all project tables within that single database, simplifying connection management.

## 11. Governance for RAG Pipeline Integrity & Testing

The project formally recognizes that ensuring the health and effectiveness of the RAG pipeline is a distinct engineering discipline, separate from traditional software testing. A successful execution of the Python codebase (e.g., passing all unit tests) does not guarantee the success or relevance of the knowledge base it produces.

This distinction can be understood through an analogy:
-   **Code Correctness (The Mechanic):** Traditional testing ensures the machinery works. Does the engine start? Do the wheels turn? This is the domain of `unittest`, linters, and static analysis.
-   **Knowledge Relevance (The Librarian):** RAG pipeline testing ensures the quality of the library's content and the skill of the research assistant. Are the books relevant? Is the card catalog accurate? Can the assistant find the right passage to answer a complex question?

To govern this second discipline, the project mandates the following RAG Pipeline Testing Protocol.

### 11.1. The RAG Pipeline Testing Protocol

This protocol is a set of required checks and evaluations designed to monitor and validate the entire lifecycle of the RAG knowledge base, from creation to consumption.

#### 11.1.1. Health & Robustness (Is the library open and the catalog intact?)
This layer ensures the data pipeline is functional and complete.

-   **CI Sanity Check:** The `smart-indexing.yml` workflow **MUST** include a "Sanity Check" step after every indexing run. This step parses the final `state.json` and **MUST** fail the build if the total number of indexed files falls below a project-specific, reasonable threshold. This is a critical guardrail against silent failures caused by overly aggressive `.aiignore` patterns.
-   **Data Pipeline Integrity:** The indexing and retrieval processes **MUST** be robust against common data errors, such as unreadable files or transient network failures, failing gracefully without crashing the entire system.

#### 11.1.2. Effectiveness (Can the assistant find the right information?)
This layer measures the *quality* and *relevance* of the RAG system's output. It serves as a regression test for the knowledge base itself.

-   **The "Golden Set" Evaluation:** The project **MUST** maintain a curated "golden set" of questions and expected outcomes in a version-controlled file (e.g., `tests/rag_evaluation_set.yml`). This set represents the core knowledge the RAG system is expected to possess.
-   **Automated Evaluation:** An automated script (`scripts/evaluate_rag.py`) **MUST** be created to test the RAG pipeline against this golden set. This script will programmatically query the RAG system and measure key metrics, including:
    -   **Retrieval Precision:** Did the retrieved context chunks originate from the expected source files?
    -   **Context Relevance:** Did the content of the retrieved chunks contain the expected keywords or concepts?
-   **CI Quality Gate:** The automated evaluation script **MUST** be run as a job in the CI pipeline after a new index is built. A drop in precision or relevance below a defined threshold **MUST** fail the build. This prevents the deployment of a "dumber" or less effective version of the RAG system.

#### 11.1.3. Efficiency (How fast and expensive is the library?)
This layer monitors the performance and resource consumption of the RAG pipeline to prevent regressions.

-   **Indexing Time:** The duration of the `smart-indexing.yml` workflow **SHOULD** be monitored over time to detect significant performance degradations.
-   **Retrieval Latency:** The "Golden Set" evaluation script **SHOULD** measure and report the average query-to-context latency to ensure a responsive user experience.
-   **Resource Footprint:** The size of the final `index.tar.gz` archive and the client-side memory usage **SHOULD** be monitored to manage costs and resource requirements.
