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
files_to_review=(
    -f README.md
    -f persona_manifest.yml
    -f persona_config.yml
)

# Define the goal for the Systems Architect with a more robust, procedural prompt.
query=$(cat <<'EOF'
Your primary task is to generate a complete execution plan to be saved in a manifest file.

The plan must perform the following actions in sequence:
1.  **Check for the existence of the 'feat/add-project-blueprint' branch.**
    - If the branch already exists, the plan should use the `git_checkout` tool to switch to it.
    - If the branch does not exist, the plan should use the `git_create_branch` tool to create it.
    - **(You will need to add a `git_checkout` tool to your `tools.py` for this to work)**

2.  Create a new file named `PROJECT_BLUEPRINT.md`. The `content` for this file should be a comprehensive architectural document for the project, serving as its "constitution." It MUST contain the following sections:
    - A "System Overview and Core Purpose" section.
    - A "Core Architectural Principles" section (mentioning Persona-First, Decoupled Execution, and Governance).
    - A "Persona Directory" section describing the roles of the `core`, `patterns`, and `domains` categories based on the attached manifest.
    - A "Data & State Contracts" section defining the structure of the "Output Package" (`manifest.json`, `workspace/`, etc.).

3.  Modify the main `README.md` file. Add a new section near the top that introduces the blueprint and provides a prominent link to the new `PROJECT_BLUEPRINT.md` file.

4.  For each of the two files (`PROJECT_BLUEPRINT.md` and `README.md`), the plan must include a separate sequence of actions to apply the file change, add it, and commit it with a conventional commit message.

5.  The final action in the plan must be to push the new branch.
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