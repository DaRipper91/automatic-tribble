
import time
import os
import shutil
import sys
import resource
from pathlib import Path
from src.file_manager.search import FileSearcher

def create_large_file(path, size_mb):
    chunk = "A" * (1024 * 1024)
    with open(path, "w") as f:
        for _ in range(size_mb):
            f.write(chunk)
        f.write("TARGET_STRING_HERE")

def benchmark():
    searcher = FileSearcher()
    test_dir = Path("benchmark_data")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()

    print("Creating 100MB test file (one line)...")
    huge_file = test_dir / "huge_line.txt"
    create_large_file(huge_file, 100)

    print("Benchmarking search_by_content...")

    start = time.time()
    try:
        results = searcher.search_by_content(test_dir, "TARGET_STRING_HERE")
        if not results:
            print("Target not found!")
    except Exception as e:
        print(f"Huge line search failed: {e}")
        results = []
    end = time.time()
    print(f"Huge line search time: {end - start:.4f}s")

    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(f"Max memory usage: {usage / 1024:.2f} MB")

    # Clean up
    shutil.rmtree(test_dir)

if __name__ == "__main__":
    benchmark()
