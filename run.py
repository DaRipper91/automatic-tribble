#!/usr/bin/env python3
"""
Simple runner script for the file manager.
Can be executed directly without installation.
"""

import sys
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from file_manager.app import main

if __name__ == "__main__":
    main()
