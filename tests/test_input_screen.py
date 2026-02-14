import pytest
from textual.app import App, ComposeResult
from textual.widgets import Label, Input, Button
from src.file_manager.screens import InputScreen

class HeadlessApp(App):
    def compose(self) -> ComposeResult:
        yield Label("Main")

@pytest.mark.asyncio
async def test_input_screen_composition():
    app = HeadlessApp()
    async with app.run_test() as pilot:
        screen = InputScreen("Test Title", "Test Prompt", "Initial")
        await app.push_screen(screen)

        # Check prompt
        prompt = screen.query_one("#message", Label)
        assert str(prompt.render()) == "Test Prompt"

        # Check input
        input_widget = screen.query_one(Input)
        assert input_widget.value == "Initial"
        assert input_widget.placeholder == "Enter value..."

        # Check buttons
        ok_btn = screen.query_one("#ok", Button)
        cancel_btn = screen.query_one("#cancel", Button)
        assert str(ok_btn.label) == "OK"
        assert str(cancel_btn.label) == "Cancel"

        # Test OK button
        input_widget.value = "New Value"
        await pilot.click("#ok")
        # After clicking OK, the screen should be dismissed with the value
        # But run_test context manager handles app shutdown, so we can't easily check the return value here directly
        # without mocking or using a different approach. However, we can check if the screen is dismissed.
        assert app.screen is not screen

@pytest.mark.asyncio
async def test_input_screen_cancel():
    app = HeadlessApp()
    result = None

    def handle_result(res):
        nonlocal result
        result = res

    async with app.run_test() as pilot:
        screen = InputScreen("Test Title", "Test Prompt")
        await app.push_screen(screen, handle_result)

        await pilot.click("#cancel")
        # In the new InputScreen, cancel returns empty string "", not None
        assert result == ""
        assert app.screen is not screen

@pytest.mark.asyncio
async def test_input_screen_submit():
    app = HeadlessApp()
    result = None

    def handle_result(res):
        nonlocal result
        result = res

    async with app.run_test() as pilot:
        screen = InputScreen("Test Title", "Test Prompt")
        await app.push_screen(screen, handle_result)

        input_widget = screen.query_one(Input)
        input_widget.value = "Test Dir"
        await pilot.press("enter")

        assert result == "Test Dir"
        assert app.screen is not screen

@pytest.mark.asyncio
async def test_input_screen_escape():
    app = HeadlessApp()
    result = None

    def handle_result(res):
        nonlocal result
        result = res

    async with app.run_test() as pilot:
        screen = InputScreen("Title", "Prompt")
        await app.push_screen(screen, handle_result)

        await pilot.press("escape")
        assert result == ""
        assert app.screen is not screen
