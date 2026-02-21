import unittest
import shutil
import time
import os
from pathlib import Path
from datetime import datetime, timedelta
from src.file_manager.automation import FileOrganizer, SECONDS_PER_DAY

class TestCleanupOldFiles(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("test_cleanup_files")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir()
        self.organizer = FileOrganizer()

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def create_file(self, path: Path, days_old: int):
        path.touch()
        # Set mtime to days_old ago
        # Subtract a bit more to be safe (e.g. 1 hour)
        mtime = time.time() - (days_old * 86400) - 3600
        os.utime(path, (mtime, mtime))

    def test_cleanup_basic(self):
        # Create old file
        old_file = self.test_dir / "old.txt"
        self.create_file(old_file, 10)

        # Create new file
        new_file = self.test_dir / "new.txt"
        self.create_file(new_file, 1)

        # Cleanup files older than 5 days
        deleted = self.organizer.cleanup_old_files(self.test_dir, days_old=5, recursive=False)

        self.assertIn(old_file, deleted)
        self.assertNotIn(new_file, deleted)
        self.assertFalse(old_file.exists())
        self.assertTrue(new_file.exists())

    def test_cleanup_recursive(self):
        subdir = self.test_dir / "subdir"
        subdir.mkdir()

        old_file = subdir / "old_recursive.txt"
        self.create_file(old_file, 10)

        deleted = self.organizer.cleanup_old_files(self.test_dir, days_old=5, recursive=True)

        self.assertIn(old_file, deleted)
        self.assertFalse(old_file.exists())

    def test_cleanup_dry_run(self):
        old_file = self.test_dir / "old_dry.txt"
        self.create_file(old_file, 10)

        deleted = self.organizer.cleanup_old_files(self.test_dir, days_old=5, recursive=False, dry_run=True)

        self.assertIn(old_file, deleted)
        self.assertTrue(old_file.exists())

    def test_cleanup_no_recursive_skips_subdir(self):
        subdir = self.test_dir / "subdir"
        subdir.mkdir()

        old_file = subdir / "old_recursive.txt"
        self.create_file(old_file, 10)

        deleted = self.organizer.cleanup_old_files(self.test_dir, days_old=5, recursive=False)

        self.assertNotIn(old_file, deleted)
        self.assertTrue(old_file.exists())

if __name__ == '__main__':
    unittest.main()
