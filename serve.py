#!/usr/bin/env python3
"""
Server runner script for the file manager.
Used for web deployments like Render using textual-serve.
"""

import os
from textual_serve.server import Server

def main():
    """Start the textual-serve web server."""
    # Render sets the PORT environment variable
    # We default to 8000 for local testing
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"

    print(f"Starting TFM Web Server on {host}:{port}")

    server = Server(
        command="python3 run.py",
        host=host,
        port=port,
        title="TFM - The Future Manager",
    )

    server.serve()

if __name__ == "__main__":
    main()
