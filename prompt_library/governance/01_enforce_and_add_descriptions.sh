#!/bin/bash
#
# PROMPT: Enforce and Add Persona Descriptions (Corrected Version)
#
# DESCRIPTION:
# This script corrects a governance flaw using a robust, iterative approach.
# 1. It first creates a branch and modifies persona_config.yml in a single action.
# 2. It then LOOPS through each persona file, invoking the AI to add a
#    description and create a commit for each one individually.
#
# WHEN TO USE:
# Run this script once to fix the current state of the persona ecosystem.
#

set -e # Exit immediately if any command fails.

# --- Configuration ---
specialist_persona="core/dca-1"
branch_name="fix/enforce-persona-descriptions"

# --- STAGE 1: Initial Setup (Branch and Config File) ---
echo "🚀 [STAGE 1/3] Creating branch and updating persona_config.yml..."

# Use a temporary, unique output directory for this initial step
setup_output_dir="./ai_runs/setup_$(date +%Y%m%d-%H%M%S)"

setup_query=$(cat <<'EOF'
Generate an execution plan to perform initial setup:
1. Create a new git branch named 'fix/enforce-persona-descriptions3'.
2. Modify `persona_config.yml` to add `description` to the `required_keys` list for the `core`, `patterns`, `domains`, and `utility` types.
3. Stage and commit the change to `persona_config.yml` with the message "feat(governance): Enforce description field in personas".
EOF
)

# Generate and execute the plan for the initial setup
ai --new-session \
   --persona "$specialist_persona" \
   --output-dir "$setup_output_dir" \
   -f persona_config.yml \
   "$setup_query"

ai-execute "$setup_output_dir" --confirm
echo "✅ Initial setup complete."
echo "---"


# --- STAGE 2: Iterative Persona Updates ---
echo "🚀 [STAGE 2/3] Iterating through persona files to add descriptions..."

# Define ONLY the persona files that need to be updated.
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

# Loop through each file and process it individually
for file_path in "${files_to_update[@]}"; do
    echo "   - Processing: $file_path"
    
    # Each iteration gets its own clean output directory
    loop_output_dir="./ai_runs/update_$(basename "$file_path" .persona.md)_$(date +%s)"
    
    # The query is now simple and focused on a SINGLE file.
    loop_query=$(cat <<EOF
Based on the content of the attached file '$file_path', add a concise, one-sentence 'description' field to its YAML frontmatter.
Then, generate a plan to:
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

# --- STAGE 3: Final Push ---
echo "🚀 [STAGE 3/3] Pushing the completed branch to remote..."
git push --set-upstream origin "$branch_name"

echo "🎉 Workflow complete. Persona governance has been strengthened and descriptions added."