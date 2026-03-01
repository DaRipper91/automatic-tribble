"""
Directory Context Builder for AI Prompts.
"""

import os
import time
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass, asdict

@dataclass
class DirectoryStats:
    total_files: int
    total_size: int
    total_size_human: str
    category_counts: Dict[str, int]
    oldest_file: str
    newest_file: str

class DirectoryContextBuilder:
    """Builds and caches directory statistics for AI context."""

    def __init__(self, cache_ttl: int = 60):
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get_context(self, directory: Path) -> Dict[str, Any]:
        """
        Get the context for a directory, using cache if available.
        """
        path_str = str(directory.resolve())
        now = time.time()

        if path_str in self._cache:
            entry = self._cache[path_str]
            if now - entry["timestamp"] < self.cache_ttl:
                return entry["data"]

        # Build context
        stats = self._scan_directory(directory)
        context = asdict(stats)

        self._cache[path_str] = {
            "timestamp": now,
            "data": context
        }
        return context

    def _scan_directory(self, directory: Path) -> DirectoryStats:
        """
        Scan directory and compute statistics.
        """
        total_files = 0
        total_size = 0
        categories: Dict[str, int] = {}
        oldest_ts = float('inf')
        newest_ts = 0.0
        oldest_name = "None"
        newest_name = "None"

        try:
            for entry in os.scandir(directory):
                if entry.is_file():
                    total_files += 1
                    stat = entry.stat()
                    size = stat.st_size
                    mtime = stat.st_mtime

                    total_size += size

                    ext = Path(entry.name).suffix.lower() or "no_ext"
                    categories[ext] = categories.get(ext, 0) + 1

                    if mtime < oldest_ts:
                        oldest_ts = mtime
                        oldest_name = entry.name
                    if mtime > newest_ts:
                        newest_ts = mtime
                        newest_name = entry.name

        except (PermissionError, OSError):
            pass

        return DirectoryStats(
            total_files=total_files,
            total_size=total_size,
            total_size_human=self._human_size(total_size),
            category_counts=categories,
            oldest_file=oldest_name,
            newest_file=newest_name
        )

    def _human_size(self, size: int) -> str:
        current_size = float(size)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if current_size < 1024.0:
                return f"{current_size:.1f} {unit}"
            current_size /= 1024.0
        return f"{current_size:.1f} PB"
