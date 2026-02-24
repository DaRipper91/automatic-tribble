#!/usr/bin/env python3
"""
Main application entry point for File Manager
"""

from textual.app import App
from textual.binding import Binding
from pathlib import Path

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
        config = self.config_manager.load_config()
        self.apply_theme(config.get('theme', 'dark'))
        self.push_screen(StartMenuScreen())

    def apply_theme(self, theme_name: str) -> None:
        """Apply the selected theme."""
        theme_path = Path(__file__).parent / "themes" / f"{theme_name}.tcss"
        if theme_path.exists():
            try:
                with open(theme_path, 'r') as f:
                    theme_css = f.read()
                if hasattr(self, 'stylesheet') and hasattr(self.stylesheet, 'add_source'):
                    self.stylesheet.add_source(theme_css)
                    self.refresh_css()
            except Exception as e:
                # Fallback or log error
                pass


def main():
    """Entry point for the application."""
    app = FileManagerApp()
    app.run()


if __name__ == "__main__":
    main()