"""
Start Menu Screen for File Manager AI
"""
from pathlib import Path
from typing import Optional
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Button, Label, Static
from textual.containers import Container, Vertical, Horizontal, Grid
from rich.text import Text

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
        width: 80;
        height: auto;
        border: round $primary;
        padding: 2 4;
        background: $panel;
        align: center middle;
    }

    #logo {
        text-align: center;
        color: $accent;
        margin-bottom: 1;
        height: auto;
        text-style: bold;
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

    #recent-container {
        margin-top: 2;
        border-top: solid $secondary;
        padding-top: 1;
    }

    .section-title {
        text-align: center;
        color: $text-muted;
        margin-bottom: 1;
    }

    .recent-btn {
        width: 100%;
        margin-bottom: 1;
    }
    """

    LOGO = """
[bold cyan]  ████████╗███████╗███╗   ███╗[/bold cyan]
[bold cyan]  ╚══██╔══╝██╔════╝████╗ ████║[/bold cyan]
[bold blue]     ██║   █████╗  ██╔████╔██║[/bold blue]
[bold blue]     ██║   ██╔══╝  ██║╚██╔╝██║[/bold blue]
[bold magenta]     ██║   ██║     ██║ ╚═╝ ██║[/bold magenta]
[bold magenta]     ╚═╝   ╚═╝     ╚═╝     ╚═╝[/bold magenta]
"""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Container(id="menu-container"):
            with Vertical():
                # Logo and Version
                yield Static(self.LOGO, id="logo")
                yield Label("v0.1.0", id="version")

                # Main Actions
                yield Button("User Mode (File Manager)", id="user_mode", variant="primary", classes="menu-button")
                yield Button("AI Mode (Automation)", id="ai_mode", variant="success", classes="menu-button")

                # Recent Directories
                with Vertical(id="recent-container"):
                    yield Label("Recent Directories", classes="section-title")
                    # Populated dynamically
                    pass

        yield Footer()

    def on_mount(self) -> None:
        """Load recent directories on mount."""
        recent_container = self.query_one("#recent-container", Vertical)

        # We need to access ConfigManager via app
        # Since we modified App to have config_manager, this should work
        if hasattr(self.app, 'config_manager'):
            recent_dirs = self.app.config_manager.load_recent_directories()

            if not recent_dirs:
                recent_container.mount(Label("No recent history", classes="text-muted"))
            else:
                for path in recent_dirs:
                    btn = Button(str(path), classes="recent-btn", variant="default")
                    btn.tooltip = f"Open {path}"
                    # Store path in button ID or data?
                    # IDs must be valid CSS identifiers, paths contain / etc.
                    # We can use a custom attribute or just check label on press.
                    # Textual buttons don't have arbitrary data storage easily accessible in event unless subclassed.
                    # We can use the button's label text.
                    recent_container.mount(btn)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id

        if btn_id == "user_mode":
            self.app.push_screen(UserModeScreen())
        elif btn_id == "ai_mode":
            self.app.push_screen(AIModeScreen())
        elif "recent-btn" in event.button.classes:
            # Handle recent directory click
            path_str = str(event.button.label)
            path = Path(path_str)
            if path.exists() and path.is_dir():
                screen = UserModeScreen(initial_path=path)
                self.app.push_screen(screen)
            else:
                self.notify(f"Directory not found: {path}", severity="error")
