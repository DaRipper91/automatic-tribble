# 🚀 TFM: The Future Manager

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![TUI](https://img.shields.io/badge/TUI-Textual-green)
![AI Powered](https://img.shields.io/badge/AI-Gemini-purple)

**The Next-Gen File Manager for your Terminal.**

TFM combines a robust Dual-Pane File Manager with powerful AI Automation. Whether you need precise control or intelligent batch operations, TFM adapts to your workflow.

## ✨ Key Features

### 🤖 AI Mode (New!)
Harness the power of Google Gemini directly in your terminal.
- **Natural Language Commands**: "Organize my downloads by date", "Find all PDF files"
- **Intelligent Automation**: Let AI generate the complex shell commands for you.
- **Chat Integration**: Ask questions about your files or get help.

### 🖥️ User Mode
A flexible, keyboard-driven interface.
- **Dual Pane**: Classic Norton Commander style for efficient file transfers.
- **Single Pane**: Focused view with **Dynamic Split**—automatically opens a second panel when you Copy or Move files!
- **Fast & Responsive**: Built with Textual for a modern, lag-free experience.

## 📦 Installation

### Prerequisites
- Python 3.8+
- [Gemini CLI](https://geminicli.com) (Optional, for AI features)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/DaRipper91/automatic-tribble.git
cd automatic-tribble

# Install dependencies
pip install -r requirements.txt

# Run TFM
python run.py
```

### 🧠 Setting up AI Mode
To unlock the full potential of AI Mode, install the Gemini CLI:

**For Termux / Android:**
```bash
npm install -g @mmmbuto/gemini-cli-termux
```

**For Desktop / Server:**
```bash
npm install -g @google/gemini-cli
```
*Ensure `gemini` is in your PATH and authenticated.*

## 🎮 Controls

| Key | Action |
|-----|--------|
| `Tab` | Switch Panel |
| `C` | Copy (Dynamic Split in Single Mode!) |
| `M` | Move (Dynamic Split in Single Mode!) |
| `D` | Delete |
| `N` | New Directory |
| `R` | Rename |
| `Q` | Quit |

## 🛠️ Architecture

TFM is built with modularity in mind:
- **`app.py`**: The core TUI application.
- **`screens.py`**: Modular screens (Launcher, Config, AI Console).
- **`ai_utils.py`**: Bridge to the Gemini CLI.
- **`file_operations.py`**: Thread-safe file management.

## 🤝 Contributing

Join us in building the future of terminal file management! PRs are welcome.

---
*Built with ❤️ and Python.*

## 🤖 AI-Ready
This repo adheres to the Repomix standard. Run `repomix` to pack the codebase for LLM context.
