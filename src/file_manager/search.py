import os
import io
import fnmatch
from pathlib import Path
from typing import List, Optional, Union
from .utils import recursive_scan
from .tags import TagManager

FILE_TYPE_CHECK_BYTES = 1024

class FileSearcher:
    """Class for searching files."""
    
    def __init__(self):
        self.results = []
        self.tag_manager = TagManager()

    def search_by_tag(self, tag: str) -> List[Path]:
        """Search for files with a specific tag."""
        results = self.tag_manager.get_files_by_tag(tag)
        self.results = results
        return results
    
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
        
        # Set of known text extensions for quick check
        text_extensions = {
            ".txt", ".md", ".py", ".js", ".java", ".c", ".cpp", ".h",
            ".json", ".xml", ".html", ".css", ".sh", ".bash", ".yaml",
            ".yml", ".ini", ".cfg", ".conf", ".log", ".csv"
        }
        search_len = len(search_term)
        if search_len == 0:
            return []

        chunk_size = 1024 * 1024 # 1MB

        try:
            stack = [str(directory)]
            while stack:
                current_dir = stack.pop()
                try:
                    with os.scandir(current_dir) as it:
                        for entry in it:
                            try:
                                if entry.is_dir(follow_symlinks=False):
                                    stack.append(entry.path)
                                    continue

                                if not entry.is_file():
                                    continue

                                if fnmatch.fnmatch(entry.name, file_pattern):
                                    file_path = Path(entry.path)

                                    # Check extension first
                                    is_known_text = file_path.suffix.lower() in text_extensions

                                    if is_known_text:
                                        try:
                                            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                                                for line in f:
                                                    if not case_sensitive:
                                                        line = line.lower()
                                                    if search_term in line:
                                                        results.append(file_path)
                                                        break
                                        except (IOError, OSError):
                                            pass
                                    else:
                                        # Not a known extension, check for binary content
                                        try:
                                            with open(file_path, "rb") as f:
                                                chunk = f.read(FILE_TYPE_CHECK_BYTES)
                                                if b"\x00" in chunk:
                                                    # Binary file, skip
                                                    continue

                                                # It's likely text, rewind and read rest
                                                f.seek(0)

                                                # Check if we should use overlap search or line-by-line
                                                # The optimized stack implementation used chunk-based overlap search for large files?
                                                # The previous code had a complex chunk reading loop inside the stack loop.
                                                # I will restore that logic.

                                                with open(file_path, "r", encoding="utf-8", errors="ignore") as text_f:
                                                     overlap = ""
                                                     found = False
                                                     while True:
                                                         chunk = text_f.read(chunk_size)
                                                         if not chunk:
                                                             break

                                                         search_chunk = chunk if case_sensitive else chunk.lower()

                                                         if search_term in search_chunk:
                                                             results.append(file_path)
                                                             found = True
                                                             break

                                                         if overlap:
                                                             boundary = overlap + search_chunk[:search_len - 1]
                                                             if search_term in boundary:
                                                                 results.append(file_path)
                                                                 found = True
                                                                 break

                                                         if len(search_chunk) >= search_len - 1:
                                                             overlap = search_chunk[-(search_len - 1):]
                                                         else:
                                                             overlap += search_chunk

                                                     if found:
                                                         continue

                                        except (IOError, OSError):
                                            pass

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

    def _scan_recursive(self, directory: Union[Path, str]):
        """Recursively scan directory using os.scandir (iterative stack-based)."""
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
