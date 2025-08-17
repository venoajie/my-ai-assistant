# Project State: External Agent Integration (Jules)

- **version**: 1.0
- **status**: PENDING_CONTEXT_GENERATION
- **goal**: "Integrate external execution agents (starting with Jules) into the ai-assistant workflow by implementing a robust, automated 'Handoff Workflow'."

---
## Project Roadmap & Dependency Chain

### Phase 1: Context Generation
- **Objective:** Create a canonical `AGENTS.md` file for the `ai-assistant` project itself, optimized for consumption by an external agent like Jules.
- **Specialist:** `core/amd-1` (Agent Manual Documenter)
- **Status:** **PENDING**
- **Inputs:** `pyproject.toml`, `README.md`
- **Output:** A new `AGENTS.md` file.

### Phase 2: Handoff Preparation
- **Objective:** Use the generated `AGENTS.md` to prepare a schema-validated `JULES_MANIFEST.json` for a sample task (e.g., creating a unit test).
- **Specialist:** `core/ia-1` (Integration Architect)
- **Status:** BLOCKED (depends on Phase 1)
- **Inputs:** An output package from `csa-1`, the `AGENTS.md` from Phase 1.
- **Output:** A validated `JULES_MANIFEST.json`.

### Phase 3: External Execution & Testing
- **Objective:** Manually provide the generated manifest to the Jules agent and monitor its execution.
- **Specialist:** Human Operator
- **Status:** BLOCKED (depends on Phase 2)
- **Inputs:** `JULES_MANIFEST.json`.
- **Output:** A `JULES_REPORT.json`.

### Phase 4: Result Ingestion & Debugging
- **Objective:** Create and test the personas required to parse the results from Jules and debug any failures.
- **Specialist:** `core/pa-1` (Persona Architect) to build `jri-1` and integrate `da-1`.
- **Status:** BLOCKED (depends on Phase 3)
- **Inputs:** `JULES_REPORT.json`.
- **Output:** A summary of the Jules run and a potential bug fix plan.

---
## Current Task Brief
- **Task ID:** P1-T1
- **Assigned To:** `core/amd-1`
- **Objective:** Analyze the attached configuration and documentation files for the `ai-assistant` project to generate a concise `AGENTS.md` file. This file should serve as an "operator's manual" for an external AI agent, detailing the core commands for testing, linting, and dependency management.