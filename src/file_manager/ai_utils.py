import subprocess
import shlex
import re
from typing import Optional, Tuple
from .utils import find_gemini_executable

class AIExecutor:
    """Handles interaction with the Gemini CLI."""

    def __init__(self):
        self.gemini_path = find_gemini_executable()

    def is_available(self) -> bool:
        """Check if Gemini CLI is installed."""
        return self.gemini_path is not None

    def execute_prompt(self, prompt: str) -> str:
        """
        Send a prompt to Gemini and return the response.
        """
        if not self.gemini_path:
            return "Error: Gemini CLI not found. Please install gemini-cli-termux or @google/gemini-cli."

        try:
            # Command format: gemini -p "prompt"
            cmd = [self.gemini_path, "-p", prompt]

            # Run the command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30  # Timeout after 30 seconds
            )

            if result.returncode != 0:
                # Some CLIs print errors to stdout, check both
                return f"Error ({result.returncode}): {result.stderr} {result.stdout}"

            return result.stdout.strip()

        except subprocess.TimeoutExpired:
            return "Error: Request timed out."
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
