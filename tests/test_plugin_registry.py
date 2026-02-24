import pytest
from pathlib import Path
from unittest.mock import patch
from src.file_manager.plugins.registry import PluginRegistry
from src.file_manager.plugins.base import TFMPlugin

class MockPlugin(TFMPlugin):
    def __init__(self):
        self.added = []
        self.deleted = []

    def on_file_added(self, path: Path) -> None:
        self.added.append(path)

    def on_file_deleted(self, path: Path) -> None:
        self.deleted.append(path)

@pytest.fixture
def registry(tmp_path):
    # Reset singleton
    PluginRegistry._instance = None
    # Patch home to ensure isolation
    with patch("pathlib.Path.home", return_value=tmp_path):
        reg = PluginRegistry()
        # Ensure it uses tmp_path/.tfm/plugins
        assert reg.plugin_dir == tmp_path / ".tfm" / "plugins"
        yield reg
    # Cleanup
    PluginRegistry._instance = None

def test_singleton(registry):
    reg2 = PluginRegistry()
    assert reg2 is registry

def test_register_and_hooks(registry):
    plugin = MockPlugin()
    registry.register(plugin)

    path = Path("/test/file")
    registry.on_file_added(path)

    assert path in plugin.added

    registry.on_file_deleted(path)
    assert path in plugin.deleted

def test_load_plugins(registry, tmp_path):
    # Create a plugin file
    plugin_dir = registry.plugin_dir
    plugin_dir.mkdir(parents=True, exist_ok=True)

    plugin_code = """
from src.file_manager.plugins.base import TFMPlugin
from pathlib import Path

class LoadedPlugin(TFMPlugin):
    def on_file_added(self, path: Path) -> None:
        print(f"Loaded: {path}")
"""
    (plugin_dir / "my_plugin.py").write_text(plugin_code)

    # Reload plugins
    registry.load_plugins()

    assert len(registry.plugins) == 1
    assert registry.plugins[0].__class__.__name__ == "LoadedPlugin"

def test_load_plugins_error_handling(registry, tmp_path):
    plugin_dir = registry.plugin_dir
    plugin_dir.mkdir(parents=True, exist_ok=True)

    # Create invalid plugin
    (plugin_dir / "bad_plugin.py").write_text("import non_existent_module")

    # Should not crash
    registry.load_plugins()
    # It might log an error but shouldn't crash
    # The valid plugin from previous test is gone because we cleared plugins list in load_plugins
    # Wait, load_plugins() clears self.plugins.
    assert len(registry.plugins) == 0
