"""
Screens for the file manager application.
"""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Label
from textual.containers import Container, Horizontal, Vertical


class ConfirmationScreen(ModalScreen[bool]):
    """Screen for confirming actions."""

    CSS = """
    ConfirmationScreen {
        align: center middle;
    }

    #dialog {
        padding: 0 1;
        width: 60;
        height: 11;
        border: thick $background 80%;
        background: $surface;
    }

    #question {
        content-align: center middle;
        height: 1fr;
        width: 100%;
    }

    #buttons {
        height: auto;
        width: 100%;
        align: center bottom;
        dock: bottom;
        margin-bottom: 1;
    }

    Button {
        margin: 0 1;
        width: 1fr;
    }
    """

    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label(self.message, id="question")
            with Horizontal(id="buttons"):
                yield Button("Cancel", variant="primary", id="cancel")
                yield Button("Delete", variant="error", id="confirm")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm":
            self.dismiss(True)
        else:
            self.dismiss(False)


class HelpScreen(ModalScreen):
    """Screen for displaying help/keybindings."""

    CSS = """
    HelpScreen {
        align: center middle;
    }

    #help-dialog {
        padding: 1 2;
        width: 60;
        height: auto;
        border: thick $background 80%;
        background: $surface;
    }

    .title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
        width: 100%;
    }

    .key-row {
        height: auto;
        padding: 0 1;
        margin-bottom: 0;
    }

    .key {
        width: 30%;
        text-style: bold;
        color: $accent;
    }

    .description {
        width: 70%;
    }

    #close-button {
        margin-top: 1;
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="help-dialog"):
            yield Label("Keyboard Shortcuts", classes="title")

            shortcuts = [
                ("Tab", "Switch Panel"),
                ("Arrow Keys", "Navigate"),
                ("Enter", "Open / Select"),
                ("c", "Copy"),
                ("m", "Move"),
                ("d", "Delete"),
                ("n", "New Directory"),
                ("r", "Rename"),
                ("ctrl+r", "Refresh"),
                ("h", "Toggle Help"),
                ("q", "Quit"),
            ]

            with Vertical(id="shortcuts-list"):
                for key, desc in shortcuts:
                    with Horizontal(classes="key-row"):
                        yield Label(key, classes="key")
                        yield Label(desc, classes="description")

            yield Button("Close", variant="primary", id="close-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()
