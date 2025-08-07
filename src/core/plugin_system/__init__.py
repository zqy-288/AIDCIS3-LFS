"""
简化的插件系统
"""
from .interfaces import Plugin, UIPlugin, DataPlugin, HookablePlugin, PluginInfo, PluginState, IPlugin, PluginMetadata
from .manager import PluginManager, get_plugin_manager
from .lifecycle import PluginLifecycle
from .utils import PluginLoader, PluginValidator, PluginError

__all__ = [
    'Plugin',
    'UIPlugin', 
    'DataPlugin',
    'HookablePlugin',
    'PluginInfo',
    'PluginState',
    'IPlugin',
    'PluginMetadata',
    'PluginManager',
    'get_plugin_manager',
    'PluginLifecycle',
    'PluginLoader',
    'PluginValidator',
    'PluginError'
]