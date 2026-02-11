
import unittest
import shutil
import os
from pathlib import Path
from src.file_manager.file_operations import FileOperations

class TestFileOperations(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("test_temp")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir()
        self.ops = FileOperations()

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_copy_source_not_found(self):
        with self.assertRaises(FileNotFoundError):
            self.ops.copy(self.test_dir / "nonexistent.txt", self.test_dir)

    def test_copy_destination_not_directory(self):
        source = self.test_dir / "source.txt"
        source.write_text("hello")
        dest = self.test_dir / "not_a_dir.txt"
        dest.write_text("I am a file")
        with self.assertRaises(NotADirectoryError):
            self.ops.copy(source, dest)

    def test_copy_file_success(self):
        source = self.test_dir / "source.txt"
        source.write_text("hello")
        dest_dir = self.test_dir / "dest_dir"
        dest_dir.mkdir()

        self.ops.copy(source, dest_dir)

        expected_path = dest_dir / "source.txt"
        self.assertTrue(expected_path.exists())
        self.assertEqual(expected_path.read_text(), "hello")

    def test_copy_directory_success(self):
        source_dir = self.test_dir / "source_dir"
        source_dir.mkdir()
        (source_dir / "file.txt").write_text("content")

        dest_dir = self.test_dir / "dest_dir"
        dest_dir.mkdir()

        self.ops.copy(source_dir, dest_dir)

        expected_dir = dest_dir / "source_dir"
        self.assertTrue(expected_dir.is_dir())
        self.assertTrue((expected_dir / "file.txt").exists())
        self.assertEqual((expected_dir / "file.txt").read_text(), "content")

    def test_move_source_not_found(self):
        with self.assertRaises(FileNotFoundError):
            self.ops.move(self.test_dir / "nonexistent.txt", self.test_dir)

    def test_move_destination_not_directory(self):
        source = self.test_dir / "source.txt"
        source.write_text("hello")
        dest = self.test_dir / "not_a_dir.txt"
        dest.write_text("I am a file")
        with self.assertRaises(NotADirectoryError):
            self.ops.move(source, dest)

    def test_move_success(self):
        source = self.test_dir / "source.txt"
        source.write_text("hello")
        dest_dir = self.test_dir / "dest_dir"
        dest_dir.mkdir()

        self.ops.move(source, dest_dir)

        expected_path = dest_dir / "source.txt"
        self.assertTrue(expected_path.exists())
        self.assertFalse(source.exists())
        self.assertEqual(expected_path.read_text(), "hello")

    def test_delete_not_found(self):
        with self.assertRaises(FileNotFoundError):
            self.ops.delete(self.test_dir / "nonexistent.txt")

    def test_delete_file_success(self):
        path = self.test_dir / "file.txt"
        path.write_text("hello")
        self.ops.delete(path)
        self.assertFalse(path.exists())

    def test_delete_directory_success(self):
        path = self.test_dir / "subdir"
        path.mkdir()
        (path / "file.txt").write_text("hello")
        self.ops.delete(path)
        self.assertFalse(path.exists())

    def test_create_directory_success(self):
        path = self.test_dir / "new_dir"
        self.ops.create_directory(path)
        self.assertTrue(path.is_dir())

    def test_create_directory_exists(self):
        path = self.test_dir / "existing_dir"
        path.mkdir()
        with self.assertRaises(FileExistsError):
            self.ops.create_directory(path)

    def test_rename_success(self):
        path = self.test_dir / "old.txt"
        path.write_text("hello")
        self.ops.rename(path, "new.txt")
        new_path = self.test_dir / "new.txt"
        self.assertTrue(new_path.exists())
        self.assertFalse(path.exists())

    def test_rename_not_found(self):
        with self.assertRaises(FileNotFoundError):
            self.ops.rename(self.test_dir / "nonexistent.txt", "new.txt")

    def test_get_size_file(self):
        path = self.test_dir / "file.txt"
        content = "hello world"
        path.write_text(content)
        self.assertEqual(self.ops.get_size(path), len(content))

    def test_get_size_directory(self):
        path = self.test_dir / "dir"
        path.mkdir()
        (path / "file1.txt").write_text("abc")
        (path / "file2.txt").write_text("defg")
        # Total size should be 3 + 4 = 7
        self.assertEqual(self.ops.get_size(path), 7)

    def test_format_size(self):
        self.assertEqual(self.ops.format_size(500), "500.0 B")
        self.assertEqual(self.ops.format_size(1024), "1.0 KB")
        self.assertEqual(self.ops.format_size(1024 * 1024), "1.0 MB")
        self.assertEqual(self.ops.format_size(1024 * 1024 * 1024), "1.0 GB")

if __name__ == "__main__":
    unittest.main()
