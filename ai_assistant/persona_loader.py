# ai_assistant/persona_loader.py
import os
import yaml
from pathlib import Path
from typing import Optional
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
        
        # Check package resources
        resource_path = f"personas/{alias}.persona.md"
        try:
            with resources.open_text("ai_assistant", resource_path) as f:
                return f.read()
        except FileNotFoundError:
            return None

    def _read_persona(self, path: Path) -> str:
        try:
            content = path.read_text(encoding="utf-8")
            parts = content.split("---")
            return "---".join(parts[2:]).strip() if len(parts) >= 3 else content
        except Exception as e:
            print(f"Error reading persona: {e}")
            return None