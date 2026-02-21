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
from textual import work

from .file_operations import FileOperations
from .file_panel import FilePanel
from .screens import ConfirmationScreen, HelpScreen, InputScreen


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
                    "Tab: Switch | C: Copy | M: Move | D: Delete | N: New Dir | R: Rename | H: Help | Esc: Back",
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
            target_path = target_dir / selected_path.name

            if target_path.exists():
                def confirm_overwrite(confirmed: bool) -> None:
                    if confirmed:
                        self._background_overwrite(selected_path, target_dir, target_path, target_panel)

                self.app.push_screen(
                    ConfirmationScreen(f"File {selected_path.name} exists. Overwrite?"),
                    confirm_overwrite
                )
            else:
                self._background_copy(selected_path, target_dir, target_panel)

    @work(thread=True)
    def _background_copy(self, source: Path, destination: Path, target_panel: FilePanel) -> None:
        try:
            self.file_ops.copy(source, destination)
            self.app.call_from_thread(self.notify, f"Copied {source.name} to {destination}")
            self.app.call_from_thread(target_panel.refresh_view)
        except Exception as e:
             self.app.call_from_thread(self.notify, f"Error copying: {str(e)}", severity="error")

    @work(thread=True)
    def _background_overwrite(self, source: Path, destination: Path, target_path: Path, target_panel: FilePanel) -> None:
        try:
            self.file_ops.delete(target_path)
            self.file_ops.copy(source, destination)
            self.app.call_from_thread(self.notify, f"Overwrote {source.name} in {destination}")
            self.app.call_from_thread(target_panel.refresh_view)
        except Exception as e:
             self.app.call_from_thread(self.notify, f"Error overwriting: {str(e)}", severity="error")

    def action_move(self) -> None:
        """Move selected file/directory."""
        active_panel_widget = self.get_active_panel()
        selected_path = active_panel_widget.get_selected_path()

        if selected_path:
            target_panel = self.get_inactive_panel()
            target_dir = target_panel.current_dir
            target_path = target_dir / selected_path.name

            if target_path.exists():
                def confirm_overwrite(confirmed: bool) -> None:
                    if confirmed:
                        self._background_move_overwrite(selected_path, target_dir, target_path, active_panel_widget, target_panel)

                self.app.push_screen(
                    ConfirmationScreen(f"File {selected_path.name} exists. Overwrite?"),
                    confirm_overwrite
                )
            else:
                self._background_move(selected_path, target_dir, active_panel_widget, target_panel)

    @work(thread=True, name="move_worker")
    def _background_move(self, source: Path, destination: Path, source_panel: FilePanel, target_panel: FilePanel) -> None:
        """
        Perform move operation in a background thread to prevent UI blocking.
        """
        try:
            self.file_ops.move(source, destination)
            self.app.call_from_thread(self.notify, f"Moved {source.name} to {destination}")
            self.app.call_from_thread(source_panel.refresh_view)
            self.app.call_from_thread(target_panel.refresh_view)
        except Exception as e:
            self.app.call_from_thread(self.notify, f"Error moving: {str(e)}", severity="error")

    @work(thread=True, name="move_overwrite_worker")
    def _background_move_overwrite(self, source: Path, destination: Path, target_path: Path, source_panel: FilePanel, target_panel: FilePanel) -> None:
        """
        Perform overwrite move operation in a background thread to prevent UI blocking.
        """
        try:
            self.file_ops.delete(target_path)
            self.file_ops.move(source, destination)
            self.app.call_from_thread(self.notify, f"Overwrote {source.name} in {destination}")
            self.app.call_from_thread(source_panel.refresh_view)
            self.app.call_from_thread(target_panel.refresh_view)
        except Exception as e:
            self.app.call_from_thread(self.notify, f"Error overwriting: {str(e)}", severity="error")

    def action_delete(self) -> None:
        """Delete selected file/directory."""
        active_panel_widget = self.get_active_panel()
        selected_path = active_panel_widget.get_selected_path()

        if selected_path:
            def check_confirm(confirmed: bool) -> None:
                if confirmed:
                    # Run deletion in a worker thread to keep UI responsive
                    self.run_worker(
                        lambda: self._perform_delete(selected_path, active_panel_widget),
                        thread=True,
                        name=f"delete-{selected_path.name}"
                    )

            self.app.push_screen(
                ConfirmationScreen(f"Are you sure you want to delete {selected_path.name}?"),
                check_confirm
            )

    def _perform_delete(self, path, panel) -> None:
        """Background task to perform deletion."""
        try:
            self.file_ops.delete(path)
            self.app.call_from_thread(self.notify, f"Deleted {path.name}")
            self.app.call_from_thread(panel.refresh_view)
        except Exception as e:
            self.app.call_from_thread(
                self.notify,
                f"Error deleting: {str(e)}",
                severity="error"
            )

    def action_new_dir(self) -> None:
        """Create a new directory."""
        active_panel_widget = self.get_active_panel()
        current_dir = active_panel_widget.current_dir

        def do_create_dir(dir_name: str) -> None:
            if not dir_name:
                return

            try:
                new_path = current_dir / dir_name
                self.file_ops.create_directory(new_path)
                self.notify(f"Created directory {dir_name}")
                active_panel_widget.refresh_view()
            except Exception as e:
                self.notify(f"Error creating directory: {str(e)}", severity="error")

        self.app.push_screen(
            InputScreen(
                title="New Directory",
                message="Enter directory name:"
            ),
            do_create_dir
        )

    def action_rename(self) -> None:
        """Rename selected file/directory."""
        active_panel_widget = self.get_active_panel()
        selected_path = active_panel_widget.get_selected_path()

        if selected_path:
            def do_rename(new_name: str) -> None:
                if not new_name or new_name == selected_path.name:
                    return

                try:
                    self.file_ops.rename(selected_path, new_name)
                    self.notify(f"Renamed to {new_name}")
                    active_panel_widget.refresh_view()
                except Exception as e:
                    self.notify(f"Error renaming: {str(e)}", severity="error")

            self.app.push_screen(
                InputScreen(
                    title="Rename",
                    message=f"Rename {selected_path.name} to:",
                    initial_value=selected_path.name
                ),
                do_rename
            )

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
