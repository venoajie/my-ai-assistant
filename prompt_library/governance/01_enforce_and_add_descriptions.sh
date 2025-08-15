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

# Define all files that need to be updated. This includes the config file
# and all personas that are currently missing a description.
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

# Define the goal for the Documentation Architect.
query=$(cat <<'EOF'
Perform a documentation and governance update on the attached files.

Generate a complete execution plan to be saved in a manifest file. The plan must:
1.  Create a new git branch named 'fix/enforce-persona-descriptions'.
2.  First, modify `persona_config.yml`. For the `core`, `patterns`, `domains`, and `utility` persona types, add `description` to their `required_keys` list.
3.  Next, for EACH of the attached `.persona.md` files, your task is to write and add a concise, one-sentence `description` field to its YAML frontmatter, explaining its core purpose.
4.  For each modified file (`persona_config.yml` and all personas), include a sequence of actions in the plan: apply the file change, add it, and commit it with a conventional commit message.
5.  The final action in the plan should be to push the new branch.
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