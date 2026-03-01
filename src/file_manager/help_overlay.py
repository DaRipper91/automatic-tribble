from textual.screen import ModalScreen
from textual.widgets import Label, Input, Button
from textual.containers import Container, Vertical, Horizontal
from textual.app import ComposeResult
from textual.binding import Binding

class HelpOverlay(ModalScreen):
    """A searchable help overlay showing keyboard shortcuts."""

    CSS = """
    HelpOverlay {
        align: center middle;
        background: $background 80%;
    }

    #help-container {
        width: 80%;
        height: 80%;
        background: $surface;
        border: thick $primary;
        padding: 1;
        opacity: 0.0; /* Start invisible for animation */
    }

    #search-box {
        dock: top;
        margin-bottom: 1;
    }

    #shortcuts-content {
        height: 1fr;
        overflow-y: auto;
    }

    .category-box {
        height: auto;
        border: solid $secondary;
        padding: 1;
        margin-bottom: 1;
    }

    .category-title {
        text-style: bold;
        color: $accent;
        border-bottom: solid $secondary;
        margin-bottom: 1;
        width: 100%;
    }

    .shortcut-row {
        height: auto;
        layout: horizontal;
        padding: 0 1;
        margin-top: 1;
    }

    .key-badge {
        background: $primary;
        color: $text;
        padding: 0 1;
        text-style: bold;
        width: 20%;
        text-align: center;
    }

    .description {
        width: 80%;
        padding-left: 2;
        color: $text;
    }

    #footer {
        dock: bottom;
        height: auto;
        align: center bottom;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
    ]

    SHORTCUTS = {
        "Navigation": [
            ("Up/Down", "Move cursor"),
            ("Enter", "Open directory"),
            ("Tab", "Switch Panel"),
            ("Ctrl+T", "New Tab"),
            ("Ctrl+W", "Close Tab"),
            ("Ctrl+Tab", "Next Tab"),
            ("Esc", "Back / Cancel"),
        ],
        "File Operations": [
            ("Space", "Toggle Selection"),
            ("Shift+Up/Down", "Range Selection"),
            ("Ctrl+A", "Select All"),
            ("Ctrl+D", "Deselect All"),
            ("c", "Copy selected"),
            ("m", "Move selected"),
            ("d", "Delete selected"),
            ("r", "Rename"),
            ("n", "New Directory"),
        ],
        "View": [
            ("p", "Toggle Preview Pane"),
            ("ctrl+r", "Refresh"),
            ("h", "Toggle Help"),
        ],
        "General": [
            ("q", "Quit"),
        ]
    }

    def compose(self) -> ComposeResult:
        with Container(id="help-container"):
            yield Label("Keyboard Shortcuts", classes="category-title")
            yield Input(placeholder="Search shortcuts...", id="search-box")

            with Vertical(id="shortcuts-content"):
                # Content populated in on_mount
                pass

            with Horizontal(id="footer"):
                yield Button("Close", variant="primary", id="close-btn")

    def on_mount(self) -> None:
        container = self.query_one("#shortcuts-content", Vertical)
        self._populate_shortcuts(container, "")

        # Animation
        main_container = self.query_one("#help-container")
        main_container.styles.animate("opacity", 1.0, duration=0.2)

    def on_input_changed(self, event: Input.Changed) -> None:
        container = self.query_one("#shortcuts-content", Vertical)
        container.remove_children()
        self._populate_shortcuts(container, event.value)

    def _populate_shortcuts(self, container: Vertical, query: str) -> None:
        query = query.lower()
        has_results = False

        for category, items in self.SHORTCUTS.items():
            filtered_items = []
            for key, desc in items:
                if query in key.lower() or query in desc.lower() or query in category.lower():
                    filtered_items.append((key, desc))

            if filtered_items:
                has_results = True
                cat_box = Vertical(classes="category-box")
                cat_box.mount(Label(category, classes="category-title"))

                for key, desc in filtered_items:
                    row = Horizontal(classes="shortcut-row")
                    row.mount(Label(key, classes="key-badge"))
                    row.mount(Label(desc, classes="description"))
                    cat_box.mount(row)

                container.mount(cat_box)

        if not has_results:
             container.mount(Label("No shortcuts found.", classes="description"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()
