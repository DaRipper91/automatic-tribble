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

AI Mode uses a local Gemini client to interpret natural language commands and execute complex file automation tasks. It features a robust multi-step planning engine, strict JSON validation, and context-aware directory analysis to make automation intelligent and safe.

### How to Use Multi-Step Planning
1.  **Select Target Directory**: Enter the path where you want operations to happen (default is current directory).
2.  **Enter Command**: Type what you want to do in plain English.
    - *Example:* "Clean up my desktop and sort everything into organized folders by project."
3.  **Process**: Click **Process** or press `Enter`.
4.  **Review Plan**: The AI will return a structured JSON plan containing an ordered list of atomic operations (each with action, source, target, description, and safety flags). This plan is displayed as a numbered checklist in the log.
5.  **Dry Run Simulation (Default)**: By default, TFM will simulate the full operation first, computing a diff of what would change. It displays this diff with color-coded output (green for new, yellow for moved, red for deleted). You can disable this via the UI toggle if you are a power user.
6.  **Confirm & Execute**: You must explicitly click the **Confirm & Execute** button to proceed. TFM will execute the steps sequentially, reporting per-step success or failure in real-time.

### Context-Aware Directory Summarization
When you open AI Mode or type a command, TFM automatically runs a lightweight background scan of the current directory. It injects a structured summary into the AI prompt, including:
- Total file count and size breakdown by category.
- Oldest and newest files.
- Top 5 largest files.
- Detected duplicate file groups.
*(This context is cached for 60 seconds to optimize performance).*

### AI Response Validation & Fallback
Every response from the AI is defensively parsed against strict JSON schemas. If the AI returns malformed JSON or an invalid plan, TFM will automatically retry the request up to 3 times, providing the validation error back to the model as feedback. If all retries fail, it gracefully falls back to showing the raw response text.

### AI Mode Command History & Semantic Search
Every command entered in AI Mode is persisted to `~/.tfm/command_history.json`, along with the resulting plan and whether it was executed or cancelled.
- **Cycle History**: Use `Up` / `Down` arrows in the input box to cycle through recent commands.
- **Semantic Search**: Click the **Search History** button to send a semantic similarity query to the AI (e.g., "find commands similar to 'organize photos'") against your past history.

### ✨ Quick Actions
The left panel provides buttons for common tasks:
- **📂 Organize by Type**: Groups files into folders like `Images/`, `Videos/`, `Documents/`.
- **📅 Organize by Date**: Groups files by Year/Month (e.g., `2023/10/`).
- **🧹 Cleanup Old Files**: Finds and removes files older than 30 days.
- **👯 Find Duplicates**: Identifies identical files to help you save space.
- **🏷️ Batch Rename**: Renames files based on a pattern.

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
Manage custom tags for your files. The AI-powered tagging system analyzes filenames, extensions, and directory context to automatically suggest tags. It uses a local SQLite database stored at `~/.tfm/tags.db`.

```bash
# Add a tag manually via natural language or directly:
tfm-auto tags --add ./document.pdf important

# List all tags in the database
tfm-auto tags --list

# Search for files with a specific tag
tfm-auto tags --search important

# Export tags
tfm-auto tags --export

# Remove a tag
tfm-auto tags --remove ./document.pdf important
```

### 7. Task Scheduler
Build persistent recurring automation jobs stored in `~/.tfm/schedule.json`.

```bash
# List scheduled jobs
tfm-auto schedule --list

# Add a job (e.g., organize downloads daily at midnight)
# Note: Params must be valid JSON
tfm-auto schedule --add "daily_org" "0 0 * * *" "organize_by_type" '{"source": "/home/user/Downloads", "target": "/home/user/Sorted"}'

# Run a scheduled job immediately
tfm-auto schedule --run-now "daily_org"

# Remove a job
tfm-auto schedule --remove "daily_org"

# Run the scheduler daemon (checks and executes due tasks every minute)
# Logs results to ~/.tfm/scheduler.log
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
