# ai_assistant/persona_loader.py
import os
import yaml
from pathlib import Path
from typing import Optional, List
from importlib import resources
from pathlib import PurePath

from .config import ai_settings

class PersonaLoader:
    def __init__(self):
        
        self.user_personas_dir = Path(ai_settings.general.personas_directory).resolve()
        self.user_personas_dir.mkdir(parents=True, exist_ok=True)
        
    def load_persona_content(self, alias: str) -> Optional[str]:
        
        alias = alias.lower()  # Normalize case
        
        # Do not use .name, preserve the full alias path for user overrides
        # Use os.sep here because we are interacting with the real filesystem
        user_path = self.user_personas_dir / f"{alias.replace('/', os.sep)}.persona.md"
        if user_path.exists():
            print(f"ℹ️  Loading user-defined persona: {alias}")
            return self._read_persona(user_path)
        
        #resource_path = f"personas/{alias.replace('/', os.sep)}.persona.md" 
        # Use POSIX forward slashes for package resources, regardless of OS
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
            return content
        except Exception as e:
            print(f"Error reading persona: {e}")
            return None
            
    def list_builtin_personas(self) -> List[str]:
        personas = []
        try:
            base_dir = resources.files("ai_assistant").joinpath("personas")
            # Use the actual base directory for relative paths
            for path in base_dir.rglob("*.persona.md"):
                try:
                    # Get relative path to base_dir
                    rel_path = path.relative_to(base_dir)
                    # Convert to POSIX format with forward slashes
                    persona_id = str(rel_path).replace(".persona.md", "").replace("\\", "/")
                    personas.append(persona_id)
                except ValueError:
                    # Skip files not in base_dir
                    continue
            return sorted(personas)
        except FileNotFoundError:
            return []