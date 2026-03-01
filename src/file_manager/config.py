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
        Merges user config with defaults.
        """
        if not self.categories_file.exists():
            # Create default file if it doesn't exist so user can edit it
            self.save_categories(DEFAULT_CATEGORIES)
            return DEFAULT_CATEGORIES

        try:
            with open(self.categories_file, 'r') as f:
                user_categories = yaml.safe_load(f)

            if not isinstance(user_categories, dict):
                logger.warning("Invalid categories config format. Using defaults.")
                return DEFAULT_CATEGORIES

            # Merge with defaults (user overrides default keys, keeps new keys)
            # Actually, standard behavior for categories usually is strict override or union?
            # Let's assume union: we start with defaults, update with user
            categories = DEFAULT_CATEGORIES.copy()
            categories.update(user_categories)
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

    def load_config(self) -> Dict:
        """Load general application configuration."""
        if not self.config_file.exists():
            default_config = {'theme': 'dark'}
            self.save_config(default_config)
            return default_config

        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)

            if not isinstance(config, dict):
                return {'theme': 'dark'}

            return config
        except (yaml.YAMLError, OSError) as e:
            logger.error(f"Error loading config: {e}")
            return {'theme': 'dark'}

    def save_config(self, config: Dict) -> None:
        """Save general application configuration."""
        try:
            self._ensure_config_dir()
            with open(self.config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
        except OSError as e:
            logger.error(f"Error saving config: {e}")

    def get_theme(self) -> str:
        """Get the configured theme name."""
        return self.load_config().get('theme', 'dark')

    def set_theme(self, theme_name: str) -> None:
        """Set the theme."""
        config = self.load_config()
        config['theme'] = theme_name
        self.save_config(config)

    def load_recent_dirs(self) -> List[str]:
        """Load recent directories."""
        recent_file = self.config_dir / "recent.json"
        if not recent_file.exists():
            return []
        try:
            import json
            with open(recent_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading recent dirs: {e}")
            return []

    def save_recent_dirs(self, dirs: List[str]) -> None:
        """Save recent directories."""
        recent_file = self.config_dir / "recent.json"
        try:
            self._ensure_config_dir()
            import json
            with open(recent_file, 'w') as f:
                json.dump(dirs, f)
        except Exception as e:
            logger.error(f"Error saving recent dirs: {e}")

    def add_recent_dir(self, path: str) -> None:
        """Add a directory to recent list (maintaining max 5)."""
        recents = self.load_recent_dirs()
        if path in recents:
            recents.remove(path)
        recents.insert(0, path)
        self.save_recent_dirs(recents[:5])

    def get_config_path(self) -> Path:
        return self.categories_file
