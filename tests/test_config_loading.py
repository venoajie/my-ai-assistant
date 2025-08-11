import os
import tempfile
import unittest
from pathlib import Path
from ai_assistant.config import load_ai_settings

class TestConfigLoading(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        os.chdir(self.temp_dir.name)
        
        # Create config files
        self.create_config(".ai_config.yml", """
        assistant:
          max_context_files: 3
        """)
        
        self.create_config("user_config.yml", """
        general:
          sessions_directory: '/custom/sessions'
        """)

    def create_config(self, filename, content):
        (Path.cwd() / filename).write_text(content)

    def test_config_priority(self):
        # Simulate layered config loading
        settings = load_ai_settings()
        self.assertEqual(settings.general.sessions_directory, "/custom/sessions")
        self.assertEqual(settings.assistant.max_context_files, 3)

    def test_default_fallback(self):
        # Test when project config is missing
        os.remove(".ai_config.yml")
        settings = load_ai_settings()
        self.assertEqual(settings.tools.git.branch_prefix, "ai")  # From defaults

if __name__ == "__main__":
    unittest.main()