"""
Plugin registry for TFM.
"""
import sys
import importlib.util
from pathlib import Path
from typing import List, Optional
from .base import TFMPlugin
from ..logger import get_logger

logger = get_logger("plugins")

class PluginRegistry:
    """Singleton registry for TFM plugins."""

    _instance: Optional['PluginRegistry'] = None
    plugins: List[TFMPlugin]
    plugin_dir: Path

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PluginRegistry, cls).__new__(cls)
            cls._instance.plugins = []
            cls._instance.plugin_dir = Path.home() / ".tfm" / "plugins"
        return cls._instance

    def register(self, plugin: TFMPlugin) -> None:
        """Register a new plugin."""
        self.plugins.append(plugin)
        logger.info(f"Registered plugin: {plugin.name}")

    def load_plugins(self) -> None:
        """Load plugins from the plugin directory."""
        self.plugins.clear()
        if not self.plugin_dir.exists():
            try:
                self.plugin_dir.mkdir(parents=True, exist_ok=True)
            except OSError:
                return

        for plugin_file in self.plugin_dir.glob("*.py"):
            if plugin_file.name == "__init__.py":
                continue

            try:
                spec = importlib.util.spec_from_file_location(plugin_file.stem, plugin_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[spec.name] = module
                    spec.loader.exec_module(module)

                    # Find and register TFMPlugin subclasses
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and
                            issubclass(attr, TFMPlugin) and
                            attr is not TFMPlugin):
                            self.register(attr())
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_file}: {e}")

    # Hooks
    def on_file_added(self, path: Path) -> None:
        for plugin in self.plugins:
            try:
                plugin.on_file_added(path)
            except Exception as e:
                logger.error(f"Error in plugin {plugin.name}.on_file_added: {e}")

    def on_file_deleted(self, path: Path) -> None:
        for plugin in self.plugins:
            try:
                plugin.on_file_deleted(path)
            except Exception as e:
                logger.error(f"Error in plugin {plugin.name}.on_file_deleted: {e}")

    def on_organize(self, source: Path, destination: Path) -> None:
        for plugin in self.plugins:
            try:
                plugin.on_organize(source, destination)
            except Exception as e:
                logger.error(f"Error in plugin {plugin.name}.on_organize: {e}")

    def on_search_complete(self, query: str, results: List[Path]) -> None:
        for plugin in self.plugins:
            try:
                plugin.on_search_complete(query, results)
            except Exception as e:
                logger.error(f"Error in plugin {plugin.name}.on_search_complete: {e}")
