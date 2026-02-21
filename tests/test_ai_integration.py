import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.file_manager.ai_integration import GeminiClient

class TestGeminiClient(unittest.TestCase):
    def setUp(self):
        # Patch the FileOrganizer class where it's used
        self.patcher = patch('src.file_manager.ai_integration.FileOrganizer')
        self.MockFileOrganizer = self.patcher.start()
        self.client = GeminiClient()
        self.mock_organizer = self.client.organizer

    def tearDown(self):
        self.patcher.stop()

    def test_process_organize_by_type(self):
        command = "organize files"
        current_dir = Path("/tmp/test")
        result = self.client.process_command(command, current_dir)

        self.assertEqual(result["action"], "organize_by_type")
        self.assertEqual(result["params"]["source_dir"], str(current_dir))
        self.assertEqual(result["params"]["target_dir"], str(current_dir / "Organized_Type"))
        self.assertTrue(result["params"]["move"])

    def test_process_organize_by_date(self):
        command = "sort by date"
        current_dir = Path("/tmp/test")
        result = self.client.process_command(command, current_dir)

        self.assertEqual(result["action"], "organize_by_date")
        self.assertEqual(result["params"]["source_dir"], str(current_dir))
        self.assertEqual(result["params"]["target_dir"], str(current_dir / "Organized_Date"))
        self.assertTrue(result["params"]["move"])

    def test_process_cleanup(self):
        command = "clean up"
        current_dir = Path("/tmp/test")
        result = self.client.process_command(command, current_dir)

        self.assertEqual(result["action"], "cleanup_old_files")
        self.assertEqual(result["params"]["directory"], str(current_dir))
        self.assertEqual(result["params"]["days_old"], 30) # Default
        self.assertFalse(result["params"]["recursive"])
        self.assertFalse(result["params"]["dry_run"])

    def test_process_cleanup_with_days(self):
        command = "delete files older than 10 days"
        current_dir = Path("/tmp/test")
        result = self.client.process_command(command, current_dir)

        self.assertEqual(result["action"], "cleanup_old_files")
        self.assertEqual(result["params"]["days_old"], 10)

    def test_process_find_duplicates(self):
        command = "find duplicates"
        current_dir = Path("/tmp/test")
        result = self.client.process_command(command, current_dir)

        self.assertEqual(result["action"], "find_duplicates")
        self.assertEqual(result["params"]["directory"], str(current_dir))
        self.assertFalse(result["params"]["recursive"])

    def test_process_batch_rename(self):
        command = "rename foo to bar"
        current_dir = Path("/tmp/test")
        result = self.client.process_command(command, current_dir)

        self.assertEqual(result["action"], "batch_rename")
        self.assertEqual(result["params"]["directory"], str(current_dir))
        self.assertEqual(result["params"]["pattern"], "foo")
        self.assertEqual(result["params"]["replacement"], "bar")

    def test_process_unknown(self):
        command = "hello world"
        result = self.client.process_command(command)

        self.assertEqual(result["action"], "unknown")
        self.assertEqual(result["description"], "Could not understand the command.")

    def test_process_command_context(self):
        # Without explicit current_dir
        with patch('pathlib.Path.cwd', return_value=Path("/cwd")):
            result = self.client.process_command("organize")
            self.assertEqual(result["params"]["source_dir"], "/cwd")

    def test_execute_organize_by_type(self):
        action_data = {
            "action": "organize_by_type",
            "params": {
                "source_dir": "/tmp/src",
                "target_dir": "/tmp/dst",
                "move": True
            }
        }
        # Mock return value: dict of list of files
        self.mock_organizer.organize_by_type.return_value = {'pdf': ['a.pdf', 'b.pdf']}

        result = self.client.execute_command(action_data)

        self.mock_organizer.organize_by_type.assert_called_with(
            Path("/tmp/src"), Path("/tmp/dst"), move=True
        )
        self.assertIn("Successfully organized 2 files by type", result)

    def test_execute_organize_by_date(self):
        action_data = {
            "action": "organize_by_date",
            "params": {
                "source_dir": "/tmp/src",
                "target_dir": "/tmp/dst",
                "move": True
            }
        }
        self.mock_organizer.organize_by_date.return_value = {'2023': ['a.txt']}

        result = self.client.execute_command(action_data)

        self.mock_organizer.organize_by_date.assert_called_with(
            Path("/tmp/src"), Path("/tmp/dst"), move=True
        )
        self.assertIn("Successfully organized 1 files by date", result)

    def test_execute_cleanup(self):
        action_data = {
            "action": "cleanup_old_files",
            "params": {
                "directory": "/tmp/dir",
                "days_old": 60,
                "recursive": True,
                "dry_run": False
            }
        }
        self.mock_organizer.cleanup_old_files.return_value = ['file1', 'file2']

        result = self.client.execute_command(action_data)

        self.mock_organizer.cleanup_old_files.assert_called_with(
            Path("/tmp/dir"), 60, True, False
        )
        self.assertIn("Deleted 2 files older than 60 days", result)

    def test_execute_find_duplicates(self):
        action_data = {
            "action": "find_duplicates",
            "params": {
                "directory": "/tmp/dir",
                "recursive": True
            }
        }
        self.mock_organizer.find_duplicates.return_value = {'hash1': ['f1', 'f2']}

        result = self.client.execute_command(action_data)

        self.mock_organizer.find_duplicates.assert_called_with(
            Path("/tmp/dir"), True
        )
        self.assertIn("Found 1 groups of duplicates (2 files total)", result)

    def test_execute_batch_rename(self):
        action_data = {
            "action": "batch_rename",
            "params": {
                "directory": "/tmp/dir",
                "pattern": "foo",
                "replacement": "bar",
                "recursive": False
            }
        }
        self.mock_organizer.batch_rename.return_value = ['f1']

        result = self.client.execute_command(action_data)

        self.mock_organizer.batch_rename.assert_called_with(
            Path("/tmp/dir"), "foo", "bar", False
        )
        self.assertIn("Renamed 1 files matching 'foo'", result)

    def test_execute_unknown(self):
        action_data = {"action": "unknown_action"}
        result = self.client.execute_command(action_data)
        self.assertEqual(result, "Unknown action or command not understood.")

    def test_execute_exception(self):
        action_data = {
            "action": "organize_by_type",
            "params": {
                "source_dir": "/tmp/src",
                "target_dir": "/tmp/dst"
            }
        }
        self.mock_organizer.organize_by_type.side_effect = Exception("Test Error")

        result = self.client.execute_command(action_data)

        self.assertIn("Error executing command: Test Error", result)

if __name__ == '__main__':
    unittest.main()
