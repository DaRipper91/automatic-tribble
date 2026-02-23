import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from src.file_manager.automation import FileOrganizer, ConflictResolutionStrategy

@pytest.mark.asyncio
class TestAutomationAsync:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        self.organizer = FileOrganizer()
        yield
        self.temp_dir.cleanup()

    async def test_organize_by_type(self):
        # Create test files
        (self.test_dir / "test.txt").touch()
        (self.test_dir / "test.jpg").touch()
        (self.test_dir / "test.unknown").touch()

        target_dir = self.test_dir / "organized"

        result = await self.organizer.organize_by_type(self.test_dir, target_dir, move=False)

        assert "documents" in result
        assert "images" in result

        # Check if files were copied correctly
        assert (target_dir / "documents" / "test.txt").exists()
        assert (target_dir / "images" / "test.jpg").exists()

        # Verify source still exists
        assert (self.test_dir / "test.txt").exists()

    async def test_organize_by_date(self):
        file_path = self.test_dir / "test.txt"
        file_path.touch()

        # Get expected date format
        mtime = file_path.stat().st_mtime
        from datetime import datetime
        date_str = datetime.fromtimestamp(mtime).strftime("%Y/%m")

        target_dir = self.test_dir / "organized"

        result = await self.organizer.organize_by_date(self.test_dir, target_dir, move=True)

        assert date_str in result
        assert (target_dir / date_str / "test.txt").exists()
        assert not file_path.exists()

    async def test_find_duplicates(self):
        # Create duplicates
        file1 = self.test_dir / "file1.txt"
        file1.write_text("content")

        file2 = self.test_dir / "file2.txt"
        file2.write_text("content")

        file3 = self.test_dir / "file3.txt"
        file3.write_text("different")

        duplicates = await self.organizer.find_duplicates(self.test_dir)

        assert len(duplicates) == 1 # One group
        hash_val = list(duplicates.keys())[0]
        paths = duplicates[hash_val]
        assert len(paths) == 2
        assert file1 in paths
        assert file2 in paths
        assert file3 not in paths

    async def test_resolve_duplicates_keep_newest(self):
        file1 = self.test_dir / "old.txt"
        file1.write_text("content")
        os.utime(file1, (0, 0)) # Very old

        file2 = self.test_dir / "new.txt"
        file2.write_text("content")
        # Default time is now

        duplicates = await self.organizer.find_duplicates(self.test_dir)
        deleted = await self.organizer.resolve_duplicates(duplicates, ConflictResolutionStrategy.KEEP_NEWEST)

        assert len(deleted) == 1
        assert deleted[0] == file1
        assert not file1.exists()
        assert file2.exists()

    async def test_batch_rename(self):
        file1 = self.test_dir / "old_name_1.txt"
        file1.touch()
        file2 = self.test_dir / "old_name_2.txt"
        file2.touch()

        renamed = await self.organizer.batch_rename(self.test_dir, "old_name", "new_name")

        assert len(renamed) == 2
        assert (self.test_dir / "new_name_1.txt").exists()
        assert (self.test_dir / "new_name_2.txt").exists()
        assert not file1.exists()

    async def test_progress_queue(self):
        queue = asyncio.Queue()
        file1 = self.test_dir / "test.txt"
        file1.touch()

        target_dir = self.test_dir / "organized"

        task = asyncio.create_task(self.organizer.organize_by_type(
            self.test_dir, target_dir, progress_queue=queue
        ))

        item = await queue.get()
        assert item == file1 or item.name == "test.txt"

        await task
