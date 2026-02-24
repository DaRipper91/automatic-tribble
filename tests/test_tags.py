import pytest
from pathlib import Path
from src.file_manager.tags import TagManager

@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "tags.db"
    return TagManager(db_file)

def test_add_remove_tag(temp_db, tmp_path):
    file = tmp_path / "test.txt"
    file.touch()

    assert temp_db.add_tag(file, "work")
    assert temp_db.get_tags(file) == ["work"]

    assert temp_db.remove_tag(file, "work")
    assert temp_db.get_tags(file) == []

def test_search_by_tag(temp_db, tmp_path):
    f1 = tmp_path / "f1.txt"
    f2 = tmp_path / "f2.txt"
    f1.touch()
    f2.touch()

    temp_db.add_tag(f1, "important")
    temp_db.add_tag(f2, "important")

    results = temp_db.search_by_tag("important")
    assert len(results) == 2
    # Check absolute paths because resolve happens in tags.py
    result_paths = [str(r.resolve()) for r in results]
    assert str(f1.resolve()) in result_paths
    assert str(f2.resolve()) in result_paths
