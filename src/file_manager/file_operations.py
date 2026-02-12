"""
File operations module for copy, move, delete, etc.
"""

import os
import shutil
from pathlib import Path
from typing import Union


class FileOperations:
    """Handles file and directory operations."""
    
    def copy(self, source: Union[str, Path], destination: Union[str, Path]) -> None:
        """
        Copy a file or directory to a destination.
        
        Args:
            source: Source file or directory path
            destination: Destination directory path
        """
        source = Path(source)
        destination = Path(destination)
        
        if not source.exists():
            raise FileNotFoundError(f"Source does not exist: {source}")
        
        if not destination.is_dir():
            raise NotADirectoryError(f"Destination is not a directory: {destination}")
        
        target = destination / source.name
        
        if target.exists():
            raise FileExistsError(f"Destination already exists: {target}")

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
        
        if not source.exists():
            raise FileNotFoundError(f"Source does not exist: {source}")
        
        if not destination.is_dir():
            raise NotADirectoryError(f"Destination is not a directory: {destination}")
        
        target = destination / source.name

        if target.exists():
            raise FileExistsError(f"Destination already exists: {target}")

        shutil.move(str(source), str(target))
    
    def delete(self, path: Union[str, Path]) -> None:
        """
        Delete a file or directory.
        
        Args:
            path: Path to file or directory to delete
        """
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")
        
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
        
        if not old_path.exists():
            raise FileNotFoundError(f"Path does not exist: {old_path}")
        
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
            total = 0
            for item in path.rglob("*"):
                if item.is_file():
                    total += item.stat().st_size
            return total
        return 0
    
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
