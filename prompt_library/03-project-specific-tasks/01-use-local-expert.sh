#!/bin/bash
set -e

# ---
# WORKFLOW 3: USING A PROJECT-LOCAL EXPERT
#
# GOAL:
# To demonstrate how to use a custom persona that you have created
# inside your project's '.ai/' directory.
# ---

# --- Configuration ---

# The specialist persona for this task.
# This alias matches the file we created at:
# .ai/personas/domains/my-app/style-enforcer-1.persona.md
specialist_persona="domains/my-app/style-enforcer-1"

# The file we want our expert to work on.
file_to_modify="my_app/utils.py"

# The high-level goal for our specialist.
# Note how the query is now simpler. We don't need to explain the rules,
# because the rules are baked into the persona itself.
query=$(cat <<'EOF'
<ACTION>
Please refactor the attached file to conform to our project's style standards.
</ACTION>
EOF
)

# --- Execution ---
echo "🚀 Invoking our custom 'Style Enforcer' persona..."

# We use the safe two-stage workflow again.
# The only difference is that we are now calling our own custom expert.
output_dir="ai_runs/style_enforcement_$(date +%Y%m%d-%H%M%S)"

ai --persona "$specialist_persona" \
   --output-dir "$output_dir" \
   -f "$file_to_modify" \
   "$query"

echo -e "\n✅ Plan generated. Review the changes in '$output_dir' and then execute:"
echo "   ai-execute \"$output_dir\" --confirm"