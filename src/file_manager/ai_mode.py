"""
AI Mode Screen - Automation Interface
"""

from typing import Optional
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
    ]

    def __init__(self):
        super().__init__()
        self.gemini_client = GeminiClient()
        self.current_dir = Path.cwd()

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
    def _execute_command_worker(self, action_data: dict) -> None:
        """Execute the command in a worker thread."""
        self.app.call_from_thread(self._log_message, "[dim]Executing...[/]")

        result = self.gemini_client.execute_command(action_data)

        if result.startswith("Error"):
            self.app.call_from_thread(self._log_message, f"[bold red]Result:[/ bold red] {result}")
        else:
            self.app.call_from_thread(self._log_message, f"[bold green]Result:[/ bold green] {result}")

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

        # 1. Process with Gemini Mock
        action_data = self.gemini_client.process_command(command_text, target_path)

        if action_data["action"] == "unknown":
            log.write(f"[bold red]AI:[/ bold red] {action_data['description']}")
            return

        log.write(f"[bold purple]AI Plan:[/ bold purple] {action_data['description']}")

        # 2. Execute
        def check_confirm(confirmed: Optional[bool]) -> None:
            if confirmed:
                self._execute_command_worker(action_data)
            else:
                log.write("[yellow]Command cancelled.[/]")

        self.app.push_screen(
            ConfirmationScreen(
                f"Execute command:\n{action_data['description']}?",
                confirm_label="Execute",
                confirm_variant="success"
            ),
            check_confirm
        )

        # Clear input? Maybe keep it for reference.
        # command_input.value = ""
