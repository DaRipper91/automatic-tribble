import pytest
from textual.pilot import Pilot
from textual.widgets import Label, Button
from src.file_manager.app import FileManagerApp
from src.file_manager.user_mode import UserModeScreen
from src.file_manager.screens import HelpScreen

@pytest.mark.asyncio
async def test_help_screen_toggle():
    app = FileManagerApp()
    async with app.run_test() as pilot:
        await pilot.pause()

        # Navigate to User Mode
        await pilot.click("#user_mode")
        await pilot.pause()

        # Should be in UserModeScreen
        assert isinstance(app.screen, UserModeScreen)

        # Trigger Help (press 'h')
        await pilot.press("h")
        await pilot.pause()

        # Verify HelpScreen is active
        # Currently this will fail because it shows a notification instead
        assert isinstance(app.screen, HelpScreen)

        # Verify Close button works
        await pilot.click("#close-button")
        await pilot.pause()

        # Should be back in UserModeScreen
        assert isinstance(app.screen, UserModeScreen)

@pytest.mark.asyncio
async def test_help_screen_escape():
    # This tests the new Esc binding
    app = FileManagerApp()
    async with app.run_test() as pilot:
        await pilot.pause()

        # Navigate to User Mode
        await pilot.click("#user_mode")
        await pilot.pause()

        # Trigger Help
        await pilot.press("h")
        await pilot.pause()

        assert isinstance(app.screen, HelpScreen)

        # Press Escape
        await pilot.press("escape")
        await pilot.pause()

        # Should be back in UserModeScreen
        assert isinstance(app.screen, UserModeScreen)
