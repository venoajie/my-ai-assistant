ai --new-session --persona core/SI-1 \
-f persona_manifest.yml \
-f src/ai_assistant/cli.py \
-f src/ai_assistant/config.py \
-f src/ai_assistant/context_optimizer.py \
-f src/ai_assistant/context_plugin.py \
-f src/ai_assistant/persona_loader.py \
-f src/ai_assistant/planner.py \
-f src/ai_assistant/prompt_builder.py \
-f src/ai_assistant/response_handler.py \
-f src/ai_assistant/session_manager.py \
-f src/ai_assistant/tools.py \
-f src/ai_assistant/_security_guards.py \
-f src/ai_assistant/plugins/trading_plugin.py \
"Initiate a final, comprehensive architectural review of the entire 'ai_assistant' application. The selected specialist should act as ARC-1.

The review must be based on all attached Python source files and the project's established architectural principles.

A key focus of this review must be the analysis of the architectural trade-off between prompt safety/explicitness and token economy. Use the detailed heuristics in 'prompt_builder.py' as the primary case study for this analysis. The final report should assess whether the current balance is appropriate and suggest any potential optimizations."