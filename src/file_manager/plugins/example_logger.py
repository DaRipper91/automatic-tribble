"""
Example plugin that logs activity to a file.
"""
from pathlib import Path
from typing import List
from datetime import datetime
from .base import TFMPlugin

class ActivityLoggerPlugin(TFMPlugin):
    """Logs file operations to ~/.tfm/activity.log"""

    def __init__(self):
        self.log_file = Path.home() / ".tfm" / "activity.log"

    def _log(self, message: str) -> None:
        timestamp = datetime.now().isoformat()
        try:
            with open(self.log_file, "a") as f:
                f.write(f"[{timestamp}] {message}\n")
        except OSError:
            pass

    def on_file_added(self, path: Path) -> None:
        self._log(f"File added: {path}")

    def on_file_deleted(self, path: Path) -> None:
        self._log(f"File deleted: {path}")

    def on_organize(self, source: Path, destination: Path) -> None:
        self._log(f"File organized: {source} -> {destination}")

    def on_search_complete(self, query: str, results: List[Path]) -> None:
        self._log(f"Search '{query}' found {len(results)} results")
