#!/bin/bash
#
# PROMPT: Enforce and Add Persona Descriptions (Production-Grade Version)
#
# DESCRIPTION:
# This script includes critical safety checks. It verifies the Git working
# directory is clean before starting and follows a "data-first, rule-last"
# sequence to avoid validation deadlocks.
#

set -e # Exit immediately if any command fails.

# --- PRE-FLIGHT CHECK ---
echo "🔎 [PRE-FLIGHT] Checking for clean Git working directory..."
if ! git diff-index --quiet HEAD --; then
    echo "❌ HALT: Your Git working directory is dirty." >&2
    echo "   Please commit or stash your changes before running this script." >&2
    git status --short >&2
    exit 1
fi
echo "✅ Git working directory is clean."
echo "---"

# --- Configuration ---
specialist_persona="core/dca-1"
branch_name="fix/enforce-persona-descriptions"

# --- STAGE 1: Create Branch ---
echo "🚀 [STAGE 1/4] Creating new branch: $branch_name"
# Use `git switch -c` which fails safely if the branch already exists.
if ! git switch -c "$branch_name"; then
    echo "ℹ️  Branch '$branch_name' already exists. Switching to it."
    git switch "$branch_name"
fi
echo "✅ Branch created and checked out."
echo "---"

# --- STAGE 2: Iterative Persona Data Fixes ---
echo "🚀 [STAGE 2/4] Iterating through persona files to add descriptions..."

files_to_update=(
    src/ai_assistant/personas/core/arc-1.persona.md
    src/ai_assistant/personas/core/csa-1.persona.md
    # ... (rest of the files) ...
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