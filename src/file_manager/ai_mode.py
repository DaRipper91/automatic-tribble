"""
AI Mode Screen - Automation Interface
"""

import asyncio
import json
import time
from typing import Optional, Dict, Any, List
from pathlib import Path
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
        Binding("up", "history_up", "Previous Command"),
        Binding("down", "history_down", "Next Command"),
    ]

    def __init__(self):
        super().__init__()
        self.gemini_client = GeminiClient()
        self.current_dir = Path.cwd()
        self.current_plan: List[Dict[str, Any]] = []
        self.history: List[Dict[str, Any]] = self._load_history()
        self.history_index = -1

    def _load_history(self) -> List[Dict[str, Any]]:
        path = Path.home() / ".tfm" / "command_history.json"
        if path.exists():
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_history_entry(self, command: str, plan: List[Dict[str, Any]], status: str):
        entry = {
            "timestamp": time.time(),
            "command": command,
            "plan": plan,
            "status": status
        }
        self.history.append(entry)
        path = Path.home() / ".tfm" / "command_history.json"
        try:
            with open(path, "w") as f:
                json.dump(self.history, f, indent=2)
        except Exception:
            pass

    def action_history_up(self):
        if not self.history:
            return
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            cmd = self.history[-(self.history_index+1)]["command"]
            self.query_one("#command_input", Input).value = cmd

    def action_history_down(self):
        if self.history_index > 0:
            self.history_index -= 1
            cmd = self.history[-(self.history_index+1)]["command"]
            self.query_one("#command_input", Input).value = cmd
        elif self.history_index == 0:
            self.history_index = -1
            self.query_one("#command_input", Input).value = ""

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

                # Right Panel: Interaction
                with Vertical(id="right-panel"):
                    yield Label("Target Directory:", classes="section-title")
                    yield Input(str(self.current_dir), id="target_dir_input")

                    yield Label("AI Command:", classes="section-title")
                    with Horizontal(id="input-container"):
                        yield Input(placeholder="Describe what you want to do...", id="command_input", classes="command-input")
                        yield Button("Process", id="process_btn", variant="primary")

                    with Horizontal(id="history-container"):
                         yield Button("Search History", id="history_btn", variant="default")
                         yield Button("Suggest Tags", id="suggest_tags_btn", variant="warning")

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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        btn_id = event.button.id
        command_input = self.query_one("#command_input", Input)

        if btn_id == "process_btn":
            self._process_command()
        elif btn_id == "history_btn":
            query = command_input.value.strip()
            self._search_history_worker(query)
        elif btn_id == "suggest_tags_btn":
            self._suggest_tags()
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

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission (Enter key)."""
        if event.input.id == "command_input":
            self._process_command()

    def _log_message(self, message: str) -> None:
        """Helper to log messages from threads safely."""
        log = self.query_one("#output_log", RichLog)
        log.write(message)

    @work(thread=True)
    def _generate_plan_worker(self, command: str, target_path: Path) -> None:
        """Generate a plan in background."""
        self.app.call_from_thread(self._log_message, f"[dim]Thinking... Context: {target_path}[/]")

        try:
            plan_data = self.gemini_client.generate_plan(command, target_path)
            self.current_plan = plan_data.get("plan", [])

            if not self.current_plan:
                self.app.call_from_thread(self._log_message, "[red]AI could not generate a plan.[/]")
                return

            # Display plan
            msg = "\n[bold purple]AI Proposed Plan:[/bold purple]\n"
            for step in self.current_plan:
                icon = "🗑️" if step.get("is_destructive") else "📝"
                msg += f"{step['step']}. {icon} [bold]{step['action']}[/]: {step['description']}\n"

            # Dry Run Simulation
            msg += "\n[bold cyan]Dry Run Simulation:[/bold cyan]\n"
            for step in self.current_plan:
                 # Running dry run for each step to get prediction
                 try:
                     res = asyncio.run(self.gemini_client.execute_plan_step(step, dry_run=True))
                     if "delete" in res.lower() or "remove" in res.lower():
                         color = "red"
                     elif "move" in res.lower() or "rename" in res.lower() or "organize" in res.lower():
                         color = "yellow"
                     else:
                         color = "green"
                     msg += f"  Step {step['step']}: [{color}]{res}[/{color}]\n"
                 except Exception as e:
                     msg += f"  Step {step['step']}: [red]Simulation failed: {e}[/]\n"

            self.app.call_from_thread(self._log_message, msg)

            # Trigger confirmation flow
            self.app.call_from_thread(self._request_confirmation, command)

        except Exception as e:
             self.app.call_from_thread(self._log_message, f"[bold red]Error generating plan:[/bold red] {e}")

    def _request_confirmation(self, command: str) -> None:
        """Ask user to confirm execution."""
        def check_confirm(confirmed: Optional[bool]) -> None:
            if confirmed:
                self._save_history_entry(command, self.current_plan, "executed")
                self._execute_plan_worker()
            else:
                self._save_history_entry(command, self.current_plan, "cancelled")
                self._log_message("[yellow]Plan cancelled.[/]")

        self.app.push_screen(
            ConfirmationScreen(
                "Execute this plan?",
                confirm_label="Confirm & Execute",
                confirm_variant="success"
            ),
            check_confirm
        )

    @work(thread=True)
    def _execute_plan_worker(self) -> None:
        """Execute the plan sequentially."""
        if not hasattr(self, 'current_plan') or not self.current_plan:
            return

        self.app.call_from_thread(self._log_message, "[bold]Executing Plan...[/]")

        for step in self.current_plan:
            try:
                # Real execution (dry_run=False)
                result = asyncio.run(self.gemini_client.execute_plan_step(step, dry_run=False))
                self.app.call_from_thread(self._log_message, f"[green]✔ Step {step['step']}: {result}[/]")
            except Exception as e:
                self.app.call_from_thread(self._log_message, f"[red]✖ Step {step['step']} Failed: {e}[/]")
                self.app.call_from_thread(self._log_message, "[bold red]Execution aborted.[/]")
                return

        self.app.call_from_thread(self._log_message, "[bold green]Plan completed successfully.[/]")

    @work(thread=True)
    def _search_history_worker(self, query: str) -> None:
        """Search history using AI."""
        self.app.call_from_thread(self._log_message, f"\n[dim]Searching history for '{query}'...[/]")

        if not self.history:
             self.app.call_from_thread(self._log_message, "[yellow]No history available.[/]")
             return

        results = self.gemini_client.search_history(query, self.history)

        if not results:
             self.app.call_from_thread(self._log_message, "[dim]No matches found.[/]")
             return

        self.app.call_from_thread(self._log_message, "\n[bold cyan]History Search Results:[/bold cyan]")
        for entry in results:
             ts = time.strftime('%Y-%m-%d %H:%M', time.localtime(entry["timestamp"]))
             self.app.call_from_thread(self._log_message, f"[{ts}] {entry['command']}")

    @work(thread=True)
    def _suggest_tags(self) -> None:
        self.app.call_from_thread(self._log_message, "\n[dim]Analyzing files for tags...[/]")

        files = []
        try:
            for p in self.current_dir.iterdir():
                if p.is_file():
                    files.append({
                        "name": p.name,
                        "size_human": str(p.stat().st_size)
                    })
        except Exception:
            pass

        if not files:
            self.app.call_from_thread(self._log_message, "[red]No files found to tag.[/]")
            return

        suggestions = self.gemini_client.suggest_tags(files)

        if not suggestions or not suggestions.get("suggestions"):
            self.app.call_from_thread(self._log_message, "[yellow]No tags suggested.[/]")
            return

        msg = "\n[bold yellow]Suggested Tags:[/bold yellow]\n"
        for item in suggestions.get("suggestions", []):
            tags = ", ".join(item["tags"])
            msg += f"- [bold]{item['file']}[/]: {tags}\n"

        self.app.call_from_thread(self._log_message, msg)
        self.app.call_from_thread(self._log_message, "[dim]Tip: Use 'tag <file> as <tag>' to apply them.[/]")

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

        # Start background worker
        self._generate_plan_worker(command_text, target_path)
