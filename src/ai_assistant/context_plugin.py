# src/ai_assistant/context_plugin.py
from typing import List, Tuple
from pathlib import Path
import inspect

class ContextPluginBase:
    """Base class for all context plugins."""
    name = "Base Plugin"
    
    def __init__(self, project_root: Path):
        """Initializes the plugin with the project's root directory."""
        self.project_root = project_root

    def get_context(self, query: str, files: List[str]) -> Tuple[bool, str]:
        """
        Synchronous method for getting context. Deprecated in favor of get_context_async.
        """
        return (True, "")

    async def get_context_async(self, query: str, files: List[str]) -> Tuple[bool, str]:
        """
        Asynchronous method for getting context. This is the preferred method.
        If a plugin does not override this, it will fall back to the synchronous version.
        """
        return self.get_context(query, files)

    @property
    def is_async(self) -> bool:
        """Checks if the plugin has an overridden async implementation."""
        return inspect.iscoroutinefunction(self.get_context_async) and \
               self.get_context_async.__func__ is not ContextPluginBase.get_context_async