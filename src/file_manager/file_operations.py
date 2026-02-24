"""
File operations module for copy, move, delete, etc.
"""

import asyncio
import os
import shutil
import uuid
from pathlib import Path
from typing import Union, List, Optional
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime
from .utils import recursive_scan
from .logger import get_logger
from .exceptions import TFMPermissionError, TFMPathNotFoundError, TFMOperationConflictError
from .plugins.registry import PluginRegistry

logger = get_logger("file_ops")

class OperationType(Enum):
    MOVE = auto()
    COPY = auto()
    DELETE = auto()
    RENAME = auto()
    CREATE_DIR = auto()

@dataclass
class FileOperation:
    type: OperationType
    original_path: Path
    target_path: Optional[Path] = None
    timestamp: datetime = field(default_factory=datetime.now)
    trash_path: Optional[Path] = None

class OperationHistory:
    """Tracks destructive operations and supports undo/redo."""

    def __init__(self):
        self._undo_stack: List[FileOperation] = []
        self._redo_stack: List[FileOperation] = []
        self.history_file = Path.home() / ".tfm" / "history.pkl"
        self._load()

    def _load(self):
        if self.history_file.exists():
            try:
                import pickle
                with open(self.history_file, "rb") as f:
                    data = pickle.load(f)
                    self._undo_stack = data.get("undo", [])
                    self._redo_stack = data.get("redo", [])
            except Exception:
                pass

    def _save(self):
        try:
            import pickle
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.history_file, "wb") as f:
                pickle.dump({"undo": self._undo_stack, "redo": self._redo_stack}, f)
        except Exception:
            pass

    def log_operation(self, op: FileOperation) -> None:
        """Log an operation to the undo stack."""
        self._undo_stack.append(op)
        self._redo_stack.clear()
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
        """Get the last undone operation to redo."""
        if not self._redo_stack:
            return None
        op = self._redo_stack.pop()
        self._undo_stack.append(op)
        self._save()
        return op

    def clear(self) -> None:
        """Clear the history."""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._save()


class FileOperations:
    """Handles file and directory operations."""

    def __init__(self):
        self.history = OperationHistory()
        self.plugins = PluginRegistry()
        self.plugins.load_plugins()
        self.trash_dir = Path.home() / ".tfm" / "trash"
        self._ensure_trash_dir()

    def _ensure_trash_dir(self):
        if not self.trash_dir.exists():
            try:
                self.trash_dir.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                logger.error(f"Failed to create trash directory: {e}")

    def _validate_transfer(self, source: Path, destination: Path) -> Path:
        """
        Validate source and destination for copy/move operations.
        """
        if not source.exists():
            raise TFMPathNotFoundError(str(source), "Source does not exist")

        if destination.is_dir():
            target = destination / source.name
        else:
            # Destination is treated as the full target path
            if not destination.parent.exists():
                raise TFMPathNotFoundError(str(destination.parent), "Destination parent directory does not exist")
            target = destination

        if target.exists():
            raise TFMOperationConflictError(str(target), "Destination already exists")

        return target

    def _ensure_path_exists(self, path: Path, message: str = "Path does not exist") -> None:
        """
        Ensure that a path exists.
        """
        if not path.exists():
            raise TFMPathNotFoundError(str(path), message)

    async def copy(self, source: Union[str, Path], destination: Union[str, Path]) -> None:
        """
        Copy a file or directory to a destination.
        """
        source = Path(source)
        destination = Path(destination)

        try:
            target = self._validate_transfer(source, destination)

            if source.is_file():
                await asyncio.to_thread(shutil.copy2, source, target)
            elif source.is_dir():
                await asyncio.to_thread(shutil.copytree, source, target, dirs_exist_ok=True)

            self.history.log_operation(FileOperation(OperationType.COPY, source, target))
            self.plugins.on_file_added(target)
            logger.info(f"Copied {source} to {target}")

        except (TFMPathNotFoundError, TFMOperationConflictError, TFMPermissionError):
            raise
        except (FileNotFoundError, FileExistsError) as e:
            raise TFMOperationConflictError(str(destination), str(e))
        except PermissionError as e:
            raise TFMPermissionError(str(source), str(e))
        except Exception as e:
            logger.error(f"Copy error: {e}")
            raise

    async def move(self, source: Union[str, Path], destination: Union[str, Path]) -> None:
        """
        Move a file or directory to a destination.
        """
        source = Path(source)
        destination = Path(destination)

        try:
            target = self._validate_transfer(source, destination)

            await asyncio.to_thread(shutil.move, str(source), str(target))

            self.history.log_operation(FileOperation(OperationType.MOVE, source, target))
            self.plugins.on_file_deleted(source)
            self.plugins.on_file_added(target)
            logger.info(f"Moved {source} to {target}")

        except (TFMPathNotFoundError, TFMOperationConflictError, TFMPermissionError):
            raise
        except PermissionError as e:
            raise TFMPermissionError(str(source), str(e))
        except Exception as e:
            logger.error(f"Move error: {e}")
            raise
    
    async def delete(self, path: Union[str, Path]) -> None:
        """
        Delete a file or directory (move to trash).
        """
        path = Path(path)
        self._ensure_path_exists(path)
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = uuid.uuid4().hex[:8]
            trash_name = f"{path.name}_{timestamp}_{unique_id}"
            trash_path = self.trash_dir / trash_name

            # Use move for deletion (trash)
            await asyncio.to_thread(shutil.move, str(path), str(trash_path))

            self.history.log_operation(FileOperation(
                OperationType.DELETE,
                original_path=path,
                trash_path=trash_path
            ))

            self.plugins.on_file_deleted(path)
            logger.info(f"Deleted {path} (moved to trash)")

        except (TFMPathNotFoundError, TFMPermissionError):
            raise
        except PermissionError as e:
            raise TFMPermissionError(str(path), str(e))
        except Exception as e:
            logger.error(f"Delete error: {e}")
            raise
    
    async def create_directory(self, path: Union[str, Path], exist_ok: bool = False) -> None:
        """
        Create a new directory.
        """
        path = Path(path)
        try:
            existed_before = path.exists()
            await asyncio.to_thread(path.mkdir, parents=True, exist_ok=exist_ok)

            if not existed_before:
                 self.history.log_operation(FileOperation(OperationType.CREATE_DIR, path))

            self.plugins.on_file_added(path)
            logger.info(f"Created directory {path}")

        except FileExistsError:
            raise TFMOperationConflictError(str(path), "Directory already exists")
        except PermissionError as e:
            raise TFMPermissionError(str(path), str(e))
        except Exception as e:
            logger.error(f"Create directory error: {e}")
            raise
    
    async def rename(self, old_path: Union[str, Path], new_name: str) -> None:
        """
        Rename a file or directory.
        """
        old_path = Path(old_path)
        self._ensure_path_exists(old_path)
        
        if any(sep in new_name for sep in [os.sep, os.altsep] if sep) or new_name in ('.', '..'):
            raise ValueError("Invalid new name")

        new_path = old_path.parent / new_name

        if new_path.exists():
            raise TFMOperationConflictError(str(new_path), "Target already exists")

        try:
            await asyncio.to_thread(old_path.rename, new_path)

            self.history.log_operation(FileOperation(OperationType.RENAME, old_path, new_path))
            self.plugins.on_file_deleted(old_path)
            self.plugins.on_file_added(new_path)
            logger.info(f"Renamed {old_path} to {new_name}")

        except (TFMPathNotFoundError, TFMOperationConflictError, TFMPermissionError):
            raise
        except PermissionError as e:
            raise TFMPermissionError(str(old_path), str(e))
        except Exception as e:
            logger.error(f"Rename error: {e}")
            raise
    
    def get_size(self, path: Union[str, Path]) -> int:
        """
        Get the size of a file or directory in bytes.
        Note: This remains synchronous as strictly a read operation,
        but could be made async if scanning large dirs blocks.
        For now we keep it sync as used by getters mostly.
        """
        path = Path(path)
        if path.is_file():
            return path.stat().st_size
        elif path.is_dir():
            return self._get_directory_size(str(path))
        return 0

    def _get_directory_size(self, directory: str) -> int:
        """
        Iteratively calculate directory size using os.scandir.
        """
        total = 0
        for entry in recursive_scan(directory):
            try:
                if entry.is_file(follow_symlinks=True):
                    total += entry.stat(follow_symlinks=True).st_size
            except OSError:
                continue
        return total
    
    @staticmethod
    def format_size(size: Union[int, float]) -> str:
        """Format size in bytes to human-readable format."""
        _size = float(size)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if _size < 1024.0:
                return f"{_size:.1f} {unit}"
            _size /= 1024.0
        return f"{_size:.1f} PB"

    async def undo_last(self) -> str:
        """Undo the last operation."""
        op = self.history.undo_last()
        if not op:
            return "Nothing to undo"
        
        try:
            if op.type == OperationType.MOVE:
                if op.target_path and op.target_path.exists():
                    await asyncio.to_thread(shutil.move, str(op.target_path), str(op.original_path))
                    self.plugins.on_file_deleted(op.target_path)
                    self.plugins.on_file_added(op.original_path)
                    return f"Undid move: {op.target_path} -> {op.original_path}"
                return "Undo failed: Target file not found"

            elif op.type == OperationType.COPY:
                if op.target_path and op.target_path.exists():
                    if op.target_path.is_dir():
                        await asyncio.to_thread(shutil.rmtree, op.target_path)
                    else:
                        await asyncio.to_thread(op.target_path.unlink)
                    self.plugins.on_file_deleted(op.target_path)
                    return f"Undid copy: deleted {op.target_path}"
                return "Undo failed: Target file not found"

            elif op.type == OperationType.DELETE:
                if op.trash_path and op.trash_path.exists():
                    await asyncio.to_thread(shutil.move, str(op.trash_path), str(op.original_path))
                    self.plugins.on_file_added(op.original_path)
                    return f"Undid delete: restored {op.original_path}"
                else:
                    return f"Cannot undo delete: trash file missing {op.trash_path}"

            elif op.type == OperationType.RENAME:
                if op.target_path and op.target_path.exists():
                    await asyncio.to_thread(op.target_path.rename, op.original_path)
                    self.plugins.on_file_deleted(op.target_path)
                    self.plugins.on_file_added(op.original_path)
                    return f"Undid rename: {op.target_path} -> {op.original_path}"
            
            elif op.type == OperationType.CREATE_DIR:
                if op.original_path.exists():
                    await asyncio.to_thread(op.original_path.rmdir)
                    self.plugins.on_file_deleted(op.original_path)
                    return f"Undid create dir: {op.original_path}"

        except Exception as e:
            logger.error(f"Undo error: {e}")
            return f"Undo failed: {e}"

        return "Undo operation unknown"

    async def redo_last(self) -> str:
        """Redo the last undone operation."""
        op = self.history.redo_last()
        if not op:
            return "Nothing to redo"

        try:
            if op.type == OperationType.MOVE:
                if op.original_path.exists():
                    await asyncio.to_thread(shutil.move, str(op.original_path), str(op.target_path))
                    self.plugins.on_file_deleted(op.original_path)
                    self.plugins.on_file_added(op.target_path)
                    return f"Redid move: {op.original_path} -> {op.target_path}"

            elif op.type == OperationType.COPY:
                if op.original_path.exists():
                    if op.original_path.is_file():
                        await asyncio.to_thread(shutil.copy2, op.original_path, op.target_path)
                    else:
                        await asyncio.to_thread(shutil.copytree, op.original_path, op.target_path, dirs_exist_ok=True)
                    self.plugins.on_file_added(op.target_path)
                    return f"Redid copy: {op.original_path} -> {op.target_path}"

            elif op.type == OperationType.DELETE:
                if op.original_path.exists():
                    await asyncio.to_thread(shutil.move, str(op.original_path), str(op.trash_path))
                    self.plugins.on_file_deleted(op.original_path)
                    return f"Redid delete: {op.original_path}"

            elif op.type == OperationType.RENAME:
                if op.original_path.exists():
                    await asyncio.to_thread(op.original_path.rename, op.target_path)
                    self.plugins.on_file_deleted(op.original_path)
                    self.plugins.on_file_added(op.target_path)
                    return f"Redid rename: {op.original_path} -> {op.target_path}"

            elif op.type == OperationType.CREATE_DIR:
                if not op.original_path.exists():
                    await asyncio.to_thread(op.original_path.mkdir, parents=True, exist_ok=False)
                    self.plugins.on_file_added(op.original_path)
                    return f"Redid create dir: {op.original_path}"

        except Exception as e:
            logger.error(f"Redo error: {e}")
            return f"Redo failed: {e}"

        return "Redo operation unknown"
