"""
Configuration management for TFM.
"""
try:
    import yaml
except ImportError:
    raise ImportError("PyYAML is required for configuration management. Please install it with `pip install PyYAML`.")

import json
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

DEFAULT_CONFIG = {
    "theme": "dark"
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

    # Categories Logic
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

    # App Config Logic (Themes)
    def load_config(self) -> Dict:
        """Load general application config."""
        if not self.config_file.exists():
            self.save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG

        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
            if not isinstance(config, dict):
                return DEFAULT_CONFIG
            return config
        except (yaml.YAMLError, OSError) as e:
            logger.error(f"Error loading config: {e}")
            return DEFAULT_CONFIG

    def save_config(self, config: Dict) -> None:
        """Save general application config."""
        try:
            self._ensure_config_dir()
            with open(self.config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
        except OSError as e:
            logger.error(f"Error saving config: {e}")

    def get_theme(self) -> str:
        """Get the configured theme name."""
        config = self.load_config()
        return config.get("theme", "dark")

    def set_theme(self, theme_name: str) -> None:
        """Set the theme name."""
        config = self.load_config()
        config["theme"] = theme_name
        self.save_config(config)

    # Recent Directories Logic
    def get_recent_directories(self) -> List[str]:
        """Get list of recent directories."""
        if not self.recent_file.exists():
            return []

        try:
            with open(self.recent_file, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                return []
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Error loading recent directories: {e}")
            return []

    def add_recent_directory(self, path: str) -> None:
        """Add a directory to recent list (keeps last 5 unique)."""
        recent = self.get_recent_directories()
        path_str = str(Path(path).resolve())

        if path_str in recent:
            recent.remove(path_str)

        recent.insert(0, path_str)
        recent = recent[:5]

        try:
            self._ensure_config_dir()
            with open(self.recent_file, 'w') as f:
                json.dump(recent, f)
        except OSError as e:
            logger.error(f"Error saving recent directories: {e}")

    def get_config_path(self) -> Path:
        return self.categories_file
