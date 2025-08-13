# src/ai_assistant/kernel.py
import sys
from typing import Dict, Any, List, Optional

from .persona_loader import PersonaLoader
from .context_optimizer import ContextOptimizer
from .planner import Planner
from .prompt_builder import PromptBuilder
from .response_handler import ResponseHandler
from .tools import TOOL_REGISTRY
from .config import ai_settings
import asyncio


async def orchestrate_agent_run(
    query: str,
    history: List[Dict[str, Any]],
    persona_alias: Optional[str] = None,
    is_autonomous: bool = False,
    ) -> Dict[str, Any]:

    timings = {}
    
    # --- PERSONA LOADING ---
    persona_content = None
    if persona_alias:
        loader = PersonaLoader()
        try:
            persona_content = loader.load_persona_content(persona_alias)
        except (RecursionError, FileNotFoundError) as e:
            error_msg = f"🛑 HALTING: Could not load persona '{persona_alias}'. Reason: {e}"
            print(error_msg, file=sys.stderr)
            return {
                "response": error_msg, 
                "synthesis_prompt": "",
                }

    # --- PRE-PROCESSING & PLANNING ---        
    optimizer = ContextOptimizer()
    optimized_query = optimizer.trim_to_limit(query)
    if len(optimized_query) < len(query):
        print(f"ℹ️  Context has been truncated to fit the token limit.")

    planner = Planner()
    plan, planning_duration = await planner.create_plan(optimized_query, history, persona_content)
    timings["planning"] = planning_duration # --- Store planning time ---
    
    if not plan or all(not step.get("tool_name") for step in plan):
        print("📝 No tool execution required. Generating direct response...")
        prompt_builder = PromptBuilder()
        direct_prompt = prompt_builder.build_synthesis_prompt(query, history, ["<Observation>No tool execution was required for this query.</Observation>"], persona_content)
        response_handler = ResponseHandler()
        synthesis_model = ai_settings.model_selection.synthesis
        
        synthesis_result = await response_handler.call_api(direct_prompt, model=synthesis_model)
        timings["synthesis"] = synthesis_result["duration"] # --- Store synthesis time ---
        
        return {
            "response": synthesis_result["content"],
            "synthesis_prompt": direct_prompt,
            "timings": timings
        }


    # --- ADAPTIVE AGENT KERNEL ---
    print("🚀 Executing adaptive plan...")
    observations = []
    step_results: Dict[int, str] = {}
    any_tool_succeeded = False
    any_risky_action_denied = False

    # 1. Evaluate Condition with Type Safety
    for i, step in enumerate(plan):
        step_num = i + 1

        if "condition" in step:
            cond = step["condition"]
            # The planner might use 'from_tool' or 'from_step'. We need to find the source step's result.
            # This logic is simplified; a real implementation might need a more robust way to map tool names to step numbers.
            # For now, we assume 'from_step' is provided as an integer.
            from_step_num = cond.get("from_step")
            if from_step_num is None:
                 print(f"  - ⚠️  Warning: Conditional step {step_num} is missing 'from_step'. Skipping condition check.")
            else:
                prev_result = step_results.get(from_step_num, "")
                
                condition_met = True # Assume condition is met unless a check fails
                
                if "in" in cond:
                    check_value = cond["in"]
                    # Handle the case where the check value or the result is None
                    if check_value is None:
                        if prev_result is not None and prev_result.strip() != "":
                            condition_met = False
                    elif prev_result is None or str(check_value) not in str(prev_result):
                        condition_met = False

                if "not_in" in cond:
                    check_value = cond["not_in"]
                    # Handle the case where the check value or the result is None
                    if check_value is None:
                        if prev_result is None or prev_result.strip() == "":
                            condition_met = False
                    elif prev_result is not None and str(check_value) in str(prev_result):
                        condition_met = False
                
                if not condition_met:
                    print(f"  - Skipping Step {step_num} because condition was not met.")
                    continue

        # 2. Execute Tool (The rest of the loop remains the same)
        tool_name = step.get("tool_name")
        args = step.get("args") or {}

        print(f"  - Executing Step {step_num}: {tool_name}({args})")
        tool = TOOL_REGISTRY.get_tool(tool_name)
        if tool:
            if tool.is_risky and not is_autonomous:
                confirm = await asyncio.to_thread(input, "      Proceed? [y/N]: ")
                if confirm.lower().strip() != 'y':
                    print("    🚫 Action denied by user. Skipping step.")
                    observations.append(f"<Observation step='{step_num}' tool='{tool_name}' args='{args}'>\nAction denied by user.\n</Observation>")
                    any_risky_action_denied = True
                    continue

            try:
                success, result = tool(**args)
                step_results[step_num] = result # Store result for future conditions

                if success:
                    observations.append(f"<Observation step='{step_num}' tool='{tool_name}' args='{args}'>\n{result}\n</Observation>")
                    print(f"    ✅ Success.")
                    any_tool_succeeded = True
                else:
                    error_msg = f"<Observation step='{step_num}' tool='{tool_name}' args='{args}'>\nError: {result}\n</Observation>"
                    observations.append(error_msg)
                    print(f"    ❌ Failure: {result}")
            except Exception as e:
                error_msg = f"<Observation step='{step_num}' tool='{tool_name}'>\nCritical Error: {e}\n</Observation>"
                observations.append(error_msg)
                print(f"    ❌ CRITICAL FAILURE: {e}")
        else:
            observations.append(f"<Observation step='{step_num}' tool='{tool_name}'>Error: Tool not found.</Observation>")
            print(f"    ❌ Failure: Tool '{tool_name}' not found.")

    # --- SYNTHESIS ---
    if any_risky_action_denied and not any_tool_succeeded:
        error_msg = "I was unable to complete the task because a necessary action was denied by the user for safety reasons."
        print(f"\n🛑 {error_msg}")
        return {
            "response": error_msg, 
            "synthesis_prompt": "",
            }
    
    # --- Conditional prompt compression ---
    # This logic applies the approved optimizations only when the context is large,
    # preserving maximum prompt fidelity for normal requests.

    use_compact_protocol = False
    threshold = ai_settings.context_optimizer.prompt_compression_threshold
    if threshold > 0:
        temp_history_str = " ".join(turn['content'] for turn in history)
        temp_observations_str = " ".join(observations)
        estimated_input = query + temp_history_str + temp_observations_str
        estimated_tokens = optimizer.estimate_tokens(estimated_input)

        if estimated_tokens > threshold:
            print(f"ℹ️  Context size ({estimated_tokens} tokens) exceeds threshold ({threshold}). Using compact prompt format.")
            use_compact_protocol = True

    print("📝 Synthesizing final response from observations...")
    prompt_builder = PromptBuilder()
    synthesis_prompt = prompt_builder.build_synthesis_prompt(
        query,
        history,
        observations,
        persona_content,
        use_compact_protocol=use_compact_protocol,
    )
    response_handler = ResponseHandler()
    synthesis_model = ai_settings.model_selection.synthesis
    synthesis_result = await response_handler.call_api(synthesis_prompt, model=synthesis_model)
    timings["synthesis"] = synthesis_result["duration"] # --- Store synthesis time ---
    final_response = synthesis_result["content"]
   
    return {
        "response": final_response,
        "synthesis_prompt": synthesis_prompt,
        "timings": timings,
        }