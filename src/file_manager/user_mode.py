"""
User Mode Screen - Standard File Manager Interface
"""

from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Label
from textual.binding import Binding
from textual.reactive import reactive
from textual.screen import Screen
from textual.worker import work

from .file_operations import FileOperations
from .file_panel import FilePanel
from .screens import ConfirmationScreen, HelpScreen


class UserModeScreen(Screen):
    """The main file manager interface."""

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
        Binding("escape", "back_to_menu", "Back to Menu", priority=True),
        Binding("tab", "switch_panel", "Switch Panel"),
        Binding("c", "copy", "Copy"),
        Binding("m", "move", "Move"),
        Binding("d", "delete", "Delete"),
        Binding("n", "new_dir", "New Dir"),
        Binding("r", "rename", "Rename"),
        Binding("h", "toggle_help", "Help"),
        Binding("ctrl+r", "refresh", "Refresh"),
    ]

    active_panel = reactive(0)  # 0 for left, 1 for right

    def __init__(self):
        super().__init__()
        self.file_ops = FileOperations()

        # Default paths - both panels start at home directory
        self.left_path = Path.home()
        self.right_path = Path.home()

    def compose(self) -> ComposeResult:
        """Create the layout."""
        yield Header()

        with Container(id="main-container"):
            with Horizontal(id="panels-container"):
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
                    "Tab: Switch | C: Copy | M: Move | D: Delete | N: New Dir | R: Rename | Esc: Back",
                    id="help-text"
                )

        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        # Ensure left panel is focused initially
        self.query_one("#left-panel", FilePanel).focus()

    def action_back_to_menu(self) -> None:
        """Return to the main menu."""
        self.app.pop_screen()

    def action_switch_panel(self) -> None:
        """Switch between left and right panels."""
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

    def action_copy(self) -> None:
        """Copy selected file/directory."""
        active_panel_widget = self.get_active_panel()
        selected_path = active_panel_widget.get_selected_path()

        if selected_path:
            target_panel = self.get_inactive_panel()
            target_dir = target_panel.current_dir
            self._do_copy(selected_path, target_dir, target_panel)

    @work(thread=True, exclusive=True)
    def _do_copy(self, selected_path: Path, target_dir: Path, target_panel: FilePanel) -> None:
        """Perform copy operation in a background thread."""
        try:
            self.file_ops.copy(selected_path, target_dir)
            self.notify(f"Copied {selected_path.name} to {target_dir}")
            target_panel.refresh_view()
        except Exception as e:
            self.notify(f"Error copying: {str(e)}", severity="error")

    def action_move(self) -> None:
        """Move selected file/directory."""
        active_panel_widget = self.get_active_panel()
        selected_path = active_panel_widget.get_selected_path()

        if selected_path:
            target_panel = self.get_inactive_panel()
            target_dir = target_panel.current_dir
            self._do_move(selected_path, target_dir, active_panel_widget, target_panel)

    @work(thread=True, exclusive=True)
    def _do_move(self, selected_path: Path, target_dir: Path, active_panel: FilePanel, target_panel: FilePanel) -> None:
        """Perform move operation in a background thread."""
        try:
            self.file_ops.move(selected_path, target_dir)
            self.notify(f"Moved {selected_path.name} to {target_dir}")
            active_panel.refresh_view()
            target_panel.refresh_view()
        except Exception as e:
            self.notify(f"Error moving: {str(e)}", severity="error")

    def action_delete(self) -> None:
        """Delete selected file/directory."""
        active_panel_widget = self.get_active_panel()
        selected_path = active_panel_widget.get_selected_path()

        if selected_path:
            def check_confirm(confirmed: bool) -> None:
                if confirmed:
                    try:
                        self.file_ops.delete(selected_path)
                        self.notify(f"Deleted {selected_path.name}")
                        active_panel_widget.refresh_view()
                    except Exception as e:
                        self.notify(f"Error deleting: {str(e)}", severity="error")

            self.app.push_screen(
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
        self.app.push_screen(HelpScreen())

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
