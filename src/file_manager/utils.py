import shutil
import os
from pathlib import Path
from typing import Optional, Union, Generator

def format_size(size_bytes: int) -> str:
    """Format size in bytes to human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

def find_gemini_executable() -> Optional[str]:
    """
    Finds the path to the gemini executable.
    Checks for 'gemini' and 'gemini-cli-termux'.
    """
    # Check for 'gemini' first (standard install)
    gemini_path = shutil.which("gemini")
    if gemini_path:
        return gemini_path

    # Check for 'gemini-cli-termux' (explicit package name)
    gemini_path = shutil.which("gemini-cli-termux")
    if gemini_path:
        return gemini_path

    return None

def recursive_scan(directory: Union[Path, str]) -> Generator[os.DirEntry, None, None]:
    """
    Recursively scan directory using os.scandir (iterative stack-based).
    Yields os.DirEntry objects for all files and directories found.
    """
    stack = [str(directory)]
    while stack:
        current_dir = stack.pop()
        try:
            with os.scandir(current_dir) as it:
                for entry in it:
                    yield entry
                    if entry.is_dir(follow_symlinks=False):
                        stack.append(entry.path)
        except (PermissionError, OSError):
            pass
