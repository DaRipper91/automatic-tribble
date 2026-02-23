"""
AI Mode Screen - Automation Interface
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Button, Label, Input, RichLog
from textual.screen import Screen
from textual.binding import Binding
from textual import work

from .ai_integration import GeminiClient
from .screens import ConfirmationScreen, InputScreen


class CommandHistoryManager:
    """Manages command history persistence."""

    def __init__(self):
        self.history_file = Path.home() / ".tfm" / "command_history.json"
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.history: List[Dict[str, Any]] = self._load_history()

    def _load_history(self) -> List[Dict[str, Any]]:
        if not self.history_file.exists():
            return []
        try:
            with open(self.history_file, "r") as f:
                return json.load(f)
        except Exception:
            return []

    def add_entry(self, command: str, plan: Dict[str, Any], status: str):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "plan": plan,
            "status": status
        }
        self.history.insert(0, entry) # Newest first
        # Limit to 100 entries
        self.history = self.history[:100]
        self._save_history()

    def _save_history(self):
        try:
            with open(self.history_file, "w") as f:
                json.dump(self.history, f, indent=2)
        except Exception:
            pass

    def get_recent_commands(self) -> List[str]:
        return [entry["command"] for entry in self.history]


class AIModeScreen(Screen):
    """Screen for AI-driven file automation."""

    CSS = """
    AIModeScreen {
        background: $surface;
    }

    #main-container {
        padding: 1;
        height: 100%;
    }

    #left-panel {
        width: 30%;
        height: 100%;
        border-right: solid $primary;
        padding-right: 1;
    }

    #right-panel {
        width: 70%;
        height: 100%;
        padding-left: 1;
    }

    .action-btn {
        width: 100%;
        margin-bottom: 1;
    }

    #output-log {
        height: 1fr;
        border: solid $secondary;
        margin-top: 1;
        background: $panel;
    }

    .section-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #input-container {
        height: auto;
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "back_to_menu", "Back to Menu", priority=True),
        Binding("up", "history_up", "History Up", show=False),
        Binding("down", "history_down", "History Down", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.gemini_client = GeminiClient()
        self.current_dir = Path.cwd()
        self.history_manager = CommandHistoryManager()
        self.history_index = -1
        self.current_plan: Dict[str, Any] = {}

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="main-container"):
            with Horizontal():
                # Left Panel: Quick Actions
                with Vertical(id="left-panel"):
                    yield Label("Quick Actions", classes="section-title")
                    yield Button("Organize by Type", id="btn_org_type", classes="action-btn")
                    yield Button("Organize by Date", id="btn_org_date", classes="action-btn")
                    yield Button("Cleanup Old Files", id="btn_cleanup", classes="action-btn")
                    yield Button("Find Duplicates", id="btn_duplicates", classes="action-btn")
                    yield Button("Batch Rename", id="btn_rename", classes="action-btn")
                    yield Label("History", classes="section-title")
                    yield Button("Search History", id="btn_history_search", classes="action-btn")

                # Right Panel: Interaction
                with Vertical(id="right-panel"):
                    yield Label("Target Directory:", classes="section-title")
                    yield Input(str(self.current_dir), id="target_dir_input")

                    yield Label("AI Command:", classes="section-title")
                    with Horizontal(id="input-container"):
                        yield Input(placeholder="Describe what you want to do...", id="command_input", classes="command-input")
                        yield Button("Process", id="process_btn", variant="primary")

                    yield Label("Output Log:", classes="section-title")
                    yield RichLog(id="output_log", wrap=True, highlight=True, markup=True)

        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        self.query_one("#command_input").focus()
        log = self.query_one("#output_log", RichLog)
        log.write("[bold green]AI Automation Mode Ready.[/]")
        log.write("Select a Quick Action or type a command.")

    def action_back_to_menu(self) -> None:
        """Return to the main menu."""
        self.app.pop_screen()

    def action_history_up(self) -> None:
        """Cycle history up."""
        commands = self.history_manager.get_recent_commands()
        if not commands:
            return

        if self.history_index < len(commands) - 1:
            self.history_index += 1
            input_widget = self.query_one("#command_input", Input)
            input_widget.value = commands[self.history_index]

    def action_history_down(self) -> None:
        """Cycle history down."""
        if self.history_index > -1:
            self.history_index -= 1
            input_widget = self.query_one("#command_input", Input)
            if self.history_index == -1:
                input_widget.value = ""
            else:
                commands = self.history_manager.get_recent_commands()
                input_widget.value = commands[self.history_index]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        btn_id = event.button.id
        command_input = self.query_one("#command_input", Input)

        if btn_id == "process_btn":
            self._process_command()
        elif btn_id == "btn_org_type":
            command_input.value = "Organize files by type"
            command_input.focus()
        elif btn_id == "btn_org_date":
            command_input.value = "Organize files by date"
            command_input.focus()
        elif btn_id == "btn_cleanup":
            command_input.value = "Cleanup files older than 30 days"
            command_input.focus()
        elif btn_id == "btn_duplicates":
            command_input.value = "Find duplicate files"
            command_input.focus()
        elif btn_id == "btn_rename":
            command_input.value = "Rename files matching 'pattern' to 'replacement'"
            command_input.focus()
        elif btn_id == "btn_history_search":
            self._show_history_search()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission (Enter key)."""
        if event.input.id == "command_input":
            self._process_command()

    def _log_message(self, message: str) -> None:
        """Helper to log messages from threads safely."""
        log = self.query_one("#output_log", RichLog)
        log.write(message)

    @work(thread=True)
    def _execute_plan_worker(self, plan_data: Dict[str, Any]) -> None:
        """Execute the plan in a worker thread."""
        self.app.call_from_thread(self._log_message, "\n[bold blue]Executing Plan...[/]")

        steps = plan_data.get("plan", [])
        success = True

        for i, step in enumerate(steps, 1):
            desc = step.get("description", "Unknown Step")
            self.app.call_from_thread(self._log_message, f"[dim]Step {i}/{len(steps)}: {desc}[/]")

            result = self.gemini_client.execute_step(step)

            if result.startswith("Error"):
                self.app.call_from_thread(self._log_message, f"[bold red]FAILED:[/ bold red] {result}")
                success = False
                break # Stop on error? or continue? Usually stop.
            else:
                self.app.call_from_thread(self._log_message, f"[bold green]OK:[/ bold green] {result}")

        if success:
            self.app.call_from_thread(self._log_message, "[bold green]All steps completed successfully.[/]")
            self.app.call_from_thread(self.history_manager.add_entry, self.query_one("#command_input", Input).value, plan_data, "success")
        else:
             self.app.call_from_thread(self.history_manager.add_entry, self.query_one("#command_input", Input).value, plan_data, "failed")

    def _process_command(self) -> None:
        """Process the current command."""
        command_input = self.query_one("#command_input", Input)
        target_dir_input = self.query_one("#target_dir_input", Input)
        log = self.query_one("#output_log", RichLog)

        command_text = command_input.value.strip()
        if not command_text:
            log.write("[bold red]Error:[/ bold red] Please enter a command.")
            return

        target_path_str = target_dir_input.value.strip()
        target_path = Path(target_path_str)

        if not target_path.exists():
            log.write(f"[bold red]Error:[/ bold red] Directory not found: {target_path}")
            return

        log.write(f"\n[bold blue]Processing command:[/] {command_text}")
        log.write(f"[dim]Context: {target_path}[/]")

        # Generate Plan
        plan_data = self.gemini_client.get_plan(command_text, target_path)

        # Check for error in plan generation
        if not plan_data or "plan" not in plan_data:
             log.write("[bold red]Error:[/ bold red] Failed to generate plan.")
             return

        first_step = plan_data["plan"][0]
        if first_step.get("action") == "error":
             log.write(f"[bold red]AI Error:[/ bold red] {first_step.get('description')}")
             return

        self.current_plan = plan_data

        # Display Plan (Dry Run)
        log.write(f"\n[bold purple]Proposed Plan ({len(plan_data['plan'])} steps):[/]")
        for i, step in enumerate(plan_data["plan"], 1):
            color = "red" if step.get("is_destructive") else "green"
            icon = "⚠️" if step.get("is_destructive") else "ℹ️"
            log.write(f"{i}. [{color}]{icon} {step.get('description')}[/]")
            # log.write(f"   [dim]{step.get('action')} {step.get('params')}[/]") # Optional detailed view

        # Confirmation
        def check_confirm(confirmed: bool) -> None:
            if confirmed:
                self._execute_plan_worker(plan_data)
            else:
                log.write("[yellow]Plan cancelled.[/]")
                self.history_manager.add_entry(command_text, plan_data, "cancelled")

        self.app.push_screen(
            ConfirmationScreen(
                f"Execute {len(plan_data['plan'])} steps?",
                confirm_label="Confirm & Execute",
                confirm_variant="success"
            ),
            check_confirm
        )

    def _show_history_search(self):
        """Show history search dialog."""
        def do_search(query: str) -> None:
            if not query:
                return
            self._perform_history_search(query)

        self.app.push_screen(
            InputScreen("Search History", "Enter search query:"),
            do_search
        )

    @work(thread=True)
    def _perform_history_search(self, query: str) -> None:
        """Perform search in background."""
        log = self.query_one("#output_log", RichLog)
        commands = self.history_manager.get_recent_commands()

        self.app.call_from_thread(log.write, f"\n[bold blue]Searching history for:[/] '{query}'...")

        matches = self.gemini_client.search_history(query, commands)

        if matches:
            self.app.call_from_thread(log.write, "[bold green]Found matches:[/]")
            for match in matches:
                self.app.call_from_thread(log.write, f"- {match}")
        else:
            self.app.call_from_thread(log.write, "[yellow]No matching commands found.[/]")
