
import unittest
import shutil
from pathlib import Path
from src.file_manager.automation import FileOrganizer
from datetime import datetime

class TestOrganizerOverwrite(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("test_organizer_overwrite")
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

    def test_organize_by_date_no_overwrite(self):
        # Create a source file
        source_file = self.source_dir / "test_file.txt"
        source_file.write_text("New Content")

        # Determine where it will go
        mtime = source_file.stat().st_mtime
        date = datetime.fromtimestamp(mtime)
        date_str = date.strftime("%Y/%m")

        target_date_dir = self.target_dir / date_str
        target_date_dir.mkdir(parents=True, exist_ok=True)

        # Create a file that would clash
        target_file = target_date_dir / "test_file.txt"
        target_file.write_text("Original Content")

        # Organize
        self.organizer.organize_by_date(self.source_dir, self.target_dir, move=False)

        # Verify original file is intact
        self.assertEqual(target_file.read_text(), "Original Content")

        # Verify new file exists with a different name
        # We expect test_file_1.txt or similar.
        # Check for files in the directory
        files = list(target_date_dir.iterdir())
        self.assertGreater(len(files), 1, "Should have more than 1 file (original + copied)")

        copied_file = None
        for f in files:
            if f.name != "test_file.txt" and f.read_text() == "New Content":
                copied_file = f
                break

        self.assertIsNotNone(copied_file, "Could not find the copied file with new content")

    def test_organize_by_type_no_overwrite(self):
        # Create a source file (image)
        source_file = self.source_dir / "image.jpg"
        source_file.write_text("New Image Content")

        # Prepare target directory
        target_cat_dir = self.target_dir / "images"
        target_cat_dir.mkdir(parents=True, exist_ok=True)

        # Create a file that would clash
        target_file = target_cat_dir / "image.jpg"
        target_file.write_text("Original Image Content")

        # Organize
        self.organizer.organize_by_type(self.source_dir, self.target_dir, move=False)

        # Verify original file is intact
        self.assertEqual(target_file.read_text(), "Original Image Content")

        # Verify new file exists with a different name
        files = list(target_cat_dir.iterdir())
        self.assertGreater(len(files), 1)

        copied_file = None
        for f in files:
            if f.name != "image.jpg" and f.read_text() == "New Image Content":
                copied_file = f
                break

        self.assertIsNotNone(copied_file, "Could not find the copied file with new content")
