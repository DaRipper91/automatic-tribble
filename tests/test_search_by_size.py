import pytest
from pathlib import Path
from src.file_manager.search import FileSearcher
import os

class TestSearchBySize:
    @pytest.fixture
    def searcher(self):
        return FileSearcher()

    @pytest.fixture
    def temp_files(self, tmp_path):
        f1 = tmp_path / "small.txt"
        f1.write_text("a") # 1 byte

        f2 = tmp_path / "medium.txt"
        f2.write_text("a" * 100) # 100 bytes

        f3 = tmp_path / "large.txt"
        f3.write_text("a" * 1000) # 1000 bytes

        subdir = tmp_path / "subdir"
        subdir.mkdir()
        f4 = subdir / "sub_medium.txt"
        f4.write_text("a" * 100)

        return tmp_path

    def test_search_min_size(self, searcher, temp_files):
        results = searcher.search_by_size(temp_files, min_size=50)
        # Should match medium, large, sub_medium
        assert len(results) == 3
        names = [p.name for p in results]
        assert "small.txt" not in names
        assert "medium.txt" in names
        assert "large.txt" in names
        assert "sub_medium.txt" in names

    def test_search_max_size(self, searcher, temp_files):
        results = searcher.search_by_size(temp_files, max_size=50)
        # Should match small
        assert len(results) == 1
        assert results[0].name == "small.txt"

    def test_search_range(self, searcher, temp_files):
        results = searcher.search_by_size(temp_files, min_size=50, max_size=500)
        # Should match medium, sub_medium
        assert len(results) == 2
        names = [p.name for p in results]
        assert "medium.txt" in names
        assert "sub_medium.txt" in names

    def test_search_recursive(self, searcher, temp_files):
        results = searcher.search_by_size(temp_files, min_size=50, recursive=False)
        # Should match medium, large (but not sub_medium)
        assert len(results) == 2
        names = [p.name for p in results]
        assert "medium.txt" in names
        assert "large.txt" in names
        assert "sub_medium.txt" not in names
