"""
Tests for UI features.
"""
import pytest
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch

from textual.widgets import DirectoryTree, Label
from textual.app import App, ComposeResult
from src.file_manager.ui_components import MultiSelectDirectoryTree, FilePreview, EnhancedStatusBar
from src.file_manager.user_mode import UserModeScreen
from src.file_manager.help_overlay import HelpOverlay

# Helper App for mounting widgets
class TestApp(App):
    def compose(self) -> ComposeResult:
        yield Label("Test App")

@pytest.mark.asyncio
async def test_multi_select_directory_tree_selection():
    """Test selection logic in MultiSelectDirectoryTree."""
    async with TestApp().run_test() as pilot:
        tree = MultiSelectDirectoryTree("/")
        await pilot.app.mount(tree)

        # Mock cursor node
        mock_node = MagicMock()
        mock_node.data = MagicMock()
        mock_node.data.path = Path("/tmp/file1")
        mock_node.label = "file1"

        with patch.object(MultiSelectDirectoryTree, 'cursor_node', new_callable=MagicMock) as mock_cursor_prop:
            mock_cursor_prop.__get__ = MagicMock(return_value=mock_node)
            tree.refresh = MagicMock()

            # Toggle selection
            tree.action_toggle_selection()
            assert Path("/tmp/file1") in tree.selected_paths

            # Toggle again (deselect)
            tree.action_toggle_selection()
            assert Path("/tmp/file1") not in tree.selected_paths

@pytest.mark.asyncio
async def test_file_preview_update():
    """Test FilePreview widget content update."""
    async with TestApp().run_test() as pilot:
        preview = FilePreview()
        await pilot.app.mount(preview)

        # Simulate content update
        preview.update_content("Test Content", "metadata")

        # Check child widget text
        content_view = preview.query_one("#content-view")
        # Use render() to get text representation
        assert "Test Content" in str(content_view.render())
        assert "metadata" in content_view.classes

@pytest.mark.asyncio
async def test_status_bar_updates():
    """Test EnhancedStatusBar reactive properties."""
    async with TestApp().run_test() as pilot:
        bar = EnhancedStatusBar()
        await pilot.app.mount(bar)

        # Default state
        assert bar.selection_count == 0

        # Update properties
        bar.selection_count = 5
        bar.selection_size = 1024

        # Wait for reactive events
        await pilot.pause()

        # Verify label update by checking child widget text
        label = bar.query_one("#selection-info", Label)
        assert "Selected: 5" in str(label.render())

@pytest.mark.asyncio
async def test_help_overlay_search():
    """Test HelpOverlay search filtering."""
    async with TestApp().run_test() as pilot:
        overlay = HelpOverlay()
        await pilot.app.mount(overlay)

        # Wait for on_mount
        await pilot.pause()

        # Test search
        overlay.refresh_shortcuts("copy")

        # Verify container has children
        container = overlay.query_one("#categories-container")
        assert len(container.children) > 0
