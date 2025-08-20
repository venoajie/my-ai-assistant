# PROJECT ROADMAP: AI Assistant

This document outlines the planned epics and major features for future versions of the AI Assistant. It serves as a strategic guide for the project's evolution.

---

## Planned Epics & Features

### [EPIC-003]: Implement Retrieval-Augmented Generation (RAG) Pipeline
-   **Problem:** The current context system relies on the user manually attaching relevant files via the `-f` flag. This does not scale to tasks that require knowledge of an entire codebase or a large set of documents.
-   **Proposed Solution:** Evolve the Context Plugin Architecture into a full-fledged RAG pipeline.
    1.  **Create an Indexing Service:** Develop a script or tool that can scan a project directory, chunk source code and documentation, and store the resulting embeddings in a local vector database (e.g., ChromaDB, LanceDB).
    2.  **Develop a Retriever Plugin:** Create a new type of `ContextPlugin` that, instead of using static logic, queries the vector database based on the user's prompt to find the most relevant code snippets or documents.
    3.  **Integrate into Kernel:** The retriever plugin will automatically inject this "retrieved context" into the prompt, giving the AI Planner the specific knowledge it needs to reason about the codebase without manual intervention.
-   **Desired Outcome:** The AI Assistant will be able to answer questions and perform modifications on large, complex projects by automatically finding and using the most relevant context, dramatically increasing its autonomy and power.
-   **Status:** Proposed.

### [EPIC-001]: Implement a "Tool-Aware" Adversarial Critic
-   **Problem:** The current Adversarial Critic is "stateless" and can produce "false alarm" critiques for powerful tools whose internal logic already mitigates the risks it identifies.
-   **Proposed Solution:** Evolve the critic into a "Tool-Aware" agent by providing it with machine-readable manifests of each tool's capabilities and safety features.
-   **Desired Outcome:** The critic will produce more intelligent, trustworthy analysis, reducing alarm fatigue and increasing user confidence.
-   **Status:** Proposed.

---

## Completed Epics

### [EPIC-002]: Implement Plan Conformance Validation Layer
-   **Status:** Completed.
-   **Summary:** A multi-layered validation system was successfully implemented. The system now uses a combination of `governance.yml` rules, Pydantic data models, the `instructor` library, and a unified validation gate in the kernel to deterministically enforce architectural and safety constraints on all AI-generated plans. This has dramatically increased the reliability and safety of the system.