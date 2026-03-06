import pytest
from src.file_manager.automation import FileOrganizer, ConflictResolutionStrategy
from unittest.mock import patch

@pytest.fixture
def organizer(tmp_path):
    org = FileOrganizer()
    org.file_ops.trash_dir = tmp_path / "trash"
    return org

@pytest.mark.asyncio
async def test_organize_by_date_empty(organizer, tmp_path):
    source = tmp_path / "src"
    target = tmp_path / "dst"
    source.mkdir()
    target.mkdir()
    result = await organizer.organize_by_date(source, target)
    assert result == {}

@pytest.mark.asyncio
async def test_organize_by_date_fail_read(organizer, tmp_path):
    source = tmp_path / "nonexistent"
    result = await organizer.organize_by_date(source, tmp_path / "dst")
    assert result == {}

@pytest.mark.asyncio
async def test_find_duplicates_recursive(organizer, tmp_path):
    d1 = tmp_path / "d1"
    d1.mkdir()
    f1 = d1 / "f1.txt"
    f2 = d1 / "f2.txt"
    f3 = tmp_path / "f3.txt"
    f1.write_text("hello")
    f2.write_text("hello")
    f3.write_text("world")

    dups = await organizer.find_duplicates(tmp_path, recursive=True)
    assert len(dups) == 1
    # Check that f1 and f2 are in it
    hash_val = list(dups.keys())[0]
    assert len(dups[hash_val]) == 2

@pytest.mark.asyncio
async def test_resolve_duplicates_newest(organizer, tmp_path):
    import time
    f1 = tmp_path / "f1.txt"
    f2 = tmp_path / "f2.txt"
    f1.write_text("dup")
    time.sleep(0.01)
    f2.write_text("dup")

    dups = {"hash": [f1, f2]}
    deleted = await organizer.resolve_duplicates(dups, ConflictResolutionStrategy.KEEP_NEWEST)
    # f2 is newest, so f1 should be deleted
    assert len(deleted) == 1
    assert deleted[0] == f1

@pytest.mark.asyncio
async def test_resolve_duplicates_oldest(organizer, tmp_path):
    import time
    f1 = tmp_path / "f1.txt"
    f2 = tmp_path / "f2.txt"
    f1.write_text("dup")
    time.sleep(0.01)
    f2.write_text("dup")

    dups = {"hash": [f1, f2]}
    deleted = await organizer.resolve_duplicates(dups, ConflictResolutionStrategy.KEEP_OLDEST)
    # f1 is oldest, so f2 should be deleted
    assert len(deleted) == 1
    assert deleted[0] == f2

@pytest.mark.asyncio
async def test_resolve_duplicates_largest(organizer, tmp_path):
    f1 = tmp_path / "f1.txt"
    f2 = tmp_path / "f2.txt"
    f1.write_text("dup") # size 3
    f2.write_text("dupdup") # size 6

    dups = {"hash": [f1, f2]}
    deleted = await organizer.resolve_duplicates(dups, ConflictResolutionStrategy.KEEP_LARGEST)
    assert len(deleted) == 1
    assert deleted[0] == f1

@pytest.mark.asyncio
async def test_resolve_duplicates_smallest(organizer, tmp_path):
    f1 = tmp_path / "f1.txt"
    f2 = tmp_path / "f2.txt"
    f1.write_text("dup") # size 3
    f2.write_text("dupdup") # size 6

    dups = {"hash": [f1, f2]}
    deleted = await organizer.resolve_duplicates(dups, ConflictResolutionStrategy.KEEP_SMALLEST)
    assert len(deleted) == 1
    assert deleted[0] == f2

@pytest.mark.asyncio
async def test_batch_rename_empty_pattern(organizer, tmp_path):
    with pytest.raises(ValueError):
        await organizer.batch_rename(tmp_path, "", "new")

@pytest.mark.asyncio
async def test_batch_rename_fail_rename(organizer, tmp_path):
    f1 = tmp_path / "test1.txt"
    f1.write_text("t")
    f2 = tmp_path / "test2.txt"
    f2.write_text("t")
    # Make new name conflict
    with patch("src.file_manager.file_operations.FileOperations.rename", return_value=False):
        renamed = await organizer.batch_rename(tmp_path, "test", "new")
        assert len(renamed) == 0

@pytest.mark.asyncio
async def test_find_duplicates_non_recursive(organizer, tmp_path):
    d1 = tmp_path / "d1"
    d1.mkdir()
    f1 = d1 / "f1.txt"
    f2 = d1 / "f2.txt"
    f3 = tmp_path / "f3.txt"
    f4 = tmp_path / "f4.txt"
    f1.write_text("hello")
    f2.write_text("hello")
    f3.write_text("world")
    f4.write_text("world")

    dups = await organizer.find_duplicates(tmp_path, recursive=False)
    assert len(dups) == 1
    hash_val = list(dups.keys())[0]
    assert len(dups[hash_val]) == 2
    assert f3 in dups[hash_val]
    assert f4 in dups[hash_val]

@pytest.mark.asyncio
async def test_resolve_duplicates_interactive(organizer, tmp_path):
    f1 = tmp_path / "f1.txt"
    f2 = tmp_path / "f2.txt"
    f1.write_text("dup")
    f2.write_text("dup")

    dups = {"hash": [f1, f2]}
    deleted = await organizer.resolve_duplicates(dups, ConflictResolutionStrategy.INTERACTIVE)
    assert len(deleted) == 0 # Interactive skips auto-deletion

@pytest.mark.asyncio
async def test_batch_rename_dry_run(organizer, tmp_path):
    f1 = tmp_path / "test1.txt"
    f1.write_text("t")
    renamed = await organizer.batch_rename(tmp_path, "test", "new", dry_run=True)
    assert len(renamed) == 1
    assert renamed[0] == tmp_path / "new1.txt"
    assert f1.exists()
    assert not (tmp_path / "new1.txt").exists()

@pytest.mark.asyncio
async def test_organize_by_type_invalid_category(organizer, tmp_path):
    source = tmp_path / "src"
    source.mkdir()
    f1 = source / "test.unknown_ext_123"
    f1.touch()

    # Should skip unknown extensions
    result = await organizer.organize_by_type(source, tmp_path / "dst")
    assert result == {}

@pytest.mark.asyncio
async def test_cleanup_old_files_dry_run(organizer, tmp_path):
    import time
    source = tmp_path / "src"
    source.mkdir()
    f1 = source / "old.txt"
    f1.touch()

    # Set mtime back by 2 days
    old_time = time.time() - (2 * 86400)
    import os
    os.utime(f1, (old_time, old_time))

    old_files = await organizer.cleanup_old_files(source, days_old=1, dry_run=True)
    assert len(old_files) == 1
    assert f1.exists() # Should not be deleted

@pytest.mark.asyncio
async def test_organize_by_date_dry_run(organizer, tmp_path):
    source = tmp_path / "src"
    target = tmp_path / "dst"
    source.mkdir()
    f1 = source / "test.txt"
    f1.touch()

    result = await organizer.organize_by_date(source, target, dry_run=True)
    assert len(result) == 1
    # Check target dir was NOT created
    assert not target.exists()

@pytest.mark.asyncio
async def test_organize_generic_file_error(organizer, tmp_path):
    source = tmp_path / "src"
    target = tmp_path / "dst"
    source.mkdir()
    f1 = source / "test.txt"
    f1.touch()

    with patch("src.file_manager.file_operations.FileOperations.move", side_effect=Exception("mocked err")):
        result = await organizer.organize_by_date(source, target, move=True)
        # Should catch Exception and continue, but return empty because it failed to organize
        # Wait, if it fails, it won't add to `organized_files` dict
        assert result == {}

@pytest.mark.asyncio
async def test_find_duplicates_oserror(organizer, tmp_path):
    # Pass in a path that throws permission error for scandir
    with patch("os.scandir", side_effect=PermissionError("mocked perm error")):
        dups = await organizer.find_duplicates(tmp_path, recursive=False)
        assert dups == {}

@pytest.mark.asyncio
async def test_resolve_duplicates_oserror(organizer, tmp_path):
    f1 = tmp_path / "f1.txt"
    f2 = tmp_path / "f2.txt"
    dups = {"hash": [f1, f2]}
    # f1 doesn't exist, stat will raise OSError
    deleted = await organizer.resolve_duplicates(dups, ConflictResolutionStrategy.KEEP_NEWEST)
    assert len(deleted) == 0

@pytest.mark.asyncio
async def test_cleanup_old_files_oserror(organizer, tmp_path):
    f1 = tmp_path / "old.txt"
    f1.touch()

    with patch("pathlib.Path.is_file", return_value=True):
        with patch("pathlib.Path.stat", side_effect=OSError("mock")):
            old_files = await organizer.cleanup_old_files(tmp_path, days_old=1)
            assert len(old_files) == 0

@pytest.mark.asyncio
async def test_compute_file_hash_oserror(organizer, tmp_path):
    f1 = tmp_path / "hash.txt"
    # Doesn't exist, so _compute_file_hash raises FileNotFoundError -> caught inside loop?
    # the method itself raises it, but `find_duplicates` catches OSError
    # We can test the helper directly to see if it raises
    with pytest.raises(OSError):
        organizer._compute_file_hash(f1)



@pytest.mark.asyncio
async def test_find_duplicates_symlink(organizer, tmp_path):
    import os
    d1 = tmp_path / "d1"
    d1.mkdir()
    f1 = d1 / "f1.txt"
    f1.write_text("hello")
    f2 = d1 / "f2.symlink"
    os.symlink(f1, f2) # Should be followed by recursive_scan

    dups = await organizer.find_duplicates(d1, recursive=True)
    assert len(dups) == 1

@pytest.mark.asyncio
async def test_batch_rename_dry_run_dot(organizer, tmp_path):
    f1 = tmp_path / "test1.txt"
    f1.write_text("t")
    # if new name contains . or .. or /, should be skipped
    renamed = await organizer.batch_rename(tmp_path, "test1.txt", "..")
    assert len(renamed) == 0

@pytest.mark.asyncio
async def test_find_duplicates_size_oserror(organizer, tmp_path):
    d1 = tmp_path / "d1"
    d1.mkdir()
    f1 = d1 / "f1.txt"
    f1.write_text("hello")
    f2 = d1 / "f2.txt"
    f2.write_text("hello")

    with patch("os.DirEntry.stat", side_effect=OSError("mock")):
        dups = await organizer.find_duplicates(d1, recursive=False)
        assert dups == {}

@pytest.mark.asyncio
async def test_find_duplicates_partial_hash_oserror(organizer, tmp_path):
    d1 = tmp_path / "d1"
    d1.mkdir()
    f1 = d1 / "f1.txt"
    f1.write_text("hello")
    f2 = d1 / "f2.txt"
    f2.write_text("hello")

    with patch("src.file_manager.automation.FileOrganizer._compute_partial_hash", side_effect=OSError("mock")):
        dups = await organizer.find_duplicates(d1, recursive=False)
        assert dups == {}

@pytest.mark.asyncio
async def test_find_duplicates_full_hash_oserror(organizer, tmp_path):
    d1 = tmp_path / "d1"
    d1.mkdir()
    f1 = d1 / "f1.txt"
    f1.write_text("hello" * 100000)
    f2 = d1 / "f2.txt"
    f2.write_text("hello" * 100000)

    with patch("src.file_manager.automation.FileOrganizer._compute_file_hash", side_effect=OSError("mock")):
        dups = await organizer.find_duplicates(d1, recursive=False)
        assert dups == {}

@pytest.mark.asyncio
async def test_organize_get_unique_path(organizer, tmp_path):
    f1 = tmp_path / "test.txt"
    f1.touch()
    f2 = tmp_path / "test_1.txt"
    f2.touch()

    res = organizer._get_unique_path(f1)
    assert res.name == "test_2.txt"

@pytest.mark.asyncio
async def test_partial_hash_small_file(organizer, tmp_path):
    f1 = tmp_path / "test.txt"
    f1.write_text("small")
    hash1 = organizer._compute_partial_hash(f1)
    # Since it is small, it hashes whole file
    assert hash1 == organizer._compute_file_hash(f1)

@pytest.mark.asyncio
async def test_partial_hash_large_file(organizer, tmp_path):
    f1 = tmp_path / "test.txt"
    # Make it exactly larger than 2 * 65536
    f1.write_bytes(b"a" * (2 * 65536 + 10))
    hash1 = organizer._compute_partial_hash(f1, chunk_size=65536)
    assert hash1 is not None
