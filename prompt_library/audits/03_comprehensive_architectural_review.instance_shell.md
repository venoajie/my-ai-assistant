#!/bin/bash
#
# PROMPT: Perform a Comprehensive Architectural Review
#
# DESCRIPTION:
# This script initiates a comprehensive architectural review of the entire
# 'ai_assistant' application. It uses the Architecture Reviewer (arc-1)
# to analyze the core source code and canonical documents against the
# PROJECT_BLUEPRINT.md to ensure consistency and adherence to design principles.
#

set -e # Exit immediately if any command fails.

# --- Configuration ---
specialist_persona="core/arc-1"

# A curated list of all artifacts required for a full architectural review.
# This list is the single source of truth for this task's context.
source_artifacts=(
    # --- Canonical Documents (The Sources of Truth) ---
    -f "PROJECT_BLUEPRINT.md"
    -f "persona_config.yml"
    -f "docs/system_contracts.yml"
    -f "AGENTS.md"
    -f "TECHNICAL_DEBT.md"

    # --- Core Application Logic (The Implementation) ---
    -f "src/ai_assistant/kernel.py"
    -f "src/ai_assistant/cli.py"
    -f "src/ai_assistant/planner.py"
    -f "src/ai_assistant/prompt_builder.py"
    -f "src/ai_assistant/executor.py"
    -f "src/ai_assistant/tools.py"

    # --- Key Process Artifacts (The Governance) ---
    -f "scripts/generate_manifest.py"
    -f "pyproject.toml"
)

# The primary mission briefing for the Architecture Reviewer.
# This prompt is streamlined to state the goal and focus areas,
# trusting the persona to follow its internal protocol.
query=$(cat <<'EOF'
Perform a comprehensive architectural review of the entire 'ai_assistant' application.

Your analysis MUST be performed against the principles and contracts defined in the attached canonical documents (`PROJECT_BLUEPRINT.md`, `persona_config.yml`, `docs/system_contracts.yml`, `AGENTS.md`).

Your final report must be a formal Markdown document with the following sections:
    1. Executive Summary
    2. Architectural Compliance Assessment
    3. Analysis of Recent Refactoring
    4. Recommendations for Improvement

In addition to a general review, you must specifically analyze and report on the consistency and robustness of the recent refactoring that moved utility modules into a `utils` sub-package.
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
echo "🚀 [STAGE 1/1] Briefing the Architecture Reviewer (arc-1)..."
ai --new-session \
   --persona "$specialist_persona" \
   "${source_artifacts[@]}" \
   "$query"

echo "---"
echo "🎉 Architectural review complete."