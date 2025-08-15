#!/bin/bash
#
# PROMPT: Enforce and Add Persona Descriptions (Final Hybrid Version)
#
# DESCRIPTION:
# This script uses a robust, multi-stage hybrid approach to avoid both
# context-window limits and validation deadlocks. It follows a strict
# "data-first, rule-last" sequence.
#
# 1. STAGE 1: Creates a new branch to isolate the work.
# 2. STAGE 2: Iteratively loops through each persona file, using the AI to
#    add a description and create a commit for each one.
# 3. STAGE 3: After all data is fixed, it makes a final call to the AI to
#    update the persona_config.yml rule and commit it.
# 4. STAGE 4: Pushes the completed, valid branch.
#

set -e # Exit immediately if any command fails.

# --- Configuration ---
specialist_persona="core/dca-1"
branch_name="fix/enforce-persona-descriptions8"

# --- STAGE 1: Create Branch ---
echo "🚀 [STAGE 1/4] Creating new branch: $branch_name"
git switch -c "$branch_name"
echo "✅ Branch created and checked out."
echo "---"

# --- STAGE 2: Iterative Persona Data Fixes ---
echo "🚀 [STAGE 2/4] Iterating through persona files to add descriptions..."

files_to_update=(
    src/ai_assistant/personas/core/arc-1.persona.md
    src/ai_assistant/personas/core/csa-1.persona.md
    src/ai_assistant/personas/core/dca-1.persona.md
    src/ai_assistant/personas/core/dpa-1.persona.md
    src/ai_assistant/personas/core/si-1.persona.md
    src/ai_assistant/personas/domains/finance/ada-1.persona.md
    src/ai_assistant/personas/domains/trading/qtsa-1.persona.md
    src/ai_assistant/personas/patterns/adr-1.persona.md
    src/ai_assistant/personas/patterns/bpr-1.persona.md
    src/ai_assistant/personas/patterns/da-1.persona.md
    src/ai_assistant/personas/patterns/pba-1.persona.md
    src/ai_assistant/personas/patterns/qsa-1.persona.md
    src/ai_assistant/personas/patterns/sia-1.persona.md
    src/ai_assistant/personas/patterns/sva-1.persona.md
    src/ai_assistant/personas/patterns/tae-1.persona.md
    src/ai_assistant/personas/utility/alignment-checker.persona.md
    src/ai_assistant/personas/utility/jan-1.persona.md
)

for file_path in "${files_to_update[@]}"; do
    echo "   - Processing: $file_path"
    loop_output_dir="./ai_runs/update_$(basename "$file_path" .persona.md)_$(date +%s)"
    
    loop_query=$(cat <<EOF
Based on the content of the attached file '$file_path', add a concise, one-sentence 'description' field to its YAML frontmatter.
Generate a plan to:
1. Overwrite the file at '$file_path' with the updated content.
2. Stage and commit this single file change with a commit message like "docs(persona): Add description for $(basename "$file_path" .persona.md)".
EOF
)

    ai --new-session \
       --persona "$specialist_persona" \
       --output-dir "$loop_output_dir" \
       -f "$file_path" \
       "$loop_query"

    ai-execute "$loop_output_dir" --confirm
    echo "   - ✅ Committed update for $file_path"
done

echo "✅ All persona files updated."
echo "---"

# --- STAGE 3: Enforce Governance Rule ---
echo "🚀 [STAGE 3/4] Enforcing governance rule in persona_config.yml..."
config_output_dir="./ai_runs/enforce_rule_$(date +%s)"

config_query=$(cat <<'EOF'
Generate an execution plan to perform the final governance update:
1. Modify `persona_config.yml` to add `description` to the `required_keys` list for the `core`, `patterns`, `domains`, and `utility` types.
2. Stage and commit the change to `persona_config.yml` with the message "feat(governance): Enforce description field in personas".
EOF
)

ai --new-session \
   --persona "$specialist_persona" \
   --output-dir "$config_output_dir" \
   -f persona_config.yml \
   "$config_query"

ai-execute "$config_output_dir" --confirm
echo "✅ Governance rule enforced and committed."
echo "---"

# --- STAGE 4: Final Push ---
echo "🚀 [STAGE 4/4] Pushing the completed branch to remote..."
git push --set-upstream origin "$branch_name"

echo "🎉 Workflow complete. Persona governance has been strengthened and descriptions added."