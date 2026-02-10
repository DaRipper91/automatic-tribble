# Termux File Manager (TFM)

A powerful Text User Interface (TUI) file manager for Termux that helps you manage files and folders across both Termux home directory and Android shared storage.

## Features

- **Dual-Pane Interface**: Navigate two directories simultaneously for easy file operations
- **Cross-Storage Management**: Seamlessly work with both Termux home folder (`~/`) and Android shared storage (`/sdcard`)
- **File Operations**: Copy, move, delete, and manage files and directories
- **Keyboard-Driven**: Efficient keyboard shortcuts for all operations
- **Modern TUI**: Built with Textual for a responsive and intuitive interface
- **Automation Tools**: Command-line utilities for batch operations
  - Organize files by type or date
  - Search files by name, content, or size
  - Find and manage duplicate files
  - Clean up old files
  - Batch rename operations

## Installation

### Requirements
- Python 3.8 or higher
- Termux (for Android)

### Install from source

```bash
# Clone the repository
git clone https://github.com/DaRipper91/automatic-tribble.git
cd automatic-tribble

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Quick Run (without installation)

```bash
# Install dependencies
pip install -r requirements.txt

# Run directly
python run.py
```

## Usage

### Start the file manager

**Interactive TUI:**
```bash
tfm
```

Or if running without installation:
```bash
python run.py
```

**Automation CLI:**
```bash
tfm-auto --help
```

Or without installation:
```bash
python src/file_manager/cli.py --help
```

**Demo script:**
```bash
python demo.py
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Tab` | Switch between left and right panels |
| `Arrow Keys` | Navigate files and directories |
| `Enter` | Enter directory / Select file |
| `c` | Copy selected file/directory to other panel |
| `m` | Move selected file/directory to other panel |
| `d` | Delete selected file/directory |
| `n` | Create new directory |
| `r` | Rename selected file/directory |
| `Ctrl+R` | Refresh both panels |
| `h` | Show help |
| `q` | Quit application |

### Automation CLI Commands

**Organize files by type:**
```bash
tfm-auto organize --source ~/Downloads --target ~/Organized --by-type
```

**Organize files by date:**
```bash
tfm-auto organize --source ~/Downloads --target ~/Organized --by-date
```

**Search for files:**
```bash
tfm-auto search --dir ~/Documents --name "*.pdf"
tfm-auto search --dir ~/Documents --content "important"
```

**Find duplicate files:**
```bash
tfm-auto duplicates --dir ~/Downloads
```

**Clean up old files:**
```bash
tfm-auto cleanup --dir ~/Downloads --days 30 --dry-run
```

**Batch rename files:**
```bash
tfm-auto rename --dir ~/Photos --pattern "IMG_" --replacement "Photo_"
```

## Architecture

The file manager consists of:

- **app.py**: Main application with dual-pane layout and keyboard bindings
- **file_panel.py**: Individual file panel widget with directory tree
- **file_operations.py**: Core file operation functions (copy, move, delete, etc.)
- **search.py**: File search functionality (by name, content, size)
- **automation.py**: Automation tools for file organization and batch operations
- **cli.py**: Command-line interface for automation features

## Default Locations

- **Left Panel**: Termux home directory (`~` or `/data/data/com.termux/files/home`)
- **Right Panel**: Android shared storage (`/sdcard` if available, otherwise `~`)

## Termux Setup

For proper access to Android shared storage, you need to grant Termux storage permissions:

```bash
termux-setup-storage
```

This will create symbolic links in your home directory to access Android folders:
- `~/storage/shared` - Internal storage
- `~/storage/downloads` - Downloads folder
- `~/storage/dcim` - Camera folder
- etc.

## Development

### Project Structure

```
automatic-tribble/
├── src/
│   └── file_manager/
│       ├── __init__.py
│       ├── app.py              # Main TUI application
│       ├── file_panel.py       # File panel widget
│       ├── file_operations.py  # File operations
│       ├── search.py           # Search functionality
│       ├── automation.py       # Automation features
│       └── cli.py              # CLI for automation
├── requirements.txt
├── setup.py
├── run.py                      # Quick run script
├── demo.py                     # Feature demonstration
└── README.md
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 
