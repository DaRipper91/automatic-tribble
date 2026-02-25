import pytest
from pathlib import Path
from typing import List
from unittest.mock import MagicMock, AsyncMock
from src.file_manager.automation import FileOrganizer, ConflictResolutionStrategy
from src.file_manager.file_operations import FileOperations

@pytest.mark.asyncio
async def test_resolve_duplicates_interactive(tmp_path):
    # Setup
    organizer = FileOrganizer()
    organizer.file_ops = MagicMock(spec=FileOperations)
    organizer.file_ops.delete = AsyncMock()

    # Create dummy duplicate files
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file3 = tmp_path / "file3.txt"

    file1.touch()
    file2.touch()
    file3.touch()

    duplicates = {
        "hash123": [file1, file2, file3]
    }

    # Callback that chooses to keep file2 (so delete file1 and file3)
    def mock_callback(files: List[Path]) -> List[Path]:
        # files is [file1, file2, file3] (or sorted)
        # We want to keep file2, so return everything else
        return [f for f in files if f != file2]

    # Execute
    deleted = await organizer.resolve_duplicates(
        duplicates,
        ConflictResolutionStrategy.INTERACTIVE,
        interactive_callback=mock_callback
    )

    # Verify
    assert len(deleted) == 2
    assert file1 in deleted
    assert file3 in deleted
    assert file2 not in deleted

    # Check delete calls
    assert organizer.file_ops.delete.call_count == 2

    # Check that called with file1 and file3
    # Note: order depends on list iteration order
    calls = [c.args[0] for c in organizer.file_ops.delete.await_args_list]
    assert file1 in calls
    assert file3 in calls

@pytest.mark.asyncio
async def test_resolve_duplicates_interactive_no_callback(tmp_path):
    organizer = FileOrganizer()
    organizer.file_ops = MagicMock()
    organizer.file_ops.delete = AsyncMock()

    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    duplicates = {"hash": [file1, file2]}

    # Execute without callback (should do nothing)
    deleted = await organizer.resolve_duplicates(
        duplicates,
        ConflictResolutionStrategy.INTERACTIVE,
        interactive_callback=None
    )

    assert len(deleted) == 0
    organizer.file_ops.delete.assert_not_called()
