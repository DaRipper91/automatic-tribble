"""
Core file operations with undo/redo support.
"""

import os
import shutil
import uuid
import json
import logging
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

from .utils import recursive_scan
from .logger import get_logger
from .exceptions import TFMPermissionError, TFMPathNotFoundError, TFMOperationConflictError
from .plugins.registry import PluginRegistry

logger = get_logger("file_ops")

class OperationType(Enum):
    MOVE = auto()
    COPY = auto()
    RENAME = auto()
    DELETE = auto()
    CREATE_DIR = auto()

@dataclass
class FileOperation:
    """Represents a single file operation for undo/redo."""
    type: OperationType
    original_path: Path
    target_path: Optional[Path] = None
    timestamp: datetime = field(default_factory=datetime.now)
    trash_path: Optional[Path] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type.name,
            "original_path": str(self.original_path),
            "target_path": str(self.target_path) if self.target_path else None,
            "timestamp": self.timestamp.isoformat(),
            "trash_path": str(self.trash_path) if self.trash_path else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileOperation':
        """Create from dictionary."""
        return cls(
            type=OperationType[data["type"]],
            original_path=Path(data["original_path"]),
            target_path=Path(data["target_path"]) if data.get("target_path") else None,
            timestamp=datetime.fromisoformat(data["timestamp"]),
            trash_path=Path(data["trash_path"]) if data.get("trash_path") else None,
        )

class OperationHistory:
    """Tracks destructive operations and supports undo/redo."""

    def __init__(self):
        self._undo_stack: List[FileOperation] = []
        self._redo_stack: List[FileOperation] = []
        self.history_file = Path.home() / ".tfm" / "history.json"
        self._cleanup_old_history()
        self._load()

    def _cleanup_old_history(self):
        """Remove old pickle history file if it exists."""
        old_history = Path.home() / ".tfm" / "history.pkl"
        if old_history.exists():
            try:
                old_history.unlink()
                logger.info("Removed legacy history.pkl file")
            except OSError as e:
                logger.warning(f"Failed to remove legacy history file: {e}")

    def _load(self):
        """Load history from JSON file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, "r") as f:
                    data = json.load(f)
                    if not isinstance(data, dict):
                        logger.warning("History file format invalid. Resetting.")
                        self._undo_stack = []
                        self._redo_stack = []
                        return

                    self._undo_stack = [FileOperation.from_dict(op) for op in data.get("undo", [])]
                    self._redo_stack = [FileOperation.from_dict(op) for op in data.get("redo", [])]
            except (json.JSONDecodeError, KeyError, ValueError, OSError) as e:
                logger.error(f"Failed to load operation history: {e}")
                self._undo_stack = []
                self._redo_stack = []

    def _save(self):
        """Save history to JSON file."""
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "undo": [op.to_dict() for op in self._undo_stack],
                "redo": [op.to_dict() for op in self._redo_stack]
            }
            with open(self.history_file, "w") as f:
                json.dump(data, f, indent=2)
        except OSError as e:
            logger.error(f"Failed to save history: {e}")

    def log_operation(self, op: FileOperation) -> None:
        """Log an operation to the undo stack."""
        self._undo_stack.append(op)
        self._redo_stack.clear()
        if len(self._undo_stack) > 100:
            self._undo_stack.pop(0)
        self._save()

    def undo_last(self) -> Optional[FileOperation]:
        """Get the last operation to undo."""
        if not self._undo_stack:
            return None
        op = self._undo_stack.pop()
        self._redo_stack.append(op)
        self._save()
        return op

    def redo_last(self) -> Optional[FileOperation]:
        """Get the last operation to redo."""
        if not self._redo_stack:
            return None
        op = self._redo_stack.pop()
        self._undo_stack.append(op)
        self._save()
        return op

class FileOperations:
    """Handles core file operations with undo support."""
    def __init__(self, history: Optional[OperationHistory] = None):
        self.history = history or OperationHistory()
        self.trash_dir = Path.home() / ".tfm" / "trash"
        self.trash_dir.mkdir(parents=True, exist_ok=True)
        self.plugins = PluginRegistry()

    async def move(self, source: Path, target: Path) -> bool:
        """Move a file or directory."""
        try:
            if target.exists():
                raise TFMOperationConflictError(f"Target already exists: {target}")
            shutil.move(str(source), str(target))
            self.history.log_operation(FileOperation(OperationType.MOVE, source, target))
            return True
        except Exception as e:
            logger.error(f"Move failed: {e}")
            return False

    async def copy(self, source: Path, target: Path) -> bool:
        """Copy a file or directory."""
        try:
            if target.exists():
                raise TFMOperationConflictError(f"Target already exists: {target}")
            if source.is_dir():
                shutil.copytree(str(source), str(target))
            else:
                shutil.copy2(str(source), str(target))
            self.history.log_operation(FileOperation(OperationType.COPY, source, target))
            return True
        except Exception as e:
            logger.error(f"Copy failed: {e}")
            return False

    async def delete(self, path: Path) -> bool:
        """Soft delete (move to trash)."""
        try:
            trash_path = self.trash_dir / f"{uuid.uuid4()}_{path.name}"
            shutil.move(str(path), str(trash_path))
            self.history.log_operation(FileOperation(OperationType.DELETE, path, trash_path=trash_path))
            self.plugins.on_file_deleted(path)
            return True
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False

    async def rename(self, path: Path, new_name: str) -> bool:
        """Rename a file or directory."""
        try:
            target = path.parent / new_name
            if target.exists():
                 raise TFMOperationConflictError(f"Target already exists: {target}")
            path.rename(target)
            self.history.log_operation(FileOperation(OperationType.RENAME, path, target))
            return True
        except Exception as e:
            logger.error(f"Rename failed: {e}")
            return False

    async def create_directory(self, path: Path, exist_ok: bool = False) -> bool:
        """Create a new directory."""
        try:
            path.mkdir(parents=True, exist_ok=exist_ok)
            self.history.log_operation(FileOperation(OperationType.CREATE_DIR, path))
            return True
        except Exception as e:
            logger.error(f"Create directory failed: {e}")
            return False

    async def undo(self) -> str:
        """Undo the last operation."""
        op = self.history.undo_last()
        if not op:
            return "Nothing to undo."

        try:
            if op.type == OperationType.MOVE:
                shutil.move(str(op.target_path), str(op.original_path))
                return f"Undid move: {op.original_path.name}"
            elif op.type == OperationType.COPY:
                if op.target_path.is_dir():
                    shutil.rmtree(str(op.target_path))
                else:
                    op.target_path.unlink()
                return f"Undid copy: {op.target_path.name}"
            elif op.type == OperationType.DELETE:
                shutil.move(str(op.trash_path), str(op.original_path))
                return f"Restored from trash: {op.original_path.name}"
            elif op.type == OperationType.RENAME:
                op.target_path.rename(op.original_path)
                return f"Undid rename: {op.original_path.name}"
            elif op.type == OperationType.CREATE_DIR:
                if op.original_path.exists():
                     shutil.rmtree(str(op.original_path))
                return f"Undid directory creation: {op.original_path.name}"
        except Exception as e:
            return f"Undo failed: {e}"

        return "Unknown operation type."

    async def redo(self) -> str:
        """Redo the last undone operation."""
        op = self.history.redo_last()
        if not op:
            return "Nothing to redo."

        try:
            if op.type == OperationType.MOVE:
                shutil.move(str(op.original_path), str(op.target_path))
                return f"Redid move: {op.original_path.name}"
            elif op.type == OperationType.COPY:
                if op.original_path.is_dir():
                    shutil.copytree(str(op.original_path), str(op.target_path))
                else:
                    shutil.copy2(str(op.original_path), str(op.target_path))
                return f"Redid copy: {op.original_path.name}"
            elif op.type == OperationType.DELETE:
                shutil.move(str(op.original_path), str(op.trash_path))
                return f"Redid delete: {op.original_path.name}"
            elif op.type == OperationType.RENAME:
                op.original_path.rename(op.target_path)
                return f"Redid rename: {op.target_path.name}"
            elif op.type == OperationType.CREATE_DIR:
                op.original_path.mkdir(parents=True, exist_ok=True)
                return f"Redid directory creation: {op.original_path.name}"
        except Exception as e:
            return f"Redo failed: {e}"

        return "Unknown operation type."
