"""
Start Menu Screen for File Manager AI
"""
from pathlib import Path
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Button, Label, Static
from textual.containers import Container, Vertical
from textual import on

from .user_mode import UserModeScreen
from .ai_mode import AIModeScreen
from .config import ConfigManager
from . import __version__

ASCII_LOGO = """
 [bold blue]████████╗███████╗███╗   ███╗[/]
 [bold blue]╚══██╔══╝██╔════╝████╗ ████║[/]
 [bold blue]   ██║   █████╗  ██╔████╔██║[/]
 [bold blue]   ██║   ██╔══╝  ██║╚██╔╝██║[/]
 [bold blue]   ██║   ██║     ██║ ╚═╝ ██║[/]
 [bold blue]   ╚═╝   ╚═╝     ╚═╝     ╚═╝[/]
"""

class StartMenuScreen(Screen):
    """The main start menu with options for User Mode or AI Mode."""

    CSS = """
    StartMenuScreen {
        align: center middle;
        background: $surface;
    }

    #menu-container {
        width: 70;
        height: auto;
        border: heavy $primary;
        padding: 2;
        background: $panel;
    }

    #logo {
        text-align: center;
        margin-bottom: 1;
        height: auto;
    }

    #version {
        text-align: center;
        color: $text-muted;
        margin-bottom: 2;
    }

    .menu-button {
        width: 100%;
        margin: 1 0;
        height: 3;
    }

    #recent-section {
        margin-top: 2;
        border-top: solid $secondary;
        padding-top: 1;
    }

    .section-title {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }

    .recent-btn {
        width: 100%;
        margin-bottom: 1;
        height: 3;
    }

    #instructions {
        margin-top: 1;
        text-align: center;
        color: $text-muted;
    }
    """

    def compose(self) -> ComposeResult:
        config_manager = ConfigManager()
        recent_dirs = config_manager.load_recent_dirs()

        yield Header(show_clock=True)

        with Container(id="menu-container"):
            with Vertical():
                yield Static(ASCII_LOGO, id="logo")
                yield Label(f"Version {__version__}", id="version")

                yield Button("User Mode (File Manager)", id="user_mode", variant="primary", classes="menu-button")
                yield Button("AI Mode (Automation)", id="ai_mode", variant="success", classes="menu-button")

                if recent_dirs:
                    with Vertical(id="recent-section"):
                        yield Label("Recent Directories", classes="section-title")
                        for path_str in recent_dirs:
                            yield Button(path_str, classes="recent-btn", variant="default")

                yield Label("Select a mode to continue", id="instructions")

        yield Footer()

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "user_mode":
            self.app.push_screen(UserModeScreen())
        elif event.button.id == "ai_mode":
            self.app.push_screen(AIModeScreen())
        elif "recent-btn" in event.button.classes:
            path_str = str(event.button.label)
            self.app.push_screen(UserModeScreen(initial_path=Path(path_str)))
