# 📁 TFM - The Future Manager

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20WSL-lightgrey)

**TFM (The Future Manager)** is a next-generation file management solution that bridges the gap between classic terminal efficiency and modern AI automation. Whether you need a robust dual-pane file browser or an intelligent assistant to organize your digital life, TFM has you covered.

---

## 🚀 Key Features

### 🖥️ **Interactive TUI (User Mode)**
- **Dual-Pane Interface**: Classic Commander-style layout for efficient file operations.
- **Keyboard-First Navigation**: Fast, intuitive shortcuts for power users.
- **Async Operations**: Non-blocking file deletions and background tasks keep the UI responsive.
- **Rich Visuals**: Built with [Textual](https://textual.textualize.io/) for a beautiful terminal experience.

### 🤖 **AI Automation (AI Mode)**
- **Natural Language Commands**: "Organize my downloads by date" or "Find duplicates in Photos".
- **Smart Execution**: The built-in AI engine (powered by Gemini integration) interprets your intent and executes complex batch operations.
- **Quick Actions**: One-click buttons for common tasks like cleanup, organization, and renaming.

### ⚡ **Automation CLI (`tfm-auto`)**
- **Scriptable Power**: Automate your workflows directly from the shell.
- **Batch Processing**: Organize, clean, search, and rename thousands of files in seconds.
- **Dry Run Support**: Preview changes before they happen.

---

## 📦 Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/DaRipper91/automatic-tribble.git
    cd automatic-tribble
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Optional (for CLI command access):**
    ```bash
    pip install -e .
    ```

---

## 🎮 Quick Start

### **Launch the TUI**
Start the interactive file manager:
```bash
python run.py
```
*Navigate with arrow keys, use `Tab` to switch panels, and press `?` or `h` for help.*

### **Run an Automation Task**
Organize your Downloads folder by file type immediately:
```bash
python src/file_manager/cli.py organize --source ~/Downloads --target ~/Documents/Sorted --by-type
```
*(Or use `tfm-auto` if you installed with `pip install -e .`)*

---

## 📚 Documentation

For a deep dive into all features, keyboard shortcuts, and advanced configuration, please consult the **[User Manual](USER_MANUAL.md)**.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
