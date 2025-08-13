---
alias: CODEGEN-STANDARDS-1
version: 2.1.0
type: _mixins
title: Code Generation Standards Mixin
status: active
directives:
  Directive_StructuredOutput:
    Description: All responses containing generated artifacts MUST be structured into two distinct, clearly-labeled sections to separate analysis from the final product. This ensures clarity and facilitates automated processing. The "Generated Artifacts" section MUST NOT contain any conversational text or wrapper tags.
    Structure: |
      ### Analysis & Plan
      (All conversational text, explanations, justifications, and step-by-step plans go here.)
      ---
      ### Generated Artifacts
      (This section contains ONLY the final, complete artifacts. Each artifact MUST be in its own clean, copy-pasteable markdown code block, preceded by a comment indicating its filename.)
  Directive_CodeAsConfig:
    - id: SelfDocumentation
      rule: Function, variable, and class names must be descriptive and unambiguous. Comments are for the contextual 'why', not the functional 'what'.
    - id: AggressiveModularity
      rule: Code must follow the Single Responsibility Principle. If a file is too large or contains unrelated logic, the primary recommendation must be to split it into smaller, more focused modules.
    - id: ExplicitDataStructures
      rule: All key data objects must be represented by explicit Types, Interfaces, or Data Classes. Do not use generic objects/dictionaries for structured data.
    - id: NoMagicValues
      rule: Hardcoded, business-logic-specific strings or numbers must be extracted into named constants or a proposed configuration structure.
---