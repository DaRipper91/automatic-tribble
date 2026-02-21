import shutil
import pytest
from pathlib import Path
from src.file_manager.automation import FileOrganizer

@pytest.fixture
def temp_dir(tmp_path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    return source, target

def test_organize_by_type_no_overwrite(temp_dir):
    source, target = temp_dir
    file_name = "test_image.jpg"

    # Create source file
    source_file = source / file_name
    source_file.write_text("New Content")

    # Create existing target file
    category_dir = target / "images"
    category_dir.mkdir()
    existing_file = category_dir / file_name
    existing_file.write_text("Original Content")

    organizer = FileOrganizer()
    organizer.organize_by_type(source, target, move=False)

    # Check original file
    assert existing_file.read_text() == "Original Content"

    # Check new file
    new_file = category_dir / "test_image_1.jpg"
    assert new_file.exists()
    assert new_file.read_text() == "New Content"

def test_organize_by_date_no_overwrite(temp_dir):
    source, target = temp_dir
    file_name = "test_doc.txt"

    # Create source file
    source_file = source / file_name
    source_file.write_text("New Content")

    # Calculate expected date directory
    import datetime
    mtime = source_file.stat().st_mtime
    date_str = datetime.datetime.fromtimestamp(mtime).strftime("%Y/%m")

    # Create existing target file
    date_dir = target / date_str
    date_dir.mkdir(parents=True)
    existing_file = date_dir / file_name
    existing_file.write_text("Original Content")

    organizer = FileOrganizer()
    organizer.organize_by_date(source, target, move=False)

    # Check original file
    assert existing_file.read_text() == "Original Content"

    # Check new file
    new_file = date_dir / "test_doc_1.txt"
    assert new_file.exists()
    assert new_file.read_text() == "New Content"

def test_multiple_collisions(temp_dir):
    source, target = temp_dir
    file_name = "test_image.jpg"

    # Create source file
    source_file = source / file_name
    source_file.write_text("New Content 3")

    # Create existing target files
    category_dir = target / "images"
    category_dir.mkdir()
    (category_dir / file_name).write_text("Original Content 0")
    (category_dir / "test_image_1.jpg").write_text("Original Content 1")
    (category_dir / "test_image_2.jpg").write_text("Original Content 2")

    organizer = FileOrganizer()
    organizer.organize_by_type(source, target, move=False)

    # Check new file uses next available index
    new_file = category_dir / "test_image_3.jpg"
    assert new_file.exists()
    assert new_file.read_text() == "New Content 3"
