"""
AI Response Validation and Retry Logic.
"""

import json
import re
from typing import Dict, Any, Optional, Tuple
from jsonschema import validate, ValidationError
from .logger import get_logger

logger = get_logger("ai_validation")

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "plan": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "source": {"type": "string"},
                    "target": {"type": ["string", "null"]},
                    "params": {"type": "object"},
                    "description": {"type": "string"},
                    "is_destructive": {"type": "boolean"}
                },
                "required": ["action", "source", "description"]
            }
        },
        "summary": {"type": "string"},
        "confidence": {"type": "number"}
    },
    "required": ["plan"]
}

TAGGING_SCHEMA = {
    "type": "object",
    "properties": {
        "suggested_tags": {
            "type": "array",
            "items": {"type": "string"}
        },
        "confidence": {"type": "number"}
    },
    "required": ["suggested_tags"]
}

class ResponseValidator:
    """Validates AI responses against expected schemas."""

    def validate_plan(self, response_text: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Validate a planning response.
        Returns (parsed_json, error_message).
        """
        return self._validate(response_text, PLAN_SCHEMA)

    def validate_tagging(self, response_text: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Validate a tagging response.
        Returns (parsed_json, error_message).
        """
        return self._validate(response_text, TAGGING_SCHEMA)

    def _validate(self, response_text: str, schema: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Internal validation logic.
        """
        try:
            # 1. Extract JSON from markdown if present
            json_str = self._extract_json(response_text)

            # 2. Parse JSON
            data = json.loads(json_str)

            # 3. Validate Schema
            validate(instance=data, schema=schema)

            return data, None

        except json.JSONDecodeError as e:
            logger.error(f"JSON Decode Error: {e}")
            return None, f"Invalid JSON format: {e}"
        except ValidationError as e:
            logger.error(f"Schema Validation Error: {e}")
            return None, f"Schema validation failed: {e.message}"
        except Exception as e:
            logger.error(f"Unexpected Validation Error: {e}")
            return None, str(e)

    def _extract_json(self, text: str) -> str:
        """
        Extract JSON content from a string that might contain markdown blocks.
        """
        text = text.strip()

        # Check for ```json block
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            return match.group(1)

        # If no block, assume the whole text is JSON (or try to parse it)
        return text
