import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.file_manager.ai_mode import AIModeScreen
from textual.app import App
from textual.widgets import Input, RichLog, Checkbox

class MockApp(App):
    def compose(self):
        yield AIModeScreen()

@pytest.mark.asyncio
async def test_ai_pipeline_e2e_plan_execution(tmp_path):
    # Setup mock files
    source_dir = tmp_path / "source"
    target_dir = tmp_path / "target"
    source_dir.mkdir()
    target_dir.mkdir()
    (source_dir / "test1.txt").touch()

    # Mock the AI Response
    mock_plan = {
        "plan": [
            {
                "step": 1,
                "action": "organize_by_type",
                "source": str(source_dir),
                "target": str(target_dir),
                "move": True,
                "description": "Organize text files",
                "is_destructive": False
            }
        ]
    }

    # Patch the GeminiClient executor
    with patch("src.file_manager.ai_integration.AIExecutor") as mock_executor_cls:
        mock_executor = mock_executor_cls.return_value
        mock_executor.is_available.return_value = True
        mock_executor.execute_prompt.return_value = json.dumps(mock_plan)

        app = MockApp()
        async with app.run_test() as pilot:
            # app.screen is the Screen, which in this case is AIModeScreen but Textual might wrap it
            # We fetch the exact AIModeScreen instance
            screen = app.query_one(AIModeScreen)
            screen.gemini_client.context_builder.get_context = MagicMock(return_value={})

            # Setup input fields
            target_input = screen.query_one("#target_dir_input", Input)
            target_input.value = str(tmp_path)

            cmd_input = screen.query_one("#command_input", Input)
            cmd_input.value = "Organize my text files"

            dry_run = screen.query_one("#dry_run_checkbox", Checkbox)
            dry_run.value = False # Disable dry run for real execution

            # Wait for any prior events, then trigger worker directly to bypass async/thread test quirks
            await pilot.pause(0.1)
            screen._generate_plan_worker(cmd_input.value, Path(target_input.value), dry_run.value)
            await pilot.pause(2.0)

            # Ensure execution triggered organizer
            assert len(screen.current_plan) > 0
            assert screen.current_plan[0]["action"] == "organize_by_type"

@pytest.mark.asyncio
async def test_ai_pipeline_e2e_validation_fallback(tmp_path):
    # Test fallback text on complete failure
    with patch("src.file_manager.ai_integration.AIExecutor") as mock_executor_cls:
        mock_executor = mock_executor_cls.return_value
        mock_executor.is_available.return_value = True
        mock_executor.execute_prompt.return_value = "I am a helpful assistant but I refuse to use JSON!"

        app = MockApp()
        async with app.run_test() as pilot:
            screen = app.query_one(AIModeScreen)
            screen.gemini_client.context_builder.get_context = MagicMock(return_value={})

            target_input = screen.query_one("#target_dir_input", Input)
            target_input.value = str(tmp_path)

            cmd_input = screen.query_one("#command_input", Input)
            cmd_input.value = "Do something bad"

            await pilot.pause(0.1)
            screen._generate_plan_worker(cmd_input.value, Path(target_input.value), True)
            await pilot.pause(2.0)

            # Verify plan is empty and fallback logic triggered
            log_widget = screen.query_one("#output_log", RichLog)
            log_text = "\n".join([str(line) for line in log_widget.lines])

            assert "AI could not generate a valid plan after retries" in log_text
            assert "I am a helpful assistant but I refuse to use JSON!" in log_text
