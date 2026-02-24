import os
import fnmatch
from pathlib import Path
from typing import List, Optional, Union, Iterator
from .utils import recursive_scan
from .plugins.registry import PluginRegistry
from .tags import TagManager

FILE_TYPE_CHECK_BYTES = 1024

class FileSearcher:
    """Class for searching files."""
    
    def __init__(self):
        self.results: List[Path] = []
        self.plugins = PluginRegistry()
        self.plugins.load_plugins()
        self.tag_manager = TagManager()
    
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
        results: List[Path] = []
        
        if not case_sensitive:
            pattern = pattern.lower()
        
        try:
            entries_iter: Iterator[os.DirEntry[str]]
            if recursive:
                entries_iter = recursive_scan(directory)
            else:
                entries_iter = self._scandir_safe(directory)

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
        self.plugins.on_search_complete(pattern, results)
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
        results: List[Path] = []
        search_term = search_text if case_sensitive else search_text.lower()
        
        if not search_term:
            return []

        try:
            # Iterate over all files recursively
            for entry in recursive_scan(directory):
                try:
                    if not entry.is_file(follow_symlinks=False):
                        continue

                    if not fnmatch.fnmatch(entry.name, file_pattern):
                        continue

                    file_path = Path(entry.path)

                    # Check if text file
                    if not self._is_text_file(file_path):
                        continue

                    # Check content
                    if self._file_contains_term(file_path, search_term, case_sensitive):
                        results.append(file_path)

                except OSError:
                    continue

        except (PermissionError, OSError):
            pass
        
        self.results = results
        self.plugins.on_search_complete(search_text, results)
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
        results: List[Path] = []
        
        try:
            entries_iter: Iterator[os.DirEntry[str]]
            if recursive:
                entries_iter = recursive_scan(directory)
            else:
                entries_iter = self._scandir_safe(directory)

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
        size_range = f"{min_size}-{max_size}"
        self.plugins.on_search_complete(f"size:{size_range}", results)
        return results

    def search_by_tag(self, tag: str) -> List[Path]:
        """Search for files with a specific tag."""
        results = self.tag_manager.search_by_tag(tag)
        self.results = results
        return results

    def _scandir_safe(self, directory: Union[Path, str]) -> Iterator[os.DirEntry[str]]:
        """Safe wrapper around os.scandir that yields entries."""
        try:
            with os.scandir(str(directory)) as it:
                for entry in it:
                    yield entry
        except (PermissionError, OSError):
            return

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
                if not chunk:
                    return True # Empty file is text
                if b"\x00" in chunk:
                    return False
                return True
        except (IOError, OSError):
            return False
