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

### 2.2. Decoupled Execution
A strict separation is maintained between **AI-driven analysis (thinking)** and **deterministic execution (doing)**. The AI's primary output for any task that modifies the system is a reviewable "Output Package." A separate, non-AI `executor` script then applies these changes. This provides a critical safety layer and enhances auditability.

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

## 4. The Workflow Tool Pattern


To ensure maximum reliability and to simplify the AI Planner's task, the system favors a **Workflow Tool Pattern** for all complex, multi-step operations.

Instead of asking the AI to generate a complex sequence of granular tools (e.g., `git_create_branch`, `refactor_file_content`, `git_add`), the system provides a single, powerful "workflow tool" (e.g., `execute_refactoring_workflow`) that encapsulates the entire best-practice sequence in deterministic Python code.

**Canonical Rule:** Personas responsible for code modification (i.e., those inheriting from `_base/developer-agent-1`) **MUST** be instructed to use the appropriate high-level workflow tool in a single-step plan. To enforce this, personas MUST also be explicitly instructed on the tool's argument schema (e.g., providing a single string for instructions) to safeguard against the AI inventing incompatible data structures.

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
-   **Retrieval (Client-Side Smart Caching):** The built-in `RAGContextPlugin` is activated automatically. On first run, or when its local cache is expired, it automatically downloads the latest index for the current branch from the cloud. Subsequent runs use the local cache for speed.
-   **Injection:** The retrieved code chunks are automatically injected into the prompt, providing the AI with highly relevant, on-the-fly context.
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
To support different operational environments (e.g., a powerful indexing server vs. a lightweight developer laptop), the project uses **optional dependencies**.

-   **`[project.optional-dependencies].indexing`:** This group includes heavy libraries required for creating the RAG index (e.g., `torch`, `sentence-transformers`). It should only be installed on the machine responsible for indexing.
-   **`[project.optional-dependencies].client`:** This group includes lightweight client libraries for querying a remote RAG index. This is the recommended installation for most users.

This approach minimizes installation footprint and resource consumption on client machines, adhering to the principle of least privilege for dependencies.

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