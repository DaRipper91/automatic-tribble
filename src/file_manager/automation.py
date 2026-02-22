"""
Automation features for file organization and management.
"""

import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Callable, Optional, Union
from datetime import datetime, timedelta
import os
from .utils import recursive_scan


# Constants
SECONDS_PER_DAY = 86400


class FileOrganizer:
    """Handles automated file organization tasks."""
    
    # Common file type categorizations
    FILE_CATEGORIES = {
        'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico'],
        'videos': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'],
        'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma'],
        'documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'],
        'spreadsheets': ['.xls', '.xlsx', '.csv', '.ods'],
        'presentations': ['.ppt', '.pptx', '.odp'],
        'archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
        'code': ['.py', '.js', '.java', '.c', '.cpp', '.h', '.html', '.css', '.sh'],
        'data': ['.json', '.xml', '.yaml', '.yml', '.sql', '.db'],
    }
    
    # Pre-computed mapping for default categories to enable O(1) lookup
    _DEFAULT_EXTENSION_MAP = {
        ext.lower(): cat
        for cat, exts in FILE_CATEGORIES.items()
        for ext in exts
    }

    def __init__(self):
        self.organized_files: Dict[str, List[Path]] = {}
    
    def organize_by_type(
        self,
        source_dir: Path,
        target_dir: Path,
        categories: Optional[Dict[str, List[str]]] = None,
        move: bool = False
    ) -> Dict[str, List[Path]]:
        """
        Organize files by type into categorized subdirectories.
        
        Args:
            source_dir: Directory containing files to organize
            target_dir: Directory where organized files will be placed
            categories: Custom category definitions (uses default if None)
            move: If True, move files; if False, copy files
            
        Returns:
            Dictionary mapping categories to lists of organized files
        """
        if categories is None:
            extension_map = self._DEFAULT_EXTENSION_MAP
        else:
            extension_map = self._build_extension_map(categories)
            
        return self._organize_generic(
            source_dir,
            target_dir,
            lambda p: self._get_file_category(p, extension_map),
            move
        )
    
    def organize_by_date(
        self,
        source_dir: Path,
        target_dir: Path,
        date_format: str = "%Y/%m",
        move: bool = False
    ) -> Dict[str, List[Path]]:
        """
        Organize files by modification date into date-based subdirectories.
        
        Args:
            source_dir: Directory containing files to organize
            target_dir: Directory where organized files will be placed
            date_format: strftime format for directory names (e.g., "%Y/%m" for Year/Month)
            move: If True, move files; if False, copy files
            
        Returns:
            Dictionary mapping date strings to lists of organized files
        """
        def get_date_key(file_path: Path) -> str:
            mtime = file_path.stat().st_mtime
            date = datetime.fromtimestamp(mtime)
            return date.strftime(date_format)

        return self._organize_generic(
            source_dir,
            target_dir,
            get_date_key,
            move
        )

    def _organize_generic(
        self,
        source_dir: Path,
        target_dir: Path,
        key_func: Callable[[Path], Optional[str]],
        move: bool
    ) -> Dict[str, List[Path]]:
        """
        Generic method to organize files based on a key generation function.

        Args:
            source_dir: Directory containing files to organize
            target_dir: Directory where organized files will be placed
            key_func: Function that takes a file Path and returns a string key (subdirectory) or None
            move: If True, move files; if False, copy files

        Returns:
            Dictionary mapping keys to lists of organized files
        """
        organized = {}
        target_dir.mkdir(parents=True, exist_ok=True)
        
        for file_path in source_dir.iterdir():
            if not file_path.is_file():
                continue
            
            key = key_func(file_path)
            if not key:
                continue

            # Create target directory and secure against path traversal
            key_dir = target_dir / key
            
            try:
                # Resolve paths to handle '..' etc.
                if not key_dir.resolve().is_relative_to(target_dir.resolve()):
                    continue
            except (ValueError, RuntimeError):
                continue

            key_dir.mkdir(parents=True, exist_ok=True)
            
            # Move or copy file
            target_path = key_dir / file_path.name
            target_path = self._get_unique_path(target_path)
            
            if move:
                shutil.move(str(file_path), str(target_path))
            else:
                shutil.copy2(file_path, target_path)
            
            if key not in organized:
                organized[key] = []
            organized[key].append(target_path)

        self.organized_files = organized
        return organized
    
    def cleanup_old_files(
        self,
        directory: Path,
        days_old: int,
        recursive: bool = False,
        dry_run: bool = False
    ) -> List[Path]:
        """
        Remove or identify files older than specified days.
        
        Args:
            directory: Directory to clean
            days_old: Delete files older than this many days
            recursive: Whether to search subdirectories
            dry_run: If True, only list files without deleting
            
        Returns:
            List of files that were (or would be) deleted
        """
        cutoff_time = datetime.now().timestamp() - (days_old * SECONDS_PER_DAY)
        old_files = []
        
        if recursive:
            for root, _, files in os.walk(directory):
                root_path = Path(root)
                for file_name in files:
                    file_path = root_path / file_name
                    if file_path.stat().st_mtime < cutoff_time:
                        old_files.append(file_path)
                        if not dry_run:
                            file_path.unlink()
        else:
            for file_path in directory.iterdir():
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    old_files.append(file_path)
                    if not dry_run:
                        file_path.unlink()
        
        return old_files
    
    def find_duplicates(
        self,
        directory: Path,
        recursive: bool = True
    ) -> Dict[str, List[Path]]:
        """
        Find duplicate files based on size and content.
        
        Args:
            directory: Directory to search
            recursive: Whether to search subdirectories
            
        Returns:
            Dictionary mapping file hashes to lists of duplicate files
        """
        # First group by size (quick)
        size_groups: Dict[int, List[Path]] = {}
        
        try:
            if recursive:
                entries = (e for e in recursive_scan(directory) if e.is_file(follow_symlinks=True))
            else:
                try:
                    entries = (e for e in os.scandir(directory) if e.is_file())
                except OSError:
                    entries = []

            for entry in entries:
                try:
                    # DirEntry.stat() is cached on Windows and faster than Path.stat() generally
                    # Also avoids creating Path object until we know it matches
                    size = entry.stat().st_size
                    if size not in size_groups:
                        size_groups[size] = []
                    # We store Path object here because we need to return it eventually
                    # and keeping DirEntry around might lock resources on some platforms
                    size_groups[size].append(Path(entry.path))
                except OSError:
                    continue
        except (PermissionError, OSError):
            pass
        
        # Then verify with hash (slower but accurate)
        duplicates: Dict[str, List[Path]] = {}
        
        for size, files in size_groups.items():
            if len(files) < 2:
                continue

            # Group by partial hash first to avoid full reads of large files
            partial_groups: Dict[str, List[Path]] = {}
            for file_path in files:
                try:
                    partial_hash = self._compute_partial_hash(file_path, file_size=size)
                    if partial_hash not in partial_groups:
                        partial_groups[partial_hash] = []
                    partial_groups[partial_hash].append(file_path)
                except OSError:
                    continue

            # Check full hash only for files with matching partial hash
            for partial_files in partial_groups.values():
                if len(partial_files) < 2:
                    continue

                for file_path in partial_files:
                    try:
                        file_hash = self._compute_file_hash(file_path)
                        if file_hash not in duplicates:
                            duplicates[file_hash] = []
                        duplicates[file_hash].append(file_path)
                    except OSError:
                        continue
        
        # Filter to only groups with actual duplicates
        result = {
            hash_val: paths for hash_val, paths in duplicates.items()
            if len(paths) > 1
        }
        
        return result

    def batch_rename(
        self,
        directory: Path,
        pattern: str,
        replacement: str,
        recursive: bool = False
    ) -> List[Path]:
        """
        Batch rename files matching a pattern.
        
        Args:
            directory: Directory containing files to rename
            pattern: Text pattern to match in filenames
            replacement: Text to replace pattern with
            recursive: Whether to process subdirectories
            
        Returns:
            List of renamed file paths
        """
        if not pattern:
            raise ValueError("Pattern cannot be empty")

        renamed_files = []
        
        if recursive:
            for root, _, files in os.walk(directory):
                root_path = Path(root)
                for file_name in files:
                    if pattern in file_name:
                        old_path = root_path / file_name
                        new_name = file_name.replace(pattern, replacement)

                        # Secure against path traversal
                        if any(sep in new_name for sep in [os.sep, os.altsep] if sep) or new_name in ('.', '..'):
                            continue

                        new_path = root_path / new_name
                        
                        if not new_path.exists():
                            old_path.rename(new_path)
                            renamed_files.append(new_path)
        else:
            for file_path in directory.iterdir():
                if file_path.is_file() and pattern in file_path.name:
                    new_name = file_path.name.replace(pattern, replacement)

                    # Secure against path traversal
                    if any(sep in new_name for sep in [os.sep, os.altsep] if sep) or new_name in ('.', '..'):
                        continue

                    new_path = file_path.parent / new_name
                    
                    if not new_path.exists():
                        file_path.rename(new_path)
                        renamed_files.append(new_path)
        
        return renamed_files
    
    @staticmethod
    def _get_unique_path(target_path: Path) -> Path:
        """
        Generate a unique path by appending a counter if the path already exists.

        Args:
            target_path: The desired path

        Returns:
            A unique path that does not exist
        """
        if not target_path.exists():
            return target_path

        stem = target_path.stem
        suffix = target_path.suffix
        parent = target_path.parent
        counter = 1

        while True:
            new_name = f"{stem}_{counter}{suffix}"
            new_path = parent / new_name
            if not new_path.exists():
                return new_path
            counter += 1

    @staticmethod
    def _build_extension_map(categories: Dict[str, List[str]]) -> Dict[str, str]:
        """
        Build an inverted mapping from extensions to categories.

        Args:
            categories: Dictionary of categories and their extensions

        Returns:
            Dictionary mapping extensions to category names
        """
        extension_map = {}
        for category, extensions in categories.items():
            for ext in extensions:
                extension_map[ext.lower()] = category
        return extension_map

    @staticmethod
    def _get_file_category(
        file_path: Path,
        extension_map: Dict[str, str]
    ) -> Optional[str]:
        """
        Determine the category of a file based on its extension.
        
        Args:
            file_path: Path to the file
            extension_map: Mapping of extensions to categories
            
        Returns:
            Category name or None if no match
        """
        extension = file_path.suffix.lower()
        return extension_map.get(extension)
    
    @staticmethod
    def _compute_file_hash(file_path: Path, chunk_size: int = 8192) -> str:
        """
        Compute SHA256 hash of a file.
        
        Args:
            file_path: Path to the file
            chunk_size: Size of chunks to read
            
        Returns:
            Hex digest of the file hash
        """
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()

    @staticmethod
    def _compute_partial_hash(
        file_path: Path,
        chunk_size: int = 8192,
        file_size: Optional[int] = None
    ) -> str:
        """
        Compute a partial hash of a file using start, middle, and end chunks.

        Args:
            file_path: Path to the file
            chunk_size: Size of chunks to read
            file_size: Size of file if known (avoids stat call)

        Returns:
            Hex digest of the partial hash
        """
        if file_size is None:
            try:
                file_size = file_path.stat().st_size
            except OSError:
                # Fallback to empty string or raise error, but caller handles OSError
                raise

        # If file is small, hash the whole thing
        if file_size <= 3 * chunk_size:
            return FileOrganizer._compute_file_hash(file_path, chunk_size)

        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            # Start
            sha256_hash.update(f.read(chunk_size))

            # Middle
            f.seek(file_size // 2 - chunk_size // 2)
            sha256_hash.update(f.read(chunk_size))

            # End
            f.seek(-chunk_size, os.SEEK_END)
            sha256_hash.update(f.read(chunk_size))

        return sha256_hash.hexdigest()
