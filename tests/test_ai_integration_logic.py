import json
import pytest
from unittest.mock import patch
from pathlib import Path
from src.file_manager.ai_integration import GeminiClient, ResponseValidator

class TestAIIntegration:
    @pytest.fixture
    def client(self):
        return GeminiClient()

    @patch("src.file_manager.ai_integration.AIExecutor")
    def test_mock_response_generation(self, mock_executor_cls, client):
        # Test default mock response (simulate Gemini unavailable to force mock path)
        mock_executor_cls.return_value.is_available.return_value = False
        client.executor = mock_executor_cls.return_value
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

    def test_validate_search_success(self):
        valid_json = '{"indices": [0, 2, 5]}'
        data = ResponseValidator.validate_search(valid_json)
        assert data["indices"] == [0, 2, 5]

    def test_validate_search_markdown(self):
        markdown_json = "```json\n{\"indices\": [1]}\n```"
        data = ResponseValidator.validate_search(markdown_json)
        assert data["indices"] == [1]

    def test_validate_search_failure(self):
        # Invalid syntax
        with pytest.raises(ValueError, match="Invalid search format"):
            ResponseValidator.validate_search("{ invalid")

        # Missing required field
        with pytest.raises(ValueError, match="Invalid search format"):
            ResponseValidator.validate_search('{"wrong": []}')

        # Wrong type
        with pytest.raises(ValueError, match="Invalid search format"):
            ResponseValidator.validate_search('{"indices": ["not-an-int"]}')

    def test_validate_tags_success(self):
        valid_json = """
        {
          "suggestions": [
            {"file": "test.txt", "tags": ["work", "important"]}
          ]
        }
        """
        data = ResponseValidator.validate_tags(valid_json)
        assert data["suggestions"][0]["file"] == "test.txt"
        assert "work" in data["suggestions"][0]["tags"]

    def test_validate_tags_failure(self):
        # Invalid syntax
        with pytest.raises(ValueError, match="Invalid tags format"):
            ResponseValidator.validate_tags("not json")

        # Missing suggestions
        with pytest.raises(ValueError, match="Invalid tags format"):
            ResponseValidator.validate_tags('{"wrong": []}')

        # Missing required field in suggestion
        invalid_item = '{"suggestions": [{"file": "only-file"}]}'
        with pytest.raises(ValueError, match="Invalid tags format"):
            ResponseValidator.validate_tags(invalid_item)

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
