import shutil
import os
from typing import Optional

def find_gemini_executable() -> Optional[str]:
    """
    Finds the path to the gemini executable.
    Checks for 'gemini' and 'gemini-cli-termux'.
    """
    # Check for 'gemini' first (standard install)
    gemini_path = shutil.which("gemini")
    if gemini_path:
        return gemini_path

    # Check for 'gemini-cli-termux' (explicit package name)
    gemini_path = shutil.which("gemini-cli-termux")
    if gemini_path:
        return gemini_path

    return None
