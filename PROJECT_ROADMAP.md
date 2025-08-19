# PROJECT ROADMAP: AI Assistant

This document outlines the planned epics and major features for future versions of the AI Assistant. It serves as a strategic guide for the project's evolution.

---

## Planned Epics & Features

### [EPIC-001]: Implement a "Tool-Aware" Adversarial Critic

-   **Problem:** The current Adversarial Critic is "stateless." It analyzes a generated plan without any knowledge of the underlying implementation of the tools in that plan. This can lead to frequent "false alarm" critiques where it flags risks that have already been mitigated by a tool's internal logic (e.g., the `execute_refactoring_workflow` tool's use of a Git branch). This creates "alarm fatigue" and reduces user trust in the critic.
-   **Proposed Solution:** Evolve the critic into a "Tool-Aware" agent.
    1.  **Tool Manifests:** Enhance the `Tool` base class with a `get_capabilities()` method that returns a machine-readable manifest of the tool's internal safety features, preconditions, and mitigations.
    2.  **Context Injection:** The `kernel` will be updated to inject the capability manifests for all tools used in a plan into the critic's context.
    3.  **Smarter Critique:** The critic's persona (`pva-1`) will be updated with a new directive to cross-reference its findings against the provided tool capabilities, allowing it to distinguish between theoretical risks and risks that have been practically mitigated.
-   **Desired Outcome:** The critic will produce more intelligent, trustworthy analysis. Instead of just flagging risks, it will be able to confirm when those risks have been mitigated by the system's design, thereby reducing false alarms and increasing user confidence.
-   **Status:** Proposed.