"""
Gemini Integration for File Manager AI.
Handles communication with the Gemini AI model, including prompt engineering,
context injection, and response validation.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import jsonschema
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .automation import FileOrganizer
from .ai_utils import AIExecutor
from .context import DirectoryContextBuilder
from .tags import TagManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# JSON Schema for validation
PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "plan": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "params": {"type": "object"},
                    "description": {"type": "string"},
                    "is_destructive": {"type": "boolean"}
                },
                "required": ["action", "params", "description"]
            }
        }
    },
    "required": ["plan"]
}

class ResponseValidator:
    """Validates AI responses against a schema."""

    @staticmethod
    def validate_plan(response_text: str) -> Dict[str, Any]:
        """
        Validate and parse the JSON response from Gemini.

        Args:
            response_text: The raw string response from the AI.

        Returns:
            The parsed JSON object if valid.

        Raises:
            ValueError: If parsing fails or schema validation fails.
        """
        try:
            # clean potential markdown code blocks
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        try:
            jsonschema.validate(instance=data, schema=PLAN_SCHEMA)
        except jsonschema.ValidationError as e:
            raise ValueError(f"Schema validation failed: {e.message}")

        return data

class GeminiClient:
    """Client for Gemini AI integration."""

    def __init__(self):
        self.organizer = FileOrganizer()
        self.tag_manager = TagManager()
        self.executor = AIExecutor()
        self.prompts_dir = Path(__file__).parent / "prompts"
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.prompts_dir),
            autoescape=select_autoescape()
        )
        self.validator = ResponseValidator()

    def get_plan(self, command: str, current_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Generate a multi-step execution plan for the given command.

        Args:
            command: The user's natural language command.
            current_dir: The context directory.

        Returns:
            A dictionary containing the 'plan' list.
        """
        if current_dir is None:
            current_dir = Path.cwd()

        # Build context
        context_builder = DirectoryContextBuilder(current_dir)
        context = context_builder.get_context()

        # Render prompt
        try:
            template = self.jinja_env.get_template("plan_generation.jinja2")
            prompt = template.render(user_request=command, context=context)
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            return self._create_error_plan(f"Internal Error: Could not generate prompt. {e}")

        # Send to Gemini with retries
        max_retries = 3
        last_error = ""

        for attempt in range(max_retries):
            response_text = self.executor.execute_prompt(prompt)

            # Check for executor errors (string starting with "Error")
            if response_text.startswith("Error"):
                return self._create_error_plan(response_text)

            try:
                plan = self.validator.validate_plan(response_text)
                return plan
            except ValueError as e:
                last_error = str(e)
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                # Add feedback to prompt for next retry
                prompt += f"\n\nERROR: The previous response was invalid JSON or did not match the schema: {e}\nPlease correct it and return ONLY valid JSON."

        return self._create_error_plan(f"Failed to generate a valid plan after {max_retries} attempts. Error: {last_error}")

    def _create_error_plan(self, message: str) -> Dict[str, Any]:
        """Helper to return an error plan."""
        return {
            "plan": [
                {
                    "action": "error",
                    "params": {},
                    "description": message,
                    "is_destructive": False
                }
            ]
        }

    def execute_step(self, step: Dict[str, Any]) -> str:
        """
        Execute a single step of the plan.

        Args:
            step: A dictionary representing one operation from the plan.

        Returns:
            Success or error message.
        """
        action = step.get("action")
        params = step.get("params", {})

        if action == "error":
            return f"Error: {step.get('description')}"

        try:
            if action == "organize_by_type":
                source = Path(params["source_dir"])
                target = Path(params["target_dir"])
                move = params.get("move", True)
                result = self.organizer.organize_by_type(source, target, move=move)
                count = sum(len(files) for files in result.values())
                return f"Organized {count} files by type into {target}."

            elif action == "organize_by_date":
                source = Path(params["source_dir"])
                target = Path(params["target_dir"])
                move = params.get("move", True)
                result = self.organizer.organize_by_date(source, target, move=move)
                count = sum(len(files) for files in result.values())
                return f"Organized {count} files by date into {target}."

            elif action == "cleanup_old_files":
                directory = Path(params["directory"])
                days = int(params["days_old"])
                recursive = params.get("recursive", False)
                # Ensure dry_run is respected if passed, though usually UI controls it
                dry_run = params.get("dry_run", False)

                deleted = self.organizer.cleanup_old_files(directory, days, recursive, dry_run)
                action_str = "Would delete" if dry_run else "Deleted"
                return f"{action_str} {len(deleted)} files older than {days} days."

            elif action == "find_duplicates":
                directory = Path(params["directory"])
                recursive = params.get("recursive", False)
                duplicates = self.organizer.find_duplicates(directory, recursive)
                count = sum(len(files) for files in duplicates.values())
                return f"Found {len(duplicates)} groups of duplicates ({count} files total)."

            elif action == "batch_rename":
                directory = Path(params["directory"])
                pattern = params["pattern"]
                replacement = params["replacement"]
                recursive = params.get("recursive", False)
                renamed = self.organizer.batch_rename(directory, pattern, replacement, recursive)
                return f"Renamed {len(renamed)} files matching '{pattern}'."

            elif action == "search_by_tag":
                # Placeholder until Searcher is integrated
                return f"Searching by tag '{params.get('tag')}' (Feature coming soon)."

            elif action == "search_by_name":
                 # Placeholder
                 return f"Searching by name '{params.get('pattern')}' (Feature coming soon)."

            elif action == "add_tag":
                file_path = Path(params["file_path"])
                tag = params["tag"]
                if file_path.exists():
                    if self.tag_manager.add_tag(file_path, tag):
                        return f"Tagged '{file_path.name}' with '#{tag}'."
                    else:
                        return f"Failed to tag '{file_path.name}'."
                else:
                    return f"File not found: {file_path}"

            else:
                return f"Unknown action: {action}"

        except Exception as e:
            return f"Error executing {action}: {str(e)}"

    def search_history(self, query: str, history: List[str]) -> List[str]:
        """
        Perform semantic search on command history using Gemini.
        """
        if not history:
            return []

        prompt = (
            f"You are a semantic search engine. User query: '{query}'.\n"
            "History items:\n" + "\n".join([f"- {h}" for h in history]) + "\n\n"
            "Return a JSON list of history items that match the intent of the query. "
            "If none match, return empty list. JSON format only: [\"match1\", ...]"
        )

        try:
            response = self.executor.execute_prompt(prompt)
            if response.startswith("Error"):
                return []

            # Simple parsing
            clean_text = response.replace("```json", "").replace("```", "").strip()
            matches = json.loads(clean_text)
            if isinstance(matches, list):
                return [str(m) for m in matches]
            return []
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    # Legacy support (deprecated)
    def process_command(self, command: str, current_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Deprecated: Use get_plan instead."""
        plan_data = self.get_plan(command, current_dir)
        if plan_data["plan"]:
            first_step = plan_data["plan"][0]
            return {
                "action": first_step["action"],
                "params": first_step["params"],
                "description": first_step["description"]
            }
        return {
            "action": "unknown",
            "params": {},
            "description": "No plan generated."
        }

    # Legacy support (deprecated)
    def execute_command(self, action_data: Dict[str, Any]) -> str:
        """Deprecated: Use execute_step instead."""
        return self.execute_step(action_data)
