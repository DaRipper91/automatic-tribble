# 📖 TFM User Manual

Welcome to the **TFM (The Future Manager)** User Manual. This guide provides comprehensive instructions for using the interactive TUI, the AI automation features, and the powerful CLI tools.

---

## 📋 Table of Contents

1.  [Getting Started](#-getting-started)
2.  [User Mode (Interactive TUI)](#-user-mode-interactive-tui)
3.  [AI Mode (Automation)](#-ai-mode-automation)
4.  [CLI Automation (tfm-auto)](#-cli-automation-tfm-auto)
5.  [Troubleshooting](#-troubleshooting)

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.8+**
- A terminal with 256-color support (e.g., modern Linux terminal, iTerm2, Windows Terminal).

### Installation

1.  **Clone and Install:**
    ```bash
    git clone https://github.com/DaRipper91/automatic-tribble.git
    cd automatic-tribble
    pip install -r requirements.txt
    ```

2.  **Optional CLI Setup:**
    To use the `tfm-auto` command globally, install the package in editable mode:
    ```bash
    pip install -e .
    ```

### Launching the App
Run the main application:
```bash
python run.py
```
This opens the **Start Menu**, where you can choose between **User Mode** and **AI Mode**.

---

## 🖥️ User Mode (Interactive TUI)

User Mode is a dual-pane file manager designed for speed and keyboard efficiency.

### 🗺️ Interface Layout

```
┌─────────────────────────────────────────┐
│ Left Panel       │ Right Panel          │
│ [..]             │ [..]                 │
│ folder1/         │ file.txt             │
│ file_a.py        │ image.png            │
│                  │                      │
│ (Active)         │                      │
├──────────────────┴──────────────────────┤
│ 1 item selected        /home/user/docs  │
└─────────────────────────────────────────┘
```

### ⌨️ Keyboard Shortcuts

| Key | Action | Description |
| :--- | :--- | :--- |
| **Navigation** | | |
| `↑` / `↓` | Move Selection | Navigate up and down the file list. |
| `Enter` | Open | Enter a directory or open a file. |
| `Tab` | Switch Panel | Toggle focus between Left and Right panels. |
| `Home` / `End` | Jump | Jump to the top or bottom of the list. |
| `Ctrl+R` | Refresh | Reload both file panels. |
| **Operations** | | |
| `c` | Copy | Copy selected item to the *inactive* panel. |
| `m` | Move | Move selected item to the *inactive* panel. |
| `d` | Delete | Delete selected item (with confirmation). |
| `n` | New Directory | Create a new folder in the current directory. |
| `r` | Rename | Rename the selected file or folder. |
| **General** | | |
| `h` | Help | Show the help screen. |
| `Esc` | Back | Return to the Start Menu. |
| `q` | Quit | Exit the application completely. |

### 💡 Tips
- **Async Deletion**: Deleting large folders happens in the background, so the UI won't freeze.
- **Overwrite Safety**: If you try to copy/move a file that already exists, TFM will ask for confirmation before overwriting.

---

## 🤖 AI Mode (Automation)

AI Mode uses natural language processing to understand your intent and execute complex file operations automatically.

### How to Use
1.  **Select Target Directory**: Enter the path where you want operations to happen (default is current directory).
2.  **Enter Command**: Type what you want to do in plain English.
    - *Example:* "Organize all PDFs into a Documents folder."
    - *Example:* "Find and delete duplicate images."
3.  **Process**: Click **Process** or press `Enter`.
4.  **Review & Execute**: The AI will propose a plan. Review it and confirm execution.

### ✨ Quick Actions
The left panel provides buttons for common tasks:
- **📂 Organize by Type**: Groups files into folders like `Images/`, `Videos/`, `Documents/`.
- **📅 Organize by Date**: Groups files by Year/Month (e.g., `2023/10/`).
- **🧹 Cleanup Old Files**: Finds and removes files older than 30 days.
- **👯 Find Duplicates**: Identifies identical files to help you save space.
- **🏷️ Batch Rename**: Renames files based on a pattern.

---

## ⚡ CLI Automation (`tfm-auto`)

For scripting and cron jobs, use the command-line interface.

*(Note: If `tfm-auto` is not available, use `python src/file_manager/cli.py`)*

### 1. Organize Files
Sort files into folders based on their extension or modification date.
```bash
# Organize by file type (e.g., .jpg -> images/, .pdf -> documents/)
tfm-auto organize --source ./Downloads --target ./Sorted --by-type

# Organize by date (Year/Month) and MOVE files (instead of copy)
tfm-auto organize --source ./Photos --target ./Archive --by-date --move
```

### 2. Search
Find files by name pattern or content.
```bash
# Find all Python files
tfm-auto search --dir ./Project --name "*.py"

# Find files containing specific text
tfm-auto search --dir ./Notes --content "meeting notes"
```

### 3. Cleanup
Delete old files to free up space.
```bash
# Delete files older than 60 days (Recursive)
tfm-auto cleanup --dir ./Temp --days 60 --recursive

# Dry run (preview what would be deleted without actually deleting)
tfm-auto cleanup --dir ./Temp --days 60 --dry-run
```

### 4. Find Duplicates
Scan a directory for identical files (based on content hash).
```bash
tfm-auto duplicates --dir ./Photos --recursive
```

### 5. Batch Rename
Rename multiple files using a simple pattern match.
```bash
# Rename "IMG_*" to "Vacation_*"
tfm-auto rename --dir ./Photos --pattern "IMG_" --replacement "Vacation_"
```

---

## 🔧 Troubleshooting

### Common Issues

**`ModuleNotFoundError: No module named 'textual'`**
- **Solution**: You are missing dependencies. Run `pip install -r requirements.txt`.

**`tfm-auto: command not found`**
- **Solution**: You haven't installed the package in editable mode. Use `pip install -e .` or execute via `python src/file_manager/cli.py`.

**UI looks broken or weird characters appear**
- **Solution**: Ensure your terminal supports UTF-8 and 256 colors. Try running `export TERM=xterm-256color` before starting the app.

**"Access Denied" errors**
- **Solution**: Ensure you have read/write permissions for the directories you are trying to modify.

---

**Happy Managing!** 🚀
