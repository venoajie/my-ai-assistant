# tests/test_persona_validation.py
import unittest
import subprocess
import sys
from pathlib import Path

class TestPersonaValidation(unittest.TestCase):
    def test_all_personas_are_valid(self):
        """
        Runs the persona validation script and asserts that it exits with code 0.
        This test ensures that all bundled personas adhere to the defined standards.
        """
        project_root = Path(__file__).parent.parent
        script_path = project_root / "scripts" / "validate_personas.py"
        
        # We must use the same Python executable that is running the tests
        python_executable = sys.executable
        
        result = subprocess.run(
            [python_executable, str(script_path)],
            capture_output=True,
            text=True
        )
        
        # Assert that the script exited successfully (exit code 0)
        self.assertEqual(
            result.returncode, 0,
            f"Persona validation failed. Output:\n{result.stdout}\n{result.stderr}"
        )