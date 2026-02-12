import pytest
from pathlib import Path
from src.file_manager.file_operations import FileOperations

class TestFileOperations:
    @pytest.fixture
    def file_ops(self):
        return FileOperations()

    @pytest.fixture
    def temp_structure(self, tmp_path):
        """
        Creates a temporary directory structure:
        tmp_path/
            source/
                file1.txt
                subdir/
                    file2.txt
            dest/
        """
        source = tmp_path / "source"
        source.mkdir()

        file1 = source / "file1.txt"
        file1.write_text("content1")

        subdir = source / "subdir"
        subdir.mkdir()
        file2 = subdir / "file2.txt"
        file2.write_text("content2")

        dest = tmp_path / "dest"
        dest.mkdir()

        return {
            "root": tmp_path,
            "source": source,
            "dest": dest,
            "file1": file1,
            "subdir": subdir,
            "file2": file2
        }

    def test_copy_file_success(self, file_ops, temp_structure):
        source_file = temp_structure["file1"]
        dest_dir = temp_structure["dest"]

        file_ops.copy(source_file, dest_dir)

        copied_file = dest_dir / source_file.name
        assert copied_file.exists()
        assert copied_file.read_text() == "content1"
        # Source should still exist
        assert source_file.exists()

    def test_copy_directory_success(self, file_ops, temp_structure):
        source_dir = temp_structure["subdir"]
        dest_dir = temp_structure["dest"]

        file_ops.copy(source_dir, dest_dir)

        copied_dir = dest_dir / source_dir.name
        assert copied_dir.exists()
        assert copied_dir.is_dir()
        assert (copied_dir / "file2.txt").read_text() == "content2"
        # Source should still exist
        assert source_dir.exists()

    def test_copy_file_exists_error(self, file_ops, temp_structure):
        source_file = temp_structure["file1"]
        dest_dir = temp_structure["dest"]

        # Create a file at the destination with the same name
        existing_file = dest_dir / source_file.name
        existing_file.write_text("existing content")

        with pytest.raises(FileExistsError):
            file_ops.copy(source_file, dest_dir)

        # Verify content was not overwritten
        assert existing_file.read_text() == "existing content"

    def test_copy_directory_exists_error(self, file_ops, temp_structure):
        source_dir = temp_structure["subdir"]
        dest_dir = temp_structure["dest"]

        # Create a directory at the destination with the same name
        existing_dir = dest_dir / source_dir.name
        existing_dir.mkdir()
        (existing_dir / "existing.txt").write_text("existing")

        with pytest.raises(FileExistsError):
            file_ops.copy(source_dir, dest_dir)

    def test_copy_source_not_found(self, file_ops, temp_structure):
        missing_source = temp_structure["source"] / "missing.txt"
        dest_dir = temp_structure["dest"]

        with pytest.raises(FileNotFoundError):
            file_ops.copy(missing_source, dest_dir)

    def test_copy_destination_not_directory(self, file_ops, temp_structure):
        source_file = temp_structure["file1"]
        # Use a file as destination, which should fail
        invalid_dest = temp_structure["file1"]

        with pytest.raises(NotADirectoryError):
            file_ops.copy(source_file, invalid_dest)

    def test_move_file_success(self, file_ops, temp_structure):
        source_file = temp_structure["file1"]
        dest_dir = temp_structure["dest"]

        file_ops.move(source_file, dest_dir)

        moved_file = dest_dir / source_file.name
        assert moved_file.exists()
        assert moved_file.read_text() == "content1"
        # Source should not exist
        assert not source_file.exists()

    def test_move_directory_success(self, file_ops, temp_structure):
        source_dir = temp_structure["subdir"]
        dest_dir = temp_structure["dest"]

        file_ops.move(source_dir, dest_dir)

        moved_dir = dest_dir / source_dir.name
        assert moved_dir.exists()
        assert moved_dir.is_dir()
        assert (moved_dir / "file2.txt").read_text() == "content2"
        # Source should not exist
        assert not source_dir.exists()

    def test_move_file_exists_error(self, file_ops, temp_structure):
        source_file = temp_structure["file1"]
        dest_dir = temp_structure["dest"]

        # Create a file at the destination with the same name
        existing_file = dest_dir / source_file.name
        existing_file.write_text("existing content")

        with pytest.raises(FileExistsError):
            file_ops.move(source_file, dest_dir)

        # Verify source still exists (failed move)
        assert source_file.exists()
        # Verify destination content preserved
        assert existing_file.read_text() == "existing content"

    def test_move_directory_exists_error(self, file_ops, temp_structure):
        source_dir = temp_structure["subdir"]
        dest_dir = temp_structure["dest"]

        # Create a directory at the destination with the same name
        existing_dir = dest_dir / source_dir.name
        existing_dir.mkdir()

        with pytest.raises(FileExistsError):
            file_ops.move(source_dir, dest_dir)

        # Verify source still exists
        assert source_dir.exists()

    def test_move_source_not_found(self, file_ops, temp_structure):
        missing_source = temp_structure["source"] / "missing.txt"
        dest_dir = temp_structure["dest"]

        with pytest.raises(FileNotFoundError):
            file_ops.move(missing_source, dest_dir)

    def test_move_destination_not_directory(self, file_ops, temp_structure):
        source_file = temp_structure["file1"]
        # Use a file as destination, which should fail
        invalid_dest = temp_structure["file1"]

        with pytest.raises(NotADirectoryError):
            file_ops.move(source_file, invalid_dest)

    def test_rename_file_success(self, file_ops, temp_structure):
        source_file = temp_structure["file1"]
        new_name = "renamed_file.txt"

        file_ops.rename(source_file, new_name)

        new_path = source_file.parent / new_name
        assert new_path.exists()
        assert new_path.read_text() == "content1"
        assert not source_file.exists()

    def test_rename_directory_success(self, file_ops, temp_structure):
        source_dir = temp_structure["subdir"]
        new_name = "renamed_dir"

        file_ops.rename(source_dir, new_name)

        new_path = source_dir.parent / new_name
        assert new_path.exists()
        assert new_path.is_dir()
        assert (new_path / "file2.txt").exists()
        assert not source_dir.exists()

    def test_rename_source_not_found(self, file_ops, temp_structure):
        missing_source = temp_structure["source"] / "missing.txt"

        with pytest.raises(FileNotFoundError):
            file_ops.rename(missing_source, "new_name.txt")

    def test_rename_target_exists_error(self, file_ops, temp_structure):
        source_file = temp_structure["file1"]
        # Create a file that already has the target name
        target_name = "already_exists.txt"
        target_path = source_file.parent / target_name
        target_path.write_text("other content")

        with pytest.raises(FileExistsError):
            file_ops.rename(source_file, target_name)

        assert source_file.exists()
        assert target_path.read_text() == "other content"

    def test_rename_invalid_name_error(self, file_ops, temp_structure):
        source_file = temp_structure["file1"]

        with pytest.raises(ValueError, match="Invalid new name"):
            file_ops.rename(source_file, "path/separator.txt")

        with pytest.raises(ValueError, match="Invalid new name"):
            file_ops.rename(source_file, "..")
