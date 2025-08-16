#!/bin/bash
#
# PROMPT: Enforce and Add Persona Descriptions (Final Resilient Version)
#
# DESCRIPTION:
# This is the final, hardened version of the script. It solves the stale
# manifest deadlock by explicitly regenerating and committing the manifest
# after all persona files have been updated, ensuring a valid state before
# the final step.
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
echo "🚀 [STAGE 1/5] Cleaning up and creating new branch: $branch_name"
if git show-ref --quiet "refs/heads/$branch_name"; then
	    echo "ℹ️  Stale branch '$branch_name' found from a previous run. Deleting it."
	        git branch -D "$branch_name"
fi
git switch -c "$branch_name"
echo "✅ Branch created and checked out."
echo "---"

# --- STAGE 2: Iterative Persona Data Fixes ---
echo "🚀 [STAGE 2/5] Iterating through persona files to add descriptions..."

files_to_update=(
	    "src/ai_assistant/personas/core/arc-1.persona.md"
	        "src/ai_assistant/personas/core/csa-1.persona.md"
		    "src/ai_assistant/personas/core/dca-1.persona.md"
		        "src/ai_assistant/personas/core/dpa-1.persona.md"
			    "src/ai_assistant/personas/core/si-1.persona.md"
			        "src/ai_assistant/personas/domains/finance/ada-1.persona.md"
				    "src/ai_assistant/personas/domains/trading/qtsa-1.persona.md"
				        "src/ai_assistant/personas/patterns/adr-1.persona.md"
					    "src/ai_assistant/personas/patterns/bpr-1.persona.md"
					        "src/ai_assistant/personas/patterns/da-1.persona.md"
						    "src/ai_assistant/personas/patterns/pba-1.persona.md"
						        "src/ai_assistant/personas/patterns/qsa-1.persona.md"
							    "src/ai_assistant/personas/patterns/sia-1.persona.md"
							        "src/ai_assistant/personas/patterns/sva-1.persona.md"
								    "src/ai_assistant/personas/patterns/tae-1.persona.md"
								        "src/ai_assistant/personas/utility/alignment-checker.persona.md"
									    "src/ai_assistant/personas/utility/jan-1.persona.md"
								    )

								    declare -A descriptions
								    descriptions["arc-1"]="Performs rigorous, evidence-based audits to identify architectural deviations and provide actionable recommendations."
								    descriptions["csa-1"]="Designs new systems or refactors existing ones, ensuring all changes are harmonious with the established architecture."
								    descriptions["dca-1"]="Creates clear, accurate, and user-centric documentation based on the system's technical artifacts."
								    descriptions["dpa-1"]="Provides a comprehensive, risk-mitigated deployment plan for production releases."
								    descriptions["si-1"]="Analyzes a user's high-level goal and selects the most appropriate specialist agent to perform the task."
								    descriptions["ada-1"]="Designs API contracts for financial services, focusing on REST and OpenAPI standards."
								    descriptions["qtsa-1"]="Guides the development of formal, testable trading strategy blueprints from high-level concepts."
								    descriptions["adr-1"]="Analyzes technical problems and generates structured Architectural Decision Records (ADRs) to document key decisions."
								    descriptions["bpr-1"]="Acts as a senior peer reviewer for code quality, style, and adherence to established best practices."
								    descriptions["da-1"]="Diagnoses the root cause of bugs from error reports, stack traces, and relevant source code."
								    descriptions["pba-1"]="Analyzes system behavior and metrics to identify and diagnose performance bottlenecks."
								    descriptions["qsa-1"]="Analyzes a codebase to create a prioritized, risk-based testing plan."
								    descriptions["sia-1"]="Audits system configurations and state to ensure they align with a declared 'source of truth' document."
								    descriptions["sva-1"]="Reviews code with an adversarial mindset to find potential security vulnerabilities."
								    descriptions["tae-1"]="Generates automated tests (unit, integration, or end-to-end) for a given source code file."
								    descriptions["alignment-checker"]="Performs a semantic check to ensure a specialist's proposed plan aligns with the user's original mandate."
								    descriptions["jan-1"]="Performs code cleanup tasks like removing comments, formatting, and deleting specified code blocks."


								    for file_path in "${files_to_update[@]}"; do
									        echo "   - Processing: $file_path"
										    base_name=$(basename "$file_path" .persona.md)
										        description_text=${descriptions[$base_name]}
											    
											    if [ -z "$description_text" ]; then
												            echo "   - ❌ ERROR: No description found for $base_name. Skipping."
													            continue
														        fi

															    sed -i "/^title:/a description: \"$description_text\"" "$file_path"
															        git add "$file_path"
																    git commit -m "docs(persona): Add description for $base_name"
																        echo "   - ✅ Committed update for $file_path"
																done

																echo "✅ All persona files updated."
																echo "---"

																# --- STAGE 3: Resynchronize State ---
																echo "🚀 [STAGE 3/5] Regenerating manifest to reflect new persona content..."
																python scripts/generate_manifest.py
																git add persona_manifest.yml
																git commit -m "chore: Regenerate manifest after adding descriptions"
																echo "✅ Manifest regenerated and committed."
																echo "---"

																# --- STAGE 4: Enforce Governance Rule ---
																echo "🚀 [STAGE 4/5] Enforcing governance rule in persona_config.yml..."
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

# --- STAGE 5: Final Push ---
echo "🚀 [STAGE 5/5] Pushing the completed branch to remote..."
git push --set-upstream origin "$branch_name"

echo "🎉 Workflow complete. Persona governance has been strengthened and descriptions added."
