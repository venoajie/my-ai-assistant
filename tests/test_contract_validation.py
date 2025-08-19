import unittest
import json
from pathlib import Path
import jsonschema
import asyncio
import shutil
import tempfile

# This sys.path manipulation is necessary for the test runner to find the package source
import sys
project_root = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(project_root / 'src'))

from ai_assistant import kernel

class TestContractValidation(unittest.TestCase):
    """
    Validates that generated artifacts adhere to the schemas defined in the project's data contracts.
    """

    def setUp(self):
        """Set up paths for schemas and fixtures, and create a temporary directory for test outputs."""
        self.schemas_dir = project_root / "tests" / "schemas"
        self.fixtures_dir = project_root / "tests" / "fixtures"
        self.manifest_schema_path = self.schemas_dir / "output_package_manifest_schema.json"
        
        self.temp_dir = Path(tempfile.mkdtemp())

        self.assertTrue(self.manifest_schema_path.exists(), "Manifest JSON schema is missing.")
        with open(self.manifest_schema_path, 'r', encoding='utf-8') as f:
            self.manifest_schema = json.load(f)

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_fixture_manifest_is_valid(self):
        """
        Validates a static, known-good manifest fixture against the JSON schema.
        This confirms the schema itself is correct and hasn't drifted from the fixture.
        """
        fixture_path = self.fixtures_dir / "sample_manifest.json"
        self.assertTrue(fixture_path.exists(), "Sample manifest fixture is missing.")
        
        with open(fixture_path, 'r', encoding='utf-8') as f:
            fixture_data = json.load(f)
            
        try:
            jsonschema.validate(instance=fixture_data, schema=self.manifest_schema)
        except jsonschema.ValidationError as e:
            self.fail(f"Fixture manifest failed validation: {e}")

    def test_generated_manifest_is_valid(self):
        """
        Generates an Output Package Manifest using the kernel and validates it against the schema.
        This is the key test to prevent contract drift in the application code.
        """
        # 1. Define a sample plan for the kernel to process
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

        # 2. Run the async kernel function to generate the package
        result = asyncio.run(kernel._handle_output_first_mode(
            plan=sample_plan,
            persona_alias="core/arc-1",
            metrics={},
            output_dir_str=str(self.temp_dir)
        ))

        # 3. Check that the manifest was created
        generated_manifest_path = self.temp_dir / "manifest.json"
        self.assertTrue(generated_manifest_path.exists(), "Kernel failed to generate manifest.json")
        self.assertIn("manifest", result, "Kernel result did not contain manifest data.")

        # 4. Load and validate the generated manifest
        with open(generated_manifest_path, 'r', encoding='utf-8') as f:
            generated_data = json.load(f)

        try:
            jsonschema.validate(instance=generated_data, schema=self.manifest_schema)
            print("\n✅ Successfully validated a dynamically generated manifest against the contract schema.")
        except jsonschema.ValidationError as e:
            self.fail(f"Generated manifest failed validation against the schema: {e}")

if __name__ == '__main__':
    unittest.main()