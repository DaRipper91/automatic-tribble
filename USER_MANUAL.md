# 🧭 TFM User Manual

Comprehensive, task-focused guidance for using the Terminal File Manager (TFM) in both keyboard-driven User Mode and AI-assisted Automation Mode. This manual is written for everyday users, power users, and operators who want predictable, repeatable workflows.

## Table of Contents
1. [Overview](#overview)
2. [System Requirements](#system-requirements)
3. [Installation & Upgrade](#installation--upgrade)
4. [Launching TFM](#launching-tfm)
5. [First Run & UI Tour](#first-run--ui-tour)
6. [Navigation & Controls](#navigation--controls)
7. [Performing File Operations](#performing-file-operations)
8. [AI Mode in Depth](#ai-mode-in-depth)
9. [Automation CLI Reference (`tfm-auto`)](#automation-cli-reference-tfm-auto)
10. [Common Workflows](#common-workflows)
11. [Customization](#customization)
12. [Troubleshooting & FAQ](#troubleshooting--faq)
13. [Safety Notes](#safety-notes)
14. [Further Reading](#further-reading)

---

## Overview
TFM is a dual-pane, keyboard-first file manager with optional AI assistance. It provides:
- **User Mode**: Fast navigation, side-by-side panels, copy/move/delete, and refresh with Textual-powered visuals.
- **AI Mode**: Natural-language prompts and quick actions powered by the built-in Gemini mock integration (works without network) with optional handoff to a real Gemini CLI when configured.
- **Automation CLI**: Scriptable batch operations (`tfm-auto`) for organizing, searching, cleaning, and renaming files.

## System Requirements
- **Python**: 3.8 or newer.
- **Dependencies**: Installed via `pip install -r requirements.txt` (Textual and Rich).
- **OS**: Linux/macOS/WSL; Termux works for Android users.
- **Optional (AI Mode)**: Gemini CLI in your `PATH` and authenticated (`gemini login`) for real AI backends. The bundled client ships with a mock implementation if Gemini is not available.

## Installation & Upgrade
1. Clone and install dependencies:
   ```bash
   git clone https://github.com/DaRipper91/automatic-tribble.git
   cd automatic-tribble
   pip install -r requirements.txt
   ```
2. Editable/developer install (exposes `tfm` and `tfm-auto` commands):
   ```bash
   pip install -e .
   ```
3. Upgrade dependencies later:
   ```bash
   pip install -r requirements.txt --upgrade
   ```

## Launching TFM
- **User Mode TUI**: `tfm` (after editable install) or `python run.py`.
- **Automation CLI**: `tfm-auto <command> [options]`.
- **Demo preview**: `python demo.py` (non-interactive showcase).
- **Quit**: Press `q` in any screen, or `Esc` to return to the start menu from a mode.

## First Run & UI Tour
1. Start with `tfm` or `python run.py`.
2. **Start Menu** appears with two choices:
   - **User Mode (File Manager)**: Dual-pane file browser for manual control.
   - **AI Mode (Automation)**: Prompt-driven automation with quick-action buttons.
3. **User Mode layout**:
   - Header + Footer with status.
   - Two panels (left/right) showing directory contents; active panel is highlighted.
   - Status bar shows current paths and available shortcuts.
4. **AI Mode layout**:
   - Left rail of **Quick Actions** (organize, cleanup, duplicates, rename).
   - Right side for target directory input, AI command box, and an output log showing plans and results.

## Navigation & Controls
**Global**
- `q`: Quit the app.
- `Esc`: Back to start menu from a mode.

**User Mode Panels**
- `Tab`: Switch active panel (left/right).
- Arrow keys / Enter: Move selection and open directories.
- `Ctrl+R`: Refresh both panels.

**File Operations (User Mode)**
- `c`: Copy selected item to the inactive panel’s directory.
- `m`: Move selected item to the inactive panel’s directory.
- `d`: Delete selected item (with confirmation dialog).
- `n`: New directory *(placeholder notification in this version)*.
- `r`: Rename selected item *(placeholder notification in this version)*.
- `h`: Toggle help overlay.

## Performing File Operations
1. **Copy/Move**
   - Select a file/folder in the active panel.
   - Navigate the other panel to the destination.
   - Press `c` (copy) or `m` (move). Success and errors appear as notifications.
2. **Delete**
   - Select the item, press `d`.
   - Confirm in the modal dialog to proceed.
3. **Refresh Views**
   - Press `Ctrl+R` to resync both panels after external changes.
4. **Placeholders**
   - `n` (new dir) and `r` (rename) currently show informative notices. Use the Automation CLI for batch rename needs.

## AI Mode in Depth
1. **Prerequisites**
   - Optional: Install Gemini CLI (`npm install -g @google/gemini-cli` or `@mmbuto/gemini-cli-termux` for Termux) and authenticate with `gemini login`.
2. **Target Directory**
   - Enter the folder where actions should run. It must exist; otherwise, the log shows an error.
3. **Quick Actions**
   - Buttons prefill the command box (e.g., “Organize files by type”). Adjust text if needed, then click **Process** or press Enter.
4. **Freeform Commands**
   - Examples: “organize by date”, “cleanup files older than 45 days recursively”, “rename report to final”.
   - The mock AI maps intent to concrete actions (organize, cleanup, duplicates, batch rename). Unknown intents are reported in the log.
5. **Execution Feedback**
   - The Rich log shows the AI plan, context path, and results (counts of affected files).
6. **Safety**
   - Prefer starting in a scratch directory. For deletions, include words like “dry run” to avoid removal when supported by the command.

## Automation CLI Reference (`tfm-auto`)
Use `tfm-auto --help` for live details. Commands and key options:

| Command | Purpose | Core Options |
|---------|---------|--------------|
| `organize` | Group files by type or date | `--source`, `--target`, `--by-type` \| `--by-date`, `--move` |
| `search` | Find files by name or content | `--dir`, `--name` pattern, `--content` text, `--case-sensitive` |
| `duplicates` | Detect duplicate files | `--dir`, `--recursive` (defaults to true) |
| `cleanup` | Remove old files | `--dir`, `--days`, `--dry-run`, `--recursive` |
| `rename` | Batch rename files | `--dir`, `--pattern`, `--replacement`, `--recursive` |

### Examples
- Organize by type:  
  `tfm-auto organize --source ~/Downloads --target ~/Organized --by-type`
- Organize by date (move instead of copy):  
  `tfm-auto organize --source ~/Downloads --target ~/Archive --by-date --move`
- Search PDFs by name:  
  `tfm-auto search --dir ~/Documents --name "*.pdf"`
- Search content (case-insensitive):  
  `tfm-auto search --dir ~/Notes --content "meeting"`
- Find duplicates recursively:  
  `tfm-auto duplicates --dir ~/Photos`
- Dry-run cleanup of 30+ day-old files:  
  `tfm-auto cleanup --dir ~/Downloads --days 30 --dry-run`
- Batch rename:  
  `tfm-auto rename --dir ~/Docs --pattern "draft" --replacement "final" --recursive`

## Common Workflows
- **Organize Downloads quickly**: `tfm-auto organize --source ~/Downloads --target ~/Organized --by-type`.
- **Monthly archive by date**: `tfm-auto organize --source ~/Projects --target ~/Archive --by-date --move`.
- **Storage cleanup**: `tfm-auto cleanup --dir ~/Downloads --days 60 --dry-run` then rerun without `--dry-run`.
- **Duplicate sweep**: `tfm-auto duplicates --dir ~/Pictures` then delete manually in User Mode.
- **Search across config files**: `tfm-auto search --dir ~/.config --name "*.conf"`.
- **Bulk rename photos**: `tfm-auto rename --dir ~/Photos --pattern "IMG_" --replacement "Trip_" --recursive`.

## Customization
- **File categories**: Edit `FILE_CATEGORIES` in `src/file_manager/automation.py` to add or change type groupings; defaults cover images, video, audio, documents, spreadsheets, presentations, archives, code, and data.
- **Date format**: Update `date_format` argument in `organize_by_date` (e.g., `"%Y/%m/%d"` for daily folders).
- **Start paths**: User Mode opens both panels at your home directory; navigate to any location and refresh as needed.
- **Termux tips**: Ensure storage permission (`termux-setup-storage`) and that `gemini` is on PATH for AI Mode.

## Troubleshooting & FAQ
- **`ModuleNotFoundError` or missing dependencies**: Run `pip install -r requirements.txt`.
- **TUI looks plain or broken**: Confirm `echo $TERM` shows a 256-color capable value (e.g., `xterm-256color`) and use a modern terminal.
- **Permission denied when copying/moving**: Check file ownership or rerun with appropriate privileges; avoid running as root unless necessary.
- **AI says it cannot understand a command**: Rephrase using action keywords like “organize”, “cleanup”, “duplicates”, or “rename”.
- **CLI reports unknown command**: Run `tfm-auto --help` to see available subcommands and required flags.
- **Nothing happens on `n` or `r` in User Mode**: These are placeholders in this version; use CLI rename or create directories with standard shell commands.

## Safety Notes
- Prefer **copy** before **move** when testing new workflows.
- Use `--dry-run` with `cleanup` to preview deletions.
- Keep destinations outside source paths to avoid accidental overwrites.
- Verify targets in AI Mode before executing commands.

## Further Reading
- Quickstart and high-level overview: [README.md](README.md)
- Task-focused walkthroughs: [USAGE.md](USAGE.md)
- Source entry points: `run.py` (TUI) and `src/file_manager/cli.py` (automation CLI)
