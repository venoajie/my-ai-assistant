# PROJECT ROADMAP: AI Assistant

This document outlines the planned epics and major features for future versions of the AI Assistant. It serves as a strategic guide for the project's evolution.

---

## Planned Epics & Features

### [EPIC-002]: Implement Plan Conformance Validation Layer

-   **Problem:** Real-world testing has proven that the AI Planner cannot be reliably constrained by persona instructions alone. When a user's prompt contains keywords that trigger a deeply ingrained training pattern, the Planner may ignore its operational protocol and generate an unsafe or non-compliant plan.
-   **Proposed Solution:** Implement a deterministic "immune system" that validates the AI's plan *after* it is generated but *before* it is executed. This moves rule enforcement from the probabilistic AI to reliable Python code.
    1.  **Evolve Governance File:** Upgrade `governance.yml` to a "Capability Map" that links trigger keywords in a user's prompt to a machine-readable "Expected Plan Signature" (e.g., `max_steps: 1`, `allowed_tools: ['...']`).
    2.  **Create Plan Validator Module:** Develop a new `plan_validator.py` module containing two core functions: `generate_plan_expectation(prompt)` and `check_plan_compliance(plan, expectation)`.
    3.  **Integrate into Kernel:** Refactor the `kernel.py` planning loop to first generate an expectation, then generate the plan, and finally validate the plan against the expectation. The kernel will force the Planner to retry with corrective feedback if the generated plan is non-compliant.
-   **Desired Outcome:** The system will be able to deterministically reject non-compliant plans, making it resilient to the AI Planner's inherent unpredictability. This will dramatically increase the safety and reliability of all automated modification tasks.
-   **Status:** Proposed.

### [EPIC-001]: Implement a "Tool-Aware" Adversarial Critic

-   **Problem:** The current Adversarial Critic is "stateless" and can produce "false alarm" critiques for powerful tools whose internal logic already mitigates the risks it identifies.
-   **Proposed Solution:** Evolve the critic into a "Tool-Aware" agent by providing it with machine-readable manifests of each tool's capabilities and safety features.
-   **Desired Outcome:** The critic will produce more intelligent, trustworthy analysis, reducing alarm fatigue and increasing user confidence.
-   **Status:** Proposed.