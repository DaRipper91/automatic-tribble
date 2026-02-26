"""
User Mode Screen - Standard File Manager Interface with Tabs, Preview, and Multi-Selection.
"""

from typing import Optional, List
from pathlib import Path
import shutil
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Label, TabbedContent, TabPane, Tree, ProgressBar
from textual.binding import Binding
from textual.reactive import reactive
from textual.screen import Screen
from textual import on, work

from .file_operations import FileOperations
from .file_panel import FilePanel, MultiSelectDirectoryTree
from .screens import ConfirmationScreen, HelpScreen, InputScreen, ThemeSwitcher
from .ui_components import DualFilePanes, EnhancedStatusBar
from .file_preview import FilePreview
from .help_overlay import HelpOverlay

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

    #preview-pane {
        width: 0;
        border: none;
        height: 100%;
        background: $surface-lighten-1;
        display: none;
    }

    #preview-pane.visible {
        width: 40%;
        border-left: solid $primary;
        padding: 0 1;
        display: block;
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
        Binding("p", "toggle_preview", "Preview"),
        Binding("ctrl+shift+t", "switch_theme", "Theme"),
        Binding("ctrl+tab", "next_tab", "Next Tab"),
    ]

    show_preview = reactive(False)

    def __init__(self, initial_path: Optional[Path] = None):
        super().__init__()
        self.file_ops = FileOperations()
        self.initial_path = initial_path if initial_path else Path.home()
        self.tab_count = 1

    def compose(self) -> ComposeResult:
        """Create the layout."""
        yield Header()

        with Container(id="main-container"):
            with Horizontal(id="workspace"):
                with TabbedContent(id="tabs", initial="tab-0"):
                    with TabPane("Home", id="tab-0"):
                        yield DualFilePanes(self.initial_path, self.initial_path, id="dual-panes-0")

                yield FilePreview(id="preview-pane")

            yield EnhancedStatusBar()

        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        # Focus the initial panel
        self._focus_active_panel()
        self._update_status_bar()

    def action_back_to_menu(self) -> None:
        """Return to the main menu."""
        self.app.pop_screen()

    def action_new_tab(self) -> None:
        """Open a new tab."""
        new_id = f"tab-{self.tab_count}"
        self.tab_count += 1

        # Determine path from current active panel or default
        current_dual = self._get_active_dual_panes()
        if current_dual:
            path = current_dual.active_panel.current_dir
        else:
            path = self.initial_path

        tabs = self.query_one(TabbedContent)
        pane = TabPane(path.name or "Tab", id=new_id)
        tabs.add_pane(pane)
        # Mount the DualFilePanes into the new pane
        pane.mount(DualFilePanes(path, path, id=f"dual-panes-{new_id}"))

        tabs.active = new_id

    def action_close_tab(self) -> None:
        """Close the current tab."""
        tabs = self.query_one(TabbedContent)
        if not tabs.active: return

        try:
            tabs.remove_pane(tabs.active)
        except Exception:
            # Likely last tab or error
            self.action_back_to_menu()

    def action_next_tab(self) -> None:
        tabs = self.query_one(TabbedContent)
        panes = list(tabs.query(TabPane))
        if not panes: return

        try:
            current_id = tabs.active
            current_index = [p.id for p in panes].index(current_id)
            next_index = (current_index + 1) % len(panes)
            tabs.active = panes[next_index].id
        except ValueError:
            pass

    def action_toggle_preview(self) -> None:
        self.show_preview = not self.show_preview

    def watch_show_preview(self, show: bool) -> None:
        preview = self.query_one("#preview-pane", FilePreview)
        if show:
            preview.add_class("visible")
            self._update_preview()
        else:
            preview.remove_class("visible")
            preview.path = None

    def action_switch_panel(self) -> None:
        # Delegate to active DualFilePanes
        dual = self._get_active_dual_panes()
        if dual:
            dual.action_switch_panel()
            self._update_status_bar()
            self._update_preview()

    def action_switch_theme(self) -> None:
        current_theme = self.app.config_manager.get_theme()

        def on_theme_selected(theme: Optional[str]) -> None:
            if theme:
                self.app.config_manager.set_theme(theme)
                self.app.load_theme_by_name(theme)
            else:
                self.app.load_theme_by_name(current_theme)

        self.app.push_screen(ThemeSwitcher(current_theme), on_theme_selected)

    def _get_active_dual_panes(self) -> Optional[DualFilePanes]:
        tabs = self.query_one(TabbedContent)
        if not tabs.active: return None
        try:
             pane = tabs.get_pane(tabs.active)
             return pane.query_one(DualFilePanes)
        except:
             return None

    def _focus_active_panel(self) -> None:
        dual = self._get_active_dual_panes()
        if dual:
            dual.active_panel.focus()

    def _update_progress(self, progress: float) -> None:
        dual = self._get_active_dual_panes()
        if not dual: return

        try:
            bar = dual.query_one("#operation-progress", ProgressBar)
            if progress >= 100 or progress < 0:
                 bar.remove_class("visible")
                 bar.update(total=100, progress=0)
            else:
                 bar.add_class("visible")
                 bar.update(total=100, progress=progress)
        except Exception:
            pass

    # --- File Operations ---

    def action_copy(self) -> None:
        dual = self._get_active_dual_panes()
        if not dual: return

        source_panel = dual.active_panel
        target_panel = dual.inactive_panel

        selected_paths = source_panel.get_selected_paths()
        if not selected_paths: return

        target_dir = target_panel.current_dir

        self.query_one(EnhancedStatusBar).is_loading = True
        self._batch_copy(list(selected_paths), target_dir, target_panel)

    @work
    async def _batch_copy(self, sources: List[Path], destination: Path, target_panel: FilePanel) -> None:
        success_count = 0
        total = len(sources)
        self.app.call_from_thread(self._update_progress, 0)

        try:
            for i, source in enumerate(sources):
                target_path = destination / source.name
                if target_path.exists():
                     self.app.call_from_thread(self.notify, f"Skipped existing: {source.name}", severity="warning")
                     continue

                await self.file_ops.copy(source, destination)
                success_count += 1
                progress = ((i + 1) / total) * 100
                self.app.call_from_thread(self._update_progress, progress)

            self.app.call_from_thread(self.notify, f"Copied {success_count} files")
            self.app.call_from_thread(target_panel.refresh_view)
        except Exception as e:
            self.app.call_from_thread(self.notify, f"Error copying: {e}", severity="error")
        finally:
            self.app.call_from_thread(self._set_loading, False)
            self.app.call_from_thread(self._update_progress, 100)

    def action_move(self) -> None:
        dual = self._get_active_dual_panes()
        if not dual: return

        source_panel = dual.active_panel
        target_panel = dual.inactive_panel

        selected_paths = source_panel.get_selected_paths()
        if not selected_paths: return

        target_dir = target_panel.current_dir

        self.query_one(EnhancedStatusBar).is_loading = True
        self._batch_move(list(selected_paths), target_dir, source_panel, target_panel)

    @work
    async def _batch_move(self, sources: List[Path], destination: Path, source_panel: FilePanel, target_panel: FilePanel) -> None:
        success_count = 0
        total = len(sources)
        self.app.call_from_thread(self._update_progress, 0)

        try:
            for i, source in enumerate(sources):
                target_path = destination / source.name
                if target_path.exists():
                     self.app.call_from_thread(self.notify, f"Skipped existing: {source.name}", severity="warning")
                     continue

                await self.file_ops.move(source, destination)
                success_count += 1
                progress = ((i + 1) / total) * 100
                self.app.call_from_thread(self._update_progress, progress)

            self.app.call_from_thread(self.notify, f"Moved {success_count} files")
            self.app.call_from_thread(source_panel.refresh_view)
            self.app.call_from_thread(target_panel.refresh_view)
        except Exception as e:
            self.app.call_from_thread(self.notify, f"Error moving: {e}", severity="error")
        finally:
            self.app.call_from_thread(self._set_loading, False)
            self.app.call_from_thread(self._update_progress, 100)

    def action_delete(self) -> None:
        dual = self._get_active_dual_panes()
        if not dual: return

        source_panel = dual.active_panel
        selected_paths = source_panel.get_selected_paths()
        if not selected_paths: return

        def check_confirm(confirmed: Optional[bool]) -> None:
            if confirmed:
                self.query_one(EnhancedStatusBar).is_loading = True
                self._batch_delete(list(selected_paths), source_panel)

        self.app.push_screen(
            ConfirmationScreen(f"Delete {len(selected_paths)} items?"),
            check_confirm
        )

    @work
    async def _batch_delete(self, paths: List[Path], panel: FilePanel) -> None:
        total = len(paths)
        self.app.call_from_thread(self._update_progress, 0)
        try:
            for i, path in enumerate(paths):
                await self.file_ops.delete(path)
                progress = ((i + 1) / total) * 100
                self.app.call_from_thread(self._update_progress, progress)

            self.app.call_from_thread(self.notify, f"Deleted {len(paths)} items")
            self.app.call_from_thread(panel.refresh_view)
        except Exception as e:
            self.app.call_from_thread(self.notify, f"Error deleting: {e}", severity="error")
        finally:
             self.app.call_from_thread(self._set_loading, False)
             self.app.call_from_thread(self._update_progress, 100)

    def action_new_dir(self) -> None:
        dual = self._get_active_dual_panes()
        if not dual: return

        active_panel = dual.active_panel
        current_dir = active_panel.current_dir

        def do_create_dir(dir_name: Optional[str]) -> None:
            if not dir_name: return
            self._background_create_dir(current_dir, dir_name, active_panel)

        self.app.push_screen(
            InputScreen(title="New Directory", message="Enter directory name:"),
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
        # Rename only supports single file usually
        dual = self._get_active_dual_panes()
        if not dual: return

        active_panel = dual.active_panel
        selected_path = active_panel.get_selected_path()
        if not selected_path: return

        def do_rename(new_name: Optional[str]) -> None:
            if not new_name or new_name == selected_path.name: return
            self._background_rename(selected_path, new_name, active_panel)

        self.app.push_screen(
            InputScreen(title="Rename", message=f"Rename {selected_path.name} to:", initial_value=selected_path.name),
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
        dual = self._get_active_dual_panes()
        if dual:
            dual.query_one("#left-panel", FilePanel).refresh_view()
            dual.query_one("#right-panel", FilePanel).refresh_view()
            self.notify("Refreshed")

    def action_toggle_help(self) -> None:
        self.app.push_screen(HelpOverlay())

    # --- Event Handlers ---

    @on(MultiSelectDirectoryTree.SelectionChanged)
    def on_selection_changed(self, event: MultiSelectDirectoryTree.SelectionChanged) -> None:
        self._update_status_bar()
        # Preview updates on cursor highlight, not selection set change (usually)
        # But if we select items, preview might stay on cursor.
        # So we leave preview update to NodeHighlighted.

    @on(Tree.NodeHighlighted)
    def on_node_highlighted(self, event) -> None:
        self._update_preview()

    @on(TabbedContent.TabActivated)
    def on_tab_activated(self, event) -> None:
        self._update_status_bar()
        self._update_preview()
        # Update tab label to current dir?
        # TabPane label can be updated.
        self._focus_active_panel()

    def _update_status_bar(self) -> None:
        dual = self._get_active_dual_panes()
        status_bar = self.query_one(EnhancedStatusBar)
        if not dual: return

        active_panel = dual.active_panel
        selected = active_panel.get_selected_paths()

        count = len(selected)
        size = sum(p.stat().st_size for p in selected if p.exists() and p.is_file())

        status_bar.selection_count = count
        status_bar.selection_size = size

        try:
            total, used, free = shutil.disk_usage(active_panel.current_dir)
            status_bar.free_space = self._format_size(free)
        except:
            status_bar.free_space = "N/A"

    def _update_preview(self) -> None:
        if not self.show_preview: return

        dual = self._get_active_dual_panes()
        if not dual: return

        active_panel = dual.active_panel
        path = active_panel.get_selected_path()

        preview = self.query_one("#preview-pane", FilePreview)
        preview.path = path

    def _set_loading(self, loading: bool) -> None:
        self.query_one(EnhancedStatusBar).is_loading = loading

    def _format_size(self, size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
             if size < 1024: return f"{size:.2f} {unit}"
             size /= 1024
        return f"{size:.2f} PB"
