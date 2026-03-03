"""
JSON Schemas for AI Responses.
"""

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "plan": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "step": {"type": "integer"},
                    "action": {"type": "string"},
                    "source": {"type": "string"},
                    "target": {"type": "string"},
                    "directory": {"type": "string"},
                    "file": {"type": "string"},
                    "tag": {"type": "string"},
                    "pattern": {"type": "string"},
                    "replacement": {"type": "string"},
                    "move": {"type": "boolean"},
                    "recursive": {"type": "boolean"},
                    "days": {"type": "integer"},
                    "dry_run": {"type": "boolean"},
                    "description": {"type": "string"},
                    "is_destructive": {"type": "boolean"}
                },
                "required": ["step", "action", "description"]
            }
        }
    },
    "required": ["plan"]
}

TAGS_SCHEMA = {
    "type": "object",
    "properties": {
        "suggestions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "file": {"type": "string"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["file", "tags"]
            }
        }
    },
    "required": ["suggestions"]
}

SEMANTIC_SEARCH_SCHEMA = {
    "type": "object",
    "properties": {
        "indices": {
            "type": "array",
            "items": {"type": "integer"}
        }
    },
    "required": ["indices"]
}
