# PROJECT BLUEPRINT: AI Assistant

<!-- Version: 2.0 -->

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
The behavior and structure of the persona ecosystem are governed by a set of explicit, machine-readable rules in `persona_config.yml`. All personas are validated against these rules, and a cryptographically signed `persona_manifest.yml` ensures the application's runtime understanding of its capabilities is never out of sync with the committed source code.

---

## 3. Persona Directory & Chain of Command

The persona ecosystem is a team of specialists with a clear, hierarchical structure.

-   **`_mixins/` & `_base/` (Foundations):** These are the architectural foundations. `_mixins` provide shared directives (like coding standards), while `_base` personas define the core archetypes for agent behavior (e.g., collaborative vs. analytical). All specialist personas MUST inherit from a base persona.

-   **`core/` (The Orchestrators & Governors):** This directory is reserved exclusively for "meta-governance" and "orchestration" personas. These are agents that manage the AI Assistant *itself* or the workflow between other agents. They do not perform domain-specific tasks.

-   **`domains/` (The Specialists):** This is the primary location for all specialist agents that perform concrete, domain-specific tasks. The ecosystem is designed to be scaled by adding new experts to this directory (e.g., `programming/`, `writing/`, `google/`).

---

## 4. Workflows

The system supports three primary workflows:

### 4.1. Live System Check Workflow
For read-only diagnostics on a live system, where the AI's plan is reviewed and executed in real-time with user confirmation.

### 4.2. Two-Stage Local Workflow
For making changes to the local file system. A specialist generates a sandboxed "Output Package" which the user reviews and then applies with the `ai-execute` script.

### 4.3. Handoff Workflow (Brain-to-Hands)
For preparing changes to be executed by a powerful, external agent. This involves using specialist personas to generate context (`AGENTS.md`) and a final, validated manifest for the external agent.

---

## 5. Data & State Contracts

The system relies on several key data contracts. While the detailed schemas are defined in `docs/system_contracts.yml`, the blueprint recognizes these as core architectural components.

### 5.1. The Output Package
A standardized directory (`manifest.json`, `workspace/`, `summary.md`) generated in the Two-Stage Workflow. It is the primary data contract for the `ai-execute` script.

### 5.2. The Project State File
The `PROJECT_STATE.md` file is the single source of truth for a long-running, multi-agent project. It is created and managed by the `pmo-1` persona to maintain state across multiple CLI invocations.