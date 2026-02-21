
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

if __name__ == "__main__":
    unittest.main()
