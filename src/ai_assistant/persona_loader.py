# ai_assistant/persona_loader.py
import os
import yaml
from pathlib import Path
from typing import Optional, List
from importlib import resources

from .config import ai_settings

class PersonaLoader:
    def __init__(self):
        self.user_personas_dir = Path(ai_settings.general.personas_directory).resolve()
        self.user_personas_dir.mkdir(parents=True, exist_ok=True)
        self._loading_stack = set()

    def _load_recursive(self, alias: str) -> str:
        """Internal recursive loader for a single inheritance chain."""
        if alias in self._loading_stack:
            raise RecursionError(f"Circular persona inheritance detected: {alias} is in the stack {self._loading_stack}")
        self._loading_stack.add(alias)

        try:
            _, content = self._find_and_read_persona(alias)
            if not content:
                raise FileNotFoundError(f"Persona '{alias}' could not be found or read.")

            parts = content.split("---")
            body = "---".join(parts[2:]) if len(parts) >= 3 else content
            frontmatter_str = parts[1] if len(parts) >= 3 else "{}"
            
            data = yaml.safe_load(frontmatter_str) or {}
            inherits_from = data.get("inherits_from")

            if inherits_from:
                parent_content = self._load_recursive(inherits_from)
                return parent_content + "\n" + body.strip()
            else:
                return body.strip()
        finally:
            self._loading_stack.remove(alias)


    def load_persona_content(self, alias: str) -> Optional[str]:
        """
        Loads the full content of a persona, prepending the universal base
        persona if one is configured and not already in the inheritance chain.
        """
        self._loading_stack.clear()
        
        # First, load the specific persona and its entire inheritance chain
        specific_content = self._load_recursive(alias)
        
        # Now, check if a universal base is needed
        universal_base_alias = ai_settings.general.universal_base_persona
        if universal_base_alias and universal_base_alias not in self._loading_stack:
            # The universal base was NOT part of the chain, so we need to prepend it.
            # The loading stack from the previous call contains all ancestors.
            self._loading_stack.clear() # Reset for the base load
            try:
                base_content = self._load_recursive(universal_base_alias)
                return (base_content + "\n" + specific_content).strip()
            except (FileNotFoundError, RecursionError) as e:
                print(f"⚠️ Warning: Could not load universal base persona '{universal_base_alias}'. Reason: {e}")
                # Fall through to return just the specific content
        
        # Either no universal base is configured, or it was already inherited.
        return specific_content
    
    def _find_and_read_persona(self, alias: str):

        alias_norm = alias.lower().replace('/', os.sep)
        user_path = self.user_personas_dir / f"{alias_norm}.persona.md"

        if user_path.exists():
            print(f"ℹ️  Loading user-defined persona: {alias}")
            return user_path, user_path.read_text(encoding="utf-8")

        resource_path = f"personas/{alias.lower()}.persona.md"
        try:
            traversable = resources.files("ai_assistant").joinpath(resource_path)
            return Path(str(traversable)), traversable.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None, None 
        
    def list_builtin_personas(self) -> List[str]:

        personas = []
        try:
            base_dir = resources.files("ai_assistant").joinpath("personas")
            for path in base_dir.rglob("*.persona.md"):
                try:
                    rel_path = path.relative_to(base_dir)
                    persona_id = str(rel_path).replace(".persona.md", "").replace("\\", "/")
                    personas.append(persona_id)
                except ValueError:
                    continue
            return sorted(personas)
        except FileNotFoundError:
            return []