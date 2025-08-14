# ai_assistant/persona_loader.py
import os
import re
import yaml
from pathlib import Path
from typing import Optional, List, Tuple
from importlib import resources

from .config import ai_settings

# Define a type alias for clarity
ParsedPersona = Tuple[Optional[str], str]

class PersonaLoader:
    def __init__(self):
        self.user_personas_dir = Path(ai_settings.general.personas_directory).resolve()
        self.user_personas_dir.mkdir(parents=True, exist_ok=True)
        self._loading_stack = set()

    def _parse_content(self, content: str) -> ParsedPersona:
        """Extracts directives and returns the remaining context."""
        directives_section = None
        context_section = content

        # Use a regex to find and extract the <directives> block
        directives_match = re.search(r"<directives>.*?</directives>", content, re.DOTALL)
        if directives_match:
            directives_section = directives_match.group(0)
            # Remove the directives from the main content to avoid duplication
            context_section = content.replace(directives_section, "").strip()
        
        return (directives_section, context_section)

    def _load_recursive(self, alias: str) -> ParsedPersona:
        """Internal recursive loader, now returns a tuple of (directives, context)."""
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

            current_directives, current_context = self._parse_content(body.strip())

            if inherits_from:
                parent_directives, parent_context = self._load_recursive(inherits_from)
                
                # Combine directives and context from parent and child
                combined_directives = "\n".join(filter(None, [parent_directives, current_directives]))
                combined_context = "\n".join([parent_context, current_context]).strip()
                
                return (combined_directives if combined_directives else None, combined_context)
            else:
                return (current_directives, current_context)
        finally:
            self._loading_stack.remove(alias)

    def load_persona_content(self, alias: str) -> ParsedPersona:
        """
        Loads and parses a persona, returning a tuple of (directives, context).
        Prepends the universal base persona if configured.
        """
        self._loading_stack.clear()
        
        specific_directives, specific_context = self._load_recursive(alias)
        
        universal_base_alias = ai_settings.general.universal_base_persona
        if universal_base_alias and universal_base_alias not in self._loading_stack:
            self._loading_stack.clear()
            try:
                base_directives, base_context = self._load_recursive(universal_base_alias)
                
                # Combine universal base with the specific persona
                final_directives = "\n".join(filter(None, [base_directives, specific_directives]))
                final_context = (base_context + "\n" + specific_context).strip()

                return (final_directives if final_directives else None, final_context)
            except (FileNotFoundError, RecursionError) as e:
                print(f"⚠️ Warning: Could not load universal base persona '{universal_base_alias}'. Reason: {e}")
        
        return (specific_directives, specific_context)
    
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