import unittest
from unittest.mock import patch, MagicMock
import subprocess
import selectors
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

    # Tests for execute_prompt (mocking _run_with_limit)

    @patch.object(AIExecutor, '_run_with_limit')
    def test_execute_prompt_success(self, mock_run):
        # Mock successful run
        mock_run.return_value = (0, "Successful response", "")

        response = self.executor.execute_prompt("Hello")
        self.assertEqual(response, "Successful response")
        mock_run.assert_called_once()

    def test_execute_prompt_no_executable(self):
        self.executor.gemini_path = None
        response = self.executor.execute_prompt("Hello")
        self.assertIn("Error: Gemini CLI not found", response)

    @patch.object(AIExecutor, '_run_with_limit')
    def test_execute_prompt_error_return_code(self, mock_run):
        # Mock error return code
        mock_run.return_value = (1, "", "Error message")

        response = self.executor.execute_prompt("Hello")
        self.assertIn("Error (1): Error message", response)

    @patch.object(AIExecutor, '_run_with_limit')
    def test_execute_prompt_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["gemini"], timeout=30)

        response = self.executor.execute_prompt("Hello")
        self.assertEqual(response, "Error: Request timed out.")

    @patch.object(AIExecutor, '_run_with_limit')
    def test_execute_prompt_exception(self, mock_run):
        mock_run.side_effect = Exception("Something went wrong")

        response = self.executor.execute_prompt("Hello")
        self.assertIn("Error executing AI command: Something went wrong", response)

    @patch.object(AIExecutor, '_run_with_limit')
    def test_execute_prompt_limit_exceeded(self, mock_run):
        mock_run.side_effect = ValueError("Output exceeded limit")

        response = self.executor.execute_prompt("Hello")
        self.assertEqual(response, "Error: Output exceeded limit.")

    # Tests for _run_with_limit (mocking Popen and selectors)

    @patch('subprocess.Popen')
    @patch('selectors.DefaultSelector')
    def test_run_with_limit_success(self, mock_selector, mock_popen):
        # Setup mocks
        mock_process = MagicMock()
        # Process is already finished when we check it
        mock_process.poll.return_value = 0
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        mock_stdout = MagicMock()
        mock_stderr = MagicMock()
        mock_process.stdout = mock_stdout
        mock_process.stderr = mock_stderr

        mock_sel_instance = mock_selector.return_value

        # Simulate selector returning one event then empty (finished)
        key = MagicMock()
        key.fileobj = mock_stdout

        # select() returns [(key, mask)]
        mock_sel_instance.select.side_effect = [
            [(key, selectors.EVENT_READ)], # First iteration: read data
            [] # Second iteration: no data, process poll checks
        ]

        # read() returns data then empty
        mock_stdout.read.side_effect = ["output data", ""]

        returncode, stdout, stderr = self.executor._run_with_limit(["cmd"])

        self.assertEqual(returncode, 0)
        self.assertEqual(stdout, "output data")
        self.assertEqual(stderr, "")

    @patch('subprocess.Popen')
    @patch('selectors.DefaultSelector')
    def test_run_with_limit_exceeds_size(self, mock_selector, mock_popen):
        # Setup mocks
        mock_process = MagicMock()
        mock_process.poll.return_value = None # Running
        mock_popen.return_value = mock_process

        mock_stdout = MagicMock()
        mock_stderr = MagicMock()
        mock_process.stdout = mock_stdout
        mock_process.stderr = mock_stderr

        mock_sel_instance = mock_selector.return_value

        key = MagicMock()
        key.fileobj = mock_stdout

        mock_sel_instance.select.return_value = [(key, selectors.EVENT_READ)]

        # Simulate read returning data larger than limit
        # Default limit is 10MB
        mock_stdout.read.return_value = "A" * (10 * 1024 * 1024 + 1)

        with self.assertRaises(ValueError) as cm:
            self.executor._run_with_limit(["cmd"])

        self.assertEqual(str(cm.exception), "Output exceeded limit")
        mock_process.kill.assert_called()

    # Tests for generate_automation_command (mocking execute_prompt)

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
