import json
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from src.file_manager.ai_integration import GeminiClient, ResponseValidator

class TestAIIntegration:
    @pytest.fixture
    def client(self):
        return GeminiClient()

    def test_mock_response_generation(self, client):
        # Test default mock response
        plan_data = client.generate_plan("organize files by type", Path.cwd())
        assert "plan" in plan_data
        assert len(plan_data["plan"]) > 0
        assert plan_data["plan"][0]["action"] == "organize_by_type"

    def test_validation_success(self):
        valid_json = """
        {
          "plan": [
            {
              "step": 1,
              "action": "organize_by_type",
              "params": {"source": ".", "target": "Organized"},
              "description": "Organize",
              "is_destructive": false
            }
          ]
        }
        """
        data = ResponseValidator.validate_plan(valid_json)
        assert data["plan"][0]["step"] == 1

    def test_validation_failure(self):
        invalid_json = """
        {
          "plan": [
            {
              "step": 1
            }
          ]
        }
        """
        # Invalid JSON (missing closing brace) or Schema mismatch
        with pytest.raises(ValueError):
             ResponseValidator.validate_plan("{ invalid json")

        # Schema mismatch
        # Note: jsonschema validation raises ValidationError which is caught and re-raised as ValueError in my code
        with pytest.raises(ValueError):
             ResponseValidator.validate_plan(invalid_json)

    @patch("src.file_manager.ai_integration.AIExecutor")
    def test_retry_logic(self, mock_executor_cls, client):
        # Setup mock executor
        mock_executor = mock_executor_cls.return_value
        client.executor = mock_executor
        mock_executor.is_available.return_value = True

        # First call returns invalid JSON
        # Second call (retry) returns valid JSON
        mock_executor.execute_prompt.side_effect = [
            "INVALID JSON",
            json.dumps({
                "plan": [{
                    "step": 1,
                    "action": "organize_by_type",
                    "params": {},
                    "description": "retry success",
                    "is_destructive": False
                }]
            })
        ]

        # Call generate_plan
        # It should try once, fail validation, call retry, succeed
        plan_data = client.generate_plan("test command", Path.cwd())

        assert plan_data["plan"][0]["description"] == "retry success"
        assert mock_executor.execute_prompt.call_count == 2
