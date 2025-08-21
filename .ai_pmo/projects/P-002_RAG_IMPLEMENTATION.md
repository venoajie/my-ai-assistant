# Project Charter: P-002 - RAG Pipeline Implementation

- **version**: 1.0
- **status**: PLANNING
- **goal**: "Evolve the Context Plugin Architecture into a full-fledged Retrieval-Augmented Generation (RAG) pipeline to enable the AI to reason over entire codebases without manual file attachment."

---
## Project Roadmap & Dependency Chain

### Phase 1: Indexing Service Implementation
- **Objective:** Develop a script or tool that can scan a project, chunk source code, generate embeddings, and store them in a local vector database.
- **Specialist:** `domains/programming/python-expert-1`
- **Status:** **PENDING**
- **Inputs:** `PROJECT_BLUEPRINT.md` (for architectural guidance), `tools.py` (as an example of existing code).
- **Output:** A new script (e.g., `scripts/indexer.py`) and a chosen vector database library added to `pyproject.toml`.

### Phase 2: Retriever Plugin Development
- **Objective:** Create a new `ContextPlugin` that queries the vector database based on the user's prompt to find and return relevant code snippets.
- **Specialist:** `domains/programming/python-expert-1`
- **Status:** BLOCKED (depends on Phase 1)
- **Inputs:** The index generated in Phase 1.
- **Output:** A new `rag_plugin.py` file.

### Phase 3: Kernel & CLI Integration
- **Objective:** Integrate the retriever plugin into the kernel's workflow, ensuring it's automatically triggered and its context is injected into the planner's prompt.
- **Specialist:** `core/ia-1` (Integration Architect)
- **Status:** BLOCKED (depends on Phase 2)
- **Inputs:** The `rag_plugin.py` from Phase 2, `kernel.py`, `cli.py`.
- **Output:** Modified `kernel.py` and `cli.py` files.

### Phase 4: Documentation & Testing
- **Objective:** Document the new RAG workflow in `PROJECT_BLUEPRINT.md` and `README.md`, and create unit tests for the indexer and retriever.
- **Specialist:** `core/arc-1` (Architectural Review Agent)
- **Status:** BLOCKED (depends on Phase 3)
- **Inputs:** All artifacts from previous phases.
- **Output:** Updated documentation and new test files.

---
## Current Task Brief
- **Task ID:** P2-P1-T1
- **Assigned To:** `domains/programming/python-expert-1`
- **Objective:** Research and select a local vector database (e.g., ChromaDB, LanceDB) and an open-source embedding model. Implement the initial file scanning and chunking logic.