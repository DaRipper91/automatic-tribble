import os
import io
import fnmatch
from pathlib import Path
from typing import List, Optional, Union

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
                entries_iter = self._scan_recursive(directory)
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
        
        # Determine case sensitivity for the search text once
        search_term = search_text if case_sensitive else search_text.lower()
        
        # Set of known text extensions for quick check
        text_extensions = {
            ".txt", ".md", ".py", ".js", ".java", ".c", ".cpp", ".h",
            ".json", ".xml", ".html", ".css", ".sh", ".bash", ".yaml",
            ".yml", ".ini", ".cfg", ".conf", ".log", ".csv"
        }

        try:
            # We use os.walk here as it is convenient for simple iteration where we need root
            for root, _, files in os.walk(directory):
                root_path = Path(root)
                
                for file_name in files:
                    if fnmatch.fnmatch(file_name, file_pattern):
                        file_path = root_path / file_name
                        
                        try:
                            # Check extension first
                            is_known_text = file_path.suffix.lower() in text_extensions

                            if is_known_text:
                                # Open as text directly
                                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                                    for line in f:
                                        if not case_sensitive:
                                            line = line.lower()
                                        if search_term in line:
                                            results.append(file_path)
                                            break
                            else:
                                # Not a known extension, check for binary content
                                # Open as binary to check first few bytes
                                with open(file_path, "rb") as f:
                                    chunk = f.read(FILE_TYPE_CHECK_BYTES)
                                    if b"\x00" in chunk:
                                        # Binary file, skip
                                        continue

                                    # It's likely text, rewind and read rest
                                    f.seek(0)

                                    # Wrap the binary stream with TextIOWrapper
                                    # This avoids closing and reopening the file
                                    with io.TextIOWrapper(f, encoding="utf-8", errors="ignore") as text_f:
                                        for line in text_f:
                                            if not case_sensitive:
                                                line = line.lower()
                                            if search_term in line:
                                                results.append(file_path)
                                                break
                        except (IOError, OSError):
                            continue
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
                entries_iter = self._scan_recursive(directory)
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
