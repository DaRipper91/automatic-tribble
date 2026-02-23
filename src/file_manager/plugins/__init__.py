"""
Plugin system for TFM.
"""
from .base import TFMPlugin
from .registry import PluginRegistry

__all__ = ['TFMPlugin', 'PluginRegistry']
