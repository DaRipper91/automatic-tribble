from textual.screen import ModalScreen
from textual.widgets import Input, Label, Static, Button
from textual.containers import Container, Vertical, Grid
from textual.app import ComposeResult
from textual.binding import Binding
from rich.text import Text

class HelpOverlay(ModalScreen):
    """Richly formatted full-screen help overlay."""

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
        padding: 2;
    }

    #search-bar {
        margin-bottom: 2;
    }

    #shortcuts-grid {
        height: 1fr;
        overflow-y: auto;
        layout: grid;
        grid-size: 2;
        grid-gutter: 1 2;
    }

    .category-box {
        height: auto;
        border: solid $secondary;
        padding: 1;
        margin-bottom: 1;
        background: $panel;
    }

    #title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #close-btn {
        width: 100%;
        margin-top: 1;
    }
    """

    BINDINGS = [Binding("escape", "dismiss", "Close")]

    SHORTCUTS = {
        "Navigation": [
            ("Tab", "Switch Panel"),
            ("Arrow Keys", "Navigate Files"),
            ("Enter", "Open / Enter Directory"),
            ("Ctrl+T", "New Tab"),
            ("Ctrl+W", "Close Tab"),
            ("Ctrl+Tab", "Next Tab"),
            ("Esc", "Back / Close"),
        ],
        "File Operations": [
            ("C", "Copy Selection"),
            ("M", "Move Selection"),
            ("D", "Delete Selection"),
            ("N", "New Directory"),
            ("R", "Rename"),
        ],
        "Selection": [
            ("Space", "Toggle Selection"),
            ("Ctrl+A", "Select All"),
            ("Ctrl+D", "Deselect All"),
        ],
        "View": [
            ("P", "Toggle Preview"),
            ("Ctrl+R", "Refresh"),
            # Theme switcher binding is not explicitly on screen unless I added it?
            # Prompt says "in-app theme switcher accessible via Ctrl+Shift+T"
            ("Ctrl+Shift+T", "Change Theme"),
        ],
        "General": [
            ("H", "Toggle Help"),
            ("Q", "Quit"),
        ]
    }

    def compose(self) -> ComposeResult:
        with Container(id="help-container"):
            yield Label("Keyboard Shortcuts", id="title")
            yield Input(placeholder="Search shortcuts...", id="search-bar")

            with Container(id="shortcuts-grid"):
                pass

            yield Button("Close", variant="primary", id="close-btn")

    async def on_mount(self) -> None:
        await self.update_shortcuts()
        self.query_one(Input).focus()

    async def on_input_changed(self, event: Input.Changed) -> None:
        await self.update_shortcuts(event.value)

    async def update_shortcuts(self, query: str = "") -> None:
        grid = self.query_one("#shortcuts-grid", Container)
        # Use query_children to remove
        for child in grid.query(".category-box"):
            await child.remove()

        query = query.lower()

        for category, items in self.SHORTCUTS.items():
            filtered = [
                (k, v) for k, v in items
                if query in k.lower() or query in v.lower() or query in category.lower()
            ]

            if filtered:
                # Construct Rich Renderable
                text = Text()
                text.append(f"{category}\n", style="bold underline $accent")
                text.append("\n")
                for k, v in filtered:
                    text.append(f" {k:<15}", style="bold reverse $primary")
                    text.append(f" {v}\n")

                await grid.mount(Static(text, classes="category-box"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()
