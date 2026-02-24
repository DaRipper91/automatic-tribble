"""
Theme Selection Screen
"""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Label, Button, RadioButton, RadioSet
from textual.containers import Vertical, Horizontal, Container
from textual.binding import Binding

from .config import ConfigManager

class ThemeSelectionScreen(ModalScreen):
    """Screen to select and preview themes."""

    CSS = """
    ThemeSelectionScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }

    #theme-container {
        width: 50;
        height: auto;
        background: $surface;
        border: heavy $primary;
        padding: 2;
        offset-y: 100%;
        transition: offset-y 0.3s;
    }

    #title {
        text-align: center;
        text-style: bold;
        margin-bottom: 2;
    }

    RadioSet {
        margin-bottom: 2;
        background: transparent;
    }

    #buttons {
        align: center bottom;
        height: 3;
        width: 100%;
        margin-top: 1;
    }

    Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    THEMES = ["dark", "light", "solarized", "dracula"]

    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.current_theme = self.config_manager.load_config().get("theme", "dark")
        self.selected_theme = self.current_theme

    def on_mount(self) -> None:
        self.query_one("#theme-container").styles.offset_y = "0"

    def compose(self) -> ComposeResult:
        with Container(id="theme-container"):
            yield Label("Select Theme", id="title")

            with RadioSet(id="theme-list"):
                for theme in self.THEMES:
                    yield RadioButton(theme.capitalize(), id=f"theme-{theme}", value=(theme == self.current_theme))

            with Horizontal(id="buttons"):
                yield Button("Apply", variant="primary", id="apply")
                yield Button("Cancel", variant="error", id="cancel")

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        if event.pressed.id and event.pressed.id.startswith("theme-"):
            theme_name = event.pressed.id[6:]
            self.selected_theme = theme_name
            # Check if App has apply_theme
            if hasattr(self.app, 'apply_theme'):
                self.app.apply_theme(theme_name)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "apply":
            config = self.config_manager.load_config()
            config["theme"] = self.selected_theme
            self.config_manager.save_config(config)
            self.dismiss(True)
        elif event.button.id == "cancel":
            self.action_cancel()

    def action_cancel(self) -> None:
        if self.selected_theme != self.current_theme:
            if hasattr(self.app, 'apply_theme'):
                self.app.apply_theme(self.current_theme)
        self.dismiss(False)
