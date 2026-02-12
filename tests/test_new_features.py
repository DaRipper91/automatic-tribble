import sys
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path.cwd() / "src"))

from file_manager.app import FileManagerApp
from file_manager.screens import AIConfigScreen, LauncherScreen, UserModeConfigScreen
from file_manager.ai_utils import AIExecutor

class TestNewFeatures(unittest.TestCase):

    def test_ai_executor_availability(self):
        with patch("file_manager.ai_utils.find_gemini_executable", return_value="/bin/gemini"):
            executor = AIExecutor()
            self.assertTrue(executor.is_available())

        with patch("file_manager.ai_utils.find_gemini_executable", return_value=None):
            executor = AIExecutor()
            self.assertFalse(executor.is_available())

    def test_app_initialization(self):
        app = FileManagerApp()
        self.assertEqual(app.layout_mode, "dual")
        self.assertIsNone(app.gemini_path)

    @patch("file_manager.ai_utils.subprocess.run")
    def test_ai_command_generation(self, mock_run):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "tfm-auto organize"

        with patch("file_manager.ai_utils.find_gemini_executable", return_value="/bin/gemini"):
            executor = AIExecutor()
            cmd, status = executor.generate_automation_command("test")
            self.assertEqual(cmd, "tfm-auto organize")

if __name__ == "__main__":
    unittest.main()
