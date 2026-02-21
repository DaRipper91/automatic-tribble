# TFM (The Future Manager) File Manager

## Introduction
TFM is an innovative file manager application designed to simplify and enhance file management tasks. It combines a robust interactive text-based user interface (TUI) with advanced AI automation capabilities, making file operations intuitive and efficient.

## Features
- **Interactive TUI**: Navigate and manage files using a user-friendly terminal interface.
- **AI Automation**: Utilize AI to automate repetitive file management tasks.
- **Multi-Platform Support**: Runs seamlessly on various operating systems, including Windows, macOS, and Linux.
- **Customization**: Configure settings and preferences to suit individual workflows.
- **File Operations**: Fast and reliable file copying, moving, renaming, and deleting.
- **Search Functionality**: Quick search feature to locate files easily.
- **Scripting Support**: Support for custom scripts to extend functionality.

## Installation
To install TFM, follow these steps:
1. **Clone the repository**:  
   ```bash
   git clone https://github.com/DaRipper91/automatic-tribble.git
   cd automatic-tribble
   ```  
2. **Install dependencies**:  
   ```bash
   pip install -r requirements.txt
   ```  
3. **Run the application**:  
   ```bash
   python main.py
   ```

## Usage
After installation, you can launch TFM by running `python main.py`. 

### Basic Commands
- `list`: Display files in the current directory.
- `move <source> <destination>`: Move files from the source to the destination.
- `copy <source> <destination>`: Copy files from the source to the destination.
- `delete <filename>`: Delete the specified file.

For a full list of commands, type `help` within the application.

## Architecture
TFM is structured in a modular way:
- **Core Module**: Handles the main functionalities of TFM.
- **TUI Module**: Responsible for rendering the user interface and user interactions.
- **AI Module**: Implements automation capabilities and intelligent suggestions.

This structure allows for easy scalability and maintenance.

## Contribution Guidelines
We welcome contributions! To contribute:
1. Fork the repository.
2. Create your feature branch:  
   ```bash
   git checkout -b feature/YourFeature
   ```
3. Commit your changes:  
   ```bash
   git commit -m 'Add some feature'
   ```
4. Push to the branch:  
   ```bash
   git push origin feature/YourFeature
   ```
5. Open a pull request.

Please ensure your code adheres to the project's coding standards.

## License
TFM is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.

---

For further information, feedback, or issues, please reach out via GitHub issues or contact us directly.