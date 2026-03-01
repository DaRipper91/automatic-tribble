"""
JSON Schemas for AI Integration.
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
                    "params": {"type": "object"},
                    "description": {"type": "string"},
                    "is_destructive": {"type": "boolean"}
                },
                "required": ["step", "action", "params", "description", "is_destructive"]
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
