"""
Start Menu Screen for File Manager AI
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Button, Label, Static
from textual.containers import Container, Vertical
from pathlib import Path

from .user_mode import UserModeScreen
from .ai_mode import AIModeScreen
from .config import ConfigManager


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

    #title {
        text-align: center;
        color: $accent;
        margin-bottom: 1;
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

    #recent-list {
        margin-top: 1;
        padding: 1;
        background: $boost;
        height: auto;
        border: solid $secondary;
    }

    .recent-button {
        width: 100%;
        text-align: left;
        background: transparent;
        border: none;
        height: 1;
        padding: 0 1;
    }

    .recent-button:hover {
        background: $accent;
        color: $surface;
    }

    #instructions {
        margin-top: 2;
        text-align: center;
        color: $text-muted;
    }

    #recent-header {
        color: $primary;
        text-style: bold;
        margin-top: 1;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_manager = ConfigManager()
        self.recent_paths = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Container(id="menu-container"):
            with Vertical():
                logo = """
 ██████╗ ██████╗ ███╗   ███╗
   ██╔═╝ ██╔═══╝ ████╗ ████║
   ██║   █████╗  ██╔████╔██║
   ██║   ██╔══╝  ██║╚██╔╝██║
   ██║   ██║     ██║ ╚═╝ ██║
   ╚═╝   ╚═╝     ╚═╝     ╚═╝
"""
                yield Static(logo, id="title")
                yield Label("v0.1.0", id="version")

                yield Button("User Mode (File Manager)", id="user_mode", variant="primary", classes="menu-button")
                yield Button("AI Mode (Automation)", id="ai_mode", variant="success", classes="menu-button")

                self.recent_paths = self.config_manager.load_recent_dirs()
                if self.recent_paths:
                    yield Label("Recent Directories:", id="recent-header")
                    with Vertical(id="recent-list"):
                        for i, path in enumerate(self.recent_paths):
                             yield Button(str(path), id=f"recent_{i}", classes="recent-button")

                yield Label("Select a mode to continue", id="instructions")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "user_mode":
            self.app.push_screen(UserModeScreen())
        elif event.button.id == "ai_mode":
            self.app.push_screen(AIModeScreen())
        elif event.button.id and event.button.id.startswith("recent_"):
            try:
                idx = int(event.button.id[7:])
                if 0 <= idx < len(self.recent_paths):
                    path = self.recent_paths[idx]
                    self.app.push_screen(UserModeScreen(initial_path=str(path)))
            except (ValueError, TypeError):
                pass
