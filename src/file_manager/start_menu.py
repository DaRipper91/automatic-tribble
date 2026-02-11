"""
Start Menu Screen for File Manager AI
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Button, Label, Static
from textual.containers import Container, Vertical, Center

from .user_mode import UserModeScreen
from .ai_mode import AIModeScreen


class StartMenuScreen(Screen):
    """The main start menu with options for User Mode or AI Mode."""

    CSS = """
    StartMenuScreen {
        align: center middle;
        background: $surface;
    }

    #menu-container {
        width: 60;
        height: auto;
        border: heavy $primary;
        padding: 2;
        background: $panel;
    }

    #title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 2;
    }

    .menu-button {
        width: 100%;
        margin: 1 0;
        height: 3;
    }

    #instructions {
        margin-top: 2;
        text-align: center;
        color: $text-muted;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Container(id="menu-container"):
            with Vertical():
                yield Label("FILE MANAGER AI", id="title")
                yield Button("User Mode (File Manager)", id="user_mode", variant="primary", classes="menu-button")
                yield Button("AI Mode (Automation)", id="ai_mode", variant="success", classes="menu-button")
                yield Label("Select a mode to continue", id="instructions")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "user_mode":
            self.app.push_screen(UserModeScreen())
        elif event.button.id == "ai_mode":
            self.app.push_screen(AIModeScreen())
