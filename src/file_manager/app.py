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
    
    def on_mount(self) -> None:
        """Called when app starts."""
        self.config_manager = ConfigManager()
        self.load_theme()
        self.push_screen(StartMenuScreen())

    def load_theme(self) -> None:
        """Load and apply the configured theme."""
        theme_name = self.config_manager.get_theme()
        self.apply_theme(theme_name)

    def apply_theme(self, theme_name: str) -> None:
        """Apply a theme by name."""
        theme_path = Path(__file__).parent / "themes" / f"{theme_name}.tcss"
        if not theme_path.exists():
            theme_path = Path(__file__).parent / "themes" / "dark.tcss"

        if theme_path.exists():
            try:
                with open(theme_path, "r") as f:
                    # Adding source appends CSS rules. Variables defined later override earlier ones.
                    self.stylesheet.add_source(f.read())
                self.refresh_css()
            except Exception as e:
                self.notify(f"Error loading theme: {e}", severity="error")


def main():
    """Entry point for the application."""
    app = FileManagerApp()
    app.run()


if __name__ == "__main__":
    main()
