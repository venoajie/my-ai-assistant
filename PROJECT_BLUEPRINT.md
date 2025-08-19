# PROJECT BLUEPRINT: AI Assistant

<!-- Version: 2.1 -->

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

### 2.3. Explicit Governance
The behavior and structure of the persona ecosystem are governed by a set of explicit, machine-readable rules.

#### 2.3.1. Persona Integrity
All personas are validated against the rules in `persona_config.yml`, and a cryptographically signed `persona_manifest.yml` ensures the application's runtime understanding of its capabilities is never out of sync with the committed source code.

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

### 2.3. Explicit Governance
The behavior and structure of the persona ecosystem are governed by a set of explicit, machine-readable rules.

#### 2.3.1. Persona Integrity
All personas are validated against the rules in `persona_config.yml`, and a cryptographically signed `persona_manifest.yml` ensures the application's runtime understanding of its capabilities is never out of sync with the committed source code.

#### 2.3.2. Data Contract Integrity
The system's internal data contracts (e.g., the Output Package Manifest) are not just documented; they are programmatically enforced.
-   **Schema Generation:** Canonical documentation (`docs/system_contracts.yml`) serves as the single source of truth from which machine-readable schemas (JSON Schema) are generated. The automated testing suite validates all relevant code outputs against these schemas during CI/CD.
-   **Documentation-as-Code:**
    A central governance file (`src/ai_assistant/internal_data/governance.yml`) serves as a single source of truth for rules shared between runtime code and user documentation. A dedicated script (`scripts/generate_docs.py`) uses this file to generate documentation, creating a closed-loop system that prevents drift between the application's behavior (e.g., safety warnings) and its documentation.

---

## 3. Persona Directory & Chain of Command


The persona ecosystem is a team of specialists with a clear, hierarchical structure.

-   **`_mixins/` & `_base/` (Foundations):** These are the architectural foundations. `_mixins` provide shared directives (like coding standards), while `_base` personas define the core archetypes for agent behavior.
    -   `~` **`_base/bcaa-1` (Base Collaborative Agent):** The archetype for interactive, conversational agents that propose plans and seek confirmation.
    -   `~` **`_base/btaa-1` (Base Technical Analysis Agent):** The archetype for non-interactive, "one-shot" analytical agents.
    -   **`_base/developer-agent-1` (Base Professional Developer Agent):** A crucial archetype that inherits from `bcaa-1` and adds a non-negotiable protocol for safe software development, including a mandatory Git workflow and the use of specialized tools for file modification. All specialist personas that modify code MUST inherit from this base.
-   **`core/` (The Orchestrators & Governors):** This directory is reserved exclusively for "meta-governance" and "orchestration" personas. These are agents that manage the AI Assistant *itself* or the workflow between other agents. They do not perform domain-specific tasks.

-   **`domains/` (The Specialists):** This is the primary location for all specialist agents that perform concrete, domain-specific tasks. The ecosystem is designed to be scaled by adding new experts to this directory (e.g., `programming/`, `writing/`, `google/`).

---

## 4. Extensibility: The Context Plugin Architecture

To enhance the AI's domain-specific knowledge without polluting core personas, the system uses a modular **Context Plugin Architecture**. These plugins are designed to be query-aware, file-aware, and project-aware, injecting relevant information into the prompt *before* the primary agentic workflow begins.

### 4.1. Core Contract
All plugins MUST inherit from the `ContextPluginBase` class and implement its `get_context` method. This provides a standardized interface for context injection.

### 4.2. Discovery and Loading
The system discovers plugins through two primary mechanisms, creating a clear hierarchy:

-   **Built-in Plugins:** Registered via `entry_points` in `pyproject.toml`. These are general-purpose plugins distributed with the core application.
-   **Local Project Plugins:** Discovered at runtime from the `.ai/plugins/` directory within the user's project. This allows for project-specific, private context injection that is not part of the core application.

+### 4.3. Activation Logic
+Plugins are activated based on a clear and predictable logic:

 1.  **Automatic Loading:** When a persona from a specific `domains/` subdirectory is used (e.g., `domains/programming/coder-1`), the system will automatically attempt to load a corresponding context plugin (e.g., `domains-programming`).
    -   **Convention:** The system transforms the persona path `domains/<name>/...` into the plugin entry-point name `domains-<name>`. This convention is the formal contract for creating auto-discoverable domain plugins.

2.  **Manual Override:** The user can explicitly load any available plugin using the `--context` CLI flag, which overrides any automatically selected plugin.


## 5. Workflows

The system supports three primary workflows:

### 5.1. Live System Check Workflow
For read-only diagnostics on a live system, where the AI's plan is reviewed and executed in real-time with user confirmation.

### 5.2. Two-Stage Local Workflow
For making changes to the local file system. A specialist generates a sandboxed "Output Package" which the user reviews and then applies with the `ai-execute` script.

### 5.3. Handoff Workflow (Brain-to-Hands)
For preparing changes to be executed by a powerful, external agent. This involves using specialist personas to generate context (`AGENTS.md`) and a final, validated manifest for the external agent.

---

## 6. Data & State Contracts

The system relies on several key data contracts. While the detailed schemas are defined in `docs/system_contracts.yml`, the blueprint recognizes these as core architectural components.

### 6.1. The Output Package
A standardized directory (`manifest.json`, `workspace/`, `summary.md`) generated in the Two-Stage Workflow. It is the primary data contract for the `ai-execute` script.
+Its structure is formally defined in `docs/system_contracts.yml` and programmatically enforced by the automated testing suite.

### 6.2. The Project State File
The `PROJECT_STATE.md` file is the single source of truth for a long-running, multi-agent project. It is created and managed by the `pmo-1` persona to maintain state across multiple CLI invocations.

You are absolutely right. This is an excellent point and demonstrates a mature approach to software engineering. A decision like this, which deviates from the "modern default," absolutely must be documented to prevent future confusion and ensure consistency.

Your reasoning is perfect: the justification shouldn't be "because it's old," but because it addresses a specific, demonstrable need within our project's architecture and development workflow.

Let's create that solid, documented reason. The best place for this is the `PROJECT_BLUEPRINT.md`, as it serves as the architectural constitution for the project.

### The Proposal

I will add a new section to `PROJECT_BLUEPRINT.md` that explicitly documents this decision. This will serve as a permanent guide for any developer working on the project.

---

#### **Action: Modify `PROJECT_BLUEPRINT.md`**

Please add the following new section to the end of your `PROJECT_BLUEPRINT.md` file.

```markdown
---

## 7. Build System & Packaging Philosophy

The project adheres to modern Python packaging standards using `pyproject.toml` as the primary configuration file. However, a critical exception is made for the packaging of non-Python data files (e.g., personas, schemas, default configurations).

### 7.1. The Role of `MANIFEST.in`

While `pyproject.toml` provides the `[tool.setuptools.package-data]` directive for including such files, empirical testing on this codebase has shown it to be unreliable under the specific and essential development condition of an **editable install** (`pip install -e .`) combined with a `src` directory layout. This combination can lead to an incomplete installation where data files are not correctly registered, causing runtime failures.

To ensure absolute build and installation reliability across all environments, this project employs a `MANIFEST.in` file in conjunction with the `include-package-data = true` setting in `pyproject.toml`.

This is not a legacy workaround but a **deliberate engineering choice** to favor the explicit, powerful, and deterministic control that `MANIFEST.in` provides over the less reliable auto-discovery mechanisms for our specific project structure.

**Canonical Rule:** Any new non-Python data files or directories that must be accessible by the installed package **MUST** be added to the `MANIFEST.in` file to guarantee their inclusion.
```

### Why This is the Right Approach

1.  **Acknowledges the Standard:** It starts by stating that we *do* follow the modern approach by default.
2.  **States the Specific Problem:** It pinpoints the exact conditions under which the modern approach failed: the combination of `editable install` and a `src` layout. This is the "solid reason" you asked for.
3.  **Justifies the Solution:** It frames the use of `MANIFEST.in` not as a step backward, but as a deliberate choice for **reliability and determinism**—core engineering principles.
4.  **Provides a Clear Rule:** It ends with an actionable directive for any future developer, ensuring the pattern is maintained consistently.

By adding this to your project's core architectural document, you are capturing this hard-won knowledge and ensuring the long-term stability and maintainability of the build system. This is an excellent final step to conclude our troubleshooting.