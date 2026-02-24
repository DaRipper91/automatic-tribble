"""
UI Components for File Manager
"""

import shutil
from pathlib import Path
from typing import Optional, Set
from datetime import datetime

from rich.syntax import Syntax
from rich.text import Text

from textual import work
from textual.widgets import DirectoryTree, Static, Label, LoadingIndicator
from textual.containers import Vertical, Horizontal, Container
from textual.reactive import reactive
from textual.binding import Binding
from textual.message import Message

class MultiSelectDirectoryTree(DirectoryTree):
    """A DirectoryTree that supports multi-selection."""

    class SelectionChanged(Message):
        """Message sent when selection changes."""
        def __init__(self, tree: "MultiSelectDirectoryTree") -> None:
            self.tree = tree
            super().__init__()

    BINDINGS = [
        Binding("space", "toggle_selection", "Toggle Selection"),
        Binding("shift+down", "select_next", "Select Next"),
        Binding("shift+up", "select_prev", "Select Prev"),
        Binding("ctrl+a", "select_all", "Select All"),
        Binding("ctrl+d", "deselect_all", "Deselect All"),
    ]

    selected_paths = reactive(set(), always_update=True)

    def watch_selected_paths(self) -> None:
        self.post_message(self.SelectionChanged(self))

    def action_toggle_selection(self) -> None:
        if self.cursor_node and self.cursor_node.data:
            path = Path(self.cursor_node.data.path)
            if path in self.selected_paths:
                self.selected_paths.remove(path)
            else:
                self.selected_paths.add(path)
            self.selected_paths = self.selected_paths # Trigger reactive update
            self.refresh()

    def action_select_next(self) -> None:
        self.action_cursor_down()
        self.action_toggle_selection()

    def action_select_prev(self) -> None:
        self.action_cursor_up()
        self.action_toggle_selection()

    def action_select_all(self) -> None:
        if not self.cursor_node:
            return

        parent = self.cursor_node.parent
        if parent:
            for node in parent.children:
                if node.data:
                    self.selected_paths.add(Path(node.data.path))
            self.selected_paths = self.selected_paths
            self.refresh()

    def action_deselect_all(self) -> None:
        self.selected_paths.clear()
        self.selected_paths = self.selected_paths
        self.refresh()

    def render_label(self, node, base_style, style):
        label = super().render_label(node, base_style, style)
        if node.data:
            path = Path(node.data.path)
            if path in self.selected_paths:
                label.stylize("reverse bold green")
        return label

class FilePreview(Vertical):
    """A widget to preview files."""

    DEFAULT_CSS = """
    FilePreview {
        width: 0;
        border-left: solid $primary;
        height: 100%;
        background: $surface;
        transition: width 0.3s;
    }
    FilePreview.open {
        width: 50;
    }
    #preview-header {
        background: $boost;
        padding: 0 1;
        text-style: bold;
    }
    #preview-content {
        height: 1fr;
        overflow: auto;
    }
    """

    path = reactive(None)

    def compose(self):
        yield Label("No file selected", id="preview-header")
        yield Container(id="preview-content")

    async def watch_path(self, path: Optional[Path]) -> None:
        header = self.query_one("#preview-header", Label)
        content_container = self.query_one("#preview-content")

        content_container.remove_children()

        if not path:
            header.update("No file selected")
            return

        header.update(str(path.name))

        if not path.exists():
            content_container.mount(Label("File not found"))
            return

        if path.is_dir():
            content_container.mount(Label("Directory preview not supported"))
            return

        self.load_preview(path)

    @work
    async def load_preview(self, path: Path) -> None:
        content_container = self.query_one("#preview-content")

        try:
            # Determine type
            suffix = path.suffix.lower()
            if suffix in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg', '.ico']:
                # Image metadata
                stat = path.stat()
                size = self._format_size(stat.st_size)
                dt = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                info = f"Image: {path.name}\nSize: {size}\nModified: {dt}\n\n[Image preview not supported in terminal]"
                self.app.call_from_thread(content_container.mount, Static(info))

            elif suffix in ['.txt', '.py', '.md', '.json', '.yaml', '.yml', '.js', '.c', '.cpp', '.h', '.sh', '.css', '.html', '.xml', '.sql']:
                # Text/Code
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()[:100]
                    content = "".join(lines)

                lexer = Syntax.guess_lexer(str(path), code=content)
                syntax = Syntax(content, lexer, theme="monokai", line_numbers=True)
                self.app.call_from_thread(content_container.mount, Static(syntax))

            else:
                # Hex dump
                with open(path, 'rb') as f:
                    data = f.read(512)

                hex_str = " ".join(f"{b:02x}" for b in data)
                # Split hex string for readability
                formatted_hex = ""
                for i in range(0, len(hex_str), 48): # 16 bytes * 3 chars
                    formatted_hex += hex_str[i:i+48] + "\n"

                self.app.call_from_thread(content_container.mount, Static(f"Hex Dump (first 512 bytes):\n{formatted_hex}"))

        except Exception as e:
             self.app.call_from_thread(content_container.mount, Static(f"Error reading file: {e}"))

    @staticmethod
    def _format_size(size: float) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

class EnhancedStatusBar(Horizontal):
    """Enhanced status bar."""

    DEFAULT_CSS = """
    EnhancedStatusBar {
        height: 1;
        dock: bottom;
        background: $panel;
        padding: 0 1;
    }
    .status-item {
        padding: 0 1;
        border-right: solid $secondary;
    }
    #spinner {
        display: none;
        width: 1;
    }
    #spinner.visible {
        display: block;
    }
    """

    total_files = reactive(0)
    selected_count = reactive(0)
    selected_size = reactive(0)
    free_space = reactive("Calculating...")
    is_loading = reactive(False)

    def compose(self):
        yield Label("Ready", id="status-message", classes="status-item")
        yield Label("0 files", id="stats", classes="status-item")
        yield Label("Selection: 0 (0 B)", id="selection-info", classes="status-item")
        yield Label("", id="free-space", classes="status-item")
        yield LoadingIndicator(id="spinner")

    def update_status(self, message: str):
        self.query_one("#status-message", Label).update(message)

    def watch_total_files(self, value: int):
        self.query_one("#stats", Label).update(f"{value} files")

    def watch_selected_count(self, value: int):
        self._update_selection_label()

    def watch_selected_size(self, value: int):
        self._update_selection_label()

    def watch_free_space(self, value: str):
        self.query_one("#free-space", Label).update(f"Free: {value}")

    def watch_is_loading(self, value: bool):
        spinner = self.query_one("#spinner")
        if value:
            spinner.add_class("visible")
        else:
            spinner.remove_class("visible")

    def _update_selection_label(self):
        size_str = self._format_size(self.selected_size)
        self.query_one("#selection-info", Label).update(f"Selection: {self.selected_count} ({size_str})")

    @staticmethod
    def _format_size(size: float) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

class FilePanel(Container):
    """A file panel widget showing directory contents."""

    DEFAULT_CSS = """
    FilePanel {
        padding: 0;
        transition: opacity 0.2s;
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

    FilePanel.loading {
        opacity: 0.5;
    }
    """

    current_dir = reactive(Path.home())

    def __init__(self, initial_path: str, **kwargs):
        super().__init__(**kwargs)
        self.initial_path = Path(initial_path)
        self.current_dir = self.initial_path
        self._tree: Optional[MultiSelectDirectoryTree] = None

    def compose(self):
        with Vertical():
            yield Static(str(self.current_dir), classes="panel-header")
            yield MultiSelectDirectoryTree(str(self.current_dir))

    def on_mount(self) -> None:
        self._tree = self.query_one(MultiSelectDirectoryTree)
        self._update_header()

    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        self.add_class("loading") # Animation trigger
        self.current_dir = Path(event.path)
        self._update_header()
        self.set_timer(0.2, lambda: self.remove_class("loading")) # Remove after brief animation

    def get_selected_path(self) -> Optional[Path]:
        if self._tree and self._tree.cursor_node:
            node = self._tree.cursor_node
            if node.data and hasattr(node.data, 'path'):
                return Path(node.data.path)
        return None

    def get_selected_paths(self) -> Set[Path]:
        """Get all selected paths."""
        if self._tree:
            return self._tree.selected_paths
        return set()

    def refresh_view(self) -> None:
        if self._tree:
            self._tree.reload()
            self._update_header()

    def _update_header(self) -> None:
        header = self.query_one(".panel-header", Static)
        header.update(str(self.current_dir))

    def navigate_to(self, path: Path) -> None:
        if path.exists() and path.is_dir():
            self.current_dir = path
            if self._tree:
                self._tree.path = str(path)
                self._tree.reload()
            self._update_header()

class DualFilePanes(Container):
    """Container for two FilePanels."""

    DEFAULT_CSS = """
    DualFilePanes {
        layout: horizontal;
        height: 100%;
    }

    DualFilePanes .file-panel {
        width: 1fr;
        border: solid $primary;
        height: 100%;
    }

    DualFilePanes .file-panel.active {
        border: solid $accent;
    }
    """

    active_panel_idx = reactive(0) # 0 for left, 1 for right

    def __init__(self, left_path: Path, right_path: Path, **kwargs):
        super().__init__(**kwargs)
        self.left_path = left_path
        self.right_path = right_path

    def compose(self):
        yield FilePanel(str(self.left_path), id="left-panel", classes="file-panel active")
        yield FilePanel(str(self.right_path), id="right-panel", classes="file-panel")

    def on_mount(self):
        self.query_one("#left-panel", FilePanel).focus()

    def switch_panel(self):
        self.active_panel_idx = 1 - self.active_panel_idx

        left = self.query_one("#left-panel", FilePanel)
        right = self.query_one("#right-panel", FilePanel)

        if self.active_panel_idx == 0:
            left.add_class("active")
            right.remove_class("active")
            left.focus()
        else:
            right.add_class("active")
            left.remove_class("active")
            right.focus()

    def get_active_panel(self) -> FilePanel:
        if self.active_panel_idx == 0:
            return self.query_one("#left-panel", FilePanel)
        return self.query_one("#right-panel", FilePanel)

    def get_inactive_panel(self) -> FilePanel:
        if self.active_panel_idx == 0:
            return self.query_one("#right-panel", FilePanel)
        return self.query_one("#left-panel", FilePanel)
