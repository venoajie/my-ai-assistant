# src/ai_assistant/kernel.py

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import time 

import structlog

from .config import ai_settings
from .data_models import ExecutionPlan, PlanStep
from .data_models import ExecutionPlan, CritiqueResponse
from .llm_client_factory import get_instructor_client 
from .persona_loader import PersonaLoader
from .plan_validator import generate_plan_expectation, check_plan_compliance
from .planner import Planner
from .prompt_builder import PromptBuilder
from .query_expander import gather_high_level_context, expand_query_with_context
from .response_handler import ResponseHandler
from .plugins.rag_plugin import RAGContextPlugin
from .tools import TOOL_REGISTRY
from .utils.context_optimizer import ContextOptimizer
from .utils.result_presenter import highlight_critique
from .utils.colors import Colors

logger = structlog.get_logger(__name__)


async def _generate_refactored_code(
    file_path_str: str, 
    instructions: str,
    ) -> str: # Modified to always return a string
    """Helper function to perform the LLM call for code refactoring."""
    file_path = Path(file_path_str)
    if not file_path.exists():
        logger.warning("File to refactor not found, skipping.", file=file_path_str)
        return "" # Return empty string on failure
    
    logger.info("Generating refactored content for plan...", file=file_path_str)
    original_content = file_path.read_text(encoding='utf-8')
    
    prompt = f"""You are an expert code refactoring agent. Your sole task is to modify the provided source code based on the user's instructions. You must return only the complete, final, modified code file. Do not add any commentary, explanations, or markdown formatting.

<Instructions>
{instructions}
</Instructions>

<OriginalCode path="{file_path_str}">
{original_content}
</OriginalCode>

Modified Code:"""
    
    handler = ResponseHandler()
    synthesis_model = ai_settings.model_selection.synthesis
    result = await handler.call_api(prompt, model=synthesis_model, generation_config={"temperature": 0.0})
    
    # --- MODIFIED: Check for API call failure indicated by "ERROR:" prefix ---
    if result["content"].strip().startswith("❌ ERROR:"):
        logger.error("Code generation API call failed.", file=file_path_str, error=result["content"])
        return "" # Return empty string on failure

    refactored_content = result["content"].strip()

    if not refactored_content:
        logger.error("Refactoring agent returned empty content. Skipping file.", file=file_path_str)
        return "" # Return empty string on failure
    
    return refactored_content


async def _expand_refactoring_workflow_plan(
    workflow_step: PlanStep,
    ) -> Tuple[bool, List[PlanStep]]:
    """
    Expands a single 'execute_refactoring_workflow' step into a sequence of
    deterministic steps by calling the LLM to generate code.
    """
    args = workflow_step.args
    branch_name = args.get("branch_name")
    commit_message = args.get("commit_message")
    instructions = args.get("refactoring_instructions")
    files_to_refactor = args.get("files_to_refactor", [])
    
    if not all([branch_name, commit_message, instructions, files_to_refactor]):
        logger.error("Invalid refactoring workflow step, missing required arguments.")
        return False, []

    new_steps = []
    
    # 1. Create Branch
    new_steps.append(PlanStep(
        thought="Start the workflow by creating a new git branch.",
        tool_name="git_create_branch",
        args={"branch_name": branch_name}
    ))

    # 2. Generate and Write Files
    successful_files = 0
    for file_path in files_to_refactor:
        refactored_content = await _generate_refactored_code(file_path, instructions)
        # --- MODIFIED: Explicitly check for non-empty content before adding steps ---
        if refactored_content:
            successful_files += 1
            new_steps.append(PlanStep(
                thought=f"Write the generated refactored content to '{file_path}'.",
                tool_name="write_file",
                args={"path": file_path, "content": refactored_content}
            ))
            new_steps.append(PlanStep(
                thought=f"Stage the modified file '{file_path}' for commit.",
                tool_name="git_add",
                args={"path": file_path}
            ))

    # --- MODIFIED: Only commit if at least one file was successfully generated ---
    if successful_files > 0:
        # 3. Commit
        new_steps.append(PlanStep(
            thought="Commit all staged changes with the planned message.",
            tool_name="git_commit",
            args={"commit_message": commit_message}
        ))
    else:
        logger.error("Code generation failed for all files. No commit will be made.")
        # Return failure if no files were processed.
        return False, []
    
    return True, new_steps

async def orchestrate_agent_run(
    query: str,
    history: List[Dict[str, Any]],
    persona_alias: Optional[str] = None,
    is_autonomous: bool = False,
    output_dir: Optional[str] = None,
    ) -> Dict[str, Any]:

    metrics = {"timings": {}, "tokens": {"planning": {}, "critique": {}, "synthesis": {}}}
    timings = metrics["timings"]

    persona_directives: Optional[str] = None
    persona_context: Optional[str] = None
    allowed_tools: Optional[List[str]] = None
    
    if persona_alias:
        loader = PersonaLoader()
        try:            
            persona_directives, persona_context, allowed_tools = loader.load_persona_content(persona_alias)
        except (RecursionError, FileNotFoundError) as e:
            error_msg = f"🛑 HALTING: Could not load persona '{persona_alias}'. Reason: {e}"
            logger.error("Persona loading failed", persona=persona_alias, error=str(e))
            return {"response": error_msg, "metrics": metrics}


    # --- CONTEXT-AWARE QUERY EXPANSION (REFACTORED) ---
    # 1. Gather high-level context from auto-injected files
    auto_inject_files = ai_settings.general.auto_inject_files or []
    high_level_context_str = gather_high_level_context(auto_inject_files)

    # 2. Expand the query using the centralized function
    effective_query = await expand_query_with_context(query, high_level_context_str)

    # --- RAG CONTEXT INJECTION ---            
    logger.info("Attempting to retrieve RAG context to enhance planning.")
    rag_content = "" # Ensure rag_content is always defined for direct response path
    system_note = None
    try:
        rag_plugin = RAGContextPlugin(project_root=Path.cwd())
        # Use the 'effective_query' instead of the original 'query'
        success, rag_content_result = rag_plugin.get_context(effective_query, [])
                
        if success and rag_content_result:
            rag_content = rag_content_result # Store the content for later use
            logger.info("Injecting RAG context into planning history.")
            system_note = f"<SystemNote>The following context was retrieved from the RAG system to aid in planning:\n{rag_content}</SystemNote>"
        elif not success:
            print(f"{Colors.YELLOW}⚠️  RAG Warning: {rag_content_result}{Colors.RESET}", file=sys.stderr)
            # Explicitly inform the AI planner of the failure.
            system_note = f"<SystemNote>CRITICAL: The RAG context retrieval system failed with the following error: {rag_content_result}. You must proceed without this information.</SystemNote>"
            
    except Exception as e:
        system_note = f"<SystemNote>CRITICAL: The RAG context retrieval system failed with an unexpected exception: {e}. You must proceed without this information.</SystemNote>"
        logger.warning("Could not retrieve RAG context due to an unexpected error", error=str(e))
        print(f"{Colors.YELLOW}⚠️  RAG Warning: Could not retrieve context due to an unexpected error. Check logs for details.{Colors.RESET}", file=sys.stderr)
    
    if system_note:
        history.append({"role": "system", "content": system_note})
            
    optimizer = ContextOptimizer()
    threshold = ai_settings.context_optimizer.prompt_compression_threshold
    use_compact_protocol = False
    current_history_str = " ".join(turn['content'] for turn in history)
    current_input = query + current_history_str
    current_tokens = optimizer.estimate_tokens(current_input)
    if threshold > 0 and current_tokens > threshold:
        logger.info("Context still large after distillation. Using compact prompt format.", tokens=current_tokens)
        use_compact_protocol = True

    plan_expectation = generate_plan_expectation(query)
    
    planner = Planner()
    max_retries = 2
    plan = None
    for attempt in range(max_retries):
        plan, planning_result = await planner.create_plan(
             query,
             history,
             persona_context,
             use_compact_protocol,
             is_output_mode=(output_dir is not None),
             plan_expectation=plan_expectation, 
         )
        
        if plan is None:
            halt_message = "HALTED: The AI planner failed to generate a plan due to a critical internal error. Check the logs for details."
            logger.critical(halt_message)
            return {"response": halt_message, "metrics": metrics}        
        
        is_compliant, compliance_reason = check_plan_compliance(plan, plan_expectation)
        
        persona_tools_valid = True
        persona_reason = ""
        if allowed_tools:
            for step in plan:
                if step.tool_name not in allowed_tools:
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
    if not plan or not plan.steps or all(not step.tool_name for step in plan):
        print("📝 No tool execution required. Generating direct response...")
        
        direct_observations = ["<Observation>No tool execution was required for this query.</Observation>"]
        if rag_content:
            direct_observations = [f"<Observation step='0' tool='RAG_retrieval'>\n{rag_content}\n</Observation>"]

        direct_prompt = prompt_builder.build_synthesis_prompt(
            query=query,
            history=history,
            observations=direct_observations,
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
    if plan and plan.steps and any(step.tool_name for step in plan):

        critique_model_name = ai_settings.model_selection.critique
        logger.info("Submitting plan for adversarial validation.",
                    model=critique_model_name
                    )
        start_time = time.monotonic()
        try:
            critic_loader = PersonaLoader()
            critic_alias = ai_settings.general.critique_persona_alias
            _, critic_context, _ = critic_loader.load_persona_content(critic_alias)
            
            critique_prompt = prompt_builder.build_critique_prompt(
                query=query,
                plan=plan,
                persona_context=critic_context
            )
            
            critique_client = get_instructor_client(critique_model_name)
            critique_gen_config = ai_settings.generation_params.critique.model_dump(exclude_none=True)

            critique_response = await critique_client.chat.completions.create(
                model=critique_model_name,
                response_model=CritiqueResponse,
                messages=[{"role": "user", "content": critique_prompt}],
                **critique_gen_config,
            )

            critique = critique_response.critique
            optimizer = ContextOptimizer()
            prompt_tokens = optimizer.estimate_tokens(critique_prompt)
            response_tokens = optimizer.estimate_tokens(critique)
            
            metrics["timings"]["critique"] = time.monotonic() - start_time
            metrics["tokens"]["critique"] = {"prompt": prompt_tokens, "response": response_tokens, "total": prompt_tokens + response_tokens}
            logger.info("Critique received and validated successfully.")
        except Exception as e:
            critique = "Plan validation step failed due to an internal error."
            logger.warning("Could not perform plan validation.", error=str(e))
            
    # --- DYNAMIC PLAN EXPANSION FOR WORKFLOWS ---
    # This is where we centralize the "thinking" for complex tools.
    # We check if the plan contains a workflow tool and expand it before execution.
    if len(plan) == 1 and plan[0].tool_name == "execute_refactoring_workflow":
        logger.info("Detected refactoring workflow. Expanding plan with generated code...")
        success, expanded_steps = await _expand_refactoring_workflow_plan(plan[0])
        if success:
            plan.steps = expanded_steps
            logger.info("Plan successfully expanded into deterministic steps.", step_count=len(plan))
        else:
            error_msg = "Failed to expand refactoring workflow. Halting execution."
            logger.error(error_msg)
            return {"response": error_msg, "metrics": metrics}

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
    if rag_content:
        observations.append(f"<Observation step='0' tool='RAG_retrieval'>\n{rag_content}\n</Observation>")

    step_results: Dict[int, str] = {}
    any_risky_action_denied = False

    for i, step in enumerate(plan):
        step_num = i + 1
        if step.condition:
            cond = step.condition
            from_step_num = cond.from_step
            
            if from_step_num is None:
                 print(f"  - ⚠️  Warning: Conditional step {step_num} is missing 'from_step'. Skipping condition check.")
            else:
                prev_result = step_results.get(from_step_num, "")
                condition_met = True
                if cond.in_output and (prev_result is None or str(cond.in_output) not in str(prev_result)):
                    condition_met = False
                if cond.not_in_output and (prev_result is not None and str(cond.not_in_output) in str(prev_result)):
                    condition_met = False
                if not condition_met:
                    print(f"  - Skipping Step {step_num} because condition was not met.")
                    continue
        
        tool_name = step.tool_name
        args = step.args or {}
        print(f"  - Executing Step {step_num}: {tool_name}({args})")
        
        tool = TOOL_REGISTRY.get_tool(tool_name)
        if tool:
            if tool.is_risky and not is_autonomous:
                if critique:
                    print("\n--- 🧐 ADVERSARIAL CRITIQUE ---")
                    print(highlight_critique(critique))
                    print("----------------------------")
                    
                print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  DISCLAIMER: Review the plan and critique carefully.{Colors.RESET}")
                print(f"{Colors.YELLOW}   The AI can make mistakes or generate incorrect code.{Colors.RESET}")
                print(f"{Colors.YELLOW}   You are responsible for approving this action.{Colors.RESET}")
                    
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
    final_synthesis_query = query
        
    last_tool_run_successful = "Error:" not in observations[-1] and "Critical Error:" not in observations[-1]
    
    if len(plan) == 1 and plan[0].tool_name and \
        TOOL_REGISTRY.get_tool(plan[0].tool_name).is_risky and \
            last_tool_run_successful:
        print("   - Action was successful. Switching to a simple confirmation prompt for synthesis.")
        final_synthesis_query = (
            "The requested action was completed successfully. Your task is to briefly and clearly "
            "inform the user of this success. Use the content of the <ToolObservations> to state "
            "what was done."
        )

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
        query=final_synthesis_query,
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
    plan: ExecutionPlan,
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
    
    # --- REFACTORED: The plan is now always deterministic, so this logic is simpler ---
    for step in plan:
        tool_name = step.tool_name
        args = step.args
        thought = step.thought
        
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