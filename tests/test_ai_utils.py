import unittest
from unittest.mock import patch, MagicMock
import subprocess
from src.file_manager.ai_utils import AIExecutor

class TestAIExecutor(unittest.TestCase):
    def setUp(self):
        # We need to patch find_gemini_executable during instantiation
        with patch('src.file_manager.ai_utils.find_gemini_executable') as mock_find:
            mock_find.return_value = '/usr/local/bin/gemini'
            self.executor = AIExecutor()

    @patch('src.file_manager.ai_utils.find_gemini_executable')
    def test_is_available(self, mock_find):
        # Test available
        mock_find.return_value = '/usr/local/bin/gemini'
        executor = AIExecutor()
        self.assertTrue(executor.is_available())

        # Test unavailable
        mock_find.return_value = None
        executor = AIExecutor()
        self.assertFalse(executor.is_available())

    @patch('subprocess.run')
    def test_execute_prompt_success(self, mock_run):
        # Mock successful subprocess run
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Successful response"
        mock_run.return_value = mock_result

        response = self.executor.execute_prompt("Hello")
        self.assertEqual(response, "Successful response")
        mock_run.assert_called_once()

    def test_execute_prompt_no_executable(self):
        self.executor.gemini_path = None
        response = self.executor.execute_prompt("Hello")
        self.assertIn("Error: Gemini CLI not found", response)

    @patch('subprocess.run')
    def test_execute_prompt_error_return_code(self, mock_run):
        # Mock error return code
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Error message"
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        response = self.executor.execute_prompt("Hello")
        self.assertIn("Error (1): Error message", response)

    @patch('subprocess.run')
    def test_execute_prompt_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["gemini"], timeout=30)

        response = self.executor.execute_prompt("Hello")
        self.assertEqual(response, "Error: Request timed out.")

    @patch('subprocess.run')
    def test_execute_prompt_exception(self, mock_run):
        mock_run.side_effect = Exception("Something went wrong")

        response = self.executor.execute_prompt("Hello")
        self.assertIn("Error executing AI command: Something went wrong", response)

    @patch.object(AIExecutor, 'execute_prompt')
    def test_generate_automation_command_success(self, mock_execute):
        mock_execute.return_value = "tfm-auto organize --source /src --target /dst --by-type"

        command, status = self.executor.generate_automation_command("organize my files")
        self.assertEqual(command, "tfm-auto organize --source /src --target /dst --by-type")
        self.assertEqual(status, "Command generated successfully.")

    @patch.object(AIExecutor, 'execute_prompt')
    def test_generate_automation_command_error(self, mock_execute):
        mock_execute.return_value = "ERROR: Unclear request"

        command, status = self.executor.generate_automation_command("do something vague")
        self.assertIsNone(command)
        self.assertEqual(status, "ERROR: Unclear request")

    @patch.object(AIExecutor, 'execute_prompt')
    def test_generate_automation_command_extraction(self, mock_execute):
        # Mock response with markdown code block
        mock_execute.return_value = "Here is the command:\n```bash\ntfm-auto search --dir . --name *.txt\n```"

        command, status = self.executor.generate_automation_command("find txt files")
        self.assertEqual(command, "tfm-auto search --dir . --name *.txt")
        self.assertEqual(status, "Command extracted from response.")

    @patch.object(AIExecutor, 'execute_prompt')
    def test_generate_automation_command_invalid(self, mock_execute):
        mock_execute.return_value = "I don't know how to do that."

        command, status = self.executor.generate_automation_command("make me a coffee")
        self.assertIsNone(command)
        self.assertIn("Could not generate a valid command", status)

if __name__ == '__main__':
    unittest.main()
