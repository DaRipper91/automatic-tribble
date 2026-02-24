"""
Automation features for file organization and management.
"""

import asyncio
import hashlib
from pathlib import Path
from typing import Dict, List, Callable, Optional, Union, Iterator, Set
from datetime import datetime
from enum import Enum, auto
import os
from .utils import recursive_scan
from .config import ConfigManager
from .file_operations import FileOperations
from .logger import get_logger

logger = get_logger("automation")


# Constants
SECONDS_PER_DAY = 86400

class ConflictResolutionStrategy(Enum):
    KEEP_NEWEST = auto()
    KEEP_OLDEST = auto()
    KEEP_LARGEST = auto()
    KEEP_SMALLEST = auto()
    INTERACTIVE = auto()


class FileOrganizer:
    """Handles automated file organization tasks."""

    def __init__(self):
        self.organized_files: Dict[str, List[Path]] = {}
        self.config_manager = ConfigManager()
        self.file_ops = FileOperations()
        self._load_categories()

    def _load_categories(self):
        """Load categories from config and build extension map."""
        self.categories = self.config_manager.load_categories()
        self.extension_map = self._build_extension_map(self.categories)
    
    async def organize_by_type(
        self,
        source_dir: Path,
        target_dir: Path,
        categories: Optional[Dict[str, List[str]]] = None,
        move: bool = False,
        dry_run: bool = False,
        progress_queue: Optional[asyncio.Queue] = None
    ) -> Dict[str, List[Path]]:
        """
        Organize files by type into categorized subdirectories.
        """
        if categories is None:
            self._load_categories()
            extension_map = self.extension_map
        else:
            extension_map = self._build_extension_map(categories)

        return await self._organize_generic(
            source_dir,
            target_dir,
            lambda p: self._get_file_category(p, extension_map),
            move,
            dry_run,
            progress_queue
        )
    
    async def organize_by_date(
        self,
        source_dir: Path,
        target_dir: Path,
        date_format: str = "%Y/%m",
        move: bool = False,
        dry_run: bool = False,
        progress_queue: Optional[asyncio.Queue] = None
    ) -> Dict[str, List[Path]]:
        """
        Organize files by modification date into date-based subdirectories.
        """
        def get_date_key(file_path: Path) -> str:
            mtime = file_path.stat().st_mtime
            date = datetime.fromtimestamp(mtime)
            return date.strftime(date_format)

        return await self._organize_generic(
            source_dir,
            target_dir,
            get_date_key,
            move,
            dry_run,
            progress_queue
        )

    async def _organize_generic(
        self,
        source_dir: Path,
        target_dir: Path,
        key_func: Callable[[Path], Optional[str]],
        move: bool,
        dry_run: bool = False,
        progress_queue: Optional[asyncio.Queue] = None
    ) -> Dict[str, List[Path]]:
        """
        Generic method to organize files based on a key generation function.
        """
        organized: Dict[str, List[Path]] = {}

        if not dry_run:
            await self.file_ops.create_directory(target_dir, exist_ok=True)

        files = list(source_dir.iterdir())
        used_paths: Set[Path] = set()
        
        for file_path in files:
            if not file_path.is_file():
                continue
            
            key = key_func(file_path)
            if not key:
                continue

            key_dir = target_dir / key
            
            try:
                if not key_dir.resolve().is_relative_to(target_dir.resolve()):
                    continue
            except (ValueError, RuntimeError):
                continue

            if not dry_run and not key_dir.exists():
                await self.file_ops.create_directory(key_dir, exist_ok=True)
            
            target_path = key_dir / file_path.name
            target_path = self._get_unique_path(target_path, used_paths if dry_run else None)

            if dry_run:
                used_paths.add(target_path)
            
            try:
                if not dry_run:
                    if move:
                        await self.file_ops.move(file_path, target_path)
                    else:
                        await self.file_ops.copy(file_path, target_path)

                    self.file_ops.plugins.on_organize(file_path, target_path)

                if key not in organized:
                    organized[key] = []
                organized[key].append(target_path)

            except Exception as e:
                logger.warning(f"Failed to organize {file_path}: {e}")
            
            if progress_queue:
                progress_queue.put_nowait(file_path)

        self.organized_files = organized
        return organized
    
    async def cleanup_old_files(
        self,
        directory: Path,
        days_old: int,
        recursive: bool = False,
        dry_run: bool = False,
        progress_queue: Optional[asyncio.Queue] = None
    ) -> List[Path]:
        """
        Remove or identify files older than specified days.
        """
        cutoff_time = datetime.now().timestamp() - (days_old * SECONDS_PER_DAY)
        old_files = []
        
        def collect_files():
            return list(self._iter_files(directory, recursive))

        files = await asyncio.to_thread(collect_files)

        for file_path in files:
            try:
                if file_path.stat().st_mtime < cutoff_time:
                    old_files.append(file_path)
                    if not dry_run:
                        await self.file_ops.delete(file_path)

                    if progress_queue:
                        progress_queue.put_nowait(file_path)
            except OSError as e:
                logger.debug(f"Failed to process {file_path} for cleanup: {e}")
                continue
        
        return old_files
    
    async def find_duplicates(
        self,
        directory: Path,
        recursive: bool = True
    ) -> Dict[str, List[Path]]:
        """
        Find duplicate files based on size and content.
        """
        return await asyncio.to_thread(self._find_duplicates_sync, directory, recursive)

    def _find_duplicates_sync(
        self,
        directory: Path,
        recursive: bool = True
    ) -> Dict[str, List[Path]]:
        """Sync implementation of find_duplicates."""
        # First group by size (quick)
        size_groups: Dict[int, List[Path]] = {}
        
        try:
            entries: Iterator[os.DirEntry[str]]
            if recursive:
                entries = (e for e in recursive_scan(directory) if e.is_file(follow_symlinks=True))
            else:
                try:
                    entries = (e for e in os.scandir(directory) if e.is_file())
                except OSError:
                    entries = iter([])

            for entry in entries:
                try:
                    size = entry.stat().st_size
                    if size not in size_groups:
                        size_groups[size] = []
                    size_groups[size].append(Path(entry.path))
                except OSError:
                    continue
        except (PermissionError, OSError) as e:
            logger.error(f"Error scanning directory for duplicates: {e}")
        
        # Then verify with hash (slower but accurate)
        duplicates: Dict[str, List[Path]] = {}
        
        for size, files in size_groups.items():
            if len(files) < 2:
                continue

            partial_groups: Dict[str, List[Path]] = {}
            for file_path in files:
                try:
                    # Use 64KB for partial hash
                    partial_hash = self._compute_partial_hash(file_path, chunk_size=65536, file_size=size)
                    if partial_hash not in partial_groups:
                        partial_groups[partial_hash] = []
                    partial_groups[partial_hash].append(file_path)
                except OSError as e:
                    logger.debug(f"Failed to compute partial hash for {file_path}: {e}")
                    continue

            for partial_files in partial_groups.values():
                if len(partial_files) < 2:
                    continue

                for file_path in partial_files:
                    try:
                        file_hash = self._compute_file_hash(file_path)
                        if file_hash not in duplicates:
                            duplicates[file_hash] = []
                        duplicates[file_hash].append(file_path)
                    except OSError as e:
                        logger.debug(f"Failed to compute full hash for {file_path}: {e}")
                        continue
        
        result = {
            hash_val: paths for hash_val, paths in duplicates.items()
            if len(paths) > 1
        }
        
        return result

    async def resolve_duplicates(
        self,
        duplicates: Dict[str, List[Path]],
        strategy: ConflictResolutionStrategy,
        progress_queue: Optional[asyncio.Queue] = None
    ) -> List[Path]:
        """
        Resolve duplicates based on strategy.
        Returns list of deleted files.
        """
        deleted_files = []

        for hash_val, paths in duplicates.items():
            if len(paths) < 2:
                continue

            sorted_paths = list(paths)
            try:
                if strategy == ConflictResolutionStrategy.KEEP_NEWEST:
                    sorted_paths.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                elif strategy == ConflictResolutionStrategy.KEEP_OLDEST:
                    sorted_paths.sort(key=lambda p: p.stat().st_mtime)
                elif strategy == ConflictResolutionStrategy.KEEP_LARGEST:
                    sorted_paths.sort(key=lambda p: p.stat().st_size, reverse=True)
                elif strategy == ConflictResolutionStrategy.KEEP_SMALLEST:
                    sorted_paths.sort(key=lambda p: p.stat().st_size)
                elif strategy == ConflictResolutionStrategy.INTERACTIVE:
                    continue
            except OSError:
                continue

            # Keep first, delete rest
            to_delete = sorted_paths[1:]

            for p in to_delete:
                try:
                    await self.file_ops.delete(p)
                    deleted_files.append(p)
                    if progress_queue:
                        progress_queue.put_nowait(p)
                except Exception as e:
                    logger.warning(f"Failed to delete duplicate {p}: {e}")

        return deleted_files

    def _scan_recursive(self, directory: Union[Path, str]):
        """Recursively scan directory using os.scandir."""
        try:
            with os.scandir(directory) as it:
                for entry in it:
                    if entry.is_dir(follow_symlinks=False):
                        yield from self._scan_recursive(entry.path)
                    elif entry.is_file(follow_symlinks=True):
                        yield entry
        except (PermissionError, OSError):
            pass
    
    def _iter_files(self, directory: Path, recursive: bool) -> Iterator[Path]:
        """
        Iterate over files in a directory, optionally recursively.
        """
        if recursive:
            for root, _, files in os.walk(directory):
                root_path = Path(root)
                for file_name in files:
                    yield root_path / file_name
        else:
            for file_path in directory.iterdir():
                if file_path.is_file():
                    yield file_path

    async def batch_rename(
        self,
        directory: Path,
        pattern: str,
        replacement: str,
        recursive: bool = False,
        dry_run: bool = False,
        progress_queue: Optional[asyncio.Queue] = None
    ) -> List[Path]:
        """
        Batch rename files matching a pattern.
        """
        if not pattern:
            raise ValueError("Pattern cannot be empty")

        renamed_files = []
        used_paths: Set[Path] = set()

        def collect_files():
            return list(self._iter_files(directory, recursive))

        files = await asyncio.to_thread(collect_files)

        for file_path in files:
            if pattern in file_path.name:
                new_name = file_path.name.replace(pattern, replacement)

                if any(sep in new_name for sep in [os.sep, os.altsep] if sep) or new_name in ('.', '..'):
                    continue

                new_path = file_path.parent / new_name

                # Check existence (considering dry run simulation)
                exists = new_path.exists()
                if dry_run:
                     if new_path in used_paths:
                         exists = True
                     used_paths.add(new_path)

                if exists and not dry_run:
                     # Rename usually fails if target exists (depending on OS/impl), or overwrites?
                     # FileOperations.rename uses shutil.move or os.rename.
                     # Standard behavior: avoid overwrite unless intended.
                     # Here we skip.
                     logger.warning(f"Skipping rename {file_path} -> {new_name}: Target exists")
                     continue

                try:
                    if not dry_run:
                        await self.file_ops.rename(file_path, new_name)

                    renamed_files.append(new_path)

                    if progress_queue:
                        progress_queue.put_nowait(new_path)
                except Exception as e:
                    logger.warning(f"Failed to rename {file_path} to {new_name}: {e}")
                    continue
        
        return renamed_files
    
    @staticmethod
    def _get_unique_path(target_path: Path, simulated_paths: Optional[Set[Path]] = None) -> Path:
        """
        Generate a unique path by appending a counter if target exists.
        """
        def exists(path):
            if simulated_paths is not None and path in simulated_paths:
                return True
            return path.exists()

        if not exists(target_path):
            return target_path

        stem = target_path.stem
        suffix = target_path.suffix
        parent = target_path.parent
        counter = 1

        while True:
            new_name = f"{stem}_{counter}{suffix}"
            new_path = parent / new_name
            if not exists(new_path):
                return new_path
            counter += 1

    @staticmethod
    def _build_extension_map(categories: Dict[str, List[str]]) -> Dict[str, str]:
        """
        Build an inverted mapping from extensions to categories.
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
        """
        extension = file_path.suffix.lower()
        return extension_map.get(extension)
    
    @staticmethod
    def _compute_file_hash(file_path: Path, chunk_size: int = 8192) -> str:
        """
        Compute SHA256 hash of a file.
        """
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()

    @staticmethod
    def _compute_partial_hash(
        file_path: Path,
        chunk_size: int = 65536,
        file_size: Optional[int] = None
    ) -> str:
        """
        Compute a partial hash of a file using start and end chunks.
        """
        if file_size is None:
            try:
                file_size = file_path.stat().st_size
            except OSError:
                raise

        # If file is small, hash the whole thing
        if file_size <= 2 * chunk_size:
            return FileOrganizer._compute_file_hash(file_path, chunk_size)

        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            # Start
            sha256_hash.update(f.read(chunk_size))

            # End
            f.seek(-chunk_size, os.SEEK_END)
            sha256_hash.update(f.read(chunk_size))

        return sha256_hash.hexdigest()
