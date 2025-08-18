#!/bin/bash
set -e

# ---
# This script uses the 'gemini-analyst-1' persona to perform a "red team"
# review of an external article, checking it for flawed assumptions,
# specifically in the context of Google's Gemini models.
#
# Usage:
# 1. Save the article content you want to analyze into a text file (e.g., article_to_analyze.txt).
# 2. Run the script: ./prompt_library/audits/validate_article_premise.sh
# ---

# --- Configuration ---
persona_alias="domains/google/gemini-analyst-1"
article_file="article_to_analyze.txt" # <-- CHANGE THIS to the file you want to analyze

# Check if the article file exists
if [ ! -f "$article_file" ]; then
    echo "ERROR: Article file not found at '$article_file'"
    echo "Please create this file and paste the article content into it."
    exit 1
fi

# This query is now a more specific mission briefing for the specialized persona.
query="Analyze the attached article specifically through the lens of its relevance and impact on Google's Gemini models. Your entire response must adhere strictly to your operational protocol: Premise Deconstruction, Factual Analysis, and Corrected Conclusion."

# --- Execution ---
echo "🤖 Submitting article for premise validation by '$persona_alias'..."
ai --new-session \
   --persona "$persona_alias" \
   -f "$article_file" \
   "$query"

echo "🎉 Analysis complete."