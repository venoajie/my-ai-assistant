import asyncio
import unittest
from pathlib import Path
from src.ai_assistant.tools import ReadFileTool

class TestReadFileTool(unittest.TestCase):
    def setUp(self):
        self.tool = ReadFileTool()
        self.test_file_path = 'test_file.txt'
        with open(self.test_file_path, 'w') as f:
            f.write('test content')

    async def test_read_file_success(self):
        success, content = await self.tool(self.test_file_path)
        self.assertTrue(success)
        self.assertEqual(content, 'test content')

    async def test_read_file_failure(self):
        success, content = await self.tool('non_existent_file.txt')
        self.assertFalse(success)
        self.assertIn('Error: File not found', content)

    def tearDown(self):
        Path(self.test_file_path).unlink(missing_ok=True)

if __name__ == '__main__':
    unittest.main()