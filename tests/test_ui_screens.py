import pytest
from textual.app import App, ComposeResult
from src.file_manager.screens import HelpScreen
from textual.widgets import Label, Button

class HeadlessApp(App):
    def compose(self) -> ComposeResult:
        yield Label("Main")

@pytest.mark.asyncio
async def test_help_screen_composition():
    app = HeadlessApp()
    async with app.run_test() as pilot:
        screen = HelpScreen()
        await app.push_screen(screen)

        # Check for title
        title = screen.query_one(".title", Label)
        assert str(title.render()) == "Keyboard Shortcuts"

        # Check for close button
        close_btn = screen.query_one("#close-button", Button)
        assert str(close_btn.label) == "Close"

        # Check for some shortcuts
        keys = screen.query(".key")
        assert len(keys) > 0
        key_texts = [str(k.render()) for k in keys]
        assert "Tab" in key_texts
        assert "q" in key_texts

        # Test closing
        await pilot.click("#close-button")
        # After closing, the screen should be popped.
        # app.screen should be the main screen (which is not 'screen')
        assert app.screen is not screen
