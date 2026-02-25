"""
Start Menu Screen for File Manager AI
"""
from pathlib import Path
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Button, Label, Static
from textual.containers import Container, Vertical, Horizontal

from .user_mode import UserModeScreen
from .ai_mode import AIModeScreen
from .config import ConfigManager
from . import __version__

LOGO = """
[bold blue]
  _______ ______ __  __
 |__   __|  ____|  \/  |
    | |  | |__  | \  / |
    | |  |  __| | |\/| |
    | |  | |    | |  | |
    |_|  |_|    |_|  |_|
[/bold blue]
[italic]The Future Manager[/italic]
"""

class StartMenuScreen(Screen):
    """The main start menu with options for User Mode or AI Mode."""

    CSS = """
    StartMenuScreen {
        align: center middle;
        background: $surface;
    }

    #menu-container {
        width: 80;
        height: auto;
        border: heavy $primary;
        padding: 2;
        background: $panel;
    }

    #logo {
        width: 100%;
        margin-bottom: 2;
        content-align: center middle;
        text-align: center;
    }

    #version {
        width: 100%;
        text-align: center;
        color: $text-muted;
        margin-bottom: 2;
    }

    .menu-button {
        width: 100%;
        margin: 1 0;
        height: 3;
    }

    #recent-container {
        margin-top: 2;
        border-top: solid $secondary;
        padding-top: 1;
    }

    .recent-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
        width: 100%;
    }

    .recent-button {
        width: 100%;
        height: 3;
        margin-bottom: 0;
        border: none;
        background: $panel;
        color: $text;
        text-align: left;
    }

    .recent-button:hover {
        background: $boost;
        color: $primary;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        config_manager = ConfigManager()
        recent_dirs = config_manager.get_recent_directories()

        with Container(id="menu-container"):
            with Vertical():
                yield Static(LOGO, id="logo")
                yield Label(f"v{__version__}", id="version")

                yield Button("User Mode (File Manager)", id="user_mode", variant="primary", classes="menu-button")
                yield Button("AI Mode (Automation)", id="ai_mode", variant="success", classes="menu-button")
                yield Button("Quit", id="quit", variant="error", classes="menu-button")

                if recent_dirs:
                    with Vertical(id="recent-container"):
                        yield Label("Recent Directories", classes="recent-title")
                        for path in recent_dirs:
                            yield Button(f"📂 {path}", id=f"recent_{path}", classes="recent-button")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "user_mode":
            self.app.push_screen(UserModeScreen())
        elif event.button.id == "ai_mode":
            self.app.push_screen(AIModeScreen())
        elif event.button.id == "quit":
            self.app.exit()
        elif event.button.id and event.button.id.startswith("recent_"):
            path_str = event.button.id[7:] # remove "recent_"
            screen = UserModeScreen()
            screen.left_path = Path(path_str)
            self.app.push_screen(screen)
