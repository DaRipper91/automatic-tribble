import pytest
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import TabbedContent
from src.file_manager.user_mode import UserModeScreen
from src.file_manager.file_panel import MultiSelectDirectoryTree

class HeadlessApp(App):
    def compose(self) -> ComposeResult:
        yield UserModeScreen()

@pytest.mark.asyncio
async def test_tabs_operation():
    app = HeadlessApp()
    async with app.run_test() as pilot:
        screen = app.query_one(UserModeScreen)
        tabs = screen.query_one(TabbedContent)

        # Initial state: 1 tab
        assert tabs.active == "tab-0"

        # New Tab
        await pilot.press("ctrl+t")
        assert tabs.active == "tab-1"

        # Close Tab
        await pilot.press("ctrl+w")
        assert tabs.active == "tab-0"

@pytest.mark.asyncio
async def test_preview_toggle():
    app = HeadlessApp()
    async with app.run_test() as pilot:
        screen = app.query_one(UserModeScreen)
        preview = screen.query_one("#preview-pane")

        assert not screen.show_preview
        assert "visible" not in preview.classes

        await pilot.press("p")
        assert screen.show_preview
        assert "visible" in preview.classes

        await pilot.press("p")
        assert not screen.show_preview

@pytest.mark.asyncio
async def test_multi_selection_logic():
    app = HeadlessApp()
    async with app.run_test() as pilot:
        # Create and mount a standalone tree for testing
        tree = MultiSelectDirectoryTree("/")
        await app.mount(tree)

        tree.selected_paths.add(Path("/test/file1"))
        assert Path("/test/file1") in tree.selected_paths

        # deselect_all calls reload(), which requires app context
        tree.action_deselect_all()
        await pilot.pause() # Allow reload worker to start/run

        assert len(tree.selected_paths) == 0
