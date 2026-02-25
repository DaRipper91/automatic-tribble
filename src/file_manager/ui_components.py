from pathlib import Path
from typing import Set, Optional
import shutil
import os
from datetime import datetime

from textual import work
from textual.app import ComposeResult
from textual.widgets import DirectoryTree, Static, Label, LoadingIndicator
from textual.containers import Container, Vertical, Horizontal
from textual.message import Message
from rich.syntax import Syntax
from rich.text import Text

class MultiSelectDirectoryTree(DirectoryTree):
    """
    A DirectoryTree that supports multi-selection.
    """

    class SelectionChanged(Message):
        """Emitted when selection changes."""
        def __init__(self, tree: "MultiSelectDirectoryTree"):
            self.tree = tree
            super().__init__()

    def __init__(self, path: str, **kwargs):
        super().__init__(path, **kwargs)
        self.selected_paths: Set[Path] = set()
        self.anchor_line: Optional[int] = None

    def on_mount(self) -> None:
        super().on_mount()
        self.anchor_line = self.cursor_line

    def on_key(self, event) -> None:
        if event.key == "space":
            self.toggle_selection()
            self.anchor_line = self.cursor_line
            event.stop()
        elif event.key == "ctrl+a":
            self.select_all()
            event.stop()
        elif event.key == "ctrl+d":
            self.deselect_all()
            event.stop()
        elif event.key == "shift+down":
            self.action_cursor_down()
            self.select_range()
            event.stop()
        elif event.key == "shift+up":
            self.action_cursor_up()
            self.select_range()
            event.stop()

    def toggle_selection(self) -> None:
        node = self.cursor_node
        if node and node.data:
            path = Path(node.data.path)
            if path in self.selected_paths:
                self.selected_paths.remove(path)
            else:
                self.selected_paths.add(path)

            self.refresh()
            self.post_message(self.SelectionChanged(self))

    def select_range(self) -> None:
        if self.anchor_line is None:
            self.anchor_line = self.cursor_line
            return

        start = min(self.anchor_line, self.cursor_line)
        end = max(self.anchor_line, self.cursor_line)

        for line in range(start, end + 1):
            node = self.get_node_at_line(line)
            if node and node.data:
                self.selected_paths.add(Path(node.data.path))

        self.refresh()
        self.post_message(self.SelectionChanged(self))

    def select_all(self) -> None:
        node = self.cursor_node
        if node and node.parent:
            for child in node.parent.children:
                if child.data:
                    self.selected_paths.add(Path(child.data.path))
            self.refresh()
            self.post_message(self.SelectionChanged(self))

    def deselect_all(self) -> None:
        self.selected_paths.clear()
        self.refresh()
        self.post_message(self.SelectionChanged(self))

    def render_label(self, node, base_style, style):
        label = super().render_label(node, base_style, style)
        if node.data:
            path = Path(node.data.path)
            if path in self.selected_paths:
                label.stylize("bold reverse red")
                label.append(" ✓", style="green")
        return label

class FilePreview(Container):
    DEFAULT_CSS = """
    FilePreview {
        width: 1fr;
        height: 100%;
        border-left: solid $primary;
        background: $surface;
        overflow: auto;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static(id="preview-content", expand=True)

    @work(thread=True)
    def show_preview(self, path: Path) -> None:
        content_widget = self.query_one("#preview-content", Static)
        self.app.call_from_thread(content_widget.update, Text("Loading...", style="dim"))

        try:
            if not path.exists():
                self.app.call_from_thread(content_widget.update, Text("File not found", style="red"))
                return

            if path.is_dir():
                stats = f"Directory: {path.name}\n"
                try:
                    items = list(path.iterdir())
                    stats += f"Items: {len(items)}"
                except Exception as e:
                    stats += f"Error: {e}"
                self.app.call_from_thread(content_widget.update, Text(stats))
                return

            stat = path.stat()
            size = stat.st_size
            suffix = path.suffix.lower()

            if suffix in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']:
                info = f"Image: {path.name}\nSize: {size} bytes\nCreated: {datetime.fromtimestamp(stat.st_ctime)}"
                self.app.call_from_thread(content_widget.update, Text(info, style="bold blue"))
                return

            if size > 1024 * 1024:
                self.app.call_from_thread(content_widget.update, Text("File too large to preview.", style="yellow"))
                return

            try:
                with open(path, 'r', encoding='utf-8') as f:
                     content = "".join([f.readline() for _ in range(100)])

                if suffix in ['.py', '.js', '.html', '.css', '.json', '.md', '.sh']:
                    syntax = Syntax(content, suffix[1:] if suffix.startswith('.') else suffix, theme="monokai", line_numbers=True)
                    self.app.call_from_thread(content_widget.update, syntax)
                else:
                    self.app.call_from_thread(content_widget.update, Text(content))
            except UnicodeDecodeError:
                with open(path, 'rb') as f:
                    data = f.read(512)
                hex_dump = " ".join(f"{b:02x}" for b in data)
                self.app.call_from_thread(content_widget.update, Text(f"Binary Preview:\n{hex_dump}", style="dim"))

        except Exception as e:
             self.app.call_from_thread(content_widget.update, Text(f"Error: {e}", style="red"))

class EnhancedStatusBar(Container):
    DEFAULT_CSS = """
    EnhancedStatusBar {
        height: 1;
        dock: bottom;
        background: $primary;
        color: white;
        layout: horizontal;
        padding: 0 1;
    }

    #status-left {
        width: 1fr;
        content-align: left middle;
    }

    #status-right {
        width: 1fr;
        content-align: right middle;
    }

    #sort-mode {
        width: auto;
        padding: 0 1;
        content-align: center middle;
    }

    #spinner {
        width: 1;
        color: yellow;
        display: none;
    }

    #spinner.visible {
        display: block;
    }
    """

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label("Ready", id="status-left")
            yield Label("", id="status-right")
            yield Label("Sort: Name", id="sort-mode")
            yield LoadingIndicator(id="spinner")

    def update_status(self, count: int, size: int, path: Path, sort_mode: str = "Name", loading: bool = False) -> None:
        left = self.query_one("#status-left", Label)
        right = self.query_one("#status-right", Label)
        sort_label = self.query_one("#sort-mode", Label)
        spinner = self.query_one("#spinner", LoadingIndicator)

        size_str = self._format_size(size)
        left.update(f"Selected: {count} ({size_str})")

        try:
            usage = shutil.disk_usage(path)
            free = self._format_size(usage.free)
            right.update(f"Free: {free}")
        except:
            right.update("Free: N/A")

        sort_label.update(f"Sort: {sort_mode}")

        if loading:
            spinner.add_class("visible")
        else:
            spinner.remove_class("visible")

    def _format_size(self, size: int) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
