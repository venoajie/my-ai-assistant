# scripts/persona_validator.py
import yaml
from pathlib import Path
import os
import sys

class PersonaValidator:
    def __init__(self, config_path: Path):
        """Initializes the validator by loading the canonical rules from a config file."""
        if not config_path.exists():
            raise FileNotFoundError(f"FATAL: Persona config file not found at {config_path}")
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.persona_types = self.config.get('persona_types', {})

    def validate_persona(self, persona_path: Path, personas_root: Path) -> (bool, str):
        """
        Validates a single persona file against the loaded rules.
        Returns (True, "OK") on success or (False, "Error message") on failure.
        """
        try:
            content = persona_path.read_text(encoding="utf-8")
            parts = content.split("---")
            if len(parts) < 3:
                return False, f"Malformed file (missing '---' separators)"

            data = yaml.safe_load(parts[1])
            if not isinstance(data, dict):
                return False, "Invalid YAML frontmatter (not a dictionary)"

            # Rule 1: Validate Persona Type
            persona_type = data.get('type')
            if persona_type not in self.persona_types:
                return False, f"Frontmatter: Invalid persona type '{persona_type}'"

            # Rule 2: Validate Required Keys for the given type
            required_keys = self.persona_types[persona_type].get('required_keys', [])
            for key in required_keys:
                if key not in data:
                    return False, f"Frontmatter: Missing required key '{key}' for type '{persona_type}'"

            # Rule 3: Validate Filename-Alias Mismatch (using the CANONICAL logic)
            expected_alias = str(persona_path.relative_to(personas_root)).replace(".persona.md", "").replace(os.path.sep, "/")
            actual_alias = data.get("alias")
            if not actual_alias or expected_alias.lower() != actual_alias.lower():
                return False, f"Filename-Alias Mismatch: Path implies '{expected_alias}', but alias is '{actual_alias}'"
            
        except Exception as e:
            return False, f"An unexpected error occurred: {e}"

        return True, "OK"