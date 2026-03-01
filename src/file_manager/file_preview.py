import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional

from textual.widgets import Static
from textual.reactive import reactive
from rich.syntax import Syntax
from rich.panel import Panel

class FilePreview(Static):
    """A widget to preview file contents."""

    path: reactive[Optional[Path]] = reactive(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._current_task: Optional[asyncio.Task] = None

    def watch_path(self, path: Optional[Path]) -> None:
        """Called when path changes."""
        if self._current_task:
            self._current_task.cancel()

        if path is None:
            self.update("")
            return

        self.update(Panel("Loading...", title=path.name))
        self._current_task = asyncio.create_task(self._load_preview(path))

    async def _load_preview(self, path: Path) -> None:
        try:
            if not path.exists():
                self.update(Panel("File not found", title=path.name, style="red"))
                return

            if path.is_dir():
                self.update(Panel("Directory preview not supported", title=path.name))
                return

            # File size check
            try:
                size = path.stat().st_size
            except OSError:
                self.update(Panel("Error accessing file", title=path.name, style="red"))
                return

            if size == 0:
                 self.update(Panel("Empty file", title=path.name))
                 return

            # Determine type
            suffix = path.suffix.lower()
            if suffix in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']:
                await self._show_image_metadata(path)
            elif suffix in ['.txt', '.py', '.md', '.json', '.yaml', '.yml', '.js', '.html', '.css', '.sh', '.c', '.cpp', '.h', '.tcss']:
                await self._show_text_content(path)
            else:
                # Try to read as text first, if fails, hex dump
                try:
                    await self._show_text_content(path)
                except UnicodeDecodeError:
                    await self._show_hex_dump(path)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.update(Panel(f"Error loading preview: {e}", title=path.name if path else "Error", style="red"))

    async def _show_image_metadata(self, path: Path) -> None:
        stats = path.stat()
        created = datetime.fromtimestamp(stats.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
        modified = datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        size_str = self._format_size(stats.st_size)

        info = [
            f"[bold]File:[/bold] {path.name}",
            f"[bold]Size:[/bold] {size_str}",
            f"[bold]Created:[/bold] {created}",
            f"[bold]Modified:[/bold] {modified}",
            "",
            "[italic]Image preview not supported in terminal.[/italic]"
        ]

        self.update(Panel("\n".join(info), title="Image Metadata", border_style="blue"))

    async def _show_text_content(self, path: Path) -> None:
        # Read first 100 lines
        def read_file():
            lines = []
            with open(path, 'r', encoding='utf-8') as f:
                for _ in range(100):
                    line = f.readline()
                    if not line: break
                    lines.append(line)
            return "".join(lines)

        try:
            content = await asyncio.to_thread(read_file)

            # Syntax highlighting
            extension = path.suffix.lstrip('.')
            if not extension:
                extension = "txt"

            syntax = Syntax(
                content,
                extension,
                theme="monokai",
                line_numbers=True,
                word_wrap=False
            )
            self.update(syntax)
        except (UnicodeDecodeError, UnicodeError):
             # Fallback to hex if utf-8 fails
             await self._show_hex_dump(path)

    async def _show_hex_dump(self, path: Path) -> None:
        def read_bytes():
            with open(path, 'rb') as f:
                return f.read(512)

        data = await asyncio.to_thread(read_bytes)

        # Format hex dump
        hex_dump = []
        for i in range(0, len(data), 16):
            chunk = data[i:i+16]
            hex_str = " ".join(f"{b:02x}" for b in chunk)
            text_str = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            hex_dump.append(f"{i:04x}  {hex_str:<48}  {text_str}")

        content = "\n".join(hex_dump)
        if len(data) == 512:
            content += "\n..."

        self.update(Panel(content, title="Binary Preview (First 512 bytes)", border_style="yellow"))

    def _format_size(self, size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"
