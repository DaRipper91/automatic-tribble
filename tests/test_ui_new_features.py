import pytest
from textual.pilot import Pilot
from src.file_manager.app import FileManagerApp
from src.file_manager.user_mode import UserModeScreen
from src.file_manager.start_menu import StartMenuScreen
from src.file_manager.ui_components import FilePreview, EnhancedStatusBar
from pathlib import Path

def test_instantiate_usermode():
    try:
        screen = UserModeScreen()
    except Exception as e:
        pytest.fail(f"UserModeScreen instantiation failed: {e}")

@pytest.mark.asyncio
async def test_preview_pane_toggle():
    app = FileManagerApp()
    async with app.run_test() as pilot:
        # Navigate to UserMode
        await pilot.click("#user_mode")

        # Wait for screen switch
        await pilot.pause(0.5)

        # Check Preview is hidden
        user_mode = app.screen
        if isinstance(user_mode, StartMenuScreen):
             # Force push for debugging
             app.push_screen(UserModeScreen())
             await pilot.pause(0.5)
             user_mode = app.screen

        if not isinstance(user_mode, UserModeScreen):
             pytest.fail(f"Expected UserModeScreen, got {type(user_mode)}")

        preview = user_mode.query_one(FilePreview)
        assert "visible" not in preview.classes

        # Press 'p'
        await pilot.press("p")
        await pilot.pause(0.2)
        assert "visible" in preview.classes

        # Press 'p' again
        await pilot.press("p")
        await pilot.pause(0.2)
        assert "visible" not in preview.classes

@pytest.mark.asyncio
async def test_tabs():
    app = FileManagerApp()
    async with app.run_test() as pilot:
        await pilot.click("#user_mode")
        await pilot.pause(0.5)

        user_mode = app.screen
        if isinstance(user_mode, StartMenuScreen):
             app.push_screen(UserModeScreen())
             await pilot.pause(0.5)
             user_mode = app.screen

        if not isinstance(user_mode, UserModeScreen):
             pytest.fail(f"Expected UserModeScreen, got {type(user_mode)}")

        tabs = user_mode.query_one("TabbedContent")
        assert tabs.tab_count == 1

        # New Tab
        await pilot.press("ctrl+t")
        await pilot.pause(0.2)
        assert tabs.tab_count == 2

        # Close Tab
        await pilot.press("ctrl+w")
        await pilot.pause(0.2)
        assert tabs.tab_count == 1
