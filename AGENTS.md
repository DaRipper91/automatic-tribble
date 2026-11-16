# AGENTS.md — automatic-tribble (TFM: The Future Manager)

## Project Overview
`automatic-tribble` (packaged as `termux-file-manager`, command `tfm`) is a terminal file management suite bridging dual-pane terminal efficiency with AI automation. Designed for both desktop Linux and Android Termux, it provides classic Commander-style navigation, asynchronous file operations, tag management, cron scheduling, and AI plan execution via Gemini.

- **Package Name:** `termux-file-manager`
- **CLI Commands:**
  - `tfm` — Interactive dual-pane Textual TUI (`src/file_manager/app.py`).
  - `tfm-auto` — Headless automation and AI scheduling CLI (`src/file_manager/cli.py`).
- **Core Package Directory:** `src/file_manager/`
- **Test Suite:** `tests/` (235 automated unit/integration tests).

---

## Technical Stack & Dependencies
- **Language:** Python 3.8+ (tested on Python 3.14 on Linux aarch64).
- **Core Dependencies:**
  - `textual>=0.47.0`, `rich>=13.7.0`
  - `jinja2`, `jsonschema`, `croniter`, `PyYAML`
- **Testing Engine:** `pytest`, `pytest-asyncio` (configured via `pytest.ini`).

---

## Architecture & Subsystems
- **TUI & Views (`src/file_manager/`):**
  - `app.py` — Root Textual application lifecycle and keybindings.
  - `file_panel.py` — Dual-pane directory tree, selection, and preview panels.
  - `user_mode.py` & `ai_mode.py` — User task execution and AI orchestration screens.
- **AI Automation & Engine:**
  - `ai_integration.py` — Gemini client integration and response schema validation.
  - `ai_utils.py` — Plan execution engine and command safety verification.
- **Metadata & Scheduling:**
  - `tags.py` — Tag indexing, search, and cleanup routines.
  - `scheduler.py` — Cron-based asynchronous recurring automation runner.
  - `operation_history.py` — Action ledger supporting undo/redo operations.

---

## Agent Guidance & Invariant Rules
- **Canonical Agent Configuration:**
  `AGENTS.md` in the repository root is canonical. `CLAUDE.md`, `GEMINI.md`, and `.cursorrules` are symlinks pointing directly to this file.
- **Pythonpath Invariant:**
  Maintain `pytest.ini` specifying `pythonpath = .` to ensure `import src...` and `import file_manager...` resolve in all submodules.
- **Verification Rule:**
  Never commit changes without running `.venv/bin/pytest tests/` and verifying 100% pass rates across all test modules.

---

## Verification Runbooks
```bash
# Navigate to working tree
cd /home/daripper/Projects/automatic-tribble

# Run full automated test suite (235 tests)
.venv/bin/pytest tests/

# Execute headless CLI help test
python3 src/file_manager/cli.py --help
```
