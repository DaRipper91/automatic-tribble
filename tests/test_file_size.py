import pytest
import os
import tempfile
from pathlib import Path
from src.file_manager.file_operations import FileOperations

class TestFileSize:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_path = Path(self.temp_dir.name)
        self.file_ops = FileOperations()
        yield
        self.temp_dir.cleanup()

    def test_get_size_nonexistent(self):
        nonexistent = self.test_path / "nonexistent"
        assert self.file_ops.get_size(nonexistent) == 0

    def test_get_size_file(self):
        file_path = self.test_path / "test.txt"
        content = "Hello, World!"
        file_path.write_text(content)
        assert self.file_ops.get_size(file_path) == len(content)

    def test_get_size_empty_directory(self):
        dir_path = self.test_path / "empty_dir"
        dir_path.mkdir()
        assert self.file_ops.get_size(dir_path) == 0

    def test_get_size_directory_with_files(self):
        dir_path = self.test_path / "dir_with_files"
        dir_path.mkdir()

        f1 = dir_path / "f1.txt"
        f1.write_text("abc") # 3 bytes

        f2 = dir_path / "f2.txt"
        f2.write_text("defg") # 4 bytes

        assert self.file_ops.get_size(dir_path) == 7

    def test_get_size_nested_directory(self):
        root_dir = self.test_path / "root"
        root_dir.mkdir()

        f1 = root_dir / "f1.txt"
        f1.write_text("123") # 3 bytes

        sub_dir = root_dir / "subdir"
        sub_dir.mkdir()

        f2 = sub_dir / "f2.txt"
        f2.write_text("4567") # 4 bytes

        assert self.file_ops.get_size(root_dir) == 7

    def test_format_size(self):
        assert FileOperations.format_size(0) == "0.0 B"
        assert FileOperations.format_size(1023) == "1023.0 B"
        assert FileOperations.format_size(1024) == "1.0 KB"
        assert FileOperations.format_size(1024**2) == "1.0 MB"
        assert FileOperations.format_size(1024**3) == "1.0 GB"
        assert FileOperations.format_size(1024**4) == "1.0 TB"
        assert FileOperations.format_size(1024**5) == "1.0 PB"
        assert FileOperations.format_size(1536) == "1.5 KB"

    def test_get_size_with_symlink_to_file(self):
        file_path = self.test_path / "test.txt"
        content = "symlink content"
        file_path.write_text(content)

        symlink_path = self.test_path / "test_link.txt"
        try:
            symlink_path.symlink_to(file_path)
        except OSError:
            pytest.skip("Symlinks not supported on this platform")

        assert self.file_ops.get_size(symlink_path) == len(content)

    def test_get_directory_size_with_symlink_to_file(self):
        dir_path = self.test_path / "dir_with_link"
        dir_path.mkdir()

        file_path = self.test_path / "external.txt"
        content = "external content"
        file_path.write_text(content)

        symlink_path = dir_path / "link.txt"
        try:
            symlink_path.symlink_to(file_path)
        except OSError:
            pytest.skip("Symlinks not supported on this platform")

        # _get_directory_size uses follow_symlinks=True for files
        assert self.file_ops.get_size(dir_path) == len(content)

    def test_get_directory_size_with_symlink_to_dir(self):
        # Setup:
        # root/
        #   subdir/ (contains file 4 bytes)
        #   link_to_subdir -> subdir

        root = self.test_path / "root_link_dir"
        root.mkdir()

        subdir = root / "subdir"
        subdir.mkdir()

        f = subdir / "file.txt"
        f.write_text("1234")

        link = root / "link_to_subdir"
        try:
            link.symlink_to(subdir, target_is_directory=True)
        except OSError:
            pytest.skip("Symlinks not supported on this platform")

        # recursive_scan uses follow_symlinks=False for directories
        # So link_to_subdir should be yielded by recursive_scan,
        # but entry.is_dir(follow_symlinks=False) will be True for it?
        # Wait, if it is a symlink, is_dir(follow_symlinks=False) is True?
        # Actually os.DirEntry.is_dir(follow_symlinks=False) is True if it's a directory and NOT a symlink?
        # No, if it's a symlink to a directory:
        # is_dir(follow_symlinks=False) -> False
        # is_dir(follow_symlinks=True) -> True

        # In recursive_scan:
        # if entry.is_dir(follow_symlinks=False): stack.append(entry.path)
        # So it won't recurse into link_to_subdir.

        # In _get_directory_size:
        # if entry.is_file(follow_symlinks=True): total += ...
        # link_to_subdir is NOT a file (it's a directory), even if we follow symlinks.
        # So it should NOT be counted.

        assert self.file_ops.get_size(root) == 4
