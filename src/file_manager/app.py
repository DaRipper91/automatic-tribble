#!/usr/bin/env python3
"""
Main application entry point for File Manager
"""

from textual.app import App
from textual.binding import Binding

from .start_menu import StartMenuScreen


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
        self.push_screen(StartMenuScreen())


def main():
    """Entry point for the application."""
    app = FileManagerApp()
    app.run()


if __name__ == "__main__":
    main()