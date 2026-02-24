"""
Configuration management for TFM.
"""
try:
    import yaml
except ImportError:
    raise ImportError("PyYAML is required for configuration management. Please install it with `pip install PyYAML`.")

from pathlib import Path
from typing import Dict, List, Optional
from .logger import get_logger

logger = get_logger("config")

DEFAULT_CATEGORIES = {
    'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico'],
    'videos': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'],
    'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma'],
    'documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'],
    'spreadsheets': ['.xls', '.xlsx', '.csv', '.ods'],
    'presentations': ['.ppt', '.pptx', '.odp'],
    'archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
    'code': ['.py', '.js', '.java', '.c', '.cpp', '.h', '.html', '.css', '.sh'],
    'data': ['.json', '.xml', '.yaml', '.yml', '.sql', '.db'],
}

class ConfigManager:
    """Manages application configuration."""

    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            config_dir = Path.home() / ".tfm"
        self.config_dir = config_dir
        self.categories_file = self.config_dir / "categories.yaml"
        self.config_file = self.config_dir / "config.yaml"
        self.recent_file = self.config_dir / "recent.json"
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        """Ensure the configuration directory exists."""
        if not self.config_dir.exists():
            try:
                self.config_dir.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                logger.error(f"Failed to create config directory: {e}")

    def load_categories(self) -> Dict[str, List[str]]:
        """
        Load file categories from configuration file.
        Falls back to defaults if file doesn't exist or is invalid.
        """
        if not self.categories_file.exists():
            # Create default file if it doesn't exist so user can edit it
            self.save_categories(DEFAULT_CATEGORIES)
            return DEFAULT_CATEGORIES

        try:
            with open(self.categories_file, 'r') as f:
                categories = yaml.safe_load(f)

            if not isinstance(categories, dict):
                logger.warning("Invalid categories config format. Using defaults.")
                return DEFAULT_CATEGORIES

            return categories

        except (yaml.YAMLError, OSError) as e:
            logger.error(f"Error loading categories config: {e}")
            return DEFAULT_CATEGORIES

    def save_categories(self, categories: Dict[str, List[str]]) -> None:
        """Save categories to configuration file."""
        try:
            self._ensure_config_dir()
            with open(self.categories_file, 'w') as f:
                yaml.dump(categories, f, default_flow_style=False)
        except OSError as e:
            logger.error(f"Error saving categories config: {e}")

    def get_config_path(self) -> Path:
        return self.categories_file

    def load_config(self) -> Dict:
        """Load main configuration."""
        if not self.config_file.exists():
            return {"theme": "dark"}

        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
            return config if isinstance(config, dict) else {"theme": "dark"}
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {"theme": "dark"}

    def save_config(self, config: Dict) -> None:
        """Save main configuration."""
        try:
            self._ensure_config_dir()
            with open(self.config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def load_recent_dirs(self) -> List[Path]:
        """Load recent directories."""
        if not self.recent_file.exists():
            return []

        try:
            import json
            with open(self.recent_file, 'r') as f:
                data = json.load(f)
                return [Path(p) for p in data if Path(p).exists()]
        except Exception as e:
            logger.error(f"Error loading recent dirs: {e}")
            return []

    def save_recent_dirs(self, paths: List[Path]) -> None:
        """Save recent directories."""
        try:
            self._ensure_config_dir()
            import json
            # Keep only valid paths and limit to 5
            valid_paths = [str(p) for p in paths if p.exists()][:5]
            with open(self.recent_file, 'w') as f:
                json.dump(valid_paths, f)
        except Exception as e:
            logger.error(f"Error saving recent dirs: {e}")

    def add_recent_dir(self, path: Path) -> None:
        """Add a path to recent directories."""
        recents = self.load_recent_dirs()
        # Remove if exists to move to top
        if path in recents:
            recents.remove(path)
        recents.insert(0, path)
        self.save_recent_dirs(recents)
