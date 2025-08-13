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
import time
import hashlib
import json

from .response_handler import ResponseHandler, APIKeyNotFoundError
from .context_plugin import ContextPluginBase
from .session_manager import SessionManager
from .persona_loader import PersonaLoader
from .config import ai_settings
from .context_optimizer import ContextOptimizer
from . import kernel 


# --- This is a necessary evil for runtime validation. ---
# In a more mature package, PersonaValidator would be part of the src library.
try:
    sys.path.insert(0, str(Path.cwd() / "scripts"))
    from persona_validator import PersonaValidator
except ImportError:
    PersonaValidator = None
    
def is_manifest_invalid(manifest_path: Path):
    """
    Checks if the manifest is invalid due to timestamps or content mismatch.
    Returns a tuple (is_invalid: bool, reason: str).
    """
    project_root = Path.cwd()
    personas_dir = project_root / "src" / "ai_assistant" / "personas"

    if not manifest_path.exists():
        return True, "Manifest file does not exist."

    # --- Check 1: Timestamp and basic structure validation ---
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = yaml.safe_load(f)
        generated_at_str = manifest_data.get("generated_at_utc")
        stored_signature = manifest_data.get("validation_signature")
        if not generated_at_str or not stored_signature:
            return True, "Manifest is malformed (missing timestamp or validation_signature)."
        manifest_time = datetime.fromisoformat(generated_at_str)
    except (yaml.YAMLError, TypeError, ValueError) as e:
        return True, f"Could not parse manifest: {e}"

    # --- Check 2: Compare file modification times ---
    try:
        for persona_path_obj in personas_dir.rglob("*.persona.md"):
            persona_mtime = datetime.fromtimestamp(persona_path_obj.stat().st_mtime, tz=timezone.utc)
            if persona_mtime > manifest_time:
                return True, f"Persona '{persona_path_obj.name}' was modified after the manifest was generated."
    except Exception as e:
        return True, f"Could not scan persona files for modification times: {e}"

    # --- Check 3: Recalculate and compare the validation signature ---
    if not PersonaValidator:
        return True, "Could not import PersonaValidator from scripts directory. Cannot perform full validation."

    try:
        validator = PersonaValidator(project_root / "persona_config.yml")
        all_persona_paths = list(personas_dir.rglob("*.persona.md"))
        validated_persona_details = []

        for persona_path in all_persona_paths:
            is_valid, reason = validator.validate_persona(persona_path, personas_dir)
            if not is_valid:
                return True, f"A persona file on disk is invalid. Reason: {reason} for file {persona_path.relative_to(project_root)}. The manifest is out of sync with an invalid state."
            else:
                content = persona_path.read_text(encoding="utf-8")
                data = yaml.safe_load(content.split("---")[1])
                validated_persona_details.append({
                    "path": persona_path,
                    "alias": data['alias'],
                    "content": content,
                })

        # This logic MUST EXACTLY MATCH generate_manifest.py
        canonical_data = []
        for details in sorted(validated_persona_details, key=lambda p: p['alias']):
            canonical_data.append({
                "alias": details['alias'],
                "path": str(details['path'].relative_to(project_root)),
                "content_sha256": hashlib.sha256(details['content'].encode('utf-8')).hexdigest()
            })

        canonical_string = json.dumps(canonical_data, sort_keys=True, separators=(',', ':'))
        recalculated_signature = hashlib.sha256(canonical_string.encode('utf-8')).hexdigest()

        if recalculated_signature != stored_signature:
            return True, "Persona file structure or content has changed since last validation. The signature does not match."

    except Exception as e:
        return True, f"A critical error occurred during runtime signature validation: {e}"

    return False, "Manifest is valid and up-to-date."


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
        invalid, reason = is_manifest_invalid(manifest_path)
        if invalid:
            print(f"🛑 HALTING: The persona manifest is invalid. Reason: {reason}", file=sys.stderr)
            print("Please run 'python scripts/generate_manifest.py' to fix it.", file=sys.stderr)
            sys.exit(1)
        print("✅ Persona manifest is valid and up-to-date.")
        
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
    query = ' '.join(args.query)
    user_query = ' '.join(args.query)
    
    full_context_str = ""
    context_plugin = load_context_plugin(args.context)
    if context_plugin:
        print("   - ✅ Plugin loaded successfully.")
        plugin_context = context_plugin.get_context(user_query, args.files or [])
        full_context_str += plugin_context
                
    if args.files:
        file_context = build_file_context(args.files, user_query)
        full_context_str += file_context

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
            # Pass the pre-built context to the interactive session
            initial_file_context=full_context_str
        )
    else:
        if not query.strip() and not full_context_str:
            parser.error("The 'query' argument is required in one-shot mode unless files are provided.")
        
        # --- Combine the pre-built context with the query ---
        final_query = full_context_str + query
        
        await run_one_shot(
            full_query=final_query,
            display_query=query,
            history=history,
            session_id=session_id,
            persona_alias=args.persona,
            is_autonomous=args.autonomous,
        )
    
def print_summary_metrics(
    start_time: float,
    end_time: float,
    synthesis_prompt: str,
    final_response: str,
    timings: Dict[str, float],
    ):
    
    """Prints the processing time and estimated token usage."""
    total_duration = end_time - start_time
    optimizer = ContextOptimizer()
    prompt_tokens = optimizer.estimate_tokens(synthesis_prompt)
    response_tokens = optimizer.estimate_tokens(final_response)
    total_tokens = prompt_tokens + response_tokens

    # --- Build a detailed timing string ---
    timing_parts = [f"Total: {total_duration:.2f}s"]
    if "planning" in timings:
        timing_parts.append(f"Planning: {timings.get('planning', 0):.2f}s")
    if "synthesis" in timings:
        timing_parts.append(f"Synthesis: {timings.get('synthesis', 0):.2f}s")
    
    time_str = " | ".join(timing_parts)

    print("-" * 60)
    print(f"📊 Metrics: "
          f"Time ({time_str}) | " 
          f"Est. Tokens: {total_tokens} (Prompt: {prompt_tokens}, Response: {response_tokens})")
    print("-" * 60)


async def run_one_shot(
    full_query: str,
    display_query: str,
    history: List,
    session_id: str,
    persona_alias: str,
    is_autonomous: bool,
):
    start_time = time.monotonic()
    print(f"🤖 Processing query: {display_query}")
    if persona_alias: print(f"👤 Embodying persona: {persona_alias}")
    if is_autonomous: print("🚨 RUNNING IN AUTONOMOUS MODE - NO CONFIRMATION WILL BE ASKED 🚨")

    # --- Use explicit keyword arguments to prevent positional errors ---
    # This ensures the correct variables are passed to the kernel, resolving the TypeError.
    result_data = await kernel.orchestrate_agent_run(
        query=full_query,
        history=history,
        persona_alias=persona_alias,
        is_autonomous=is_autonomous
    )
    response = result_data["response"]

    print("\n" + "="*60)
    print(response)
    print("="*60)

    end_time = time.monotonic()
    print_summary_metrics(
        start_time,
        end_time,
        result_data["synthesis_prompt"],
        response,
        result_data.get("timings", {})
    )

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
    initial_file_context: str = "", # --- Receive pre-built context ---
    ):
    print("Entering interactive mode. Type 'exit' or 'quit' to end the session.")
    if persona_alias: print(f"👤 Embodying persona: {persona_alias}")
    if is_autonomous: print("🚨 RUNNING IN AUTONOMOUS MODE - NO CONFIRMATION WILL BE ASKED 🚨")

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

            start_time = time.monotonic()
            history = session_manager.update_history(history, "user", query)
            
            result_data = await kernel.orchestrate_agent_run(
                query=query,
                history=history,
                persona_alias=persona_alias,
                is_autonomous=is_autonomous,
            )
            
            response = result_data["response"]

            print("\n" + "="*60)
            print(response)
            print("="*60)

            end_time = time.monotonic()
            print_summary_metrics(
                start_time, 
                end_time, 
                result_data["synthesis_prompt"], 
                response,
                result_data.get("timings", {}),
                )

            history = session_manager.update_history(history, "model", response)
            session_manager.save_session(session_id, history)
        except Exception as e:
            print(f"\n❌ An unexpected error occurred: {e}")
            history = session_manager.update_history(history, "system_error", str(e))
            session_manager.save_session(session_id, history)
    print("👋 Exiting interactive session.")


if __name__ == "__main__":
    main()