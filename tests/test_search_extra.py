import pytest
from src.file_manager.search import FileSearcher
from unittest.mock import patch

@pytest.fixture
def searcher():
    return FileSearcher()

def test_search_by_name_case_sensitive(searcher, tmp_path):
    f1 = tmp_path / "Test.txt"
    f1.touch()
    f2 = tmp_path / "test.txt"
    f2.touch()

    res = searcher.search_by_name(tmp_path, "Test.txt", case_sensitive=True)
    assert len(res) == 1
    assert res[0].name == "Test.txt"

def test_search_by_name_non_recursive(searcher, tmp_path):
    f1 = tmp_path / "test.txt"
    f1.touch()
    d1 = tmp_path / "d1"
    d1.mkdir()
    f2 = d1 / "test.txt"
    f2.touch()

    res = searcher.search_by_name(tmp_path, "test.txt", recursive=False)
    assert len(res) == 1
    assert res[0].name == "test.txt"

def test_search_by_name_oserror(searcher, tmp_path):
    with patch("os.scandir", side_effect=OSError("mock")):
        res = searcher.search_by_name(tmp_path, "test.txt", recursive=False)
        assert len(res) == 0

def test_search_by_content_empty_query(searcher, tmp_path):
    res = searcher.search_by_content(tmp_path, "")
    assert len(res) == 0

def test_search_by_content_case_sensitive(searcher, tmp_path):
    f1 = tmp_path / "test1.txt"
    f1.write_text("Hello World")
    f2 = tmp_path / "test2.txt"
    f2.write_text("hello world")

    res = searcher.search_by_content(tmp_path, "Hello", case_sensitive=True)
    assert len(res) == 1
    assert res[0].name == "test1.txt"

def test_search_by_size_min(searcher, tmp_path):
    f1 = tmp_path / "test1.txt"
    f1.write_text("a" * 10)
    f2 = tmp_path / "test2.txt"
    f2.write_text("a" * 100)

    res = searcher.search_by_size(tmp_path, min_size=50)
    assert len(res) == 1
    assert res[0].name == "test2.txt"

def test_search_by_size_max(searcher, tmp_path):
    f1 = tmp_path / "test1.txt"
    f1.write_text("a" * 10)
    f2 = tmp_path / "test2.txt"
    f2.write_text("a" * 100)

    res = searcher.search_by_size(tmp_path, max_size=50)
    assert len(res) == 1
    assert res[0].name == "test1.txt"

def test_search_by_size_oserror(searcher, tmp_path):
    with patch("os.scandir", side_effect=OSError("mock")):
        res = searcher.search_by_size(tmp_path, min_size=10, recursive=False)
        assert len(res) == 0

def test_search_is_text_file(searcher, tmp_path):
    f1 = tmp_path / "test.bin"
    f1.write_bytes(b"\x00\x01")
    assert searcher._is_text_file(f1) is False

    f2 = tmp_path / "test.txt"
    f2.write_text("hello")
    assert searcher._is_text_file(f2) is True

def test_search_is_text_file_empty(searcher, tmp_path):
    f1 = tmp_path / "empty.bin"
    f1.write_bytes(b"")
    assert searcher._is_text_file(f1) is True

def test_search_by_tag_missing(searcher, tmp_path):
    with patch("src.file_manager.tags.TagManager.get_files_by_tag", return_value=[tmp_path / "missing.txt"]):
         res = searcher.search_by_tag("mytag")
         assert len(res) == 0 # because missing.txt doesn't exist

def test_search_by_name_recursive_oserror(searcher, tmp_path):
    with patch("src.file_manager.utils.recursive_scan", side_effect=OSError("mock")):
        res = searcher.search_by_name(tmp_path, "test.txt", recursive=True)
        assert len(res) == 0

def test_search_by_size_recursive_oserror(searcher, tmp_path):
    with patch("src.file_manager.utils.recursive_scan", side_effect=OSError("mock")):
        res = searcher.search_by_size(tmp_path, min_size=10, recursive=True)
        assert len(res) == 0

def test_search_by_content_recursive_oserror(searcher, tmp_path):
    with patch("src.file_manager.utils.recursive_scan", side_effect=OSError("mock")):
        res = searcher.search_by_content(tmp_path, "test", file_pattern="*")
        assert len(res) == 0

def test_file_contains_term_oserror(searcher, tmp_path):
    f = tmp_path / "test.txt"
    f.touch()
    with patch("builtins.open", side_effect=OSError("mock")):
        res = searcher._file_contains_term(f, "test", False)
        assert res is False

def test_is_text_file_oserror(searcher, tmp_path):
    f = tmp_path / "test.bin"
    f.touch()
    with patch("builtins.open", side_effect=OSError("mock")):
        res = searcher._is_text_file(f)
        assert res is False
