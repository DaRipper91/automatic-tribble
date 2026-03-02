#!/usr/bin/env python3
"""
Main application entry point for File Manager
"""

from pathlib import Path
from textual.app import App
from textual.binding import Binding

from .start_menu import StartMenuScreen
from .config import ConfigManager


class FileManagerApp(App):
    """A dual-pane file manager TUI."""
    
    CSS = """
    Screen {
        background: $surface;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
    ]
    
    TITLE = "File Manager"

    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
    
    def on_mount(self) -> None:
        """Called when app starts."""
        self.load_configured_theme()
        self.push_screen(StartMenuScreen())

    def load_configured_theme(self) -> None:
        """Load and apply the configured theme."""
        theme_name = self.config_manager.get_theme()
        self.load_theme_by_name(theme_name)

    def load_theme_by_name(self, theme_name: str) -> None:
        """Load a specific theme by name."""
        try:
            theme_path = Path(__file__).parent / "themes" / f"{theme_name}.tcss"
            if theme_path.exists():
                with open(theme_path, "r") as f:
                    self.stylesheet.add_source(f.read())
                    self.refresh_css()
        except Exception as e:
            # Fallback to defaults if theme loading fails
            print(f"Failed to load theme {theme_name}: {e}")


def main():
    """Entry point for the application."""
    app = FileManagerApp()
    app.run()


if __name__ == "__main__":
    main()
