"""
Search functionality for finding files and directories.
"""

import os
from pathlib import Path
from typing import List, Optional
import fnmatch


# Constants
FILE_TYPE_CHECK_BYTES = 512


class FileSearcher:
    """Handles file and directory searching."""
    
    def __init__(self):
        self.results: List[Path] = []
    
    def search_by_name(
        self,
        directory: Path,
        pattern: str,
        recursive: bool = True,
        case_sensitive: bool = False
    ) -> List[Path]:
        """
        Search for files and directories by name pattern.
        
        Args:
            directory: Directory to search in
            pattern: Name pattern (supports wildcards like *.txt)
            recursive: Whether to search subdirectories
            case_sensitive: Whether search should be case sensitive
            
        Returns:
            List of matching paths
        """
        results = []
        
        if not case_sensitive:
            pattern = pattern.lower()
        
        try:
            if recursive:
                for root, dirs, files in os.walk(directory):
                    root_path = Path(root)
                    
                    # Check directories
                    for dir_name in dirs:
                        name = dir_name if case_sensitive else dir_name.lower()
                        if fnmatch.fnmatch(name, pattern):
                            results.append(root_path / dir_name)
                    
                    # Check files
                    for file_name in files:
                        name = file_name if case_sensitive else file_name.lower()
                        if fnmatch.fnmatch(name, pattern):
                            results.append(root_path / file_name)
            else:
                # Non-recursive search
                for item in directory.iterdir():
                    name = item.name if case_sensitive else item.name.lower()
                    if fnmatch.fnmatch(name, pattern):
                        results.append(item)
        except PermissionError:
            # Skip directories we don't have permission to read
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
        
        Args:
            directory: Directory to search in
            search_text: Text to search for in files
            file_pattern: File name pattern to limit search
            case_sensitive: Whether search should be case sensitive
            
        Returns:
            List of files containing the search text
        """
        results = []
        
        if not case_sensitive:
            search_text = search_text.lower()
        
        try:
            for root, _, files in os.walk(directory):
                root_path = Path(root)
                
                for file_name in files:
                    if fnmatch.fnmatch(file_name, file_pattern):
                        file_path = root_path / file_name
                        
                        # Only search text files
                        if self._is_text_file(file_path):
                            try:
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    # Optimization: Read in chunks to avoid loading large files into memory
                                    # Use a chunk size that is reasonably large (64KB) but small enough to be memory efficient
                                    # Ensure chunk size is larger than search text to simplify logic
                                    chunk_size = max(64 * 1024, len(search_text) * 2)
                                    overlap = len(search_text) - 1
                                    buffer = ""
                                    
                                    while True:
                                        chunk = f.read(chunk_size)
                                        if not chunk:
                                            break

                                        # Combine overlap from previous chunk with current chunk
                                        current_haystack = buffer + chunk
                                        if not case_sensitive:
                                            current_haystack_search = current_haystack.lower()
                                        else:
                                            current_haystack_search = current_haystack

                                        if search_text in current_haystack_search:
                                            results.append(file_path)
                                            break

                                        # Prepare overlap for next iteration
                                        if overlap > 0:
                                            buffer = current_haystack[-overlap:]
                                        else:
                                            buffer = ""
                            except (IOError, UnicodeDecodeError):
                                # Skip files we can't read
                                continue
        except PermissionError:
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
        
        Args:
            directory: Directory to search in
            min_size: Minimum file size in bytes (None for no minimum)
            max_size: Maximum file size in bytes (None for no maximum)
            recursive: Whether to search subdirectories
            
        Returns:
            List of files matching the size criteria
        """
        results = []
        
        try:
            if recursive:
                for root, _, files in os.walk(directory):
                    root_path = Path(root)
                    
                    for file_name in files:
                        file_path = root_path / file_name
                        try:
                            size = file_path.stat().st_size
                            
                            if min_size is not None and size < min_size:
                                continue
                            if max_size is not None and size > max_size:
                                continue
                            
                            results.append(file_path)
                        except OSError:
                            continue
            else:
                for item in directory.iterdir():
                    if item.is_file():
                        try:
                            size = item.stat().st_size
                            
                            if min_size is not None and size < min_size:
                                continue
                            if max_size is not None and size > max_size:
                                continue
                            
                            results.append(item)
                        except OSError:
                            continue
        except PermissionError:
            pass
        
        self.results = results
        return results
    
    @staticmethod
    def _is_text_file(file_path: Path) -> bool:
        """
        Check if a file is likely a text file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file appears to be text, False otherwise
        """
        # Check by extension
        text_extensions = {
            '.txt', '.md', '.py', '.js', '.java', '.c', '.cpp', '.h',
            '.json', '.xml', '.html', '.css', '.sh', '.bash', '.yaml',
            '.yml', '.ini', '.cfg', '.conf', '.log', '.csv'
        }
        
        if file_path.suffix.lower() in text_extensions:
            return True
        
        # Try reading first few bytes
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(FILE_TYPE_CHECK_BYTES)
                # Check for null bytes (common in binary files)
                if b'\x00' in chunk:
                    return False
                return True
        except (IOError, OSError):
            return False
