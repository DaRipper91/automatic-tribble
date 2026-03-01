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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_manager = ConfigManager()
    
    def on_mount(self) -> None:
        """Called when app starts."""
        self._load_theme()
        self.push_screen(StartMenuScreen())

    def _load_theme(self) -> None:
        """Load the configured theme."""
        theme_name = self.config_manager.get_theme()
        self.load_theme_by_name(theme_name)

    def load_theme_by_name(self, theme_name: str) -> None:
        """Load a specific theme by name."""
        theme_path = Path(__file__).parent / "themes" / f"{theme_name}.tcss"

        if theme_path.exists():
            try:
                theme_content = theme_path.read_text()
                # Determine if we can use existing stylesheet manipulation
                # For simplicity, we just add the source which overrides variables
                # Note: Repeatedly adding sources might grow memory, but for reasonable usage it's fine.
                # Ideally we would replace the theme layer.
                self.stylesheet.add_source(theme_content, str(theme_path))
                self.refresh_css()
            except Exception as e:
                self.notify(f"Failed to load theme {theme_name}: {e}", severity="error")
        else:
            # Fallback to dark if theme not found
            if theme_name != "dark":
                self.config_manager.set_theme("dark")
                self.load_theme_by_name("dark")


def main():
    """Entry point for the application."""
    app = FileManagerApp()
    app.run()


if __name__ == "__main__":
    main()