import unittest
from unittest.mock import patch
from src.file_manager.utils import find_gemini_executable, format_size

class TestFormatSize(unittest.TestCase):
    def test_format_size_zero(self):
        self.assertEqual(format_size(0), "0.0 B")

    def test_format_size_bytes(self):
        self.assertEqual(format_size(1023), "1023.0 B")

    def test_format_size_kilobytes(self):
        self.assertEqual(format_size(1024), "1.0 KB")

    def test_format_size_megabytes(self):
        self.assertEqual(format_size(1024**2), "1.0 MB")

    def test_format_size_gigabytes(self):
        self.assertEqual(format_size(1024**3), "1.0 GB")

    def test_format_size_terabytes(self):
        self.assertEqual(format_size(1024**4), "1.0 TB")

    def test_format_size_petabytes(self):
        self.assertEqual(format_size(1024**5), "1.0 PB")

    def test_format_size_exceeding_petabytes(self):
        self.assertEqual(format_size(1024**6), "1024.0 PB")

class TestFindGeminiExecutable(unittest.TestCase):
    @patch('src.file_manager.utils.shutil.which')
    def test_find_gemini_standard(self, mock_which):
        """Test finding 'gemini' executable."""
        # Setup mock to return a path only for 'gemini'
        def side_effect(arg):
            if arg == "gemini":
                return "/usr/bin/gemini"
            return None

        mock_which.side_effect = side_effect

        result = find_gemini_executable()
        self.assertEqual(result, "/usr/bin/gemini")
        # Ensure it was called with 'gemini'
        mock_which.assert_any_call("gemini")

    @patch('src.file_manager.utils.shutil.which')
    def test_find_gemini_termux(self, mock_which):
        """Test finding 'gemini-cli-termux' executable."""
        # Setup mock to return None for 'gemini' but a path for 'gemini-cli-termux'
        def side_effect(arg):
            if arg == "gemini":
                return None
            if arg == "gemini-cli-termux":
                return "/data/data/com.termux/files/usr/bin/gemini-cli-termux"
            return None

        mock_which.side_effect = side_effect

        result = find_gemini_executable()
        self.assertEqual(result, "/data/data/com.termux/files/usr/bin/gemini-cli-termux")
        # Ensure it was called for both
        mock_which.assert_any_call("gemini")
        mock_which.assert_any_call("gemini-cli-termux")

    @patch('src.file_manager.utils.shutil.which')
    def test_find_gemini_none(self, mock_which):
        """Test when no executable is found."""
        mock_which.return_value = None

        result = find_gemini_executable()
        self.assertIsNone(result)
        # Ensure it tried both
        mock_which.assert_any_call("gemini")
        mock_which.assert_any_call("gemini-cli-termux")

if __name__ == '__main__':
    unittest.main()
