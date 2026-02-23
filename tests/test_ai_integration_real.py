"""
Tests for the real AI integration logic (mocking the external API).
"""

import pytest
import json
from unittest.mock import MagicMock, patch
from pathlib import Path
from src.file_manager.ai_integration import GeminiClient, ResponseValidator, PLAN_SCHEMA

# Mock data
VALID_JSON_RESPONSE = """
```json
{
  "plan": [
    {
      "action": "organize_by_type",
      "params": {
        "source_dir": "/tmp/test",
        "target_dir": "/tmp/organized",
        "move": true
      },
      "description": "Organize files by type",
      "is_destructive": true
    }
  ]
}
```
"""

INVALID_JSON_RESPONSE = "This is not JSON."

MALFORMED_SCHEMA_RESPONSE = """
{
  "plan": [
    {
      "action": "organize_by_type",
      "description": "Missing params"
    }
  ]
}
"""

@pytest.fixture
def mock_executor():
    with patch("src.file_manager.ai_integration.AIExecutor") as mock:
        executor_instance = mock.return_value
        executor_instance.execute_prompt.return_value = VALID_JSON_RESPONSE
        yield executor_instance

@pytest.fixture
def mock_context_builder():
    with patch("src.file_manager.ai_integration.DirectoryContextBuilder") as mock:
        builder_instance = mock.return_value
        builder_instance.get_context.return_value = {
            "path": "/tmp/test",
            "file_count": 10,
            "total_size_bytes": 1024,
            "categories": {"txt": 5, "jpg": 5},
            "oldest_file": "/tmp/test/old.txt",
            "oldest_file_date": "2023-01-01",
            "newest_file": "/tmp/test/new.txt",
            "newest_file_date": "2023-01-02",
            "largest_files": [],
            "os": "posix",
            "scan_time": "2023-01-01T00:00:00"
        }
        yield builder_instance

def test_response_validator_valid():
    validator = ResponseValidator()
    data = validator.validate_plan(VALID_JSON_RESPONSE)
    assert "plan" in data
    assert len(data["plan"]) == 1
    assert data["plan"][0]["action"] == "organize_by_type"

def test_response_validator_invalid_json():
    validator = ResponseValidator()
    with pytest.raises(ValueError, match="Invalid JSON"):
        validator.validate_plan(INVALID_JSON_RESPONSE)

def test_response_validator_invalid_schema():
    validator = ResponseValidator()
    with pytest.raises(ValueError, match="Schema validation failed"):
        validator.validate_plan(MALFORMED_SCHEMA_RESPONSE)

def test_gemini_client_get_plan_success(mock_executor, mock_context_builder):
    client = GeminiClient()
    plan = client.get_plan("organize my files")

    assert plan["plan"][0]["action"] == "organize_by_type"
    mock_executor.execute_prompt.assert_called_once()
    # Verify prompt contains context
    args, _ = mock_executor.execute_prompt.call_args
    prompt = args[0]
    # Check for backticks as used in the template
    assert "Total Files: `10`" in prompt

def test_gemini_client_get_plan_retry(mock_executor, mock_context_builder):
    # First 2 calls fail, 3rd succeeds
    mock_executor.execute_prompt.side_effect = [INVALID_JSON_RESPONSE, MALFORMED_SCHEMA_RESPONSE, VALID_JSON_RESPONSE]

    client = GeminiClient()
    plan = client.get_plan("organize my files")

    assert plan["plan"][0]["action"] == "organize_by_type"
    assert mock_executor.execute_prompt.call_count == 3

def test_gemini_client_get_plan_failure(mock_executor, mock_context_builder):
    # All calls fail
    mock_executor.execute_prompt.return_value = INVALID_JSON_RESPONSE

    client = GeminiClient()
    plan = client.get_plan("organize my files")

    assert plan["plan"][0]["action"] == "error"
    assert "Failed to generate a valid plan" in plan["plan"][0]["description"]
    assert mock_executor.execute_prompt.call_count == 3
