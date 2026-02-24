"""
Help Overlay Screen
"""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Label, Input
from textual.containers import Vertical, Horizontal, Container
from textual.binding import Binding

class ShortcutRow(Horizontal):
    def __init__(self, key: str, desc: str):
        super().__init__(classes="shortcut-row")
        self.key = key
        self.desc = desc

    def compose(self) -> ComposeResult:
        yield Label(self.key, classes="key-badge")
        yield Label(self.desc, classes="description")

class HelpOverlay(ModalScreen):
    """A modal help screen with searchable shortcuts."""

    CSS = """
    HelpOverlay {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }

    #help-container {
        width: 80%;
        height: 80%;
        background: $surface;
        border: heavy $primary;
        padding: 1 2;
        offset-y: 100%;
        transition: offset-y 0.3s;
    }

    #search-box {
        margin-bottom: 1;
    }

    .title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
        width: 100%;
    }

    .category-title {
        text-style: bold;
        color: $accent;
        margin-top: 1;
        border-bottom: solid $secondary;
        width: 100%;
    }

    .shortcut-row {
        height: 1;
        margin: 0 1;
        width: 100%;
    }

    .key-badge {
        background: $boost;
        color: $text; /* Using $text, might need fallback logic or rely on theme */
        padding: 0 1;
        min-width: 15;
        text-align: center;
        text-style: bold;
    }

    .description {
        margin-left: 2;
        color: $secondary; /* Fallback from $text-muted */
    }

    #shortcuts-list {
        height: 1fr;
        overflow-y: auto;
    }
    """

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
    ]

    SHORTCUTS = {
        "Navigation": [
            ("Up/Down", "Navigate list"),
            ("Enter", "Open file/directory"),
            ("Tab", "Switch panel"),
            ("Ctrl+T", "New Tab"),
            ("Ctrl+W", "Close Tab"),
            ("Ctrl+Tab", "Next Tab"),
            ("Esc", "Back / Close Modal"),
        ],
        "File Operations": [
            ("C", "Copy"),
            ("M", "Move"),
            ("D", "Delete"),
            ("R", "Rename"),
            ("N", "New Directory"),
        ],
        "Selection": [
            ("Space", "Toggle selection"),
            ("Shift+Up/Down", "Range selection"),
            ("Ctrl+A", "Select All"),
            ("Ctrl+D", "Deselect All"),
        ],
        "View": [
            ("P", "Toggle Preview Pane"),
            ("Ctrl+R", "Refresh"),
            ("H", "Help"),
            ("Ctrl+Shift+T", "Change Theme"),
        ],
        "AI Mode": [
            ("Type command", "Execute AI task"),
        ]
    }

    def compose(self) -> ComposeResult:
        with Container(id="help-container"):
            yield Label("Keyboard Shortcuts", classes="title")
            yield Input(placeholder="Search shortcuts...", id="search-box")
            with Vertical(id="shortcuts-list"):
                pass # Populated in on_mount

    def on_mount(self) -> None:
        self.query_one("#help-container").styles.offset_y = "0"
        self.update_shortcuts()

    def on_input_changed(self, event: Input.Changed) -> None:
        self.update_shortcuts(event.value)

    def update_shortcuts(self, query: str = "") -> None:
        container = self.query_one("#shortcuts-list")
        container.remove_children()

        query = query.lower()

        widgets = []
        for category, shortcuts in self.SHORTCUTS.items():
            filtered = [s for s in shortcuts if query in s[0].lower() or query in s[1].lower()]

            if filtered:
                widgets.append(Label(category, classes="category-title"))
                for key, desc in filtered:
                    widgets.append(ShortcutRow(key, desc))

        if widgets:
            container.mount(*widgets)
        else:
            container.mount(Label("No shortcuts found", classes="no-shortcuts"))
