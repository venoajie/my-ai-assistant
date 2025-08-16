#!/bin/bash
#
# PROMPT: Perform a Comprehensive Architectural Review (v2)
#
# DESCRIPTION:
# This script initiates a comprehensive architectural review of the entire
# 'ai_assistant' application. It uses the Architecture Reviewer (arc-1)
# to analyze the core source code, documentation, and process artifacts
# against the canonical PROJECT_BLUEPRINT.md to ensure consistency and
# adherence to design principles. This version is updated to include new
# areas of focus like the documentation structure and system contracts.
#

set -e # Exit immediately if any command fails.

# --- Configuration ---
specialist_persona="core/arc-1"

# A comprehensive list of all artifacts required for a full architectural review.
source_artifacts=(
    # The Constitution of the Project
    -f "PROJECT_BLUEPRINT.md"
    -f "TECHNICAL_DEBT.md"
    -f "persona_config.yml"
    -f "docs/system_contracts.yml" # NEW: Added for contract compliance check

    # Core Application Logic
    -f "src/ai_assistant/kernel.py"
    -f "src/ai_assistant/cli.py"
    -f "src/ai_assistant/planner.py"
    -f "src/ai_assistant/prompt_builder.py"
    -f "src/ai_assistant/executor.py"
    -f "scripts/generate_manifest.py"

    # Documentation & Process Artifacts
    -f "README.md"
    -f "docs/index.md"
    -f "docs/getting_started.md"
    -f "prompt_library/audits/04_validate_persona_examples.sh" # Example of a best-practice script
)

# The primary mission briefing for the Architecture Reviewer.
query=$(cat <<'EOF'
Perform a final, comprehensive architectural review of the entire 'ai_assistant' application.

Your analysis MUST be performed against the principles and contracts defined in the attached `PROJECT_BLUEPRINT.md` and `docs/system_contracts.yml`.

**Operational Protocol:**
Your final report must be a formal Markdown document with the following sections:
    1. Executive Summary
    2. Architectural Compliance
    3. Analysis of New Features & Fixes
    4. Recommendations

**New Areas of Focus for this Review:**
In addition to a general review, you must specifically analyze and report on the following:
1.  **Documentation Architecture:** Evaluate the new `docs/` structure. Is it logical, consistent, and effective at onboarding a new user? Does the main `README.md` serve as a good entry point?
2.  **Contract Compliance:** Verify that the core components (e.g., the `executor.py` manifest handling) adhere to the schemas defined in `docs/system_contracts.yml`.
3.  **Process Artifact Quality:** Review the attached `prompt_library` script. Does it exemplify the project's own documented best practices for scripting and prompting?
4.  **Verification of Recent Fixes:**
    - Confirm that the fix for TD-001 (unified context handling in `cli.py`) is robust.
    - Assess the planner optimization (generating empty `[]` plans for analysis tasks). Does it work correctly without causing regressions?
EOF
)

# --- PRE-FLIGHT CHECK ---
echo "🔎 [PRE-FLIGHT] Checking for clean Git working directory..."
if ! git diff-index --quiet HEAD --; then
    echo "❌ HALT: Your Git working directory is dirty." >&2
    echo "   This is an analysis-only script and should be run from a clean state." >&2
    git status --short >&2
    exit 1
fi
echo "✅ Git working directory is clean."
echo "---"

# --- STAGE 1: Analysis ---
echo "🤖 [STAGE 1/1] Briefing the Architecture Reviewer (arc-1)..."
ai --new-session \
   --persona "$specialist_persona" \
   "${source_artifacts[@]}" \
   "$query"

echo "---"
echo "🎉 Architectural review complete."