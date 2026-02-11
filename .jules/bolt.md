## 2024-05-23 - Chunked File Reading Performance
**Learning:** Python's `read()` on large text files creates massive string allocations, causing significant memory overhead and slowdowns, even for simple substring search.
**Action:** Always use chunked reading (`read(size)`) or line-by-line iteration for large file processing, especially when only a boolean result is needed.
