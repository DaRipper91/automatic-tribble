import pytest
from src.file_manager.file_operations import FileOperations
from src.file_manager.exceptions import TFMPermissionError, TFMOperationConflictError
from unittest.mock import patch, MagicMock

@pytest.fixture
def file_ops(tmp_path):
    f = FileOperations()
    f.trash_dir = tmp_path / "trash"
    f._ensure_trash_dir()
    return f

@pytest.mark.asyncio
async def test_copy_dir_tree(file_ops, tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    f1 = src / "f1.txt"
    f1.write_text("hello")
    dst = tmp_path / "dst"

    res = await file_ops.copy(src, dst)
    assert res is True
    assert (dst / "f1.txt").exists()

@pytest.mark.asyncio
async def test_copy_conflict_caught(file_ops, tmp_path):
    src = tmp_path / "src.txt"
    src.touch()
    dst = tmp_path / "dst.txt"
    dst.touch()

    with pytest.raises(TFMOperationConflictError):
        await file_ops.copy(src, dst)

@pytest.mark.asyncio
async def test_copy_oserror(file_ops, tmp_path):
    src = tmp_path / "src.txt"
    src.touch()
    dst = tmp_path / "dst.txt"

    with patch("shutil.copy2", side_effect=OSError("mock")):
        res = await file_ops.copy(src, dst)
        assert res is False

@pytest.mark.asyncio
async def test_move_oserror(file_ops, tmp_path):
    src = tmp_path / "src.txt"
    src.touch()
    dst = tmp_path / "dst.txt"

    with patch("shutil.move", side_effect=OSError("mock")):
        res = await file_ops.move(src, dst)
        assert res is False

@pytest.mark.asyncio
async def test_delete_permission_error(file_ops, tmp_path):
    src = tmp_path / "src.txt"
    src.touch()

    with patch("shutil.move", side_effect=PermissionError("mock")):
        with pytest.raises(TFMPermissionError):
            await file_ops.delete(src)

@pytest.mark.asyncio
async def test_delete_oserror(file_ops, tmp_path):
    src = tmp_path / "src.txt"
    src.touch()

    with patch("shutil.move", side_effect=OSError("mock")):
        res = await file_ops.delete(src)
        assert res is False

@pytest.mark.asyncio
async def test_rename_oserror(file_ops, tmp_path):
    src = tmp_path / "src.txt"
    src.touch()

    with patch("pathlib.Path.rename", side_effect=OSError("mock")):
        res = await file_ops.rename(src, "new.txt")
        assert res is False

@pytest.mark.asyncio
async def test_create_directory_oserror(file_ops, tmp_path):
    src = tmp_path / "newdir"

    with patch("pathlib.Path.mkdir", side_effect=OSError("mock")):
        res = await file_ops.create_directory(src)
        assert res is False

@pytest.mark.asyncio
async def test_get_size_file(file_ops, tmp_path):
    f = tmp_path / "f1.txt"
    f.write_text("hello")
    size = file_ops.get_size(f)
    assert size == 5

@pytest.mark.asyncio
async def test_get_size_dir(file_ops, tmp_path):
    d = tmp_path / "dir"
    d.mkdir()
    f1 = d / "f1.txt"
    f1.write_text("hello")
    f2 = d / "f2.txt"
    f2.write_text("world!")
    size = file_ops.get_size(d)
    assert size == 11

@pytest.mark.asyncio
async def test_get_size_not_found(file_ops, tmp_path):
    f = tmp_path / "missing.txt"
    assert file_ops.get_size(f) == 0

@pytest.mark.asyncio
async def test_get_size_oserror_file(file_ops, tmp_path):
    f = tmp_path / "f1.txt"
    f.write_text("hello")
    # Path.exists calls stat too.
    with patch("pathlib.Path.stat", side_effect=OSError("mock")):
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.is_file", return_value=True):
                size = file_ops.get_size(f)
                assert size == 0

@pytest.mark.asyncio
async def test_get_size_oserror_dir(file_ops, tmp_path):
    d = tmp_path / "d1"
    d.mkdir()
    f = d / "f1.txt"
    f.write_text("hello")
    with patch("os.DirEntry.stat", side_effect=OSError("mock")):
        size = file_ops.get_size(d)
        assert size == 0

@pytest.mark.asyncio
async def test_format_size_tb(file_ops):
    res = file_ops.format_size(1024 * 1024 * 1024 * 1024 * 2)
    assert res == "2.0 TB"

@pytest.mark.asyncio
async def test_undo_redo_empty(file_ops):
    assert await file_ops.undo_last() == "Nothing to undo."
    assert await file_ops.redo_last() == "Nothing to redo."

@pytest.mark.asyncio
async def test_undo_unknown_op(file_ops, tmp_path):
    from src.file_manager.file_operations import FileOperation
    fake_op = FileOperation(MagicMock(), tmp_path / "src", tmp_path / "dst")
    file_ops.history.log_operation(fake_op)
    res = await file_ops.undo_last()
    assert "Unknown operation type" in res

@pytest.mark.asyncio
async def test_redo_unknown_op(file_ops, tmp_path):
    from src.file_manager.file_operations import FileOperation
    fake_op = FileOperation(MagicMock(), tmp_path / "src", tmp_path / "dst")
    file_ops.history._redo_stack.append(fake_op)
    res = await file_ops.redo_last()
    assert "Unknown operation type" in res
