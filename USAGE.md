# Termux File Manager - Usage Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [TUI Interface](#tui-interface)
3. [Automation CLI](#automation-cli)
4. [Common Tasks](#common-tasks)
5. [Tips and Tricks](#tips-and-tricks)

## Getting Started

### First-Time Setup in Termux

1. Install Python and dependencies:
```bash
pkg install python git
```

2. Clone and install:
```bash
git clone https://github.com/DaRipper91/automatic-tribble.git
cd automatic-tribble
pip install -r requirements.txt
```

3. Set up storage access:
```bash
termux-setup-storage
```

This creates symbolic links in `~/storage/` for accessing Android folders.

### Running the Application

**Interactive TUI:**
```bash
python run.py
```

**Demo:**
```bash
python demo.py
```

## TUI Interface

### Layout Overview

```
┌─────────────────────────────────────────┐
│ Termux File Manager                     │  ← Header
├──────────────────┬──────────────────────┤
│ Termux Home      │ Android Storage      │  ← Panel Headers
│                  │                      │
│ Left Panel       │ Right Panel          │  ← File Lists
│ (Active)         │                      │
│                  │                      │
├──────────────────┴──────────────────────┤
│ Paths Info                              │  ← Status Bar
│ Keyboard Shortcuts                      │
├─────────────────────────────────────────┤
│ Tab: Switch | C: Copy | M: Move ...     │  ← Footer
└─────────────────────────────────────────┘
```

### Navigation

- **Arrow Keys**: Move up/down in file list
- **Enter**: Open directory or select file
- **Tab**: Switch between left and right panels
- **Home**: Jump to top of list
- **End**: Jump to bottom of list

### File Operations

| Key | Operation | Description |
|-----|-----------|-------------|
| `c` | Copy | Copy selected item to other panel |
| `m` | Move | Move selected item to other panel |
| `d` | Delete | Delete selected item |
| `n` | New Dir | Create new directory |
| `r` | Rename | Rename selected item |
| `Ctrl+R` | Refresh | Refresh both panels |

### General

| Key | Operation | Description |
|-----|-----------|-------------|
| `h` | Help | Show help message |
| `q` | Quit | Exit application |

## Automation CLI

The `tfm-auto` command provides batch operations without the TUI.

### Organize Files

**By Type:**
```bash
# Organize Downloads folder by file type
tfm-auto organize --source ~/Downloads --target ~/Organized --by-type

# Move instead of copy
tfm-auto organize --source ~/Downloads --target ~/Organized --by-type --move
```

This creates folders like:
- `images/` - .jpg, .png, .gif, etc.
- `videos/` - .mp4, .avi, .mkv, etc.
- `documents/` - .pdf, .doc, .txt, etc.
- `audio/` - .mp3, .wav, .flac, etc.

**By Date:**
```bash
# Organize by modification date (YYYY/MM format)
tfm-auto organize --source ~/Downloads --target ~/Organized --by-date
```

This creates folders like `2024/01/`, `2024/02/`, etc.

### Search Files

**By Name:**
```bash
# Find all PDFs
tfm-auto search --dir ~/Documents --name "*.pdf"

# Find files with specific name
tfm-auto search --dir ~/storage/shared --name "receipt*"

# Case-sensitive search
tfm-auto search --dir ~/Documents --name "README" --case-sensitive
```

**By Content:**
```bash
# Find files containing text
tfm-auto search --dir ~/Documents --content "important"

# Search in specific file types
tfm-auto search --dir ~/Documents --content "TODO"
```

### Find Duplicates

```bash
# Find duplicate files in Downloads
tfm-auto duplicates --dir ~/Downloads

# Non-recursive (current directory only)
tfm-auto duplicates --dir ~/Photos --recursive
```

### Clean Up Old Files

```bash
# Preview files to be deleted (dry run)
tfm-auto cleanup --dir ~/Downloads --days 30 --dry-run

# Actually delete old files
tfm-auto cleanup --dir ~/Downloads --days 30

# Recursive cleanup
tfm-auto cleanup --dir ~/storage/shared/DCIM --days 90 --recursive
```

### Batch Rename

```bash
# Rename all files with pattern
tfm-auto rename --dir ~/Photos --pattern "IMG_" --replacement "Photo_"

# Recursive rename
tfm-auto rename --dir ~/Documents --pattern "draft" --replacement "final" --recursive
```

## Common Tasks

### Task 1: Organize Downloads

```bash
# Create organized folder
mkdir ~/Organized

# Organize by type
tfm-auto organize --source ~/Downloads --target ~/Organized --by-type

# Review results
ls ~/Organized
```

### Task 2: Clean Up Storage

```bash
# Find old files (preview)
tfm-auto cleanup --dir ~/storage/shared/Downloads --days 60 --dry-run

# Delete if satisfied
tfm-auto cleanup --dir ~/storage/shared/Downloads --days 60
```

### Task 3: Find and Remove Duplicates

```bash
# Find duplicates
tfm-auto duplicates --dir ~/storage/shared/DCIM

# Review the list
# Manually delete unwanted duplicates using TUI or rm command
```

### Task 4: Transfer Files Between Storage

Using TUI:
1. Run `python run.py`
2. Navigate in left panel to Termux file
3. Navigate in right panel to Android destination
4. Press `c` to copy or `m` to move

### Task 5: Search for Specific Files

```bash
# Find all Python scripts
tfm-auto search --dir ~/ --name "*.py"

# Find config files
tfm-auto search --dir ~/.config --name "*.conf"

# Find files containing sensitive data
tfm-auto search --dir ~/Documents --content "password"
```

## Tips and Tricks

### 1. Use Symbolic Links

After running `termux-setup-storage`, use these shortcuts:
- `~/storage/shared` - Internal storage
- `~/storage/downloads` - Downloads folder
- `~/storage/dcim` - Camera folder
- `~/storage/music` - Music folder

### 2. Automate Regular Tasks

Create a script to organize downloads weekly:

```bash
#!/bin/bash
# organize-weekly.sh
tfm-auto organize \
    --source ~/storage/downloads \
    --target ~/storage/shared/Organized \
    --by-date \
    --move

tfm-auto cleanup \
    --dir ~/storage/shared/Organized \
    --days 90
```

### 3. Search Efficiently

Use wildcards for flexible searches:
- `*.txt` - All text files
- `report_*.pdf` - Reports
- `2024*.jpg` - Photos from 2024

### 4. Backup Important Files

```bash
# Copy important files to Termux home
tfm-auto organize \
    --source ~/storage/shared/Important \
    --target ~/Backups \
    --by-date
```

### 5. Monitor Storage Usage

Create a script to monitor large files:

```bash
#!/bin/bash
# find-large-files.sh
echo "Files larger than 100MB:"
find ~/storage/shared -type f -size +100M -ls
```

### 6. Quick File Organization

For quick one-time organization without moving files:

```bash
# Just copy to organized folders
tfm-auto organize \
    --source ~/Downloads \
    --target ~/Organized \
    --by-type
# Original files stay in Downloads
```

## Troubleshooting

### Permission Errors

If you get permission errors accessing `/sdcard`:
```bash
termux-setup-storage
# Then accept the permission prompt
```

### Module Not Found

If you see `ModuleNotFoundError`:
```bash
pip install -r requirements.txt
```

### TUI Not Displaying Properly

Ensure terminal supports colors:
```bash
echo $TERM
# Should show something like "xterm-256color"
```

## Advanced Usage

### Custom File Categories

Edit `src/file_manager/automation.py` to customize file categories:

```python
FILE_CATEGORIES = {
    'my_category': ['.custom', '.special'],
    # ... add your categories
}
```

### Integration with Other Tools

Combine with standard Unix tools:

```bash
# Find and organize only files from last week
find ~/Downloads -mtime -7 | \
while read file; do
    tfm-auto organize --source "$file" --target ~/Recent --by-type
done
```

---

For more information, see the [README.md](README.md) file.
