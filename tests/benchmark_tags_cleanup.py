import time
import sqlite3
import shutil
from pathlib import Path
from src.file_manager.tags import TagManager

def benchmark_cleanup(num_files=1000, missing_ratio=0.5):
    test_dir = Path("test_benchmark_tags")
    test_dir.mkdir(exist_ok=True)
    db_path = test_dir / "tags.db"
    if db_path.exists():
        db_path.unlink()

    manager = TagManager(db_path)

    # Create files and tags
    files = []
    for i in range(num_files):
        f = test_dir / f"file_{i}.txt"
        f.touch()
        manager.add_tag(f, f"tag_{i}")
        files.append(f)

    # Remove some files
    num_to_remove = int(num_files * missing_ratio)
    for i in range(num_to_remove):
        files[i].unlink()

    start_time = time.perf_counter()
    removed = manager.cleanup_missing_files()
    end_time = time.perf_counter()

    duration = end_time - start_time
    print(f"Cleaned up {removed} entries for {num_to_remove} missing files in {duration:.4f} seconds")

    # Cleanup
    shutil.rmtree(test_dir)
    return duration

if __name__ == "__main__":
    # Warm up
    benchmark_cleanup(num_files=100, missing_ratio=0.5)

    print("Running benchmark with 2000 files, 1000 missing...")
    duration = benchmark_cleanup(num_files=2000, missing_ratio=0.5)
    print(f"Result: {duration:.4f}s")
