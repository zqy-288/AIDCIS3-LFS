"""
插件系统核心接口定义
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List, Protocol
from PySide6.QtWidgets import QWidget


class PluginState(Enum):
    """插件状态"""
    UNLOADED = "unloaded"
    LOADED = "loaded"
    INITIALIZED = "initialized"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class PluginInfo:
    """插件信息"""
    name: str
    version: str
    author: str
    description: str
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class Plugin(Protocol):
    """基础插件协议"""
    
    @abstractmethod
    def get_info(self) -> PluginInfo:
        """获取插件信息"""
        pass
    
    @abstractmethod
    def initialize(self) -> None:
        """初始化插件"""
        pass
    
    @abstractmethod
    def start(self) -> None:
        """启动插件"""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """停止插件"""
        pass
    
    def get_config_widget(self) -> Optional[QWidget]:
        """获取配置界面（可选）"""
        return None


class UIPlugin(Plugin):
    """UI插件接口"""
    
    @abstractmethod
    def get_menu_actions(self) -> List[Dict[str, Any]]:
        """获取菜单项"""
        pass
    
    @abstractmethod
    def get_toolbar_actions(self) -> List[Dict[str, Any]]:
        """获取工具栏项"""
        pass
    
    def get_dock_widget(self) -> Optional[QWidget]:
        """获取停靠窗口（可选）"""
        return None


class DataPlugin(Plugin):
    """数据处理插件接口"""
    
    @abstractmethod
    def process_data(self, data: Any) -> Any:
        """处理数据"""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """获取支持的数据格式"""
        pass


class HookablePlugin(Plugin):
    """支持钩子的插件接口"""
    
    def before_process(self, context: Dict[str, Any]) -> None:
        """处理前钩子"""
        pass
    
    def after_process(self, context: Dict[str, Any], result: Any) -> Any:
        """处理后钩子"""
        return result
    
    def on_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """错误处理钩子"""
        pass


# 别名以保持向后兼容性
IPlugin = Plugin
PluginMetadata = PluginInfo