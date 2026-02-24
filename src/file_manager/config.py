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
