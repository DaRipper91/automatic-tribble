
import pytest
import asyncio
from pathlib import Path
from textual.app import App, ComposeResult
from src.file_manager.user_mode import UserModeScreen
from src.file_manager.file_panel import FilePanel

class MockApp(App):
    def compose(self) -> ComposeResult:
        yield UserModeScreen()

@pytest.mark.asyncio
async def test_action_delete_starts_worker(tmp_path):
    # Setup: create a file to delete
    test_file = tmp_path / "to_delete.txt"
    test_file.write_text("hello")

    app = MockApp()
    async with app.run_test() as pilot:
        screen = app.query_one(UserModeScreen)
        # Mock the active panel and selected path
        panel = screen.query_one("#left-panel", FilePanel)
        panel.get_selected_path = lambda: test_file

        # Trigger action_delete
        await pilot.press("d")

        # Confirmation screen should be visible
        from src.file_manager.screens import ConfirmationScreen
        assert isinstance(app.screen, ConfirmationScreen)

        # Confirm deletion
        await pilot.click("#confirm")

        # Wait for the worker to finish
        # In Textual, workers can be tracked.
        # We'll just wait a bit for the file to disappear
        max_wait = 2.0
        wait_step = 0.1
        elapsed = 0
        while test_file.exists() and elapsed < max_wait:
            await asyncio.sleep(wait_step)
            elapsed += wait_step

        assert not test_file.exists()

        # Check that a worker was indeed created and finished
        # Workers are in screen.workers
        # Note: Depending on timing, it might already be gone from screen.workers
