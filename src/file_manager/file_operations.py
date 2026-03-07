"""
Core file operations with undo/redo support.
"""

import shutil
import uuid
import asyncio
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional
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

    def log_operation(self, op: FileOperation) -> None:
        """Log an operation to the undo stack."""
        self._undo_stack.append(op)
        self._redo_stack.clear()
        if len(self._undo_stack) > 100:
            self._undo_stack.pop(0)

    def undo_last(self) -> Optional[FileOperation]:
        """Get the last operation to undo."""
        if not self._undo_stack:
            return None
        op = self._undo_stack.pop()
        self._redo_stack.append(op)
        return op

    def redo_last(self) -> Optional[FileOperation]:
        """Get the last operation to redo."""
        if not self._redo_stack:
            return None
        op = self._redo_stack.pop()
        self._undo_stack.append(op)
        return op

class FileOperations:
    """Handles core file operations with undo support."""
    def __init__(self, history: Optional[OperationHistory] = None):
        self.history = history or OperationHistory()
        self.trash_dir = Path.home() / ".tfm" / "trash"
        self._ensure_trash_dir()
        self.plugins = PluginRegistry()

    def _ensure_trash_dir(self):
        """Ensure trash directory exists."""
        self.trash_dir.mkdir(parents=True, exist_ok=True)

    async def move(self, source: Path, target: Path) -> bool:
        """Move a file or directory."""
        if not source.exists():
             raise TFMPathNotFoundError(str(source))
        if target.exists():
            raise TFMOperationConflictError(f"Target already exists: {target}")
        try:
            await asyncio.to_thread(shutil.move, str(source), str(target))
            self.history.log_operation(FileOperation(OperationType.MOVE, source, target))
            self.plugins.on_file_added(target)
            return True
        except (TFMPathNotFoundError, TFMOperationConflictError):
            raise
        except Exception as e:
            logger.error(f"Move failed: {e}")
            return False

    async def copy(self, source: Path, target: Path) -> bool:
        """Copy a file or directory."""
        if not source.exists():
             raise TFMPathNotFoundError(str(source))
        if target.exists():
            raise TFMOperationConflictError(f"Target already exists: {target}")
        try:

            if source.is_dir():
                await asyncio.to_thread(shutil.copytree, str(source), str(target))
            else:
                await asyncio.to_thread(shutil.copy2, str(source), str(target))
            self.history.log_operation(FileOperation(OperationType.COPY, source, target))
            self.plugins.on_file_added(target)
            return True
        except (TFMPathNotFoundError, TFMOperationConflictError):
            raise
        except Exception as e:
            logger.error(f"Copy failed: {e}")
            return False

    async def delete(self, path: Path) -> bool:
        """Soft delete (move to trash)."""
        if not path.exists():
             raise TFMPathNotFoundError(str(path))
        try:
            trash_path = self.trash_dir / f"{uuid.uuid4()}_{path.name}"
            await asyncio.to_thread(shutil.move, str(path), str(trash_path))
            self.history.log_operation(FileOperation(OperationType.DELETE, path, trash_path=trash_path))
            self.plugins.on_file_deleted(path)
            return True
        except PermissionError:
            raise TFMPermissionError(str(path))
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False

    async def rename(self, path: Path, new_name: str) -> bool:
        """Rename a file or directory."""
        if not path.exists():
             raise TFMPathNotFoundError(str(path))
        target = path.parent / new_name
        if target.exists():
             raise TFMOperationConflictError(f"Target already exists: {target}")
        try:
            await asyncio.to_thread(path.rename, target)
            self.history.log_operation(FileOperation(OperationType.RENAME, path, target))
            return True
        except (TFMPathNotFoundError, TFMOperationConflictError):
            raise
        except Exception as e:
            logger.error(f"Rename failed: {e}")
            return False

    async def create_directory(self, path: Path, exist_ok: bool = False) -> bool:
        """Create a new directory."""
        if path.exists() and not exist_ok:
             raise TFMOperationConflictError(f"Target already exists: {path}")
        try:
            if not exist_ok and path.exists():
                raise TFMOperationConflictError(f"Target already exists: {path}")
            await asyncio.to_thread(path.mkdir, parents=True, exist_ok=exist_ok)
            self.history.log_operation(FileOperation(OperationType.CREATE_DIR, path))
            self.plugins.on_file_added(path)
            return True
        except TFMOperationConflictError:
            raise
        except Exception as e:
            logger.error(f"Create directory failed: {e}")
            return False

    def get_size(self, path: Path) -> int:
        """Return size in bytes. For directories, recurse via recursive_scan."""
        if not path.exists():
            return 0
        if path.is_file():
            try:
                return path.stat().st_size
            except OSError:
                return 0
        total = 0
        for entry in recursive_scan(path):
            if entry.is_file(follow_symlinks=True):
                try:
                    total += entry.stat().st_size
                except OSError:
                    pass
        return total

    @staticmethod
    def format_size(size: int) -> str:
        """Convert bytes to a human-readable string."""
        current_size = float(size)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if current_size < 1024:
                return f"{current_size:.1f} {unit}"
            current_size /= 1024
        return f"{current_size:.1f} PB"

    async def undo_last(self) -> str:
        """Undo the last operation."""
        op = self.history.undo_last()
        if not op:
            return "Nothing to undo."

        try:
            if op.type == OperationType.MOVE and op.target_path:
                await asyncio.to_thread(shutil.move, str(op.target_path), str(op.original_path))
                return f"Undid move: {op.original_path.name}"
            elif op.type == OperationType.COPY and op.target_path:
                if op.target_path.is_dir():
                    await asyncio.to_thread(shutil.rmtree, str(op.target_path))
                else:
                    await asyncio.to_thread(op.target_path.unlink)
                return f"Undid copy: {op.target_path.name}"
            elif op.type == OperationType.DELETE and op.trash_path:
                if not op.trash_path.exists():
                    return f"Undo failed: trash file missing for {op.original_path.name}"
                await asyncio.to_thread(shutil.move, str(op.trash_path), str(op.original_path))
                return f"Restored from trash: {op.original_path.name}"
            elif op.type == OperationType.RENAME and op.target_path:
                await asyncio.to_thread(op.target_path.rename, op.original_path)
                return f"Undid rename: {op.original_path.name}"
            elif op.type == OperationType.CREATE_DIR:
                if op.original_path.exists():
                     await asyncio.to_thread(shutil.rmtree, str(op.original_path))
                return f"Undid directory creation: {op.original_path.name}"
        except Exception as e:
            # Revert history if execution fails
            self.history.redo_last()
            return f"Undo failed: {e}"

        return "Unknown operation type."

    async def redo_last(self) -> str:
        """Redo the last undone operation."""
        op = self.history.redo_last()
        if not op:
            return "Nothing to redo."

        try:
            if op.type == OperationType.MOVE and op.target_path:
                await asyncio.to_thread(shutil.move, str(op.original_path), str(op.target_path))
                return f"Redid move: {op.original_path.name}"
            elif op.type == OperationType.COPY and op.target_path:
                if op.original_path.is_dir():
                    await asyncio.to_thread(shutil.copytree, str(op.original_path), str(op.target_path))
                else:
                    await asyncio.to_thread(shutil.copy2, str(op.original_path), str(op.target_path))
                return f"Redid copy: {op.original_path.name}"
            elif op.type == OperationType.DELETE and op.trash_path:
                await asyncio.to_thread(shutil.move, str(op.original_path), str(op.trash_path))
                return f"Redid delete: {op.original_path.name}"
            elif op.type == OperationType.RENAME and op.target_path:
                await asyncio.to_thread(op.original_path.rename, op.target_path)
                return f"Redid rename: {op.target_path.name}"
            elif op.type == OperationType.CREATE_DIR:
                await asyncio.to_thread(op.original_path.mkdir, parents=True, exist_ok=True)
                return f"Redid directory creation: {op.original_path.name}"
        except Exception as e:
            # Revert history if execution fails
            self.history.undo_last()
            return f"Redo failed: {e}"

        return "Unknown operation type."

    # Short aliases expected by tests and TUI
    undo = undo_last
    redo = redo_last
