#!/bin/bash
#
# PROMPT: Create Project Blueprint
#
# DESCRIPTION:
# This script tasks the Systems Architect (csa-1) with creating a new,
# high-level PROJECT_BLUEPRINT.md file. This document will serve as the
# project's "constitution," defining its core architecture and the governance
# of the persona ecosystem. It also updates the README to link to it.
#
# WHEN TO USE:
# Run this script once to establish the initial blueprint for the project.
#

set -e # Exit immediately if any command fails.

# --- Configuration ---
specialist_persona="core/csa-1"
output_package_dir="./ai_runs/create_blueprint_$(date +%Y%m%d-%H%M%S)"

# Provide the AI with relevant context to build the blueprint.
# The persona manifest and config are crucial for defining the persona ecosystem.
files_to_review=(
    -f README.md
    -f persona_manifest.yml
    -f persona_config.yml
)

# Define the goal for the Systems Architect.
query=$(cat <<'EOF'
Create a new, high-level architectural document for this project named `PROJECT_BLUEPRINT.md`. This document will serve as the project's "constitution" and a "README for the AI."

Generate a complete execution plan to be saved in a manifest file. The plan must:
1.  Create a new git branch named 'feat/add-project-blueprint'.
2.  Create a new file, `PROJECT_BLUEPRINT.md`. Its content should define:
    - A System Overview and Core Purpose.
    - The Core Architectural Principles (e.g., Persona-First, Decoupled Execution, Governance).
    - A "Persona Directory" describing the roles of the `core`, `patterns`, and `domains` categories.
    - A "Data & State Contracts" section defining the structure of the "Output Package" (`manifest.json`, `workspace/`, etc.).
3.  Modify the main `README.md` to add a prominent link to the new `PROJECT_BLUEPRINT.md` near the top.
4.  For each new or modified file, include a sequence of actions in the plan: apply the file change, add it, and commit it with a conventional commit message.
5.  The final action in the plan should be to push the new branch.
EOF
)

# --- STAGE 1: GENERATION ---
echo "🤖 [STAGE 1/2] Starting AI analysis to generate the project blueprint..."
ai --new-session \
   --persona "$specialist_persona" \
   --output-dir "$output_package_dir" \
   "${files_to_review[@]}" \
   "$query"

# --- VALIDATION STEP ---
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

echo "🎉 Workflow complete. The project blueprint has been created and integrated."