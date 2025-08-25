# src/ai_assistant/context_plugin.py
from typing import List, Tuple
from pathlib import Path

class ContextPluginBase:
    """Base class for all context plugins."""
    name = "Base Plugin"
    
    def __init__(self, project_root: Path):
        """Initializes the plugin with the project's root directory."""
        self.project_root = project_root

    def get_context(self, query: str, files: List[str]) -> Tuple[bool, str]:
        """
        Analyzes the query and files to provide domain-specific context.
        Returns a tuple of (success, content_or_error_message).
        """
        return (True, "") # Default is to provide no extra context.