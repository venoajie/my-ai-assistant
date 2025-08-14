#!/bin/bash

# This script invokes the Persona Architect (pa-1) to perform a
# health check on the core persona architecture.

# --- Configuration ---
# Define the specialist persona to use for this task.
specialist_persona="core/pa-1"

# Define the set of persona files to be audited.
files_to_review=(
    -f src/ai_assistant/personas/_base/bcaa-1.persona.md
    -f src/ai_assistant/personas/_base/btaa-1.persona.md
    -f src/ai_assistant/personas/core/si-1.persona.md
    -f src/ai_assistant/personas/core/csa-1.persona.md
    -f src/ai_assistant/personas/core/pa-1.persona.md # The architect can review itself
    -f src/ai_assistant/personas/patterns/da-1.persona.md
)

# Define the high-level goal for the specialist.
query=$(cat <<'EOF'
Perform a full architectural audit of the attached persona files.

Specifically, I want you to:
1.  Assess if the chosen base persona (`bcaa-1` vs. `btaa-1`) is appropriate for each specialist's stated function.
2.  Identify any inconsistencies or weaknesses in the `OPERATIONAL_PROTOCOL` of the `si-1` and `csa-1` personas.
3.  Propose any refactoring that would improve the clarity and reliability of the overall ecosystem.
EOF
)

# --- Execution ---
# Run the AI assistant with the configured parameters.
echo "🚀 Invoking the Persona Architect for an ecosystem audit..."
ai --new-session --persona "$specialist_persona" "${files_to_review[@]}" "$query"