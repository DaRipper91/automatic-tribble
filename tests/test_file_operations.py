
import unittest
import shutil
import tempfile
import os
from pathlib import Path
from src.file_manager.file_operations import FileOperations

class TestFileOperations(unittest.TestCase):
    def setUp(self):
        """Create a temporary directory for tests."""
        self.test_dir = tempfile.mkdtemp()
        self.file_ops = FileOperations()

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.test_dir)

    def create_file(self, path: Path, content: str = ""):
        """Helper to create a file with given content."""
        with open(path, "w") as f:
            f.write(content)

    def test_get_size_file(self):
        """Test getting the size of a single file."""
        file_path = Path(self.test_dir) / "test_file.txt"
        content = "Hello, world!"
        self.create_file(file_path, content)

        expected_size = len(content)
        actual_size = self.file_ops.get_size(file_path)

        self.assertEqual(actual_size, expected_size)

    def test_get_size_empty_directory(self):
        """Test getting the size of an empty directory."""
        dir_path = Path(self.test_dir) / "empty_dir"
        dir_path.mkdir()

        self.assertEqual(self.file_ops.get_size(dir_path), 0)

    def test_get_size_flat_directory(self):
        """Test getting the size of a directory with multiple files."""
        dir_path = Path(self.test_dir) / "flat_dir"
        dir_path.mkdir()

        self.create_file(dir_path / "file1.txt", "abc")
        self.create_file(dir_path / "file2.txt", "de")

        expected_size = 3 + 2
        actual_size = self.file_ops.get_size(dir_path)

        self.assertEqual(actual_size, expected_size)

    def test_get_size_nested_directory(self):
        """Test getting the size of a nested directory structure."""
        # Structure:
        # nested_dir/
        #   file1.txt ("a")
        #   subdir/
        #     file2.txt ("bc")

        dir_path = Path(self.test_dir) / "nested_dir"
        dir_path.mkdir()

        subdir_path = dir_path / "subdir"
        subdir_path.mkdir()

        self.create_file(dir_path / "file1.txt", "a")
        self.create_file(subdir_path / "file2.txt", "bc")

        expected_size = 1 + 2
        actual_size = self.file_ops.get_size(dir_path)

        self.assertEqual(actual_size, expected_size)

    def test_get_size_non_existent(self):
        """Test getting the size of a non-existent path."""
        path = Path(self.test_dir) / "does_not_exist"

        # Current implementation returns 0 for non-existent paths
        self.assertEqual(self.file_ops.get_size(path), 0)

if __name__ == "__main__":
    unittest.main()
