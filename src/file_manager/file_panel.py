"""
File panel widget for displaying and navigating files.
"""

from pathlib import Path
from typing import Optional, List
from textual.widgets import DirectoryTree, Static
from textual.containers import Vertical, Container
from textual.reactive import reactive

from .ui_components import MultiSelectDirectoryTree


class FilePanel(Container):
    """A file panel widget showing directory contents."""
    
    DEFAULT_CSS = """
    FilePanel {
        padding: 0;
    }
    
    FilePanel > Vertical {
        height: 100%;
    }
    
    FilePanel .panel-header {
        height: 3;
        background: $boost;
        content-align: center middle;
        text-style: bold;
    }
    
    FilePanel DirectoryTree {
        height: 1fr;
        scrollbar-gutter: stable;
    }
    """
    
    current_dir = reactive(Path.home())
    
    def __init__(self, initial_path: str, **kwargs):
        """
        Initialize the file panel.
        
        Args:
            initial_path: Initial directory path to display
            **kwargs: Additional keyword arguments for Container
        """
        super().__init__(**kwargs)
        self.initial_path = Path(initial_path)
        self.current_dir = self.initial_path
        self._tree: Optional[MultiSelectDirectoryTree] = None
    
    def compose(self):
        """Compose the file panel layout."""
        with Vertical():
            yield Static(str(self.current_dir), classes="panel-header")
            yield MultiSelectDirectoryTree(str(self.current_dir))
    
    def on_mount(self) -> None:
        """Handle mounting of the widget."""
        self._tree = self.query_one(MultiSelectDirectoryTree)
        self._update_header()
    
    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        """Handle directory selection."""
        self.current_dir = Path(event.path)
        self._update_header()
    
    def get_selected_path(self) -> Optional[Path]:
        """
        Get the currently focused file or directory path (cursor).
        
        Returns:
            Path object of focused item, or None if nothing focused
        """
        if self._tree and self._tree.cursor_node:
            node = self._tree.cursor_node
            if node.data and hasattr(node.data, 'path'):
                return Path(node.data.path)
        return None

    def get_selected_paths(self) -> List[Path]:
        """
        Get the list of selected paths.
        If no explicit selection, returns a list containing the focused item.
        """
        if self._tree:
            if self._tree.selected_paths:
                return list(self._tree.selected_paths)

            # Fallback to cursor
            cursor_path = self.get_selected_path()
            if cursor_path:
                return [cursor_path]
        return []
    
    def refresh_view(self) -> None:
        """Refresh the directory tree view."""
        if self._tree:
            self._tree.reload()
            self._update_header()
    
    def _update_header(self) -> None:
        """Update the panel header with current directory."""
        header = self.query_one(".panel-header", Static)
        header.update(str(self.current_dir))
    
    def navigate_to(self, path: Path) -> None:
        """
        Navigate to a specific path.
        
        Args:
            path: Path to navigate to
        """
        if path.exists() and path.is_dir():
            self.current_dir = path
            if self._tree:
                self._tree.path = str(path)
                self._tree.reload()
                self._tree.styles.opacity = 0.0
                self._tree.animate("opacity", 1.0, duration=0.2)
            self._update_header()
