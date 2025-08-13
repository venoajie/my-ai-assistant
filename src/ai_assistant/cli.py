# src/ai_assistant/cli.py 
#!/usr/bin/env python3

import argparse
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
import sys
import yaml
from importlib import metadata
from datetime import datetime, timezone
from importlib import resources

from .response_handler import ResponseHandler, APIKeyNotFoundError
from .context_plugin import ContextPluginBase
from .prompt_builder import PromptBuilder
from .session_manager import SessionManager
from .planner import Planner
from .tools import TOOL_REGISTRY
from .persona_loader import PersonaLoader
from .config import ai_settings
from .context_optimizer import ContextOptimizer

def is_manifest_stale(manifest_path: Path):
    """Checks if the manifest is older than any persona file in the package."""
    if not manifest_path.exists():
        return True, "Manifest file does not exist."

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = yaml.safe_load(f)
        generated_at_str = manifest_data.get("generated_at_utc")
        if not generated_at_str:
            return True, "Manifest is missing the 'generated_at_utc' timestamp."
        manifest_time = datetime.fromisoformat(generated_at_str)
    except (yaml.YAMLError, TypeError, ValueError) as e:
        return True, f"Could not parse manifest or its timestamp: {e}"

    try:
        # Find all persona files within the package resources
        persona_root = resources.files("ai_assistant").joinpath("personas")
        for persona_path_traversable in persona_root.rglob("*.persona.md"):
            # We need to get the real file path to check mtime
            with resources.as_file(persona_path_traversable) as persona_path:
                persona_mtime = datetime.fromtimestamp(persona_path.stat().st_mtime, tz=timezone.utc)
                if persona_mtime > manifest_time:
                    return True, f"Persona '{persona_path.name}' was modified after the manifest was generated."
    except Exception as e:
        return True, f"Could not scan package persona files: {e}"

    return False, "Manifest is up-to-date."

def build_file_context(files: List[str], query: str) -> str:
    """Reads multiple files and formats them into a single context string."""
    if not files:
        return ""
    
    MAX_FILE_SIZE = MAX_FILE_SIZE = ai_settings.general.max_file_size_mb * 1024 * 1024
    context_str = ""
    print("📎 Attaching files to context...")
    optimizer = ContextOptimizer()
    for file_path_str in files:
        path = Path(file_path_str)
        if not path.exists():
            print(f"   - ⚠️  Warning: File not found, skipping: {file_path_str}")
            continue
        
        if path.stat().st_size > MAX_FILE_SIZE:
            print(f"   - ⚠️  Warning: File exceeds 5MB limit, skipping: {file_path_str}")
            continue

        try:
            
            content = path.read_text(encoding='utf-8')

            compressed_content = optimizer.compress_file_context(
                file_path=file_path_str,
                content=content, 
                query=query,
            )

            if len(compressed_content) < len(content):
                print(f"   - ℹ️  Compressed for relevance: {file_path_str}")

            context_str += f"<AttachedFile path=\"{file_path_str}\">\n{compressed_content}\n</AttachedFile>\n\n"
            print(f"   - ✅ Attached: {file_path_str}")
        except Exception as e:
            print(f"   - ❌ Error reading file {file_path_str}: {e}")
            
    return context_str

def list_available_plugins() -> List[str]:
    """Dynamically discovers available plugins via entry points."""
    discovered_plugins = []
    # Use importlib.metadata to find registered entry points
    entry_points = metadata.entry_points(group='ai_assistant.context_plugins')
    for entry in entry_points:
        discovered_plugins.append(entry.name)
    return sorted(discovered_plugins)

    
def load_context_plugin(plugin_name: Optional[str]) -> Optional[ContextPluginBase]:
    """Dynamically loads a context plugin using its registered entry point."""
    if not plugin_name:
        return None

    print(f"🔌 Loading context plugin: {plugin_name}...")
    try:
        # Find the specific entry point by name
        entry_points = metadata.entry_points(group='ai_assistant.context_plugins')
        plugin_entry = next((ep for ep in entry_points if ep.name == plugin_name.lower()), None)

        if not plugin_entry:
            print(f"   - ❌ Error: Plugin '{plugin_name}' is not a registered entry point.", file=sys.stderr)
            return None

        # Load the class from the entry point and instantiate it
        plugin_class = plugin_entry.load()
        return plugin_class(project_root=Path.cwd())
    except Exception as e:
        print(f"   - ❌ Error: An unexpected error occurred while loading plugin '{plugin_name}': {e}", file=sys.stderr)
        return None

def main():
    """Synchronous entry point for the 'ai' command, required by pyproject.toml."""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\n👋 Exiting.")

async def async_main():
    """The core asynchronous logic of the application."""
    # Pre-flight check for API keys is critical.
    try:
        ResponseHandler().check_api_keys()
    except APIKeyNotFoundError as e:
        print(f"\n❌ CONFIGURATION ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    
    parser = argparse.ArgumentParser(description='AI Assistant - Interactive Agent')
    parser.add_argument('--version', action='version', version=f'%(prog)s {metadata.version("my-ai-assistant")} (Config: v{ai_settings.config_version})')
    parser.add_argument('--list-personas', action='store_true', help='List available personas')
    parser.add_argument('query', nargs='*', help='Your initial question or request for the agent. Required for one-shot mode.')
    parser.add_argument('-f', '--file', dest='files', action='append', help='Attach a file to the context. Can be used multiple times.')
    parser.add_argument('--persona', help='The alias of the persona to use (e.g., core/SA-1).')
    parser.add_argument('--autonomous', action='store_true', help='Run in autonomous mode.')
    parser.add_argument('--interactive', action='store_true', help='Start an interactive chat session.')
    parser.add_argument('--context', help='The name of the context plugin to use (e.g., Trading).')
    session_group = parser.add_mutually_exclusive_group()
    session_group.add_argument('--session', help='Continue an existing session by ID.')
    session_group.add_argument('--new-session', action='store_true', help='Start a new session.')    
    parser.add_argument('--list-plugins', action='store_true', help='List available context plugins')
    
    args = parser.parse_args()
    
    if args.persona:
        manifest_path = Path.cwd() / "persona_manifest.yml"
        if manifest_path.exists(): # Only check if the manifest file is present
            stale, reason = is_manifest_stale(manifest_path)
            if stale:
                print(f"🛑 HALTING: The persona manifest is stale. Reason: {reason}", file=sys.stderr)
                print("Please run your manifest generation script to update it before using personas.", file=sys.stderr)
                sys.exit(1)
            print("✅ Persona manifest is up-to-date.")
    
    if args.list_plugins:
        print("Available Context Plugins:")
        plugins = list_available_plugins()
        if not plugins:
            print("  No plugins found.")
        for p in plugins:
            print(f"  - {p}")
        sys.exit(0)
        
    session_manager = SessionManager()
    session_id = args.session
    context_plugin = load_context_plugin(args.context)
    query = ' '.join(args.query)
    user_query = ' '.join(args.query)
    initial_context = ""

    context_plugin = load_context_plugin(args.context)
    if context_plugin:
        print("   - ✅ Plugin loaded successfully.")
        plugin_context = context_plugin.get_context(user_query, args.files or [])
        initial_context += plugin_context
        
    if args.files:
        file_context = build_file_context(args.files, user_query)
        initial_context += file_context
        
    if args.list_personas:
        print("Built-in Personas:")
        for p in PersonaLoader().list_builtin_personas():
            print(f" - {p}")
        sys.exit(0) 
        
    session_manager = SessionManager()
    session_id = args.session
    history = []
    if args.new_session or (args.interactive and not args.session):
        session_id = session_manager.start_new_session()
        print(f"✨ Starting new session: {session_id}")
    elif session_id:
        print(f"🔄 Continuing session: {session_id}")
        history = session_manager.load_session(session_id) or []
        
    if args.interactive:
        await run_interactive_session(
            history, 
            session_id, 
            args.persona, 
            args.autonomous, 
            args.files,
            )
    else:
        if not query.strip() and not args.files:
            parser.error("The 'query' argument is required in one-shot mode.")
        await run_one_shot(
            query, 
            history, 
            session_id, 
            args.persona, 
            args.autonomous,
            args.files,
            )

async def run_one_shot(
    query: str, 
    history: List, 
    session_id: str, 
    persona_alias: str, 
    is_autonomous: bool, 
    files: Optional[List[str]] = None,
    ):
    
    file_context = build_file_context(files, query)
    full_query = file_context + query
    print(f"🤖 Processing query: {query}")
    if persona_alias: print(f"👤 Embodying persona: {persona_alias}")
    if is_autonomous: print("🚨 RUNNING IN AUTONOMOUS MODE - NO CONFIRMATION WILL BE ASKED 🚨")
    response = await orchestrate_agent_run(full_query, history, persona_alias, is_autonomous)
    print("\n" + "="*60)
    print(response)
    print("="*60)
    if session_id:
        history = SessionManager().update_history(history, "user", full_query)
        history = SessionManager().update_history(history, "model", response)
        SessionManager().save_session(session_id, history)
        print(f"💾 Session {session_id} saved.")

async def run_interactive_session(
    history: List,
    session_id: str, 
    persona_alias: str,
    is_autonomous: bool, 
    files: Optional[List[str]] = None,
    ):
    
    print("Entering interactive mode. Type 'exit' or 'quit' to end the session.")
    if persona_alias: print(f"👤 Embodying persona: {persona_alias}")
    if is_autonomous: print("🚨 RUNNING IN AUTONOMOUS MODE - NO CONFIRMATION WILL BE ASKED 🚨")
    
    if files:
        # In interactive mode, there's no initial query, so we pass an empty one
        # to trigger the summarization fallback in the optimizer.
        initial_file_context = build_file_context(files, query="")
        if initial_file_context:
            print("The content of the attached files has been added to the start of this session's context.")
            history = SessionManager().update_history(history, "user", initial_file_context + "The preceding file(s) have been attached for context in this session.")
            history = SessionManager().update_history(history, "model", "Acknowledged. I will use the content of the attached files as context for our conversation.")

    session_manager = SessionManager()
    while True:
        try:
            query = await asyncio.to_thread(input, "\n> ")
            if query.lower() in ["exit", "quit"]:
                break
            history = session_manager.update_history(history, "user", query)
            response = await orchestrate_agent_run(query, history, persona_alias, is_autonomous)
            print("\n" + "="*60)
            print(response)
            print("="*60)
            history = session_manager.update_history(history, "model", response)
            session_manager.save_session(session_id, history)
        except Exception as e:
            print(f"\n❌ An unexpected error occurred: {e}")
            history = session_manager.update_history(history, "system_error", str(e))
            session_manager.save_session(session_id, history)
    print("👋 Exiting interactive session.")

async def orchestrate_agent_run(
    query: str,
    history: List[Dict[str, Any]],
    persona_alias: Optional[str] = None,
    is_autonomous: bool = False,
    ):

    # --- PERSONA LOADING ---
    persona_content = None
    if persona_alias:
        loader = PersonaLoader()
        try:
            persona_content = loader.load_persona_content(persona_alias)
        except (RecursionError, FileNotFoundError) as e:
            error_msg = f"🛑 HALTING: Could not load persona '{persona_alias}'. Reason: {e}"
            print(error_msg, file=sys.stderr)
            return error_msg

    # --- PRE-PROCESSING & PLANNING ---
    optimizer = ContextOptimizer()
    optimized_query = optimizer.trim_to_limit(query)
    if len(optimized_query) < len(query):
        print(f"ℹ️  Context has been truncated to fit the token limit.")

    planner = Planner()
    plan = await planner.create_plan(optimized_query, history, persona_content)

    is_no_op_plan = not plan or all(not step.get("tool_name") for step in plan)
    if is_no_op_plan:
        print("📝 No tool execution required. Generating direct response...")
        prompt_builder = PromptBuilder()
        direct_prompt = prompt_builder.build_synthesis_prompt(query, history, ["<Observation>No tool execution was required for this query.</Observation>"], persona_content)
        response_handler = ResponseHandler()
        synthesis_model = ai_settings.model_selection.synthesis
        return await response_handler.call_api(direct_prompt, model=synthesis_model)

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
        print("\n🛑 Halting before synthesis. A critical action was denied and no other operations succeeded.")
        return "I was unable to complete the task because a necessary action was denied by the user for safety reasons."

    print("📝 Synthesizing final response from observations...")
    prompt_builder = PromptBuilder()
    synthesis_prompt = prompt_builder.build_synthesis_prompt(query, history, observations, persona_content)
    response_handler = ResponseHandler()
    synthesis_model = ai_settings.model_selection.synthesis
    final_response = await response_handler.call_api(synthesis_prompt, model=synthesis_model)
    return final_response

if __name__ == "__main__":
    main()