# src/ai_assistant/cli.py 
from datetime import datetime
from importlib import metadata, resources
from pathlib import Path
from typing import Dict, Any, List, Optional
import argparse
import asyncio
import importlib.util
import inspect
import sys
import time
import yaml
import structlog # Add this

from . import kernel 
from .config import ai_settings
from .context_plugin import ContextPluginBase
from .logging_config import setup_logging 
from .persona_loader import PersonaLoader
from .response_handler import ResponseHandler, APIKeyNotFoundError
from .session_manager import SessionManager
from .utils.context_optimizer import ContextOptimizer
from .utils.persona_validator import PersonaValidator
from .utils.colors import Colors
from .utils.result_presenter import present_result
from .utils.signature import calculate_persona_signature
from .utils.symbol_extractor import extract_symbol_source

logger = structlog.get_logger()

try:
    governance_text = resources.files('ai_assistant').joinpath('internal_data/governance.yml').read_text(encoding='utf-8')
    GOVERNANCE_RULES = yaml.safe_load(governance_text)
    RISKY_KEYWORDS = GOVERNANCE_RULES.get("prompting_best_practices", {}).get("risky_modification_keywords", [])
except Exception as e:
    print(f"⚠️  Warning: Could not load governance rules for sanity checks. Reason: {e}", file=sys.stderr)
    RISKY_KEYWORDS = []

def list_available_plugins() -> List[str]:
    """Dynamically discovers available plugins from both entry points and the local project directory."""
    discovered_plugins = []
    
    # 1. Load built-in plugins via entry points (with version compatibility)
    try:
        # For Python 3.10+
        if sys.version_info >= (3, 10):
            entry_points = metadata.entry_points(group='ai_assistant.context_plugins')
        # For Python < 3.10
        else:
            entry_points = metadata.entry_points().get('ai_assistant.context_plugins', [])
            
        for entry in entry_points:
            discovered_plugins.append(entry.name)
    except Exception as e:
        print(f"{Colors.YELLOW}⚠️  Warning: Could not load plugins from entry points: {e}{Colors.RESET}", file=sys.stderr)
        
    # 2. Discover and load local, project-specific plugins
    local_plugins_path = ai_settings.paths.local_plugins_dir
    if local_plugins_path.is_dir():
        for file_path in local_plugins_path.glob("*.py"):
            # --- THIS IS THE FIX ---
            # Explicitly ignore __init__.py files
            if file_path.name == "__init__.py":
                continue
            
            # Use a special suffix to distinguish local plugins
            plugin_name = f"{file_path.stem.replace('_plugin', '')} (local)"
            if plugin_name not in discovered_plugins:
                 discovered_plugins.append(plugin_name)

    return sorted(discovered_plugins)

def is_manifest_invalid(manifest_path: Path):
    """
    Checks if the manifest is invalid due to timestamps or content mismatch.
    Returns a tuple (is_invalid: bool, reason: str).
    """
    # Use resources to find the canonical personas directory within the package
    try:
        #  Locate internal data files relative to the package
        config_traversable = resources.files('ai_assistant').joinpath('internal_data/persona_config.yml')
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
        # Initialize validator with the correct, packaged config path
        validator = PersonaValidator(Path(str(config_traversable)))
        all_persona_paths = list(personas_dir.rglob("*.persona.md"))
        validated_persona_details = []
        
        for persona_path in all_persona_paths:
            is_valid, reason = validator.validate_persona(persona_path, personas_dir)
            if not is_valid:
                return True, f"A persona file on disk is invalid. Reason: {reason}"
            else:
                content = persona_path.read_text(encoding="utf-8")
                data = yaml.safe_load(content.split("---")[1])
                validated_persona_details.append({
                    "path": persona_path,
                    "alias": data['alias'],
                    "content": content,
                })

        package_root_path = personas_dir.parent 
        
        # Use the centralized signature calculation function
        recalculated_signature = calculate_persona_signature(validated_persona_details, package_root_path)

        if recalculated_signature != stored_signature:
            return True, "Persona file structure or content has changed since last validation. The signature does not match."

    except Exception as e:
        return True, f"A critical error occurred during runtime signature validation: {e}"

    return False, "Manifest is valid and up-to-date."

def build_file_context(
    files: List[str],
    query: str,
    extract_symbols: Optional[List[List[str]]] = None,
) -> str:
    """Reads multiple files, formats them into a single context string, and provides clear logging."""
    if not files:
        return ""

    symbol_map = {path: symbol for path, symbol in extract_symbols} if extract_symbols else {}
    MAX_FILE_SIZE = ai_settings.general.max_file_size_mb * 1024 * 1024
    
    context_str = ""
    attached_files = []
    skipped_files = [] # Store tuples of (path, reason)
    
    logger.info("Attaching files to context...", requested_count=len(files))
    optimizer = ContextOptimizer()

    for file_path_str in files:
        path = Path(file_path_str)
        if not path.exists():
            skipped_files.append((file_path_str, "File not found"))
            continue
        
        if path.stat().st_size > MAX_FILE_SIZE:
            skipped_files.append((file_path_str, f"Exceeds size limit of {ai_settings.general.max_file_size_mb}MB"))
            continue

        content = ""
        symbol_to_extract = symbol_map.get(file_path_str)
        
        try:
            if symbol_to_extract:
                logger.debug("Performing surgical context pruning.", file=file_path_str, symbol=symbol_to_extract)
                extracted_source = extract_symbol_source(path, symbol_to_extract)
                if extracted_source:
                    content = extracted_source
                    logger.debug("Symbol extracted successfully.", symbol=symbol_to_extract)
                else:
                    logger.warning("Could not extract symbol, falling back to full file.", symbol=symbol_to_extract)
                    content = path.read_text(encoding='utf-8')
            else:
                content = path.read_text(encoding='utf-8')
            
            compressed_content = optimizer.compress_file_context(
                file_path=file_path_str,
                content=content,
                query=query,
            )
            
            context_str += f"<AttachedFile path=\"{file_path_str}\">\n{compressed_content}\n</AttachedFile>\n\n"
            attached_files.append(file_path_str)

        except Exception as e:
            skipped_files.append((file_path_str, f"Error reading file: {e}"))

    # --- FINAL SUMMARY LOGGING ---
    logger.info(
        "File context processing complete.",
        attached=len(attached_files),
        skipped=len(skipped_files),
        total=len(files)
    )
    # Log the details of any skipped files for clarity
    for file_path, reason in skipped_files:
        logger.warning("Skipped file", path=file_path, reason=reason)
            
    return context_str

def load_context_plugin(plugin_name: Optional[str]) -> Optional[ContextPluginBase]:
    """Dynamically loads a context plugin from entry points or the local project directory."""
    if not plugin_name:
        return None

    logger.info("Loading context plugin", plugin_name=plugin_name)
    
    try:
        # --- Handle local plugins ---
        if plugin_name.endswith(" (local)"):
            base_name = plugin_name.removesuffix(" (local)") # pyright: ignore
            local_plugins_path = ai_settings.paths.local_plugins_dir
            plugin_file = local_plugins_path / f"{base_name}_plugin.py"
            
            if not plugin_file.exists():
                print(f"   - {Colors.RED}❌ Error: Local plugin file not found: {plugin_file}{Colors.RESET}", file=sys.stderr)
                return None

            # Dynamically load the module from the file path
            spec = importlib.util.spec_from_file_location(base_name, plugin_file)
            if not spec or not spec.loader:
                raise ImportError(f"Could not create module spec for {plugin_file}")
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find the class that inherits from ContextPluginBase
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, ContextPluginBase) and obj is not ContextPluginBase:
                    return obj(project_root=Path.cwd())
            
            print(f"   - {Colors.RED}❌ Error: No class inheriting from ContextPluginBase found in {plugin_file}{Colors.RESET}", file=sys.stderr)
            return None

        # --- Handle entry-point plugins (existing logic) ---
        else:
            # For Python 3.10+
            if sys.version_info >= (3, 10):
                entry_points = metadata.entry_points(group='ai_assistant.context_plugins')
            # For Python < 3.10
            else:
                entry_points = metadata.entry_points().get('ai_assistant.context_plugins', [])

            plugin_entry = next((ep for ep in entry_points if ep.name == plugin_name.lower()), None)

            if not plugin_entry:
                print(f"   - {Colors.RED}❌ Error: Plugin '{plugin_name}' is not a registered entry point.{Colors.RESET}", file=sys.stderr)
                return None

            plugin_class = plugin_entry.load()
            return plugin_class(project_root=Path.cwd())

    except Exception as e:
        print(f"   - {Colors.RED}❌ Error: An unexpected error occurred while loading plugin '{plugin_name}': {e}{Colors.RESET}", file=sys.stderr)
        return None

def _run_prompt_sanity_checks(
    args: argparse.Namespace, 
    query: str,
    ):
    
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

    # --- START: P-003 IMPLEMENTATION ---
    # This new, enhanced check replaces the previous generic risky action check.
    
    # Define the high-level workflow tools that represent best practices for modification.
    WORKFLOW_TOOLS = ["execute_refactoring_workflow", "create_service_from_template"]
    
    contains_risky_keyword = any(keyword in query_lower for keyword in RISKY_KEYWORDS)
    mentions_workflow_tool = any(tool_name in query_lower for tool_name in WORKFLOW_TOOLS)

    # Trigger the detailed warning if the prompt is ambiguous for a live-mode modification.
    if contains_risky_keyword and not mentions_workflow_tool and not args.output_dir:
        print(f"\n{Colors.YELLOW}{'='*60}{Colors.RESET}")
        print(f"{Colors.YELLOW}           - PROMPTING BEST PRACTICE ALERT -{Colors.RESET}")
        print(f"{Colors.YELLOW}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}⚠️  Your prompt requests a file modification but is ambiguous.{Colors.RESET}\n")
        print(f"- {Colors.BOLD}REASON:{Colors.RESET} The prompt contains risky keywords (e.g., 'change', 'refactor') but does not")
        print("  specify a high-level workflow tool. This can lead to unpredictable or unsafe plans.\n")
        print(f"- {Colors.BOLD}RECOMMENDATION:{Colors.RESET} For maximum reliability, explicitly constrain the AI by naming the")
        print("  tool and its required arguments.\n")
        print(f"- {Colors.BOLD}EXAMPLE OF A MORE ROBUST PROMPT:{Colors.RESET}")
        print(f"  {Colors.CYAN}\"Using the execute_refactoring_workflow tool, apply the necessary changes to [file1]...\"{Colors.RESET}\n")
        print(f"{Colors.DIM}Proceeding with ambiguous prompt...{Colors.RESET}")
        print(f"{Colors.DIM}{'-'*60}{Colors.RESET}\n")
    # --- END: P-003 IMPLEMENTATION ---

    # Check 4: Large batch-processing attempt
    file_count = len(args.files) if args.files else 0
    if file_count > 5:
        warnings.append(
            f"You have attached {file_count} files. Attempting to process many files in a "
            "single prompt can lead to incomplete runs due to context limits. "
            "Consider using a shell script to process files in a loop."
        )

    if warnings:
        logger.warning("Prompting Best Practice Reminders")
        for i, warning in enumerate(warnings):
            logger.warning(f"[{i+1}] {warning}")
        print(f"{Colors.YELLOW}-------------------------------------------{Colors.RESET}", file=sys.stderr)

def main():
    """Synchronous entry point for the 'ai' command, required by pyproject.toml."""
    setup_logging()
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
    parser.add_argument(
        '-e', '--extract-symbol',
        dest='extract_symbols',
        action='append',
        nargs=2,
        metavar=('FILE_PATH', 'SYMBOL_NAME'),
        help="Extract only a specific class or function from a file for context. Use multiple times for multiple files."
    )
    parser.add_argument('-f', '--file', dest='files', action='append', help='Attach a file to the context. Can be used multiple times.')
    parser.add_argument('--persona', help='The alias of the persona to use (e.g., core/SA-1).')
    parser.add_argument('--autonomous', action='store_true', help='Run in autonomous mode.')
    parser.add_argument('--interactive', action='store_true', help='Start an interactive chat session.')
    parser.add_argument('--context', help='The name of the context plugin to use (e.g., Trading).')
    parser.add_argument('--output-dir', help='Activates Output-First mode, generating an execution package in the specified directory instead of executing live.')
    parser.add_argument('--show-context', action='store_true', help='Build and display the context from files and plugins, then exit without running the agent.')
    session_group = parser.add_mutually_exclusive_group()
    session_group.add_argument('--session', help='Continue an existing session by ID.')
    session_group.add_argument('--new-session', action='store_true', help='Start a new session.')    
    parser.add_argument('--list-plugins', action='store_true', help='List available context plugins')
    parser.add_argument('query', nargs='*', help="Your request for the agent. For tasks that modify files, wrap your goal in <ACTION> tags.")

    args = parser.parse_args()
    
    user_query = ' '.join(args.query)
    
    # Initialize args.files as a list if it's None
    if args.files is None:
        args.files = []

    # Prepend auto-injected files from config, ensuring no duplicates
    auto_injected_files = ai_settings.general.auto_inject_files or []
    # Use a set for efficient duplicate checking of already present files
    seen_files = set(args.files)
    
    # We prepend in reverse order so the final list has the config order correct
    for f_path in reversed(auto_injected_files):
        if f_path not in seen_files:
            args.files.insert(0, f_path)
            seen_files.add(f_path)
            
    if args.persona:
        try:
            # Find the manifest inside the installed package
            manifest_traversable = resources.files('ai_assistant').joinpath('internal_data/persona_manifest.yml')
            manifest_path = Path(str(manifest_traversable))
        except (ModuleNotFoundError, FileNotFoundError):
            print(f"{Colors.RED}🛑 HALTING: Could not locate the built-in persona manifest.{Colors.RESET}", file=sys.stderr)
            sys.exit(1)

        invalid, reason = is_manifest_invalid(manifest_path)
        if invalid:
            print(f"{Colors.RED}🛑 HALTING: The persona manifest is invalid. Reason: {reason}{Colors.RESET}", file=sys.stderr)
            print(f"{Colors.YELLOW}Please run 'python scripts/generate_manifest.py' to fix it.{Colors.RESET}", file=sys.stderr)
            sys.exit(1)
        logger.info("Persona manifest is valid and up-to-date.")
        
    if args.list_plugins:
        print(f"{Colors.BOLD}Available Context Plugins:{Colors.RESET}")
        plugins = list_available_plugins()
        if not plugins:
            print("  No plugins found.")
        for p in plugins:
            print(f"  - {p}")
        sys.exit(0)
        
    if args.list_personas:
        loader = PersonaLoader()
        all_personas = loader.list_all_personas()
        
        if all_personas.get("project"):
            print(f"{Colors.BOLD}Project-Local Personas (in .ai/personas):{Colors.RESET}")
            for p in all_personas["project"]:
                print(f" - {p}")
        
        if all_personas.get("user"):
            print(f"{Colors.BOLD}User-Global Personas (in ~/.config/ai_assistant/personas):{Colors.RESET}")
            for p in all_personas["user"]:
                print(f" - {p}")

        if all_personas.get("builtin"):
            print(f"{Colors.BOLD}Built-in Personas:{Colors.RESET}")
            for p in all_personas["builtin"]:
                print(f" - {p}")

        if not any(all_personas.values()):
            print("No personas found.")

        sys.exit(0)
        
    # --- Sanity checks now run only when proceeding with a query ---
    # Don't run sanity checks if we are just showing context
    if not args.show_context:
        _run_prompt_sanity_checks(args, user_query)

    session_manager = SessionManager()
    history = []
    session_id = None
    if args.new_session or (args.interactive and not args.session):
        session_id = session_manager.start_new_session()
        logger.info("Starting new session", session_id=session_id)
    elif args.session:
        session_id = args.session
        print(f"{Colors.CYAN}🔄 Continuing session: {session_id}{Colors.RESET}")
        history = session_manager.load_session(session_id) or []
    else:
        session_id = session_manager.start_new_session()
        print(f"{Colors.CYAN}✨ Starting new session (implicit): {session_id}{Colors.RESET}")

    full_context_str = ""
    context_plugin = None
    
    # --- MODIFIED: Made auto-loader more graceful ---
    # Get a list of available plugins once to avoid multiple discoveries
    available_plugins = list_available_plugins()

    # --- Automatic Domain-Based Plugin Loading ---                
    if args.persona and args.persona.startswith('domains/'):
        parts = args.persona.split('/')
        if len(parts) > 1:
            domain_name = parts[1]
            plugin_name_to_load = f"domains-{domain_name}"
            
            # Only attempt to load if the plugin actually exists
            if plugin_name_to_load in available_plugins:
                # --- REFACTORED: Load first, then print explicit message ---
                temp_plugin = load_context_plugin(plugin_name_to_load)
                if temp_plugin:
                    print(f"{Colors.MAGENTA}🔌 Persona '{args.persona}' triggered auto-loading of the '{temp_plugin.name}' context plugin.{Colors.RESET}")
                    context_plugin = temp_plugin
            
            else:
                # --- Feedback when an auto-plugin is not found ---
                print(f"{Colors.DIM}   - Searched for plugin '{plugin_name_to_load}' (triggered by persona '{args.persona}') but it was not found.{Colors.RESET}")
             
             
    # --- Manual Override ---
    # If the user specifies --context, it overrides any auto-loaded plugin.
    if args.context:
        print(f"{Colors.YELLOW}--context flag provided, overriding any auto-loaded plugin.{Colors.RESET}")
        context_plugin = load_context_plugin(args.context)

    if context_plugin:
        print(f"   - {Colors.GREEN}✅ Plugin loaded successfully.{Colors.RESET}")
        plugin_context = context_plugin.get_context(user_query, args.files or [])
        full_context_str += plugin_context
                
    if args.files:
        file_context = build_file_context(args.files, user_query)
        full_context_str += file_context

    # --- NEW: Handle --show-context flag ---
    if args.show_context:
        print(f"\n{Colors.BOLD}{Colors.CYAN}--- Generated Context Preview ---{Colors.RESET}")
        if full_context_str.strip():
            print(full_context_str)
        else:
            print(f"{Colors.YELLOW}No context was generated from the provided files or plugins.{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}---------------------------------{Colors.RESET}")
        sys.exit(0) # Exit after showing context

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
    logger.info("Processing one-shot query", query=display_query)
    if persona_alias: logger.info("Embodying persona", persona=persona_alias)
    if is_autonomous: logger.warning("RUNNING IN AUTONOMOUS MODE - NO CONFIRMATION WILL BE ASKED")
    if output_dir: logger.info("OUTPUT-FIRST MODE: Generating execution package", dir=output_dir)

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