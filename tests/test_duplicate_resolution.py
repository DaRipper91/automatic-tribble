import pytest
import os
import time
from src.file_manager.automation import FileOrganizer, ConflictResolutionStrategy

@pytest.mark.asyncio
async def test_duplicate_detection(tmp_path):
    organizer = FileOrganizer()

    # Setup files
    file1 = tmp_path / "file1.txt"
    file1.write_text("content")

    file2 = tmp_path / "file2.txt"
    file2.write_text("content") # Duplicate of file1

    file3 = tmp_path / "file3.txt"
    file3.write_text("different content")

    duplicates = await organizer.find_duplicates(tmp_path)

    assert len(duplicates) == 1
    # Check that file1 and file2 are in the same group
    paths = list(duplicates.values())[0]
    assert len(paths) == 2
    assert file1 in paths
    assert file2 in paths
    assert file3 not in [p for sublist in duplicates.values() for p in sublist]

@pytest.mark.asyncio
async def test_resolve_duplicates_keep_newest(tmp_path):
    organizer = FileOrganizer()

    # Setup files with different timestamps
    file1 = tmp_path / "old.txt"
    file1.write_text("content")

    # Set file1 to be older
    os.utime(file1, (time.time() - 100, time.time() - 100))

    file2 = tmp_path / "new.txt"
    file2.write_text("content")

    duplicates = await organizer.find_duplicates(tmp_path)
    assert len(duplicates) == 1

    # Resolve
    deleted = await organizer.resolve_duplicates(duplicates, ConflictResolutionStrategy.KEEP_NEWEST)

    assert len(deleted) == 1
    assert deleted[0] == file1
    assert not file1.exists()
    assert file2.exists()

@pytest.mark.asyncio
async def test_resolve_duplicates_keep_oldest(tmp_path):
    organizer = FileOrganizer()

    file1 = tmp_path / "old.txt"
    file1.write_text("content")
    os.utime(file1, (time.time() - 100, time.time() - 100))

    file2 = tmp_path / "new.txt"
    file2.write_text("content")

    duplicates = await organizer.find_duplicates(tmp_path)

    deleted = await organizer.resolve_duplicates(duplicates, ConflictResolutionStrategy.KEEP_OLDEST)

    assert len(deleted) == 1
    assert deleted[0] == file2
    assert not file2.exists()
    assert file1.exists()

@pytest.mark.asyncio
async def test_3_pass_logic(tmp_path):
    # This test verifies that files with same size but different content are NOT duplicates
    organizer = FileOrganizer()

    file1 = tmp_path / "A.txt"
    file1.write_text("AAAA") # 4 bytes

    file2 = tmp_path / "B.txt"
    file2.write_text("BBBB") # 4 bytes

    duplicates = await organizer.find_duplicates(tmp_path)
    assert len(duplicates) == 0
