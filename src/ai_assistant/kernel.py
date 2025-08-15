# src/ai_assistant/kernel.py
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from .config import ai_settings
from .context_optimizer import ContextOptimizer
from .persona_loader import PersonaLoader
from .planner import Planner
from .prompt_builder import PromptBuilder
from .response_handler import ResponseHandler
from .tools import TOOL_REGISTRY


async def orchestrate_agent_run(
    query: str,
    history: List[Dict[str, Any]],
    persona_alias: Optional[str] = None,
    is_autonomous: bool = False,
    output_dir: Optional[str] = None,
    ) -> Dict[str, Any]:

    timings = {}
    
    # --- PERSONA LOADING ---
    persona_directives: Optional[str] = None
    persona_context: Optional[str] = None
    if persona_alias:
        loader = PersonaLoader()
        try:
            # The loader now returns a tuple of (directives, context)
            persona_directives, persona_context = loader.load_persona_content(persona_alias)
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

    use_compact_protocol = False
    threshold = ai_settings.context_optimizer.prompt_compression_threshold
    if threshold > 0:
        temp_history_str = " ".join(turn['content'] for turn in history)
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
        persona_context,
        use_compact_protocol,
        is_output_mode=(output_dir is not None)
    )
    timings["planning"] = planning_duration
    
    prompt_builder = PromptBuilder()

    # --- DIRECT RESPONSE (NO TOOLS) ---
    if not plan or all(not step.get("tool_name") for step in plan):
        print("📝 No tool execution required. Generating direct response...")
        direct_prompt = prompt_builder.build_synthesis_prompt(
            query=query,
            history=history,
            observations=["<Observation>No tool execution was required for this query.</Observation>"],
            persona_context=persona_context or "You are a helpful AI assistant.",
            directives=persona_directives
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

    # --- ADVERSARIAL VALIDATION (CRITIQUE) ---
    critique = None
    if plan and any(step.get("tool_name") for step in plan):
        print("🕵️  Submitting plan for adversarial validation...")
        try:
            critic_loader = PersonaLoader()
            # The critic persona is hardcoded for reliability
            _, critic_context = critic_loader.load_persona_content('patterns/pva-1')
            
            critique_prompt = prompt_builder.build_critique_prompt(
                query=query,
                plan=plan,
                persona_context=critic_context
            )
            
            response_handler = ResponseHandler()
            # Use the faster planning model for the critique
            critique_model = ai_settings.model_selection.planning
            critique_result = await response_handler.call_api(critique_prompt, model=critique_model)
            critique = critique_result["content"]
            timings["critique"] = critique_result["duration"]
            print("   ✅ Critique received.")
        except Exception as e:
            print(f"   - ⚠️ Warning: Could not perform plan validation. Reason: {e}")
            critique = "Plan validation step failed due to an internal error."


    # --- OUTPUT-FIRST MODE (GENERATE PACKAGE) ---
    if output_dir:
        return await _handle_output_first_mode(plan, persona_alias, timings, output_dir)

    # --- LIVE MODE (TOOL EXECUTION) ---
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
                if critique:
                    print("\n--- 🧐 ADVERSARIAL CRITIQUE ---")
                    print(critique)
                    print("----------------------------")
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
        return { "response": error_msg, "synthesis_prompt": "", "timings": timings }
            
    observation_text = "\n".join(observations)

    is_failure_state = False
    for obs in observations:
        if obs.startswith("<Observation") and ("Error:" in obs or "Critical Error:" in obs or "Action denied by user" in obs):
            is_failure_state = True
            break

    use_compact_protocol = False
    if threshold > 0:
        temp_history_str = " ".join(turn['content'] for turn in history)
        estimated_input = query + temp_history_str + observation_text
        estimated_tokens = optimizer.estimate_tokens(estimated_input)
        if estimated_tokens > threshold:
            print(f"ℹ️  Context size ({estimated_tokens} tokens) exceeds threshold ({threshold}). Using compact prompt format for synthesis.")
            use_compact_protocol = True

    print("📝 Synthesizing final response from observations...")

    final_directives = persona_directives
    final_context = persona_context
    if is_failure_state:
        print("   ...A failure was detected. Switching to Debugging Analyst persona...")
        loader = PersonaLoader()
        try:
            final_directives, final_context = loader.load_persona_content('patterns/da-1')
        except (FileNotFoundError, RecursionError) as e:
            print(f"   - ⚠️ CRITICAL: Could not load failure persona 'da-1'. Reason: {e}")
            final_context = "CRITICAL: The primary task failed, and the 'da-1' recovery persona could not be loaded. Your only job is to report the raw tool observations to the user clearly."
            final_directives = None

    if not final_context:
        print("   - ⚠️ Warning: No persona was loaded. The agent will use a generic, system-defined personality.")
        final_context = "You are a helpful AI assistant. Answer the user's query based on the provided context and observations."

    synthesis_prompt = prompt_builder.build_synthesis_prompt(
        query=query,
        history=history,
        observations=observations,
        persona_context=final_context,
        directives=final_directives,
        use_compact_protocol=use_compact_protocol
    )
    response_handler = ResponseHandler()
    synthesis_model = ai_settings.model_selection.synthesis
    synthesis_result = await response_handler.call_api(synthesis_prompt, model=synthesis_model)
    timings["synthesis"] = synthesis_result["duration"]
    final_response = synthesis_result["content"]
   
    return {
        "response": final_response,
        "synthesis_prompt": synthesis_prompt,
        "timings": timings,
    }

async def _handle_output_first_mode(
    plan: List[Dict[str, Any]],
    persona_alias: str,
    timings: Dict[str, float],
    output_dir_str: str,
) -> Dict[str, Any]:
    """Handles the logic for generating an output package instead of executing live."""
    print("📦 Generating execution package...")
    output_dir = Path(output_dir_str)
    workspace_dir = output_dir / "workspace"
    
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        workspace_dir.mkdir(exist_ok=True)
    except OSError as e:
        error_msg = f"❌ Error creating output directory '{output_dir}': {e}"
        return {"response": error_msg, "synthesis_prompt": "", "timings": timings}

    manifest = {
        "version": "1.0",
        "sessionId": f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "generated_by": persona_alias,
        "actions": []
    }
    
    summary_parts = ["# AI-Generated Change Summary\n"]
    
    tool_map = {
        "write_file": "apply_file_change",
        "git_create_branch": "create_branch",
        "git_add": "git_add",
        "git_commit": "git_commit",
        "git_push": "git_push",
    }

    for step in plan:
        tool_name = step.get("tool_name")
        args = step.get("args", {})
        thought = step.get("thought", "No thought provided.")
        
        action_type = tool_map.get(tool_name)
        if not action_type:
            print(f"  - ⚠️ Skipping unsupported tool '{tool_name}' in output-first mode.")
            continue

        action = {"type": action_type, "comment": thought}
        
        if tool_name == "write_file":
            path_str = args.get("path")
            content = args.get("content")
            if not path_str or content is None:
                print(f"  - ⚠️ Skipping invalid write_file step: missing path or content.")
                continue
            
            # Write content to workspace
            target_path_in_workspace = workspace_dir / path_str
            target_path_in_workspace.parent.mkdir(parents=True, exist_ok=True)
            target_path_in_workspace.write_text(content, encoding='utf-8')
            
            action["source"] = f"workspace/{path_str}"
            action["target"] = path_str
            summary_parts.append(f"## Modify `{path_str}`\n\n**Reason:** {thought}\n\n```diff\n# Diff view not yet implemented. Full content written.\n```\n")

        elif tool_name == "git_create_branch":
            action["branch_name"] = args.get("branch_name")
            summary_parts.append(f"### Create Branch\n- **Name:** `{action['branch_name']}`\n- **Reason:** {thought}\n")
        
        elif tool_name == "git_add":
            action["path"] = args.get("path")
            summary_parts.append(f"### Stage File\n- **Path:** `{action['path']}`\n")

        elif tool_name == "git_commit":
            action["message"] = args.get("commit_message")
            summary_parts.append(f"### Commit Changes\n- **Message:** `{action['message']}`\n")
        
        elif tool_name == "git_push":
            summary_parts.append(f"### Push Branch\n- Pushes the current branch to remote 'origin'.\n")

        manifest["actions"].append(action)
        print(f"  - ✅ Packaged action: {action_type}")

    # Write manifest and summary
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    (output_dir / "summary.md").write_text("\n".join(summary_parts), encoding='utf-8')

    final_message = f"✅ Successfully generated execution package in '{output_dir}'.\n" \
                    f"   - Review the plan in '{output_dir / 'summary.md'}'\n" \
                    f"   - To apply, run: ai-execute \"{output_dir}\" --confirm"

    return {
        "response": final_message,
        "manifest": manifest,
        "timings": timings
    }