import pytest
from textual.app import App, ComposeResult
from src.file_manager.screens import HelpScreen, InputScreen, ConfirmationScreen
from textual.widgets import Label, Button, Input

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

@pytest.mark.asyncio
async def test_input_screen_composition():
    app = HeadlessApp()
    async with app.run_test() as pilot:
        screen = InputScreen("Test Title", "Test Message", initial_value="initial")
        await app.push_screen(screen)

        # Check for title and message
        assert str(screen.query_one(".title", Label).render()) == "Test Title"
        assert str(screen.query_one("#message", Label).render()) == "Test Message"

        # Check for input
        input_widget = screen.query_one(Input)
        assert input_widget.value == "initial"

        # Test OK button
        input_widget.value = "new_value"
        # We need to capture the result of the screen
        # Since push_screen is used with a callback usually, we can check dismiss value if we had a way.
        # But here we just want to see if it dismisses with the right value.

        # We can mock dismiss or just check if it's called.
        # In textual 0.30+, we can await push_screen if it's not a callback.
        # But app.py uses callbacks.

        await pilot.click("#ok")
        assert app.screen is not screen

@pytest.mark.asyncio
async def test_input_screen_cancel():
    app = HeadlessApp()
    async with app.run_test() as pilot:
        screen = InputScreen("Title", "Msg")
        await app.push_screen(screen)

        await pilot.click("#cancel")
        assert app.screen is not screen

@pytest.mark.asyncio
async def test_input_screen_submit():
    app = HeadlessApp()
    async with app.run_test() as pilot:
        screen = InputScreen("Title", "Msg")
        await app.push_screen(screen)

        input_widget = screen.query_one(Input)
        input_widget.value = "submitted"
        await pilot.press("enter")
        assert app.screen is not screen

@pytest.mark.asyncio
async def test_confirmation_screen_custom_labels():
    app = HeadlessApp()
    async with app.run_test() as pilot:
        screen = ConfirmationScreen("Confirm Action?", confirm_label="Execute", confirm_variant="success")
        await app.push_screen(screen)

        # Check message
        assert str(screen.query_one("#question", Label).render()) == "Confirm Action?"

        # Check buttons

@pytest.mark.asyncio
async def test_confirmation_screen_default():
    app = HeadlessApp()
    async with app.run_test() as pilot:
        screen = ConfirmationScreen("Are you sure?")
        await app.push_screen(screen)

        confirm_btn = screen.query_one("#confirm", Button)
        assert str(confirm_btn.label) == "Delete"
        assert confirm_btn.variant == "error"

@pytest.mark.asyncio
async def test_confirmation_screen_custom():
    app = HeadlessApp()
    async with app.run_test() as pilot:
        screen = ConfirmationScreen("Execute?", confirm_label="Execute", confirm_variant="success")
        await app.push_screen(screen)

        confirm_btn = screen.query_one("#confirm", Button)
        assert str(confirm_btn.label) == "Execute"
        assert confirm_btn.variant == "success"

        cancel_btn = screen.query_one("#cancel", Button)
        assert str(cancel_btn.label) == "Cancel"
        assert cancel_btn.variant == "primary"

        # Test confirm
        await pilot.click("#confirm")

@pytest.mark.asyncio
async def test_confirmation_screen_escape():
    app = HeadlessApp()
    result = None

    def handle_result(res):
        nonlocal result
        result = res

    async with app.run_test() as pilot:
        screen = ConfirmationScreen("Are you sure?")
        await app.push_screen(screen, handle_result)

        await pilot.press("escape")
        assert result is False
        assert app.screen is not screen
