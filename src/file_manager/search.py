import os
import fnmatch
from pathlib import Path
from typing import List, Optional, Union
from .utils import recursive_scan

FILE_TYPE_CHECK_BYTES = 1024

class FileSearcher:
    """Class for searching files."""
    
    def __init__(self):
        self.results = []
    
    def search_by_name(
        self,
        directory: Path,
        pattern: str,
        recursive: bool = True,
        case_sensitive: bool = False
    ) -> List[Path]:
        """
        Search for files and directories by name pattern.
        """
        results = []
        
        if not case_sensitive:
            pattern = pattern.lower()
        
        try:
            if recursive:
                # Use list() to force iteration and catch errors early if any
                entries_iter = recursive_scan(directory)
            else:
                entries_iter = os.scandir(directory)

            for entry in entries_iter:
                try:
                    name = entry.name
                    check_name = name if case_sensitive else name.lower()

                    if fnmatch.fnmatch(check_name, pattern):
                        results.append(Path(entry.path))
                except OSError:
                    continue

        except (PermissionError, OSError):
            pass
        
        self.results = results
        return results

    def search_by_content(
        self,
        directory: Path,
        search_text: str,
        file_pattern: str = "*",
        case_sensitive: bool = False
    ) -> List[Path]:
        """
        Search for files containing specific text.
        """
        results = []
        search_term = search_text if case_sensitive else search_text.lower()
        search_len = len(search_term)
        if search_len == 0:
            return []

        chunk_size = 1024 * 1024 # 1MB

        try:
            # We use os.walk here as it is convenient for simple iteration where we need root
            for root, _, files in os.walk(directory):
                root_path = Path(root)
                
                for file_name in files:
                    if fnmatch.fnmatch(file_name, file_pattern):
                        file_path = root_path / file_name
                        
                        if self._is_text_file(file_path):
                            if self._file_contains_term(file_path, search_term, case_sensitive):
                                results.append(file_path)
            stack = [str(directory)]
            while stack:
                current_dir = stack.pop()
                try:
                    with os.scandir(current_dir) as it:
                        for entry in it:
                            try:
                                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                                    overlap = ""
                                    while True:
                                        chunk = f.read(chunk_size)
                                        if not chunk:
                                            break

                                        search_chunk = chunk if case_sensitive else chunk.lower()

                                        if search_term in search_chunk:
                                            results.append(file_path)
                                            break

                                        # Check boundary
                                        if overlap:
                                            # Combine overlap from previous chunk with start of current chunk
                                            # We only need enough from current chunk to complete a potential match starting in overlap
                                            boundary = overlap + search_chunk[:search_len - 1]
                                            if search_term in boundary:
                                                results.append(file_path)
                                                break

                                        # Update overlap for next iteration
                                        # We need the last (search_len - 1) chars from the current chunk
                                        if len(search_chunk) >= search_len - 1:
                                            overlap = search_chunk[-(search_len - 1):]
                                        else:
                                            # If chunk is tiny, append to overlap
                                            overlap += search_chunk
                            except (IOError, OSError):
                                if entry.is_dir(follow_symlinks=False):
                                    stack.append(entry.path)
                                    continue

                                if not entry.is_file():
                                    continue

                                if fnmatch.fnmatch(entry.name, file_pattern):
                                    file_path = Path(entry.path)

                                    if self._is_text_file(file_path):
                                        try:
                                            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                                                # Simple line-by-line search for now
                                                for line in f:
                                                    if not case_sensitive:
                                                        line = line.lower()
                                                    if search_term in line:
                                                        results.append(file_path)
                                                        break
                                        except (IOError, OSError):
                                            continue
                            except OSError:
                                continue
                except (PermissionError, OSError):
                    pass
        except (PermissionError, OSError):
            pass
        
        self.results = results
        return results

    def search_by_size(
        self,
        directory: Path,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
        recursive: bool = True
    ) -> List[Path]:
        """
        Search for files by size range.
        """
        results = []
        
        try:
            if recursive:
                entries_iter = recursive_scan(directory)
            else:
                entries_iter = os.scandir(directory)

            for entry in entries_iter:
                try:
                    if not entry.is_file(follow_symlinks=True):
                        continue

                    size = entry.stat().st_size

                    if min_size is not None and size < min_size:
                        continue
                    if max_size is not None and size > max_size:
                        continue

                    results.append(Path(entry.path))
                except OSError:
                    continue
        except (PermissionError, OSError):
            pass

        self.results = results
        return results

    @staticmethod
    def _file_contains_term(file_path: Path, search_term: str, case_sensitive: bool) -> bool:
        """Check if a file contains the search term."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if not case_sensitive:
                        line = line.lower()
                    if search_term in line:
                        return True
        except (IOError, OSError):
            pass
        return False

    @staticmethod
    def _is_text_file(file_path: Path) -> bool:
        """Check if a file is likely a text file."""
        text_extensions = {
            ".txt", ".md", ".py", ".js", ".java", ".c", ".cpp", ".h",
            ".json", ".xml", ".html", ".css", ".sh", ".bash", ".yaml",
            ".yml", ".ini", ".cfg", ".conf", ".log", ".csv"
        }
        
        if file_path.suffix.lower() in text_extensions:
            return True

        try:
            with open(file_path, "rb") as f:
                chunk = f.read(FILE_TYPE_CHECK_BYTES)
                if b"\x00" in chunk:
                    return False
                return True
        except (IOError, OSError):
            return False
