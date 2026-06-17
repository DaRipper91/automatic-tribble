import pytest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path
from src.file_manager.app import FileManagerApp

@pytest.fixture
def mock_config_manager():
    with patch("src.file_manager.app.ConfigManager") as mock:
        instance = mock.return_value
        instance.get_theme.return_value = "dark"
        yield instance

@pytest.mark.asyncio
async def test_load_theme_by_name_success(mock_config_manager):
    """Test that a valid theme is loaded correctly."""
    # We establish mocks BEFORE instantiating the app to be safer,
    # though in this specific test we call load_theme_by_name manually.
    with patch("src.file_manager.app.Path.exists", return_value=True), \
         patch("src.file_manager.app.open", mock_open(read_data="/* CSS */")):

        app = FileManagerApp()
        async with app.run_test() as pilot:
            with patch.object(app.stylesheet, "add_source") as mock_add_source, \
                 patch.object(app, "refresh_css") as mock_refresh_css:

                app.load_theme_by_name("valid_theme")

                mock_add_source.assert_called_once_with("/* CSS */", is_default_css=False)
                mock_refresh_css.assert_called_once()

@pytest.mark.asyncio
async def test_load_theme_by_name_file_not_found(mock_config_manager):
    """Test that an error is logged when the theme file does not exist."""
    app = FileManagerApp()
    async with app.run_test() as pilot:
        with patch("textual.Logger.__call__") as mock_log:
            with patch("src.file_manager.app.Path.exists", return_value=False):
                app.load_theme_by_name("invalid_theme")

            mock_log.assert_called()
            # Check the log message
            log_message = mock_log.call_args[0][0]
            assert "Failed to load theme invalid_theme" in log_message
            assert "Theme file not found" in log_message

@pytest.mark.asyncio
async def test_load_theme_by_name_exception(mock_config_manager):
    """Test that general exceptions during theme loading are caught and logged."""
    app = FileManagerApp()
    async with app.run_test() as pilot:
        with patch("src.file_manager.app.Path.exists", return_value=True), \
             patch("src.file_manager.app.open", side_effect=OSError("Read error")), \
             patch("textual.Logger.__call__") as mock_log:

            app.load_theme_by_name("error_theme")

            mock_log.assert_called()
            log_message = mock_log.call_args[0][0]
            assert "Failed to load theme error_theme" in log_message
            assert "Read error" in log_message

@pytest.mark.asyncio
async def test_load_configured_theme_calls_load_theme_by_name(mock_config_manager):
    """Test that load_configured_theme calls load_theme_by_name with the correct theme."""
    mock_config_manager.get_theme.return_value = "custom_theme"
    app = FileManagerApp()
    async with app.run_test() as pilot:
        with patch.object(app, "load_theme_by_name") as mock_load_theme:
            app.load_configured_theme()
            mock_load_theme.assert_called_once_with("custom_theme")
