"""
Tests for the plugin system.
"""
from unittest.mock import patch
from pathlib import Path
from src.file_manager.plugins.base import TFMPlugin
from src.file_manager.plugins.registry import PluginRegistry

class TestPlugin(TFMPlugin):
    def __init__(self):
        self.added = []
        self.deleted = []
        self.organized = []
        self.searched = []

    def on_file_added(self, path: Path):
        self.added.append(path)

    def on_file_deleted(self, path: Path):
        self.deleted.append(path)

    def on_organize(self, source: Path, destination: Path):
        self.organized.append((source, destination))

    def on_search_complete(self, query: str, results: list):
        self.searched.append((query, results))

def test_registry_singleton(tmp_path):
    # Patch Path.home to use tmp_path
    with patch("pathlib.Path.home", return_value=tmp_path):
        # Reset singleton for test isolation
        PluginRegistry._instance = None

        reg1 = PluginRegistry()
        reg2 = PluginRegistry()
        assert reg1 is reg2
        assert reg1.plugins == reg2.plugins

def test_register_and_hooks(tmp_path):
    with patch("pathlib.Path.home", return_value=tmp_path):
        PluginRegistry._instance = None
        registry = PluginRegistry()

        plugin = TestPlugin()
        registry.register(plugin)

        # Test hooks
        p1 = Path("/a/b")
        registry.on_file_added(p1)
        assert plugin.added == [p1]

        registry.on_file_deleted(p1)
        assert plugin.deleted == [p1]

        p2 = Path("/c/d")
        registry.on_organize(p1, p2)
        assert plugin.organized == [(p1, p2)]

        registry.on_search_complete("test", [p1])
        assert plugin.searched == [("test", [p1])]

def test_load_plugins(tmp_path):
    with patch("pathlib.Path.home", return_value=tmp_path):
        PluginRegistry._instance = None
        registry = PluginRegistry()

        # Create a dummy plugin file
        plugin_dir = tmp_path / ".tfm" / "plugins"
        plugin_dir.mkdir(parents=True, exist_ok=True)

        plugin_code = """
from src.file_manager.plugins.base import TFMPlugin

class LoadedPlugin(TFMPlugin):
    pass
"""
        (plugin_dir / "my_plugin.py").write_text(plugin_code)

        # Mock sys.modules to avoid polluting global state, or just let it load
        # We need to make sure src.file_manager... is importable in the context of the loaded file
        # The test runner environment should handle this if PYTHONPATH is set.

        registry.load_plugins()

        # Should have loaded one plugin
        assert len(registry.plugins) == 1
        assert registry.plugins[0].__class__.__name__ == "LoadedPlugin"
