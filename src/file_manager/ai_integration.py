"""
Gemini Integration Mock for File Manager AI
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional

from .automation import FileOrganizer


class GeminiClient:
    """Mock client for Gemini AI integration."""

    def __init__(self):
        self.organizer = FileOrganizer()

    def process_command(self, command: str, current_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Process a natural language command and determine the action to take.

        Args:
            command: The user's input string.
            current_dir: The directory context for the command (default: current working dir).

        Returns:
            Dictionary containing 'action', 'params', and 'description'.
        """
        command_lower = command.lower()
        if current_dir is None:
            current_dir = Path.cwd()

        action_data = {
            "action": "unknown",
            "params": {},
            "description": "Could not understand the command."
        }

        # Simple keyword matching for mock logic
        if "organize" in command_lower or "sort" in command_lower:
            if "date" in command_lower or "time" in command_lower:
                action_data = {
                    "action": "organize_by_date",
                    "params": {
                        "source_dir": str(current_dir),
                        "target_dir": str(current_dir / "Organized_Date"),
                        "move": True
                    },
                    "description": f"Organizing files in {current_dir} by date."
                }
            else:
                # Default to type
                action_data = {
                    "action": "organize_by_type",
                    "params": {
                        "source_dir": str(current_dir),
                        "target_dir": str(current_dir / "Organized_Type"),
                        "move": True
                    },
                    "description": f"Organizing files in {current_dir} by file type."
                }

        elif "clean" in command_lower or "remove" in command_lower or "delete" in command_lower:
            days = 30 # Default
            # Try to extract days
            import re
            days_match = re.search(r'(\d+)\s*days?', command_lower)
            if days_match:
                days = int(days_match.group(1))

            action_data = {
                "action": "cleanup_old_files",
                "params": {
                    "directory": str(current_dir),
                    "days_old": days,
                    "recursive": "recursive" in command_lower,
                    "dry_run": "dry" in command_lower or "check" in command_lower
                },
                "description": f"Cleaning up files older than {days} days in {current_dir}."
            }

        elif "duplicate" in command_lower:
            action_data = {
                "action": "find_duplicates",
                "params": {
                    "directory": str(current_dir),
                    "recursive": "recursive" in command_lower
                },
                "description": f"Scanning for duplicate files in {current_dir}."
            }

        elif "rename" in command_lower:
            # Simple mock for rename, expecting format "rename pattern to replacement"
            # Use original command to preserve case for pattern
            parts = command.split()
            parts_lower = command_lower.split()
            try:
                # Very basic parsing logic
                pattern = "image" # Default
                replacement = "img" # Default

                if "rename" in parts_lower:
                    idx = parts_lower.index("rename")
                    # Try to find 'to'
                    to_idx = -1
                    if "to" in parts_lower[idx:]:
                         to_idx = parts_lower.index("to", idx)

                    if idx + 1 < len(parts):
                        if to_idx != -1 and to_idx > idx + 1:
                            pattern = " ".join(parts[idx + 1:to_idx])
                            if to_idx + 1 < len(parts):
                                replacement = " ".join(parts[to_idx + 1:])
                        else:
                            # Fallback if no 'to'
                            pattern = parts[idx + 1]

                action_data = {
                    "action": "batch_rename",
                    "params": {
                        "directory": str(current_dir),
                        "pattern": pattern,
                        "replacement": replacement,
                        "recursive": "recursive" in command_lower
                    },
                    "description": f"Renaming files matching '{pattern}' to '{replacement}' in {current_dir}."
                }
            except Exception:
                pass

        return action_data

    def execute_command(self, action_data: Dict[str, Any]) -> str:
        """
        Execute the action determined by process_command.

        Args:
            action_data: Dictionary from process_command.

        Returns:
            Result message.
        """
        action = action_data.get("action")
        params = action_data.get("params", {})

        try:
            if action == "organize_by_type":
                source = Path(params["source_dir"])
                target = Path(params["target_dir"])
                move = params.get("move", False)
                result = self.organizer.organize_by_type(source, target, move=move)
                count = sum(len(files) for files in result.values())
                return f"Successfully organized {count} files by type into {target}."

            elif action == "organize_by_date":
                source = Path(params["source_dir"])
                target = Path(params["target_dir"])
                move = params.get("move", False)
                result = self.organizer.organize_by_date(source, target, move=move)
                count = sum(len(files) for files in result.values())
                return f"Successfully organized {count} files by date into {target}."

            elif action == "cleanup_old_files":
                directory = Path(params["directory"])
                days = params.get("days_old", 30)
                recursive = params.get("recursive", False)
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

            else:
                return "Unknown action or command not understood."

        except Exception as e:
            return f"Error executing command: {str(e)}"
