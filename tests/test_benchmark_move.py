
import time
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from textual.app import App, ComposeResult
from textual.pilot import Pilot

from src.file_manager.user_mode import UserModeScreen

class BenchmarkApp(App):
    def compose(self) -> ComposeResult:
        yield UserModeScreen()

@pytest.mark.asyncio
async def test_move_blocking_time(tmp_path):
    """
    Measure how long action_move blocks the main thread.
    We patch FileOperations.move to be slow.
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

    with patch('src.file_manager.file_operations.FileOperations.move') as mock_move:
        # Simulate a slow move operation (blocking)
        def slow_move(src, dst):
            time.sleep(1.0) # sleep 1 second

        mock_move.side_effect = slow_move

        async with app.run_test() as pilot:
            screen = app.query_one(UserModeScreen)

            # Patch panel methods to return our paths without relying on UI state
            mock_active_panel = MagicMock()
            mock_active_panel.get_selected_path.return_value = dummy_file
            mock_active_panel.current_dir = source_dir

            mock_inactive_panel = MagicMock()
            mock_inactive_panel.current_dir = target_dir

            screen.get_active_panel = MagicMock(return_value=mock_active_panel)
            screen.get_inactive_panel = MagicMock(return_value=mock_inactive_panel)

            # Measure time to trigger action
            start = time.time()
            await pilot.press("m") # Trigger move
            end = time.time()

            duration = end - start
            print(f"Non-blocking duration: {duration:.4f}s")

            # Check if it was non-blocking (should be < 0.3s)
            assert duration < 0.3, f"Expected non-blocking call < 0.3s, got {duration:.4f}s"

            # Wait for the worker to execute the move
            start_wait = time.time()
            while not mock_move.called:
                if time.time() - start_wait > 2.0:
                    pytest.fail("Timeout waiting for background move")
                await pilot.pause(0.1)

            # Verify move was called
            mock_move.assert_called_once()
