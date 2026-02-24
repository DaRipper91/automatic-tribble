import sys
import os
import unittest
from unittest.mock import MagicMock, patch, AsyncMock

# Ensure the installer directory is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../installer')))

try:
    from installer import InstallScreen
    from textual.app import App
except ImportError:
    pass

class TestInstaller(unittest.IsolatedAsyncioTestCase):
    async def test_run_install_calls_write(self):
        """
        Verify that run_install calls log.write() and not log.write_line().
        """
        # Subclass to mock app property
        class MockInstallScreen(InstallScreen):
            @property
            def app(self):
                return self._mock_app

        screen = MockInstallScreen()
        screen._mock_app = MagicMock()
        screen._mock_app.env = "TestEnv"

        # Mock the log widget
        mock_log = MagicMock()
        # Ensure write is available
        mock_log.write = MagicMock()

        # Mock query_one to return our mock_log
        screen.query_one = MagicMock(return_value=mock_log)

        # Mock asyncio.create_subprocess_shell
        # We need to simulate stdout/stderr
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"Success output", b"")
        mock_proc.return_value = 0

        with patch('asyncio.create_subprocess_shell', return_value=mock_proc) as mock_shell:
            await screen.run_install()

            # Verify that write was called
            self.assertTrue(mock_log.write.called, "log.write() should have been called")

            # Verify expected calls
            calls = mock_log.write.call_args_list
            # Check content of calls
            # First call should be "Starting installation..."
            self.assertIn("Starting installation", calls[0][0][0])

            # Check subprocess calls
            # It should call pip install -r requirements.txt
            # And pip install .
            self.assertGreaterEqual(mock_shell.call_count, 2)

            # Verify args passed to shell
            # args[0] is cmd
            cmds = [call.args[0] for call in mock_shell.call_args_list]
            self.assertTrue(any("pip install -r requirements.txt" in cmd for cmd in cmds))
            self.assertTrue(any("pip install ." in cmd for cmd in cmds))

if __name__ == '__main__':
    unittest.main()
