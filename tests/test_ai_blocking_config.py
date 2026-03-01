
import pytest
import time
import asyncio
from textual.app import App, ComposeResult
from textual.widgets import Input
from src.file_manager.screens import AIConfigScreen
from src.file_manager.ai_utils import AIExecutor

class SlowAIExecutor(AIExecutor):
    def generate_automation_command(self, user_request):
        # simulate slow operation
        time.sleep(2.0)
        return "tfm-auto organize", "Success"

    def is_available(self):
        return True

class MockApp(App):
    def compose(self) -> ComposeResult:
        screen = AIConfigScreen()
        screen.ai = SlowAIExecutor()
        yield screen

@pytest.mark.asyncio
async def test_non_blocking_behavior():
    app = MockApp()
    async with app.run_test() as pilot:
        screen = app.query_one(AIConfigScreen)
        input_widget = screen.query_one(Input)

        input_widget.value = "organize files"

        # Start a task that submits the input
        # This will trigger on_input_submitted which starts a background worker
        submission_task = asyncio.create_task(pilot.press("enter"))

        # Wait a bit for the submission to start
        await asyncio.sleep(0.5)

        # Now try to interact with something else.
        # If it's non-blocking, this should return quickly.
        start_time = time.time()
        await pilot.press("tab") # Try to navigate
        end_time = time.time()

        duration = end_time - start_time
        print(f"UI interaction took {duration:.2f}s")

        # If non-blocking, duration will be very small (e.g., < 0.1s)
        assert duration < 0.5, f"Expected non-blocking behavior, but UI was blocked (took {duration:.2f}s)"

        await submission_task
