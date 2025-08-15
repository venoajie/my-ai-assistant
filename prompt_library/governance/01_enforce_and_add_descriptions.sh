#!/bin/bash
#
# PROMPT: Enforce and Add Persona Descriptions
#
# DESCRIPTION:
# This script corrects a governance flaw where persona descriptions were not
# required. It performs a two-step, automated refactoring:
# 1. Updates persona_config.yml to make 'description' a required key.
# 2. Tasks the Documentation Architect (dca-1) to write and add the missing
#    descriptions to all affected persona files.
#
# WHEN TO USE:
# Run this script once to fix the current state of the persona ecosystem.
#

set -e # Exit immediately if any command fails.

# --- Configuration ---
specialist_persona="core/dca-1"
output_package_dir="./ai_runs/enforce_descriptions_$(date +%Y%m%d-%H%M%S)"

# Define all files that need to be updated.
files_to_review=(
    -f persona_config.yml
    -f src/ai_assistant/personas/core/arc-1.persona.md
    -f src/ai_assistant/personas/core/csa-1.persona.md
    -f src/ai_assistant/personas/core/dca-1.persona.md
    -f src/ai_assistant/personas/core/dpa-1.persona.md
    -f src/ai_assistant/personas/core/si-1.persona.md
    -f src/ai_assistant/personas/domains/finance/ada-1.persona.md
    -f src/ai_assistant/personas/domains/trading/qtsa-1.persona.md
    -f src/ai_assistant/personas/patterns/adr-1.persona.md
    -f src/ai_assistant/personas/patterns/bpr-1.persona.md
    -f src/ai_assistant/personas/patterns/da-1.persona.md
    -f src/ai_assistant/personas/patterns/pba-1.persona.md
    -f src/ai_assistant/personas/patterns/qsa-1.persona.md
    -f src/ai_assistant/personas/patterns/sia-1.persona.md
    -f src/ai_assistant/personas/patterns/sva-1.persona.md
    -f src/ai_assistant/personas/patterns/tae-1.persona.md
    -f src/ai_assistant/personas/utility/alignment-checker.persona.md
    -f src/ai_assistant/personas/utility/jan-1.persona.md
)

# Define the goal for the Documentation Architect with a more robust prompt.
query=$(cat <<'EOF'
Perform a critical documentation and governance update on the attached files.

Generate a complete execution plan to be saved in a manifest file. The plan must perform the following actions in sequence:
1.  Create a new git branch named 'fix/enforce-persona-descriptions'.

2.  First, modify `persona_config.yml`. In this file, for the `core`, `patterns`, `domains`, and `utility` persona types, you MUST add `description` to their `required_keys` list. After this change, create a single commit for this file.

3.  Next, you must process EACH of the following persona files that were attached:
    - `core/arc-1.persona.md`
    - `core/csa-1.persona.md`
    - `core/dca-1.persona.md`
    - `core/dpa-1.persona.md`
    - `core/si-1.persona.md`
    - `domains/finance/ada-1.persona.md`
    - `domains/trading/qtsa-1.persona.md`
    - `patterns/adr-1.persona.md`
    - `patterns/bpr-1.persona.md`
    - `patterns/da-1.persona.md`
    - `patterns/pba-1.persona.md`
    - `patterns/qsa-1.persona.md`
    - `patterns/sia-1.persona.md`
    - `patterns/sva-1.persona.md`
    - `patterns/tae-1.persona.md`
    - `utility/alignment-checker.persona.md`
    - `utility/jan-1.persona.md`

    For each file in the list above, your plan must add a concise, one-sentence `description` field to its YAML frontmatter explaining its core purpose. Each file modification must be followed by its own separate commit.

4.  The final action in the plan must be to push the new branch.
EOF
)

# --- STAGE 1: GENERATION ---
echo "🤖 [STAGE 1/2] Starting AI analysis to enforce and add descriptions..."
ai --new-session \
   --persona "$specialist_persona" \
   --output-dir "$output_package_dir" \
   "${files_to_review[@]}" \
   "$query"

# --- VALIDATION STEP ---
if [ ! -f "$output_package_dir/manifest.json" ]; then
    echo "❌ ERROR: AI generation failed. Manifest file was not created." >&2
    echo "   The AI's direct response is available in the logs above." >&2
    echo "   Halting execution." >&2
    exit 1
fi

echo "✅ Generation complete. Manifest found in '$output_package_dir'"
echo "---"

# --- STAGE 2: EXECUTION ---
echo "🚀 [STAGE 2/2] Automatically executing the generated plan..."
ai-execute "$output_package_dir" --confirm

echo "🎉 Workflow complete. Persona governance has been strengthened and descriptions added."