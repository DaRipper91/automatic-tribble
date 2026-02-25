"""
User Mode Screen - Standard File Manager Interface
"""

from typing import Optional, List
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Label, TabbedContent, TabPane
from textual.binding import Binding
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import DirectoryTree
from textual import work, on

from .file_operations import FileOperations
from .file_panel import FilePanel
from .screens import ConfirmationScreen, HelpScreen, InputScreen, ThemeSwitcher
from .ui_components import FilePreview, EnhancedStatusBar, MultiSelectDirectoryTree
from .config import ConfigManager
from .help_overlay import HelpOverlay

class DualFilePanes(Container):
    """Container for two side-by-side file panels."""

    active_panel_index = reactive(0)

    def __init__(self, left_path: Path, right_path: Path, **kwargs):
        super().__init__(**kwargs)
        self.left_path = left_path
        self.right_path = right_path

    def compose(self) -> ComposeResult:
        with Horizontal(id="panels-container"):
            yield FilePanel(str(self.left_path), id="left-panel", classes="file-panel active")
            yield FilePanel(str(self.right_path), id="right-panel", classes="file-panel")

    def on_mount(self) -> None:
        try:
            self.get_active_panel().focus()
        except:
            pass

    def get_active_panel(self) -> FilePanel:
        if self.active_panel_index == 0:
            return self.query_one("#left-panel", FilePanel)
        return self.query_one("#right-panel", FilePanel)

    def get_inactive_panel(self) -> FilePanel:
        if self.active_panel_index == 0:
            return self.query_one("#right-panel", FilePanel)
        return self.query_one("#left-panel", FilePanel)

    def switch_active(self) -> None:
        self.active_panel_index = 1 - self.active_panel_index

        left = self.query_one("#left-panel", FilePanel)
        right = self.query_one("#right-panel", FilePanel)

        if self.active_panel_index == 0:
            left.add_class("active")
            right.remove_class("active")
            left.focus()
        else:
            right.add_class("active")
            left.remove_class("active")
            right.focus()

class UserModeScreen(Screen):
    """The main file manager interface."""

    CSS = """
    Screen {
        background: $surface;
    }

    #main-container {
        height: 100%;
    }

    #workspace {
        height: 1fr;
    }

    #tabs {
        width: 1fr;
        height: 100%;
    }

    FilePreview {
        display: none;
        width: 40; /* Initial width */
    }

    FilePreview.visible {
        display: block;
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
        height: 1;
        background: $primary;
        padding: 0 1;
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
        Binding("ctrl+t", "new_tab", "New Tab"),
        Binding("ctrl+w", "close_tab", "Close Tab"),
        Binding("ctrl+tab", "next_tab", "Next Tab"),
        Binding("p", "toggle_preview", "Preview"),
        Binding("ctrl+shift+t", "change_theme", "Theme"),
    ]

    show_preview = reactive(False)

    def __init__(self):
        super().__init__()
        self.file_ops = FileOperations()
        self.config_manager = ConfigManager()
        self.left_path = Path.home()
        self.right_path = Path.home()
        self.tab_count = 1

    def compose(self) -> ComposeResult:
        """Create the layout."""
        yield Header()

        with Container(id="main-container"):
            with Horizontal(id="workspace"):
                with TabbedContent(id="tabs", initial="tab-1"):
                    with TabPane("Home", id="tab-1"):
                        yield DualFilePanes(self.left_path, self.right_path, id="panes-1")

                yield FilePreview()

            yield EnhancedStatusBar(id="status-bar")

        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        # Focus the first panel
        try:
            panes = self.query_one("#panes-1", DualFilePanes)
            panes.get_active_panel().focus()
        except:
            pass

    def get_active_dual_panes(self) -> Optional[DualFilePanes]:
        try:
            tabs = self.query_one(TabbedContent)
            if not tabs.active:
                return None
            pane_id = tabs.active
            # TabPane ID is pane_id
            tab_pane = self.query_one(f"#{pane_id}", TabPane)
            return tab_pane.query_one(DualFilePanes)
        except:
            return None

    def get_active_panel(self) -> Optional[FilePanel]:
        dp = self.get_active_dual_panes()
        if dp:
            return dp.get_active_panel()
        return None

    def get_inactive_panel(self) -> Optional[FilePanel]:
        dp = self.get_active_dual_panes()
        if dp:
            return dp.get_inactive_panel()
        return None

    def action_back_to_menu(self) -> None:
        self.app.pop_screen()

    def action_switch_panel(self) -> None:
        dp = self.get_active_dual_panes()
        if dp:
            dp.switch_active()
            self._update_status_bar()

    def action_new_tab(self) -> None:
        self.tab_count += 1
        tabs = self.query_one(TabbedContent)
        # Add new tab
        new_id = f"tab-{self.tab_count}"
        tabs.add_pane(
            TabPane(
                f"Tab {self.tab_count}",
                DualFilePanes(Path.home(), Path.home(), id=f"panes-{self.tab_count}"),
                id=new_id
            )
        )
        tabs.active = new_id

    def action_close_tab(self) -> None:
        tabs = self.query_one(TabbedContent)
        if tabs.tab_count > 1:
            active = tabs.active
            tabs.remove_pane(active)

    def action_next_tab(self) -> None:
        try:
            tabs = self.query_one(TabbedContent)
            # Access internal Tabs widget to trigger next
            tab_bar = tabs.query_one("Tabs")
            tab_bar.action_next_tab()
        except:
            pass

    def action_toggle_preview(self) -> None:
        self.show_preview = not self.show_preview
        preview = self.query_one(FilePreview)
        if self.show_preview:
            preview.add_class("visible")
            self._update_preview()
        else:
            preview.remove_class("visible")

    def _focus_active_panel(self) -> None:
        p = self.get_active_panel()
        if p: p.focus()

    # Event Handlers
    @on(TabbedContent.TabActivated)
    def handle_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        self.call_after_refresh(self._on_tab_switched)

    def _on_tab_switched(self) -> None:
        self._update_preview()
        self._update_status_bar()
        self._focus_active_panel()

    @on(DirectoryTree.NodeHighlighted)
    def handle_node_highlighted(self, event: DirectoryTree.NodeHighlighted) -> None:
        self._update_preview()
        self._update_status_bar()

    @on(MultiSelectDirectoryTree.SelectionChanged)
    def handle_selection_changed(self, event: MultiSelectDirectoryTree.SelectionChanged) -> None:
        self._update_status_bar()

    @on(DirectoryTree.DirectorySelected)
    def handle_dir_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        path = Path(event.path)
        self.config_manager.add_recent_directory(str(path))

        # Update Tab Label
        tabs = self.query_one(TabbedContent)
        if tabs.active:
            try:
                pane = self.query_one(f"#{tabs.active}", TabPane)
                pane.title = path.name
            except:
                pass

        self._update_status_bar()

    def _update_preview(self) -> None:
        if not self.show_preview:
            return

        panel = self.get_active_panel()
        if not panel: return

        path = panel.get_selected_path()
        preview = self.query_one(FilePreview)
        if path:
            preview.show_preview(path)

    def _update_status_bar(self) -> None:
        panel = self.get_active_panel()
        if not panel: return

        status_bar = self.query_one(EnhancedStatusBar)

        paths = panel.get_selected_paths()
        count = len(paths)

        # Calculate size sync for responsiveness on small selections
        total_size = 0
        for p in paths:
             try:
                 if p.is_file():
                     total_size += p.stat().st_size
             except: pass

        status_bar.update_status(count, total_size, panel.current_dir)

    # File Operations

    def action_copy(self) -> None:
        active_panel = self.get_active_panel()
        if not active_panel: return

        paths = active_panel.get_selected_paths()
        if not paths: return

        target_panel = self.get_inactive_panel()
        target_dir = target_panel.current_dir

        self._perform_copy_multi(paths, target_dir, target_panel)

    @work
    async def _perform_copy_multi(self, sources: List[Path], target_dir: Path, target_panel: FilePanel) -> None:
        for source in sources:
            target_path = target_dir / source.name
            try:
                if target_path.exists():
                    self.app.call_from_thread(self.notify, f"Skipping {source.name}: Target exists", severity="warning")
                    continue

                await self.file_ops.copy(source, target_dir)
            except Exception as e:
                 self.app.call_from_thread(self.notify, f"Error copying {source.name}: {e}", severity="error")

        self.app.call_from_thread(target_panel.refresh_view)
        self.app.call_from_thread(self.notify, f"Finished copying {len(sources)} items")

    def action_move(self) -> None:
        active_panel = self.get_active_panel()
        if not active_panel: return

        paths = active_panel.get_selected_paths()
        if not paths: return

        target_panel = self.get_inactive_panel()
        target_dir = target_panel.current_dir

        self._perform_move_multi(paths, target_dir, active_panel, target_panel)

    @work
    async def _perform_move_multi(self, sources: List[Path], target_dir: Path, source_panel: FilePanel, target_panel: FilePanel) -> None:
        for source in sources:
            target_path = target_dir / source.name
            try:
                if target_path.exists():
                    self.app.call_from_thread(self.notify, f"Skipping {source.name}: Target exists", severity="warning")
                    continue
                await self.file_ops.move(source, target_dir)
            except Exception as e:
                self.app.call_from_thread(self.notify, f"Error moving {source.name}: {e}", severity="error")

        self.app.call_from_thread(source_panel.refresh_view)
        self.app.call_from_thread(target_panel.refresh_view)
        self.app.call_from_thread(self.notify, f"Finished moving {len(sources)} items")

    def action_delete(self) -> None:
        active_panel = self.get_active_panel()
        if not active_panel: return

        paths = active_panel.get_selected_paths()
        if not paths: return

        def confirm(result: bool) -> None:
            if result:
                self._perform_delete_multi(paths, active_panel)

        self.app.push_screen(
            ConfirmationScreen(f"Delete {len(paths)} items?"),
            confirm
        )

    @work
    async def _perform_delete_multi(self, paths: List[Path], panel: FilePanel) -> None:
        for path in paths:
            try:
                await self.file_ops.delete(path)
            except Exception as e:
                 self.app.call_from_thread(self.notify, f"Error deleting {path.name}: {e}", severity="error")

        self.app.call_from_thread(panel.refresh_view)
        self.app.call_from_thread(self.notify, f"Finished deleting {len(paths)} items")

    def action_new_dir(self) -> None:
        active_panel = self.get_active_panel()
        current_dir = active_panel.current_dir

        def do_create_dir(dir_name: Optional[str]) -> None:
            if not dir_name: return
            self._background_create_dir(current_dir, dir_name, active_panel)

        self.app.push_screen(InputScreen("New Directory", "Enter directory name:"), do_create_dir)

    @work
    async def _background_create_dir(self, current_dir: Path, dir_name: str, panel: FilePanel) -> None:
        try:
            await self.file_ops.create_directory(current_dir / dir_name)
            self.app.call_from_thread(panel.refresh_view)
            self.app.call_from_thread(self.notify, f"Created {dir_name}")
        except Exception as e:
            self.app.call_from_thread(self.notify, str(e), severity="error")

    def action_rename(self) -> None:
        active_panel = self.get_active_panel()
        path = active_panel.get_selected_path()
        if not path: return

        def do_rename(new_name: Optional[str]) -> None:
            if not new_name or new_name == path.name: return
            self._background_rename(path, new_name, active_panel)

        self.app.push_screen(InputScreen("Rename", f"Rename {path.name} to:", path.name), do_rename)

    @work
    async def _background_rename(self, path: Path, new_name: str, panel: FilePanel) -> None:
        try:
            await self.file_ops.rename(path, new_name)
            self.app.call_from_thread(panel.refresh_view)
            self.app.call_from_thread(self.notify, f"Renamed to {new_name}")
        except Exception as e:
            self.app.call_from_thread(self.notify, str(e), severity="error")

    def action_refresh(self) -> None:
        dp = self.get_active_dual_panes()
        if dp:
            dp.query_one("#left-panel", FilePanel).refresh_view()
            dp.query_one("#right-panel", FilePanel).refresh_view()
        self.notify("Refreshed")

    def action_toggle_help(self) -> None:
        self.app.push_screen(HelpOverlay())

    def action_change_theme(self) -> None:
        current_theme = self.config_manager.get_theme()

        def on_theme_selected(theme: Optional[str]) -> None:
            if theme:
                self.config_manager.set_theme(theme)
                self.app.apply_theme(theme)

        self.app.push_screen(ThemeSwitcher(current_theme), on_theme_selected)
