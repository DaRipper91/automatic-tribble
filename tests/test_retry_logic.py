import json
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
from src.file_manager.ai_integration import GeminiClient, ResponseValidator

class TestAIRetryLogic:
    @pytest.fixture
    def client(self):
        return GeminiClient()

    @patch("src.file_manager.ai_integration.AIExecutor")
    def test_retry_success(self, mock_executor_cls, client):
        mock_executor = mock_executor_cls.return_value
        client.executor = mock_executor
        mock_executor.is_available.return_value = True

        # Sequence:
        # 1. Invalid JSON
        # 2. Valid JSON (Retry)
        mock_executor.execute_prompt.side_effect = [
            "INVALID JSON RESPONSE",
            json.dumps({
                "plan": [{
                    "step": 1,
                    "action": "organize_by_type",
                    "params": {"source": ".", "target": "dest"},
                    "description": "Retry success",
                    "is_destructive": False
                }]
            })
        ]

        result = client.generate_plan("organize files", Path.cwd())

        # Verify result
        assert result["plan"][0]["description"] == "Retry success"
        # Verify called twice
        assert mock_executor.execute_prompt.call_count == 2

        # Check if second call included feedback
        args, _ = mock_executor.execute_prompt.call_args_list[1]
        assert "Your previous response failed validation" in args[0]

    @patch("src.file_manager.ai_integration.AIExecutor")
    def test_max_retries_exceeded(self, mock_executor_cls, client):
        mock_executor = mock_executor_cls.return_value
        client.executor = mock_executor
        mock_executor.is_available.return_value = True

        # Always invalid
        mock_executor.execute_prompt.return_value = "INVALID"

        with pytest.raises(ValueError, match="Invalid plan format"):
            client.generate_plan("organize files", Path.cwd())

        # 1 initial + 3 retries = 4 calls
        assert mock_executor.execute_prompt.call_count == 4
