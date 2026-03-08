import unittest
from pathlib import Path
import shutil
import tempfile
from src.file_manager.tags import TagManager

class TestTagManagerCleanup(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.db_path = self.test_dir / "test_tags.db"
        self.manager = TagManager(self.db_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_cleanup_missing_files(self):
        # Create files and tags
        f1 = self.test_dir / "f1.txt"
        f1.touch()
        f2 = self.test_dir / "f2.txt"
        f2.touch()

        self.manager.add_tag(f1, "tag1")
        self.manager.add_tag(f1, "tag2")
        self.manager.add_tag(f2, "tag3")

        # Verify initial state
        self.assertEqual(len(self.manager.get_tags_for_file(f1)), 2)
        self.assertEqual(len(self.manager.get_tags_for_file(f2)), 1)

        # Delete f1
        f1.unlink()

        # Run cleanup
        removed = self.manager.cleanup_missing_files()

        # Should have removed 2 entries for f1
        self.assertEqual(removed, 2)
        self.assertEqual(len(self.manager.get_tags_for_file(f1)), 0)
        self.assertEqual(len(self.manager.get_tags_for_file(f2)), 1)

    def test_cleanup_no_missing_files(self):
        f1 = self.test_dir / "f1.txt"
        f1.touch()
        self.manager.add_tag(f1, "tag1")

        removed = self.manager.cleanup_missing_files()
        self.assertEqual(removed, 0)
        self.assertEqual(len(self.manager.get_tags_for_file(f1)), 1)

    def test_cleanup_multiple_missing(self):
        f1 = self.test_dir / "f1.txt"
        f1.touch()
        f2 = self.test_dir / "f2.txt"
        f2.touch()

        self.manager.add_tag(f1, "tag1")
        self.manager.add_tag(f2, "tag2")

        f1.unlink()
        f2.unlink()

        removed = self.manager.cleanup_missing_files()
        self.assertEqual(removed, 2)
        self.assertEqual(len(self.manager.get_tags_for_file(f1)), 0)
        self.assertEqual(len(self.manager.get_tags_for_file(f2)), 0)

if __name__ == "__main__":
    unittest.main()
