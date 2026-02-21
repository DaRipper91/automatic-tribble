## 2024-05-23 - Chunked File Reading Performance
**Learning:** Python's `read()` on large text files creates massive string allocations, causing significant memory overhead and slowdowns, even for simple substring search.
**Action:** Always use chunked reading (`read(size)`) or line-by-line iteration for large file processing, especially when only a boolean result is needed.

## 2024-05-24 - File Search Performance
**Learning:** `os.walk` and `Path.iterdir()` create full path strings or objects for every entry, which is slow for large directories. `os.scandir` yields lightweight `DirEntry` objects with cached attributes, avoiding stat calls.
**Action:** Prefer `os.scandir` (recursively if needed) for file traversal, and delay `Path` object creation until a match is confirmed.
