"""
Help Overlay Screen
"""
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Input, Label
from textual.containers import Vertical, Horizontal
from textual.binding import Binding

class ShortcutRow(Horizontal):
    """Row displaying a shortcut."""

    DEFAULT_CLASSES = "shortcut-row"

    def __init__(self, key: str, desc: str):
        super().__init__()
        self.key_text = key
        self.desc_text = desc

    def compose(self) -> ComposeResult:
        with Horizontal(classes="key-badge-container"):
             yield Label(self.key_text, classes="key-badge")
        yield Label(self.desc_text, classes="action-desc")


class CategoryWidget(Vertical):
    """Widget for a shortcut category."""

    DEFAULT_CLASSES = "category-box"

    def __init__(self, title: str, shortcuts: list):
        super().__init__()
        self.category_title = title
        self.shortcuts = shortcuts

    def compose(self) -> ComposeResult:
        yield Label(self.category_title, classes="category-title")
        for key, desc in self.shortcuts:
             yield ShortcutRow(key, desc)


class HelpOverlay(ModalScreen):
    """A full-screen help overlay with search."""

    CSS = """
    HelpOverlay {
        align: center middle;
        background: $surface 90%;
    }

    #help-dialog {
        width: 80%;
        height: 80%;
        background: $panel;
        border: thick $primary;
        padding: 1;
    }

    .title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
        width: 100%;
        background: $boost;
        padding: 1;
    }

    #search-bar {
        margin-bottom: 1;
        dock: top;
    }

    #categories-container {
        height: 1fr;
        overflow-y: auto;
    }

    .category-box {
        height: auto;
        border: solid $secondary;
        padding: 1;
        margin-bottom: 1;
        background: $surface;
    }

    .category-title {
        text-style: bold;
        color: $accent;
        border-bottom: solid $secondary;
        margin-bottom: 1;
        width: 100%;
    }

    .shortcut-row {
        height: 3;
        margin-bottom: 0;
        padding: 0 1;
    }

    .key-badge-container {
        width: 25;
        content-align: right middle;
    }

    .key-badge {
        background: $primary;
        color: $text;
        text-style: bold;
    }

    .action-desc {
        color: $text-muted;
        width: 1fr;
        padding-left: 2;
        content-align: left middle;
    }

    .footer-tip {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
        dock: bottom;
    }
    """

    BINDINGS = [
        Binding("escape", "dismiss", "Close Help"),
        Binding("h", "dismiss", "Close Help"),
    ]

    SHORTCUTS = {
        "Navigation": [
            ("↑/↓", "Move cursor"),
            ("Enter", "Open directory / Select"),
            ("Tab", "Switch panel"),
            ("Ctrl+Tab", "Next tab"),
            ("Ctrl+T", "New tab"),
            ("Ctrl+W", "Close tab"),
            ("Esc", "Go up / Back"),
        ],
        "File Operations": [
            ("c", "Copy selected"),
            ("m", "Move selected"),
            ("d", "Delete selected"),
            ("n", "New directory"),
            ("r", "Rename selected"),
        ],
        "Selection": [
            ("Space", "Toggle selection"),
            ("Shift+↑/↓", "Range selection"),
            ("Ctrl+A", "Select all"),
            ("Ctrl+D", "Deselect all"),
        ],
        "View": [
            ("p", "Toggle preview pane"),
            ("h", "Toggle help"),
            ("Ctrl+R", "Refresh view"),
            ("Ctrl+Shift+T", "Switch theme"),
        ],
        "AI Mode": [
            ("Ctrl+Space", "Open AI prompt"),
        ],
        "General": [
            ("q", "Quit application"),
        ]
    }

    def compose(self) -> ComposeResult:
        with Vertical(id="help-dialog"):
            yield Label("Keyboard Shortcuts", classes="title")
            yield Input(placeholder="Search shortcuts...", id="search-bar")
            with Vertical(id="categories-container"):
                pass # Dynamic content populated in on_mount
            yield Label("Press Esc or h to close", classes="footer-tip")

    def on_mount(self) -> None:
        self.refresh_shortcuts()

    def refresh_shortcuts(self, query: str = "") -> None:
        container = self.query_one("#categories-container")
        container.remove_children()

        for category, shortcuts in self.SHORTCUTS.items():
            if query and query in category.lower():
                # Show all if category matches
                container.mount(CategoryWidget(category, shortcuts))
                continue

            # Filter shortcuts
            filtered = [
                (k, d) for k, d in shortcuts
                if not query or query in k.lower() or query in d.lower()
            ]

            if filtered:
                container.mount(CategoryWidget(category, filtered))

    def on_input_changed(self, event: Input.Changed) -> None:
        """Filter shortcuts based on search."""
        self.refresh_shortcuts(event.value.lower())
