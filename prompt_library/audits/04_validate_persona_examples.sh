#!/bin/bash
#
# PROMPT: Validate Persona Static Examples
#
# DESCRIPTION:
# This script performs a "meta-audit" to combat documentation-code drift.
# It uses the Persona Architect (pa-1) to critically review the static
# example output within a target persona's OUTPUT_CONTRACT. It cross-references
# the claims made in the example against the live source code to ensure the
# examples remain factually accurate and are not misleading.
#

set -e # Exit immediately if any command fails.

# --- Configuration ---
# The meta-specialist responsible for auditing other personas.
specialist_persona="core/pa-1"

# The persona file whose static examples we want to audit.
target_persona_to_audit="src/ai_assistant/personas/core/arc-1.persona.md"

# The list of source code files required for the AI to have enough
# context to perform an accurate validation.
source_files_for_context=(
    -f "persona_config.yml"
    -f "TECHNICAL_DEBT.md"
    -f "scripts/generate_manifest.py"
    -f "src/ai_assistant/cli.py"
    -f "src/ai_assistant/_security_guards.py"
    -f "src/ai_assistant/persona_validator.py"
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
echo "🚀 [STAGE 1/1] Auditing examples in '$target_persona_to_audit'..."

# A long, multi-line query is safely defined using a "here document".
# This is the best practice for complex prompts in shell scripts.
query=$(cat <<'EOF'
As the Persona Architect, your task is to perform a meta-audit.

Critically review the `OUTPUT_CONTRACT` section of the attached target persona file. Cross-reference the claims, findings, and code examples made in its static example output against the actual source code and configuration files provided as context.

Your goal is to identify any claims in the example that are factually incorrect, have become outdated due to code changes, or are otherwise inconsistent with the current state of the codebase.

Provide a concise, bulleted list of your findings. If the examples are fully accurate and aligned with the codebase, state that clearly.
EOF
)

# The final command is assembled safely.
# Note: This is an analysis task, so --output-dir is not used.
# The result is a report printed directly to the console.
ai --new-session \
   --persona "$specialist_persona" \
   -f "$target_persona_to_audit" \
   "${source_files_for_context[@]}" \
   "$query"

echo "---"
echo "🎉 Audit complete."