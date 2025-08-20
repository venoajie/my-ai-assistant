# ai_assistant/persona_loader.py
import os
import re
import yaml
from pathlib import Path
from typing import Optional, List, Tuple
from importlib import resources

from .config import ai_settings

# Define a type alias for clarity
ParsedPersona = Tuple[Optional[str], str, Optional[List[str]]]

class PersonaLoader:
    def __init__(self):
        self.user_personas_dir = ai_settings.paths.user_personas_dir
        self.user_personas_dir.mkdir(parents=True, exist_ok=True)
        self.project_local_personas_dir = ai_settings.paths.project_local_personas_dir
        self._loading_stack = set()
        
    def _parse_content(self, content: str) -> Tuple[Optional[str], str]:
        """Extracts directives and returns the remaining context."""
        directives_section = None
        context_section = content

        directives_match = re.search(r"<directives>.*?</directives>", content, re.DOTALL)
        if directives_match:
            directives_section = directives_match.group(0)
            context_section = content.replace(directives_section, "").strip()
        
        return (directives_section, context_section)

    def _load_recursive(self, alias: str) -> ParsedPersona:
        """Internal recursive loader, now returns a tuple of (directives, context, allowed_tools)."""
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
            allowed_tools = data.get("allowed_tools")

            current_directives, current_context = self._parse_content(body.strip())

            if inherits_from:
                parent_directives, parent_context, parent_allowed_tools = self._load_recursive(inherits_from)
                
                final_allowed_tools = allowed_tools if allowed_tools is not None else parent_allowed_tools
                
                combined_directives = "\n".join(filter(None, [parent_directives, current_directives]))
                combined_context = "\n".join([parent_context, current_context]).strip()
                
                return (combined_directives if combined_directives else None, combined_context, final_allowed_tools)
            else:
                return (current_directives, current_context, allowed_tools)
        finally:
            self._loading_stack.remove(alias)

    def load_persona_content(self, alias: str) -> ParsedPersona:
        """
        Loads and parses a persona, returning a tuple of (directives, context, allowed_tools).
        Prepends the universal base persona if configured.
        """
        self._loading_stack.clear()
        
        specific_directives, specific_context, specific_allowed_tools = self._load_recursive(alias)
        
        universal_base_alias = ai_settings.general.universal_base_persona
        if universal_base_alias and alias != universal_base_alias:
            self._loading_stack.clear()
            try:
                # --- THE DEFINITIVE FIX IS HERE ---
                # Load the universal base, but only use its text content.
                # The rules (`allowed_tools`) must ALWAYS come from the specific persona's own inheritance chain.
                base_directives, base_context, _ = self._load_recursive(universal_base_alias)
                
                final_directives = "\n".join(filter(None, [base_directives, specific_directives]))
                final_context = (base_context + "\n" + specific_context).strip()

                # Always return the allowed_tools from the specific persona, not the universal base.
                return (final_directives if final_directives else None, final_context, specific_allowed_tools)
            except (FileNotFoundError, RecursionError) as e:
                print(f"⚠️ Warning: Could not load universal base persona '{universal_base_alias}'. Reason: {e}")
        
        return (specific_directives, specific_context, specific_allowed_tools)
    
    def _find_and_read_persona(self, alias: str):
        """Finds and reads a persona file in the correct override order."""
        alias_norm = alias.lower().replace('/', os.sep)
        
        if self.project_local_personas_dir.exists():
            project_local_path = self.project_local_personas_dir / f"{alias_norm}.persona.md"
            if project_local_path.exists():
                print(f"ℹ️  Loading project-local persona: {alias}")
                return project_local_path, project_local_path.read_text(encoding="utf-8")

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