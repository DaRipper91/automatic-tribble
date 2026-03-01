import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
from src.file_manager.cli import handle_duplicates
from src.file_manager.automation import ConflictResolutionStrategy

@pytest.mark.asyncio
async def test_interactive_duplicate_resolution():
    # Mock args
    args = MagicMock()
    args.dir = "/test/dir"
    args.recursive = True
    args.resolve = "interactive"
    args.json = False

    # Mock duplicates result
    # Group 1: file1, file2. Keep file1 (index 0+1=1).
    duplicates = {
        "hash1": [Path("/test/dir/file1.txt"), Path("/test/dir/file2.txt")],
        "hash2": [Path("/test/dir/file3.txt"), Path("/test/dir/file4.txt")]
    }

    # Mock FileOrganizer
    with patch("src.file_manager.cli.FileOrganizer") as MockOrganizer:
        organizer_instance = MockOrganizer.return_value
        organizer_instance.find_duplicates = AsyncMock(return_value=duplicates)
        organizer_instance.file_ops.delete = AsyncMock()

        # Mock os.stat (via Path.stat) to prevent OSError on non-existent files
        with patch("pathlib.Path.stat") as mock_stat:
            mock_stat.return_value.st_size = 1024
            mock_stat.return_value.st_mtime = 1600000000.0

            # Mock Prompt.ask to return "1" (Keep first file) for both groups
            with patch("src.file_manager.cli.Prompt.ask", return_value="1"):

                await handle_duplicates(args)

                # Assertions
                # Should delete file2 and file4 (since we kept 1st file in each group)
                assert organizer_instance.file_ops.delete.call_count == 2

                # Verify calls
                calls = organizer_instance.file_ops.delete.await_args_list
                deleted_paths = [c.args[0] for c in calls]

                assert Path("/test/dir/file2.txt") in deleted_paths
                assert Path("/test/dir/file4.txt") in deleted_paths
                assert Path("/test/dir/file1.txt") not in deleted_paths
                assert Path("/test/dir/file3.txt") not in deleted_paths

@pytest.mark.asyncio
async def test_interactive_duplicate_resolution_invalid_input():
    # Mock args
    args = MagicMock()
    args.dir = "/test/dir"
    args.recursive = True
    args.resolve = "interactive"
    args.json = False

    duplicates = {
        "hash1": [Path("/test/dir/file1.txt"), Path("/test/dir/file2.txt")]
    }

    with patch("src.file_manager.cli.FileOrganizer") as MockOrganizer:
        organizer_instance = MockOrganizer.return_value
        organizer_instance.find_duplicates = AsyncMock(return_value=duplicates)
        organizer_instance.file_ops.delete = AsyncMock()

        with patch("pathlib.Path.stat"):
            # Mock Prompt.ask to return invalid input "99" then "invalid"
            # Since the loop goes once per group, we can just test one invalid input which skips the group
            with patch("src.file_manager.cli.Prompt.ask", return_value="99"):

                await handle_duplicates(args)

                # Should not delete anything
                organizer_instance.file_ops.delete.assert_not_called()

@pytest.mark.asyncio
async def test_interactive_duplicate_resolution_json_error():
    args = MagicMock()
    args.dir = "/test/dir"
    args.recursive = True
    args.resolve = "interactive"
    args.json = True # JSON mode

    duplicates = {"hash": [Path("a"), Path("b")]}

    with patch("src.file_manager.cli.FileOrganizer") as MockOrganizer:
        organizer_instance = MockOrganizer.return_value
        organizer_instance.find_duplicates = AsyncMock(return_value=duplicates)

        # Should print JSON error and return 1
        with patch("builtins.print") as mock_print:
            ret = await handle_duplicates(args)
            assert ret == 1
            mock_print.assert_called()
            assert "Interactive mode not supported" in mock_print.call_args[0][0]
