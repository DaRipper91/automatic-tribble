import os
import time
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class DirectoryStats:
    total_files: int
    total_size: int
    total_size_human: str
    category_counts: Dict[str, int]
    oldest_file: str
    newest_file: str
    top_5_largest: List[str]
    duplicate_groups: int

class DirectoryContextBuilder:
    """Builds and caches directory statistics for AI context."""
    
    def __init__(self):
        self.cache: Dict[Path, Dict[str, Any]] = {}

    def get_context(self, directory: Path) -> str:
        """Get a string representation of the directory context."""
        stats = self._scan_directory(directory)
        
        context = [
            f"Current Directory: {directory}",
            f"Total Files: {stats.total_files}",
            f"Total Size: {stats.total_size_human}",
            f"Top 5 Largest Files: {', '.join(stats.top_5_largest)}",
            f"Duplicate Groups: {stats.duplicate_groups}",
            "File Categories:"
        ]
        
        for ext, count in stats.category_counts.items():
            context.append(f"  - {ext}: {count}")
            
        context.append(f"Oldest File: {stats.oldest_file}")
        context.append(f"Newest File: {stats.newest_file}")
        
        return "\n".join(context)

    def _scan_directory(self, directory: Path) -> DirectoryStats:
        total_files = 0
        total_size = 0
        categories = {}
        oldest_ts = time.time()
        newest_ts = 0.0
        oldest_name = "None"
        newest_name = "None"
        files_with_size = []
        duplicate_groups = 0

        try:
            for entry in os.scandir(directory):
                if entry.is_file():
                    total_files += 1
                    stat = entry.stat()
                    size = stat.st_size
                    mtime = stat.st_mtime

                    total_size += size
                    files_with_size.append((size, entry.name))

                    ext = Path(entry.name).suffix.lower() or "no_ext"
                    categories[ext] = categories.get(ext, 0) + 1

                    if mtime < oldest_ts:
                        oldest_ts = mtime
                        oldest_name = entry.name
                    if mtime > newest_ts:
                        newest_ts = mtime
                        newest_name = entry.name

            # Identify top 5 largest files
            files_with_size.sort(key=lambda x: x[0], reverse=True)
            top_5_largest = [name for _, name in files_with_size[:5]]

            # Quick check for duplicates (placeholder logic if needed)
            # In a real scenario, this would call the organizer.
            duplicate_groups = 0 

        except (PermissionError, OSError):
            top_5_largest = []

        return DirectoryStats(
            total_files=total_files,
            total_size=total_size,
            total_size_human=self._human_size(total_size),
            category_counts=categories,
            oldest_file=oldest_name,
            newest_file=newest_name,
            top_5_largest=top_5_largest,
            duplicate_groups=duplicate_groups
        )

    def _human_size(self, size_bytes: int) -> str:
        size = float(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"
