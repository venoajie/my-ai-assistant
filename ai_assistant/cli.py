# ai_assistant/cli.py
#!/usr/bin/env python3

import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
import sys 

from .response_handler import ResponseHandler, APIKeyNotFoundError
from ai_assistant.context_plugin import ContextPluginBase
from .prompt_builder import PromptBuilder
from .session_manager import SessionManager
from .planner import Planner
from .tools import TOOL_REGISTRY
from .persona_loader import PersonaLoader
from .config import ai_settings

def build_file_context(files: List[str]) -> str:
    """Reads multiple files and formats them into a single context string."""
    if not files:
        return ""
    
    context_str = ""
    print("📎 Attaching files to context...")
    for file_path_str in files:
        path = Path(file_path_str)
        if not path.exists():
            print(f"   - ⚠️  Warning: File not found, skipping: {file_path_str}")
            continue
        try:
            content = path.read_text(encoding='utf-8')
            context_str += f"<AttachedFile path=\"{file_path_str}\">\n{content}\n</AttachedFile>\n\n"
            print(f"   - ✅ Attached: {file_path_str}")
        except Exception as e:
            print(f"   - ❌ Error reading file {file_path_str}: {e}")
            
    return context_str

def main():
    
    try:
        ResponseHandler().check_api_keys()
    except APIKeyNotFoundError as e:
        print(f"\n❌ CONFIGURATION ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    
    parser = argparse.ArgumentParser(description='Trading AI Assistant - Interactive Agent')
    parser.add_argument('query', nargs='*', help='Your initial question or request for the agent. Required for one-shot mode.')
    parser.add_argument('-f', '--file', dest='files', action='append', help='Attach a file to the context. Can be used multiple times.')
    parser.add_argument('--persona', help='The alias of the PEL persona to use (e.g., CSA-1).')
    parser.add_argument('--autonomous', action='store_true', help='Run in autonomous mode.')
    parser.add_argument('--interactive', action='store_true', help='Start an interactive chat session.')
    parser.add_argument('--context', help='The name of the context plugin to use (e.g., Trading).')
    session_group = parser.add_mutually_exclusive_group()
    session_group.add_argument('--session', help='Continue an existing session by ID.')
    session_group.add_argument('--new-session', action='store_true', help='Start a new session.')
    args = parser.parse_args()
    session_manager = SessionManager()
    session_id = args.session
    
    # Load context plugin
    context_plugin = None
    if args.context == "Trading":
        from plugins.trading_plugin import TradingContextPlugin
        context_plugin = TradingContextPlugin(Path.cwd())
    
    # Add context to query
    if context_plugin:
        context_str = context_plugin.get_context(query, args.files or [])
        query = context_str + query
    
    history = []
    if args.new_session or (args.interactive and not args.session):
        session_id = session_manager.start_new_session()
        print(f"✨ Starting new session: {session_id}")
    elif session_id:
        print(f"🔄 Continuing session: {session_id}")
        history = session_manager.load_session(session_id) or []
    if args.interactive:
        run_interactive_session(history, session_id, args.persona, args.autonomous, args.files)
    else:
        if not args.query:
            parser.error("The 'query' argument is required in one-shot mode.")
        query = ' '.join(args.query)
        run_one_shot(query, history, session_id, args.persona, args.autonomous, args.files)

def run_one_shot(
    query: str,
    history: List, session_id: str, 
    persona_alias: str, 
    is_autonomous: bool,
    files: Optional[List[str]] = None,
    ):
    file_context = build_file_context(files)
    full_query = file_context + query
    
    print(f"🤖 Processing query: {query}")
    if persona_alias: print(f"👤 Embodying persona: {persona_alias}")
    if is_autonomous: print("🚨 RUNNING IN AUTONOMOUS MODE - NO CONFIRMATION WILL BE ASKED 🚨")
    response = orchestrate_agent_run(full_query, history, persona_alias, is_autonomous)
    print("\n" + "="*60)
    print(response)
    print("="*60)
    if session_id:
        history = SessionManager().update_history(history, "user", full_query)
        history = SessionManager().update_history(history, "model", response)
        SessionManager().save_session(session_id, history)
        print(f"💾 Session {session_id} saved.")

def run_interactive_session(history: List, session_id: str, persona_alias: str, is_autonomous: bool, files: Optional[List[str]] = None):
    print("Entering interactive mode. Type 'exit' or 'quit' to end the session.")
    if persona_alias: print(f"👤 Embodying persona: {persona_alias}")
    if is_autonomous: print("🚨 RUNNING IN AUTONOMOUS MODE - NO CONFIRMATION WILL BE ASKED 🚨")
    
    if files:
        initial_file_context = build_file_context(files)
        if initial_file_context:
            print("The content of the attached files has been added to the start of this session's context.")
            history = SessionManager().update_history(history, "user", initial_file_context + "The preceding file(s) have been attached for context in this session.")
            history = SessionManager().update_history(history, "model", "Acknowledged. I will use the content of the attached files as context for our conversation.")

    session_manager = SessionManager()
    while True:
        try:
            query = input("\n> ")
            if query.lower() in ["exit", "quit"]:
                print("👋 Exiting interactive session.")
                break
            history = session_manager.update_history(history, "user", query)
            response = orchestrate_agent_run(query, history, persona_alias, is_autonomous)
            print("\n" + "="*60)
            print(response)
            print("="*60)
            history = session_manager.update_history(history, "model", response)
            session_manager.save_session(session_id, history)
        except KeyboardInterrupt:
            print("\n👋 Exiting interactive session.")
            break
        except Exception as e:
            print(f"\n❌ An unexpected error occurred: {e}")
            history = session_manager.update_history(history, "system_error", str(e))
            session_manager.save_session(session_id, history)

def orchestrate_agent_run(
    query: str, 
    history: List[Dict[str, Any]], 
    persona_alias: Optional[str] = None, 
    is_autonomous: bool = False,
    ):
    
    """Orchestrates the Plan-Execute-Synthesize loop for the agent."""
    persona_content = None
    if persona_alias:
        loader = PersonaLoader(root_dir=Path.cwd()) 
        persona_content = loader.load_persona_content(persona_alias)

    planner = Planner()
    plan = planner.create_plan(query, history, persona_content)

    # MODIFIED: Check if the plan is empty OR contains only no-op steps.
    is_no_op_plan = not plan or all(not step.get("tool_name") for step in plan)

    if is_no_op_plan:
        print("📝 No tool execution required. Generating direct response...")
        prompt_builder = PromptBuilder()
        direct_prompt = prompt_builder.build_synthesis_prompt(query, history, ["<Observation>No tool execution was required for this query.</Observation>"], persona_content)
        response_handler = ResponseHandler()
        synthesis_model = ai_settings.model_selection.synthesis
        return response_handler.call_api(direct_prompt, model=synthesis_model)

    print("🚀 Executing plan...")
    observations = []
    any_tool_succeeded = False
    any_risky_action_denied = False

    for i, step in enumerate(plan):
        tool_name = step.get("tool_name")
        # Use .get() with a default for args to handle cases where it's null
        args = step.get("args") or {}
        
        print(f"  - Executing Step {i+1}: {tool_name}({args})")
        tool = TOOL_REGISTRY.get_tool(tool_name)
        if tool:
            if tool.is_risky and not is_autonomous:
                confirm = input("      Proceed? [y/N]: ").lower().strip()
                if confirm != 'y':
                    print("    🚫 Action denied by user. Skipping step.")
                    observations.append(f"<Observation tool='{tool_name}' args='{args}'>\nAction denied by user.\n</Observation>")
                    any_risky_action_denied = True
                    continue
            
            try:
                success, result = tool(**args)
                if success:
                    observations.append(f"<Observation tool='{tool_name}' args='{args}'>\n{result}\n</Observation>")
                    print(f"    ✅ Success.")
                    any_tool_succeeded = True
                else:
                    error_msg = f"<Observation tool='{tool_name}' args='{args}'>\nError: {result}\n</Observation>"
                    observations.append(error_msg)
                    print(f"    ❌ Failure: {result}")

            except Exception as e:
                error_msg = f"<Observation tool='{tool_name}'>\nCritical Error: {e}\n</Observation>"
                observations.append(error_msg)
                print(f"    ❌ CRITICAL FAILURE: {e}")
        else:
            observations.append(f"<Observation tool='{tool_name}'>Error: Tool not found.</Observation>")
            print(f"    ❌ Failure: Tool '{tool_name}' not found.")

    if any_risky_action_denied and not any_tool_succeeded:
        print("\n🛑 Halting before synthesis. A critical action was denied and no other operations succeeded.")
        return "I was unable to complete the task because a necessary action was denied by the user for safety reasons."

    print("📝 Synthesizing final response from observations...")
    prompt_builder = PromptBuilder()
    synthesis_prompt = prompt_builder.build_synthesis_prompt(query, history, observations, persona_content)
    response_handler = ResponseHandler()
    synthesis_model = ai_settings.model_selection.synthesis
    final_response = response_handler.call_api(synthesis_prompt, model=synthesis_model)
    return final_response

if __name__ == "__main__":
    main()