# Project State: External Agent Integration (Jules)

- **version**: 1.1
- **status**: PENDING_HANDOFF_PREPARATION
- **goal**: "Integrate external execution agents (starting with Jules) into the ai-assistant workflow by implementing a robust, automated 'Handoff Workflow'."

---
## Project Roadmap & Dependency Chain

### Phase 1: Context Generation
- **Objective:** Create a canonical `AGENTS.md` file for the `ai-assistant` project itself, optimized for consumption by an external agent like Jules.
- **Specialist:** `core/amd-1` (Agent Manual Documenter)
- **Status:** **COMPLETE**
- **Inputs:** `pyproject.toml`, `README.md`
- **Output:** A new `AGENTS.md` file.

ai-instruction:
(.venv) ubuntu@LAPTOP-KDN0MGVF:~/my-ai-assistance$ ai --persona core/amd-1 --output-dir ./ai_runs/generate-agents-md-v2 \
>   -f pyproject.toml \
>   "<ACTION>Analyze the attached pyproject.toml file. Based *only* on its content, generate a new AGENTS.md file that documents the canonical, machine-executable commands for installing dependencies, running tests, and running the application. Place the generated file in the workspace.</ACTION>"


### Phase 2: Handoff Preparation
- **Objective:** Use the generated `AGENTS.md` to prepare a schema-validated `JULES_MANIFEST.json` for a sample task (e.g., creating a unit test).
- **Specialist:** `core/ia-1` (Integration Architect)
- **Status:** **PENDING**
- **Inputs:** An output package from `csa-1`, the `AGENTS.md` from Phase 1.
- **Output:** A validated `JULES_MANIFEST.json`.

### Phase 3: External Execution & Testing
- **Objective:** Manually provide the generated manifest to the Jules agent and monitor its execution.
- **Specialist:** Human Operator
- **Status:** BLOCKED (depends on Phase 2)

### Phase 4: Result Ingestion & Debugging
- **Objective:** Create and test the personas required to parse the results from Jules and debug any failures.
- **Specialist:** `core/pa-1` (Persona Architect) to build `jri-1` and integrate `da-1`.
- **Status:** BLOCKED (depends on Phase 3)

---
## Current Task Brief
- **Task ID:** P2-T1
- **Assigned To:** `core/ia-1`
- **Objective:** Take a sample implementation package and the project's `AGENTS.md` file, and generate a validated `JULES_MANIFEST.json`. This will test the handoff preparation workflow.