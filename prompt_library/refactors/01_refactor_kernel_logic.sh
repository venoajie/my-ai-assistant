#!/bin/bash
#
# PROMPT: Refactor Core Kernel Logic
#
# DESCRIPTION:
# This script tasks a Systems Architect (csa-1) with refactoring the core
# application kernel (kernel.py) and its primary dependency, the planner.
# It uses the robust, automated two-stage workflow.
#
# WHEN TO USE:
# Use this for significant architectural changes to the core agent loop where
# safety and resilience are paramount.
#

set -e # Exit immediately if any command fails.

# --- Configuration ---
specialist_persona="core/csa-1"
output_package_dir="./ai_runs/kernel_refactor_$(date +%Y%m%d-%H%M%S)"

# Define the set of core application files to be refactored.
# Providing related files gives the AI better context for its changes.
files_to_review=(
    -f src/ai_assistant/kernel.py
    -f src/ai_assistant/planner.py
    -f src/ai_assistant/prompt_builder.py
)

# Define the goal. This prompt is clear, specific, and focused on the outcome.
query=$(cat <<'EOF'
Perform a targeted refactoring of the attached `kernel.py` and `planner.py` files.

The primary goal is to improve error handling and resilience.

Generate a complete execution plan to be saved in a manifest file. The plan must:
1.  Create a new git branch named 'refactor/kernel-resilience'.
2.  In `planner.py`, modify the `create_plan` function. If all JSON extraction methods fail, it should not just return an empty list, but should raise a specific `PlanningError` exception.
3.  In `kernel.py`, modify the `orchestrate_agent_run` function to include a `try...except PlanningError` block around the call to `planner.create_plan`. If this exception is caught, the system should halt with a clear error message instead of proceeding to the synthesis step with an empty plan.
4.  For each modified file, include a sequence of actions in the plan: apply the file change, add it, and commit it with a conventional commit message.
5.  The final action in the plan should be to push the new branch.
EOF
)

# --- STAGE 1: GENERATION ---
echo "🤖 [STAGE 1/2] Starting AI analysis to generate execution package..."
ai --new-session \
   --persona "$specialist_persona" \
   --output-dir "$output_package_dir" \
   "${files_to_review[@]}" \
   "$query"

# --- VALIDATION STEP ---
# This is a critical safety check. Do not proceed if the manifest wasn't created.
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

echo "🎉 Workflow complete. All changes have been applied and pushed to Git."