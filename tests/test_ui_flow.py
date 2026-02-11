import pytest
import tempfile
import shutil
from pathlib import Path
from textual.pilot import Pilot
from textual.widgets import Button, Input, RichLog
from src.file_manager.app import FileManagerApp
from src.file_manager.start_menu import StartMenuScreen
from src.file_manager.user_mode import UserModeScreen
from src.file_manager.ai_mode import AIModeScreen

@pytest.fixture
def temp_test_dir():
    dir_path = Path(tempfile.mkdtemp())
    # Create some dummy files
    (dir_path / "test.txt").touch()
    (dir_path / "image.jpg").touch()
    yield dir_path
    shutil.rmtree(dir_path)

@pytest.mark.asyncio
async def test_start_menu_initial_screen():
    app = FileManagerApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert isinstance(app.screen, StartMenuScreen)
        assert app.screen.query_one("#user_mode") is not None
        assert app.screen.query_one("#ai_mode") is not None

@pytest.mark.asyncio
async def test_navigate_to_user_mode_and_back():
    app = FileManagerApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert isinstance(app.screen, StartMenuScreen)

        # Click User Mode button
        await pilot.click("#user_mode")
        await pilot.pause()

        # Now screen should be UserModeScreen
        assert isinstance(app.screen, UserModeScreen)
        assert app.screen.query_one("#left-panel") is not None

        # Press Escape to go back
        await pilot.press("escape")
        await pilot.pause()

        # Back to StartMenuScreen
        assert isinstance(app.screen, StartMenuScreen)

@pytest.mark.asyncio
async def test_navigate_to_ai_mode_and_interact(temp_test_dir):
    app = FileManagerApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert isinstance(app.screen, StartMenuScreen)

        # Click AI Mode button
        await pilot.click("#ai_mode")
        await pilot.pause()

        # Now screen should be AIModeScreen
        assert isinstance(app.screen, AIModeScreen)
        assert app.screen.query_one("#command_input") is not None

        # Set target dir to temp dir
        target_input = app.screen.query_one("#target_dir_input", Input)
        target_input.value = str(temp_test_dir)

        # Click "Organize by Type" button
        await pilot.click("#btn_org_type")
        await pilot.pause()

        # Check input value
        command_input = app.screen.query_one("#command_input", Input)
        assert command_input.value == "Organize files by type"

        # Click "Process" button (or press enter since input is focused)
        await pilot.press("enter")
        await pilot.pause()

        # Check log output
        log = app.screen.query_one("#output_log", RichLog)
        assert len(log.lines) > 2

        # Verify files were organized (optional, but good)
        assert (temp_test_dir / "Organized_Type" / "images" / "image.jpg").exists()

@pytest.mark.asyncio
async def test_ai_mode_custom_command(temp_test_dir):
    app = FileManagerApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        # Navigate to AI Mode
        await pilot.click("#ai_mode")
        await pilot.pause()

        # Set target dir
        target_input = app.screen.query_one("#target_dir_input", Input)
        target_input.value = str(temp_test_dir)

        # Type custom command
        command_input = app.screen.query_one("#command_input", Input)
        command_input.value = "Clean up downloads" # This cleans, might delete test files?
        # Mock logic uses keywords. "clean" uses cleanup_old_files.
        # But uses "directory" param from current_dir (target_dir_input).

        # Submit
        await pilot.press("enter")
        await pilot.pause()

        # Check log output
        log = app.screen.query_one("#output_log", RichLog)
        assert len(log.lines) > 2
