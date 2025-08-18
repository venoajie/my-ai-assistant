# ai_assistant/context_plugin.py
from typing import List, Dict
from pathlib import Path

class ContextPluginBase:
    """Base class for all context plugins."""
    name = "Base Plugin"
    
    def __init__(self, project_root: Path):
        """Initializes the plugin with the project's root directory."""
        self.project_root = project_root

    def get_context(self, query: str, files: List[str]) -> str:
        """
        Analyzes the query and files to provide domain-specific context.
        Returns a string to be prepended to the AI's prompt.
        """
        return "" # Default is to provide no extra context.
