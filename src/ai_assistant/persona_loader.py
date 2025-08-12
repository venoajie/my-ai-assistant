# ai_assistant/persona_loader.py
import os
import yaml
from pathlib import Path
from typing import Optional
# MODIFIED: 'resources' is the only import needed from importlib
from importlib import resources

class PersonaLoader:
    def __init__(self):
        self.user_personas_dir = Path.home() / ".config" / "ai_assistant" / "personas"
        self.user_personas_dir.mkdir(parents=True, exist_ok=True)

    def load_persona_content(self, alias: str) -> Optional[str]:
        # Check user override first
        user_path = self.user_personas_dir / f"{alias.replace('/', os.sep)}.persona.md"
        if user_path.exists():
            return self._read_persona(user_path)
        
        # MODIFIED: Use the modern `files()` API to correctly handle nested directories.
        # This is the definitive fix for the ValueError.
        resource_path = f"personas/{alias}.persona.md"
        try:
            # This returns a traversable object for the package data
            traversable = resources.files("ai_assistant").joinpath(resource_path)
            return traversable.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None

    def _read_persona(self, path: Path) -> str:
        try:
            content = path.read_text(encoding="utf-8")
            # This logic to strip YAML frontmatter is incorrect. It should be removed
            # as the persona content is the entire file.
            # parts = content.split("---")
            # return "---".join(parts[2:]).strip() if len(parts) >= 3 else content
            return content
        except Exception as e:
            print(f"Error reading persona: {e}")
            return None