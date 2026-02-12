#!/usr/bin/env python3
"""
Main application entry point for File Manager
"""

from pathlib import Path
from typing import Optional, Dict, Any
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Label
from textual.binding import Binding
from textual.reactive import reactive

from .file_operations import FileOperations
from .file_panel import FilePanel
from .screens import ConfirmationScreen, HelpScreen, StartupScreen, LauncherScreen, ProgressScreen
from .utils import find_gemini_executable


class FileManagerApp(App):
    """A dual-pane file manager TUI."""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #main-container {
        height: 100%;
    }
    
    #panels-container {
        height: 1fr;
    }
    
    .file-panel {
        width: 1fr;
        border: solid $primary;
        height: 100%;
    }
    
    .file-panel.active {
        border: solid $accent;
    }
    
    /* Single Panel Mode CSS */
    .single-mode #right-panel {
        display: none;
    }

    .single-mode #left-panel {
        width: 100%;
    }

    #status-bar {
        height: 3;
        background: $panel;
        padding: 1;
    }
    
    #help-text {
        text-align: center;
        color: $text-muted;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("tab", "switch_panel", "Switch Panel"),
        Binding("c", "copy", "Copy"),
        Binding("m", "move", "Move"),
        Binding("d", "delete", "Delete"),
        Binding("n", "new_dir", "New Dir"),
        Binding("r", "rename", "Rename"),
        Binding("h", "toggle_help", "Help"),
        Binding("ctrl+r", "refresh", "Refresh"),
        Binding("escape", "close_panel", "Close Panel"),
    ]
    
    TITLE = "File Manager"
    
    active_panel = reactive(0)  # 0 for left, 1 for right
    layout_mode = reactive("dual") # "dual" or "single"
    
    def __init__(self, mode: str = "dual"):
        super().__init__()
        self.file_ops = FileOperations()
        self.layout_mode = mode
        
        # Default paths - both panels start at home directory
        self.left_path = Path.home()
        self.right_path = Path.home()
        
        self.is_temporary_dual = False
        self.gemini_path: Optional[str] = None

        # Store pending operation (type, source_path)
        self.pending_operation: Optional[Dict[str, Any]] = None

    def compose(self) -> ComposeResult:
        """Create the layout."""
        yield Header()
        
        with Container(id="main-container"):
            # Add class for single mode if needed
            classes = "single-mode" if self.layout_mode == "single" else ""

            with Horizontal(id="panels-container", classes=classes):
                yield FilePanel(
                    str(self.left_path),
                    id="left-panel",
                    classes="file-panel active"
                )
                yield FilePanel(
                    str(self.right_path),
                    id="right-panel", 
                    classes="file-panel"
                )
            
            with Vertical(id="status-bar"):
                yield Label(
                    f"Left: {self.left_path} | Right: {self.right_path}",
                    id="paths-info"
                )
                yield Label(
                    "Tab: Switch | C: Copy | M: Move | D: Delete | N: New Dir | R: Rename | Q: Quit",
                    id="help-text"
                )
        
        yield Footer()

    def on_mount(self) -> None:
        """Called when app is mounted."""
        self.gemini_path = find_gemini_executable()
        if self.gemini_path:
            self.notify(f"AI Mode enabled (Gemini found at {self.gemini_path})")

        # Ensure layout matches initial mode
        self._update_layout()

        # Show Startup Screen then Launcher
        # Push Launcher first, then Startup so Startup is on top
        self.push_screen(LauncherScreen())
        self.push_screen(StartupScreen())

    def watch_layout_mode(self, mode: str) -> None:
        """React to layout mode changes."""
        self._update_layout()

    def _update_layout(self) -> None:
        """Update CSS classes based on layout mode."""
        try:
            container = self.query_one("#panels-container")
            if self.layout_mode == "single":
                container.add_class("single-mode")
                # Ensure left panel is active and focused
                self.active_panel = 0
                self.query_one("#left-panel").add_class("active")
                self.query_one("#right-panel").remove_class("active")
            else:
                container.remove_class("single-mode")
        except Exception:
            pass # Widget might not be mounted yet

    def action_switch_panel(self) -> None:
        """Switch between left and right panels."""
        if self.layout_mode == "single":
            return # No switching in single mode

        self.active_panel = 1 - self.active_panel
        
        left_panel = self.query_one("#left-panel", FilePanel)
        right_panel = self.query_one("#right-panel", FilePanel)
        
        if self.active_panel == 0:
            left_panel.add_class("active")
            right_panel.remove_class("active")
            left_panel.focus()
        else:
            right_panel.add_class("active")
            left_panel.remove_class("active")
            right_panel.focus()
    
    def action_close_panel(self) -> None:
        """Close the second panel if in temporary dual mode."""
        if self.is_temporary_dual:
            self.layout_mode = "single"
            self.is_temporary_dual = False
            self.pending_operation = None
            self.notify("Cancelled operation. Returned to Single Panel Mode")

    def action_copy(self) -> None:
        """Copy selected file/directory."""

        # Check for pending copy operation
        if self.pending_operation and self.pending_operation["type"] == "copy":
            source_path = self.pending_operation["source"]
            target_panel = self.get_active_panel() # We are now in the target panel
            target_dir = target_panel.current_dir

            async def run_copy():
                progress = ProgressScreen(f"Copying {source_path.name}...")
                self.push_screen(progress)
                try:
                    await self.run_in_thread(self.file_ops.copy, source_path, target_dir)
                    self.notify(f"Copied {source_path.name} to {target_dir}")
                    target_panel.refresh_view()

                    # Cleanup
                    self.pending_operation = None
                    if self.is_temporary_dual:
                        self.layout_mode = "single"
                        self.is_temporary_dual = False
                        self.notify("Copy complete.")
                except Exception as e:
                    self.notify(f"Error copying: {str(e)}", severity="error")
                finally:
                    progress.dismiss()

            self.run_worker(run_copy(), exclusive=True)
            return

        # Handle Single Mode transition
        if self.layout_mode == "single":
            active_panel_widget = self.get_active_panel()
            selected_path = active_panel_widget.get_selected_path()
            if not selected_path:
                self.notify("No file selected", severity="error")
                return

            self.pending_operation = {"type": "copy", "source": selected_path}
            self.layout_mode = "dual"
            self.is_temporary_dual = True
            # Switch focus to the right panel (destination)
            self.action_switch_panel()
            self.notify(f"Copying {selected_path.name}. Select destination and press 'C' to confirm.")
            return

        # Normal Dual Mode Copy
        active_panel_widget = self.get_active_panel()
        selected_path = active_panel_widget.get_selected_path()
        
        if selected_path:
            target_panel = self.get_inactive_panel()
            target_dir = target_panel.current_dir
            
            async def run_normal_copy():
                progress = ProgressScreen(f"Copying {selected_path.name}...")
                self.push_screen(progress)
                try:
                    await self.run_in_thread(self.file_ops.copy, selected_path, target_dir)
                    self.notify(f"Copied {selected_path.name} to {target_dir}")
                    target_panel.refresh_view()
                except Exception as e:
                    self.notify(f"Error copying: {str(e)}", severity="error")
                finally:
                    progress.dismiss()

            self.run_worker(run_normal_copy(), exclusive=True)
    
    def action_move(self) -> None:
        """Move selected file/directory."""

        # Check for pending move operation
        if self.pending_operation and self.pending_operation["type"] == "move":
            source_path = self.pending_operation["source"]
            target_panel = self.get_active_panel()
            target_dir = target_panel.current_dir

            async def run_move():
                progress = ProgressScreen(f"Moving {source_path.name}...")
                self.push_screen(progress)
                try:
                    await self.run_in_thread(self.file_ops.move, source_path, target_dir)
                    self.notify(f"Moved {source_path.name} to {target_dir}")
                    target_panel.refresh_view()
                    # Refresh source panel (inactive)
                    self.get_inactive_panel().refresh_view()

                    # Cleanup
                    self.pending_operation = None
                    if self.is_temporary_dual:
                        self.layout_mode = "single"
                        self.is_temporary_dual = False
                        self.notify("Move complete.")
                except Exception as e:
                    self.notify(f"Error moving: {str(e)}", severity="error")
                finally:
                    progress.dismiss()

            self.run_worker(run_move(), exclusive=True)
            return

        # Handle Single Mode transition
        if self.layout_mode == "single":
            active_panel_widget = self.get_active_panel()
            selected_path = active_panel_widget.get_selected_path()
            if not selected_path:
                self.notify("No file selected", severity="error")
                return

            self.pending_operation = {"type": "move", "source": selected_path}
            self.layout_mode = "dual"
            self.is_temporary_dual = True
            # Switch focus to the right panel
            self.action_switch_panel()
            self.notify(f"Moving {selected_path.name}. Select destination and press 'M' to confirm.")
            return

        # Normal Dual Mode Move
        active_panel_widget = self.get_active_panel()
        selected_path = active_panel_widget.get_selected_path()
        
        if selected_path:
            target_panel = self.get_inactive_panel()
            target_dir = target_panel.current_dir
            
            async def run_normal_move():
                progress = ProgressScreen(f"Moving {selected_path.name}...")
                self.push_screen(progress)
                try:
                    await self.run_in_thread(self.file_ops.move, selected_path, target_dir)
                    self.notify(f"Moved {selected_path.name} to {target_dir}")
                    active_panel_widget.refresh_view()
                    target_panel.refresh_view()
                except Exception as e:
                    self.notify(f"Error moving: {str(e)}", severity="error")
                finally:
                    progress.dismiss()

            self.run_worker(run_normal_move(), exclusive=True)
    
    def action_delete(self) -> None:
        """Delete selected file/directory."""
        active_panel_widget = self.get_active_panel()
        selected_path = active_panel_widget.get_selected_path()
        
        if selected_path:
            def check_confirm(confirmed: bool) -> None:
                if confirmed:
                    async def run_delete():
                        progress = ProgressScreen(f"Deleting {selected_path.name}...")
                        self.push_screen(progress)
                        try:
                            await self.run_in_thread(self.file_ops.delete, selected_path)
                            self.notify(f"Deleted {selected_path.name}")
                            active_panel_widget.refresh_view()
                        except Exception as e:
                            self.notify(f"Error deleting: {str(e)}", severity="error")
                        finally:
                            progress.dismiss()

                    self.run_worker(run_delete(), exclusive=True)

            self.push_screen(
                ConfirmationScreen(f"Are you sure you want to delete {selected_path.name}?"),
                check_confirm
            )
    
    def action_new_dir(self) -> None:
        """Create a new directory."""
        self.notify("New directory creation - feature placeholder")
    
    def action_rename(self) -> None:
        """Rename selected file/directory."""
        self.notify("Rename - feature placeholder")
    
    def action_refresh(self) -> None:
        """Refresh both panels."""
        left_panel = self.query_one("#left-panel", FilePanel)
        right_panel = self.query_one("#right-panel", FilePanel)
        left_panel.refresh_view()
        right_panel.refresh_view()
        self.notify("Refreshed")
    
    def action_toggle_help(self) -> None:
        """Toggle help display."""
        self.push_screen(HelpScreen())
    
    def get_active_panel(self) -> FilePanel:
        """Get the currently active file panel."""
        if self.active_panel == 0:
            return self.query_one("#left-panel", FilePanel)
        else:
            return self.query_one("#right-panel", FilePanel)
    
    def get_inactive_panel(self) -> FilePanel:
        """Get the currently inactive file panel."""
        if self.active_panel == 1:
            return self.query_one("#left-panel", FilePanel)
        else:
            return self.query_one("#right-panel", FilePanel)


def main():
    """Entry point for the application."""
    app = FileManagerApp()
    app.run()


if __name__ == "__main__":
    main()
