# PROJECT ROADMAP: AI Assistant

This document outlines the planned epics and major features for future versions of the AI Assistant. It serves as a strategic guide for the project's evolution.

---

## Planned Epics & Features

### [EPIC-001]: Implement a "Tool-Aware" Adversarial Critic
-   **Problem:** The current Adversarial Critic is "stateless" and can produce "false alarm" critiques for powerful tools whose internal logic already mitigates the risks it identifies.
-   **Proposed Solution:** Evolve the critic into a "Tool-Aware" agent by providing it with machine-readable manifests of each tool's capabilities and safety features.
-   **Desired Outcome:** The critic will produce more intelligent, trustworthy analysis, reducing alarm fatigue and increasing user confidence.
-   **Status:** Proposed.

---

## Completed Epics

### [EPIC-003]: Implement Retrieval-Augmented Generation (RAG) Pipeline
-   **Status:** Completed.
-   **Summary:** The Context Plugin Architecture was successfully evolved into a full-fledged RAG pipeline. A new `ai-index` command was created to scan a project, generate embeddings, and build a local vector database. A corresponding `RAGContextPlugin` was integrated into the core application, activated by the `--context rag` flag. This allows the assistant to automatically retrieve relevant, codebase-aware context for complex queries, dramatically increasing its autonomy and analytical power on large projects. The system was hardened through iterative testing and the implementation of a `.aiignore` file for precise knowledge base curation.

### [EPIC-002]: Implement Plan Conformance Validation Layer
-   **Status:** Completed.
-   **Summary:** A multi-layered validation system was successfully implemented. The system now uses a combination of `governance.yml` rules, Pydantic data models, the `instructor` library, and a unified validation gate in the kernel to deterministically enforce architectural and safety constraints on all AI-generated plans. This has dramatically increased the reliability and safety of the system.