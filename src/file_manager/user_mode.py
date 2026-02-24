"""
User Mode Screen - Standard File Manager Interface
"""

from pathlib import Path
from typing import Set, Optional
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Label, TabbedContent, TabPane, DirectoryTree
from textual.binding import Binding
from textual.reactive import reactive
from textual.screen import Screen
from textual import work
from textual.message import Message

from .file_operations import FileOperations
from .ui_components import DualFilePanes, EnhancedStatusBar, FilePreview, FilePanel, MultiSelectDirectoryTree
from .screens import ConfirmationScreen, InputScreen
from .help_overlay import HelpOverlay
from .theme_screen import ThemeSelectionScreen
from .config import ConfigManager


class UserModeScreen(Screen):
    """The main file manager interface."""

    CSS = """
    Screen {
        background: $surface;
    }

    #main-area {
        width: 1fr;
        height: 100%;
    }

    #tabs {
        height: 1fr;
    }

    DualFilePanes {
        height: 100%;
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
        Binding("space", "toggle_selection", "Select"),
        Binding("ctrl+shift+t", "change_theme", "Theme"),
    ]

    def __init__(self, initial_path: Optional[str] = None):
        super().__init__()
        self.file_ops = FileOperations()
        self.initial_path = Path(initial_path) if initial_path else Path.home()
        self.tab_count = 1
        self.config_manager = ConfigManager()
        self.config_manager.add_recent_dir(self.initial_path)

    def compose(self) -> ComposeResult:
        """Create the layout."""
        yield Header()

        with Horizontal():
            with Vertical(id="main-area"):
                with TabbedContent(id="tabs"):
                    with TabPane(f"Tab 1", id="tab-1"):
                        yield DualFilePanes(self.initial_path, self.initial_path, id="dual-panes-1")
                yield EnhancedStatusBar()

            yield FilePreview(id="preview-pane")

        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        self.query_one("DualFilePanes").focus()
        self.update_status_bar()

    def action_back_to_menu(self) -> None:
        """Return to the main menu."""
        self.app.pop_screen()

    def get_active_dual_panes(self) -> Optional[DualFilePanes]:
        tabs = self.query_one(TabbedContent)
        if not tabs.active:
            return None
        # Find the DualFilePanes in the active tab
        try:
            return tabs.get_pane(tabs.active).query_one(DualFilePanes)
        except Exception:
            return None

    def action_switch_panel(self) -> None:
        pane = self.get_active_dual_panes()
        if pane:
            pane.switch_panel()
            self.update_status_bar()

    def action_new_tab(self) -> None:
        self.tab_count += 1
        tabs = self.query_one(TabbedContent)
        new_id = f"tab-{self.tab_count}"
        tabs.add_pane(
            TabPane(f"Tab {self.tab_count}", DualFilePanes(Path.home(), Path.home(), id=f"dual-panes-{self.tab_count}"), id=new_id)
        )
        tabs.active = new_id

    def action_close_tab(self) -> None:
        tabs = self.query_one(TabbedContent)
        if tabs.tab_count > 1:
            tabs.remove_pane(tabs.active)
        else:
            self.notify("Cannot close the last tab", severity="warning")

    def action_next_tab(self) -> None:
        tabs = self.query_one(TabbedContent)
        if not tabs.active:
            return

        panes = [c.id for c in tabs.query(TabPane)]
        if not panes:
            return

        try:
            current_idx = panes.index(tabs.active)
            next_idx = (current_idx + 1) % len(panes)
            tabs.active = panes[next_idx]
        except ValueError:
            if panes:
                tabs.active = panes[0]

    def action_toggle_preview(self) -> None:
        preview = self.query_one(FilePreview)
        preview.toggle_class("open")
        self.update_preview()

    def on_directory_tree_node_highlighted(self, event: DirectoryTree.NodeHighlighted) -> None:
        self.update_preview()

    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        self.update_status_bar()
        self.config_manager.add_recent_dir(Path(event.path))

    def on_multi_select_directory_tree_selection_changed(self, event: MultiSelectDirectoryTree.SelectionChanged) -> None:
        self.update_status_bar()

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        self.update_status_bar()

    def update_preview(self) -> None:
        preview = self.query_one(FilePreview)
        if not preview.has_class("open"):
            return

        pane = self.get_active_dual_panes()
        if not pane:
            return

        active_panel = pane.get_active_panel()
        path = active_panel.get_selected_path()
        preview.path = path

    def update_status_bar(self) -> None:
        pane = self.get_active_dual_panes()
        if not pane:
            return

        active_panel = pane.get_active_panel()
        status_bar = self.query_one(EnhancedStatusBar)

        # Selected (sync is fine for set length)
        selected_paths = active_panel.get_selected_paths()
        status_bar.selected_count = len(selected_paths)

        # Calculate size of selection (async for safety if many items)
        self._calculate_selection_size(selected_paths)

        # Background tasks for expensive operations
        self._update_disk_usage(active_panel.current_dir)
        self._count_files_async(active_panel.current_dir)

    @work(thread=True)
    async def _calculate_selection_size(self, paths: Set[Path]) -> None:
        size = 0
        for p in paths:
            if p.is_file():
                try:
                    size += p.stat().st_size
                except:
                    pass

        def update_ui():
            try:
                self.query_one(EnhancedStatusBar).selected_size = size
            except Exception:
                pass

        self.app.call_from_thread(update_ui)

    @work(thread=True)
    async def _update_disk_usage(self, path: Path) -> None:
        try:
            import shutil
            total, used, free = shutil.disk_usage(path)
            formatted = EnhancedStatusBar._format_size(free)
            self.app.call_from_thread(lambda: setattr(self.query_one(EnhancedStatusBar), 'free_space', formatted))
        except Exception:
            pass

    @work(thread=True)
    async def _count_files_async(self, path: Path) -> None:
        try:
            # Non-recursive count
            count = 0
            # Use os.scandir for better performance than iterdir
            import os
            try:
                with os.scandir(path) as it:
                    for _ in it:
                        count += 1
            except OSError:
                pass

            # Safe update
            def update_count():
                try:
                    self.query_one(EnhancedStatusBar).total_files = count
                except Exception:
                    pass

            self.app.call_from_thread(update_count)
        except Exception:
            pass

    # Actions using multi-selection

    def action_copy(self) -> None:
        pane = self.get_active_dual_panes()
        if not pane: return

        source_panel = pane.get_active_panel()
        target_panel = pane.get_inactive_panel()

        paths = source_panel.get_selected_paths()
        # Fallback to cursor
        if not paths:
            p = source_panel.get_selected_path()
            if p: paths = {p}

        if not paths:
            self.notify("No files selected", severity="warning")
            return

        target_dir = target_panel.current_dir

        self.app.push_screen(
            ConfirmationScreen(f"Copy {len(paths)} items to {target_dir}?"),
            lambda c: self._batch_copy(paths, target_dir, target_panel) if c else None
        )

    @work
    async def _batch_copy(self, sources: Set[Path], destination: Path, target_panel: FilePanel) -> None:
        status_bar = self.query_one(EnhancedStatusBar)
        status_bar.is_loading = True

        count = 0
        for source in sources:
            try:
                target_path = destination / source.name
                if target_path.exists():
                     # Simple skip for now
                     self.app.call_from_thread(self.notify, f"Skipped existing: {source.name}", severity="warning")
                     continue

                if source.is_dir():
                    # Recursive copy
                    # We use shutil.copytree via file_ops
                     await self.file_ops.copy(source, destination)
                else:
                     await self.file_ops.copy(source, destination)
                count += 1
            except Exception as e:
                self.app.call_from_thread(self.notify, f"Error: {e}", severity="error")

        status_bar.is_loading = False
        self.app.call_from_thread(self.notify, f"Copied {count} items")
        self.app.call_from_thread(target_panel.refresh_view)

    def action_move(self) -> None:
        pane = self.get_active_dual_panes()
        if not pane: return

        source_panel = pane.get_active_panel()
        target_panel = pane.get_inactive_panel()

        paths = source_panel.get_selected_paths()
        if not paths:
            p = source_panel.get_selected_path()
            if p: paths = {p}

        if not paths:
            self.notify("No files selected", severity="warning")
            return

        target_dir = target_panel.current_dir

        self.app.push_screen(
            ConfirmationScreen(f"Move {len(paths)} items to {target_dir}?"),
            lambda c: self._batch_move(paths, target_dir, source_panel, target_panel) if c else None
        )

    @work
    async def _batch_move(self, sources: Set[Path], destination: Path, source_panel: FilePanel, target_panel: FilePanel) -> None:
        status_bar = self.query_one(EnhancedStatusBar)
        status_bar.is_loading = True

        count = 0
        for source in sources:
            try:
                target_path = destination / source.name
                if target_path.exists():
                     self.app.call_from_thread(self.notify, f"Skipped existing: {source.name}", severity="warning")
                     continue

                await self.file_ops.move(source, destination)
                count += 1
            except Exception as e:
                self.app.call_from_thread(self.notify, f"Error: {e}", severity="error")

        status_bar.is_loading = False
        self.app.call_from_thread(self.notify, f"Moved {count} items")
        self.app.call_from_thread(source_panel.refresh_view)
        self.app.call_from_thread(target_panel.refresh_view)

    def action_delete(self) -> None:
        pane = self.get_active_dual_panes()
        if not pane: return

        source_panel = pane.get_active_panel()
        paths = source_panel.get_selected_paths()
        if not paths:
            p = source_panel.get_selected_path()
            if p: paths = {p}

        if not paths:
            self.notify("No files selected", severity="warning")
            return

        self.app.push_screen(
            ConfirmationScreen(f"Delete {len(paths)} items?"),
            lambda c: self._batch_delete(paths, source_panel) if c else None
        )

    @work
    async def _batch_delete(self, sources: Set[Path], panel: FilePanel) -> None:
        status_bar = self.query_one(EnhancedStatusBar)
        status_bar.is_loading = True

        count = 0
        for source in sources:
            try:
                await self.file_ops.delete(source)
                count += 1
            except Exception as e:
                self.app.call_from_thread(self.notify, f"Error: {e}", severity="error")

        status_bar.is_loading = False
        self.app.call_from_thread(self.notify, f"Deleted {count} items")
        self.app.call_from_thread(panel.refresh_view)

    def action_new_dir(self) -> None:
        pane = self.get_active_dual_panes()
        if not pane: return
        active_panel = pane.get_active_panel()
        current_dir = active_panel.current_dir

        def do_create_dir(dir_name: str) -> None:
            if not dir_name: return
            self._background_create_dir(current_dir, dir_name, active_panel)

        self.app.push_screen(InputScreen(title="New Directory", message="Enter directory name:"), do_create_dir)

    @work
    async def _background_create_dir(self, current_dir: Path, dir_name: str, panel: FilePanel) -> None:
        try:
            await self.file_ops.create_directory(current_dir / dir_name)
            self.app.call_from_thread(panel.refresh_view)
        except Exception as e:
            self.app.call_from_thread(self.notify, f"Error: {e}", severity="error")

    def action_rename(self) -> None:
        pane = self.get_active_dual_panes()
        if not pane: return
        active_panel = pane.get_active_panel()
        p = active_panel.get_selected_path()
        if not p: return

        def do_rename(new_name: str) -> None:
            if not new_name or new_name == p.name: return
            self._background_rename(p, new_name, active_panel)

        self.app.push_screen(InputScreen(title="Rename", message=f"Rename {p.name} to:", initial_value=p.name), do_rename)

    @work
    async def _background_rename(self, path: Path, new_name: str, panel: FilePanel) -> None:
        try:
            await self.file_ops.rename(path, new_name)
            self.app.call_from_thread(panel.refresh_view)
        except Exception as e:
            self.app.call_from_thread(self.notify, f"Error: {e}", severity="error")

    def action_refresh(self) -> None:
        pane = self.get_active_dual_panes()
        if pane:
            pane.query_one("#left-panel", FilePanel).refresh_view()
            pane.query_one("#right-panel", FilePanel).refresh_view()
        self.notify("Refreshed")

    def action_toggle_help(self) -> None:
        self.app.push_screen(HelpOverlay())

    def action_change_theme(self) -> None:
        self.app.push_screen(ThemeSelectionScreen())
