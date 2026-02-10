# Termux File Manager (TFM)

A powerful Text User Interface (TUI) file manager for Termux that helps you manage files and folders across both Termux home directory and Android shared storage.

## Features

- **Dual-Pane Interface**: Navigate two directories simultaneously for easy file operations
- **Cross-Storage Management**: Seamlessly work with both Termux home folder (`~/`) and Android shared storage (`/sdcard`)
- **File Operations**: Copy, move, delete, and manage files and directories
- **Keyboard-Driven**: Efficient keyboard shortcuts for all operations
- **Modern TUI**: Built with Textual for a responsive and intuitive interface

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

```bash
tfm
```

Or if running without installation:
```bash
python run.py
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

## Architecture

The file manager consists of:

- **app.py**: Main application with dual-pane layout and keyboard bindings
- **file_panel.py**: Individual file panel widget with directory tree
- **file_operations.py**: Core file operation functions (copy, move, delete, etc.)

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
│       ├── app.py              # Main application
│       ├── file_panel.py       # File panel widget
│       └── file_operations.py  # File operations
├── requirements.txt
├── setup.py
├── run.py
└── README.md
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 
