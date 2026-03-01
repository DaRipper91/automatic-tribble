"""
Shared UI components for the File Manager.
"""
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Set, Optional, Iterable

from rich.syntax import Syntax
from rich.text import Text
from rich.markup import escape

from textual import work
from textual.widgets import DirectoryTree, Static, Label, LoadingIndicator
from textual.containers import Vertical, Horizontal
from textual.reactive import reactive
from textual.binding import Binding
from textual.message import Message

from .utils import format_size


class MultiSelectDirectoryTree(DirectoryTree):
    """A DirectoryTree that supports multiple file selection."""

    BINDINGS = [
        Binding("space", "toggle_selection", "Toggle Selection"),
        Binding("ctrl+a", "select_all", "Select All"),
        Binding("ctrl+d", "deselect_all", "Deselect All"),
    ]

    class SelectionChanged(Message):
        """Posted when the selection set changes."""
        def __init__(self, selection: Set[Path]) -> None:
            self.selection = selection
            super().__init__()

    def __init__(self, path: str, **kwargs):
        super().__init__(path, **kwargs)
        self.selected_paths: Set[Path] = set()
        self._anchor_node = None  # For shift-select (not fully implemented yet but reserved)

    def on_mount(self) -> None:
        super().on_mount()

    def action_toggle_selection(self) -> None:
        """Toggle selection of the current node."""
        node = self.cursor_node
        if node and node.data:
            path = Path(node.data.path)
            if path in self.selected_paths:
                self.selected_paths.remove(path)
                # Remove visual highlight
                self._update_node_style(node, False)
            else:
                self.selected_paths.add(path)
                # Add visual highlight
                self._update_node_style(node, True)

            self.post_message(self.SelectionChanged(self.selected_paths))

    def action_select_all(self) -> None:
        """Select all items in the current directory."""
        # This is tricky in a lazy-loaded tree.
        # For now, let's just select visible siblings of the cursor.
        if not self.cursor_node or not self.cursor_node.parent:
            return

        parent = self.cursor_node.parent
        for node in parent.children:
             if node.data:
                 path = Path(node.data.path)
                 self.selected_paths.add(path)
                 self._update_node_style(node, True)

        self.post_message(self.SelectionChanged(self.selected_paths))

    def action_deselect_all(self) -> None:
        """Clear all selections."""
        self.selected_paths.clear()
        # We need to refresh styles. Iterating all nodes might be expensive if tree is huge,
        # but we can try to re-render visible ones or just reload.
        # Reloading is drastic. Let's just reset styles on currently loaded nodes if possible.
        # Textual's Tree doesn't easily expose 'all loaded nodes', so we might just reload or
        # let the styles stick until navigated away if we can't easily iterate.
        # Better approach: Iterate root and children recursively if loaded.
        self._clear_styles_recursive(self.root)
        self.post_message(self.SelectionChanged(self.selected_paths))

    def _update_node_style(self, node, selected: bool) -> None:
        """
        Update the visual style of a node to reflect selection state.
        In Textual, we can style the label.
        """
        # This relies on internal Textual Tree implementation details potentially,
        # or we wrap the label in a widget.
        # Standard DirectoryTree uses simple labels.
        # We can try setting a class on the node's widget if it exists.

        # NOTE: Textual's Tree nodes don't directly map to widgets 1:1 in a simple way
        # exposed for styling individual rows easily without custom renderers.
        # However, we can use `Tree.update_label` to change the text style.

        label = str(node.label)
        if selected:
            # Add a visual indicator
            if not label.startswith("[bold reverse]"):
                 node.label = f"[bold reverse]{label}[/]"
        else:
            # Remove visual indicator
            # This is a bit hacky, stripping tags.
            # Ideally we'd store original label.
            # For now, let's assume standard label is filename.
            if node.data:
                node.label = node.data.path.name

        self.refresh()

    def _clear_styles_recursive(self, node):
        if not node:
            return
        self._update_node_style(node, False)
        if node.children:
            for child in node.children:
                self._clear_styles_recursive(child)

    def filter_paths(self, paths: Iterable[Path]) -> None:
        """Called when underlying tree refreshes/filters? Not standard."""
        pass

    def get_selected_paths(self) -> Set[Path]:
        return self.selected_paths


class FilePreview(Vertical):
    """A widget to preview file contents."""

    DEFAULT_CSS = """
    FilePreview {
        width: 100%;
        height: 100%;
        background: $surface;
        border-left: solid $primary;
        overflow: auto;
    }

    FilePreview Static {
        padding: 1;
    }

    .error {
        color: $error;
    }

    .metadata {
        color: $text-muted;
    }
    """

    def __init__(self):
        super().__init__()
        self.content_view = Static(id="content-view", expand=True)
        self.loading = LoadingIndicator()
        self.loading.display = False
        self.current_path: Optional[Path] = None

    def compose(self):
        yield self.loading
        yield self.content_view

    @work
    async def show_preview(self, path: Path) -> None:
        """Load and display preview for the given path."""
        if path == self.current_path:
            return

        self.current_path = path
        self.loading.display = True
        self.content_view.display = False

        try:
            if not path.exists():
                self.app.call_from_thread(self.update_content, "File not found.", "error")
                return

            if path.is_dir():
                self.app.call_from_thread(self.update_content, f"Directory: {path.name}", "metadata")
                return

            stat = path.stat()
            size = format_size(stat.st_size)

            # Check for images
            suffix = path.suffix.lower()
            if suffix in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']:
                info = f"[bold]Image File[/]\n\nName: {path.name}\nSize: {size}\nCreated: {datetime.fromtimestamp(stat.st_ctime)}\nModified: {datetime.fromtimestamp(stat.st_mtime)}"
                self.app.call_from_thread(self.update_content, info, "metadata")
                return

            # Text/Code files
            try:
                # Read first 100 lines or 8KB
                with open(path, "r", encoding="utf-8") as f:
                    lines = []
                    for _ in range(100):
                        line = f.readline()
                        if not line:
                            break
                        lines.append(line)
                    content = "".join(lines)

                # Syntax highlighting
                syntax = Syntax(content, self._get_lexer(suffix), theme="monokai", line_numbers=True)
                self.app.call_from_thread(self.update_syntax, syntax)

            except UnicodeDecodeError:
                # Binary file - show hex dump
                with open(path, "rb") as f:
                    data = f.read(512)

                hex_dump = self._create_hex_dump(data)
                self.app.call_from_thread(self.update_content, hex_dump, "metadata")

        except Exception as e:
            self.app.call_from_thread(self.update_content, f"Error reading file: {str(e)}", "error")
        finally:
            self.app.call_from_thread(self._finish_loading)

    def _finish_loading(self):
        self.loading.display = False
        self.content_view.display = True

    def update_content(self, content: str, style_class: str = "") -> None:
        self.content_view.update(content)
        self.content_view.classes = style_class

    def update_syntax(self, syntax: Syntax) -> None:
        self.content_view.update(syntax)
        self.content_view.classes = ""

    def _get_lexer(self, suffix: str) -> str:
        lexers = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.html': 'html',
            '.css': 'css',
            '.json': 'json',
            '.md': 'markdown',
            '.sh': 'bash',
            '.c': 'c',
            '.cpp': 'cpp',
            '.rs': 'rust',
            '.go': 'go',
            '.java': 'java',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml',
            '.xml': 'xml',
        }
        return lexers.get(suffix, 'text')

    def _create_hex_dump(self, data: bytes) -> str:
        hex_lines = []
        for i in range(0, len(data), 16):
            chunk = data[i:i+16]
            hex_part = " ".join(f"{b:02x}" for b in chunk)
            text_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            hex_lines.append(f"{i:04x}  {hex_part:<48}  {text_part}")

        return "[bold]Binary File (First 512 bytes)[/]\n\n" + "\n".join(hex_lines)


class EnhancedStatusBar(Horizontal):
    """Status bar showing selection stats and disk info."""

    DEFAULT_CSS = """
    EnhancedStatusBar {
        height: 1;
        background: $panel;
        color: $text;
        dock: bottom;
        padding: 0 1;
    }

    .status-item {
        margin-right: 2;
        min-width: 10;
    }

    .spacer {
        width: 1fr;
    }
    """

    selection_count = reactive(0)
    selection_size = reactive(0)
    total_free_space = reactive("Calculating...")
    sort_mode = reactive("Name")

    def compose(self):
        yield Label("Ready", id="status-msg", classes="status-item")
        yield Label("", classes="spacer")
        yield Label("Selected: 0 (0 B)", id="selection-info", classes="status-item")
        yield Label("Free: ...", id="disk-info", classes="status-item")
        yield Label("Sort: Name", id="sort-info", classes="status-item")

    def watch_selection_count(self, value: int):
        self._update_selection_label()

    def watch_selection_size(self, value: int):
        self._update_selection_label()

    def watch_total_free_space(self, value: str):
        self.query_one("#disk-info", Label).update(f"Free: {value}")

    def watch_sort_mode(self, value: str):
        self.query_one("#sort-info", Label).update(f"Sort: {value}")

    def _update_selection_label(self):
        size_str = format_size(self.selection_size)
        self.query_one("#selection-info", Label).update(f"Selected: {self.selection_count} ({size_str})")

    def update_disk_usage(self, path: Path):
        try:
            import shutil
            total, used, free = shutil.disk_usage(path)
            self.total_free_space = format_size(free)
        except Exception:
            self.total_free_space = "Unknown"
