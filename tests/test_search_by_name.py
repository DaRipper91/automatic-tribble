import pytest
from pathlib import Path
from src.file_manager.search import FileSearcher

class TestSearchByName:
    @pytest.fixture
    def searcher(self):
        return FileSearcher()

    @pytest.fixture
    def temp_structure(self, tmp_path):
        """
        Creates a temporary directory structure:
        tmp_path/
            file1.txt
            file2.PY
            subfolder/
                file3.txt
                MatchingDir/
                    file4.log
            OtherDir/
        """
        file1 = tmp_path / "file1.txt"
        file1.write_text("content1")

        file2 = tmp_path / "file2.PY"
        file2.write_text("content2")

        subfolder = tmp_path / "subfolder"
        subfolder.mkdir()
        file3 = subfolder / "file3.txt"
        file3.write_text("content3")

        matching_dir = subfolder / "MatchingDir"
        matching_dir.mkdir()
        file4 = matching_dir / "file4.log"
        file4.write_text("content4")

        other_dir = tmp_path / "OtherDir"
        other_dir.mkdir()

        return {
            "root": tmp_path,
            "file1": file1,
            "file2": file2,
            "subfolder": subfolder,
            "file3": file3,
            "matching_dir": matching_dir,
            "file4": file4,
            "other_dir": other_dir
        }

    def test_search_recursive(self, searcher, temp_structure):
        results = searcher.search_by_name(temp_structure["root"], "*.txt", recursive=True)
        # Should find file1.txt and subdir/file3.txt
        assert len(results) == 2
        assert temp_structure["file1"] in results
        assert temp_structure["file3"] in results

    def test_search_non_recursive(self, searcher, temp_structure):
        results = searcher.search_by_name(temp_structure["root"], "*.txt", recursive=False)
        # Should only find file1.txt
        assert len(results) == 1
        assert temp_structure["file1"] in results
        assert temp_structure["file3"] not in results

    def test_search_case_sensitive(self, searcher, temp_structure):
        # Case sensitive search for *.PY
        results = searcher.search_by_name(temp_structure["root"], "*.PY", case_sensitive=True)
        assert len(results) == 1
        assert temp_structure["file2"] in results

        # Case sensitive search for *.py should fail to find file2.PY
        results = searcher.search_by_name(temp_structure["root"], "*.py", case_sensitive=True)
        assert len(results) == 0

    def test_search_case_insensitive(self, searcher, temp_structure):
        # Default is case-insensitive
        results = searcher.search_by_name(temp_structure["root"], "*.py")
        assert len(results) == 1
        assert temp_structure["file2"] in results

        # Explicitly case-insensitive
        results = searcher.search_by_name(temp_structure["root"], "*.py", case_sensitive=False)
        assert len(results) == 1
        assert temp_structure["file2"] in results

    def test_search_wildcards(self, searcher, temp_structure):
        results = searcher.search_by_name(temp_structure["root"], "file*", recursive=True)
        # Should find file1.txt, file2.PY, subdir/file3.txt, subdir/MatchingDir/file4.log
        assert len(results) == 4
        assert temp_structure["file1"] in results
        assert temp_structure["file2"] in results
        assert temp_structure["file3"] in results
        assert temp_structure["file4"] in results

    def test_search_matches_directories(self, searcher, temp_structure):
        results = searcher.search_by_name(temp_structure["root"], "*Dir", recursive=True)
        # Should find MatchingDir and OtherDir
        assert len(results) == 2
        assert temp_structure["matching_dir"] in results
        assert temp_structure["other_dir"] in results

    def test_search_non_recursive_dirs(self, searcher, temp_structure):
        results = searcher.search_by_name(temp_structure["root"], "*Dir", recursive=False)
        # Should only find OtherDir (MatchingDir is in subdir)
        assert len(results) == 1
        assert temp_structure["other_dir"] in results
        assert temp_structure["matching_dir"] not in results

    def test_search_no_results(self, searcher, temp_structure):
        results = searcher.search_by_name(temp_structure["root"], "nonexistent*")
        assert len(results) == 0
