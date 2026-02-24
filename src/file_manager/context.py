"""
Context management for AI operations.
"""

import time
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from .utils import recursive_scan

class DirectoryContextBuilder:
    """Builds context information about a directory for AI consumption."""

    def __init__(self, cache_ttl: int = 60):
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, float] = {}

    def get_context(self, directory: Path) -> Dict[str, Any]:
        """
        Get structured context for the given directory.
        Uses cached data if available and fresh.
        """
        dir_str = str(directory.resolve())
        now = time.time()

        if dir_str in self._cache:
            if now - self._cache_timestamps[dir_str] < self.cache_ttl:
                return self._cache[dir_str]

        context = self._build_context(directory)
        self._cache[dir_str] = context
        self._cache_timestamps[dir_str] = now
        return context

    def _build_context(self, directory: Path) -> Dict[str, Any]:
        """
        Scan directory and build context dictionary.
        """
        stats = {
            "total_files": 0,
            "total_size": 0,
            "extensions": {},
            "oldest_file": None,
            "newest_file": None,
            "largest_files": [], # Top 5
        }

        files_list = []
        error_msg = None

        try:
            for entry in recursive_scan(directory):
                if entry.is_file():
                    try:
                        stat = entry.stat()
                        size = stat.st_size
                        mtime = stat.st_mtime

                        stats["total_files"] += 1
                        stats["total_size"] += size

                        ext = Path(entry.name).suffix.lower()
                        stats["extensions"][ext] = stats["extensions"].get(ext, 0) + 1

                        file_info = {
                            "name": entry.name,
                            "path": str(Path(entry.path)),
                            "size": size,
                            "mtime": mtime
                        }
                        files_list.append(file_info)

                    except (OSError, ValueError):
                        continue
        except (OSError, PermissionError) as e:
            error_msg = str(e)

        if not files_list:
             return {
                "path": str(directory),
                "file_count": 0,
                "total_size_bytes": 0,
                "file_types": {},
                "key_files": {
                    "oldest": "None",
                    "newest": "None",
                    "largest": []
                },
                "summary": error_msg or "Empty directory or no access."
            }

        # Process gathered data
        files_list.sort(key=lambda x: x["size"], reverse=True)
        stats["largest_files"] = [f["name"] for f in files_list[:5]]

        files_list.sort(key=lambda x: x["mtime"])
        stats["oldest_file"] = files_list[0]["name"] if files_list else None
        stats["newest_file"] = files_list[-1]["name"] if files_list else None

        # Convert timestamps to readable dates
        oldest_date = datetime.fromtimestamp(files_list[0]["mtime"]).strftime('%Y-%m-%d') if files_list else "N/A"
        newest_date = datetime.fromtimestamp(files_list[-1]["mtime"]).strftime('%Y-%m-%d') if files_list else "N/A"

        # Format for AI
        return {
            "path": str(directory),
            "file_count": stats["total_files"],
            "total_size_bytes": stats["total_size"],
            "file_types": stats["extensions"],
            "key_files": {
                "oldest": f"{stats['oldest_file']} ({oldest_date})",
                "newest": f"{stats['newest_file']} ({newest_date})",
                "largest": stats["largest_files"]
            }
        }
