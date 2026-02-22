
import unittest
import shutil
import os
from pathlib import Path
from src.file_manager.search import FileSearcher

class TestSearchOptimization(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("test_search_opt")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir()
        self.searcher = FileSearcher()

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_search_split_boundary(self):
        # Create a file where the target string is likely to be split across chunks
        # Chunk size is 1MB = 1048576 bytes

        filename = self.test_dir / "split_test.txt"
        target = "SEARCH_TARGET"
        chunk_size = 1048576

        # Position the target so it crosses the 1MB boundary
        # We put 1048570 bytes of padding.
        # Boundary is at 1048576.
        # Target starts at 1048570.
        # "SEARCH_TARGET" is 13 chars.
        # 1048570 + 13 = 1048583.
        # So it crosses from chunk 1 to chunk 2.

        padding_len = chunk_size - 6 # Leave 6 chars in first chunk
        padding = "x" * padding_len

        with open(filename, "w") as f:
            f.write(padding)
            f.write(target)
            f.write("padding_after")

        results = self.searcher.search_by_content(self.test_dir, target)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], filename)

    def test_search_case_insensitive(self):
        filename = self.test_dir / "case_test.txt"
        with open(filename, "w") as f:
            f.write("Some TeXt HeRe")

        results = self.searcher.search_by_content(self.test_dir, "text", case_sensitive=False)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], filename)

    def test_search_not_found(self):
        filename = self.test_dir / "not_found.txt"
        with open(filename, "w") as f:
            f.write("Some random text")

        results = self.searcher.search_by_content(self.test_dir, "missing")
        self.assertEqual(len(results), 0)

    def test_search_unknown_extension_text(self):
        # File with unknown extension, but text content
        filename = self.test_dir / "unknown.foo"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("This is some text content that should be found.")

        results = self.searcher.search_by_content(self.test_dir, "content")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], filename)

    def test_search_unknown_extension_binary(self):
        # File with unknown extension, binary content
        filename = self.test_dir / "unknown.bin"
        with open(filename, "wb") as f:
            # Null byte makes it binary
            f.write(b"This is binary content \x00 that should be skipped.")

        # Even if we search for "content", it should be skipped because of null byte
        results = self.searcher.search_by_content(self.test_dir, "content")
        self.assertEqual(len(results), 0)

    def test_search_known_extension_text(self):
        # File with known extension
        filename = self.test_dir / "known.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("This is some text content in a txt file.")

        results = self.searcher.search_by_content(self.test_dir, "content")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], filename)

    def test_search_known_extension_binary_content(self):
        # File with known extension but binary content (e.g. utf-16 or just bad usage)
        # The current implementation opens known extensions as text with errors='ignore'.
        # So it might find strings if they appear in between binary data,
        # or if it's just a text file with a null byte.
        # It should be found because known extensions bypass the binary check.

        filename = self.test_dir / "lying.txt"
        with open(filename, "wb") as f:
            f.write(b"content \x00 more content")

        # "content" is in there. Open as text (ignore errors) will read "content \x00 more content".
        # It should be found.
        results = self.searcher.search_by_content(self.test_dir, "content")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], filename)

if __name__ == "__main__":
    unittest.main()

class TestFileSearcherHelper(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("test_search_helper")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir()

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_file_contains_term_simple(self):
        file_path = self.test_dir / "simple.txt"
        with open(file_path, "w") as f:
            f.write("This is a simple test.")

        # Test exact match
        self.assertTrue(FileSearcher._file_contains_term(file_path, "simple", case_sensitive=False))
        self.assertTrue(FileSearcher._file_contains_term(file_path, "simple", case_sensitive=True))

    def test_file_contains_term_case_sensitive(self):
        file_path = self.test_dir / "case.txt"
        with open(file_path, "w") as f:
            f.write("Case Sensitive Test")

        # In search_by_content, search_term is lowercased if case_sensitive is False.
        # But _file_contains_term expects search_term to be consistent with case_sensitive logic.

        # If case_sensitive is False, _file_contains_term lowercases the line.
        # So we should pass a lowercased search term if we want it to match "Case" with "case".

        # If case_sensitive is True, it does NOT lowercase the line.
        # So we must pass exact match.

        self.assertTrue(FileSearcher._file_contains_term(file_path, "case", case_sensitive=False))
        self.assertFalse(FileSearcher._file_contains_term(file_path, "case", case_sensitive=True))
        self.assertTrue(FileSearcher._file_contains_term(file_path, "Case", case_sensitive=True))

    def test_file_contains_term_not_found(self):
        file_path = self.test_dir / "missing.txt"
        with open(file_path, "w") as f:
            f.write("Nothing here.")

        self.assertFalse(FileSearcher._file_contains_term(file_path, "found", case_sensitive=False))

    def test_file_contains_term_empty(self):
        file_path = self.test_dir / "empty.txt"
        file_path.touch()

        self.assertFalse(FileSearcher._file_contains_term(file_path, "anything", case_sensitive=False))

    def test_file_contains_term_utf8(self):
        file_path = self.test_dir / "utf8.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("Hello 🌍 World")

        self.assertTrue(FileSearcher._file_contains_term(file_path, "🌍", case_sensitive=False))
