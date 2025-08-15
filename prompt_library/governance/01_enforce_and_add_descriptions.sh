#!/bin/bash
#
# PROMPT: Enforce and Add Persona Descriptions (Corrected Atomic Version)
#
# DESCRIPTION:
# This script corrects a governance flaw using a robust, atomic approach.
# It generates a single, comprehensive plan that:
# 1. Creates a new branch.
# 2. Updates persona_config.yml to make 'description' a required key.
# 3. Adds the missing descriptions to all affected persona files.
# 4. Creates a SINGLE commit containing all of the above changes.
# 5. Pushes the branch.
# This ensures the repository is never in an invalid intermediate state.
#
# WHEN TO USE:
# Run this script once to fix the current state of the persona ecosystem.
#

set -e # Exit immediately if any command fails.

# --- Configuration ---
specialist_persona="core/dca-1"
output_package_dir="./ai_runs/enforce_descriptions_atomic_$(date +%Y%m%d-%H%M%S)"

# Define all files that need to be updated in a single operation.
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

# Define a single, comprehensive goal for the AI.
query=$(cat <<'EOF'
Perform a critical, ATOMIC documentation and governance update.

Generate a complete execution plan to perform the following actions in sequence:
1.  Create a new git branch named 'fix/enforce-persona-descriptions5'.

2.  Modify `persona_config.yml` to add `description` to the `required_keys` list for the `core`, `patterns`, `domains`, and `utility` persona types.

3.  For EACH of the attached `.persona.md` files, add a concise, one-sentence `description` field to its YAML frontmatter that accurately explains its core purpose.

4.  After ALL file modifications are defined, stage ALL modified files (`persona_config.yml` and all `.persona.md` files) using `git add`.

5.  Create a SINGLE commit with the message "feat(governance): Enforce and add persona descriptions".

6.  Push the new branch.
EOF
)

# --- STAGE 1: GENERATION ---
echo "🤖 [STAGE 1/2] Starting AI analysis for atomic update..."
ai --new-session \
   --persona "$specialist_persona" \
   --output-dir "$output_package_dir" \
   "${files_to_review[@]}" \
   "$query"

# --- VALIDATION STEP ---
if [ ! -f "$output_package_dir/manifest.json" ]; then
    echo "❌ ERROR: AI generation failed. Manifest file was not created." >&2
    exit 1
fi

echo "✅ Generation complete. Manifest found in '$output_package_dir'"
echo "---"

# --- STAGE 2: EXECUTION ---
echo "🚀 [STAGE 2/2] Automatically executing the generated atomic plan..."
ai-execute "$output_package_dir" --confirm

echo "🎉 Workflow complete. Persona governance has been strengthened and descriptions added."