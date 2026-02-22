import unittest
import shutil
import os
from datetime import datetime
from pathlib import Path
from src.file_manager.automation import FileOrganizer

class TestBatchRename(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("test_batch_rename")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir()
        self.organizer = FileOrganizer()

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_batch_rename_basic(self):
        # Create a file with the pattern
        file1 = self.test_dir / "test_pattern_1.txt"
        file1.touch()

        # Rename it
        renamed_files = self.organizer.batch_rename(
            directory=self.test_dir,
            pattern="pattern",
            replacement="replacement",
            recursive=False
        )

        # Verify result
        expected_file = self.test_dir / "test_replacement_1.txt"
        self.assertTrue(expected_file.exists())
        self.assertFalse(file1.exists())
        self.assertEqual(len(renamed_files), 1)
        self.assertIn(expected_file, renamed_files)

    def test_batch_rename_recursive(self):
        # Create a subdirectory with a file
        subdir = self.test_dir / "subdir"
        subdir.mkdir()
        file2 = subdir / "test_pattern_2.txt"
        file2.touch()

        # Rename it recursively
        renamed_files = self.organizer.batch_rename(
            directory=self.test_dir,
            pattern="pattern",
            replacement="replacement",
            recursive=True
        )

        # Verify result
        expected_file = subdir / "test_replacement_2.txt"
        self.assertTrue(expected_file.exists())
        self.assertFalse(file2.exists())
        self.assertEqual(len(renamed_files), 1)
        self.assertIn(expected_file, renamed_files)

    def test_batch_rename_no_recursive(self):
        # Create a subdirectory with a file
        subdir = self.test_dir / "subdir"
        subdir.mkdir()
        file2 = subdir / "test_pattern_2.txt"
        file2.touch()

        # Rename without recursion
        renamed_files = self.organizer.batch_rename(
            directory=self.test_dir,
            pattern="pattern",
            replacement="replacement",
            recursive=False
        )

        # Verify file is untouched
        self.assertTrue(file2.exists())
        self.assertEqual(len(renamed_files), 0)

    def test_batch_rename_no_match(self):
        # Create a file without the pattern
        file3 = self.test_dir / "no_match.txt"
        file3.touch()

        # Try to rename
        renamed_files = self.organizer.batch_rename(
            directory=self.test_dir,
            pattern="missing",
            replacement="replacement",
            recursive=False
        )

        # Verify file is untouched
        self.assertTrue(file3.exists())
        self.assertEqual(len(renamed_files), 0)

    def test_batch_rename_partial_match(self):
        # Create a file with pattern as part of name
        file4 = self.test_dir / "prefix_pattern_suffix.txt"
        file4.touch()

        # Rename
        renamed_files = self.organizer.batch_rename(
            directory=self.test_dir,
            pattern="pattern",
            replacement="replaced",
            recursive=False
        )

        # Verify partial replacement
        expected_file = self.test_dir / "prefix_replaced_suffix.txt"
        self.assertTrue(expected_file.exists())
        self.assertFalse(file4.exists())
        self.assertEqual(len(renamed_files), 1)
        self.assertIn(expected_file, renamed_files)

    def test_batch_rename_multiple_occurrences(self):
        # Create a file with multiple occurrences
        file5 = self.test_dir / "pattern_pattern.txt"
        file5.touch()

        # Rename
        renamed_files = self.organizer.batch_rename(
            directory=self.test_dir,
            pattern="pattern",
            replacement="rep",
            recursive=False
        )

        # Verify all occurrences replaced
        expected_file = self.test_dir / "rep_rep.txt"
        self.assertTrue(expected_file.exists())
        self.assertFalse(file5.exists())
        self.assertEqual(len(renamed_files), 1)
        self.assertIn(expected_file, renamed_files)


class TestOrganizeByType(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("test_organize_by_type")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir()

        self.source_dir = self.test_dir / "source"
        self.target_dir = self.test_dir / "target"
        self.source_dir.mkdir()
        self.target_dir.mkdir()

        self.organizer = FileOrganizer()

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_organize_by_type_basic(self):
        # Create some test files
        (self.source_dir / "test.jpg").touch()
        (self.source_dir / "test.mp4").touch()
        (self.source_dir / "test.txt").touch()
        (self.source_dir / "test.unknown").touch()

        # Organize
        result = self.organizer.organize_by_type(
            source_dir=self.source_dir,
            target_dir=self.target_dir,
            move=False
        )

        # Verify results
        self.assertIn('images', result)
        self.assertIn('videos', result)
        self.assertIn('documents', result)
        self.assertNotIn('data', result) # No data files created

        self.assertTrue((self.target_dir / "images" / "test.jpg").exists())
        self.assertTrue((self.target_dir / "videos" / "test.mp4").exists())
        self.assertTrue((self.target_dir / "documents" / "test.txt").exists())
        self.assertFalse((self.target_dir / "test.unknown").exists())

        # Original files should still exist because move=False
        self.assertTrue((self.source_dir / "test.jpg").exists())

    def test_organize_by_type_custom_categories(self):
        # Create some test files
        (self.source_dir / "test.custom").touch()

        custom_categories = {
            'special': ['.custom']
        }

        # Organize
        result = self.organizer.organize_by_type(
            source_dir=self.source_dir,
            target_dir=self.target_dir,
            categories=custom_categories,
            move=True
        )

        # Verify results
        self.assertIn('special', result)
        self.assertTrue((self.target_dir / "special" / "test.custom").exists())

        # Original file should be gone because move=True
        self.assertFalse((self.source_dir / "test.custom").exists())


class TestFindDuplicates(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("test_find_duplicates")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir()
        self.organizer = FileOrganizer()

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_find_duplicates_basic(self):
        # Create original file
        file1 = self.test_dir / "original.txt"
        with open(file1, "w") as f:
            f.write("content")

        # Create duplicate
        file2 = self.test_dir / "duplicate.txt"
        with open(file2, "w") as f:
            f.write("content")

        # Create different file
        file3 = self.test_dir / "different.txt"
        with open(file3, "w") as f:
            f.write("different content")

        duplicates = self.organizer.find_duplicates(self.test_dir)

        self.assertEqual(len(duplicates), 1)
        # Verify the duplicate set contains both files
        for files in duplicates.values():
            self.assertEqual(len(files), 2)
            self.assertTrue(any(f.name == "original.txt" for f in files))
            self.assertTrue(any(f.name == "duplicate.txt" for f in files))

    def test_find_duplicates_recursive(self):
        # Create file in root
        file1 = self.test_dir / "root.txt"
        with open(file1, "w") as f:
            f.write("recursive content")

        # Create subdirectory with duplicate
        subdir = self.test_dir / "subdir"
        subdir.mkdir()
        file2 = subdir / "nested.txt"
        with open(file2, "w") as f:
            f.write("recursive content")

        duplicates = self.organizer.find_duplicates(self.test_dir, recursive=True)

        self.assertEqual(len(duplicates), 1)
        for files in duplicates.values():
            self.assertEqual(len(files), 2)

    def test_find_duplicates_no_recursive(self):
        # Create file in root
        file1 = self.test_dir / "root.txt"
        with open(file1, "w") as f:
            f.write("recursive content")

        # Create subdirectory with duplicate
        subdir = self.test_dir / "subdir"
        subdir.mkdir()
        file2 = subdir / "nested.txt"
        with open(file2, "w") as f:
            f.write("recursive content")

        duplicates = self.organizer.find_duplicates(self.test_dir, recursive=False)

        self.assertEqual(len(duplicates), 0)

    def test_no_duplicates(self):
        file1 = self.test_dir / "file1.txt"
        with open(file1, "w") as f:
            f.write("content 1")
        file2 = self.test_dir / "file2.txt"
        with open(file2, "w") as f:
            f.write("content 2")

        duplicates = self.organizer.find_duplicates(self.test_dir)
        self.assertEqual(len(duplicates), 0)

    def test_find_duplicates_partial_collision(self):
        # Create two files with same size, same partial hash, but different full hash
        # To do this, we need files > 3 * chunk_size (8192) = 24576
        # Let's use 30000 bytes

        chunk_size = 8192
        size = 30000

        # We need to construct content such that:
        # Start (0-8192) is same
        # Middle (size//2 - 4096 : size//2 + 4096) is same. 15000-4096=10904 to 19096
        # End (size - 8192 : size) is same. 21808 to 30000

        # Different parts: 8192-10904, 19096-21808

        import os
        common_content = os.urandom(size)
        content1 = bytearray(common_content)
        content2 = bytearray(common_content)

        # Modify in unsampled region (e.g., byte 9000)
        content2[9000] = (content2[9000] + 1) % 256

        file1 = self.test_dir / "file1.bin"
        with open(file1, "wb") as f:
            f.write(content1)

        file2 = self.test_dir / "file2.bin"
        with open(file2, "wb") as f:
            f.write(content2)

        duplicates = self.organizer.find_duplicates(self.test_dir)

        # Should be empty because they are different
        self.assertEqual(len(duplicates), 0)


class TestOrganizeByDate(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("test_organize_by_date")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir()

        self.source_dir = self.test_dir / "source"
        self.target_dir = self.test_dir / "target"
        self.source_dir.mkdir()
        self.target_dir.mkdir()

        self.organizer = FileOrganizer()

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_organize_by_date_basic(self):
        # Create a file
        file1 = self.source_dir / "test.txt"
        file1.touch()

        # Set a specific mtime (2023-01-01 12:00:00)
        timestamp = datetime(2023, 1, 1, 12, 0, 0).timestamp()
        os.utime(file1, (timestamp, timestamp))

        # Organize
        result = self.organizer.organize_by_date(
            source_dir=self.source_dir,
            target_dir=self.target_dir,
            move=False
        )

        # Verify default format %Y/%m
        # Note: on Windows paths might be different, but Path / operator handles it.
        # However, the key in result dictionary will be "2023/01" because of strftime("%Y/%m")
        expected_path = self.target_dir / "2023" / "01" / "test.txt"
        # Wait, strftime produces "2023/01". target_dir / "2023/01" might mean target_dir/"2023"/"01" on some systems if passed to Path constructor,
        # but here we use target_dir / date_str.
        # If date_str is "2023/01", Path("target") / "2023/01" -> "target/2023/01".

        self.assertTrue(expected_path.exists())
        self.assertIn("2023/01", result)
        self.assertIn(expected_path, result["2023/01"])

    def test_organize_by_date_custom_format(self):
        # Create a file
        file1 = self.source_dir / "test.txt"
        file1.touch()

        # Set a specific mtime (2023-01-01 12:00:00)
        timestamp = datetime(2023, 1, 1, 12, 0, 0).timestamp()
        os.utime(file1, (timestamp, timestamp))

        # Organize with custom format
        result = self.organizer.organize_by_date(
            source_dir=self.source_dir,
            target_dir=self.target_dir,
            date_format="%Y-%m-%d",
            move=True
        )

        # Verify format %Y-%m-%d
        expected_path = self.target_dir / "2023-01-01" / "test.txt"
        self.assertTrue(expected_path.exists())
        self.assertIn("2023-01-01", result)
        self.assertFalse(file1.exists()) # moved


if __name__ == '__main__':
    unittest.main()
