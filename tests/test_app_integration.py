import pytest
from pathlib import Path
from textual.pilot import Pilot
from src.file_manager.app import FileManagerApp
from src.file_manager.screens import InputScreen
from textual.widgets import Input

@pytest.mark.asyncio
async def test_action_new_dir_creates_directory(tmp_path):
    # Setup
    app = FileManagerApp()
    app.left_path = tmp_path
    app.right_path = tmp_path

    async with app.run_test() as pilot:
        # Trigger action_new_dir
        await pilot.press("n")

        # Expect InputScreen
        assert isinstance(app.screen, InputScreen)

        # Enter directory name
        input_widget = app.screen.query_one(Input)
        input_widget.value = "new_test_dir"

        # Click OK
        await pilot.click("#ok")

        # Verify directory creation
        new_dir = tmp_path / "new_test_dir"
        assert new_dir.exists()
        assert new_dir.is_dir()

        # Verify notification (optional, but good to check)
        # Notifications are harder to check in pilot directly without inspecting private attributes or UI
        # But we can check if the file system state changed.

@pytest.mark.asyncio
async def test_action_new_dir_cancel(tmp_path):
    # Setup
    app = FileManagerApp()
    app.left_path = tmp_path

    async with app.run_test() as pilot:
        # Trigger action_new_dir
        await pilot.press("n")

        # Expect InputScreen
        assert isinstance(app.screen, InputScreen)

        # Click Cancel
        await pilot.click("#cancel")

        # Verify directory creation
        new_dir = tmp_path / "new_test_dir_cancel"
        assert not new_dir.exists()

        # Check we are back to main screen
        assert not isinstance(app.screen, InputScreen)
