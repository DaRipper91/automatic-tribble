
import time
import pytest
from unittest.mock import MagicMock, patch

from textual.app import App, ComposeResult

from src.file_manager.user_mode import UserModeScreen

class BenchmarkApp(App):
    def compose(self) -> ComposeResult:
        yield UserModeScreen()

@pytest.mark.asyncio
async def test_copy_blocking_time(tmp_path):
    """
    Measure how long action_copy blocks the main thread.
    We patch FileOperations.copy to be slow.
    """
    # Setup directories
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    target_dir = tmp_path / "target"
    target_dir.mkdir()

    # Create a dummy file
    dummy_file = source_dir / "large_file.txt"
    dummy_file.write_text("content")

    app = BenchmarkApp()

    with patch('src.file_manager.file_operations.FileOperations.copy') as mock_copy:
        # Simulate a slow copy operation (blocking)
        def slow_copy(src, dst):
            time.sleep(1.0) # sleep 1 second

        mock_copy.side_effect = slow_copy

        async with app.run_test() as pilot:
            screen = app.query_one(UserModeScreen)

            # Patch panel methods to return our paths without relying on UI state
            mock_active_panel = MagicMock()
            mock_active_panel.get_selected_path.return_value = dummy_file

            mock_inactive_panel = MagicMock()
            mock_inactive_panel.current_dir = target_dir

            screen.get_active_panel = MagicMock(return_value=mock_active_panel)
            screen.get_inactive_panel = MagicMock(return_value=mock_inactive_panel)

            # Measure time to trigger action
            start = time.time()
            await pilot.press("c") # Trigger copy
            end = time.time()

            duration = end - start
            print(f"Non-blocking duration: {duration:.4f}s")

            # Check if it was non-blocking (should be < 0.3s)
            assert duration < 0.3, f"Expected non-blocking call < 0.3s, got {duration:.4f}s"

            # Wait for the worker to execute the copy
            start_wait = time.time()
            while not mock_copy.called:
                if time.time() - start_wait > 2.0:
                    pytest.fail("Timeout waiting for background copy")
                await pilot.pause(0.1)

            # Verify copy was called
            mock_copy.assert_called_once()
