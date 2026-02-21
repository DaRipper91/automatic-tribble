import pytest
import os
import shutil
from pathlib import Path
from src.file_manager.automation import FileOrganizer
from src.file_manager.file_operations import FileOperations

@pytest.fixture
def test_env(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    secret_dir = tmp_path / "secret"
    secret_dir.mkdir()

    test_file = source_dir / "match_me.txt"
    test_file.write_text("sensitive data")

    return {
        "root": tmp_path,
        "source": source_dir,
        "target": target_dir,
        "secret": secret_dir,
        "file": test_file
    }

def test_batch_rename_traversal(test_env):
    organizer = FileOrganizer()
    source = test_env["source"]
    secret = test_env["secret"]

    # Attempt to move file out of source directory via replacement
    # We want it to be blocked or at least not move the file to the secret zone
    pattern = "match"
    replacement = "../secret/stolen"

    organizer.batch_rename(source, pattern, replacement, recursive=False)

    stolen_file = secret / "stolen_me.txt"
    assert not stolen_file.exists(), "Vulnerability: File was moved out of directory via batch_rename"

def test_organize_by_date_traversal(test_env):
    organizer = FileOrganizer()
    source = test_env["source"]
    secret = test_env["secret"]

    # Attempt to move file out via date_format
    # We use a date_format that goes up and into the secret directory
    date_format = "../../secret/%Y"

    organizer.organize_by_date(source, secret, date_format=date_format, move=True)

    # Check if any files appeared in the secret directory's parent or elsewhere
    # The expected path would be secret/../../secret/2023/... which is secret/../secret/2023
    # Wait, target_dir is 'secret'. date_str is '../../secret/2023'.
    # date_dir = secret / "../../secret/2023" = tmp_path / "secret/2023"
    # Actually, secret/../../secret/2023 = tmp_path / "secret" / "2023"
    # Let's use a more direct traversal:

    date_format = "../../../stolen_date"
    organizer.organize_by_date(source, test_env["target"], date_format=date_format, move=True)

    # Better to check if it's NOT in target, excluding the source directory
    for p in test_env["root"].rglob("match_me.txt"):
        if test_env["target"] not in p.parents and test_env["source"] not in p.parents:
             pytest.fail(f"Vulnerability: File found outside target and source directories: {p}")

def test_rename_traversal(test_env):
    ops = FileOperations()
    source_file = test_env["file"]
    secret_dir = test_env["secret"]

    new_name = "../secret/stolen_rename.txt"

    try:
        ops.rename(source_file, new_name)
    except (ValueError, Exception):
        pass # Expected if fixed

    stolen_file = secret_dir / "stolen_rename.txt"
    assert not stolen_file.exists(), "Vulnerability: File was moved out via FileOperations.rename"

def test_batch_rename_overwrite_prevention(test_env):
    organizer = FileOrganizer()
    source = test_env["source"]

    # Create two files
    file_a = source / "file_a.txt"
    file_b = source / "file_b.txt"

    file_a.write_text("content A")
    file_b.write_text("content B")

    # Try to rename file_a to file_b
    organizer.batch_rename(source, "a", "b")

    # Verify file_b still has its original content and file_a still exists
    assert file_b.read_text() == "content B", "Security: batch_rename should not overwrite existing files"
    assert file_a.exists(), "Security: file_a should still exist because rename should have been skipped"
