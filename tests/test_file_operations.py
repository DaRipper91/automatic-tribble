"""
Tests for FileOperations class.
"""
import pytest
from pathlib import Path
from src.file_manager.file_operations import FileOperations

@pytest.fixture
def file_ops():
    """Fixture to provide a FileOperations instance."""
    return FileOperations()

@pytest.fixture
def temp_workspace(tmp_path):
    """Fixture to provide a temporary workspace with files and directories."""
    # Create a structure:
    # workspace/
    #   file1.txt
    #   dir1/
    #     file2.txt

    workspace = tmp_path / "workspace"
    workspace.mkdir()

    file1 = workspace / "file1.txt"
    file1.write_text("content1")

    dir1 = workspace / "dir1"
    dir1.mkdir()

    file2 = dir1 / "file2.txt"
    file2.write_text("content2")

    return workspace

def test_delete_file(file_ops, temp_workspace):
    """Test deleting a file using Path object."""
    file_path = temp_workspace / "file1.txt"
    assert file_path.exists()

    file_ops.delete(file_path)

    assert not file_path.exists()

def test_delete_directory(file_ops, temp_workspace):
    """Test deleting a directory using Path object."""
    dir_path = temp_workspace / "dir1"
    file_in_dir = dir_path / "file2.txt"

    assert dir_path.exists()
    assert file_in_dir.exists()

    file_ops.delete(dir_path)

    assert not dir_path.exists()
    assert not file_in_dir.exists()

def test_delete_non_existent_path(file_ops, tmp_path):
    """Test deleting a path that does not exist raises FileNotFoundError."""
    non_existent_path = tmp_path / "non_existent"

    with pytest.raises(FileNotFoundError):
        file_ops.delete(non_existent_path)

def test_delete_string_path(file_ops, temp_workspace):
    """Test deleting a file using string path."""
    file_path = temp_workspace / "file1.txt"

    assert file_path.exists()
    file_ops.delete(str(file_path))
    assert not file_path.exists()
