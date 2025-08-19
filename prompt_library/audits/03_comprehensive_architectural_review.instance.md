---
persona_alias: core/arc-1
---
<Mandate>
    <primary_objective>
        Perform a final, comprehensive architectural review of the entire 'ai_assistant' application, which has recently undergone a major refactoring to improve portability and robustness.

        Your analysis MUST be performed against the principles and contracts defined in the attached `PROJECT_BLUEPRINT.md`.

        **Operational Protocol:**
        1.  **Completeness Check:** First, review the list of attached artifacts. If a critical document is missing for a full architectural review, you MUST halt and state what is missing.
        2.  **Architectural Review:** Proceed with the full review. Your analysis must verify that the recent refactoring has been implemented consistently across all components (`cli.py`, `kernel.py`, `planner.py`, `signature.py`, etc.) and remains aligned with the project's core principles. A key focus should also remain on the trade-off between prompt safety and token economy.
        3.  **Generate Final Report:** The final output must be a formal report in Markdown with the following sections:
            - **1. Executive Summary:** A high-level overview of the findings.
            - **2. Architectural Compliance:** An assessment of how well the provided source code adheres to the principles laid out in the `PROJECT_BLUEPRINT.md`.
            - **3. Core Trade-Off Analysis:** A detailed analysis of the prompt safety vs. token economy trade-off.
            - **4. Recommendations:** A list of actionable recommendations for improvement.
    </primary_objective>

    <SECTION:ARTIFACTS_FOR_REVIEW>
        <!-- The Constitution of the Project -->
        <Inject src="PROJECT_BLUEPRINT.md"/>
        <Inject src="TECHNICAL_DEBT.md"/>
        
        <!-- Core Governance Files (Corrected Paths & Content) -->
        <StaticFile path="src/ai_assistant/internal_data/persona_config.yml">
# persona_config.yml
# This file is the single source of truth for persona architectural rules.

# Defines valid persona types and their validation rules for the frontmatter.
persona_types:
  _base: 
    required_keys: ["alias", "type", "status"]
  _mixins:
    required_keys: ["alias", "type", "status"]
  core:
    required_keys: ["alias", "type", "version", "title", "description"]
  domains:
    required_keys: ["alias", "type", "version", "title", "description"]
# Defines the canonical schema for the body of a persona file, based on its type.
# Types with an empty list [] will skip body validation.
body_schemas_by_type:
  core:
    - "CORE_PHILOSOPHY"
    - "PRIMARY_DIRECTIVE"
    - "OPERATIONAL_PROTOCOL"
    - "OUTPUT_CONTRACT"
  domains:
    - "CORE_PHILOSOPHY"
    - "PRIMARY_DIRECTIVE"
    - "OPERATIONAL_PROTOCOL"
    - "OUTPUT_CONTRACT"
    
# Defines which persona statuses the validation script should process.
validation_rules:
  active_stati:
        </StaticFile>
        <StaticFile path="src/ai_assistant/default_config.yml">
# ai_assistant/default_config.yml
config_version: "1.4.0"
model_selection:
  planning: "deepseek-coder"
  critique: "deepseek-coder"
  synthesis: "gemini-2.5-pro"
  json_corrector: "gemini-2.5-flash-lite"
default_provider: "gemini"
general:
  personas_directory: "personas"
  sessions_directory: ".ai_sessions"
  max_file_size_mb: 5
  universal_base_persona: "_mixins/codegen-standards-1"
  # Centralized configuration for auto-injected files and special personas
  auto_inject_files:
    - "AGENTS.md"
  critique_persona_alias: "domains/programming/pva-1"
  failure_persona_alias: "domains/programming/da-1"
  enable_llm_json_corrector: true
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
    temperature: 0.15
    topP: 0.95
    topK: 40
    max_tokens: 8192
  critique:
    temperature: 0.1
    topP: 0.95
    topK: 40
providers:
  gemini:
    api_key_env: "GEMINI_API_KEY"
    api_endpoint_template: "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    models:
      - "gemini-2.5-pro"
      - "gemini-2.5-flash-lite" 
  deepseek:
    api_key_env: "DEEPSEEK_API_KEY"
    api_endpoint: "https://api.deepseek.com/chat/completions"
    models:
      - "deepseek-reasoner"
      - "deepseek-coder"
      - "deepseek-chat"        
      </StaticFile>
      
              <StaticFile path="docs/system_contracts.yml">
# Version: 1.1
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

  - name: Project State File
    path: "PROJECT_STATE.md"
    type: Markdown File
    description: "The single source of truth for a long-running, multi-agent project. It is created and managed by the `pmo-1` persona to maintain state across multiple CLI invocations."
    schema:
      - field: metadata
        type: Key-Value List
        description: "Contains high-level project status, version, and the original goal."
      - field: Project Plan
        type: Markdown Section
        description: "Defines the sequence of phases, the specialist persona assigned to each, and their dependency relationships."
      - field: Artifact Sections
        type: Markdown Sections
        description: "Dedicated sections (e.g., 'Requirements', 'Architecture') that are populated by specialist personas as the project progresses."

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
      
      
        <StaticFile path="pyproject.toml">
        # pyproject.toml
[project]
name = "my-ai-assistant"
version = "1.2.1"
description = "AI Assistant for Software Development"
readme = "README.md"
requires-python = ">=3.9"
dependencies = [
      "aiohttp",
      "requests",
      "pyyaml",
      "pydantic>=2.0",
      ]

[build-system]
requires = ["setuptools>=65.0", "wheel"]
build-backend = "setuptools.build_meta"

[project.scripts]
ai = "ai_assistant.cli:main"
ai-execute = "ai_assistant.executor:main"

[project.entry-points."ai_assistant.context_plugins"]
"domains-programming" = "ai_assistant.plugins.domains.programming.context:ProgrammingContextPlugin"
"domains-finance" = "ai_assistant.plugins.domains.finance.context:FinanceContextPlugin"
"domains-writing" = "ai_assistant.plugins.domains.writing.context:WritingContextPlugin"

[project.optional-dependencies]
test = [
    "unittest-xml-reporting",
    "pytest",
]

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]
include = ["ai_assistant*"]

[tool.setuptools.package-data]
ai_assistant = [
    "default_config.yml",
    "personas/**/*.md",
    "personas/**/*.py",
    "internal_data/*"
]
        </StaticFile>

        <!-- Core Application Logic -->
        <Inject src="src/ai_assistant/kernel.py"/>
        <Inject src="src/ai_assistant/cli.py"/>
        <Inject src="src/ai_assistant/config.py"/>
        <Inject src="src/ai_assistant/planner.py"/>
        <Inject src="src/ai_assistant/prompt_builder.py"/>
        <Inject src="src/ai_assistant/executor.py"/>
        <Inject src="src/ai_assistant/tools.py"/>
        <Inject src="src/ai_assistant/persona_loader.py"/>
        <Inject src="src/ai_assistant/response_handler.py"/>
        <Inject src="src/ai_assistant/session_manager.py"/>
        <Inject src="src/ai_assistant/utils/signature.py"/>
        <Inject src="scripts/generate_manifest.py"/>

        <!-- New Plugin Architecture -->
        <Inject src="src/ai_assistant/plugins/domains/programming/context.py"/>
        <Inject src="src/ai_assistant/plugins/domains/finance/context.py"/>

    </SECTION:ARTIFACTS_FOR_REVIEW>
</Mandate>
```