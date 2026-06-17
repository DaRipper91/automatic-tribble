import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.file_manager.context import DirectoryContextBuilder

@pytest.fixture
def builder():
    return DirectoryContextBuilder(cache_ttl=60)

def test_human_size(builder):
    assert builder._human_size(500) == "500.0 B"
    assert builder._human_size(1024) == "1.0 KB"
    assert builder._human_size(1024 * 1024) == "1.0 MB"
    assert builder._human_size(1024**3) == "1.0 GB"
    assert builder._human_size(1024**4) == "1.0 TB"
    assert builder._human_size(1024**5) == "1.0 PB"
    assert builder._human_size(1024**6) == "1024.0 PB"

def test_scan_empty_directory(builder, tmp_path):
    stats = builder._scan_directory(tmp_path)
    assert stats.total_files == 0
    assert stats.total_size == 0
    assert stats.category_counts == {}
    assert stats.oldest_file == "None"
    assert stats.newest_file == "None"
    assert stats.top_largest_files == []
    assert stats.duplicate_groups == 0

def test_scan_directory_with_files(builder, tmp_path):
    # Create files with specific sizes and extensions
    (tmp_path / "file1.txt").write_text("hello") # 5 bytes
    (tmp_path / "file2.txt").write_text("world!!") # 7 bytes
    (tmp_path / "image.png").write_text("data") # 4 bytes

    # We'll mock entry.stat() to return specific values to avoid relying on filesystem mtimes
    with patch("os.scandir") as mock_scandir:
        mock_entries = []
        files = [
            ("file1.txt", 5, 100),
            ("file2.txt", 7, 150),
            ("image.png", 4, 200),
        ]
        for name, size, mtime in files:
            entry = MagicMock()
            entry.is_file.return_value = True
            entry.name = name
            entry.stat.return_value = MagicMock(st_size=size, st_mtime=mtime)
            mock_entries.append(entry)

        mock_scandir.return_value = mock_entries
        stats = builder._scan_directory(tmp_path)

    assert stats.total_files == 3
    assert stats.total_size == 16
    assert stats.category_counts == {".txt": 2, ".png": 1}
    assert stats.oldest_file == "file1.txt"
    assert stats.newest_file == "image.png"
    assert len(stats.top_largest_files) == 3
    assert stats.top_largest_files[0].name == "file2.txt"
    assert stats.top_largest_files[0].size == "7.0 B"

def test_duplicate_groups(builder, tmp_path):
    # Create files with same sizes using mock
    with patch("os.scandir") as mock_scandir:
        mock_entries = []
        sizes = [4, 4, 4, 6, 6]
        for i, size in enumerate(sizes):
            entry = MagicMock()
            entry.is_file.return_value = True
            entry.name = f"file{i}.txt"
            entry.stat.return_value = MagicMock(st_size=size, st_mtime=100)
            mock_entries.append(entry)

        mock_scandir.return_value = mock_entries
        stats = builder._scan_directory(tmp_path)

    # Sizes: 4, 4, 4, 6, 6
    # Groups: size 4 (count 3), size 6 (count 2) -> total 2 groups
    assert stats.duplicate_groups == 2

def test_top_5_largest(builder, tmp_path):
    with patch("os.scandir") as mock_scandir:
        mock_entries = []
        for i in range(10):
            entry = MagicMock()
            entry.is_file.return_value = True
            entry.name = f"file{i}.txt"
            entry.stat.return_value = MagicMock(st_size=i, st_mtime=100)
            mock_entries.append(entry)

        mock_scandir.return_value = mock_entries
        stats = builder._scan_directory(tmp_path)

    assert len(stats.top_largest_files) == 5
    assert len(stats.top_5_largest) == 5
    # Largest should be file9.txt (9 bytes)
    assert stats.top_largest_files[0].name == "file9.txt"
    assert stats.top_5_largest[0] == "file9.txt (9.0 B)"

def test_cache_mechanism(builder, tmp_path):
    with patch("time.time") as mock_time:
        mock_time.return_value = 1000.0

        # First call
        with patch.object(builder, "_scan_directory") as mock_scan:
            mock_scan.return_value = MagicMock()
            mock_scan.return_value.total_files = 1
            # context.py uses asdict(stats)
            with patch("src.file_manager.context.asdict") as mock_asdict:
                mock_asdict.return_value = {"total_files": 1}

                context1 = builder.get_context(tmp_path)
                assert context1["total_files"] == 1
                assert mock_scan.call_count == 1

                # Second call (should be cached)
                context2 = builder.get_context(tmp_path)
                assert context2["total_files"] == 1
                assert mock_scan.call_count == 1

                # Advance time beyond TTL
                mock_time.return_value = 1061.0
                mock_asdict.return_value = {"total_files": 2}

                # Third call (should be refreshed)
                context3 = builder.get_context(tmp_path)
                assert context3["total_files"] == 2
                assert mock_scan.call_count == 2

@patch("os.scandir")
def test_error_handling(mock_scandir, builder, tmp_path):
    mock_scandir.side_effect = PermissionError("Access denied")

    # Should not raise exception
    stats = builder._scan_directory(tmp_path)
    assert stats.total_files == 0

def test_stat_error_handling(builder, tmp_path):
    with patch("os.scandir") as mock_scandir:
        entry = MagicMock()
        entry.is_file.return_value = True
        entry.name = "test.txt"
        entry.stat.side_effect = OSError("Stat failed")
        mock_scandir.return_value = [entry]

        stats = builder._scan_directory(tmp_path)
        # Entry is found, but stat fails, so it should be skipped in totals
        assert stats.total_files == 1 # total_files incremented before try-except for stat
        assert stats.total_size == 0
