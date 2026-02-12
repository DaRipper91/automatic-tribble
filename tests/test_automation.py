import unittest
import shutil
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


if __name__ == '__main__':
    unittest.main()
