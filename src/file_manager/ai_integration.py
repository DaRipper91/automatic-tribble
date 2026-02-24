"""
Gemini Integration for File Manager AI
"""

import os
import json
import platform
from pathlib import Path
from typing import Dict, Any, Optional, List
from jinja2 import Environment, FileSystemLoader

from .automation import FileOrganizer
from .ai_utils import AIExecutor
from .ai_validation import ResponseValidator
from .context import DirectoryContextBuilder
from .logger import get_logger
from .file_operations import FileOperations

logger = get_logger("ai_integration")

class GeminiClient:
    """Client for Gemini AI integration with structured planning and validation."""

    def __init__(self):
        self.organizer = FileOrganizer()
        self.file_ops = FileOperations()
        self.executor = AIExecutor()
        self.validator = ResponseValidator()
        self.context_builder = DirectoryContextBuilder()

        # Jinja2 Setup
        # Assuming prompts are in src/file_manager/prompts/ relative to this file
        template_dir = Path(__file__).parent / "prompts"
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))

        self.is_available = self.executor.is_available()
        if not self.is_available:
            logger.warning("Gemini CLI not found. AI features will run in MOCK mode.")

    def process_command(self, command: str, current_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Process a natural language command and generate a structured plan.
        """
        if current_dir is None:
            current_dir = Path.cwd()

        # Build Context
        context = self.context_builder.get_context(current_dir)
        os_name = platform.system()

        # Render Prompt
        try:
            template = self.jinja_env.get_template("planning.jinja2")
            prompt = template.render(
                context=context,
                os_name=os_name,
                user_request=command
            )
        except Exception as e:
            logger.error(f"Error rendering prompt: {e}")
            return {"plan": [], "summary": "Internal Error", "description": str(e), "confidence": 0.0}

        # Execute with Retry
        if self.is_available:
            response_text = self._execute_with_retry(prompt, self.validator.validate_plan)
        else:
            response_text = self._mock_response(command, current_dir)

        # Parse final response (or mock)
        plan_data, error = self.validator.validate_plan(response_text)

        if error:
            logger.error(f"Final validation failed: {error}")
            return {
                "plan": [],
                "summary": "Failed to generate a valid plan.",
                "description": f"AI Error: {error}\n\nRaw Response:\n{response_text}",
                "confidence": 0.0
            }

        return plan_data

    def suggest_tags(self, file_path: Path) -> List[str]:
        """
        Suggest tags for a given file.
        """
        if not file_path.exists():
            return []

        try:
            stat = file_path.stat()
            context = {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "file_type": file_path.suffix,
                "file_size": stat.st_size,
                "creation_date": stat.st_ctime, # Roughly
                "surrounding_files": [p.name for p in list(file_path.parent.iterdir())[:5]]
            }

            template = self.jinja_env.get_template("tagging.jinja2")
            prompt = template.render(**context)

            if self.is_available:
                response_text = self._execute_with_retry(prompt, self.validator.validate_tagging)
                data, error = self.validator.validate_tagging(response_text)
                if data:
                    return data.get("suggested_tags", [])

            # Mock fallback
            return ["#auto-suggested"]

        except Exception as e:
            logger.error(f"Error suggesting tags: {e}")
            return []

    async def execute_step(self, step: Dict[str, Any]) -> str:
        """
        Execute a single atomic step from the plan.
        """
        action = step.get("action")
        source = step.get("source")
        target = step.get("target")
        params = step.get("params", {})

        # Ensure dry_run is respected if passed in params, but usually UI handles dry run by just showing the plan.
        # Here we are executing the REAL step.
        # Wait, if the plan says dry_run=True, should we execute it?
        # The prompts say "default dry_run=true for destructive".
        # If the user confirmed the plan, they want to EXECUTE it.
        # So we should override dry_run=False unless the step explicitly calls for a check.
        # But wait, automation methods like cleanup_old_files use dry_run to RETURN the list of files.
        # If we are in execute phase, we want to delete.

        # We assume the caller (UI) decides when to run dry (display plan) vs real (execute).
        # When calling execute_step, we mean "do it".
        # So we force dry_run=False for automation tasks.

        source_path = Path(source) if source else None
        target_path = Path(target) if target else None

        try:
            if action == "copy":
                await self.file_ops.copy(source_path, target_path)
                return f"Copied {source} to {target}"

            elif action == "move":
                await self.file_ops.move(source_path, target_path)
                return f"Moved {source} to {target}"

            elif action == "delete":
                await self.file_ops.delete(source_path)
                return f"Deleted {source}"

            elif action == "rename":
                await self.file_ops.rename(source_path, target_path.name) # rename expects new_name
                return f"Renamed {source} to {target}"

            elif action == "mkdir":
                await self.file_ops.create_directory(source_path)
                return f"Created directory {source}"

            elif action == "organize_by_type":
                result = await self.organizer.organize_by_type(source_path, target_path, move=True)
                count = sum(len(files) for files in result.values())
                return f"Organized {count} files by type."

            elif action == "organize_by_date":
                result = await self.organizer.organize_by_date(source_path, target_path, move=True)
                count = sum(len(files) for files in result.values())
                return f"Organized {count} files by date."

            elif action == "cleanup_old_files":
                days = params.get("days", 30)
                recursive = params.get("recursive", False)
                # Force dry_run=False
                deleted = await self.organizer.cleanup_old_files(source_path, days, recursive, dry_run=False)
                return f"Deleted {len(deleted)} files older than {days} days."

            elif action == "find_duplicates":
                # This is a read-only action usually, unless resolved?
                # The plan probably just says "find duplicates".
                # Real execution might mean "report them" or "delete them if auto-resolve is on".
                # For now, just report.
                recursive = params.get("recursive", False)
                dupes = await self.organizer.find_duplicates(source_path, recursive)
                count = sum(len(files) for files in dupes.values())
                return f"Found {len(dupes)} duplicate groups ({count} files)."

            elif action == "batch_rename":
                pattern = params.get("pattern")
                replacement = params.get("replacement")
                recursive = params.get("recursive", False)
                renamed = await self.organizer.batch_rename(source_path, pattern, replacement, recursive)
                return f"Renamed {len(renamed)} files."

            elif action == "tag":
                tags = params.get("tags", [])
                # We need TagManager here.
                # Since TagManager is not instantiated in __init__ (circular dep risk?), we import locally or handle it.
                # For now, let's just log it.
                return f"Tagged {source} with {tags} (Not fully implemented in step executor yet)"

            else:
                return f"Unknown action: {action}"

        except Exception as e:
            return f"Error: {str(e)}"

    def _execute_with_retry(self, prompt: str, validator_func) -> str:
        """
        Execute prompt with retry logic for validation failures.
        """
        current_prompt = prompt
        last_response = ""

        for attempt in range(3):
            logger.info(f"AI Request Attempt {attempt + 1}")
            response = self.executor.execute_prompt(current_prompt)
            last_response = response

            # Validate
            _, error = validator_func(response)

            if not error:
                return response

            logger.warning(f"Validation failed: {error}")

            # Generate correction prompt
            try:
                validation_template = self.jinja_env.get_template("validation.jinja2")
                current_prompt = validation_template.render(
                    error_message=error,
                    original_prompt=prompt,
                    original_response=response
                )
            except Exception as e:
                logger.error(f"Error rendering validation prompt: {e}")
                break

        return last_response # Return last response even if invalid

    def _mock_response(self, command: str, current_dir: Path) -> str:
        """
        Generate a mock response for testing when Gemini is unavailable.
        """
        command_lower = command.lower()
        plan = []
        summary = "Mock execution plan."

        if "organize" in command_lower:
            target = current_dir / "Organized"
            if "date" in command_lower:
                plan.append({
                    "action": "organize_by_date",
                    "source": str(current_dir),
                    "target": str(target),
                    "params": {"dry_run": True},
                    "description": f"Organize files in {current_dir} by date into {target}",
                    "is_destructive": False
                })
                summary = "Organizing files by date."
            else:
                 plan.append({
                    "action": "organize_by_type",
                    "source": str(current_dir),
                    "target": str(target),
                    "params": {"dry_run": True},
                    "description": f"Organize files in {current_dir} by type into {target}",
                    "is_destructive": False
                })
                 summary = "Organizing files by type."
        elif "clean" in command_lower:
             plan.append({
                "action": "cleanup_old_files",
                "source": str(current_dir),
                "params": {"days": 30, "dry_run": True},
                "description": "Clean up files older than 30 days.",
                "is_destructive": True
            })
             summary = "Cleaning up old files."
        elif "rename" in command_lower:
             plan.append({
                 "action": "batch_rename",
                 "source": str(current_dir),
                 "params": {"pattern": "test", "replacement": "demo", "dry_run": True},
                 "description": "Batch rename 'test' to 'demo'.",
                 "is_destructive": False
             })
             summary = "Batch renaming files."
        else:
             summary = "Could not understand command (Mock)."

        return json.dumps({
            "plan": plan,
            "summary": summary,
            "confidence": 0.9 if plan else 0.0
        })
