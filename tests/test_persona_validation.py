import unittest
from pathlib import Path
from ai_assistant.utils.persona_validator import PersonaValidator

class TestPersonaValidation(unittest.TestCase):
    """
    Tests the PersonaValidator class by running it against all discovered personas.
    """

    def setUp(self):
        """Set up the test environment."""
        # Assumes tests are run from the project root directory
        self.project_root = Path.cwd()
        self.personas_dir = self.project_root / "src" / "ai_assistant" / "personas"
        self.config_path = self.project_root / "persona_config.yml"
        
        if not self.personas_dir.exists():
            self.fail(f"Personas directory not found at {self.personas_dir}")
        if not self.config_path.exists():
            self.fail(f"Persona config file not found at {self.config_path}")

    def test_all_personas_are_valid(self):
        """
        Validates every .persona.md file found in the personas directory.
        """
        validator = PersonaValidator(self.config_path)
        persona_files = list(self.personas_dir.rglob("*.persona.md"))
        
        self.assertTrue(
            len(persona_files) > 0,
            "No persona files were found to validate."
        )

        failures = []
        for persona_path in persona_files:
            is_valid, reason = validator.validate_persona(persona_path, self.personas_dir)
            if not is_valid:
                relative_path = persona_path.relative_to(self.project_root)
                failures.append(f"  - {relative_path}: {reason}")

        if failures:
            error_messages = "\n".join(failures)
            self.fail(f"Persona validation failed for the following files:\n{error_messages}")

        print(f"\n✅ Successfully validated {len(persona_files)} persona files.")

if __name__ == '__main__':
    unittest.main()