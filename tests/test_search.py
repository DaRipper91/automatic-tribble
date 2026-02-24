import pytest
from src.file_manager.search import FileSearcher

class TestFileSearcher:

    @pytest.fixture
    def searcher(self):
        return FileSearcher()

    @pytest.fixture
    def test_files(self, tmp_path):
        # Create structure:
        # root/
        #   file1.txt (content: "hello world")
        #   File2.TXT (content: "HELLO WORLD")
        #   subdir/
        #     file3.py (content: "print('hello')")
        #     image.png (binary)

        (tmp_path / "file1.txt").write_text("hello world")
        (tmp_path / "File2.TXT").write_text("HELLO WORLD")

        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file3.py").write_text("print('hello')")

        # Create a "binary" file
        with open(subdir / "image.png", "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + b"\x00" * 100)

        return tmp_path

    def test_search_by_name(self, searcher, test_files):
        results = searcher.search_by_name(test_files, "file*.txt")
        # file1.txt, File2.TXT (case insensitive default)
        names = sorted([p.name for p in results])
        assert "File2.TXT" in names
        assert "file1.txt" in names

        results = searcher.search_by_name(test_files, "file*.txt", case_sensitive=True)
        # Should match file1.txt but NOT File2.TXT (because pattern is lowercase and F is uppercase? Wait.
        # fnmatch is platform dependent? No, implementation handles case sensitivity logic manually before calling fnmatch.
        # Implementation:
        # check_name = name if case_sensitive else name.lower()
        # if fnmatch.fnmatch(check_name, pattern):

        # If pattern is "file*.txt" (lowercase):
        # Case sensitive: check_name="File2.TXT". Pattern="file*.txt". No match.
        # check_name="file1.txt". Pattern="file*.txt". Match.
        assert len(results) == 1
        assert results[0].name == "file1.txt"

        results = searcher.search_by_name(test_files, "*.py", recursive=True)
        assert len(results) == 1
        assert results[0].name == "file3.py"

        results = searcher.search_by_name(test_files, "*.py", recursive=False)
        assert len(results) == 0

    def test_search_by_content(self, searcher, test_files):
        results = searcher.search_by_content(test_files, "hello")
        # file1.txt (hello), File2.TXT (HELLO -> hello if case insensitive), file3.py (hello)
        assert len(results) == 3

        results = searcher.search_by_content(test_files, "hello", case_sensitive=True)
        # file1.txt, file3.py. File2.TXT has HELLO.
        assert len(results) == 2

        # Add "hello" to binary file
        subdir = test_files / "subdir"
        with open(subdir / "image_with_text.png", "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + b"hello" + b"\x00" * 100)

        results = searcher.search_by_content(test_files, "hello")
        # Should NOT find image_with_text.png because it's detected as binary
        names = [p.name for p in results]
        assert "image_with_text.png" not in names

    def test_search_by_size(self, searcher, test_files):
        # file1.txt: 11 bytes
        # File2.TXT: 11 bytes
        # file3.py: 14 bytes
        # image.png: > 100 bytes

        results = searcher.search_by_size(test_files, min_size=12)
        # file3.py, image.png
        names = [p.name for p in results]
        assert "file3.py" in names
        assert "image.png" in names
        assert "file1.txt" not in names

        results = searcher.search_by_size(test_files, max_size=12)
        # file1.txt, File2.TXT
        names = [p.name for p in results]
        assert "file1.txt" in names
        assert "File2.TXT" in names
        assert "file3.py" not in names
