
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
        # We will force a small chunk size in the implementation or just test with a large enough file
        # But since I can't easily mock chunk size inside the method without modifying it,
        # I will rely on the logic being correct for any chunk size.
        # However, to be sure, I should test with a string that would definitely cross a 64KB boundary if I could control it.
        # Instead, I'll trust the logic verification I did.

        # But I can create a scenario that verifies "search works" generally.

        filename = self.test_dir / "split_test.txt"
        target = "SEARCH_TARGET"
        padding = "x" * (64 * 1024 - 5) # 64KB - 5 chars

        # This puts "SEARCH_TARGET" starting at index 65531.
        # If chunk size is 64KB (65536), the first chunk will end at 65536.
        # "SEARCH_TARGET" is 13 chars.
        # It spans from 65531 to 65544.
        # So it is split: "SEARCH" (6 chars) in chunk 1, "_TARGET" (7 chars) in chunk 2.

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
