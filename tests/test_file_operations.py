import os
import tempfile
import unittest
from pathlib import Path
from ai_assistant.tools import ReadFileTool, WriteFileTool, ListFilesTool

class TestFileOperations(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file = Path(self.temp_dir.name) / "test.txt"
        self.test_file.write_text("Hello, world!")
        
        self.sub_dir = Path(self.temp_dir.name) / "test_dir"
        self.sub_dir.mkdir()
        (self.sub_dir / "file1.txt").write_text("File 1")
        (self.sub_dir / "file2.txt").write_text("File 2")

    def test_read_file(self):
        tool = ReadFileTool()
        success, content = tool(str(self.test_file))
        self.assertTrue(success)
        self.assertEqual(content, "Hello, world!")

    def test_write_file(self):
        tool = WriteFileTool()
        new_file = Path(self.temp_dir.name) / "new.txt"
        success, _ = tool(str(new_file), "New content")
        self.assertTrue(success)
        self.assertEqual(new_file.read_text(), "New content")

    def test_list_files(self):
        tool = ListFilesTool()
        success, listing = tool(str(self.sub_dir))
        self.assertTrue(success)
        self.assertIn("file1.txt", listing)
        self.assertIn("file2.txt", listing)

    def tearDown(self):
        self.temp_dir.cleanup()

if __name__ == "__main__":
    unittest.main()