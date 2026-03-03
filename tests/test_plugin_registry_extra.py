from unittest.mock import patch
from src.file_manager.plugins.registry import PluginRegistry
from src.file_manager.plugins.base import TFMPlugin

class MockPlugin(TFMPlugin):
    def __init__(self):
        self.added = False
        self.deleted = False
        self.organized = False
        self.searched = False

    def on_file_added(self, path):
        self.added = True
    def on_file_deleted(self, path):
        self.deleted = True
    def on_organize(self, source, destination):
        self.organized = True
    def on_search_complete(self, query, results):
        self.searched = True

class FailingPlugin(TFMPlugin):
    def on_file_added(self, path):
        raise Exception("mock")
    def on_file_deleted(self, path):
        raise Exception("mock")
    def on_organize(self, source, destination):
        raise Exception("mock")
    def on_search_complete(self, query, results):
        raise Exception("mock")

def test_registry_hooks():
    registry = PluginRegistry()
    registry.plugins = []

    mp = MockPlugin()
    registry.register(mp)

    registry.on_file_added(None)
    assert mp.added

    registry.on_file_deleted(None)
    assert mp.deleted

    registry.on_organize(None, None)
    assert mp.organized

    registry.on_search_complete(None, None)
    assert mp.searched

def test_registry_hooks_exceptions():
    registry = PluginRegistry()
    registry.plugins = []

    fp = FailingPlugin()
    registry.register(fp)

    # Should catch exceptions
    registry.on_file_added(None)
    registry.on_file_deleted(None)
    registry.on_organize(None, None)
    registry.on_search_complete(None, None)

def test_load_plugins_oserror(tmp_path):
    registry = PluginRegistry()
    with patch("pathlib.Path.mkdir", side_effect=OSError("mock")):
        registry.plugin_dir = tmp_path / "missing_dir"
        registry.load_plugins()
