"""
Context builder for AI integration.
Gathers directory statistics and metadata to provide context for AI operations.
"""

import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from .utils import recursive_scan
from .automation import FileOrganizer

class DirectoryContextBuilder:
    """Builds context information about a directory."""

    def __init__(self, directory: Path):
        self.directory = directory
        self.stats: Dict[str, Any] = {}
        self._last_scan_time = 0
        self._cache_duration = 60  # seconds

    def get_context(self) -> Dict[str, Any]:
        """
        Get the context for the directory.
        Uses cached data if available and fresh.
        """
        if time.time() - self._last_scan_time < self._cache_duration and self.stats:
            return self.stats

        self._scan_directory()
        return self.stats

    def _scan_directory(self) -> None:
        """Perform a lightweight scan of the directory."""
        file_count = 0
        total_size = 0
        categories: Dict[str, int] = {}
        oldest_file: Optional[tuple[float, str]] = None
        newest_file: Optional[tuple[float, str]] = None
        largest_files: List[tuple[int, str]] = []

        # Use FileOrganizer categories for consistent classification
        extension_map = FileOrganizer._DEFAULT_EXTENSION_MAP

        try:
            for entry in recursive_scan(self.directory):
                if not entry.is_file(follow_symlinks=True):
                    continue

                try:
                    stat = entry.stat()
                    size = stat.st_size
                    mtime = stat.st_mtime
                    path = entry.path
                    name = entry.name

                    file_count += 1
                    total_size += size

                    # Category
                    ext = Path(name).suffix.lower()
                    category = extension_map.get(ext, 'other')
                    categories[category] = categories.get(category, 0) + 1

                    # Oldest/Newest
                    if oldest_file is None or mtime < oldest_file[0]:
                        oldest_file = (mtime, path)
                    if newest_file is None or mtime > newest_file[0]:
                        newest_file = (mtime, path)

                    # Largest files (keep top 5)
                    largest_files.append((size, path))
                    largest_files.sort(key=lambda x: x[0], reverse=True)
                    largest_files = largest_files[:5]

                except (OSError, PermissionError):
                    continue

        except (OSError, PermissionError):
            pass

        self.stats = {
            "path": str(self.directory),
            "file_count": file_count,
            "total_size_bytes": total_size,
            "categories": categories,
            "oldest_file": oldest_file[1] if oldest_file else None,
            "oldest_file_date": datetime.fromtimestamp(oldest_file[0]).isoformat() if oldest_file else None,
            "newest_file": newest_file[1] if newest_file else None,
            "newest_file_date": datetime.fromtimestamp(newest_file[0]).isoformat() if newest_file else None,
            "largest_files": [f[1] for f in largest_files],
            "os": os.name,
            "scan_time": datetime.now().isoformat()
        }
        self._last_scan_time = time.time()
