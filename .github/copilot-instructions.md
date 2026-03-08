# TFM (The Future Manager) — Copilot Instructions

## Commands

```bash
# Run all tests
python -m pytest tests/

# Run a single test
python -m pytest tests/test_automation_async.py::TestAutomationAsync::test_organize_by_type

# Lint
ruff check src/

# Type check
mypy src/

# Launch TUI
python run.py

# Run automation CLI
python src/file_manager/cli.py <command>

# Install (editable, enables tfm / tfm-auto entry points)
pip install -e .
```

## Architecture

TFM has three modes sharing a common core:

- **TUI (User Mode)** — `app.py` → `start_menu.py` → `user_mode.py`. `FileManagerApp` is a Textual `App` that pushes `StartMenuScreen` first. `UserModeScreen` renders the dual-pane interface using `DualFilePanes` / `FilePanel`.
- **AI Mode** — `ai_mode.py` (`AIModeScreen`) sends natural-language commands to `GeminiClient` (`ai_integration.py`). Prompts are rendered via Jinja2 templates in `prompts/` (planning, tagging, semantic_search, validation).
- **Automation CLI** — `cli.py` (`tfm-auto` entry point). Uses argparse subcommands: `organize`, `search`, `duplicates`, `rename`, `schedule`, `tags`, `config`.

### Core modules

| Module | Responsibility |
|---|---|
| `file_operations.py` | `FileOperations` — async copy/move/rename/delete with undo/redo via `OperationHistory` |
| `automation.py` | `FileOrganizer` — organize by type/date, duplicate detection, `ConflictResolutionStrategy` |
| `config.py` | `ConfigManager` — reads/writes `~/.tfm/` (categories.yaml, config.yaml, recent.json) |
| `plugins/registry.py` | `PluginRegistry` (singleton) — loads `TFMPlugin` subclasses from `~/.tfm/plugins/` |
| `scheduler.py` | `TaskScheduler` — cron-based scheduling via `croniter` |
| `search.py` | `FileSearcher` — name pattern and content search |
| `tags.py` | `TagManager` — file tagging |
| `logger.py` | Central logging config |

All runtime state lives under `~/.tfm/`: `history.json` (undo/redo), `categories.yaml`, `config.yaml`, `recent.json`, `plugins/`.

## Key Conventions

### Logging
Use `get_logger(name)` from `logger.py` — returns a logger named `tfm.<name>`. Do **not** use `logging.getLogger(__name__)` directly in core modules.

### Exceptions
All custom exceptions extend `TFMError` (from `exceptions.py`). Public API raises `TFMPermissionError`, `TFMPathNotFoundError`, or `TFMOperationConflictError`.

### Async
- `FileOperations` methods are `async`; tests use `@pytest.mark.asyncio`.
- Textual background workers use `@work(thread=True)` from `textual`.

### Themes
Textual CSS files (`.tcss`) in `themes/`. `ConfigManager.get_theme()` returns the name; `FileManagerApp.load_theme_by_name()` loads the file.

### Testing
- Tests that instantiate `ConfigManager`, `OperationHistory`, or `PluginRegistry` **must** patch `pathlib.Path.home()` to `tmp_path` to avoid touching `~/.tfm`.
- `PluginRegistry` is a singleton — reset it between tests: `PluginRegistry._instance = None`.
- `FileOperations.__init__` touches `Path.home()`; tests redirect `file_ops.trash_dir` after construction.
- Benchmark files (`benchmark_*.py`) are not prefixed with `test_` and are not collected by pytest.

### Duplicate detection
Multi-stage in `automation.py`: group by size → partial hash (start/middle/end chunks) → full hash. Avoid bypassing the stages.

### CLI `--resolve` flag
`ConflictResolutionStrategy` supports `KEEP_NEWEST`, `KEEP_OLDEST`, `KEEP_LARGEST`, `KEEP_SMALLEST`, `INTERACTIVE`. The CLI `--resolve` argument maps string names to the enum.
