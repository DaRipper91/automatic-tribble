import subprocess
import shlex
import re
import time
import selectors
from typing import Optional, Tuple
from .utils import find_gemini_executable

class AIExecutor:
    """Handles interaction with the Gemini CLI."""

    def __init__(self):
        self.gemini_path = find_gemini_executable()

    def is_available(self) -> bool:
        """Check if Gemini CLI is installed."""
        return self.gemini_path is not None

    def _run_with_limit(self, cmd: list, timeout: int = 30, max_size: int = 10 * 1024 * 1024) -> Tuple[int, str, str]:
        """
        Run a command with a timeout and output size limit.
        Returns (returncode, stdout, stderr).
        """
        start_time = time.time()
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  # Line buffered
        )

        stdout_chunks = []
        stderr_chunks = []
        current_size = 0

        # We use selectors to read from both pipes without blocking
        sel = selectors.DefaultSelector()
        sel.register(process.stdout, selectors.EVENT_READ)
        sel.register(process.stderr, selectors.EVENT_READ)

        try:
            while True:
                # Check for timeout
                if time.time() - start_time > timeout:
                    process.kill()
                    raise subprocess.TimeoutExpired(cmd, timeout)

                # Wait for I/O with a small timeout to allow checking the overall timeout
                events = sel.select(timeout=0.1)

                if not events and process.poll() is not None:
                    # Process finished and no more data to read
                    break

                for key, _ in events:
                    fileobj = key.fileobj
                    # Read a chunk. 4096 is a reasonable size.
                    chunk = fileobj.read(4096)

                    if not chunk:
                        # End of file
                        sel.unregister(fileobj)
                        continue

                    if fileobj == process.stdout:
                        stdout_chunks.append(chunk)
                    else:
                        stderr_chunks.append(chunk)

                    current_size += len(chunk)
                    if current_size > max_size:
                        process.kill()
                        raise ValueError("Output exceeded limit")

                # If both pipes are closed, we are done
                if not sel.get_map():
                    break

        finally:
            sel.close()
            # Ensure process is cleaned up
            if process.poll() is None:
                process.kill()
                process.wait()

            # Close pipes explicitly to avoid ResourceWarning
            if process.stdout:
                process.stdout.close()
            if process.stderr:
                process.stderr.close()

        return process.returncode, "".join(stdout_chunks), "".join(stderr_chunks)

    def execute_prompt(self, prompt: str) -> str:
        """
        Send a prompt to Gemini and return the response.
        """
        if not self.gemini_path:
            return "Error: Gemini CLI not found. Please install gemini-cli-termux or @google/gemini-cli."

        try:
            # Command format: gemini -p "prompt"
            cmd = [self.gemini_path, "-p", prompt]

            # Run the command with limit
            returncode, stdout, stderr = self._run_with_limit(cmd, timeout=30)

            if returncode != 0:
                # Some CLIs print errors to stdout, check both
                return f"Error ({returncode}): {stderr} {stdout}"

            return stdout.strip()

        except subprocess.TimeoutExpired:
            return "Error: Request timed out."
        except ValueError as e:
            if str(e) == "Output exceeded limit":
                return "Error: Output exceeded limit."
            return f"Error executing AI command: {str(e)}"
        except Exception as e:
            return f"Error executing AI command: {str(e)}"

    def generate_automation_command(self, user_request: str) -> Tuple[Optional[str], str]:
        """
        Translate a natural language request into a tfm-auto command.

        Returns:
            Tuple[Optional[str], str]: (command_string, status_message)
        """
        system_prompt = (
            "You are an assistant for a file manager CLI tool named tfm-auto.\n"
            "The user wants to perform a file operation. Translate their request into a valid shell command.\n"
            "\n"
            "Available Commands:\n"
            "1. Organize files:\n"
            "   tfm-auto organize --source <src_dir> --target <dst_dir> [--by-type|--by-date] [--move]\n"
            "2. Search files:\n"
            "   tfm-auto search --dir <dir> [--name <pattern>|--content <text>] [--case-sensitive]\n"
            "3. Cleanup old files:\n"
            "   tfm-auto cleanup --dir <dir> --days <N> [--dry-run] [--recursive]\n"
            "4. Find duplicates:\n"
            "   tfm-auto duplicates --dir <dir> [--recursive]\n"
            "5. Batch rename:\n"
            "   tfm-auto rename --dir <dir> --pattern <text> --replacement <text> [--recursive]\n"
            "\n"
            "Rules:\n"
            "- Output ONLY the command string. Do not add markdown blocks or explanations.\n"
            "- If the request is dangerous (e.g., delete all files), prefer --dry-run if available.\n"
            "- If the request is unclear, output 'ERROR: Unclear request'.\n"
            "\n"
            f"User Request: '{user_request}'\n"
        )

        response = self.execute_prompt(system_prompt)

        # Clean up response (remove code blocks if present)
        response = response.replace("```bash", "").replace("```", "").strip()

        if response.startswith("tfm-auto"):
            return response, "Command generated successfully."
        elif response.startswith("ERROR"):
            return None, response
        else:
            # Fallback: try to find the command in the text
            match = re.search(r"tfm-auto\s+[\w\-]+.*", response)
            if match:
                return match.group(0), "Command extracted from response."

            return None, f"Could not generate a valid command. Response: {response}"
