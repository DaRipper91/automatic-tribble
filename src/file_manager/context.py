"""
Directory Context Builder for AI Prompts.
"""

import os
import time
import heapq
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict

@dataclass
class DirectoryStats:
    total_files: int
    total_size: int
    total_size_human: str
    category_counts: Dict[str, int]
    oldest_file: str
    newest_file: str
    top_largest_files: List[Dict[str, Any]]
    duplicate_groups: int

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

        # Heap for top 5 largest files: stores (size, name)
        largest_files_heap: List[Tuple[int, str]] = []

        # Simple duplicate detection based on size
        size_map: Dict[int, int] = {}

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

                    # Track largest files
                    if len(largest_files_heap) < 5:
                        heapq.heappush(largest_files_heap, (size, entry.name))
                    else:
                        heapq.heappushpop(largest_files_heap, (size, entry.name))

                    # Track potential duplicates by size
                    size_map[size] = size_map.get(size, 0) + 1

        except (PermissionError, OSError):
            pass

        # Sort largest files descending
        largest_files = sorted(largest_files_heap, key=lambda x: x[0], reverse=True)
        formatted_largest = [
            {"name": name, "size_human": self._human_size(size)}
            for size, name in largest_files
        ]

        # Estimate duplicate groups (files with same size > 1)
        duplicate_groups = sum(1 for count in size_map.values() if count > 1)

        return DirectoryStats(
            total_files=total_files,
            total_size=total_size,
            total_size_human=self._human_size(total_size),
            category_counts=categories,
            oldest_file=oldest_name,
            newest_file=newest_name,
            top_largest_files=formatted_largest,
            duplicate_groups=duplicate_groups
        )

    def _human_size(self, size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
