import pytest
import json
import sqlite3
from pathlib import Path
from src.file_manager.tags import TagManager

@pytest.fixture
def tag_manager(tmp_path):
    db_path = tmp_path / "test_tags_export.db"
    return TagManager(db_path)

def test_export_tags(tag_manager, tmp_path):
    f1 = tmp_path / "file1.txt"
    f2 = tmp_path / "file2.txt"
    f1.touch()
    f2.touch()

    tag_manager.add_tag(f1, "work")
    tag_manager.add_tag(f1, "important")
    tag_manager.add_tag(f2, "personal")

    exported = tag_manager.export_tags()

    # Paths in DB are absolute resolved strings
    path1 = str(f1.resolve())
    path2 = str(f2.resolve())

    assert path1 in exported
    assert "work" in exported[path1]
    assert "important" in exported[path1]

    assert path2 in exported
    assert "personal" in exported[path2]
