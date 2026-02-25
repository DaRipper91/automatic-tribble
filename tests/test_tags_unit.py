import pytest
import sqlite3
from pathlib import Path
from src.file_manager.tags import TagManager

@pytest.fixture
def tag_manager(tmp_path):
    db_path = tmp_path / "test_tags.db"
    return TagManager(db_path)

def test_add_and_get_tag(tag_manager, tmp_path):
    file_path = tmp_path / "test_file.txt"
    file_path.touch()

    assert tag_manager.add_tag(file_path, "work")
    tags = tag_manager.get_tags_for_file(file_path)
    assert "work" in tags

def test_remove_tag(tag_manager, tmp_path):
    file_path = tmp_path / "test_file.txt"
    file_path.touch()

    tag_manager.add_tag(file_path, "work")
    assert tag_manager.remove_tag(file_path, "work")
    tags = tag_manager.get_tags_for_file(file_path)
    assert "work" not in tags

def test_get_files_by_tag(tag_manager, tmp_path):
    f1 = tmp_path / "f1.txt"
    f2 = tmp_path / "f2.txt"
    f1.touch()
    f2.touch()

    tag_manager.add_tag(f1, "urgent")
    tag_manager.add_tag(f2, "urgent")

    files = tag_manager.get_files_by_tag("urgent")
    assert len(files) == 2
    # Check resolution
    assert f1.resolve() in [f.resolve() for f in files]

def test_cleanup(tag_manager, tmp_path):
    f1 = tmp_path / "f1.txt"
    f1.touch()
    tag_manager.add_tag(f1, "temp")

    f1.unlink() # Delete file

    deleted = tag_manager.cleanup_missing_files()
    assert deleted > 0
    assert len(tag_manager.get_files_by_tag("temp")) == 0
