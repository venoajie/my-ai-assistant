---
persona_alias: core/arc-1
---
<Mandate>
    <primary_objective>
        Perform a final, comprehensive architectural review of the entire 'ai_assistant' application.

        Your analysis MUST be performed against the principles and contracts defined in the attached `PROJECT_BLUEPRINT.md`, which is the canonical source of truth for the project's architecture.

        **Operational Protocol:**
        1.  **Completeness Check (Preliminary Step):** First, review the list of attached artifacts. If you determine that a critical document is missing for a full architectural review (e.g., `persona_config.yml` when analyzing the persona system), you MUST halt and state what is missing. Do not proceed with an incomplete analysis.

        2.  **Architectural Review:** If all artifacts are present, proceed with the full review. A key focus of this review must be the analysis of the architectural trade-off between prompt safety/explicitness and token economy, using `prompt_builder.py` as the primary case study. in addition to that, the application just get a major refactoring. hence, ensure consistency of each component are still maintained and inline with the overall architecture and nature of the application itself.

        3.  **Generate Final Report:** The final output must be a formal report in Markdown format with the following sections:
            - **1. Executive Summary:** A high-level overview of the findings.
            - **2. Architectural Compliance:** An assessment of how well the provided source code adheres to the principles laid out in the `PROJECT_BLUEPRINT.md`.
            - **3. Core Trade-Off Analysis:** A detailed analysis of the prompt safety vs. token economy trade-off.
            - **4. Recommendations:** A list of actionable recommendations for improvement.
    </primary_objective>

    <SECTION:ARTIFACTS_FOR_REVIEW>
        <!-- The Constitution of the Project -->
        <Inject src="PROJECT_BLUEPRINT.md"/>
        <Inject src="TECHNICAL_DEBT.md"/>
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
      - "description"
  patterns:
    required_keys:
      - "alias"
      - "version"
      - "type"
      - "title"
      - "description"
  domains:
    required_keys:
      - "alias"
      - "version"
      - "type"
      - "title"
      - "description"
  utility:
    required_keys: [ "alias", "version", "type", "title", "description" ]

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
        </StaticFile>
        <StaticFile path="src/ai_assistant/default_config.yml">
# ai_assistant/default_config.yml
config_version: "1.3.0"
model_selection:
  planning: "deepseek-coder"
  critique: "deepseek-coder"
  synthesis: "gemini-2.5-pro"
default_provider: "gemini"
general:
  personas_directory: "personas"
  sessions_directory: ".ai_sessions"
  max_file_size_mb: 5
  universal_base_persona: "_mixins/codegen-standards-1"
context_optimizer:
  max_tokens: 8000
  # If estimated input tokens exceed this, use compact prompts. Set to 0 to always use verbose prompts.
  prompt_compression_threshold: 6000
tools:
  git:
    branch_prefix: "ai"
deepseek_discount:
  start_hour: 16
  start_minute: 30
  end_hour: 0
  end_minute: 30
generation_params:
  planning:
    temperature: 0.05
    max_tokens: 512
  synthesis:
    temperature: 0.015
    topP: 0.95
    topK: 40
    max_tokens: 8192
  synthesis:
    temperature: 0.1
    topP: 0.95
    topK: 40
    max_tokens: 8192
providers:
  gemini:
    api_key_env: "GEMINI_API_KEY"
    api_endpoint_template: "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    models:
      - "gemini-2.5-pro"
  deepseek:
    api_key_env: "DEEPSEEK_API_KEY"
    api_endpoint: "https://api.deepseek.com/chat/completions"
    models:
      - "deepseek-reasoner"
      - "deepseek-coder"
      - "deepseek-chat"
        </StaticFile>

        <StaticFile path="docs/system_contracts.yml">
# Version: 1.0
# Description: This file is the canonical, machine-readable data dictionary for the AI Assistant.
# It defines the schema and purpose of all major internal data contracts.

contracts:
  - name: Persona File
    path: "src/ai_assistant/personas/**/*.persona.md"
    type: File (Markdown with YAML Frontmatter)
    description: "The source of truth for an AI agent's identity, protocol, and capabilities. It is the core component of the Persona-First architecture."
    schema:
      - field: frontmatter
        type: YAML
        description: "Contains structured metadata like alias, title, and inheritance rules, governed by persona_config.yml."
      - field: body
        type: Markdown (with custom XML-style tags)
        description: "Contains the persona's core philosophy, directives, and operational protocol in a semi-structured format."

  - name: Session History
    path: ".ai_sessions/session_*.json"
    type: JSON File
    description: "A chronological log of a single conversation between a user and the AI assistant. Managed by the SessionManager."
    schema:
      - field: role
        type: string
        description: "The originator of the message (e.g., 'user', 'model', 'system_error')."
      - field: content
        type: string
        description: "The textual content of the message."

  - name: Execution Plan
    source: Planner
    type: In-Memory Python List of Dictionaries
    description: "The AI-generated, structured plan of tool calls to be executed by the Kernel or packaged by the Executor."
    schema:
      - field: thought
        type: string
        description: "The AI's rationale for choosing the tool and arguments."
      - field: tool_name
        type: string
        description: "The name of the tool to be executed, which must exist in the TOOL_REGISTRY."
      - field: args
        type: dict
        description: "A dictionary of arguments to be passed to the tool."
      - field: condition
        type: dict (optional)
        description: "A block that makes the step's execution conditional on the output of a previous step."

  - name: Output Package Manifest
    path: "[output_dir]/manifest.json"
    type: JSON File
    description: "The machine-readable 'blueprint for action' generated in Output-First mode. It is the single source of truth for the `ai-execute` script."
    schema:
      - field: version
        type: string
        description: "The schema version of the manifest."
      - field: sessionId
        type: string
        description: "A unique, timestamp-based ID for the generation run."
      - field: generated_by
        type: string
        description: "The alias of the persona that created the plan."
      - field: actions
        type: array
        description: "A sequential list of action objects to be executed."
        schema:
          - field: type
            type: string
            description: "The action to perform (e.g., 'create_branch', 'apply_file_change')."
          - field: comment
            type: string
            description: "The AI's 'thought' or rationale for the action."
          - field: ...other_params
            type: any
            description: "Action-specific fields (e.g., 'branch_name', 'path', 'message')."        
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
        <!-- Relevant personas to be embodied later -->
        <Inject src="src/ai_assistant/personas/core/arc-1.persona.md"/>
        <Inject src="src/ai_assistant/personas/core/dca-1.persona.md"/>
        <Inject src="src/ai_assistant/personas/_base_/bcaa-1.persona.md"/>
        <Inject src="src/ai_assistant/personas/_base/btaa-1.persona.md"/>
        

    </SECTION:ARTIFACTS_FOR_REVIEW>
</Mandate>