"""
AI Integration for File Manager
"""

import json
import platform
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from jsonschema import validate, ValidationError
from jinja2 import Environment, FileSystemLoader

from .automation import FileOrganizer
from .context import DirectoryContextBuilder
from .ai_utils import AIExecutor
from .tags import TagManager

logger = logging.getLogger(__name__)

class ResponseValidator:
    """Validates AI responses against JSON schemas."""

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
                    "required": ["step", "action", "params", "description"]
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

    @staticmethod
    def validate_plan(response_text: str) -> Dict[str, Any]:
        """Validate and parse a planning response."""
        try:
            # clean markdown code blocks
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            # Find the first { and last }
            start = clean_text.find("{")
            end = clean_text.rfind("}")
            if start != -1 and end != -1:
                clean_text = clean_text[start:end+1]

            data = json.loads(clean_text)
            validate(instance=data, schema=ResponseValidator.PLAN_SCHEMA)
            return data
        except (json.JSONDecodeError, ValidationError) as e:
            raise ValueError(f"Invalid plan format: {str(e)}")

    @staticmethod
    def validate_tags(response_text: str) -> Dict[str, Any]:
        """Validate and parse a tagging response."""
        try:
             # clean markdown code blocks
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            # Find the first { and last }
            start = clean_text.find("{")
            end = clean_text.rfind("}")
            if start != -1 and end != -1:
                clean_text = clean_text[start:end+1]

            data = json.loads(clean_text)
            validate(instance=data, schema=ResponseValidator.TAGS_SCHEMA)
            return data
        except (json.JSONDecodeError, ValidationError) as e:
            raise ValueError(f"Invalid tags format: {str(e)}")

class GeminiClient:
    """Client for Gemini AI integration."""

    def __init__(self):
        self.organizer = FileOrganizer()
        self.executor = AIExecutor()
        self.context_builder = DirectoryContextBuilder()
        self.tag_manager = TagManager()

        # Load Jinja2 templates
        try:
            self.prompt_env = Environment(
                loader=FileSystemLoader(str(Path(__file__).parent / "prompts"))
            )
        except Exception:
            # Fallback if prompts dir is missing or path issue
            logger.error("Failed to load prompt templates. AI features may be limited.")
            self.prompt_env = None

    def generate_plan(self, user_command: str, current_dir: Path) -> Dict[str, Any]:
        """
        Generate a multi-step plan from a user command.
        """
        if not self.prompt_env:
            return json.loads(self._mock_response(user_command, current_dir))

        # Get context
        context = self.context_builder.get_context(current_dir)

        # Prepare template
        try:
            template = self.prompt_env.get_template("planning.jinja2")
            prompt = template.render(
                current_dir=str(current_dir),
                os_name=platform.system(),
                directory_stats=context,
                user_command=user_command
            )
        except Exception as e:
            logger.error(f"Error rendering prompt: {e}")
            return json.loads(self._mock_response(user_command, current_dir))

        # Call AI
        if self.executor.is_available():
            response_text = self.executor.execute_prompt(prompt)
        else:
            # Fallback/Mock for testing environment
            logger.warning("Gemini CLI not available. Using mock response.")
            return json.loads(self._mock_response(user_command, current_dir))

        # Validate
        try:
            return ResponseValidator.validate_plan(response_text)
        except ValueError as e:
            logger.warning(f"Validation failed: {e}. Retrying with feedback.")
            return self._retry_with_feedback(user_command, prompt, str(e))

    def _retry_with_feedback(self, original_command: str, original_prompt: str, error: str) -> Dict[str, Any]:
        try:
            template = self.prompt_env.get_template("validation.jinja2")
            feedback_prompt = template.render(
                validation_error=error,
                user_command=original_command
            )

            full_prompt = f"{original_prompt}\n\n{feedback_prompt}"

            if self.executor.is_available():
                response_text = self.executor.execute_prompt(full_prompt)
                return ResponseValidator.validate_plan(response_text)
            else:
                 raise ValueError(f"Mock validation failed: {error}")
        except Exception as e:
            logger.error(f"Retry failed: {e}")
            raise ValueError(f"AI Plan Generation Failed: {e}")

    def _mock_response(self, command: str, current_dir: Path) -> str:
        """Generate a mock JSON response for testing."""
        command_lower = command.lower()
        plan = []

        if "organize" in command_lower:
            if "date" in command_lower:
                plan.append({
                    "step": 1,
                    "action": "organize_by_date",
                    "params": {"source": str(current_dir), "target": str(current_dir / "Organized_Date"), "move": True},
                    "description": "Organize files by date.",
                    "is_destructive": False
                })
            else:
                 plan.append({
                    "step": 1,
                    "action": "organize_by_type",
                    "params": {"source": str(current_dir), "target": str(current_dir / "Organized_Type"), "move": True},
                    "description": "Organize files by type.",
                    "is_destructive": False
                })

        elif "clean" in command_lower or "delete" in command_lower:
             plan.append({
                    "step": 1,
                    "action": "cleanup_old_files",
                    "params": {"directory": str(current_dir), "days": 30, "recursive": False, "dry_run": True},
                    "description": "Clean up old files (Dry Run).",
                    "is_destructive": True
                })

        elif "rename" in command_lower:
             plan.append({
                    "step": 1,
                    "action": "batch_rename",
                    "params": {"directory": str(current_dir), "pattern": "IMG", "replacement": "image", "recursive": False},
                    "description": "Batch rename IMG to image.",
                    "is_destructive": False
             })

        else:
             plan.append({
                    "step": 1,
                    "action": "find_duplicates",
                    "params": {"directory": str(current_dir), "recursive": False},
                    "description": "Find duplicate files.",
                    "is_destructive": False
                })

        return json.dumps({"plan": plan}, indent=2)

    async def execute_plan_step(self, step: Dict[str, Any], dry_run: bool = True) -> str:
        """
        Execute a single step from the plan.
        """
        action = step.get("action")
        params = step.get("params", {})

        try:
            if action == "organize_by_type":
                result = await self.organizer.organize_by_type(
                    Path(params["source"]), Path(params["target"]), move=params.get("move", True), dry_run=dry_run
                )
                count = sum(len(files) for files in result.values())
                action_str = "Would organize" if dry_run else "Organized"
                return f"{action_str} {count} files by type."

            elif action == "organize_by_date":
                result = await self.organizer.organize_by_date(
                     Path(params["source"]), Path(params["target"]), move=params.get("move", True), dry_run=dry_run
                )
                count = sum(len(files) for files in result.values())
                action_str = "Would organize" if dry_run else "Organized"
                return f"{action_str} {count} files by date."

            elif action == "cleanup_old_files":
                is_dry = dry_run or params.get("dry_run", False)
                deleted = await self.organizer.cleanup_old_files(
                    Path(params["directory"]), params.get("days", 30), params.get("recursive", False), is_dry
                )
                prefix = "Would delete" if is_dry else "Deleted"
                return f"{prefix} {len(deleted)} files."

            elif action == "find_duplicates":
                duplicates = await self.organizer.find_duplicates(
                    Path(params["directory"]), params.get("recursive", False)
                )
                count = sum(len(files) for files in duplicates.values())
                return f"Found {len(duplicates)} duplicate groups ({count} files)."

            elif action == "batch_rename":
                 renamed = await self.organizer.batch_rename(
                     Path(params["directory"]), params["pattern"], params["replacement"], params.get("recursive", False), dry_run=dry_run
                 )
                 action_str = "Would rename" if dry_run else "Renamed"
                 return f"{action_str} {len(renamed)} files."

            elif action == "add_tag":
                file_path = Path(params["file"])
                tag = params["tag"]
                if not dry_run:
                    self.tag_manager.add_tag(file_path, tag)
                prefix = "Would add" if dry_run else "Added"
                return f"{prefix} tag '{tag}' to {file_path.name}."

            elif action == "remove_tag":
                file_path = Path(params["file"])
                tag = params["tag"]
                if not dry_run:
                    self.tag_manager.remove_tag(file_path, tag)
                prefix = "Would remove" if dry_run else "Removed"
                return f"{prefix} tag '{tag}' from {file_path.name}."

            else:
                return f"Unknown action: {action}"

        except Exception as e:
            return f"Error: {str(e)}"

    def suggest_tags(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Suggest tags for files."""
        if not self.prompt_env:
            return {}

        try:
            template = self.prompt_env.get_template("tagging.jinja2")
            prompt = template.render(files=files)
        except Exception as e:
            logger.error(f"Error rendering prompt: {e}")
            return {}

        if self.executor.is_available():
            response_text = self.executor.execute_prompt(prompt)
            try:
                return ResponseValidator.validate_tags(response_text)
            except ValueError as e:
                logger.warning(f"Tag validation failed: {e}")
                return {}
        else:
            # Mock for testing
            logger.warning("Gemini CLI not available. Using mock tags.")
            return {
                "suggestions": [
                    {"file": f.get("name", "unknown"), "tags": ["mock-tag", "auto-generated"]}
                    for f in files[:5]
                ]
            }

    def search_history(self, query: str, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Search history using AI."""
        if not self.executor.is_available():
            # Fallback to keyword search locally if AI unavailable
            return [h for h in history if query.lower() in h["command"].lower()]

        prompt = f"Find the most relevant commands from the history for the query: '{query}'.\nHistory:\n"
        for i, entry in enumerate(history):
            prompt += f"{i}. {entry['command']}\n"
        prompt += "\nReturn JSON: {'indices': [0, 2]}"

        response_text = self.executor.execute_prompt(prompt)
        try:
            # Clean response
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            start = clean_text.find("{")
            end = clean_text.rfind("}")
            if start != -1 and end != -1:
                clean_text = clean_text[start:end+1]

            data = json.loads(clean_text)
            indices = data.get("indices", [])
            return [history[i] for i in indices if 0 <= i < len(history)]
        except Exception:
             return [h for h in history if query.lower() in h["command"].lower()]

    def process_command(self, command: str, current_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Legacy/Compatibility wrapper.
        """
        if current_dir is None:
            current_dir = Path.cwd()

        try:
            plan_data = self.generate_plan(command, current_dir)
            if not plan_data["plan"]:
                 return {"action": "unknown", "description": "No plan generated."}

            return {
                "action": "plan_ready",
                "plan": plan_data["plan"],
                "description": f"Generated plan with {len(plan_data['plan'])} steps."
            }
        except Exception as e:
            return {
                "action": "unknown",
                "description": f"Error processing command: {e}"
            }
