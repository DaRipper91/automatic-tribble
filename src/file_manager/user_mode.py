"""
User Mode Screen - Standard File Manager Interface
"""

from typing import Optional, List, Dict
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Label, Tabs, Tab
from textual.binding import Binding
from textual.reactive import reactive
from textual.screen import Screen, ModalScreen
from textual.widgets import Button, RadioSet, RadioButton, ProgressBar
from textual import work

from .file_operations import FileOperations
from .file_panel import FilePanel
from .ui_components import FilePreview, EnhancedStatusBar, MultiSelectDirectoryTree
from .help_overlay import HelpOverlay
from .screens import ConfirmationScreen, InputScreen


class ThemeSwitcher(ModalScreen):
    """Screen for switching themes."""

    CSS = """
    ThemeSwitcher {
        align: center middle;
    }

    #theme-dialog {
        padding: 1 2;
        width: 40;
        height: auto;
        border: thick $primary;
        background: $surface;
    }

    .title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
        width: 100%;
    }

    RadioSet {
        margin: 1 0;
    }

    #buttons {
        margin-top: 1;
        align: center bottom;
    }

    Button {
        margin: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="theme-dialog"):
            yield Label("Select Theme", classes="title")
            with RadioSet(id="theme-select"):
                yield RadioButton("Dark", id="dark")
                yield RadioButton("Light", id="light")
                yield RadioButton("Solarized", id="solarized")
                yield RadioButton("Dracula", id="dracula")

            with Horizontal(id="buttons"):
                yield Button("Cancel", id="cancel", variant="error")
                yield Button("Apply", id="apply", variant="primary")

    def on_mount(self) -> None:
        """Set initial selection based on current theme."""
        current_theme = self.app.config_manager.get_theme()
        try:
            self.query_one(f"#{current_theme}", RadioButton).value = True
        except Exception:
            self.query_one("#dark", RadioButton).value = True

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Preview theme on selection."""
        theme_name = event.pressed.id
        if theme_name:
            self.app.load_theme_by_name(theme_name)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "apply":
            radio_set = self.query_one(RadioSet)
            if radio_set.pressed_button:
                selected_id = radio_set.pressed_button.id
                if selected_id:
                    self.app.config_manager.set_theme(selected_id)
            self.dismiss()
        elif event.button.id == "cancel":
            # Revert to saved config if cancelled
            original_theme = self.app.config_manager.get_theme()
            self.app.load_theme_by_name(original_theme)
            self.dismiss()


class UserModeScreen(Screen):
    """The main file manager interface."""

    CSS = """
    Screen {
        background: $surface;
    }

    #main-container {
        height: 100%;
    }

    #tabs-container {
        height: 3;
        dock: top;
        background: $boost;
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

    #preview-pane {
        width: 0;
        height: 100%;
        border-left: solid $primary;
        display: none;
        transition: width 0.3s;
    }

    #preview-pane.open {
        width: 40%;
        display: block;
    }

    #status-bar-container {
        height: auto;
        dock: bottom;
    }

    #progress-area {
        height: auto;
        dock: bottom;
        background: $panel;
        padding: 0 1;
        display: none;
    }

    #progress-area.visible {
        display: block;
    }

    ProgressBar {
        margin: 1 0;
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
        Binding("p", "toggle_preview", "Toggle Preview"),
        Binding("ctrl+shift+t", "change_theme", "Change Theme"),
        Binding("ctrl+t", "new_tab", "New Tab"),
        Binding("ctrl+w", "close_tab", "Close Tab"),
        Binding("ctrl+tab", "next_tab", "Next Tab"),
    ]

    active_panel_idx = reactive(0)  # 0 for left, 1 for right
    show_preview = reactive(False)

    class TabState:
        def __init__(self, left_path: Path, right_path: Path, active_panel_idx: int = 0):
            self.left_path = left_path
            self.right_path = right_path
            self.active_panel_idx = active_panel_idx

    def __init__(self):
        super().__init__()
        self.file_ops = FileOperations()

        # Tabs management
        self.tabs: List[UserModeScreen.TabState] = []
        self.current_tab_idx = 0

        # Initialize first tab
        initial_path = Path.home()
        self.tabs.append(self.TabState(initial_path, initial_path))

    def compose(self) -> ComposeResult:
        """Create the layout."""
        yield Header()

        with Container(id="main-container"):
            with Horizontal(id="tabs-container"):
                yield Tabs(
                    Tab("Home", id="tab-0"),
                )

            with Horizontal(id="panels-container"):
                yield FilePanel(
                    str(self.tabs[0].left_path),
                    id="left-panel",
                    classes="file-panel active"
                )
                yield FilePanel(
                    str(self.tabs[0].right_path),
                    id="right-panel",
                    classes="file-panel"
                )
                yield FilePreview(id="preview-pane")

            with Vertical(id="progress-area"):
                yield Label("Operation in progress...", id="progress-label")
                yield ProgressBar(total=100, show_eta=True, id="operation-progress")

            with Vertical(id="status-bar-container"):
                yield EnhancedStatusBar()

        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        self.query_one("#left-panel", FilePanel).focus()
        self._update_status_bar()

    def action_back_to_menu(self) -> None:
        """Return to the main menu."""
        self.app.pop_screen()

    def action_change_theme(self) -> None:
        """Open theme switcher."""
        self.app.push_screen(ThemeSwitcher())

    # --- Tab Management ---

    def action_new_tab(self) -> None:
        """Create a new tab starting at home."""
        path = Path.home()
        new_tab = self.TabState(path, path)
        self.tabs.append(new_tab)

        tabs_widget = self.query_one(Tabs)
        new_tab_id = f"tab-{len(self.tabs) - 1}"
        tabs_widget.add_tab(Tab("Home", id=new_tab_id))

        # Switch to new tab
        self.current_tab_idx = len(self.tabs) - 1
        tabs_widget.active = new_tab_id
        self._load_tab_state()

    def action_close_tab(self) -> None:
        """Close current tab."""
        if len(self.tabs) <= 1:
            return  # Don't close last tab

        # Remove current tab
        self.tabs.pop(self.current_tab_idx)

        # Update index
        if self.current_tab_idx >= len(self.tabs):
            self.current_tab_idx = len(self.tabs) - 1

        # Rebuild tabs UI
        tabs_widget = self.query_one(Tabs)
        tabs_widget.clear()
        for i, tab in enumerate(self.tabs):
            name = tab.left_path.name if tab.active_panel_idx == 0 else tab.right_path.name
            if not name: name = "/"
            tabs_widget.add_tab(Tab(name, id=f"tab-{i}"))

        tabs_widget.active = f"tab-{self.current_tab_idx}"
        self._load_tab_state()

    def action_next_tab(self) -> None:
        """Cycle to next tab."""
        if len(self.tabs) <= 1:
            return

        self.current_tab_idx = (self.current_tab_idx + 1) % len(self.tabs)
        tabs_widget = self.query_one(Tabs)
        tabs_widget.active = f"tab-{self.current_tab_idx}"
        # on_tabs_tab_activated will call _load_tab_state

    def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        """Handle tab switching via UI."""
        if event.tab and event.tab.id:
            try:
                idx = int(event.tab.id.split("-")[1])
                self.current_tab_idx = idx
                self._load_tab_state()
            except (ValueError, IndexError):
                pass

    def _load_tab_state(self) -> None:
        """Load state of current tab into panels."""
        state = self.tabs[self.current_tab_idx]

        left = self.query_one("#left-panel", FilePanel)
        right = self.query_one("#right-panel", FilePanel)

        left.navigate_to(state.left_path)
        right.navigate_to(state.right_path)

        self.active_panel_idx = state.active_panel_idx
        if self.active_panel_idx == 0:
            left.add_class("active")
            right.remove_class("active")
            left.focus()
        else:
            right.add_class("active")
            left.remove_class("active")
            right.focus()

        self._update_tab_title()
        self._update_status_bar()

    def _update_tab_title(self) -> None:
        """Update current tab title to active dir name."""
        tabs_widget = self.query_one(Tabs)
        if not tabs_widget.active_tab:
            return

        state = self.tabs[self.current_tab_idx]
        path = state.left_path if state.active_panel_idx == 0 else state.right_path
        name = path.name if path.name else "/"
        tabs_widget.active_tab.label = name

    def on_directory_tree_directory_selected(self, event: MultiSelectDirectoryTree.DirectorySelected) -> None:
        """Update tab state when directory changes."""
        path = Path(event.path)
        state = self.tabs[self.current_tab_idx]

        left = self.query_one("#left-panel", FilePanel)
        right = self.query_one("#right-panel", FilePanel)

        if left.current_dir == path:
             state.left_path = path
        elif right.current_dir == path:
             state.right_path = path

        if (self.active_panel_idx == 0 and left.current_dir == path) or \
           (self.active_panel_idx == 1 and right.current_dir == path):
             self._update_tab_title()
             self.app.config_manager.add_recent_directory(str(path))

    def on_multi_select_directory_tree_selection_changed(self, event: MultiSelectDirectoryTree.SelectionChanged) -> None:
        """Update status bar when selection changes."""
        self._update_status_bar()

    # --- Panels & Preview ---

    def action_switch_panel(self) -> None:
        """Switch between left and right panels."""
        self.active_panel_idx = 1 - self.active_panel_idx
        self.tabs[self.current_tab_idx].active_panel_idx = self.active_panel_idx

        left_panel = self.query_one("#left-panel", FilePanel)
        right_panel = self.query_one("#right-panel", FilePanel)

        if self.active_panel_idx == 0:
            left_panel.add_class("active")
            right_panel.remove_class("active")
            left_panel.focus()
        else:
            right_panel.add_class("active")
            left_panel.remove_class("active")
            right_panel.focus()

        self._update_tab_title()
        self._update_status_bar()

        if self.show_preview:
            self._update_preview()

    def action_toggle_preview(self) -> None:
        """Toggle the preview pane."""
        self.show_preview = not self.show_preview
        pane = self.query_one("#preview-pane", FilePreview)

        if self.show_preview:
            pane.add_class("open")
            self._update_preview()
        else:
            pane.remove_class("open")

    def on_directory_tree_node_highlighted(self, event: MultiSelectDirectoryTree.NodeHighlighted) -> None:
        """Update preview when a node is highlighted."""
        if self.show_preview and event.node.data:
            path = Path(event.node.data.path)
            self.query_one("#preview-pane", FilePreview).show_preview(path)

    def _update_preview(self) -> None:
        """Update preview based on current active panel selection."""
        panel = self.get_active_panel()
        path = panel.get_selected_path()
        if path:
            self.query_one("#preview-pane", FilePreview).show_preview(path)

    def _update_status_bar(self) -> None:
        """Update the enhanced status bar."""
        panel = self.get_active_panel()
        status_bar = self.query_one(EnhancedStatusBar)

        status_bar.update_disk_usage(panel.current_dir)

        selected = panel.get_marked_paths()
        count = len(selected)
        size = 0
        if count > 0:
            for p in selected:
                try:
                    if p.is_file():
                        size += p.stat().st_size
                except: pass
        else:
            cursor_path = panel.get_selected_path()
            if cursor_path and cursor_path.is_file():
                count = 1
                try:
                    size = cursor_path.stat().st_size
                except: pass

        status_bar.selection_count = count
        status_bar.selection_size = size

    # --- File Operations (Refactored for Multi-Select) ---

    def _show_progress(self, message: str, total: int):
        area = self.query_one("#progress-area")
        label = self.query_one("#progress-label", Label)
        bar = self.query_one("#operation-progress", ProgressBar)

        label.update(message)
        bar.update(total=total, progress=0)
        area.add_class("visible")

    def _update_progress(self, advance: int = 1):
        bar = self.query_one("#operation-progress", ProgressBar)
        bar.advance(advance)

    def _hide_progress(self):
        area = self.query_one("#progress-area")
        area.remove_class("visible")

    def _get_files_to_operate(self) -> List[Path]:
        """Get list of files to operate on (multi-selection or single cursor)."""
        panel = self.get_active_panel()
        selected = list(panel.get_marked_paths())
        if not selected:
            cursor = panel.get_selected_path()
            if cursor:
                selected = [cursor]
        return selected

    def action_copy(self) -> None:
        """Copy selected file/directory."""
        sources = self._get_files_to_operate()
        if not sources:
            return

        target_panel = self.get_inactive_panel()
        target_dir = target_panel.current_dir

        # Check for conflicts first to determine action
        conflicts = []
        for src in sources:
            if (target_dir / src.name).exists():
                conflicts.append(src.name)

        if conflicts:
            msg = f"Copy {len(sources)} items to {target_dir.name}?\n\n{len(conflicts)} files exist and will be overwritten."
            confirm_label = "Overwrite All"
            variant = "warning"
        else:
            msg = f"Copy {len(sources)} items to {target_dir.name}?"
            confirm_label = "Copy"
            variant = "success"

        self.app.push_screen(
            ConfirmationScreen(msg, confirm_label=confirm_label, confirm_variant=variant),
            lambda c: self._batch_copy(sources, target_dir, overwrite=True) if c else None
        )

    @work
    async def _batch_copy(self, sources: List[Path], destination: Path, overwrite: bool = False) -> None:
        target_panel = self.get_inactive_panel()
        success_count = 0
        total = len(sources)

        self.app.call_from_thread(self._show_progress, f"Copying {total} items...", total)

        for src in sources:
            target_path = destination / src.name
            try:
                if target_path.exists():
                    if not overwrite:
                         self.app.call_from_thread(self.notify, f"Skipped {src.name} (exists)", severity="warning")
                         self.app.call_from_thread(self._update_progress)
                         continue
                    else:
                         # Overwrite logic: remove then copy
                         # If it's a dir, this is dangerous. FileOperations.copy handles file overwrite usually if forced,
                         # but shutils.copy2 might fail if dest exists?
                         # FileOperations.copy uses shutil.copy2 or copytree.
                         # Let's delete if exists to be safe/explicit, or rely on internal implementation.
                         # To be safe, we delete target first if it's a file.
                         if target_path.is_file():
                             await self.file_ops.delete(target_path)
                         elif target_path.is_dir():
                             # Merging dirs? Or replacing? Replacing is safer for 'overwrite' semantics usually.
                             # But let's just try copy.
                             pass

                await self.file_ops.copy(src, destination)
                success_count += 1
                self.app.call_from_thread(self._update_progress)
            except Exception as e:
                self.app.call_from_thread(self.notify, f"Error copying {src.name}: {e}", severity="error")
                self.app.call_from_thread(self._update_progress)

        self.app.call_from_thread(self._hide_progress)
        self.app.call_from_thread(self.notify, f"Copied {success_count} items.")
        self.app.call_from_thread(target_panel.refresh_view)

    def action_move(self) -> None:
        sources = self._get_files_to_operate()
        if not sources:
            return

        target_panel = self.get_inactive_panel()
        target_dir = target_panel.current_dir

        conflicts = []
        for src in sources:
            if (target_dir / src.name).exists():
                conflicts.append(src.name)

        if conflicts:
            msg = f"Move {len(sources)} items to {target_dir.name}?\n\n{len(conflicts)} files exist and will be overwritten."
            confirm_label = "Overwrite All"
            variant = "warning"
        else:
            msg = f"Move {len(sources)} items to {target_dir.name}?"
            confirm_label = "Move"
            variant = "success"

        self.app.push_screen(
            ConfirmationScreen(msg, confirm_label=confirm_label, confirm_variant=variant),
            lambda c: self._batch_move(sources, target_dir, overwrite=True) if c else None
        )

    @work
    async def _batch_move(self, sources: List[Path], destination: Path, overwrite: bool = False) -> None:
        source_panel = self.get_active_panel()
        target_panel = self.get_inactive_panel()
        success_count = 0
        total = len(sources)

        self.app.call_from_thread(self._show_progress, f"Moving {total} items...", total)

        for src in sources:
            target_path = destination / src.name
            try:
                if target_path.exists():
                    if not overwrite:
                         self.app.call_from_thread(self.notify, f"Skipped {src.name} (exists)", severity="warning")
                         self.app.call_from_thread(self._update_progress)
                         continue
                    else:
                        if target_path.is_file():
                             await self.file_ops.delete(target_path)

                await self.file_ops.move(src, destination)
                success_count += 1
                self.app.call_from_thread(self._update_progress)
            except Exception as e:
                self.app.call_from_thread(self.notify, f"Error moving {src.name}: {e}", severity="error")
                self.app.call_from_thread(self._update_progress)

        self.app.call_from_thread(self._hide_progress)
        self.app.call_from_thread(self.notify, f"Moved {success_count} items.")
        self.app.call_from_thread(source_panel.refresh_view)
        self.app.call_from_thread(target_panel.refresh_view)

    def action_delete(self) -> None:
        sources = self._get_files_to_operate()
        if not sources:
            return

        self.app.push_screen(
            ConfirmationScreen(f"Delete {len(sources)} items?"),
            lambda c: self._batch_delete(sources) if c else None
        )

    @work
    async def _batch_delete(self, sources: List[Path]) -> None:
        panel = self.get_active_panel()
        success_count = 0
        total = len(sources)

        self.app.call_from_thread(self._show_progress, f"Deleting {total} items...", total)

        for src in sources:
            try:
                await self.file_ops.delete(src)
                success_count += 1
                self.app.call_from_thread(self._update_progress)
            except Exception as e:
                self.app.call_from_thread(self.notify, f"Error deleting {src.name}: {e}", severity="error")
                self.app.call_from_thread(self._update_progress)

        self.app.call_from_thread(self._hide_progress)
        self.app.call_from_thread(self.notify, f"Deleted {success_count} items.")
        self.app.call_from_thread(panel.refresh_view)

    def action_new_dir(self) -> None:
        """Create a new directory."""
        active_panel_widget = self.get_active_panel()
        current_dir = active_panel_widget.current_dir

        def do_create_dir(dir_name: Optional[str]) -> None:
            if not dir_name:
                return

            self._background_create_dir(current_dir, dir_name, active_panel_widget)

        self.app.push_screen(
            InputScreen(
                title="New Directory",
                message="Enter directory name:"
            ),
            do_create_dir
        )

    @work
    async def _background_create_dir(self, current_dir: Path, dir_name: str, panel: FilePanel) -> None:
        try:
            new_path = current_dir / dir_name
            await self.file_ops.create_directory(new_path)
            self.app.call_from_thread(self.notify, f"Created directory {dir_name}")
            self.app.call_from_thread(panel.refresh_view)
        except Exception as e:
            self.app.call_from_thread(self.notify, f"Error creating directory: {str(e)}", severity="error")

    def action_rename(self) -> None:
        """Rename selected file/directory (single only)."""
        active_panel_widget = self.get_active_panel()
        selected_path = active_panel_widget.get_selected_path()

        if selected_path:
            def do_rename(new_name: Optional[str]) -> None:
                if not new_name or new_name == selected_path.name:
                    return

                self._background_rename(selected_path, new_name, active_panel_widget)

            self.app.push_screen(
                InputScreen(
                    title="Rename",
                    message=f"Rename {selected_path.name} to:",
                    initial_value=selected_path.name
                ),
                do_rename
            )

    @work
    async def _background_rename(self, selected_path: Path, new_name: str, panel: FilePanel) -> None:
        try:
            await self.file_ops.rename(selected_path, new_name)
            self.app.call_from_thread(self.notify, f"Renamed to {new_name}")
            self.app.call_from_thread(panel.refresh_view)
        except Exception as e:
            self.app.call_from_thread(self.notify, f"Error renaming: {str(e)}", severity="error")

    def action_refresh(self) -> None:
        """Refresh both panels."""
        left_panel = self.query_one("#left-panel", FilePanel)
        right_panel = self.query_one("#right-panel", FilePanel)
        left_panel.refresh_view()
        right_panel.refresh_view()
        self.notify("Refreshed")

    def action_toggle_help(self) -> None:
        """Toggle help display."""
        self.app.push_screen(HelpOverlay())

    def get_active_panel(self) -> FilePanel:
        """Get the currently active file panel."""
        if self.active_panel_idx == 0:
            return self.query_one("#left-panel", FilePanel)
        else:
            return self.query_one("#right-panel", FilePanel)

    def get_inactive_panel(self) -> FilePanel:
        """Get the currently inactive file panel."""
        if self.active_panel_idx == 1:
            return self.query_one("#left-panel", FilePanel)
        else:
            return self.query_one("#right-panel", FilePanel)
