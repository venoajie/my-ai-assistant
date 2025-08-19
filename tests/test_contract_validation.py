# tests/test_contract_validation.py
import unittest
import json
from pathlib import Path
import jsonschema
import asyncio
import shutil
import tempfile
from importlib import resources

from ai_assistant import kernel

class TestContractValidation(unittest.TestCase):
    """
    Validates that generated artifacts adhere to the schemas defined in the project's data contracts.
    """

    def setUp(self):
        """Set up paths for schemas and fixtures, and create a temporary directory for test outputs."""
        self.temp_dir = Path(tempfile.mkdtemp())

        # --- THIS IS THE FIX ---
        # Use the new, unambiguous package name to load resources.
        try:
            schema_path = resources.files('ai_assistant._test_data.schemas').joinpath('output_package_manifest_schema.json')
            with schema_path.open('r', encoding='utf-8') as f:
                self.manifest_schema = json.load(f)
        except (FileNotFoundError, ModuleNotFoundError):
            self.fail("Could not load manifest JSON schema from package resources. Check file location and pyproject.toml.")

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_fixture_manifest_is_valid(self):
        """
        Validates a static, known-good manifest fixture against the JSON schema.
        This confirms the schema itself is correct and hasn't drifted from the fixture.
        """
        # --- THIS IS THE FIX ---
        # Use the new, unambiguous package name to load resources.
        try:
            fixture_path = resources.files('ai_assistant._test_data.fixtures').joinpath('sample_manifest.json')
            with fixture_path.open('r', encoding='utf-8') as f:
                fixture_data = json.load(f)
        except (FileNotFoundError, ModuleNotFoundError):
            self.fail("Could not load sample manifest fixture from package resources. Check file location and pyproject.toml.")
            
        try:
            jsonschema.validate(instance=fixture_data, schema=self.manifest_schema)
        except jsonschema.ValidationError as e:
            self.fail(f"Fixture manifest failed validation: {e}")

    def test_generated_manifest_is_valid(self):
        """
        Generates an Output Package Manifest using the kernel and validates it against the schema.
        This is the key test to prevent contract drift in the application code.
        """
        # (This test method remains unchanged)
        sample_plan = [
            {
                "tool_name": "git_create_branch",
                "args": {"branch_name": "test-branch"},
                "thought": "Start a new branch for the work."
            },
            {
                "tool_name": "write_file",
                "args": {"path": "README.md", "content": "# New Readme"},
                "thought": "Create a readme file."
            },
            {
                "tool_name": "git_add",
                "args": {"path": "."},
                "thought": "Stage all changes."
            },
            {
                "tool_name": "git_commit",
                "args": {"commit_message": "feat: Initial commit"},
                "thought": "Commit the staged changes."
            }
        ]

        result = asyncio.run(kernel._handle_output_first_mode(
            plan=sample_plan,
            persona_alias="core/arc-1",
            metrics={},
            output_dir_str=str(self.temp_dir)
        ))

        generated_manifest_path = self.temp_dir / "manifest.json"
        self.assertTrue(generated_manifest_path.exists(), "Kernel failed to generate manifest.json")
        self.assertIn("manifest", result, "Kernel result did not contain manifest data.")

        with open(generated_manifest_path, 'r', encoding='utf-8') as f:
            generated_data = json.load(f)

        try:
            jsonschema.validate(instance=generated_data, schema=self.manifest_schema)
            print("\n✅ Successfully validated a dynamically generated manifest against the contract schema.")
        except jsonschema.ValidationError as e:
            self.fail(f"Generated manifest failed validation against the schema: {e}")

if __name__ == '__main__':
    unittest.main()