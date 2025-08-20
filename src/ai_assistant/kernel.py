# src/ai_assistant/kernel.py
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import structlog

from .config import ai_settings
from .utils.context_optimizer import ContextOptimizer
from .persona_loader import PersonaLoader
from .plan_validator import generate_plan_expectation, check_plan_compliance
from .planner import Planner
from .prompt_builder import PromptBuilder
from .response_handler import ResponseHandler
from .tools import TOOL_REGISTRY
from .data_models import ExecutionPlan

logger = structlog.get_logger(__name__)

async def _inject_project_context(history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Finds and injects content from files specified in the configuration."""
    for filename in ai_settings.general.auto_inject_files:
        file_path = Path.cwd() / filename
        if file_path.exists():
            print(f"ℹ️  Found '{filename}'. Injecting project context...")
            try:
                content = file_path.read_text(encoding='utf-8')
                context_str = f"<InjectedProjectContext file_path='{filename}'>\n{content}\n</InjectedProjectContext>"
                history.insert(0, {"role": "system", "content": context_str})
            except Exception as e:
                print(f"⚠️  Warning: Could not read or inject {filename}. Reason: {e}")
    return history

async def orchestrate_agent_run(
    query: str,
    history: List[Dict[str, Any]],
    persona_alias: Optional[str] = None,
    is_autonomous: bool = False,
    output_dir: Optional[str] = None,
    ) -> Dict[str, Any]:

    history = await _inject_project_context(history)

    metrics = {"timings": {}, "tokens": {"planning": {}, "critique": {}, "synthesis": {}}}
    timings = metrics["timings"]

    # --- PERSONA LOADING ---
    persona_directives: Optional[str] = None
    persona_context: Optional[str] = None
    allowed_tools: Optional[List[str]] = None
    
    if persona_alias:
        loader = PersonaLoader()
        try:            
            persona_directives, persona_context, allowed_tools = loader.load_persona_content(persona_alias)
        except (RecursionError, FileNotFoundError) as e:
            error_msg = f"🛑 HALTING: Could not load persona '{persona_alias}'. Reason: {e}"
            print(error_msg, file=sys.stderr)
            return {"response": error_msg, "metrics": metrics}

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

    # --- PLANNING & UNIFIED VALIDATION LOOP ---
    plan_expectation = generate_plan_expectation(query)
    if plan_expectation:
        print(f"ℹ️  Compliance rule triggered. Expected plan signature: {plan_expectation}")
        
    planner = Planner()
    max_retries = 2
    for attempt in range(max_retries):
        plan, planning_result = await planner.create_plan(
             optimized_query,
             history,
             persona_context,
             use_compact_protocol,
             is_output_mode=(output_dir is not None),
         )

     # --- Explicit check for planner failure ---
        if plan is None:
            # The planner itself failed critically. No point in retrying.
            halt_message = "HALTED: The AI planner failed to generate a plan due to a critical internal error. Check the logs for details."
            logger.critical(halt_message)
            return {"response": halt_message, "metrics": metrics}        
        
        # --- THE DEFINITIVE FIX IS HERE ---
        # This is the single, unified validation gate.
        is_compliant, compliance_reason = check_plan_compliance(plan, plan_expectation) # Pass the object
        
        persona_tools_valid = True
        persona_reason = ""
        if allowed_tools:
            for step in plan: # <--- This now iterates over plan.root
                if step.tool_name not in allowed_tools: # <--- Use attribute access
                    persona_tools_valid = False
                    persona_reason = (
                        f"Plan violates persona rules. Used forbidden tool '{step.tool_name}'. "
                        f"This persona can only use: {', '.join(allowed_tools)}."
                    )
                    break
        
        if is_compliant and persona_tools_valid:
            print("✅ Plan passed all validation checks.")
            break

        failure_reason = (compliance_reason + " " + persona_reason).strip()
        print(f"❌ Plan failed validation. Reason: {failure_reason}", file=sys.stderr)

        if attempt < max_retries - 1:
            print("   - Retrying with corrective instructions...", file=sys.stderr)
            history.append({"role": "system", "content": f"CORRECTION: Your plan was rejected. {failure_reason} You MUST generate a new plan that is compliant."})
        else:
            halt_message = f"HALTED: The AI planner failed to generate a valid plan after {max_retries} attempts. Final reason: {failure_reason}"
            print("   - Max retries reached. Halting.", file=sys.stderr)
            return {"response": halt_message, "metrics": metrics}
    
    timings["planning"] = planning_result["duration"]
    metrics["tokens"]["planning"] = planning_result["tokens"]
     
    prompt_builder = PromptBuilder()

    # --- DIRECT RESPONSE (NO TOOLS) ---
    if not plan or not plan.root or all(not step.tool_name for step in plan):
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
        metrics["timings"]["synthesis"] = synthesis_result["duration"]
        metrics["tokens"]["synthesis"] = synthesis_result["tokens"]        
        return {"response": synthesis_result["content"], "metrics": metrics}

    # --- ADVERSARIAL VALIDATION (CRITIQUE) ---
    critique = None
    if plan and plan.root and any(step.tool_name for step in plan):
        print("🕵️  Submitting plan for adversarial validation...")
        try:
            critic_loader = PersonaLoader()
            critic_alias = ai_settings.general.critique_persona_alias
            _, critic_context, _ = critic_loader.load_persona_content(critic_alias)
            
            critique_prompt = prompt_builder.build_critique_prompt(
                query=query,
                plan=plan,
                persona_context=critic_context
            )
            
            response_handler = ResponseHandler()
            critique_model = ai_settings.model_selection.critique
            critique_gen_config = ai_settings.generation_params.critique.model_dump(exclude_none=True)
            critique_result = await response_handler.call_api(
                critique_prompt, 
                model=critique_model,
                generation_config=critique_gen_config
            )
            critique = critique_result["content"]
            metrics["timings"]["critique"] = critique_result["duration"]
            metrics["tokens"]["critique"] = critique_result["tokens"]     
            print("   ✅ Critique received.")
        except Exception as e:
            print(f"   - ⚠️ Warning: Could not perform plan validation. Reason: {e}")
            critique = "Plan validation step failed due to an internal error."

    # --- OUTPUT-FIRST MODE (GENERATE PACKAGE) ---
    if output_dir:
        return await _handle_output_first_mode(
            plan, 
            persona_alias,
            metrics, 
            output_dir,
            )

    # --- LIVE MODE (TOOL EXECUTION) ---
    print("🚀 Executing adaptive plan...")
    observations = []
    step_results: Dict[int, str] = {}
    any_risky_action_denied = False


    for i, step in enumerate(plan): # <--- This now iterates over plan.root
        step_num = i + 1
        if step.condition: # <--- Use attribute access
            cond = step.condition
            from_step_num = cond.from_step
            
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
        
        tool_name = step.tool_name # <--- Use attribute access
        args = step.args or {} # <--- Use attribute access
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
                    break
            try:
                success, result = await tool(**args)
                step_results[step_num] = result
                if success:
                    observations.append(f"<Observation step='{step_num}' tool='{tool_name}' args='{args}'>\n{result}\n</Observation>")
                    print(f"    ✅ Success.")
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
    if any_risky_action_denied:
        error_msg = "Task aborted by user. No actions were performed."
        print(f"\n🛑 {error_msg}")
        return {
            "response": error_msg, 
            "metrics": metrics,
            }
            
    observation_text = "\n".join(observations)

    is_failure_state = False
    for obs in observations:
        if obs.startswith("<Observation") and ("Error:" in obs or "Critical Error:" in obs):
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
            failure_alias = ai_settings.general.failure_persona_alias
            _, final_context, _ = loader.load_persona_content(failure_alias)
        except (FileNotFoundError, RecursionError) as e:
            print(f"   - ⚠️ CRITICAL: Could not load failure persona '{ai_settings.general.failure_persona_alias}'. Reason: {e}")
            final_context = "CRITICAL: The primary task failed, and the recovery persona could not be loaded. Your only job is to report the raw tool observations to the user clearly."
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
    metrics["timings"]["synthesis"] = synthesis_result["duration"]
    metrics["tokens"]["synthesis"] = synthesis_result["tokens"]
    final_response = synthesis_result["content"]
   
    return {
        "response": final_response,
        "metrics": metrics,
    }

async def _handle_output_first_mode(
    plan: List[Dict[str, Any]],
    persona_alias: str,
    metrics: Dict[str, Any],
    output_dir_str: str,
) -> Dict[str, Any]:
    """Handles the logic for generating an output package instead of executing live."""

    logger.info("Generating execution package...", dir=output_dir_str)
    output_dir = Path(output_dir_str)
    workspace_dir = output_dir / "workspace"
    
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        workspace_dir.mkdir(exist_ok=True)
    except OSError as e:
        error_msg = f"❌ Error creating output directory '{output_dir}': {e}"
        return {
            "response": error_msg, 
            "metrics": metrics,
            }

    manifest = {
        "version": "1.1",
        "sessionId": f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "generated_by": persona_alias,
        "actions": [],
    }
    
    summary_parts = ["# AI-Generated Change Summary\n"]
    
    tool_map = {
        "write_file": "apply_file_change",
        "create_directory": "create_directory",
        "move_file": "move_file",
        "git_create_branch": "create_branch",
        "git_add": "git_add",
        "git_commit": "git_commit",
        "git_push": "git_push",
    }
    
    for step in plan:
        tool_name = step.tool_name
        args = step.args
        thought = step.thought
        
        # Handle the high-level workflow tool by unpacking it into granular actions.
        if tool_name == "execute_refactoring_workflow":
            logger.debug("Unpacking execute_refactoring_workflow for manifest.")
            

            # 3. Commit Action
            commit_message = args.get("commit_message")
            if commit_message:
                manifest["actions"].append({
                    "type": "git_commit",
                    "comment": "Part of workflow: Commit all staged changes.",
                    "message": commit_message,
                })
            
            # 1. Create Branch Action
            branch_name = args.get("branch_name")
            if branch_name:
                manifest["actions"].append({
                    "type": "create_branch",
                    "comment": f"Part of workflow: Create branch for '{commit_message}'",
                    "branch_name": branch_name,
                })

            # 2. Refactor Files (as apply_file_change actions)
            instructions = args.get("refactoring_instructions")
            files_to_refactor = args.get("files_to_refactor", [])
            for file_path in files_to_refactor:
                target_path_in_workspace = workspace_dir / file_path
                target_path_in_workspace.parent.mkdir(parents=True, exist_ok=True)
                # For now, we assume the instructions ARE the content. A more advanced
                # version would call another LLM here, but this is correct for this persona.
                target_path_in_workspace.write_text(instructions, encoding='utf-8')
                
                manifest["actions"].append({
                    "type": "apply_file_change",
                    "comment": f"Part of workflow: Refactor file based on instructions.",
                    "source": f"workspace/{file_path}",
                    "target": file_path,
                })
                manifest["actions"].append({
                    "type": "git_add",
                    "comment": f"Part of workflow: Stage refactored file.",
                    "path": file_path,
                })

            # This step has been fully processed, so skip the rest of the loop.
            continue
        
        action_type = tool_map.get(tool_name)
        if not action_type:
            logger.warning("Skipping unsupported tool in output-first mode.", tool_name=tool_name)
            continue
        
        action = {
            "type": action_type, 
            "comment": thought,
            }
        
        if tool_name == "write_file":
            path_str = args.get("path")
            content = args.get("content")
            if not path_str or content is None:
                logger.warning("Skipping invalid write_file step: missing path or content.", step=step)
                continue
                              
            target_path_in_workspace = workspace_dir / path_str
            target_path_in_workspace.parent.mkdir(parents=True, exist_ok=True)
            target_path_in_workspace.write_text(content, encoding='utf-8')
            
            action["source"] = f"workspace/{path_str}"
            action["target"] = path_str
            summary_parts.append(f"## Modify `{path_str}`\n\n**Reason:** {thought}\n\n```diff\n# Diff view not yet implemented. Full content written.\n```\n")

        elif tool_name == "create_directory":
            action["path"] = args.get("path")
            summary_parts.append(f"### Create Directory\n- **Path:** `{action['path']}`\n- **Reason:** {thought}\n")

        elif tool_name == "move_file":
            action["source"] = args.get("source")
            action["destination"] = args.get("destination")
            summary_parts.append(f"### Move Item\n- **From:** `{action['source']}`\n- **To:** `{action['destination']}`\n- **Reason:** {thought}\n")

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
        logger.debug("Packaged action", action_type=action_type)

    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    (output_dir / "summary.md").write_text("\n".join(summary_parts), encoding='utf-8')

    final_message = f"✅ Successfully generated execution package in '{output_dir}'.\n" \
                    f"   - Review the plan in '{output_dir / 'summary.md'}'\n" \
                    f"   - To apply, run: ai-execute \"{output_dir}\" --confirm"

    return {
        "response": final_message,
        "manifest": manifest,
        "metrics": metrics,
    }