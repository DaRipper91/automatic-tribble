import pytest
from src.file_manager.automation import FileOrganizer
from src.file_manager.file_operations import FileOperations
from src.file_manager.exceptions import TFMPermissionError, TFMPathNotFoundError, TFMOperationConflictError

@pytest.mark.asyncio
async def test_organize_edge_cases(tmp_path):
    organizer = FileOrganizer()
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()

    # 1. Empty source
    result = await organizer.organize_by_type(source, target)
    assert result == {}

    # 2. File without extension
    (source / "no_ext_file").touch()
    result = await organizer.organize_by_type(source, target)
    assert result == {} # Should remain

    # 3. Hidden file
    (source / ".hidden").touch()
    result = await organizer.organize_by_type(source, target)
    assert result == {}

    # 4. Nested directory in source (should be ignored by simple organize, or handled?)
    # organize_by_type iterates source_dir.iterdir() which is non-recursive.
    (source / "subdir").mkdir()
    (source / "subdir" / "file.txt").touch()
    result = await organizer.organize_by_type(source, target)
    # subdir is a dir, so it is skipped
    assert result == {}

@pytest.mark.asyncio
async def test_file_ops_exceptions(tmp_path):
    ops = FileOperations()

    # 1. Path not found
    with pytest.raises(TFMPathNotFoundError):
        await ops.delete(tmp_path / "nonexistent")

    # 2. Conflict
    src = tmp_path / "src.txt"
    src.write_text("a")
    dst = tmp_path / "dst.txt"
    dst.write_text("b")

    with pytest.raises(TFMOperationConflictError):
        # copy to existing file without overwrite logic inside copy?
        # FileOperations.copy -> _validate_transfer checks if target exists
        await ops.copy(src, dst)

    # 3. Permission (mocking because difficult to reliably trigger across environments)
    # But we can try readonly dir
    import os
    import stat

    protected_dir = tmp_path / "protected"
    protected_dir.mkdir()
    protected_file = protected_dir / "file.txt"
    protected_file.touch()

    # Remove write permission
    os.chmod(protected_dir, stat.S_IREAD | stat.S_IEXEC)

    try:
        # Try to delete file inside protected dir
        with pytest.raises((TFMPermissionError, PermissionError)):
             await ops.delete(protected_file)
    finally:
        # Restore for cleanup
        os.chmod(protected_dir, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
