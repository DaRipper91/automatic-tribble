"""
Screens for the file manager application.
"""

from typing import Optional
from textual.app import ComposeResult
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, Label, RadioSet, RadioButton, Input, Log, ProgressBar
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding

from .ai_utils import AIExecutor


class StartupScreen(Screen):
    """Initial splash screen."""

    CSS = """
    StartupScreen {
        align: center middle;
        background: $surface;
    }

    #title {
        text-style: bold;
        text-align: center;
        width: 100%;
        color: $accent;
        margin-bottom: 2;
        content-align: center middle;
    }

    #subtitle {
        text-align: center;
        width: 100%;
        color: $text-muted;
    }
    """

    def compose(self) -> ComposeResult:
        with Container():
            yield Label("TFM: The Future Manager", id="title")
            yield Label("Press any key to enter...", id="subtitle")

    def on_key(self, event) -> None:
        self.dismiss()


class ExitScreen(Screen):
    """Goodbye screen."""

    CSS = """
    ExitScreen {
        align: center middle;
        background: $surface;
    }

    #goodbye {
        text-style: bold;
        text-align: center;
        width: 100%;
        color: $success;
        margin-bottom: 2;
    }
    """

    def compose(self) -> ComposeResult:
        with Container():
            yield Label("Goodbye! Session Terminated.", id="goodbye")
            yield Label("Closing application...", classes="subtitle")

    def on_mount(self) -> None:
        self.set_timer(2.0, self.app.exit)


class LauncherScreen(Screen):
    """Main menu to choose between User Mode and AI Mode."""

    CSS = """
    LauncherScreen {
        align: center middle;
    }

    #menu-container {
        width: 60;
        height: auto;
        border: thick $primary;
        padding: 2;
        background: $surface;
    }

    .menu-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 2;
        width: 100%;
    }

    Button {
        width: 100%;
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="menu-container"):
            yield Label("Select Mode", classes="menu-title")
            yield Button("User Mode (Interactive)", id="user-mode", variant="primary")
            yield Button("AI Mode (Automation)", id="ai-mode", variant="success")
            yield Button("Quit", id="quit", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "user-mode":
            def on_mode_selected(mode: str) -> None:
                if mode:
                    # Set the layout mode on the main app
                    if hasattr(self.app, "layout_mode"):
                        self.app.layout_mode = mode
                    # Dismiss the launcher to reveal the file manager
                    self.dismiss()

            self.app.push_screen(UserModeConfigScreen(), on_mode_selected)

        elif event.button.id == "ai-mode":
            self.app.push_screen(AIConfigScreen())
        elif event.button.id == "quit":
            self.app.push_screen(ExitScreen())


class UserModeConfigScreen(ModalScreen[str]):
    """Configuration for User Mode (Single vs Dual)."""

    CSS = """
    UserModeConfigScreen {
        align: center middle;
    }

    #config-dialog {
        padding: 1 2;
        width: 60;
        height: auto;
        border: thick $background 80%;
        background: $surface;
    }

    .title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
        width: 100%;
    }

    RadioSet {
        margin: 1 0;
    }

    #buttons {
        margin-top: 1;
        align: center bottom;
    }

    Button {
        margin: 0 1;
    }
    """

    BINDINGS = [Binding("escape", "dismiss", "Dismiss")]

    def action_dismiss(self) -> None:
        self.dismiss(None)

    def compose(self) -> ComposeResult:
        with Container(id="config-dialog"):
            yield Label("Select Layout", classes="title")
            with RadioSet(id="layout-select"):
                yield RadioButton("Dual Panel (Default)", id="dual", value=True)
                yield RadioButton("Single Panel", id="single")

            with Horizontal(id="buttons"):
                yield Button("Cancel", id="cancel", variant="error")
                yield Button("Start", id="start", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start":
            radio_set = self.query_one(RadioSet)
            if radio_set.pressed_button:
                selected_id = radio_set.pressed_button.id
                self.dismiss(selected_id)
            else:
                self.dismiss("dual")
        elif event.button.id == "cancel":
            self.dismiss(None)



class AIConfigScreen(Screen):
    """AI Mode Interface."""

    CSS = """
    AIConfigScreen {
        align: center middle;
    }

    #ai-container {
        width: 90%;
        height: 90%;
        border: thick $success;
        background: $surface;
        padding: 1;
    }

    #header {
        height: 3;
        dock: top;
        content-align: center middle;
        text-style: bold;
        background: $success 20%;
    }

    #prompt-area {
        height: auto;
        margin: 1 0;
    }

    #output-log {
        height: 1fr;
        border: solid $secondary;
        background: $surface-lighten-1;
    }

    .preset-btn {
        width: 1fr;
        margin: 0 1;
    }

    #controls {
        height: auto;
        dock: bottom;
        margin-top: 1;
    }
    """

    BINDINGS = [Binding("escape", "back", "Back")]

    def __init__(self):
        super().__init__()
        self.ai = AIExecutor()

    def compose(self) -> ComposeResult:
        with Container(id="ai-container"):
            title = "AI Automation Console"
            if not self.ai.is_available():
                title += " (OFFLINE - Gemini CLI not found)"

            yield Label(title, id="header")

            with Vertical(id="prompt-area"):
                yield Label("Natural Language Command:")
                yield Input(placeholder="e.g., 'Organize my downloads folder by date'", id="ai-input")

            yield Label("Output:")
            yield Log(id="output-log")

            with Horizontal(id="controls"):
                yield Button("Organize", classes="preset-btn", id="btn-organize")
                yield Button("Cleanup", classes="preset-btn", id="btn-cleanup")
                yield Button("Search", classes="preset-btn", id="btn-search")
                yield Button("Back to Menu", variant="error", id="btn-back")

    def on_mount(self) -> None:
        log = self.query_one(Log)
        if not self.ai.is_available():
            log.write_line("[bold red]Error: Gemini CLI not found.[/]")
            log.write_line("Please install 'gemini-cli-termux' or '@google/gemini-cli' globally.")
            log.write_line("Ensure 'gemini' is in your PATH.")
        else:
            log.write_line("[green]AI System Online. Ready for commands.[/]")
            log.write_line("Type a request above or use the preset buttons.")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        user_input = event.value
        log = self.query_one(Log)
        input_widget = self.query_one(Input)

        if not user_input:
            return

        log.write_line(f"\n[bold blue]User:[/] {user_input}")
        input_widget.value = ""

        if not self.ai.is_available():
            log.write_line("[red]AI is not available.[/]")
            return

        # Show processing
        log.write_line("[yellow]Processing...[/]")

        # Determine intent (command vs general query)
        # For now, assume command generation unless it looks like a question
        command, status = self.ai.generate_automation_command(user_input)

        if command:
            log.write_line(f"[bold green]Generated Command:[/] {command}")
            log.write_line(f"[italic]{status}[/]")

            # Ask for confirmation to run
            def check_confirm(confirmed: bool) -> None:
                if confirmed:
                    log.write_line("[yellow]Executing command...[/]")
                    # Execute the command locally
                    import subprocess
                    import shlex
                    try:
                        args = shlex.split(command)
                        result = subprocess.run(args, capture_output=True, text=True)
                        if result.stdout:
                            log.write_line(result.stdout)
                        if result.stderr:
                            log.write_line(f"[red]{result.stderr}[/]")
                        log.write_line("[green]Command execution finished.[/]")
                    except Exception as e:
                        log.write_line(f"[red]Execution failed: {e}[/]")
                else:
                    log.write_line("[yellow]Command cancelled.[/]")

            self.app.push_screen(
                ConfirmationScreen(f"Execute command:\n{command}?", confirm_label="Execute", confirm_variant="success"),
                check_confirm
            )
        else:
            log.write_line(f"[red]Could not generate command:[/] {status}")
            # Fallback to generic AI response
            log.write_line("[yellow]Asking Gemini directly...[/]")
            response = self.ai.execute_prompt(user_input)
            log.write_line(f"[bold magenta]Gemini:[/] {response}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        input_widget = self.query_one(Input)

        if event.button.id == "btn-back":
            self.dismiss()
        elif event.button.id == "btn-organize":
            input_widget.value = "Organize files in Downloads folder by type"
            input_widget.focus()
        elif event.button.id == "btn-cleanup":
            input_widget.value = "Clean up old files in Downloads older than 30 days"
            input_widget.focus()
        elif event.button.id == "btn-search":
            input_widget.value = "Search for PDF files in Documents"
            input_widget.focus()


class ProgressScreen(ModalScreen):
    """Screen for showing progress of operations."""

    CSS = """
    ProgressScreen {
        align: center middle;
    }

    #progress-dialog {
        padding: 2;
        width: 60;
        height: auto;
        border: thick $background 80%;
        background: $surface;
    }

    ProgressBar {
        margin: 1 0;
    }

    #status-label {
        text-align: center;
        width: 100%;
    }
    """

    def __init__(self, message: str = "Processing..."):
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        with Container(id="progress-dialog"):
            yield Label(self.message, id="status-label")
            yield ProgressBar(total=100, show_eta=True, id="progress-bar")

    def update_progress(self, progress: float, message: Optional[str] = None) -> None:
        bar = self.query_one(ProgressBar)
        bar.update(progress=progress)
        if message:
            self.query_one("#status-label").update(message)


# Keep existing ConfirmationScreen and HelpScreen
class ConfirmationScreen(ModalScreen[bool]):
    """Screen for confirming actions."""

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    CSS = """
    ConfirmationScreen {
        align: center middle;
    }

    #dialog {
        padding: 0 1;
        width: 60;
        height: 11;
        border: thick $background 80%;
        background: $surface;
    }

    #question {
        content-align: center middle;
        height: 1fr;
        width: 100%;
    }

    #buttons {
        height: auto;
        width: 100%;
        align: center bottom;
        dock: bottom;
        margin-bottom: 1;
    }

    Button {
        margin: 0 1;
        width: 1fr;
    }
    """

    BINDINGS = [Binding("escape", "dismiss", "Dismiss")]

    def action_dismiss(self) -> None:
        self.dismiss(False)

    def __init__(self, message: str, confirm_label: str = "Delete", confirm_variant: str = "error"):
        super().__init__()
        self.message = message
        self.confirm_label = confirm_label
        self.confirm_variant = confirm_variant

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label(self.message, id="question")
            with Horizontal(id="buttons"):
                yield Button("Cancel", variant="primary", id="cancel")
                yield Button(self.confirm_label, variant=self.confirm_variant, id="confirm")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm":
            self.dismiss(True)
        else:
            self.dismiss(False)

    def action_cancel(self):
        self.dismiss(False)




class HelpScreen(ModalScreen):
    """Screen for displaying help/keybindings."""

    CSS = """
    HelpScreen {
        align: center middle;
    }

    #help-dialog {
        padding: 1 2;
        width: 60;
        height: auto;
        border: thick $background 80%;
        background: $surface;
    }

    .title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
        width: 100%;
    }

    .key-row {
        height: auto;
        padding: 0 1;
        margin-bottom: 0;
    }

    .key {
        width: 30%;
        text-style: bold;
        color: $accent;
    }

    .description {
        width: 70%;
    }

    #close-button {
        margin-top: 1;
        width: 100%;
    }
    """

    BINDINGS = [Binding("escape", "dismiss", "Close")]

    def action_dismiss(self):
        self.dismiss()

    def compose(self) -> ComposeResult:
        with Container(id="help-dialog"):
            yield Label("Keyboard Shortcuts", classes="title")

            shortcuts = [
                ("Tab", "Switch Panel"),
                ("Arrow Keys", "Navigate"),
                ("Enter", "Open / Select"),
                ("c", "Copy"),
                ("m", "Move"),
                ("d", "Delete"),
                ("n", "New Directory"),
                ("r", "Rename"),
                ("ctrl+r", "Refresh"),
                ("h", "Toggle Help"),
                ("q", "Quit"),
                ("esc", "Close Panel / Cancel"),
            ]

            with Vertical(id="shortcuts-list"):
                for key, desc in shortcuts:
                    with Horizontal(classes="key-row"):
                        yield Label(key, classes="key")
                        yield Label(desc, classes="description")

            yield Button("Close", variant="primary", id="close-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()


class InputScreen(ModalScreen[str]):
    """Screen for getting text input from the user."""

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    CSS = """
    InputScreen {
        align: center middle;
    }

    #input-dialog {
        padding: 0 1;
        width: 60;
        height: 13;
        border: thick $background 80%;
        background: $surface;
    }

    .title {
        text-align: center;
        text-style: bold;
        margin-top: 1;
        width: 100%;
    }

    #message {
        margin-top: 1;
        margin-bottom: 1;
        content-align: center middle;
        width: 100%;
    }

    Input {
        margin-bottom: 1;
    }

    #buttons {
        height: auto;
        width: 100%;
        align: center bottom;
        dock: bottom;
        margin-bottom: 1;
    }

    Button {
        margin: 0 1;
        width: 1fr;
    }
    """

    BINDINGS = [Binding("escape", "dismiss", "Dismiss")]

    def action_dismiss(self) -> None:
        self.dismiss("")

    def __init__(self, title: str, message: str, initial_value: str = ""):
        super().__init__()
        self.title_text = title
        self.message = message
        self.initial_value = initial_value

    def compose(self) -> ComposeResult:
        with Container(id="input-dialog"):
            yield Label(self.title_text, classes="title")
            yield Label(self.message, id="message")
            yield Input(value=self.initial_value, placeholder="Enter value...")
            with Horizontal(id="buttons"):
                yield Button("Cancel", variant="primary", id="cancel")
                yield Button("OK", variant="success", id="ok")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            self.dismiss(self.query_one(Input).value)
        else:
            self.dismiss("")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value)

    def action_cancel(self):
        self.dismiss("")
