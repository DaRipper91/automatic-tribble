import pytest
import tempfile
from pathlib import Path
from src.file_manager.file_operations import FileOperations, OperationType
from src.file_manager.exceptions import TFMPathNotFoundError, TFMOperationConflictError

@pytest.mark.asyncio
class TestFileOperationsAsync:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        self.file_ops = FileOperations()
        # Mock trash dir to be inside temp dir
        self.file_ops.trash_dir = self.test_dir / ".trash"
        self.file_ops._ensure_trash_dir()
        yield
        self.temp_dir.cleanup()

    async def test_copy_file(self):
        source = self.test_dir / "source.txt"
        source.write_text("content")
        dest = self.test_dir / "dest.txt"

        await self.file_ops.copy(source, dest)

        assert dest.exists()
        assert dest.read_text() == "content"
        assert source.exists()

        # Verify history
        last_op = self.file_ops.history.undo_last()
        assert last_op.type == OperationType.COPY
        assert last_op.original_path == source
        assert last_op.target_path == dest

    async def test_move_file(self):
        source = self.test_dir / "source.txt"
        source.write_text("content")
        dest = self.test_dir / "dest.txt"

        await self.file_ops.move(source, dest)

        assert dest.exists()
        assert not source.exists()

    async def test_copy_source_not_found(self):
        source = self.test_dir / "nonexistent.txt"
        dest = self.test_dir / "dest.txt"

        with pytest.raises(TFMPathNotFoundError):
            await self.file_ops.copy(source, dest)

    async def test_copy_dest_exists(self):
        source = self.test_dir / "source.txt"
        source.write_text("content")
        dest = self.test_dir / "dest.txt"
        dest.write_text("exists")

        with pytest.raises(TFMOperationConflictError):
            await self.file_ops.copy(source, dest)

    async def test_move_source_not_found(self):
        source = self.test_dir / "nonexistent.txt"
        dest = self.test_dir / "dest.txt"

        with pytest.raises(TFMPathNotFoundError):
            await self.file_ops.move(source, dest)

    async def test_delete_not_found(self):
        source = self.test_dir / "nonexistent.txt"

        with pytest.raises(TFMPathNotFoundError):
            await self.file_ops.delete(source)

    async def test_rename_not_found(self):
        source = self.test_dir / "nonexistent.txt"

        with pytest.raises(TFMPathNotFoundError):
            await self.file_ops.rename(source, "newname.txt")

    async def test_rename_conflict(self):
        source = self.test_dir / "source.txt"
        source.write_text("content")
        existing = self.test_dir / "existing.txt"
        existing.touch()

        with pytest.raises(TFMOperationConflictError):
            await self.file_ops.rename(source, "existing.txt")

    async def test_create_dir_exists(self):
        existing = self.test_dir / "existing_dir"
        existing.mkdir()

        with pytest.raises(TFMOperationConflictError):
            await self.file_ops.create_directory(existing)

        # Should not raise if exist_ok=True
        await self.file_ops.create_directory(existing, exist_ok=True)

    async def test_undo_delete_missing_trash(self):
        source = self.test_dir / "file.txt"
        source.touch()

        await self.file_ops.delete(source)

        # Manually delete from trash
        op = self.file_ops.history._undo_stack[-1]
        if op.trash_path and op.trash_path.exists():
             op.trash_path.unlink()

        result = await self.file_ops.undo_last()
        assert "Cannot undo delete" in result
        assert not source.exists()

        # Verify history
        last_op = self.file_ops.history.undo_last()
        assert last_op.type == OperationType.MOVE

    async def test_delete_file(self):
        source = self.test_dir / "todelete.txt"
        source.write_text("content")

        await self.file_ops.delete(source)

        assert not source.exists()
        # Check trash
        trash_files = list(self.file_ops.trash_dir.glob("todelete.txt*"))
        assert len(trash_files) == 1

        # Verify history
        last_op = self.file_ops.history.undo_last()
        assert last_op.type == OperationType.DELETE

    async def test_create_directory(self):
        new_dir = self.test_dir / "newdir"

        await self.file_ops.create_directory(new_dir)

        assert new_dir.exists()
        assert new_dir.is_dir()

        # Verify history
        last_op = self.file_ops.history.undo_last()
        assert last_op.type == OperationType.CREATE_DIR

    async def test_rename_file(self):
        source = self.test_dir / "oldname.txt"
        source.write_text("content")
        new_name = "newname.txt"
        expected_path = self.test_dir / new_name

        await self.file_ops.rename(source, new_name)

        assert expected_path.exists()
        assert not source.exists()

        # Verify history
        last_op = self.file_ops.history.undo_last()
        assert last_op.type == OperationType.RENAME

    async def test_undo_copy(self):
        source = self.test_dir / "source.txt"
        source.write_text("content")
        dest = self.test_dir / "dest.txt"

        await self.file_ops.copy(source, dest)
        await self.file_ops.undo_last()

        assert not dest.exists()
        assert source.exists()

    async def test_undo_move(self):
        source = self.test_dir / "source.txt"
        source.write_text("content")
        dest = self.test_dir / "dest.txt"

        await self.file_ops.move(source, dest)
        await self.file_ops.undo_last()

        assert source.exists()
        assert not dest.exists()

    async def test_undo_delete(self):
        source = self.test_dir / "todelete.txt"
        source.write_text("content")

        await self.file_ops.delete(source)
        await self.file_ops.undo_last()

        assert source.exists()

    async def test_undo_rename(self):
        source = self.test_dir / "oldname.txt"
        source.write_text("content")
        new_name = "newname.txt"

        await self.file_ops.rename(source, new_name)
        await self.file_ops.undo_last()

        assert source.exists()
        assert not (self.test_dir / new_name).exists()

    async def test_undo_create_dir(self):
        new_dir = self.test_dir / "newdir"

        await self.file_ops.create_directory(new_dir)
        await self.file_ops.undo_last()

        assert not new_dir.exists()

    async def test_redo_copy(self):
        source = self.test_dir / "source.txt"
        source.write_text("content")
        dest = self.test_dir / "dest.txt"

        await self.file_ops.copy(source, dest)
        await self.file_ops.undo_last() # Undo
        await self.file_ops.redo_last() # Redo

        assert dest.exists()

    async def test_redo_move(self):
        source = self.test_dir / "source.txt"
        source.write_text("content")
        dest = self.test_dir / "dest.txt"

        await self.file_ops.move(source, dest)
        await self.file_ops.undo_last()
        await self.file_ops.redo_last()

        assert dest.exists()
        assert not source.exists()
