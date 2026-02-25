import unittest
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path
from src.file_manager.ai_integration import GeminiClient

class TestGeminiClient(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Patch the FileOrganizer class where it's used
        self.patcher = patch('src.file_manager.ai_integration.FileOrganizer')
        self.MockFileOrganizer = self.patcher.start()

        # Patch AIExecutor to avoid real calls or missing binary
        self.patcher_exec = patch('src.file_manager.ai_integration.AIExecutor')
        self.MockAIExecutor = self.patcher_exec.start()

        self.client = GeminiClient()
        self.mock_organizer = self.client.organizer
        self.client.executor.is_available.return_value = False # Use mock response by default

        # Configure AsyncMocks for async methods
        self.mock_organizer.organize_by_type = AsyncMock(return_value={})
        self.mock_organizer.organize_by_date = AsyncMock(return_value={})
        self.mock_organizer.cleanup_old_files = AsyncMock(return_value=[])
        self.mock_organizer.find_duplicates = AsyncMock(return_value={})
        self.mock_organizer.batch_rename = AsyncMock(return_value=[])

    async def asyncTearDown(self):
        self.patcher.stop()
        self.patcher_exec.stop()

    def test_process_organize_by_type(self):
        command = "organize files"
        current_dir = Path("/tmp/test")
        result = self.client.process_command(command, current_dir)

        # New API returns plan_ready
        self.assertEqual(result["action"], "plan_ready")
        self.assertTrue(len(result["plan"]) > 0)
        self.assertEqual(result["plan"][0]["action"], "organize_by_type")

    async def test_execute_plan_step(self):
        step = {
            "step": 1,
            "action": "organize_by_type",
            "params": {
                "source": "/tmp/src",
                "target": "/tmp/dst",
                "move": True
            },
            "description": "desc",
            "is_destructive": False
        }

        self.mock_organizer.organize_by_type.return_value = {'pdf': [Path('a.pdf')]}

        result = await self.client.execute_plan_step(step, dry_run=False)

        # Check call arguments. Note: organize_by_type now takes dry_run
        self.mock_organizer.organize_by_type.assert_awaited_with(
            Path("/tmp/src"), Path("/tmp/dst"), move=True, dry_run=False
        )
        self.assertIn("Organized 1 files", result)

    def test_suggest_tags(self):
        files = [{"name": "test.txt", "size_human": "10 KB"}]
        result = self.client.suggest_tags(files)
        self.assertIn("suggestions", result)

    def test_search_history(self):
        history = [{"command": "organize", "timestamp": 123}]
        result = self.client.search_history("org", history)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["command"], "organize")

if __name__ == '__main__':
    unittest.main()
