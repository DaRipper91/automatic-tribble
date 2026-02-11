import unittest
import shutil
import tempfile
from pathlib import Path
from src.file_manager.file_operations import FileOperations

class TestFileOperations(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.file_ops = FileOperations()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_rename_file(self):
        """Test renaming a file successfully."""
        original = self.test_dir / "old_name.txt"
        original.touch()

        self.file_ops.rename(original, "new_name.txt")

        self.assertFalse(original.exists())
        self.assertTrue((self.test_dir / "new_name.txt").exists())

    def test_rename_directory(self):
        """Test renaming a directory successfully."""
        original_dir = self.test_dir / "old_dir"
        original_dir.mkdir()
        (original_dir / "file.txt").touch()

        self.file_ops.rename(original_dir, "new_dir")

        self.assertFalse(original_dir.exists())
        new_dir = self.test_dir / "new_dir"
        self.assertTrue(new_dir.exists())
        self.assertTrue(new_dir.is_dir())
        self.assertTrue((new_dir / "file.txt").exists())

    def test_rename_overwrite_file(self):
        """Test that renaming overwrites an existing file (current behavior)."""
        source = self.test_dir / "source.txt"
        dest_name = "dest.txt"
        dest = self.test_dir / dest_name

        with open(source, "w") as f:
            f.write("source content")

        with open(dest, "w") as f:
            f.write("dest content")

        self.file_ops.rename(source, dest_name)

        self.assertFalse(source.exists())
        self.assertTrue(dest.exists())
        with open(dest, "r") as f:
            content = f.read()
        self.assertEqual(content, "source content")

    def test_rename_nonexistent(self):
        """Test renaming a non-existent file raises FileNotFoundError."""
        non_existent = self.test_dir / "ghost.txt"
        with self.assertRaises(FileNotFoundError):
            self.file_ops.rename(non_existent, "new_name.txt")
