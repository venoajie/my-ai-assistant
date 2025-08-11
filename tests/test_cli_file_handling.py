import os
import subprocess
import tempfile
import unittest
from pathlib import Path

class TestCLIFileHandling(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        os.chdir(self.temp_dir.name)
        
        # Create sample files
        (Path.cwd() / "sample.py").write_text("print('Hello')")
        (Path.cwd() / "test_dir").mkdir()
        (Path.cwd() / "test_dir" / "file.txt").write_text("Test content")

    def test_file_attachment(self):
        result = subprocess.run(
            ["ai", "-f", "sample.py", "Explain this code"],
            capture_output=True,
            text=True
        )
        self.assertIn("print('Hello')", result.stdout)
        self.assertIn("Python code", result.stdout)

    def test_directory_listing(self):
        result = subprocess.run(
            ["ai", "List files in test_dir"],
            capture_output=True,
            text=True
        )
        self.assertIn("file.txt", result.stdout)
        self.assertEqual(result.returncode, 0)

    def test_file_generation(self):
        result = subprocess.run(
            ["ai", "--autonomous", "Create file.txt with content 'Test'"],
            capture_output=True,
            text=True
        )
        self.assertTrue(Path("file.txt").exists())
        self.assertIn("Created file.txt", result.stdout)

    def tearDown(self):
        self.temp_dir.cleanup()

if __name__ == "__main__":
    unittest.main()