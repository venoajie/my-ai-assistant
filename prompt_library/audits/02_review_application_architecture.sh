#!/bin/bash

# This script invokes the Architecture Reviewer (arc-1) to perform a
# comprehensive review of the entire Python application source code.

# --- Configuration ---
# Define the specialist persona to use for this task.
specialist_persona="core/arc-1"

# Define the complete set of application source files for review.
files_to_review=(
    -f src/ai_assistant/cli.py
    -f src/ai_assistant/config.py
    -f src/ai_assistant/context_optimizer.py
    -f src/ai_assistant/context_plugin.py
    -f src/ai_assistant/persona_loader.py
    -f src/ai_assistant/planner.py
    -f src/ai_assistant/prompt_builder.py
    -f src/ai_assistant/kernel.py
    -f src/ai_assistant/response_handler.py
    -f src/ai_assistant/session_manager.py
    -f src/ai_assistant/tools.py
    -f src/ai_assistant/_security_guards.py
    # Note: Adjust path if trading_plugin.py is in a different location
    -f src/ai_assistant/plugins/trading_plugin.py
)

# Define the high-level goal for the specialist.
query=$(cat <<'EOF'
Perform a final, comprehensive architectural review of the entire 'ai_assistant' application. The review must be based on all attached Python source files. A key focus of this review must be the analysis of the architectural trade-off between prompt safety/explicitness and token economy, using 'prompt_builder.py' as the primary case study. The final report should assess whether the current balance is appropriate and suggest any potential optimizations.
EOF
)

# --- Execution ---
# Run the AI assistant with the configured parameters.
echo "🚀 Invoking the Architecture Reviewer for a full application audit..."
ai --new-session --persona "$specialist_persona" "${files_to_review[@]}" "$query"