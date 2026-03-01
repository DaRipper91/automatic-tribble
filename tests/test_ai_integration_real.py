import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path
from src.file_manager.ai_integration import GeminiClient
from src.file_manager.ai_schema import PLAN_SCHEMA

class MockExecutor:
    def is_available(self):
        return True
    def execute_prompt(self, prompt):
        return "{}"

@pytest.fixture
def gemini_client():
    client = GeminiClient()
    # Mock AIExecutor
    client.executor = MagicMock()
    client.executor.is_available.return_value = True

    # Mock context builder to avoid actual scanning
    client.context_builder = MagicMock()
    client.context_builder.get_context.return_value = {}

    # Mock organizer methods
    client.organizer = MagicMock()
    client.organizer.organize_by_type = AsyncMock()
    client.organizer.organize_by_date = AsyncMock()
    client.organizer.cleanup_old_files = AsyncMock()
    client.organizer.find_duplicates = AsyncMock()
    client.organizer.batch_rename = AsyncMock()

    # Mock tag manager
    client.tag_manager = MagicMock()
    client.tag_manager.add_tag = MagicMock()
    client.tag_manager.remove_tag = MagicMock()

    return client

def test_generate_plan_mock(gemini_client, tmp_path):
    # Mock response
    mock_response = """
    {
      "plan": [
        {
          "step": 1,
          "action": "organize_by_type",
          "params": {"source": "/tmp", "target": "/tmp/organized"},
          "description": "Sort files by type",
          "is_destructive": false
        }
      ]
    }
    """
    gemini_client.executor.execute_prompt.return_value = mock_response

    plan = gemini_client.generate_plan("Organize /tmp", tmp_path)

    assert "plan" in plan
    assert len(plan["plan"]) == 1
    step = plan["plan"][0]
    assert step["action"] == "organize_by_type"
    assert step["is_destructive"] is False

def test_generate_plan_retry(gemini_client, tmp_path):
    # First response invalid, second response valid (retry logic)
    gemini_client.executor.execute_prompt.side_effect = [
        "Not valid JSON",
        """
        {
          "plan": []
        }
        """
    ]

    plan = gemini_client.generate_plan("Bad request", tmp_path)
    # Should retry and get empty plan
    assert "plan" in plan
    assert len(plan["plan"]) == 0
    assert gemini_client.executor.execute_prompt.call_count == 2

@pytest.mark.asyncio
async def test_execute_plan_step(gemini_client):
    step = {
        "step": 1,
        "action": "organize_by_type",
        "params": {"source": "/tmp", "target": "/tmp/out", "move": False},
        "description": "Test step",
        "is_destructive": False
    }

    # Mock return value
    gemini_client.organizer.organize_by_type.return_value = {"jpg": ["file1.jpg"]}

    # Dry Run
    msg = await gemini_client.execute_plan_step(step, dry_run=True)
    assert "Would organize" in msg
    gemini_client.organizer.organize_by_type.assert_called_with(Path("/tmp"), Path("/tmp/out"), move=False, dry_run=True)

    # Real Run
    msg = await gemini_client.execute_plan_step(step, dry_run=False)
    assert "Organized" in msg
    gemini_client.organizer.organize_by_type.assert_called_with(Path("/tmp"), Path("/tmp/out"), move=False, dry_run=False)
