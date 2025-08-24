# PROJECT ROADMAP: AI Assistant

<!-- Status: As of 2024-05-24 -->

This document outlines the strategic development roadmap for the AI Assistant project.

---

## ✅ Done (Key Milestones Achieved)

| Feature ID | Description | Status | Notes |
| :--- | :--- | :--- | :--- |
| **CORE-001** | Establish Core Kernel & Planner | ✅ Done | The foundational agent loop is stable. |
| **CORE-002** | Implement Persona System | ✅ Done | `PersonaLoader` supports inheritance and local overrides. |
| **CORE-003** | Two-Stage Workflow & Executor | ✅ Done | `ai-execute` provides a robust safety layer. |
| **GOV-001** | Documentation-as-Code Pipeline | ✅ Done | `generate_docs.py` and `generate_manifest.py` are in CI. |
| **GOV-002** | Deterministic Plan Validation | ✅ Done | `plan_validator.py` enforces `governance.yml` rules. |
| **EXT-001** | Context Plugin System | ✅ Done | Supports built-in and local project plugins. |
| **ROB-001** | Enhance System Robustness | ✅ Done | Fixed critical bugs in output package generation and planner failure modes. |
| **RAG-001** | Formalize RAG Pipeline | ✅ Done | RAG is a first-class citizen via `RAGContextPlugin`. |
| **SCALE-001** | Improve Portability & Scalability | ✅ Done | Implemented hybrid client-server RAG architecture and optional dependencies for lightweight client installs. |

---

## 🚀 Next Up (In Progress or Actively Planned)

| Feature ID | Description | Priority | Status |
| :--- | :--- | :--- | :--- |
| **GOV-003** | Unify All Governance Files | 🔴 High | **Planning.** Consolidate `prompt_analysis_rules.yml` into `governance.yml` to create a single source of truth for all prompt and plan validation. |
| **MET-001** | Centralized Token Management | 🟡 Medium | **Backlog.** Implement a `TokenManager` class to provide consistent tracking and budgeting of token usage across all agent phases. |
| **UI-001** | Enhance CLI User Experience | 🟡 Medium | **Backlog.** Improve argument parsing, help messages, and interactive prompts. |
| **ROB-002** | Implement Circuit Breakers | 🟢 Low | **Backlog.** Add circuit breakers to tools and API calls to prevent repeated failures on transient issues. |

---

## 🔭 Future Vision (Under Consideration)

| Feature ID | Description |
| :--- | :--- |
| **STATE-001** | Advanced Session State Management |
| **OBS-001** | Structured Observability & Tracing |
| **TOOL-001** | Dynamic Tool Generation |
| **UI-002** | Interactive GUI/Web Interface |