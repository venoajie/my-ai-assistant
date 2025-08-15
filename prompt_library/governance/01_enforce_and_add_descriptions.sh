#!/bin/bash
#
# PROMPT: Enforce and Add Persona Descriptions (Idempotent Version)
#
# DESCRIPTION:
# This script is hardened against partial-run failures and Git normalization
# issues. It deletes each file before processing to ensure the subsequent
# write and commit operations are always treated as a change by Git.
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
    
    # --- CRITICAL IDEMPOTENCY FIX ---
    # Ensure the file is restored to its original state from the repo,
    # then delete it. This guarantees that the subsequent write is a
    # clean creation that Git will always recognize as a change.
    git restore "$file_path"
    rm -f "$file_path"
    # --------------------------------

    loop_output_dir="./ai_runs/update_$(basename "$file_path" .persona.md)_$(date +%s)"
    
    loop_query=$(cat <<EOF
The file '$file_path' has been provided for context. Add a concise, one-sentence 'description' field to its YAML frontmatter.
Generate a plan to:
1. Create the file at '$file_path' with the updated content.
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

# (Stages 3 and 4 remain the same)

# --- STAGE 3: Enforce Governance Rule ---
echo "🚀 [STAGE 3/4] Enforcing governance rule in persona_config.yml..."
# ... (rest of stage 3) ...

# --- STAGE 4: Final Push ---
echo "🚀 [STAGE 4/4] Pushing the completed branch to remote..."
# ... (rest of stage 4) ...