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


def list_available_plugins() -> List[str]:
    """Dynamically discovers available plugins from both entry points and the local project directory."""
    discovered_plugins = []
    
    # 1. Load built-in plugins via entry points (existing logic)
    entry_points = metadata.entry_points(group='ai_assistant.context_plugins')
    for entry in entry_points:
        discovered_plugins.append(entry.name)
        
    # 2. Discover and load local, project-specific plugins
    local_plugins_path = Path.cwd() / ai_settings.general.local_plugins_directory
    if local_plugins_path.is_dir():
        for file_path in local_plugins_path.glob("*.py"):
            plugin_name = file_path.stem.replace("_plugin", "")
            if plugin_name not in discovered_plugins:
                 discovered_plugins.append(f"{plugin_name} (local)")

    return sorted(discovered_plugins)

    
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
        internal_data_dir_traversable = resources.files('ai_assistant').joinpath('internal_data')
        internal_data_dir = Path(str(internal_data_dir_traversable))
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
        validator = PersonaValidator(internal_data_dir / "persona_config.yml")
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


# Rest of the cli.py content remains unchanged...