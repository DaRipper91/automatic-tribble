import unittest
from unittest.mock import patch, MagicMock
import sys
from io import StringIO
from src.file_manager.cli import main
from pathlib import Path

class TestCLI(unittest.TestCase):
    def setUp(self):
        self.held_stdout = sys.stdout
        self.held_stderr = sys.stderr
        sys.stdout = StringIO()
        sys.stderr = StringIO()

    def tearDown(self):
        sys.stdout = self.held_stdout
        sys.stderr = self.held_stderr

    @patch('src.file_manager.cli.FileOrganizer')
    @patch('src.file_manager.cli.Path')
    def test_organize_by_type(self, MockPath, MockOrganizer):
        # Mock Path.exists to return True
        MockPath.return_value.exists.return_value = True

        test_args = ['cli.py', 'organize', '--source', '/src', '--target', '/dst', '--by-type']
        with patch.object(sys, 'argv', test_args):
            ret = main()
            self.assertEqual(ret, 0)
            # Verify organize_by_type was called
            # We need to check if the instance method was called.
            # MockOrganizer is the class, MockOrganizer.return_value is the instance.
            MockOrganizer.return_value.organize_by_type.assert_called_once()

            # Verify arguments passed to organize_by_type
            # Since Path is mocked, we need to be careful about what is passed.
            # The code does: source = Path(args.source), target = Path(args.target)
            # So it passes the return value of Path(str).
            # assert_called_with checks for equality.

            # Let's just verify it was called. detailed arg checking might be brittle due to Path mocking.

    @patch('src.file_manager.cli.FileOrganizer')
    @patch('src.file_manager.cli.Path')
    def test_organize_by_date(self, MockPath, MockOrganizer):
        MockPath.return_value.exists.return_value = True
        test_args = ['cli.py', 'organize', '--source', '/src', '--target', '/dst', '--by-date']
        with patch.object(sys, 'argv', test_args):
            ret = main()
            self.assertEqual(ret, 0)
            MockOrganizer.return_value.organize_by_date.assert_called_once()

    @patch('src.file_manager.cli.FileSearcher')
    @patch('src.file_manager.cli.Path')
    def test_search_by_name(self, MockPath, MockSearcher):
        MockPath.return_value.exists.return_value = True
        # Mock return value of search_by_name to be a list so len() works
        MockSearcher.return_value.search_by_name.return_value = []

        test_args = ['cli.py', 'search', '--dir', '/dir', '--name', '*.txt']
        with patch.object(sys, 'argv', test_args):
            ret = main()
            self.assertEqual(ret, 0)
            MockSearcher.return_value.search_by_name.assert_called_once()

    @patch('src.file_manager.cli.FileOrganizer')
    @patch('src.file_manager.cli.Path')
    def test_duplicates(self, MockPath, MockOrganizer):
        MockPath.return_value.exists.return_value = True
        MockOrganizer.return_value.find_duplicates.return_value = {}

        test_args = ['cli.py', 'duplicates', '--dir', '/dir']
        with patch.object(sys, 'argv', test_args):
            ret = main()
            self.assertEqual(ret, 0)
            MockOrganizer.return_value.find_duplicates.assert_called_once()

    @patch('src.file_manager.cli.FileOrganizer')
    @patch('src.file_manager.cli.Path')
    def test_cleanup(self, MockPath, MockOrganizer):
        MockPath.return_value.exists.return_value = True
        MockOrganizer.return_value.cleanup_old_files.return_value = []

        test_args = ['cli.py', 'cleanup', '--dir', '/dir', '--days', '30']
        with patch.object(sys, 'argv', test_args):
            ret = main()
            self.assertEqual(ret, 0)
            MockOrganizer.return_value.cleanup_old_files.assert_called_once()

    @patch('src.file_manager.cli.FileOrganizer')
    @patch('src.file_manager.cli.Path')
    def test_rename(self, MockPath, MockOrganizer):
        MockPath.return_value.exists.return_value = True
        MockOrganizer.return_value.batch_rename.return_value = []

        test_args = ['cli.py', 'rename', '--dir', '/dir', '--pattern', 'old', '--replacement', 'new']
        with patch.object(sys, 'argv', test_args):
            ret = main()
            self.assertEqual(ret, 0)
            MockOrganizer.return_value.batch_rename.assert_called_once()

    @patch('src.file_manager.cli.Path')
    def test_invalid_directory(self, MockPath):
        MockPath.return_value.exists.return_value = False
        test_args = ['cli.py', 'organize', '--source', '/src', '--target', '/dst', '--by-type']
        with patch.object(sys, 'argv', test_args):
            ret = main()
            self.assertEqual(ret, 1)

if __name__ == '__main__':
    unittest.main()
