import pytest
import asyncio
import os
from unittest.mock import MagicMock, AsyncMock
from src.file_manager.automation import FileOrganizer, ConflictResolutionStrategy
from src.file_manager.file_operations import FileOperations

@pytest.mark.asyncio
async def test_find_duplicates_progress(tmp_path):
    # Setup
    organizer = FileOrganizer()

    # Create some files
    (tmp_path / "f1.txt").write_text("content_a")
    (tmp_path / "f2.txt").write_text("content_a") # duplicate
    (tmp_path / "f3.txt").write_text("content_b")

    queue = asyncio.Queue()

    # Find duplicates
    # This runs in thread, uses loop.call_soon_threadsafe
    duplicates = await organizer.find_duplicates(
        tmp_path,
        recursive=False,
        progress_queue=queue
    )

    # Check queue
    items = []
    while not queue.empty():
        items.append(queue.get_nowait())

    # Check if items contain "Scanning: f1.txt" etc.
    assert len(items) > 0
    # Note: "Scanning: ..." items are strings.
    assert any("Scanning" in str(item) for item in items)
    # Hashing happens only for duplicates
    # f1 and f2 are duplicates by size (9 bytes) and content
    # So hashing should occur
    assert any("Hashing (partial)" in str(item) for item in items)
    assert any("Hashing (full)" in str(item) for item in items)

    assert len(duplicates) == 1

@pytest.mark.asyncio
async def test_resolve_duplicates_progress(tmp_path):
    # Setup
    organizer = FileOrganizer()
    # We mock file_ops to avoid actual deletion logic complexities but we use real files for stat
    organizer.file_ops = MagicMock(spec=FileOperations)
    organizer.file_ops.delete = AsyncMock()

    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.touch()
    file2.touch()

    duplicates = {"hash": [file1, file2]}
    queue = asyncio.Queue()

    # Resolve (NEWEST = keep newest, delete others)
    # Make file1 newer
    newest = file1
    oldest = file2
    # Set mtime
    os.utime(newest, (1000, 2000))
    os.utime(oldest, (1000, 1000))

    deleted = await organizer.resolve_duplicates(
        duplicates,
        ConflictResolutionStrategy.KEEP_NEWEST,
        progress_queue=queue
    )

    assert len(deleted) == 1
    assert deleted[0] == oldest # Deleted file2

    # Check queue
    items = []
    while not queue.empty():
        items.append(queue.get_nowait())

    assert len(items) == 1
    assert items[0] == oldest
