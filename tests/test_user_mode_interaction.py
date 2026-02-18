import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Label, Input, Button

from src.file_manager.user_mode import UserModeScreen
from src.file_manager.screens import InputScreen

class HeadlessApp(App):
    def compose(self) -> ComposeResult:
        yield Label("Main")

@pytest.mark.asyncio
async def test_action_rename_flow():
    # Mock FileOperations to prevent actual file system operations
    with patch('src.file_manager.user_mode.FileOperations') as MockFileOps:
        mock_ops = MockFileOps.return_value

        app = HeadlessApp()
        screen = UserModeScreen()

        async with app.run_test() as pilot:
            await app.push_screen(screen)

            # Mock active panel and selected path
            mock_panel = MagicMock()
            mock_path = Path("test_file.txt")
            mock_panel.get_selected_path.return_value = mock_path

            # Mock get_active_panel to return our mock panel
            screen.get_active_panel = MagicMock(return_value=mock_panel)

            # Trigger rename action
            screen.action_rename()
            await pilot.pause()

            # Verify InputScreen is pushed
            assert isinstance(app.screen, InputScreen)
            assert app.screen.title_text == "Rename"
            assert app.screen.initial_value == "test_file.txt"

            # Clear input and type new name
            input_widget = app.screen.query_one(Input)
            input_widget.value = ""

            # Type new name char by char
            for char in "new_name.txt":
                await pilot.press(char)

            # Click OK
            await pilot.click("#ok")

            # Verify rename was called with correct arguments
            mock_ops.rename.assert_called_with(mock_path, "new_name.txt")

            # Verify panel refresh
            mock_panel.refresh_view.assert_called()

@pytest.mark.asyncio
async def test_action_new_dir_flow():
    with patch('src.file_manager.user_mode.FileOperations') as MockFileOps:
        mock_ops = MockFileOps.return_value

        app = HeadlessApp()
        screen = UserModeScreen()

        async with app.run_test() as pilot:
            await app.push_screen(screen)

            mock_panel = MagicMock()
            current_dir = Path("/home/user")
            mock_panel.current_dir = current_dir
            screen.get_active_panel = MagicMock(return_value=mock_panel)

            screen.action_new_dir()
            await pilot.pause()

            assert isinstance(app.screen, InputScreen)
            assert app.screen.title_text == "New Directory"

            for char in "new_folder":
                await pilot.press(char)

            await pilot.click("#ok")

            # Check if create_directory called with correct path
            expected_path = current_dir / "new_folder"
            mock_ops.create_directory.assert_called_with(expected_path)

            mock_panel.refresh_view.assert_called()
