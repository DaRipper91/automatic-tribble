import pytest
import yaml
from src.file_manager.config import ConfigManager, DEFAULT_CATEGORIES

class TestConfigManager:

    @pytest.fixture
    def config_dir(self, tmp_path):
        return tmp_path / ".tfm"

    @pytest.fixture
    def manager(self, config_dir):
        return ConfigManager(config_dir=config_dir)

    def test_load_defaults(self, manager, config_dir):
        # File shouldn't exist initially
        assert not (config_dir / "categories.yaml").exists()

        # Load should create default
        categories = manager.load_categories()
        assert categories == DEFAULT_CATEGORIES
        assert (config_dir / "categories.yaml").exists()

    def test_load_existing(self, manager, config_dir):
        custom_categories = {"custom": [".xyz"]}
        config_dir.mkdir(parents=True, exist_ok=True)
        with open(config_dir / "categories.yaml", "w") as f:
            yaml.dump(custom_categories, f)

        categories = manager.load_categories()
        assert categories == custom_categories

    def test_save_categories(self, manager, config_dir):
        custom_categories = {"custom": [".abc"]}
        manager.save_categories(custom_categories)

        with open(config_dir / "categories.yaml", "r") as f:
            loaded = yaml.safe_load(f)
        assert loaded == custom_categories

    def test_invalid_yaml(self, manager, config_dir):
        config_dir.mkdir(parents=True, exist_ok=True)
        # Create invalid yaml
        with open(config_dir / "categories.yaml", "w") as f:
            f.write("invalid: yaml: [")

        # Should fall back to defaults
        categories = manager.load_categories()
        assert categories == DEFAULT_CATEGORIES

    def test_get_config_path(self, manager, config_dir):
        assert manager.get_config_path() == config_dir / "categories.yaml"
