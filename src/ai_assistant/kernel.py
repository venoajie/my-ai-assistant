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
                "timings": timings,
                }

    # --- PRE-PROCESSING & COMPRESSION LOGIC ---
    optimizer = ContextOptimizer()
    optimized_query = optimizer.trim_to_limit(query)
    if len(optimized_query) < len(query):
        print(f"ℹ️  Context has been truncated to fit the token limit.")

    # This logic must run BEFORE the planner is called to decide if planning prompt needs compact history.
    use_compact_protocol = False
    threshold = ai_settings.context_optimizer.prompt_compression_threshold
    if threshold > 0:
        temp_history_str = " ".join(turn['content'] for turn in history)
        # At this stage, there are no observations, so we estimate based on query and history.
        estimated_input = query + temp_history_str
        estimated_tokens = optimizer.estimate_tokens(estimated_input)

        if estimated_tokens > threshold:
            print(f"ℹ️  Context size ({estimated_tokens} tokens) exceeds threshold ({threshold}). Using compact prompt format for planning.")
            use_compact_protocol = True

    # --- PLANNING ---
    planner = Planner()
    plan, planning_duration = await planner.create_plan(
        optimized_query,
        history,
        persona_content,
        use_compact_protocol  # Now this variable exists and has a value
    )
    timings["planning"] = planning_duration
    
    prompt_builder = PromptBuilder()

    # --- DIRECT RESPONSE (NO TOOLS) ---
    if not plan or all(not step.get("tool_name") for step in plan):
        print("📝 No tool execution required. Generating direct response...")
        # For no-op, we don't need to worry about compact protocol as context is small.
        direct_prompt = prompt_builder.build_synthesis_prompt(
            query=query,
            history=history,
            observations=["<Observation>No tool execution was required for this query.</Observation>"],
            persona_content=persona_content,
        )
        response_handler = ResponseHandler()
        synthesis_model = ai_settings.model_selection.synthesis
        
        synthesis_result = await response_handler.call_api(direct_prompt, model=synthesis_model)
        timings["synthesis"] = synthesis_result["duration"]
        
        return {
            "response": synthesis_result["content"],
            "synthesis_prompt": direct_prompt,
            "timings": timings
        }

    # --- ADAPTIVE AGENT KERNEL (TOOL EXECUTION) ---
    print("🚀 Executing adaptive plan...")
    observations = []
    step_results: Dict[int, str] = {}
    any_tool_succeeded = False
    any_risky_action_denied = False

    for i, step in enumerate(plan):
        step_num = i + 1

        if "condition" in step:
            cond = step["condition"]
            from_step_num = cond.get("from_step")
            if from_step_num is None:
                 print(f"  - ⚠️  Warning: Conditional step {step_num} is missing 'from_step'. Skipping condition check.")
            else:
                prev_result = step_results.get(from_step_num, "")
                condition_met = True
                if "in" in cond and (prev_result is None or str(cond["in"]) not in str(prev_result)):
                    condition_met = False
                if "not_in" in cond and (prev_result is not None and str(cond["not_in"]) in str(prev_result)):
                    condition_met = False
                if not condition_met:
                    print(f"  - Skipping Step {step_num} because condition was not met.")
                    continue

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
                step_results[step_num] = result
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
            "timings": timings,
            }
            
    # Join observations into a single string for analysis and prompt building.
    observation_text = "\n".join(observations)

    # Precise Failure Detection
    is_failure_state = False
    for obs in observations:
        if obs.startswith("<Observation") and ("Error:" in obs or "Critical Error:" in obs or "Action denied by user" in obs):
            is_failure_state = True
            break

    # Re-run compression check for synthesis, now including the observations.
    use_compact_protocol = False
    if threshold > 0:
        temp_history_str = " ".join(turn['content'] for turn in history)
        estimated_input = query + temp_history_str + observation_text
        estimated_tokens = optimizer.estimate_tokens(estimated_input)
        if estimated_tokens > threshold:
            print(f"ℹ️  Context size ({estimated_tokens} tokens) exceeds threshold ({threshold}). Using compact prompt format for synthesis.")
            use_compact_protocol = True

    print("📝 Synthesizing final response from observations...")

    # Dynamic Persona Selection
    final_persona_content = persona_content
    if is_failure_state:
        print("   ...A failure was detected. Switching to Debugging Analyst persona...")
        loader = PersonaLoader()
        try:
            final_persona_content = loader.load_persona_content('patterns/da-1')
        except (FileNotFoundError, RecursionError) as e:
            print(f"   - ⚠️ CRITICAL: Could not load failure persona 'da-1'. Reason: {e}")
            final_persona_content = "CRITICAL: The primary task failed, and the 'da-1' recovery persona could not be loaded. Your only job is to report the raw tool observations to the user clearly."

    if not final_persona_content:
        print("   - ⚠️ Warning: No persona was loaded. The agent will use a generic, system-defined personality.")
        final_persona_content = "You are a helpful AI assistant. Answer the user's query based on the provided context and observations."

    # Final Prompt Construction and API Call
    synthesis_prompt = prompt_builder.build_synthesis_prompt(
        query=query,
        history=history,
        observations=observations,
        persona_content=final_persona_content,
        use_compact_protocol=use_compact_protocol
    )
    response_handler = ResponseHandler()
    synthesis_model = ai_settings.model_selection.synthesis
    synthesis_result = await response_handler.call_api(synthesis_prompt, model=synthesis_model)
    timings["synthesis"] = synthesis_result