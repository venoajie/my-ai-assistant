---
persona_alias: core/arc-1
---
<Mandate>
    <primary_objective>
        Perform a final, comprehensive architectural review of the entire 'ai_assistant' application.

        Your analysis MUST be performed against the principles and contracts defined in the attached `PROJECT_BLUEPRINT.md`, which is the canonical source of truth for the project's architecture.

        **Operational Protocol:**
        1.  **Completeness Check (Preliminary Step):** First, review the list of attached artifacts. If you determine that a critical document is missing for a full architectural review (e.g., `persona_config.yml` when analyzing the persona system), you MUST halt and state what is missing. Do not proceed with an incomplete analysis.

        2.  **Architectural Review:** If all artifacts are present, proceed with the full review. A key focus of this review must be the analysis of the architectural trade-off between prompt safety/explicitness and token economy, using `prompt_builder.py` as the primary case study.

        3.  **Generate Final Report:** The final output must be a formal report in Markdown format with the following sections:
            - **1. Executive Summary:** A high-level overview of the findings.
            - **2. Architectural Compliance:** An assessment of how well the provided source code adheres to the principles laid out in the `PROJECT_BLUEPRINT.md`.
            - **3. Core Trade-Off Analysis:** A detailed analysis of the prompt safety vs. token economy trade-off.
            - **4. Recommendations:** A list of actionable recommendations for improvement.
    </primary_objective>

    <SECTION:ARTIFACTS_FOR_REVIEW>
        <!-- The Constitution of the Project -->
        <Inject src="PROJECT_BLUEPRINT.md"/>
        <StaticFile path="persona_config.yml">
       # persona_config.yml
# This file is the single source of truth for persona architectural rules.

# Defines valid persona types and their validation rules for the frontmatter.
persona_types:
  _base: 
    required_keys: ["alias", "type", "status"]
  _mixins:
    required_keys: ["alias", "type", "status"]
  core:
    required_keys:
      - "alias"
      - "version"
      - "type"
      - "title"
  patterns:
    required_keys:
      - "alias"
      - "version"
      - "type"
      - "title"
  domains:
    required_keys:
      - "alias"
      - "version"
      - "type"
      - "title"
  utility:
    required_keys: [ "alias", "version", "type", "title" ]

# Defines the canonical schema for the body of a persona file, based on its type.
# Types with an empty list [] will skip body validation.
body_schemas_by_type:
  core:
    - "CORE_PHILOSOPHY"
    - "PRIMARY_DIRECTIVE"
    - "OPERATIONAL_PROTOCOL"
    - "OUTPUT_CONTRACT"
  patterns:
    - "CORE_PHILOSOPHY"
    - "PRIMARY_DIRECTIVE"
    - "OPERATIONAL_PROTOCOL"
    - "OUTPUT_CONTRACT"
  domains:
    - "CORE_PHILOSOPHY"
    - "PRIMARY_DIRECTIVE"
    - "OPERATIONAL_PROTOCOL"
    - "OUTPUT_CONTRACT"
  utility:
    - "OUTPUT_CONTRACT"
    
# Defines which persona statuses the validation script should process.
validation_rules:
  active_stati:
    - "active" 


        </StaticFile>

        <!-- Core Application Logic -->
        <Inject src="src/ai_assistant/kernel.py"/>
        <Inject src="src/ai_assistant/cli.py"/>
        <Inject src="src/ai_assistant/config.py"/>
        <Inject src="src/ai_assistant/planner.py"/>
        <Inject src="src/ai_assistant/prompt_builder.py"/>
        <Inject src="src/ai_assistant/persona_loader.py"/>
        <Inject src="src/ai_assistant/persona_validator.py"/>
        <Inject src="src/ai_assistant/executor.py"/>
        <Inject src="src/ai_assistant/tools.py"/>
        <Inject src="src/ai_assistant/_security_guards.py"/>
        <Inject src="src/ai_assistant/response_handler.py"/>
        <Inject src="src/ai_assistant/session_manager.py"/>
        <Inject src="src/ai_assistant/plugins/trading_plugin.py"/>
        <Inject src="scripts/generate_manifest.py"/>

        <!-- Supporting Documents -->
        <Inject src="README.md"/>
    </SECTION:ARTIFACTS_FOR_REVIEW>
</Mandate>