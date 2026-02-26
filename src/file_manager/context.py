"""
Directory Context Builder for AI Prompts.
"""

import os
import time
import heapq
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class FileInfo:
    name: str
    size: str

@dataclass
class DirectoryStats:
    total_files: int
    total_size: int
    total_size_human: str
    category_counts: Dict[str, int]
    oldest_file: str
    newest_file: str
    top_largest_files: List[FileInfo]
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

        # Use a min-heap to keep track of top 5 largest files (size, name)
        # We store (size, name) so heap is ordered by size
        largest_files_heap: List[Any] = []

        # For duplicate detection (size -> count)
        size_counts: Dict[int, int] = {}

        try:
            for entry in os.scandir(directory):
                if entry.is_file():
                    total_files += 1
                    try:
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

                        # Top 5 largest
                        heapq.heappush(largest_files_heap, (size, entry.name))
                        if len(largest_files_heap) > 5:
                            heapq.heappop(largest_files_heap)

                        # Duplicate check (simple size-based)
                        size_counts[size] = size_counts.get(size, 0) + 1

                    except OSError:
                        continue

        except (PermissionError, OSError):
            pass

        # Process largest files (sort descending)
        largest_files_heap.sort(key=lambda x: x[0], reverse=True)
        top_largest = [
            FileInfo(name=name, size=self._human_size(size))
            for size, name in largest_files_heap
        ]

        # Count duplicate groups (files with same size > 1)
        duplicate_groups = sum(1 for count in size_counts.values() if count > 1)

        return DirectoryStats(
            total_files=total_files,
            total_size=total_size,
            total_size_human=self._human_size(total_size),
            category_counts=categories,
            oldest_file=oldest_name,
            newest_file=newest_name,
            top_largest_files=top_largest,
            duplicate_groups=duplicate_groups
        )

    def _human_size(self, size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
