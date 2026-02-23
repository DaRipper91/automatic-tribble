"""
Base class for TFM plugins.
"""
from pathlib import Path
from typing import List

class TFMPlugin:
    """Abstract base class for TFM plugins."""

    @property
    def name(self) -> str:
        """Name of the plugin."""
        return self.__class__.__name__

    def on_file_added(self, path: Path) -> None:
        """Called when a file is added (copied, moved, created)."""
        pass

    def on_file_deleted(self, path: Path) -> None:
        """Called when a file is deleted."""
        pass

    def on_organize(self, source: Path, destination: Path) -> None:
        """Called when a file is organized."""
        pass

    def on_search_complete(self, query: str, results: List[Path]) -> None:
        """Called when a search is completed."""
        pass
