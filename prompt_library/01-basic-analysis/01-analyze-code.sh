#!/bin/bash
set -e

# ---
# WORKFLOW 1: BASIC READ-ONLY ANALYSIS
#
# GOAL:
# To demonstrate the simplest, safest way to use the AI Assistant.
# We will ask a specialist persona to review a file and provide feedback.
# No files will be changed.
# ---

# --- Configuration ---

# The specialist persona for this task.
# 'core/arc-1' is the Architecture Reviewer, a good choice for code analysis.
specialist_persona="core/arc-1"

# The file we want the AI to analyze.
file_to_review="my_app/utils.py"

# The high-level goal for the specialist.
# This is a clear, direct instruction.
query="Please provide a brief architectural review of the attached Python file. Focus on clarity and adherence to best practices."

# --- Execution ---
echo "🚀 Invoking the Architecture Reviewer for a safe, read-only analysis..."

# The 'ai' command:
# --persona: Specifies which expert to use.
# -f: Attaches a file to the context. The AI can read this file.
# The final argument is our query.
ai --persona "$specialist_persona" \
   -f "$file_to_review" \
   "$query"

echo -e "\n✅ Analysis complete. No files were modified."