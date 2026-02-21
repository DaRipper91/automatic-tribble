"""
File operations module for copy, move, delete, etc.
"""

import os
import shutil
from pathlib import Path
from typing import Union


class FileOperations:
    """Handles file and directory operations."""

    def _validate_transfer(self, source: Path, destination: Path) -> Path:
        """
        Validate source and destination for copy/move operations.
        
        Args:
            source: Source Path object
            destination: Destination Path object

        Returns:
            Target Path object (destination / source.name)

        Raises:
            FileNotFoundError: If source does not exist
            NotADirectoryError: If destination is not a directory
            FileExistsError: If target already exists
        """
        if not source.exists():
            raise FileNotFoundError(f"Source does not exist: {source}")

        if not destination.is_dir():
            raise NotADirectoryError(f"Destination is not a directory: {destination}")

        target = destination / source.name

        if target.exists():
            raise FileExistsError(f"Destination already exists: {target}")

        return target

    def _ensure_path_exists(self, path: Path, message: str = "Path does not exist") -> None:
        """
        Ensure that a path exists, otherwise raise FileNotFoundError.

        Args:
            path: Path object to check
            message: Custom error message prefix

        Raises:
            FileNotFoundError: If path does not exist
        """
        if not path.exists():
            raise FileNotFoundError(f"{message}: {path}")

    def copy(self, source: Union[str, Path], destination: Union[str, Path]) -> None:
        """
        Copy a file or directory to a destination.

        Args:
            source: Source file or directory path
            destination: Destination directory path
        """
        source = Path(source)
        destination = Path(destination)
        target = self._validate_transfer(source, destination)

        if source.is_file():
            shutil.copy2(source, target)
        elif source.is_dir():
            shutil.copytree(source, target, dirs_exist_ok=True)
    
    def move(self, source: Union[str, Path], destination: Union[str, Path]) -> None:
        """
        Move a file or directory to a destination.
        
        Args:
            source: Source file or directory path
            destination: Destination directory path
        """
        source = Path(source)
        destination = Path(destination)
        target = self._validate_transfer(source, destination)

        shutil.move(str(source), str(target))
    
    def delete(self, path: Union[str, Path]) -> None:
        """
        Delete a file or directory.
        
        Args:
            path: Path to file or directory to delete
        """
        path = Path(path)
        self._ensure_path_exists(path)
        
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
    
    def create_directory(self, path: Union[str, Path]) -> None:
        """
        Create a new directory.
        
        Args:
            path: Path to the new directory
        """
        path = Path(path)
        path.mkdir(parents=True, exist_ok=False)
    
    def rename(self, old_path: Union[str, Path], new_name: str) -> None:
        """
        Rename a file or directory.
        
        Args:
            old_path: Current path of the file or directory
            new_name: New name (not full path)
        """
        old_path = Path(old_path)
        self._ensure_path_exists(old_path)
        
        # Secure against path traversal
        if any(sep in new_name for sep in [os.sep, os.altsep] if sep) or new_name in ('.', '..'):
            raise ValueError("Invalid new name: path separators or reserved names not allowed")

        new_path = old_path.parent / new_name

        if new_path.exists():
            raise FileExistsError(f"Target already exists: {new_path}")

        old_path.rename(new_path)
    
    def get_size(self, path: Union[str, Path]) -> int:
        """
        Get the size of a file or directory in bytes.
        
        Args:
            path: Path to file or directory
            
        Returns:
            Size in bytes
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

        This is significantly faster than Path.rglob() for large directory trees
        because it avoids creating Path objects for every entry and uses
        os.scandir's cached stat results where possible.
        """
        total = 0
        stack = [directory]

        while stack:
            current_dir = stack.pop()
            try:
                with os.scandir(current_dir) as it:
                    for entry in it:
                        try:
                            # Use follow_symlinks=True for files to match Path.is_file() behavior
                            if entry.is_file(follow_symlinks=True):
                                total += entry.stat().st_size
                            elif entry.is_dir(follow_symlinks=False):
                                stack.append(entry.path)
                        except OSError:
                            pass
            except OSError:
                pass

        return total
    
    @staticmethod
    def format_size(size: int) -> str:
        """
        Format size in bytes to human-readable format.
        
        Args:
            size: Size in bytes
            
        Returns:
            Formatted string (e.g., "1.5 MB")
        """
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
