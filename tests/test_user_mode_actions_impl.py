import pytest
from pathlib import Path
from textual.pilot import Pilot
from src.file_manager.app import FileManagerApp
from src.file_manager.screens import InputScreen
from src.file_manager.user_mode import UserModeScreen
from textual.widgets import Input, DirectoryTree

@pytest.mark.asyncio
async def test_action_new_dir_creates_directory(tmp_path):
    # Setup app with StartMenuScreen
    app = FileManagerApp()

    async with app.run_test() as pilot:
        # Wait for mount
        await pilot.pause()

        # Click user_mode button
        await pilot.click("#user_mode")
        await pilot.pause()

        # Check we are at UserModeScreen
        assert isinstance(app.screen, UserModeScreen)
        user_mode = app.screen

        left_panel = user_mode.query_one("#left-panel")
        right_panel = user_mode.query_one("#right-panel")

        # Navigate panels to tmp_path
        left_panel.navigate_to(tmp_path)
        right_panel.navigate_to(tmp_path)

        await pilot.pause()

        # Trigger action_new_dir
        await pilot.press("n")

        # Expect InputScreen
        await pilot.pause()
        assert isinstance(app.screen, InputScreen)

        # Enter directory name
        input_widget = app.screen.query_one(Input)
        input_widget.value = "new_test_dir"

        # Click OK
        await pilot.click("#ok")

        # Wait for operation to complete
        await pilot.pause()

        # Verify directory creation
        new_dir = tmp_path / "new_test_dir"
        assert new_dir.exists()
        assert new_dir.is_dir()

@pytest.mark.asyncio
async def test_action_rename_renames_file(tmp_path):
    # Setup
    app = FileManagerApp()

    # Create a file to rename
    test_file = tmp_path / "test_file.txt"
    test_file.touch()

    async with app.run_test() as pilot:
        # Navigate to User Mode
        await pilot.pause()
        await pilot.click("#user_mode")
        await pilot.pause()

        user_mode = app.screen
        left_panel = user_mode.query_one("#left-panel")

        # Navigate to tmp_path
        left_panel.navigate_to(tmp_path)
        await pilot.pause()

        # We need to select the file.
        # DirectoryTree nodes are populated.
        tree = left_panel.query_one(DirectoryTree)
        # Find the node for test_file.txt
        # Accessing private attribute _tree_lines or similar might be needed if public API is lacking,
        # but let's try to focus it.

        # Force reload just in case
        tree.reload()
        await pilot.pause()

        # In a real TUI test, we might press down until we find it.
        # But we can try to find the node index.
        # DirectoryTree behaves like a Tree.

        # Let's inspect tree content for debugging if needed.
        # For now, let's assume it's the only file and select the first child.
        # Root is tmp_path.

        # If we can't select easily via UI events, we can manually set the selection state
        # IF the action uses get_selected_path().

        # get_selected_path uses self._tree.cursor_node.data.path

        # Let's try to set cursor_line to the node index.
        # We need to find the node.

        # This is tricky without more deep knowledge of DirectoryTree or inspection.
        # But we can try to just mock get_selected_path method on the panel instance?
        # That would test the action logic but not the integration with DirectoryTree selection.
        # It's safer for this test.

        original_get_selected_path = left_panel.get_selected_path
        left_panel.get_selected_path = lambda: test_file

        try:
            # Trigger action_rename
            await pilot.press("r")

            # Expect InputScreen
            await pilot.pause()
            assert isinstance(app.screen, InputScreen)

            # Check initial value
            input_widget = app.screen.query_one(Input)
            assert input_widget.value == "test_file.txt"

            # Enter new name
            input_widget.value = "renamed_file.txt"

            # Click OK
            await pilot.click("#ok")

            # Wait for operation
            await pilot.pause()

            # Verify rename
            assert not test_file.exists()
            assert (tmp_path / "renamed_file.txt").exists()

        finally:
            left_panel.get_selected_path = original_get_selected_path
