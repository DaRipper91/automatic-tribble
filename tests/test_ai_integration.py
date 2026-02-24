import unittest
from unittest.mock import patch, AsyncMock
from pathlib import Path
from src.file_manager.ai_integration import GeminiClient

class TestGeminiClient(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Patch the FileOrganizer class where it's used
        self.patcher = patch('src.file_manager.ai_integration.FileOrganizer')
        self.MockFileOrganizer = self.patcher.start()
        self.client = GeminiClient()
        self.mock_organizer = self.client.organizer

        # Configure AsyncMocks for async methods
        self.mock_organizer.organize_by_type = AsyncMock()
        self.mock_organizer.organize_by_date = AsyncMock()
        self.mock_organizer.cleanup_old_files = AsyncMock()
        self.mock_organizer.find_duplicates = AsyncMock()
        self.mock_organizer.batch_rename = AsyncMock()

    async def asyncTearDown(self):
        self.patcher.stop()

    def test_process_organize_by_type(self):
        command = "organize files"
        current_dir = Path("/tmp/test")
        result = self.client.process_command(command, current_dir)

        self.assertEqual(result["action"], "organize_by_type")
        self.assertEqual(result["params"]["source_dir"], str(current_dir))
        self.assertEqual(result["params"]["target_dir"], str(current_dir / "Organized_Type"))
        self.assertTrue(result["params"]["move"])

    def test_process_cleanup(self):
        command = "clean up"
        current_dir = Path("/tmp/test")
        result = self.client.process_command(command, current_dir)

        self.assertEqual(result["action"], "cleanup_old_files")
        self.assertEqual(result["params"]["directory"], str(current_dir))
        self.assertEqual(result["params"]["days_old"], 30)

    async def test_execute_organize_by_type(self):
        action_data = {
            "action": "organize_by_type",
            "params": {
                "source_dir": "/tmp/src",
                "target_dir": "/tmp/dst",
                "move": True
            }
        }
        self.mock_organizer.organize_by_type.return_value = {'pdf': [Path('a.pdf'), Path('b.pdf')]}

        result = await self.client.execute_command(action_data)

        self.mock_organizer.organize_by_type.assert_awaited_with(
            Path("/tmp/src"), Path("/tmp/dst"), move=True
        )
        self.assertIn("Successfully organized 2 files", result)

    async def test_execute_cleanup(self):
        action_data = {
            "action": "cleanup_old_files",
            "params": {
                "directory": "/tmp/dir",
                "days_old": 60,
                "recursive": True,
                "dry_run": False
            }
        }
        self.mock_organizer.cleanup_old_files.return_value = [Path('file1'), Path('file2')]

        result = await self.client.execute_command(action_data)

        self.mock_organizer.cleanup_old_files.assert_awaited_with(
            Path("/tmp/dir"), 60, True, False
        )
        self.assertIn("Deleted 2 files older than 60 days", result)

    async def test_execute_unknown(self):
        action_data = {"action": "unknown_action"}
        result = await self.client.execute_command(action_data)
        self.assertEqual(result, "Unknown action or command not understood.")

    async def test_execute_exception(self):
        action_data = {
            "action": "organize_by_type",
            "params": {
                "source_dir": "/tmp/src",
                "target_dir": "/tmp/dst"
            }
        }
        self.mock_organizer.organize_by_type.side_effect = Exception("Test Error")

        result = await self.client.execute_command(action_data)

        self.assertIn("Error executing command: Test Error", result)

if __name__ == '__main__':
    unittest.main()
