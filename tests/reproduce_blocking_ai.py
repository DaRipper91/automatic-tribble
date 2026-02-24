
import pytest
import time
import asyncio
from textual.app import App, ComposeResult
from textual.widgets import Input
from src.file_manager.ai_mode import AIModeScreen
from src.file_manager.ai_integration import GeminiClient
from src.file_manager.screens import ConfirmationScreen

class SlowGeminiClient(GeminiClient):
    def execute_command(self, action_data):
        # simulate slow operation
        time.sleep(1.0)
        return "Done"

class MockApp(App):
    def compose(self) -> ComposeResult:
        screen = AIModeScreen()
        screen.gemini_client = SlowGeminiClient()
        yield screen

@pytest.mark.asyncio
async def test_non_blocking_behavior():
    app = MockApp()
    async with app.run_test() as pilot:
        screen = app.query_one(AIModeScreen)

        # Prepare the command execution
        screen.query_one("#command_input", Input).value = "organize files"
        screen.query_one("#target_dir_input", Input).value = "."

        # Trigger the process command directly
        screen._process_command()

        # Wait for the confirmation dialog to appear
        print("Waiting for ConfirmationScreen...")

        # Wait until top of stack is ConfirmationScreen AND it has children
        start_wait = time.time()
        while True:
            await asyncio.sleep(0.1)
            current_screen = app.screen
            if isinstance(current_screen, ConfirmationScreen):
                if len(current_screen.query("*")) > 0:
                    break

            if time.time() - start_wait > 5.0:
                 print(f"Current screen: {app.screen}")
                 print(f"Screen stack: {app.screen_stack}")
                 print(f"Widgets: {[w for w in app.screen.query('*')]}")
                 break

        assert isinstance(app.screen, ConfirmationScreen), "ConfirmationScreen did not appear"
        assert len(app.screen.query("*")) > 0, "ConfirmationScreen has no widgets"

        # The confirmation dialog is now active.

        start_time = time.time()

        # Click "Execute" in the ConfirmationScreen. ID is "confirm"
        await pilot.click("#confirm")

        end_time = time.time()
        duration = end_time - start_time

        print(f"Execution took {duration:.2f}s")

        # If non-blocking, duration should be small (e.g. < 0.2s)
        # The worker runs in background, so the click returns immediately.
        assert duration < 0.5, f"Expected non-blocking behavior (< 0.5s), got {duration:.2f}s"
