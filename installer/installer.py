import os
import sys
import shutil
import subprocess
import asyncio
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.screen import Screen
from textual.widgets import Header, Footer, Button, Label, Static, RichLog
from rich.console import Console

console = Console()

class InstallerApp(App):
    CSS = """
    Screen {
        align: center middle;
    }
    #welcome {
        padding: 2;
        border: solid green;
        height: auto;
        width: 60%;
        background: $surface;
    }
    #install-log {
        height: 80%;
        width: 80%;
        border: solid blue;
        background: $surface;
    }
    .title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    .info {
        text-align: center;
        margin-bottom: 1;
    }
    Button {
        width: 100%;
        margin-top: 1;
    }
    """

    def on_mount(self) -> None:
        self.push_screen(WelcomeScreen())

class WelcomeScreen(Screen):
    def compose(self) -> ComposeResult:
        with Container(id="welcome"):
            yield Label("TFM Installer", classes="title")
            yield Label("Detecting environment...", id="env-status", classes="info")
            yield Button("Install", id="install-btn", variant="primary", disabled=True)
            yield Button("Quit", id="quit-btn", variant="error")

    def on_mount(self) -> None:
        self.detect_environment()

    def detect_environment(self) -> None:
        env = "Unknown"
        if os.environ.get("TERMUX_VERSION"):
            env = "Termux"
        elif Path("/etc/arch-release").exists():
            env = "Arch Linux / CachyOS"
        elif Path("/etc/os-release").exists():
             try:
                 with open("/etc/os-release") as f:
                     content = f.read()
                     if "cachyos" in content.lower() or "arch" in content.lower():
                         env = "Arch Linux / CachyOS"
                     else:
                         env = "Generic Linux"
             except:
                 pass

        self.query_one("#env-status", Label).update(f"Detected Environment: {env}")
        self.app.env = env
        if env != "Unknown":
            self.query_one("#install-btn", Button).disabled = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "install-btn":
            self.app.push_screen(InstallScreen())
        elif event.button.id == "quit-btn":
            self.app.exit()

class InstallScreen(Screen):
    def compose(self) -> ComposeResult:
        with Container(id="install-log"):
            yield Label("Installing...", classes="title")
            yield RichLog(id="log", highlight=True, markup=True)
            yield Button("Finish", id="finish-btn", disabled=True, variant="success")

    def on_mount(self) -> None:
        self.run_install()

    async def run_install(self) -> None:
        log = self.query_one("#log", RichLog)
        env = getattr(self.app, "env", "Unknown")

        log.write(f"[bold green]Starting installation for {env}...[/]")

        # Helper to run command
        async def run_cmd(cmd, desc):
            log.write(f"[bold blue]Running:[/ {desc}")
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            if stdout:
                log.write(stdout.decode().strip())
            if stderr:
                log.write(f"[red]{stderr.decode().strip()}[/]")
            if proc.returncode != 0:
                log.write(f"[bold red]Error running {desc}[/]")
                return False
            return True

        # Install dependencies
        # We assume we are in the root of the repo
        if not await run_cmd("pip install -r requirements.txt", "Installing dependencies"):
             log.write("[yellow]Warning: Failed to install requirements.txt. Proceeding...[/]")

        # Install package
        install_cmd = "pip install ."

        if not await run_cmd(install_cmd, "Installing TFM package"):
             log.write("[yellow]Retrying with --break-system-packages...[/]")
             if not await run_cmd(install_cmd + " --break-system-packages", "Installing TFM package (forced)"):
                 log.write("[bold red]Installation Failed![/]")
                 return

        # Environment specific setup
        home = Path.home()

        if env == "Termux":
            log.write("[bold yellow]Configuring Termux...[/]")
            log.write("Please run 'termux-setup-storage' manually if you haven't already to access shared storage.")

        elif "Arch Linux / CachyOS" in env:
            log.write("[bold yellow]Configuring Desktop Environment...[/]")
            # Create .desktop file
            desktop_file = """[Desktop Entry]
Type=Application
Name=TFM
Comment=Terminal File Manager
Exec=tfm
Icon=utilities-terminal
Terminal=true
Categories=System;FileTools;FileManager;
"""
            apps_dir = home / ".local/share/applications"
            apps_dir.mkdir(parents=True, exist_ok=True)
            desktop_path = apps_dir / "tfm.desktop"

            try:
                with open(desktop_path, "w") as f:
                    f.write(desktop_file)
                log.write(f"Created desktop entry at {desktop_path}")
            except Exception as e:
                log.write(f"[red]Failed to create desktop entry: {e}[/]")

        log.write("[bold green]Installation Complete![/]")
        log.write("You can now run TFM by typing 'tfm' in your terminal.")

        self.query_one("#finish-btn", Button).disabled = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "finish-btn":
            self.app.exit()

if __name__ == "__main__":
    app = InstallerApp()
    app.run()
