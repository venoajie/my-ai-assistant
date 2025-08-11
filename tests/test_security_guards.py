import unittest
from ai_assistant.tools import RunShellCommandTool
from ai_assistant._security_guards import SHELL_COMMAND_BLOCKLIST

class TestSecurityGuards(unittest.TestCase):
    def test_dangerous_commands(self):
        tool = RunShellCommandTool()
        
        for pattern in SHELL_COMMAND_BLOCKLIST:
            # Test pattern matching
            test_cmd = f"sudo {pattern.strip()}"
            success, result = tool(test_cmd)
            self.assertFalse(success)
            self.assertIn("SECURITY BLOCK", result)
            
    def test_safe_commands(self):
        tool = RunShellCommandTool()
        safe_commands = [
            "ls -la",
            "git status",
            "python --version",
            "echo 'Hello'"
        ]
        
        for cmd in safe_commands:
            success, result = tool(cmd)
            self.assertTrue(success)
            self.assertNotIn("SECURITY BLOCK", result)

if __name__ == "__main__":
    unittest.main()