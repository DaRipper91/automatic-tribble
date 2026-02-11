import unittest
import shutil
import tempfile
from pathlib import Path
from src.file_manager.automation import FileOrganizer

class TestFileOrganizer(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.source_dir = self.test_dir / "source"
        self.target_dir = self.test_dir / "target"
        self.source_dir.mkdir()
        self.organizer = FileOrganizer()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_organize_by_type(self):
        # Create dummy files
        (self.source_dir / "test.txt").touch()
        (self.source_dir / "image.jpg").touch()

        organized = self.organizer.organize_by_type(self.source_dir, self.target_dir)

        self.assertIn('documents', organized)
        self.assertIn('images', organized)
        self.assertTrue((self.target_dir / 'documents' / 'test.txt').exists())
        self.assertTrue((self.target_dir / 'images' / 'image.jpg').exists())

if __name__ == '__main__':
    unittest.main()
