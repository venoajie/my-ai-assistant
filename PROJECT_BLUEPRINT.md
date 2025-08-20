# PROJECT BLUEPRINT: AI Assistant

<!-- Version: 2.4 -->

## 1. System Overview and Core Purpose

This document is the canonical source of truth for the architectural principles and governance of the AI Assistant project. It serves as a "constitution" for human developers and a "README for the AI," ensuring that all development and AI-driven actions are aligned with the core design philosophy.

The system is a command-line-native, persona-driven agent designed to assist with software development and other knowledge-work tasks. Its primary purpose is to provide a safe, reliable, and extensible framework for leveraging Large Language Models to perform complex, multi-step operations.

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
In addition to adversarial validation, all core data contracts, such as the `ExecutionPlan`, are enforced at runtime using Pydantic models. This provides an immediate, deterministic validation layer that rejects malformed plans *before* they are even passed to the critic, increasing system robustness and preventing entire classes of errors.

### 2.3. Explicit Governance
The behavior and structure of the persona ecosystem are governed by a set of explicit, machine-readable rules.

#### 2.3.1. Persona Integrity
All personas are validated against the rules in `persona_config.yml`, and a cryptographically signed `persona_manifest.yml` ensures the application's runtime understanding of its capabilities is never out of sync with the committed source code.

#### 2.3.2. Data Contract Integrity
The system's internal data contracts are programmatically enforced through a "Documentation-as-Code" pattern, where a central governance file (`governance.yml`) and documentation templates serve as the single source of truth for generating both runtime rules and user-facing documentation.

#### 2.3.3. Deterministic Plan Validation
To mitigate the inherent unreliability of probabilistic AI planners, the system MUST employ a deterministic validation layer. This layer operates between the AI Planner and the Execution Engine. Before planning, a deterministic function analyzes the user's prompt against rules in `governance.yml` to create an "Expected Plan Signature." After the AI generates a plan, a second deterministic function validates the plan against this signature. Non-compliant plans are rejected, and the AI is forced to retry with corrective feedback. This process is further hardened by the use of a structured generation library (`instructor`) in the Planner, which forces the LLM's output to conform to the `ExecutionPlan`'s Pydantic schema, drastically reducing the likelihood of syntactically invalid plans.

---

## 3. Persona Directory & Chain of Command

The persona ecosystem is a team of specialists with a clear, hierarchical structure.

-   **`_mixins/` & `_base/` (Foundations):** These are the architectural foundations. `_mixins` provide shared directives (like coding standards), while `_base` personas define the core archetypes for agent behavior.
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

## 5. Extensibility: The Context Plugin Architecture

To enhance the AI's domain-specific knowledge, the system uses a modular **Context Plugin Architecture**.

### 5.1. Core Contract
All plugins MUST inherit from the `ContextPluginBase` class and implement its `get_context` method.

### 5.2. Discovery and Loading
-   **Built-in Plugins:** Registered via `entry_points` in `pyproject.toml`.
-   **Local Project Plugins:** Discovered at runtime from the `.ai/plugins/` directory within the user's project.

### 5.3. Activation Logic
-   **Automatic Loading:** A persona from `domains/<name>/...` automatically triggers loading of a plugin named `domains-<name>`.
-   **Manual Override:** The `--context` CLI flag overrides any automatically selected plugin.

---

## 6. Workflows

The system supports three primary workflows:

### 6.1. Live System Check Workflow
For read-only diagnostics on a live system with real-time user confirmation.

### 6.2. Two-Stage Local Workflow
For making changes to the local file system via a sandboxed "Output Package" and the `ai-execute` script.

### 6.3. Handoff Workflow (Brain-to-Hands)
For preparing changes to be executed by a powerful, external agent.

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


