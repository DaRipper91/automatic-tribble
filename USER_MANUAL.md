# 📖 TFM User Manual

Welcome to the **TFM (The Future Manager)** User Manual. This guide provides comprehensive instructions for using the interactive TUI, the AI automation features, and the powerful CLI tools.

---

## 📋 Table of Contents

1.  [Getting Started](#-getting-started)
2.  [User Mode (Interactive TUI)](#-user-mode-interactive-tui)
3.  [AI Mode (Automation)](#-ai-mode-automation)
4.  [CLI Automation (tfm-auto)](#-cli-automation-tfm-auto)
5.  [Advanced Features](#-advanced-features)
    - [Undo/Redo System](#-undoredo-system)
    - [Plugin System](#-plugin-system)
    - [Configuration](#-configuration)
6.  [Troubleshooting](#-troubleshooting)

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
| `d` | Delete | Delete selected item (moved to Trash). |
| `n` | New Directory | Create a new folder in the current directory. |
| `r` | Rename | Rename the selected file or folder. |
| **General** | | |
| `h` | Help | Show the help screen. |
| `Esc` | Back | Return to the Start Menu. |
| `q` | Quit | Exit the application completely. |

### 💡 Tips
- **Async Operations**: Copying, moving, and deleting files happen in the background, keeping the UI responsive.
- **Undo/Redo**: Core operations are tracked. You can undo mistakes using the CLI (`tfm-auto --undo`).
- **Safe Delete**: Deleted files are moved to `~/.tfm/trash/` instead of being permanently removed immediately.

---

## 🤖 AI Mode (Automation)

AI Mode uses natural language processing to understand your intent and execute complex file operations automatically.

### How to Use
1.  **Select Target Directory**: Enter the path where you want operations to happen (default is current directory).
2.  **Enter Command**: Type what you want to do in plain English.
    - *Example:* "Organize all PDFs into a Documents folder and clean up files older than 30 days."
    - *Example:* "Find and delete duplicate images."
3.  **Process**: Click **Process** or press `Enter`.
4.  **Review Plan**: The AI will propose a structured plan with steps.
5.  **Dry Run Simulation**: TFM will simulate the plan and show you exactly what will change (files moved, deleted, etc.) with color-coded feedback.
6.  **Confirm**: Click **Confirm & Execute** to apply the changes.

### Command History
- Use `Up` / `Down` arrows in the input box to cycle through previous commands.
- Click **Search History** to find past commands.

### ✨ Quick Actions
The left panel provides buttons for common tasks:
- **📂 Organize by Type**: Groups files into folders like `Images/`, `Videos/`, `Documents/`.
- **📅 Organize by Date**: Groups files by Year/Month (e.g., `2023/10/`).
- **🧹 Cleanup Old Files**: Finds and removes files older than 30 days.
- **👯 Find Duplicates**: Identifies identical files to help you save space.
- **🏷️ Batch Rename**: Renames files based on a pattern.

---

## ⚡ CLI Automation (`tfm-auto`)

For scripting and cron jobs, use the command-line interface. Use `--json` flag for machine-readable output.

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

# Find files containing specific text (case-insensitive)
tfm-auto search --dir ./Notes --content "meeting notes"

# Output results as JSON
tfm-auto search --dir ./Notes --content "TODO" --json
```

### 3. Cleanup
Delete old files to free up space.
```bash
# Delete files older than 60 days (Recursive)
tfm-auto cleanup --dir ./Temp --days 60 --recursive

# Dry run (preview what would be deleted without actually deleting)
tfm-auto cleanup --dir ./Temp --days 60 --dry-run
```

### 4. Find & Resolve Duplicates
Scan a directory for identical files. The system uses a multi-pass strategy (size -> partial hash -> full hash) for efficiency.

```bash
# Find duplicates
tfm-auto duplicates --dir ./Photos --recursive

# Resolve duplicates by keeping the newest version automatically
tfm-auto duplicates --dir ./Photos --resolve newest

# Resolve duplicates by keeping the oldest version
tfm-auto duplicates --dir ./Photos --resolve oldest
```
**Resolution Strategies:**
- `newest`: Keeps the file with the most recent modification time.
- `oldest`: Keeps the file with the oldest modification time.
- `interactive`: Prompts you to choose which file to keep for each duplicate group.

### 5. Batch Rename
Rename multiple files using a simple pattern match.
```bash
# Rename "IMG_*" to "Vacation_*"
tfm-auto rename --dir ./Photos --pattern "IMG_" --replacement "Vacation_"
```

### 6. File Tagging
Manage custom tags for your files.
```bash
# Add a tag
tfm-auto tags --add ./document.pdf important

# List all tags
tfm-auto tags --list

# Find files by tag
tfm-auto tags --search important

# Remove a tag
tfm-auto tags --remove ./document.pdf important
```

### 7. Task Scheduler
Automate recurring tasks using cron expressions.
```bash
# List scheduled jobs
tfm-auto schedule --list

# Add a job (e.g., organize downloads daily at midnight)
# Note: Params must be valid JSON
tfm-auto schedule --add "daily_org" "0 0 * * *" "organize_by_type" '{"source": "/home/user/Downloads", "target": "/home/user/Sorted"}'

# Remove a job
tfm-auto schedule --remove "daily_org"

# Run the scheduler daemon (keeps running)
tfm-auto schedule --daemon
```

### 8. Undo / Redo
Revert accidental changes. The history is persisted to `~/.tfm/history.json`.
```bash
# Undo the last operation
tfm-auto --undo

# Redo the last undone operation
tfm-auto --redo
```

### 9. Configuration
Manage settings.
```bash
# Open configuration file in default editor
tfm-auto config --edit
```

---

## ⚙️ Advanced Features

### 🔄 Undo/Redo System
TFM tracks all destructive operations (Move, Copy, Delete, Rename, Create Directory).
- **Storage**: History is saved in `~/.tfm/history.json`, so it persists between sessions.
- **Limit**: The undo stack is currently unbounded (until cleared manually or by file size limits in future versions).
- **Usage**: You can use `tfm-auto --undo` or `tfm-auto --redo` at any time.

### 🔌 Plugin System
Extend functionality by adding Python scripts to `~/.tfm/plugins/`.

1.  **Create the directory**:
    ```bash
    mkdir -p ~/.tfm/plugins
    ```
2.  **Create a plugin file** (e.g., `my_plugin.py`):
    ```python
    from src.file_manager.plugins import TFMPlugin

    class MyPlugin(TFMPlugin):
        def on_file_added(self, path):
            print(f"Plugin: File added at {path}")

        def on_file_deleted(self, path):
            print(f"Plugin: File deleted at {path}")
    ```
3.  **Restart TFM**: The plugin will be automatically loaded.

**Available Hooks:**
- `on_file_added(path)`
- `on_file_deleted(path)`
- `on_organize(source, destination)`
- `on_search_complete(query, results)`

### 🛠️ Configuration
File categories can be customized in `~/.tfm/categories.yaml`.
Default categories include: `images`, `videos`, `documents`, `archives`, `code`, `data`.

To edit the configuration:
```bash
tfm-auto config --edit
```

**Example `categories.yaml`:**
```yaml
images:
  - .jpg
  - .png
  - .gif
documents:
  - .pdf
  - .docx
  - .txt
```

### 🔍 Logging
All operations are logged. You can create a plugin to redirect logs to a specific file or external service. By default, errors are printed to stderr and info to stdout (or `rich` console).

---

## 🔧 Troubleshooting

### Common Issues

**`ModuleNotFoundError: No module named 'rich'`**
- **Solution**: You are missing dependencies. Run `pip install -r requirements.txt`.

**`tfm-auto: command not found`**
- **Solution**: You haven't installed the package in editable mode. Use `pip install -e .` or execute via `python src/file_manager/cli.py`.

**"Access Denied" errors**
- **Solution**: Ensure you have read/write permissions for the directories you are trying to modify.

---

**Happy Managing!** 🚀

## New Features (v1.1)

### Undo and Redo

TFM now includes an `OperationHistory` stack that tracks all destructive operations (move, copy, delete, rename, create directory). You can easily undo or redo operations using the CLI flags:

- `tfm-auto --undo`: Undoes the last operation.
- `tfm-auto --redo`: Redoes the last undone operation.

### Duplicate File Resolution Engine

The `duplicates` command in `tfm-auto` has been enhanced with a multi-pass intelligent resolution engine. It compares file size, partial hash, and full SHA-256 hash. It now supports five resolution strategies:

- `newest`: Keeps the newest file, deletes others.
- `oldest`: Keeps the oldest file, deletes others.
- `largest`: Keeps the largest file, deletes others.
- `smallest`: Keeps the smallest file, deletes others.
- `interactive`: Prompts you to select which file to keep.

Example:
`tfm-auto duplicates --dir ~/Downloads --resolve largest`

### Custom Categories Configuration

You can now customize your file categories used by the `organize` command. TFM creates a `categories.yaml` in your `~/.tfm/` folder.
To quickly edit this file, use:
`tfm-auto config --edit-categories`

### CLI Progress Bars and JSON Output

- All long-running operations (`organize`, `duplicates`, `cleanup`, `rename`) now present a beautiful rich progress bar with dynamic summaries.
- Add `--json` to any command to receive machine-readable JSON output instead of the visual UI, useful for scripting and pipelining commands.

### TFM Plugin Architecture

TFM supports extending its functionality with Python plugins! Simply drop a Python file containing a subclass of `TFMPlugin` into `~/.tfm/plugins/`.
Plugins support hooks:
- `on_file_added(path)`
- `on_file_deleted(path)`
- `on_organize(source, destination)`
- `on_search_complete(query, results)`
