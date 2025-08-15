# src/ai_assistant/persona_validator.py
import yaml
from pathlib import Path
import os
import re

class PersonaValidator:
    def __init__(self, config_path: Path):
        """Initializes the validator by loading the canonical rules from a config file."""
        if not config_path.exists():
            raise FileNotFoundError(f"FATAL: Persona config file not found at {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        self.persona_types = self.config.get('persona_types', {})
        self.body_schemas = self.config.get('body_schemas_by_type', {})

    def _validate_frontmatter(
        self, 
        data: dict, 
        persona_type: str,
        ):
        
        """Validates the YAML frontmatter dictionary."""
        if persona_type not in self.persona_types:
            return False, f"Frontmatter: Invalid persona type '{persona_type}'"

        required_keys = self.persona_types[persona_type].get('required_keys', [])
        for key in required_keys:
            if key not in data:
                return False, f"Frontmatter: Missing required key '{key}' for type '{persona_type}'"
        return True, "OK"

    def _validate_body(
        self, 
        body_content: str, 
        persona_type: str,
        ):
        
        """Validates that the persona body contains all required sections."""
        required_sections = self.body_schemas.get(persona_type, [])
        if not required_sections:
            return True, "OK" # No body validation required for this type

        missing_sections = []
        for section in required_sections:
            pattern = re.compile(f"<SECTION:{section}>.*?</SECTION:{section}>", re.DOTALL)
            if not pattern.search(body_content):
                missing_sections.append(section)

        if missing_sections:
            return False, f"Body: Missing required sections: {', '.join(missing_sections)}"
        return True, "OK"

    def validate_persona(
        self, 
        persona_path: Path, 
        personas_root: Path,
        ):
        
        """
        Validates a single persona file against all loaded rules (frontmatter and body).
        Returns (True, "OK") on success or (False, "Error message") on failure.
        """
        try:
            content = persona_path.read_text(encoding="utf-8")
            parts = content.split("---")
            if len(parts) < 3:
                return False, f"Malformed file (missing '---' separators)"

            frontmatter_data = yaml.safe_load(parts[1])
            if not isinstance(frontmatter_data, dict):
                return False, "Invalid YAML frontmatter (not a dictionary)"

            persona_type = frontmatter_data.get('type')
            is_valid, reason = self._validate_frontmatter(frontmatter_data, persona_type)
            if not is_valid:
                return False, reason

            expected_alias = str(persona_path.relative_to(personas_root)).replace(".persona.md", "").replace(os.path.sep, "/")
            actual_alias = frontmatter_data.get("alias")
            if not actual_alias or expected_alias.lower() != actual_alias.lower():
                return False, f"Filename-Alias Mismatch: Path implies '{expected_alias}', but alias is '{actual_alias}'"

            body_content = "---".join(parts[2:])
            is_valid, reason = self._validate_body(body_content, persona_type)
            if not is_valid:
                return False, reason

        except Exception as e:
            return False, f"An unexpected error occurred: {e}"

        return True, "OK"