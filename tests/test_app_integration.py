import pytest
from pathlib import Path
from textual.pilot import Pilot
from src.file_manager.app import FileManagerApp
from src.file_manager.screens import InputScreen
from src.file_manager.user_mode import UserModeScreen
from src.file_manager.file_panel import FilePanel
from textual.widgets import Input

@pytest.mark.asyncio
async def test_action_new_dir_creates_directory(tmp_path):
    # Setup
    app = FileManagerApp()

    async with app.run_test() as pilot:
        # Navigate to User Mode
        await pilot.click("#user_mode")
        await pilot.pause()

        # Ensure we are on UserModeScreen
        assert isinstance(app.screen, UserModeScreen)

        # Update left panel to tmp_path
        left_panel = app.screen.query_one("#left-panel", FilePanel)
        left_panel.current_dir = tmp_path
        left_panel.refresh_view()

        # Trigger action_new_dir (n)
        await pilot.press("n")

        # Expect InputScreen
        assert isinstance(app.screen, InputScreen)

        # Enter directory name
        input_widget = app.screen.query_one(Input)
        input_widget.value = "new_test_dir"

        # Click OK (Enter key on input is handled)
        await pilot.press("enter")
        await pilot.pause()

        # Verify directory creation
        new_dir = tmp_path / "new_test_dir"
        assert new_dir.exists()
        assert new_dir.is_dir()

@pytest.mark.asyncio
async def test_action_new_dir_cancel(tmp_path):
    # Setup
    app = FileManagerApp()

    async with app.run_test() as pilot:
        # Navigate to User Mode
        await pilot.click("#user_mode")
        await pilot.pause()

        # Trigger action_new_dir
        await pilot.press("n")

        # Expect InputScreen
        assert isinstance(app.screen, InputScreen)

        # Click Cancel
        await pilot.click("#cancel")
        await pilot.pause()

        # Verify directory NOT created
        new_dir = tmp_path / "new_test_dir_cancel"
        assert not new_dir.exists()

        # Check we are back to UserModeScreen
        assert isinstance(app.screen, UserModeScreen)
