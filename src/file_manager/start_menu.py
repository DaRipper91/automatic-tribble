"""
Start Menu Screen for File Manager AI
"""
from pathlib import Path
import json
import importlib.metadata
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Button, Label, Static
from textual.containers import Container, Vertical

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

        try:
            version_str = importlib.metadata.version("termux-file-manager")
            version_str = f"v{version_str}"
        except importlib.metadata.PackageNotFoundError:
            version_str = "v0.1.0"

        with Container(id="menu-container"):
            with Vertical():
                # Logo and Version
                yield Static(self.LOGO, id="logo")
                yield Label(version_str, id="version")

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

        recent_file = Path.home() / ".tfm" / "recent.json"
        recent_dirs = []
        if recent_file.exists():
            try:
                with open(recent_file, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        recent_dirs = data
            except Exception:
                pass

        if not recent_dirs:
            recent_container.mount(Label("No recent history", classes="text-muted"))
        else:
            for path in recent_dirs[:5]:
                btn = Button(str(path), classes="recent-btn", variant="default")
                btn.tooltip = f"Open {path}"
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
