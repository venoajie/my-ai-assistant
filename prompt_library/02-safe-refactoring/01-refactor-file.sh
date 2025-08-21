#!/bin/bash
set -e

# ---
# WORKFLOW 2: SAFE, TWO-STAGE REFACTORING
#
# GOAL:
# To demonstrate the canonical, safe workflow for modifying a file.
# This pattern is the foundation of the AI Assistant's safety model.
# ---

# --- Configuration ---

# The specialist persona for this task.
# 'domains/programming/coder-1' is a general-purpose software engineer.
specialist_persona="domains/programming/coder-1"

# The file we want the AI to modify.
file_to_modify="my_app/utils.py"

# The directory where the AI's plan and proposed changes will be saved.
# Using the date ensures each run is unique.
output_dir="ai_runs/refactor_utils_$(date +%Y%m%d-%H%M%S)"

# The high-level goal for the specialist.
# The <ACTION> tag is a best practice to signal a modification task.
query=$(cat <<'EOF'
<ACTION>
Refactor the attached file `my_app/utils.py`.
Add Python type hints to both functions and include a docstring for the `calculate_sum` function.
</ACTION>
EOF
)

# --- STAGE 1: GENERATE THE PLAN ---
echo "🚀 [STAGE 1/2] Invoking the Software Engineer to generate a refactoring plan..."
echo "   - Output will be saved to: $output_dir"

# The 'ai' command for safe modifications:
# --output-dir: This is the key flag. It tells the AI to write its proposed
#               changes to a safe, sandboxed directory instead of your source files.
ai --persona "$specialist_persona" \
   --output-dir "$output_dir" \
   -f "$file_to_modify" \
   "$query"

# --- STAGE 2: REVIEW AND EXECUTE ---
echo -e "\n✅ Plan generated successfully."
echo "   - You can now review the proposed changes in '$output_dir/summary.md'"
echo "   - The full content of the modified file is in '$output_dir/workspace/'"
read -p "   - Press Enter to approve and apply the changes..."

echo "🚀 [STAGE 2/2] Executing the plan to apply the changes..."

# The 'ai-execute' command:
# This is a separate, non-AI script that safely applies the changes
# described in the generated 'manifest.json'.
# --confirm: This flag gives the final approval to apply the changes.
ai-execute "$output_dir" --confirm

echo -e "\n🎉 Refactoring complete. The file '$file_to_modify' has been updated."