#!/bin/bash
#
# PROMPT: Enforce and Add Persona Descriptions (Idempotent & Resilient Version)
#
# DESCRIPTION:
# This is the final, hardened version. It is resilient to partial-run
# failures and Git's line-ending normalization issues by explicitly
# deleting each file before processing it. This guarantees that the
# subsequent write is always a "creation" that Git will commit.
#

set -e # Exit immediately if any command fails.

# --- Configuration ---
specialist_persona="core/dca-1"
branch_name="fix/enforce-persona-descriptions"

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

# --- STAGE 1: Cleanup & Branch Creation ---
echo "🚀 [STAGE 1/4] Cleaning up and creating new branch: $branch_name"
if git show-ref --quiet "refs/heads/$branch_name"; then
	    echo "ℹ️  Stale branch '$branch_name' found from a previous run. Deleting it."
	        git branch -D "$branch_name"
fi
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
										    
										    # --- CRITICAL IDEMPOTENCY FIX ---
										        # Read the original content into memory BEFORE deleting the file.
											    original_content=$(cat "$file_path")
											        rm -f "$file_path"
												    # --------------------------------

												        loop_output_dir="./ai_runs/update_$(basename "$file_path" .persona.md)_$(date +%s)"
													    
													    # We now pass the original content in the prompt itself to ensure the AI
													        # has the context even after the file is deleted.
														    loop_query=$(cat <<EOF
The original content of the file '$file_path' is provided below for context. Add a concise, one-sentence 'description' field to its YAML frontmatter.

Generate a plan to:
1. Create the file at '$file_path' with the updated content.
2. Stage and commit this single file change with a commit message like "docs(persona): Add description for $(basename "$file_path" .persona.md)".

<OriginalFileContent>
$original_content
</OriginalFileContent>
EOF
)

    # The -f flag is no longer needed as the content is in the prompt.
        ai --new-session \
		       --persona "$specialist_persona" \
		              --output-dir "$loop_output_dir" \
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
