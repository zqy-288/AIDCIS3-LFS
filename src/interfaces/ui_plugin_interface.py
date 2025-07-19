"""
UI插件接口定义
为UI组件提供标准化的插件接口，支持组件的热插拔和动态扩展
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable, Union
from enum import Enum
from dataclasses import dataclass

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QObject, Signal

try:
    from ..core.plugin_manager import IPlugin, PluginMetadata, PluginState
    from ..modules.ui_component_base import UIComponentBase, ComponentState
except ImportError:
    # 从项目根目录运行时的导入路径
    from core.plugin_manager import IPlugin, PluginMetadata, PluginState
    from modules.ui_component_base import UIComponentBase, ComponentState


class UIPluginType(Enum):
    """UI插件类型枚举"""
    WIDGET = "widget"              # 独立的UI组件
    THEME = "theme"                # 主题插件
    TOOL = "tool"                  # 工具插件
    PANEL = "panel"                # 面板插件
    DIALOG = "dialog"              # 对话框插件
    TOOLBAR = "toolbar"            # 工具栏插件
    MENU = "menu"                  # 菜单插件
    STATUSBAR = "statusbar"        # 状态栏插件
    DOCK = "dock"                  # 停靠窗口插件


class UIPluginCapability(Enum):
    """UI插件能力枚举"""
    CONFIGURABLE = "configurable"     # 可配置
    THEMEABLE = "themeable"           # 支持主题
    RESIZABLE = "resizable"           # 可调整大小
    DOCKABLE = "dockable"             # 可停靠
    MODAL = "modal"                   # 模态显示
    CONTEXT_MENU = "context_menu"     # 支持右键菜单
    DRAG_DROP = "drag_drop"           # 支持拖放
    HOTKEY = "hotkey"                 # 支持快捷键


@dataclass
class UIPluginMetadata(PluginMetadata):
    """UI插件元数据扩展"""
    ui_type: UIPluginType = UIPluginType.WIDGET
    capabilities: List[UIPluginCapability] = None
    default_position: str = "center"  # center, left, right, top, bottom
    icon: Optional[str] = None
    menu_text: Optional[str] = None
    tooltip: Optional[str] = None
    shortcut: Optional[str] = None
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []


class IUIPlugin(IPlugin):
    """UI插件基础接口
    
    继承自IPlugin，为UI组件提供额外的接口定义
    """
    
    def __init__(self, metadata: UIPluginMetadata):
        super().__init__(metadata)
        self._ui_metadata = metadata
        self._widget: Optional[QWidget] = None
        self._ui_ready = False
    
    @property
    def ui_metadata(self) -> UIPluginMetadata:
        """获取UI插件元数据"""
        return self._ui_metadata
    
    @property
    def widget(self) -> Optional[QWidget]:
        """获取主要UI组件"""
        return self._widget
    
    @property
    def is_ui_ready(self) -> bool:
        """检查UI是否就绪"""
        return self._ui_ready
    
    @abstractmethod
    def create_widget(self, parent: Optional[QWidget] = None) -> QWidget:
        """创建UI组件
        
        Args:
            parent: 父组件
            
        Returns:
            创建的UI组件
        """
        pass
    
    @abstractmethod
    def destroy_widget(self) -> bool:
        """销毁UI组件
        
        Returns:
            是否成功销毁
        """
        pass
    
    def get_widget_size_hint(self) -> tuple:
        """获取组件大小建议
        
        Returns:
            (width, height) 元组
        """
        if self._widget:
            size_hint = self._widget.sizeHint()
            return (size_hint.width(), size_hint.height())
        return (300, 200)  # 默认大小
    
    def get_widget_minimum_size(self) -> tuple:
        """获取组件最小大小
        
        Returns:
            (width, height) 元组
        """
        if self._widget:
            min_size = self._widget.minimumSize()
            return (min_size.width(), min_size.height())
        return (100, 50)  # 默认最小大小
    
    def configure_widget(self, config: Dict[str, Any]) -> bool:
        """配置UI组件
        
        Args:
            config: 配置字典
            
        Returns:
            是否配置成功
        """
        return True
    
    def apply_theme(self, theme_data: Dict[str, Any]) -> bool:
        """应用主题
        
        Args:
            theme_data: 主题数据
            
        Returns:
            是否应用成功
        """
        return True
    
    def handle_context_menu(self, position) -> bool:
        """处理右键菜单
        
        Args:
            position: 菜单位置
            
        Returns:
            是否处理成功
        """
        return False
    
    def serialize_state(self) -> Dict[str, Any]:
        """序列化UI状态
        
        Returns:
            序列化的状态数据
        """
        return {}
    
    def restore_state(self, state: Dict[str, Any]) -> bool:
        """恢复UI状态
        
        Args:
            state: 状态数据
            
        Returns:
            是否恢复成功
        """
        return True
    
    def get_ui_status(self) -> Dict[str, Any]:
        """获取UI状态信息"""
        status = super().get_status()
        status.update({
            'ui_type': self._ui_metadata.ui_type.value,
            'capabilities': [cap.value for cap in self._ui_metadata.capabilities],
            'ui_ready': self._ui_ready,
            'has_widget': self._widget is not None,
            'widget_visible': self._widget.isVisible() if self._widget else False
        })
        return status


class IUIThemePlugin(IUIPlugin):
    """UI主题插件接口"""
    
    @abstractmethod
    def get_theme_name(self) -> str:
        """获取主题名称"""
        pass
    
    @abstractmethod
    def get_theme_colors(self) -> Dict[str, str]:
        """获取主题颜色配置"""
        pass
    
    @abstractmethod
    def get_stylesheet(self) -> str:
        """获取样式表"""
        pass
    
    @abstractmethod
    def apply_to_widget(self, widget: QWidget) -> bool:
        """应用主题到指定组件"""
        pass


class IUIToolPlugin(IUIPlugin):
    """UI工具插件接口"""
    
    @abstractmethod
    def get_tool_name(self) -> str:
        """获取工具名称"""
        pass
    
    @abstractmethod
    def get_tool_icon(self) -> str:
        """获取工具图标路径"""
        pass
    
    @abstractmethod
    def execute_tool(self, context: Dict[str, Any] = None) -> Any:
        """执行工具功能"""
        pass


class IUIDialogPlugin(IUIPlugin):
    """UI对话框插件接口"""
    
    @abstractmethod
    def show_dialog(self, parent: Optional[QWidget] = None, **kwargs) -> Any:
        """显示对话框"""
        pass
    
    @abstractmethod
    def get_dialog_result(self) -> Any:
        """获取对话框结果"""
        pass


class UIPluginEvent:
    """UI插件事件"""
    
    def __init__(self, event_type: str, plugin_name: str, data: Dict[str, Any] = None):
        self.event_type = event_type
        self.plugin_name = plugin_name
        self.data = data or {}
        self.timestamp = None
    
    def __str__(self):
        return f"UIPluginEvent({self.event_type}, {self.plugin_name})"


class UIPluginRegistry:
    """UI插件注册表
    
    管理UI插件的注册、查找和生命周期
    """
    
    def __init__(self):
        self._plugins: Dict[str, IUIPlugin] = {}
        self._plugins_by_type: Dict[UIPluginType, List[IUIPlugin]] = {}
        self._event_handlers: Dict[str, List[Callable]] = {}
        
        # 初始化插件类型分组
        for plugin_type in UIPluginType:
            self._plugins_by_type[plugin_type] = []
    
    def register_plugin(self, plugin: IUIPlugin) -> bool:
        """注册UI插件"""
        try:
            plugin_name = plugin.metadata.name
            
            # 检查是否已注册
            if plugin_name in self._plugins:
                return False
            
            # 注册插件
            self._plugins[plugin_name] = plugin
            
            # 按类型分组
            plugin_type = plugin.ui_metadata.ui_type
            self._plugins_by_type[plugin_type].append(plugin)
            
            # 触发注册事件
            self._trigger_event("plugin_registered", plugin_name, {"plugin": plugin})
            
            return True
            
        except Exception:
            return False
    
    def unregister_plugin(self, plugin_name: str) -> bool:
        """注销UI插件"""
        try:
            if plugin_name not in self._plugins:
                return False
            
            plugin = self._plugins[plugin_name]
            
            # 从类型分组中移除
            plugin_type = plugin.ui_metadata.ui_type
            if plugin in self._plugins_by_type[plugin_type]:
                self._plugins_by_type[plugin_type].remove(plugin)
            
            # 注销插件
            del self._plugins[plugin_name]
            
            # 触发注销事件
            self._trigger_event("plugin_unregistered", plugin_name, {"plugin": plugin})
            
            return True
            
        except Exception:
            return False
    
    def get_plugin(self, plugin_name: str) -> Optional[IUIPlugin]:
        """获取UI插件"""
        return self._plugins.get(plugin_name)
    
    def get_plugins_by_type(self, plugin_type: UIPluginType) -> List[IUIPlugin]:
        """按类型获取UI插件列表"""
        return self._plugins_by_type.get(plugin_type, []).copy()
    
    def get_plugins_by_capability(self, capability: UIPluginCapability) -> List[IUIPlugin]:
        """按能力获取UI插件列表"""
        result = []
        for plugin in self._plugins.values():
            if capability in plugin.ui_metadata.capabilities:
                result.append(plugin)
        return result
    
    def list_plugins(self) -> List[str]:
        """列出所有UI插件名称"""
        return list(self._plugins.keys())
    
    def list_plugin_types(self) -> List[UIPluginType]:
        """列出所有已注册的插件类型"""
        return [ptype for ptype, plugins in self._plugins_by_type.items() if plugins]
    
    def subscribe_event(self, event_type: str, handler: Callable):
        """订阅UI插件事件"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
    
    def unsubscribe_event(self, event_type: str, handler: Callable):
        """取消订阅UI插件事件"""
        if event_type in self._event_handlers:
            try:
                self._event_handlers[event_type].remove(handler)
            except ValueError:
                pass
    
    def _trigger_event(self, event_type: str, plugin_name: str, data: Dict[str, Any] = None):
        """触发UI插件事件"""
        event = UIPluginEvent(event_type, plugin_name, data)
        handlers = self._event_handlers.get(event_type, [])
        
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                pass  # 忽略事件处理错误
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """获取注册表统计信息"""
        stats = {
            'total_plugins': len(self._plugins),
            'plugins_by_type': {},
            'plugins_by_capability': {}
        }
        
        # 按类型统计
        for plugin_type, plugins in self._plugins_by_type.items():
            stats['plugins_by_type'][plugin_type.value] = len(plugins)
        
        # 按能力统计
        capability_counts = {}
        for plugin in self._plugins.values():
            for capability in plugin.ui_metadata.capabilities:
                cap_name = capability.value
                capability_counts[cap_name] = capability_counts.get(cap_name, 0) + 1
        
        stats['plugins_by_capability'] = capability_counts
        
        return stats


# 全局UI插件注册表实例
_ui_plugin_registry: Optional[UIPluginRegistry] = None


def get_ui_plugin_registry() -> UIPluginRegistry:
    """获取全局UI插件注册表"""
    global _ui_plugin_registry
    if _ui_plugin_registry is None:
        _ui_plugin_registry = UIPluginRegistry()
    return _ui_plugin_registry


def register_ui_plugin(plugin: IUIPlugin) -> bool:
    """注册UI插件到全局注册表"""
    registry = get_ui_plugin_registry()
    return registry.register_plugin(plugin)


def unregister_ui_plugin(plugin_name: str) -> bool:
    """从全局注册表注销UI插件"""
    registry = get_ui_plugin_registry()
    return registry.unregister_plugin(plugin_name)


def get_ui_plugin(plugin_name: str) -> Optional[IUIPlugin]:
    """从全局注册表获取UI插件"""
    registry = get_ui_plugin_registry()
    return registry.get_plugin(plugin_name)


def list_ui_plugins_by_type(plugin_type: UIPluginType) -> List[IUIPlugin]:
    """按类型列出UI插件"""
    registry = get_ui_plugin_registry()
    return registry.get_plugins_by_type(plugin_type)


def list_ui_plugins_by_capability(capability: UIPluginCapability) -> List[IUIPlugin]:
    """按能力列出UI插件"""
    registry = get_ui_plugin_registry()
    return registry.get_plugins_by_capability(capability)