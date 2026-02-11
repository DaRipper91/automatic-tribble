"""
Screens for the file manager application.
"""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Label
from textual.containers import Container, Horizontal


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
