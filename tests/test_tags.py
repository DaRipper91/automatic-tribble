"""
Tests for the tagging system.
"""

import pytest
import sqlite3
from pathlib import Path
from src.file_manager.tags import TagManager

@pytest.fixture
def temp_db(tmp_path):
    db_path = tmp_path / "test_tags.db"
    return db_path

def test_add_tag(temp_db):
    tm = TagManager(temp_db)
    file_path = Path("/tmp/test_file.txt")

    # Add tag
    assert tm.add_tag(file_path, "work")

    # Verify
    tags = tm.get_tags_for_file(file_path)
    assert "work" in tags

def test_remove_tag(temp_db):
    tm = TagManager(temp_db)
    file_path = Path("/tmp/test_file.txt")
    tm.add_tag(file_path, "work")

    # Remove
    assert tm.remove_tag(file_path, "work")
    tags = tm.get_tags_for_file(file_path)
    assert "work" not in tags

def test_get_files_by_tag(temp_db):
    tm = TagManager(temp_db)
    file1 = Path("/tmp/f1.txt")
    file2 = Path("/tmp/f2.txt")

    tm.add_tag(file1, "project")
    tm.add_tag(file2, "project")
    tm.add_tag(file1, "draft")

    files = tm.get_files_by_tag("project")
    assert len(files) == 2
    # Check paths (convert to resolved strings for comparison, but sqlite stores resolved)
    # Since we passed absolute paths (or at least starting with /), resolve() should keep them absolute.
    # But Path("/tmp/f1.txt").resolve() might be actual path.
    # In test environment, /tmp might be symlink.
    # Let's use string comparison of resolved paths.
    expected = {str(file1.resolve()), str(file2.resolve())}
    actual = {str(p.resolve()) for p in files}
    assert expected == actual

def test_suggest_tags():
    tm = TagManager() # In-memory or default, doesn't matter for static suggestion

    assert "image" in tm.suggest_tags(Path("photo.jpg"))
    assert "code" in tm.suggest_tags(Path("script.py"))
    assert "finance" in tm.suggest_tags(Path("invoice_2023.pdf"))
