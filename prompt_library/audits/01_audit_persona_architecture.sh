#!/bin/bash
#
# SCRIPT: audit_persona_ecosystem.sh
#
# DESCRIPTION:
# This script invokes a specialist AI architect to perform a comprehensive
# health check on the entire persona ecosystem. It automatically discovers all
# persona files and grounds the audit in the project's canonical architectural
# documents, generating a reviewable output package.

set -e # Exit immediately if a command exits with a non-zero status.

# --- Configuration ---
# The specialist persona responsible for architectural audits.
# 'core/arc-1' or a similar persona is ideal. We'll use the original 'core/pa-1'.
specialist_persona="core/pa-1"

# The directory where the review package will be generated.
output_dir="ai_runs/persona_audit_$(date +%Y%m%d-%H%M%S)"

# --- Automated File Discovery ---
# Automatically find all persona files to be audited.
echo "🔎 Discovering all persona files in the project..."
files_to_review=()
while IFS= read -r -d '' file; do
    files_to_review+=(-f "$file")
done < <(find src/ai_assistant/personas -name "*.persona.md" -print0)

# Add the canonical architectural documents as the primary context for the audit.
files_to_review+=(-f "PROJECT_BLUEPRINT.md")
files_to_review+=(-f "src/ai_assistant/internal_data/persona_config.yml")

echo "✅ Found ${#files_to_review[@]} files to attach for the audit."

# --- High-Level Goal Definition ---
# This query is structured to be more precise and aligned with current best practices.
query=$(cat <<'EOF'
<ACTION>
Perform a comprehensive architectural audit of the entire attached persona ecosystem.

Your analysis MUST be performed against the principles and rules defined in the attached `PROJECT_BLUEPRINT.md` and `persona_config.yml` files. These are your sources of truth.

Your final output must be a formal Markdown report with the following sections:
1.  **Executive Summary:** A high-level overview of the ecosystem's health and alignment with the project blueprint.
2.  **Architectural Compliance Analysis:** For each specialist persona, assess its compliance with the blueprint. Specifically:
    - Is its `inherits_from` choice appropriate for its function?
    - Does its location (`core/` vs. `domains/`) align with the "Chain of Command" defined in the blueprint?
    - Does its `OPERATIONAL_PROTOCOL` reflect a logical and safe workflow?
3.  **Actionable Recommendations:** Provide a list of concrete refactoring suggestions to improve architectural alignment, clarity, or safety. For each suggestion, cite the specific principle from the blueprint that justifies the change.
</ACTION>
EOF
)

# --- Execution ---
# Run the AI assistant using the safe, two-stage "Output-First" workflow.
echo "🚀 Invoking the Persona Architect..."
echo "   - Persona: $specialist_persona"
echo "   - Output will be generated in: $output_dir"

ai --persona "$specialist_persona" \
   --output-dir "$output_dir" \
   "${files_to_review[@]}" \
   "$query"

echo -e "\n✅ Audit package successfully generated."
echo "   - Review the analysis in: ${output_dir}/summary.md"
echo "   - To apply any proposed changes, review the manifest and run: ai-execute \"${output_dir}\" --confirm"