from pathlib import Path
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, ProgressBar
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.binding import Binding

from .file_panel import FilePanel

class EnhancedStatusBar(Widget):
    """Rich status bar showing selection stats and system info."""

    selection_count = reactive(0)
    selection_size = reactive(0)
    free_space = reactive("Calculating...")
    sort_mode = reactive("Name")
    is_loading = reactive(False)
    message = reactive("")

    DEFAULT_CSS = """
    EnhancedStatusBar {
        height: 1;
        dock: bottom;
        background: $panel;
        color: $text;
        layout: horizontal;
    }
    .status-item {
        padding: 0 1;
        content-align: center middle;
    }
    #spacer {
        width: 1fr;
    }
    #spinner {
        color: $accent;
        display: none;
    }
    #spinner.loading {
        display: block;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("", id="status-msg", classes="status-item")
        yield Label("", id="spacer")
        yield Label("", id="selection-info", classes="status-item")
        yield Label("", id="disk-info", classes="status-item")
        yield Label("", id="sort-info", classes="status-item")
        yield Label("⟳", id="spinner", classes="status-item")

    def watch_selection_count(self, count: int) -> None:
        self._update_selection()

    def watch_selection_size(self, size: int) -> None:
        self._update_selection()

    def watch_free_space(self, space: str) -> None:
        self.query_one("#disk-info", Label).update(f"Free: {space}")

    def watch_sort_mode(self, mode: str) -> None:
        self.query_one("#sort-info", Label).update(f"Sort: {mode}")

    def watch_is_loading(self, loading: bool) -> None:
        spinner = self.query_one("#spinner", Label)
        if loading:
            spinner.add_class("loading")
        else:
            spinner.remove_class("loading")

    def watch_message(self, message: str) -> None:
        self.query_one("#status-msg", Label).update(message)

    def _update_selection(self) -> None:
        label = self.query_one("#selection-info", Label)
        if self.selection_count > 0:
            size_str = self._format_size(self.selection_size)
            label.update(f"{self.selection_count} selected ({size_str})")
        else:
            label.update("")

    def _format_size(self, size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"


class DualFilePanes(Container):
    """Container for two side-by-side file panels."""

    BINDINGS = [
        Binding("tab", "switch_panel", "Switch Panel"),
    ]

    DEFAULT_CSS = """
    DualFilePanes {
        height: 100%;
        width: 100%;
    }

    DualFilePanes Horizontal {
        height: 1fr;
    }

    .file-panel {
        width: 1fr;
        border: solid $primary;
        height: 100%;
    }

    .file-panel.active {
        border: solid $accent;
    }

    #operation-progress {
        display: none;
        dock: bottom;
        height: 1;
        margin: 0;
        padding: 0;
    }

    #operation-progress.visible {
        display: block;
    }
    """

    active_panel_index = reactive(0) # 0 = Left, 1 = Right

    def __init__(self, left_path: Path, right_path: Path, **kwargs):
        super().__init__(**kwargs)
        self.left_path = left_path
        self.right_path = right_path

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal():
                yield FilePanel(str(self.left_path), id="left-panel", classes="file-panel active")
                yield FilePanel(str(self.right_path), id="right-panel", classes="file-panel")
            yield ProgressBar(total=100, show_eta=True, id="operation-progress", classes="hidden")

    def on_mount(self) -> None:
        self.query_one("#left-panel", FilePanel).focus()

    def action_switch_panel(self) -> None:
        self.active_panel_index = 1 - self.active_panel_index

        left = self.query_one("#left-panel", FilePanel)
        right = self.query_one("#right-panel", FilePanel)

        if self.active_panel_index == 0:
            left.add_class("active")
            right.remove_class("active")
            left.focus()
        else:
            right.add_class("active")
            left.remove_class("active")
            right.focus()

    @property
    def active_panel(self) -> FilePanel:
        if self.active_panel_index == 0:
            return self.query_one("#left-panel", FilePanel)
        return self.query_one("#right-panel", FilePanel)

    @property
    def inactive_panel(self) -> FilePanel:
        if self.active_panel_index == 0:
            return self.query_one("#right-panel", FilePanel)
        return self.query_one("#left-panel", FilePanel)
