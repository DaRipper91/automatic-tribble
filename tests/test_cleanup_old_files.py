import unittest
import shutil
import os
import time
import tempfile
from pathlib import Path
from src.file_manager.automation import FileOrganizer

# Define locally for test isolation
SECONDS_PER_DAY = 86400

class TestCleanupOldFiles(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        self.organizer = FileOrganizer()

        # Calculate current time
        self.now = time.time()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _create_file_with_age(self, path: Path, days_old: float):
        """Create a file with modification time set to days_old ago."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        mtime = self.now - (days_old * SECONDS_PER_DAY)
        os.utime(path, (mtime, mtime))

    def test_cleanup_basic(self):
        # Create an old file (older than 30 days)
        old_file = self.test_dir / "old_file.txt"
        self._create_file_with_age(old_file, 31)

        # Create a new file (younger than 30 days)
        new_file = self.test_dir / "new_file.txt"
        self._create_file_with_age(new_file, 29)

        # Run cleanup
        deleted_files = self.organizer.cleanup_old_files(
            directory=self.test_dir,
            days_old=30,
            recursive=False
        )

        # Verify old file is deleted
        self.assertFalse(old_file.exists(), "Old file should be deleted")
        self.assertIn(old_file, deleted_files)

        # Verify new file is kept
        self.assertTrue(new_file.exists(), "New file should be kept")
        self.assertNotIn(new_file, deleted_files)

    def test_cleanup_recursive(self):
        # Create directory structure
        subdir = self.test_dir / "subdir"
        subdir.mkdir()

        # Create old file in subdir
        old_file = subdir / "old_file_recursive.txt"
        self._create_file_with_age(old_file, 31)

        # Create new file in subdir
        new_file = subdir / "new_file_recursive.txt"
        self._create_file_with_age(new_file, 29)

        # Run cleanup recursively
        deleted_files = self.organizer.cleanup_old_files(
            directory=self.test_dir,
            days_old=30,
            recursive=True
        )

        # Verify old file is deleted
        self.assertFalse(old_file.exists(), "Old file in subdir should be deleted")
        self.assertIn(old_file, deleted_files)

        # Verify new file is kept
        self.assertTrue(new_file.exists(), "New file in subdir should be kept")
        self.assertNotIn(new_file, deleted_files)

    def test_cleanup_no_recursive(self):
        # Create directory structure
        subdir = self.test_dir / "subdir"
        subdir.mkdir()

        # Create old file in subdir
        old_file = subdir / "old_file_recursive.txt"
        self._create_file_with_age(old_file, 31)

        # Run cleanup non-recursively
        deleted_files = self.organizer.cleanup_old_files(
            directory=self.test_dir,
            days_old=30,
            recursive=False
        )

        # Verify old file in subdir is kept
        self.assertTrue(old_file.exists(), "Old file in subdir should be kept when recursive=False")
        self.assertNotIn(old_file, deleted_files)

    def test_cleanup_dry_run(self):
        # Create an old file
        old_file = self.test_dir / "dry_run_file.txt"
        self._create_file_with_age(old_file, 31)

        # Run cleanup with dry_run=True
        deleted_files = self.organizer.cleanup_old_files(
            directory=self.test_dir,
            days_old=30,
            dry_run=True
        )

        # Verify old file is kept
        self.assertTrue(old_file.exists(), "Old file should be kept in dry run")
        self.assertIn(old_file, deleted_files, "Old file should be reported in dry run")

    def test_cleanup_edge_case_days(self):
        # Create a file just now (effectively 0 days old)
        zero_days_file = self.test_dir / "zero_days.txt"
        # Create it with an age slightly greater than 0 so it's definitely in the past
        # relative to when cleanup_old_files runs.
        self._create_file_with_age(zero_days_file, 0.01)

        # Run cleanup with days_old=0
        deleted_files = self.organizer.cleanup_old_files(
            directory=self.test_dir,
            days_old=0,
            recursive=False
        )

        # Verify file is deleted
        self.assertFalse(zero_days_file.exists(), "File created before now should be deleted with days_old=0")
        self.assertIn(zero_days_file, deleted_files)

if __name__ == '__main__':
    unittest.main()
