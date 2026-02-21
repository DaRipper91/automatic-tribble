import pytest
import os
from datetime import datetime
from src.file_manager.automation import FileOrganizer

@pytest.fixture
def organizer():
    return FileOrganizer()

def test_organize_by_date_copy_default(tmp_path, organizer):
    """Test default copy behavior: organized by YYYY/MM, original files kept."""
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    # Create file
    f = source / "test.txt"
    f.touch()

    # Get its date to know where it should go
    mtime = f.stat().st_mtime
    date_str = datetime.fromtimestamp(mtime).strftime("%Y/%m")

    organizer.organize_by_date(source, target)

    expected_path = target / date_str / "test.txt"
    assert expected_path.exists()
    assert f.exists() # Copy, so original remains

def test_organize_by_date_move(tmp_path, organizer):
    """Test move behavior: original files removed."""
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    f = source / "test.txt"
    f.touch()

    mtime = f.stat().st_mtime
    date_str = datetime.fromtimestamp(mtime).strftime("%Y/%m")

    organizer.organize_by_date(source, target, move=True)

    expected_path = target / date_str / "test.txt"
    assert expected_path.exists()
    assert not f.exists() # Move, so original gone

def test_organize_by_date_custom_format(tmp_path, organizer):
    """Test custom date format support."""
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    f = source / "test.txt"
    f.touch()

    mtime = f.stat().st_mtime
    date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")

    organizer.organize_by_date(source, target, date_format="%Y-%m-%d")

    expected_path = target / date_str / "test.txt"
    assert expected_path.exists()

def test_organize_by_date_mixed_dates(tmp_path, organizer):
    """Test organization of files with different timestamps."""
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    f1 = source / "file1.txt"
    f1.touch()
    # Set time to 2023-01-01
    dt1 = datetime(2023, 1, 1, 12, 0, 0)
    ts1 = dt1.timestamp()
    os.utime(f1, (ts1, ts1))

    f2 = source / "file2.txt"
    f2.touch()
    # Set time to 2023-02-01
    dt2 = datetime(2023, 2, 1, 12, 0, 0)
    ts2 = dt2.timestamp()
    os.utime(f2, (ts2, ts2))

    organizer.organize_by_date(source, target)

    assert (target / "2023/01" / "file1.txt").exists()
    assert (target / "2023/02" / "file2.txt").exists()

def test_organize_by_date_ignores_directories(tmp_path, organizer):
    """Test that directories in source are ignored."""
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    subdir = source / "subdir"
    subdir.mkdir()

    result = organizer.organize_by_date(source, target)

    # Check if any folder was created in target
    assert len(list(target.iterdir())) == 0
    assert len(result) == 0

def test_organize_by_date_path_traversal(tmp_path, organizer):
    """Test protection against path traversal via date_format."""
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    f = source / "test.txt"
    f.touch()

    # Try to write outside target using date_format
    organizer.organize_by_date(source, target, date_format="../outside")

    # Verify file was NOT copied outside
    outside = tmp_path / "outside"
    assert not outside.exists()

    # Verify file was NOT copied to target either (skipped)
    assert len(list(target.iterdir())) == 0
