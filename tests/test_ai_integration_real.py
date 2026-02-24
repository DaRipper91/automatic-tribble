"""
Integration tests for the real AI integration (with mocked AIExecutor).
"""

import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.file_manager.ai_integration import GeminiClient
from src.file_manager.ai_utils import AIExecutor

@pytest.fixture
def mock_executor():
    with patch("src.file_manager.ai_integration.AIExecutor") as mock:
        yield mock.return_value

def test_process_command_structure(mock_executor):
    # Mock AI response
    plan_json = {
        "plan": [
            {
                "action": "organize_by_type",
                "source": "/test/dir",
                "target": "/test/organized",
                "params": {"dry_run": True},
                "description": "Organize by type",
                "is_destructive": False
            }
        ],
        "summary": "Test Summary",
        "confidence": 0.95
    }

    mock_executor.is_available.return_value = True
    mock_executor.execute_prompt.return_value = json.dumps(plan_json)

    client = GeminiClient()
    result = client.process_command("organize files", Path("/test/dir"))

    assert result["plan"][0]["action"] == "organize_by_type"
    assert result["summary"] == "Test Summary"
    assert client.executor.execute_prompt.called

def test_validation_retry_logic(mock_executor):
    # First response invalid, second valid
    invalid_response = "I will organize your files."
    valid_response = json.dumps({
        "plan": [],
        "summary": "Empty plan",
        "confidence": 1.0
    })

    mock_executor.is_available.return_value = True
    mock_executor.execute_prompt.side_effect = [invalid_response, valid_response]

    client = GeminiClient()
    result = client.process_command("do nothing", Path("/test/dir"))

    assert result["summary"] == "Empty plan"
    assert mock_executor.execute_prompt.call_count == 2
