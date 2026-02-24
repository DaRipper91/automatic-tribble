"""
AI Mode Screen - Automation Interface
"""

import json
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
from .screens import ConfirmationScreen


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
        Binding("up", "history_up", "History Up"),
        Binding("down", "history_down", "History Down"),
    ]

    def __init__(self):
        super().__init__()
        self.gemini_client = GeminiClient()
        self.current_dir = Path.cwd()
        self.current_plan = None
        self.history_file = Path.home() / ".tfm" / "command_history.json"
        self.history: List[Dict[str, Any]] = self._load_history()
        self.history_index = -1

    def _load_history(self) -> List[Dict[str, Any]]:
        """Load command history from file."""
        if not self.history_file.exists():
            return []
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except Exception:
            return []

    def _save_history(self, command: str, plan: Dict[str, Any], status: str) -> None:
        """Save executed command to history."""
        # Clean plan (remove objects if any, keep JSON serializable)
        entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "plan_summary": plan.get("summary", ""),
            "status": status
        }
        self.history.insert(0, entry) # Prepend
        if len(self.history) > 100:
            self.history = self.history[:100]

        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception:
            pass

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
                    yield Button("Search History", id="btn_search_history", classes="action-btn")

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
        if self.history:
            log.write(f"[dim]Loaded {len(self.history)} past commands.[/]")

    def action_back_to_menu(self) -> None:
        """Return to the main menu."""
        self.app.pop_screen()

    def action_history_up(self) -> None:
        """Navigate history up."""
        if not self.history:
            return

        # history[0] is most recent
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            command = self.history[self.history_index]["command"]
            input_widget = self.query_one("#command_input", Input)
            input_widget.value = command
            input_widget.cursor_position = len(command)

    def action_history_down(self) -> None:
        """Navigate history down."""
        input_widget = self.query_one("#command_input", Input)

        if self.history_index > 0:
            self.history_index -= 1
            command = self.history[self.history_index]["command"]
            input_widget.value = command
            input_widget.cursor_position = len(command)
        elif self.history_index == 0:
            self.history_index = -1
            input_widget.value = ""

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
        elif btn_id == "btn_search_history":
            # Simple implementation: dump history to log for now
            self._search_history_dialog()

    def _search_history_dialog(self):
        """Show history search dialog (simulated via log for now)."""
        log = self.query_one("#output_log", RichLog)
        log.write("\n[bold]Command History:[/bold]")
        for i, entry in enumerate(self.history[:10]):
            log.write(f"{i+1}. {entry['command']} [dim]({entry['timestamp']})[/]")
        log.write("[dim]... (Use Up/Down arrows to cycle)[/]")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission (Enter key)."""
        if event.input.id == "command_input":
            self._process_command()

    def _log_message(self, message: str) -> None:
        """Helper to log messages from threads safely."""
        log = self.query_one("#output_log", RichLog)
        log.write(message)

    @work(thread=True)
    def _process_plan_worker(self, command_text: str, target_path: Path) -> None:
        """Process the command and generate a plan in a thread."""
        self.app.call_from_thread(self._log_message, f"\n[bold blue]Processing command:[/] {command_text}")
        self.app.call_from_thread(self._log_message, "[dim]Asking Gemini...[/]")

        plan_data = self.gemini_client.process_command(command_text, target_path)

        self.current_plan = plan_data

        if not plan_data.get("plan"):
            self.app.call_from_thread(self._log_message, f"[bold red]AI:[/ bold red] {plan_data.get('summary', 'Failed to generate plan.')}")
            if plan_data.get("description"):
                self.app.call_from_thread(self._log_message, f"[red]{plan_data['description']}[/]")
            return

        # Display Plan
        self.app.call_from_thread(self._display_plan, plan_data)

        # Ask for confirmation
        self.app.call_from_thread(self._request_confirmation, plan_data)

    def _display_plan(self, plan_data: dict) -> None:
        """Display the plan in the log."""
        log = self.query_one("#output_log", RichLog)
        log.write("\n[bold purple]=== AI Execution Plan ===[/]")
        log.write(f"[bold]Summary:[/bold] {plan_data.get('summary', 'No summary')}")
        log.write(f"[bold]Confidence:[/bold] {plan_data.get('confidence', 0.0)}")
        log.write("")

        for idx, step in enumerate(plan_data["plan"]):
            icon = "🛑" if step.get("is_destructive") else "🔹"
            log.write(f"{idx + 1}. {icon} [bold]{step['action']}[/]: {step['description']}")
            if step.get("is_destructive"):
                 log.write("   [red]Warning: Destructive Action[/]")

        log.write("\n[dim]Waiting for confirmation...[/]")

    def _request_confirmation(self, plan_data: dict) -> None:
        """Request user confirmation."""
        def check_confirm(confirmed: bool) -> None:
            if confirmed:
                self._execute_plan_worker(plan_data)
            else:
                self._log_message("[yellow]Plan execution cancelled.[/]")
                # Save as cancelled
                command_text = self.query_one("#command_input", Input).value
                self._save_history(command_text, plan_data, "cancelled")

        self.app.push_screen(
            ConfirmationScreen(
                f"Execute {len(plan_data['plan'])} steps?\n(See log for details)",
                confirm_label="Execute Plan",
                confirm_variant="success"
            ),
            check_confirm
        )

    @work
    async def _execute_plan_worker(self, plan_data: dict) -> None:
        """Execute the plan sequentially."""
        self._log_message("\n[bold green]=== Executing Plan ===[/]")

        success_count = 0
        total_steps = len(plan_data["plan"])

        for idx, step in enumerate(plan_data["plan"]):
            self._log_message(f"Step {idx + 1}/{total_steps}: {step['description']}...")

            try:
                result = await self.gemini_client.execute_step(step)
                self._log_message(f"  ✅ {result}")
                success_count += 1
            except Exception as e:
                self._log_message(f"  ❌ Error: {e}")
                self._log_message("[red]Execution halted due to error.[/]")

                # Save partial history
                command_text = self.query_one("#command_input", Input).value
                self._save_history(command_text, plan_data, "failed")
                return

        self._log_message(f"\n[bold green]Execution Complete. {success_count}/{total_steps} steps successful.[/]")

        # Save history
        command_text = self.query_one("#command_input", Input).value
        self._save_history(command_text, plan_data, "completed")
        self.history_index = -1

    def _process_command(self) -> None:
        """Initiate command processing."""
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

        self._process_plan_worker(command_text, target_path)
