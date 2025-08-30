# PROJECT BLUEPRINT: AI Assistant

<!-- Version: 2.7 -->
<!-- Change Summary (v2.7): Documented the hybrid client-server RAG architecture and the use of optional dependencies for flexible, environment-specific installations. -->

## 1. System Overview and Core Purpose

This document is the canonical source of truth for the architectural principles and governance of the AI Assistant project. It serves as a "constitution" for human developers and a "README for the AI," ensuring that all development and AI-driven actions are aligned with the core design philosophy.

The system is a command-line-native, persona-driven agent designed to assist with software development and other knowledge-work tasks. Its primary purpose is to provide a safe, reliable, and extensible framework for leveraging Large Language Models to perform complex, multi-step operations, **now enhanced with a codebase-aware RAG pipeline for deep project analysis.**

---

## 2. Core Architectural Principles

The architecture is built on three foundational principles:

### 2.1. Persona-First Operation
The primary interface for quality and control is the **Persona System**. All complex tasks should be initiated through a specialized persona. This ensures that AI behavior is constrained, predictable, and follows a proven operational protocol.

### 2.2. Decoupled Thinking and Doing
A strict separation is maintained between **AI-driven analysis (thinking)** and **deterministic execution (doing)**. This principle is enforced through two primary operational modes:

-   **Live Execution Mode:** This is the default interactive workflow. The `kernel` orchestrates the entire process: planning, adversarial validation, and step-by-step execution of deterministic tools. It includes a critical safety gate where the user **MUST** provide explicit confirmation before any risky action (e.g., writing a file) is performed.

-   **Output-First Mode:** This workflow is designed for generating reviewable change packages, ideal for asynchronous or automated environments. The AI's final output is a standardized "Output Package" containing a manifest of deterministic actions (`manifest.json`) and all necessary files. A separate, non-AI `executor` script (`ai-execute`) is then used to safely and predictably apply these changes to the system.

Both modes rely on the same underlying planning and validation chain to ensure consistency.

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

To enhance the AI's domain-specific knowledge, the system uses a modular, two-tiered architecture for context injection.

### 5.1. The Context Plugin System (Static Knowledge)
This system is for injecting pre-defined, static knowledge based on simple triggers.

-   **Core Contract:** All plugins MUST inherit from the `ContextPluginBase` class and implement its `get_context` method.
-   **Discovery and Loading:**
    -   **Built-in Plugins:** Registered via `entry_points` in `pyproject.toml`.
    -   **Local Project Plugins:** Discovered at runtime from the `.ai/plugins/` directory within the user's project.
-   **Activation Logic:**
    -   **Automatic Loading:** A persona from `domains/<name>/...` automatically triggers loading of a plugin named `domains-<name>`.
    -   **Manual Override:** The `--context` CLI flag overrides any automatically selected plugin.

### 5.2. The RAG Pipeline (Dynamic Knowledge)
This system provides the assistant with deep, codebase-aware knowledge by dynamically retrieving the most relevant information from a project-specific knowledge base. It is designed for a robust, automated, and scalable team environment.

-   **Architecture:** The system uses a **CI/CD-driven, cloud-cached model**. A central, automated process builds the knowledge base, which is then distributed to lightweight clients via cloud object storage. This decouples the resource-intensive indexing process from the day-to-day client usage.
-   **Indexing (CI/CD via GitHub Actions):** The `ai-index` command is executed within a CI/CD pipeline (e.g., GitHub Actions) upon every code push. It scans the project, chunks source code, and creates a branch-specific vector database. This index is then packaged and uploaded to a shared cloud object store (e.g., OCI Object Storage).
-   **Retrieval, Reranking, and Caching (Client-Side):** The built-in `RAGContextPlugin` is activated automatically. The client-side process involves multiple stages for maximum accuracy and performance:
    1.  **Smart Caching:** On first run, or when its local cache is expired, the client automatically downloads the latest index for the current branch from the cloud. Subsequent runs use the local cache for speed.
    2.  **Initial Retrieval:** The plugin performs a broad semantic search against the local vector database, retrieving a larger set of potentially relevant documents (`retrieval_n_results`).
    3.  **Second-Stage Reranking:** To improve precision, these initial results are passed to a more sophisticated CrossEncoder model (`reranker.py`). This model re-evaluates and re-scores the documents specifically against the user's query, pushing the most relevant results to the top.
    4.  **Final Selection:** The system selects the top N documents (`rerank_top_n`) from the reranked list.
-   **Injection:** The final, highly-relevant code chunks are automatically injected into the prompt, providing the AI with on-the-fly context for its analysis.
-   **Curation:** The knowledge base can be precisely controlled by adding file and directory patterns to a project-local `.aiignore` file, which is respected by the CI/CD indexing process.

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
For performing complex analysis on a large codebase. The standard flow is now fully automated:
1.  **Index (Automated):** A developer pushes a commit. The CI/CD pipeline automatically runs `ai-index` and uploads the branch-specific knowledge base to cloud storage.
2.  **Configure (One-Time Setup):** A developer configures their local `.ai_config.yml` to point to the shared cloud storage bucket.
3.  **Query (Any Machine):** A developer runs an `ai "..."` command. The `RAGContextPlugin` automatically ensures a fresh, local copy of the index is present (downloading it if necessary) and injects the relevant context into the prompt.

#### 6.5. The RAG Index Data Lifecycle

The codebase-aware RAG system operates on a robust, automated data lifecycle that ensures all clients have access to a fresh, relevant index without manual intervention. The flow is triggered by developer actions in Git and managed by the CI/CD pipeline.

The lifecycle consists of five distinct stages:

**Stage 1: Local Development (Developer's Machine)**
*   A developer writes or modifies code in their local Git repository. This is the source of all new information.

**Stage 2: The Trigger (Git Push)**
*   The entire automated workflow is triggered when a developer executes a `git push` to a tracked branch on the remote repository (e.g., GitHub).

**Stage 3: Indexing (CI/CD Environment)**
*   The push event activates the `smart-indexing.yml` GitHub Actions workflow.
*   The CI/CD runner checks out the specific commit.
*   It runs the `ai-index` command, which scans the repository, chunks the code, and builds a complete, self-contained vector database in the `.ai_rag_index/` directory.

**Stage 4: Centralization (Cloud Object Storage)**
*   The CI/CD workflow compresses the entire `.ai_rag_index/` directory into a `index.tar.gz` file.
*   This archive is uploaded to the central OCI Object Storage bucket. Two copies are stored:
    1.  `indexes/<branch>/latest/index.tar.gz`: This file is **overwritten** on every push, always representing the absolute latest version for that branch.
    2.  `indexes/<branch>/archive/<timestamp>_<commit>.tar.gz`: A new, timestamped file is created for **historical auditing and debugging**. These are automatically deleted after a set period by a bucket lifecycle policy.

**Stage 5: Consumption (Client Machine)**
*   A developer runs an `ai "..."` command on their local machine.
*   The `RAGContextPlugin` activates and checks its local cache (`.ai_rag_index/.cache_state.json`).
*   **If the cache is fresh** (within the configured TTL), it uses the existing local database instantly.
*   **If the cache is stale or missing**, the plugin connects to OCI, downloads `latest/index.tar.gz` for the current Git branch, unpacks it, and updates its cache state.
*   The plugin then queries this fresh, local database to provide context to the LLM.

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
To ensure absolute build and installation reliability for non-Python data files (e.g., personas, schemas), this project uses the `[tool.setuptools.package-data]` directive within `pyproject.toml`. This is a deliberate engineering choice to use modern, standardized packaging practices for explicit and deterministic control over packaged data.

**Canonical Rule:** Any new non-Python data files that must be accessible by the installed package **MUST** be added to the `[tool.setuptools.package-data]` configuration in `pyproject.toml` to guarantee their inclusion.

### 8.2. Optional Dependencies for Flexibility

To support different operational environments (e.g., a powerful indexing server vs. a developer laptop), the project uses **optional dependencies**.

-   **`[project.optional-dependencies].indexing`:** This group includes heavy libraries required for creating the RAG index (e.g., `torch`, `sentence-transformers`). It should only be installed on the machine responsible for indexing.
-   **`[project.optional-dependencies].client`:** This group includes libraries for querying a remote RAG index. This is the recommended installation for most users.

**Architectural Note:** The current `[client]` installation is not fully "lightweight" as it requires `sentence-transformers` (and its dependency, `torch`) to perform query embedding and reranking on the client machine. While this ensures maximum flexibility, it introduces a significant installation footprint. A future architectural goal is to offload query embedding to a remote service, which would allow for a truly minimal client dependency set.
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
