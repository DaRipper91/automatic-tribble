#!/bin/bash
set -e

echo "TFM Installer Bootstrap"
echo "======================="

exists() {
  command -v "$1" >/dev/null 2>&1
}

# 1. Environment Detection & System Dependencies
if [ -n "$TERMUX_VERSION" ]; then
    echo "[*] Termux detected."
    pkg install -y python python-pip rust binutils git
elif [ -f /etc/arch-release ]; then
    echo "[*] Arch/CachyOS detected."
    if ! exists python3; then
        echo "[*] Installing Python..."
        sudo pacman -Syu --noconfirm python python-pip git base-devel
    fi
else
    echo "[!] Unknown environment. Attempting generic install..."
    if ! exists python3; then
        echo "Python3 not found. Please install Python 3.8+ manually."
        exit 1
    fi
fi

# 2. Install Python dependencies for the installer (Textual, Rich)
echo "[*] Installing installer dependencies..."
if exists pip3; then
    PIP=pip3
else
    PIP=pip
fi

$PIP install textual rich --break-system-packages 2>/dev/null || $PIP install textual rich --user

# 3. Launch the TUI Installer
echo "[*] Launching TUI..."
python3 installer/installer.py
