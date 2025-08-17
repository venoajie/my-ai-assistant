# src/ai_assistant/cli.py 

import argparse
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
import sys
import yaml
from importlib import metadata, resources
from datetime import datetime
import time

from . import kernel 
from .config import ai_settings
from .context_plugin import ContextPluginBase
from .persona_loader import PersonaLoader
from .response_handler import ResponseHandler, APIKeyNotFoundError
from .session_manager import SessionManager
from .utils.context_optimizer import ContextOptimizer
from .utils.persona_validator import PersonaValidator
from .utils.colors import Colors
from .utils.signature import calculate_persona_signature
from .utils.result_presenter import present_result

    
def is_manifest_invalid(manifest_path: Path):
    """
    Checks if the manifest is invalid due to timestamps or content mismatch.
    Returns a tuple (is_invalid: bool, reason: str).
    """
    project_root = Path.cwd()
    # Use resources to find the canonical personas directory within the package
    try:
        personas_dir_traversable = resources.files('ai_assistant').joinpath('personas')
        personas_dir = Path(str(personas_dir_traversable))
    except (ModuleNotFoundError, FileNotFoundError):
        return True, "Could not locate the built-in personas directory."


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

    # --- Check 2: Compare file modification times (fast check) ---
    try:
        for persona_path_obj in personas_dir.rglob("*.persona.md"):
            # This check is now more complex due to package installation vs. dev mode
            # For simplicity in a runtime check, we rely on the signature.
            # A more advanced check could compare against package metadata.
            pass # Skipping direct mtime check in favor of signature, which is more robust.
    except Exception as e:
        return True, f"Could not scan persona files for modification times: {e}"

    # --- Check 3: Recalculate and compare the validation signature (robust check) ---
    try:
        validator = PersonaValidator(project_root / "persona_config.yml")
        all_persona_paths = list(personas_dir.rglob("*.persona.md"))
        validated_persona_details = []

        for persona_path in all_persona_paths:
            is_valid, reason = validator.validate_persona(persona_path, personas_dir)
            if not is_valid:
                return True, f"A persona file on disk is invalid. Reason: {reason} for file {persona_path.relative_to(personas_dir)}. The manifest is out of sync with an invalid state."
            else:
                content = persona_path.read_text(encoding="utf-8")
                data = yaml.safe_load(content.split("---")[1])
                validated_persona_details.append({
                    "path": persona_path,
                    "alias": data['alias'],
                    "content": content,
                })

        # Use the centralized signature calculation function
        recalculated_signature = calculate_persona_signature(validated_persona_details, project_root)

        if recalculated_signature != stored_signature:
            return True, "Persona file structure or content has changed since last validation. The signature does not match."

    except Exception as e:
        return True, f"A critical error occurred during runtime signature validation: {e}"

    return False, "Manifest is valid and up-to-date."


def build_file_context(
    files: List[str],
    query: str,
    ) -> str:
    
    """Reads multiple files and formats them into a single context string."""
    if not files:
        return ""
    
    MAX_FILE_SIZE = MAX_FILE_SIZE = ai_settings.general.max_file_size_mb * 1024 * 1024
    context_str = ""
    print(f"{Colors.CYAN}📎 Attaching files to context...{Colors.RESET}")
    optimizer = ContextOptimizer()
    for file_path_str in files:
        path = Path(file_path_str)
        if not path.exists():
            print(f"   - {Colors.YELLOW}⚠️  Warning: File not found, skipping: {file_path_str}{Colors.RESET}")
            continue
        
        if path.stat().st_size > MAX_FILE_SIZE:
            print(f"   - {Colors.YELLOW}⚠️  Warning: File exceeds 5MB limit, skipping: {file_path_str}{Colors.RESET}")
            continue

        try:
            
            content = path.read_text(encoding='utf-8')

            compressed_content = optimizer.compress_file_context(
                file_path=file_path_str,
                content=content, 
                query=query,
            )

            if len(compressed_content) < len(content):
                print(f"   - {Colors.BLUE}ℹ️  Compressed for relevance: {file_path_str}{Colors.RESET}")

            context_str += f"<AttachedFile path=\"{file_path_str}\">\n{compressed_content}\n</AttachedFile>\n\n"
            print(f"   - {Colors.GREEN}✅ Attached: {file_path_str}{Colors.RESET}")
        except Exception as e:
            print(f"   - {Colors.RED}❌ Error reading file {file_path_str}: {e}{Colors.RESET}")
            
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

    print(f"{Colors.MAGENTA}🔌 Loading context plugin: {plugin_name}...{Colors.RESET}")
    try:
        # Find the specific entry point by name
        entry_points = metadata.entry_points(group='ai_assistant.context_plugins')
        plugin_entry = next((ep for ep in entry_points if ep.name == plugin_name.lower()), None)

        if not plugin_entry:
            print(f"   - {Colors.RED}❌ Error: Plugin '{plugin_name}' is not a registered entry point.{Colors.RESET}", file=sys.stderr)
            return None

        # Load the class from the entry point and instantiate it
        plugin_class = plugin_entry.load()
        return plugin_class(project_root=Path.cwd())
    except Exception as e:
        print(f"   - {Colors.RED}❌ Error: An unexpected error occurred while loading plugin '{plugin_name}': {e}{Colors.RESET}", file=sys.stderr)
        return None

def _run_prompt_sanity_checks(args: argparse.Namespace, query: str):
    """
    Analyzes the user's prompt and flags for common anti-patterns and
    prints non-halting warnings to guide the user.
    """
    warnings = []
    query_lower = query.lower()
    
    # Check 1: Missing Persona
    if not args.persona:
        warnings.append(
            "You are running without a specific persona (--persona). "
            "Results may be generic. For best results, select a specialist."
        )

    # Check 2 (NEW): Explicit high-risk action tag without the safe workflow
    if "<action>" in query_lower \
        and not args.output_dir:
        warnings.append(
            "CRITICAL: You used the <ACTION> tag to declare a high-risk operation "
            "but did not use the --output-dir flag. This is highly discouraged. "
            "Always use the two-stage workflow for actions."
        )
    # Check 3 (Fallback): Inferred risky action without the safe workflow
    elif not "<action>" in query_lower:
        risky_keywords = ["refactor", "fix", "modify", "commit", "change", "add", "create", "write"]
        if any(keyword in query_lower for keyword in risky_keywords) \
            and not args.output_dir:
            warnings.append(
                "Your prompt seems to request a system modification. For clarity and safety, "
                "wrap your goal in <ACTION> tags and use the --output-dir flag."
            )

    # Check 4: Large batch-processing attempt
    file_count = len(args.files) if args.files else 0
    if file_count > 5:
        warnings.append(
            f"You have attached {file_count} files. Attempting to process many files in a "
            "single prompt can lead to incomplete runs due to context limits. "
            "Consider using a shell script to process files in a loop."
        )

    if warnings:
        print(f"{Colors.YELLOW}--- 💡 Prompting Best Practice Reminders ---{Colors.RESET}", file=sys.stderr)
        for i, warning in enumerate(warnings):
            print(f"[{i+1}] {Colors.YELLOW}⚠️  {warning}{Colors.RESET}", file=sys.stderr)
        print(f"{Colors.YELLOW}-------------------------------------------{Colors.RESET}", file=sys.stderr)

def main():
    """Synchronous entry point for the 'ai' command, required by pyproject.toml."""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print(f"\n{Colors.CYAN}👋 Exiting.{Colors.RESET}")

async def async_main():
    """The core asynchronous logic of the application."""
    # Pre-flight check for API keys is critical.
    try:
        ResponseHandler().check_api_keys()
    except APIKeyNotFoundError as e:
        print(f"\n{Colors.RED}❌ CONFIGURATION ERROR: {e}{Colors.RESET}", file=sys.stderr)
        sys.exit(1)
    
    parser = argparse.ArgumentParser(description='AI Assistant - Interactive Agent')
    parser.add_argument('--version', action='version', version=f'%(prog)s {metadata.version("my-ai-assistant")} (Config: v{ai_settings.config_version})')
    parser.add_argument('--list-personas', action='store_true', help='List available personas')
    parser.add_argument('-f', '--file', dest='files', action='append', help='Attach a file to the context. Can be used multiple times.')
    parser.add_argument('--persona', help='The alias of the persona to use (e.g., core/SA-1).')
    parser.add_argument('--autonomous', action='store_true', help='Run in autonomous mode.')
    parser.add_argument('--interactive', action='store_true', help='Start an interactive chat session.')
    parser.add_argument('--context', help='The name of the context plugin to use (e.g., Trading).')
    parser.add_argument('--output-dir', help='Activates Output-First mode, generating an execution package in the specified directory instead of executing live.')
    session_group = parser.add_mutually_exclusive_group()
    session_group.add_argument('--session', help='Continue an existing session by ID.')
    session_group.add_argument('--new-session', action='store_true', help='Start a new session.')    
    parser.add_argument('--list-plugins', action='store_true', help='List available context plugins')
    parser.add_argument('query', nargs='*', help="Your request for the agent. For tasks that modify files, wrap your goal in <ACTION> tags.")

    args = parser.parse_args()
    
    user_query = ' '.join(args.query)
    _run_prompt_sanity_checks(args, user_query)
    
    if args.persona:
        manifest_path = Path.cwd() / "persona_manifest.yml"
        invalid, reason = is_manifest_invalid(manifest_path)
        if invalid:
            print(f"{Colors.RED}🛑 HALTING: The persona manifest is invalid. Reason: {reason}{Colors.RESET}", file=sys.stderr)
            print(f"{Colors.YELLOW}Please run 'python scripts/generate_manifest.py' to fix it.{Colors.RESET}", file=sys.stderr)
            sys.exit(1)
        print(f"{Colors.GREEN}✅ Persona manifest is valid and up-to-date.{Colors.RESET}")
        
    if args.list_plugins:
        print(f"{Colors.BOLD}Available Context Plugins:{Colors.RESET}")
        plugins = list_available_plugins()
        if not plugins:
            print("  No plugins found.")
        for p in plugins:
            print(f"  - {p}")
        sys.exit(0)
        
    if args.list_personas:
        print(f"{Colors.BOLD}Built-in Personas:{Colors.RESET}")
        for p in PersonaLoader().list_builtin_personas():
            print(f" - {p}")
        sys.exit(0) 
        
    session_manager = SessionManager()
    history = []
    session_id = None
    if args.new_session or (args.interactive and not args.session):
        session_id = session_manager.start_new_session()
        print(f"{Colors.CYAN}✨ Starting new session: {session_id}{Colors.RESET}")
    elif args.session:
        session_id = args.session
        print(f"{Colors.CYAN}🔄 Continuing session: {session_id}{Colors.RESET}")
        history = session_manager.load_session(session_id) or []
    else:
        session_id = session_manager.start_new_session()
        print(f"{Colors.CYAN}✨ Starting new session (implicit): {session_id}{Colors.RESET}")

    full_context_str = ""
    context_plugin = load_context_plugin(args.context)
    if context_plugin:
        print(f"   - {Colors.GREEN}✅ Plugin loaded successfully.{Colors.RESET}")
        plugin_context = context_plugin.get_context(user_query, args.files or [])
        full_context_str += plugin_context
                
    if args.files:
        file_context = build_file_context(args.files, user_query)
        full_context_str += file_context

    # --- UNIFIED CONTEXT INJECTION (TD-001 FIX) ---
    # If any context was built, inject it into the history now. This ensures
    # both interactive and one-shot modes start with the same context.
    if full_context_str:
        print(f"{Colors.BLUE}Injecting file/plugin context into session history.{Colors.RESET}")
        context_message = "The following context from files and/or plugins has been attached to our session:\n\n" + full_context_str
        history = session_manager.update_history(history, "user", context_message)
        history = session_manager.update_history(history, "model", "Acknowledged. I will use the provided context in our conversation.")

    if args.interactive:
        await run_interactive_session(
            history,
            session_id,
            args.persona,
            args.autonomous,
        )
    else:
        if not user_query.strip() and not full_context_str:
            parser.error("The 'query' argument is required in one-shot mode unless files or context are provided.")
        
        await run_one_shot(
            query=user_query,
            display_query=user_query,
            history=history,
            session_id=session_id,
            persona_alias=args.persona,
            is_autonomous=args.autonomous,
            output_dir=args.output_dir,
        )
    
def print_summary_metrics(
    start_time: float,
    end_time: float,
    metrics: Dict[str, Any],
    ):
    
    """Prints the processing time and estimated token usage for one-shot mode."""
    total_duration = end_time - start_time
    timings = metrics.get("timings", {})
    planning_tokens = metrics.get("tokens", {}).get("planning", {}).get("total", 0)
    critique_tokens = metrics.get("tokens", {}).get("critique", {}).get("total", 0)
    synthesis_tokens = metrics.get("tokens", {}).get("synthesis", {}).get("total", 0)
    total_tokens = planning_tokens + critique_tokens + synthesis_tokens
    
    timing_parts = [f"Total: {Colors.BOLD}{total_duration:.2f}s{Colors.RESET}"]
    if "planning" in timings:
        timing_parts.append(f"Planning: {timings.get('planning', 0):.2f}s")
    if "critique" in timings:
        timing_parts.append(f"Critique: {timings.get('critique', 0):.2f}s")
    if "synthesis" in timings:
        timing_parts.append(f"Synthesis: {timings.get('synthesis', 0):.2f}s")
    
    time_str = " | ".join(timing_parts)
    token_str = f"Total: {Colors.BOLD}{total_tokens}{Colors.RESET}"
    if planning_tokens > 0 or critique_tokens > 0 or synthesis_tokens > 0:
        token_str += f" (P: {planning_tokens}, C: {critique_tokens}, S: {synthesis_tokens})"
        
    print(f"{Colors.DIM}{'-' * 60}{Colors.RESET}")
    print(f"📊 {Colors.CYAN}Metrics:{Colors.RESET} "
           f"{Colors.BLUE}Time ({time_str}){Colors.RESET} | "            
          f"{Colors.MAGENTA}Est. Tokens: {token_str}{Colors.RESET}")
    print(f"{Colors.DIM}{'-' * 60}{Colors.RESET}")

def print_interactive_summary_metrics(
    turn_metrics: Dict[str, Any],
    session_tokens: Dict[str, int]
    ):
    """Prints metrics for a turn in interactive mode, including session totals."""
    # Turn-specific metrics
    turn_duration = turn_metrics.get("timings", {}).get("total", 0)
    turn_tokens_data = turn_metrics.get("tokens", {})
    turn_planning = turn_tokens_data.get("planning", {}).get("total", 0)
    turn_critique = turn_tokens_data.get("critique", {}).get("total", 0)
    turn_synthesis = turn_tokens_data.get("synthesis", {}).get("total", 0)
    turn_total_tokens = turn_planning + turn_critique + turn_synthesis

    # Session totals
    session_total_tokens = sum(session_tokens.values())

    print(f"{Colors.DIM}{'-' * 60}{Colors.RESET}")
    # Turn Metrics Line
    turn_time_str = f"Time: {Colors.BOLD}{turn_duration:.2f}s{Colors.RESET}"
    turn_token_str = f"Tokens: {Colors.BOLD}{turn_total_tokens}{Colors.RESET} (P:{turn_planning} C:{turn_critique} S:{turn_synthesis})"
    print(f"📊 {Colors.CYAN}Turn Metrics:{Colors.RESET} {Colors.BLUE}{turn_time_str}{Colors.RESET} | {Colors.MAGENTA}{turn_token_str}{Colors.RESET}")
    
    # Session Metrics Line
    session_token_str = f"Total Tokens: {Colors.BOLD}{session_total_tokens}{Colors.RESET} (P:{session_tokens['planning']} C:{session_tokens['critique']} S:{session_tokens['synthesis']})"
    print(f" cumulatively {Colors.CYAN}Session Totals:{Colors.RESET} {Colors.MAGENTA}{session_token_str}{Colors.RESET}")
    print(f"{Colors.DIM}{'-' * 60}{Colors.RESET}")


async def run_one_shot(
    query: str,
    display_query: str,
    history: List,
    session_id: str,
    persona_alias: str,
    is_autonomous: bool,
    output_dir: Optional[str] = None,
):
    start_time = time.monotonic()
    print(f"{Colors.BLUE}🤖 Processing query: {display_query}{Colors.RESET}")
    if persona_alias: print(f"{Colors.MAGENTA}👤 Embodying persona: {persona_alias}{Colors.RESET}")
    if is_autonomous: print(f"{Colors.RED}{Colors.BOLD}🚨 RUNNING IN AUTONOMOUS MODE - NO CONFIRMATION WILL BE ASKED 🚨{Colors.RESET}")
    if output_dir: print(f"{Colors.CYAN}📦 OUTPUT-FIRST MODE: Generating execution package in '{output_dir}'{Colors.RESET}")

    result_data = await kernel.orchestrate_agent_run(
        query=query,
        history=history,
        persona_alias=persona_alias,
        is_autonomous=is_autonomous,
        output_dir=output_dir,
    )
    response = result_data["response"]

    print("\n" + f"{Colors.DIM}{'='*60}{Colors.RESET}")
    print(present_result(response))
    print(f"{Colors.DIM}{'='*60}{Colors.RESET}")

    end_time = time.monotonic()
    print_summary_metrics(
         start_time,
         end_time,
         result_data.get("metrics", {}),
         )

    if session_id and not output_dir: # Don't save session history in output-first mode
        history = SessionManager().update_history(history, "user", query)        
        history = SessionManager().update_history(history, "model", response)
        SessionManager().save_session(session_id, history)
        print(f"{Colors.GREEN}💾 Session {session_id} saved.{Colors.RESET}")

async def run_interactive_session(
    history: List,
    session_id: str,
    persona_alias: str,
    is_autonomous: bool,
    ):
    print("Entering interactive mode. Type 'exit' or 'quit' to end the session.")
    if persona_alias: print(f"{Colors.MAGENTA}👤 Embodying persona: {persona_alias}{Colors.RESET}")
    if is_autonomous: print(f"{Colors.RED}{Colors.BOLD}🚨 RUNNING IN AUTONOMOUS MODE - NO CONFIRMATION WILL BE ASKED 🚨{Colors.RESET}")

    session_manager = SessionManager()
    session_total_tokens = {"planning": 0, "critique": 0, "synthesis": 0}

    while True:
        try:
            query = await asyncio.to_thread(input, f"\n{Colors.GREEN}> {Colors.RESET}")
            if query.lower() in ["exit", "quit"]:
                break

            start_time = time.monotonic()
            
            current_turn_history = session_manager.update_history(list(history), "user", query)
            
            result_data = await kernel.orchestrate_agent_run(
                query=query,
                history=current_turn_history,
                persona_alias=persona_alias,
                is_autonomous=is_autonomous,
            )
            
            response = result_data["response"]
            end_time = time.monotonic()

            # --- Metrics Calculation ---
            turn_metrics = result_data.get("metrics", {})
            turn_metrics.setdefault("timings", {})["total"] = end_time - start_time
            
            turn_tokens = turn_metrics.get("tokens", {})
            session_total_tokens["planning"] += turn_tokens.get("planning", {}).get("total", 0)
            session_total_tokens["critique"] += turn_tokens.get("critique", {}).get("total", 0)
            session_total_tokens["synthesis"] += turn_tokens.get("synthesis", {}).get("total", 0)

            print("\n" + f"{Colors.DIM}{'='*60}{Colors.RESET}")
            print(present_result(response))
            print(f"{Colors.DIM}{'='*60}{Colors.RESET}")

            print_interactive_summary_metrics(
                turn_metrics=turn_metrics,
                session_tokens=session_total_tokens
            )

            # Update the main history object for the next loop iteration
            history = session_manager.update_history(current_turn_history, "model", response)
            session_manager.save_session(session_id, history)
        except Exception as e:
            print(f"\n{Colors.RED}❌ An unexpected error occurred: {e}{Colors.RESET}")
            history = session_manager.update_history(history, "system_error", str(e))
            session_manager.save_session(session_id, history)
    print(f"{Colors.CYAN}👋 Exiting interactive session.{Colors.RESET}")


if __name__ == "__main__":
    main()