import pytest
from pathlib import Path
from src.file_manager.tags import TagManager

@pytest.fixture
def tag_manager(tmp_path):
    db_path = tmp_path / "tags.db"
    return TagManager(db_path)

def test_add_remove_tag(tag_manager, tmp_path):
    file1 = tmp_path / "file1.txt"
    file1.touch()

    assert tag_manager.add_tag(file1, "work")
    assert tag_manager.add_tag(file1, "project")

    tags = tag_manager.get_tags_for_file(file1)
    assert "work" in tags
    assert "project" in tags
    assert len(tags) == 2

    assert tag_manager.remove_tag(file1, "work")
    tags = tag_manager.get_tags_for_file(file1)
    assert "work" not in tags
    assert "project" in tags

def test_get_files_by_tag(tag_manager, tmp_path):
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.touch()
    file2.touch()

    tag_manager.add_tag(file1, "important")
    tag_manager.add_tag(file2, "important")

    files = tag_manager.get_files_by_tag("important")
    assert len(files) == 2
    # Check string representation because Path equality can be tricky with resolve()
    paths = [str(p.resolve()) for p in files]
    assert str(file1.resolve()) in paths
    assert str(file2.resolve()) in paths

def test_list_all_tags(tag_manager, tmp_path):
    file1 = tmp_path / "file1.txt"
    file1.touch()

    tag_manager.add_tag(file1, "tag1")
    tag_manager.add_tag(file1, "tag2")

    tags = tag_manager.list_all_tags()
    tag_names = [t[0] for t in tags]
    assert "tag1" in tag_names
    assert "tag2" in tag_names
    assert len(tags) == 2

def test_cleanup_missing_files(tag_manager, tmp_path):
    file1 = tmp_path / "file1.txt"
    file1.touch()
    tag_manager.add_tag(file1, "temp")

    file1.unlink() # Delete file

    removed = tag_manager.cleanup_missing_files()
    assert removed == 1

    tags = tag_manager.list_all_tags()
    assert len(tags) == 0

def test_export_tags(tag_manager, tmp_path):
    file1 = tmp_path / "file1.txt"
    file1.touch()
    tag_manager.add_tag(file1, "export_tag")

    export = tag_manager.get_all_tags_export()
    key = str(file1.resolve())
    assert key in export
    assert "export_tag" in export[key]
