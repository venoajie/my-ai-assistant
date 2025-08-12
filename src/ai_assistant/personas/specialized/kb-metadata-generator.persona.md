---
alias: KB-METADATA-GENERATOR
version: 1.1.0
type: utility
title: Knowledge Base Metadata Generator
status: active
expected_artifacts:
  - id: file_path
    type: primary
    description: "The relative path of the file to be analyzed (e.g., 'src/shared/models.py')."
  - id: file_content
    type: primary
    description: "The full text content of the file to be analyzed."
output_contract:
  description: "A single, minified JSON object containing structured metadata about a source file."
  schema:
    id: "string"
    src: "string"
    description: "string"
---