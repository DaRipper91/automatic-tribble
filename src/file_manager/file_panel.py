"""
File panel widget for displaying and navigating files with multi-selection.
"""

from pathlib import Path
from typing import Optional, Set
from textual.widgets import DirectoryTree, Static
from textual.containers import Vertical, Container
from textual.reactive import reactive
from textual.binding import Binding
from textual.message import Message
from rich.text import Text

class MultiSelectDirectoryTree(DirectoryTree):
    """DirectoryTree with multi-selection support."""

    class SelectionChanged(Message):
        """Emitted when selection changes."""
        def __init__(self, tree: "MultiSelectDirectoryTree"):
            self.tree = tree
            super().__init__()

    BINDINGS = [
        Binding("space", "toggle_selection", "Toggle Selection"),
        Binding("shift+down", "select_down", "Select Down", show=False),
        Binding("shift+up", "select_up", "Select Up", show=False),
        Binding("ctrl+a", "select_all", "Select All"),
        Binding("ctrl+d", "deselect_all", "Deselect All"),
    ]

    def __init__(self, path: str, **kwargs):
        super().__init__(path, **kwargs)
        self.selected_paths: Set[Path] = set()
        self._anchor_node = None

    def on_mount(self) -> None:
        super().on_mount()

    def action_toggle_selection(self) -> None:
        node = self.cursor_node
        if not node: return
        self._anchor_node = node

        # Determine path from node data
        if not node.data or not hasattr(node.data, 'path'):
            return

        path = Path(node.data.path)
        if path in self.selected_paths:
            self.selected_paths.remove(path)
            self._update_node_visual(node, selected=False)
        else:
            self.selected_paths.add(path)
            self._update_node_visual(node, selected=True)

        self.post_message(self.SelectionChanged(self))

    def action_select_down(self) -> None:
        if not self._anchor_node:
            self._anchor_node = self.cursor_node
        self.action_cursor_down()
        self._select_range()

    def action_select_up(self) -> None:
        if not self._anchor_node:
            self._anchor_node = self.cursor_node
        self.action_cursor_up()
        self._select_range()

    def _select_range(self) -> None:
        if not self._anchor_node or not self.cursor_node:
            return

        # Simple range selection: from anchor to current cursor
        # In a real tree, we'd need to find the flat order of nodes to know which are between.
        # DirectoryTree nodes don't easily give a flat index. We can traverse visible nodes.
        nodes = []
        def _collect(n):
            if n.is_expanded:
                for c in n.children:
                    nodes.append(c)
                    _collect(c)
        for child in self.root.children:
            nodes.append(child)
            _collect(child)

        try:
            anchor_idx = nodes.index(self._anchor_node)
            cursor_idx = nodes.index(self.cursor_node)
            start = min(anchor_idx, cursor_idx)
            end = max(anchor_idx, cursor_idx)

            # Clear current selection if we're making a new range from an anchor
            self.selected_paths.clear()
            self.reload() # Clear visual state, although it flashes it works

            for i in range(start, end + 1):
                node = nodes[i]
                if node.data and hasattr(node.data, 'path'):
                    path = Path(node.data.path)
                    self.selected_paths.add(path)
                    self._update_node_visual(node, selected=True)
            self.post_message(self.SelectionChanged(self))
        except ValueError:
            pass

    def action_select_all(self) -> None:
        # Select all siblings of current node (or all visible nodes if possible)
        # We'll target siblings of cursor for simplicity, or children of root if at root.
        node = self.cursor_node
        if not node:
             # Fallback to root children
             node = self.root

        parent = node.parent
        # If node is root (which shouldn't happen for cursor usually unless empty), use it
        if not parent:
            target_nodes = node.children
        else:
            target_nodes = parent.children

        for child in target_nodes:
            if child.data and hasattr(child.data, 'path'):
                path = Path(child.data.path)
                self.selected_paths.add(path)
                self._update_node_visual(child, selected=True)

        self.post_message(self.SelectionChanged(self))

    def action_deselect_all(self) -> None:
        self.selected_paths.clear()
        self.reload()
        self.post_message(self.SelectionChanged(self))

    def _update_node_visual(self, node, selected: bool) -> None:
        label = node.label
        # Textual DirectoryTree labels are typically simple strings or Text objects.
        # We need to preserve the original text but change style.

        # Check if we have cached original label (not standard, but we can try to guess)
        # Or just toggle style.

        current_text = str(label)

        if selected:
            # Apply highlight style. Use generic reverse for theme compatibility.
            new_label = Text(current_text, style="reverse")
        else:
            # Revert to default (empty style or just string)
            new_label = Text(current_text)

        node.set_label(new_label)


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
    
    FilePanel MultiSelectDirectoryTree {
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
        # Clear selection on navigation
        if self._tree:
            self._tree.selected_paths.clear()
            self._tree.post_message(MultiSelectDirectoryTree.SelectionChanged(self._tree))

            # Animate transition
            self._tree.styles.opacity = 0.0
            self._tree.styles.animate("opacity", 1.0, duration=0.2)

        self.current_dir = Path(event.path)
        self._update_header()
    
    def get_selected_path(self) -> Optional[Path]:
        """
        Get the currently selected file or directory path (cursor).
        
        Returns:
            Path object of selected item, or None if nothing selected
        """
        if self._tree and self._tree.cursor_node:
            node = self._tree.cursor_node
            if node.data and hasattr(node.data, 'path'):
                return Path(node.data.path)
        return None

    def get_selected_paths(self) -> Set[Path]:
        """
        Get the set of selected paths.
        If selection is empty, returns set containing cursor path (if any).
        """
        if self._tree:
            if self._tree.selected_paths:
                return self._tree.selected_paths.copy()

            # Fallback to cursor
            cursor = self.get_selected_path()
            if cursor:
                return {cursor}
        return set()
    
    def refresh_view(self) -> None:
        """Refresh the directory tree view."""
        if self._tree:
            self._tree.selected_paths.clear() # Clear selection on refresh
            self._tree.post_message(MultiSelectDirectoryTree.SelectionChanged(self._tree))
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
                self._tree.selected_paths.clear()
                self._tree.post_message(MultiSelectDirectoryTree.SelectionChanged(self._tree))
                self._tree.path = str(path)
                self._tree.reload()
            self._update_header()
