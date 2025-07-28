"""
UI插件加载器
基于核心插件管理器，专门负责UI插件的加载、管理和热重载
"""

import os
import sys
import time
import json
import weakref
import threading
from typing import Dict, List, Any, Optional, Callable, Type, Union, Set
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
import logging

from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import QObject, Signal, QTimer

try:
    from ..core.plugin_system.manager import PluginManager, IPlugin, PluginMetadata, PluginState, PluginLoadResult
    from ..core.dependency_injection import DependencyContainer, injectable, ServiceLifetime
    from ..core.application import EventBus, ApplicationEvent
    from ..interfaces.ui_plugin_interface import (
        IUIPlugin, UIPluginMetadata, UIPluginType, UIPluginCapability,
        UIPluginRegistry, get_ui_plugin_registry
    )
    from ..modules.ui_component_base import UIComponentBase, ComponentState, ui_component_manager
except ImportError:
    # 从项目根目录运行时的导入路径
    from core.plugin_system.manager import PluginManager, IPlugin, PluginMetadata, PluginState, PluginLoadResult
    from core.dependency_injection import DependencyContainer, injectable, ServiceLifetime
    from core.application import EventBus, ApplicationEvent
    from interfaces.ui_plugin_interface import (
        IUIPlugin, UIPluginMetadata, UIPluginType, UIPluginCapability,
        UIPluginRegistry, get_ui_plugin_registry
    )
    from src.modules.ui_component_base import UIComponentBase, ComponentState, ui_component_manager


class UIPluginLoadError(Exception):
    """UI插件加载错误"""
    pass


class UIPluginEvent(QObject):
    """UI插件事件信号"""
    plugin_loaded = Signal(str)        # 插件已加载
    plugin_unloaded = Signal(str)      # 插件已卸载
    plugin_started = Signal(str)       # 插件已启动
    plugin_stopped = Signal(str)       # 插件已停止
    plugin_error = Signal(str, str)    # 插件错误 (name, error)
    widget_created = Signal(str, QWidget)  # 组件已创建
    widget_destroyed = Signal(str)     # 组件已销毁


@dataclass
class UIPluginLoadResult:
    """UI插件加载结果"""
    success: bool
    plugin: Optional[IUIPlugin] = None
    widget: Optional[QWidget] = None
    error: Optional[str] = None
    load_time: float = 0.0


class UIPluginContainer:
    """UI插件容器，管理插件的UI组件"""
    
    def __init__(self, plugin: IUIPlugin):
        self.plugin = plugin
        self.widget: Optional[QWidget] = None
        self.parent_widget: Optional[QWidget] = None
        self.is_visible = False
        self.position = plugin.ui_metadata.default_position
        self.state = {}
        self.created_at = time.time()
        self.last_accessed = time.time()
    
    def create_widget(self, parent: Optional[QWidget] = None) -> bool:
        """创建UI组件"""
        try:
            if self.widget is not None:
                return True
            
            self.widget = self.plugin.create_widget(parent)
            self.parent_widget = parent
            self.last_accessed = time.time()
            
            return self.widget is not None
            
        except Exception as e:
            logging.error(f"Failed to create widget for plugin {self.plugin.metadata.name}: {e}")
            return False
    
    def destroy_widget(self) -> bool:
        """销毁UI组件"""
        try:
            if self.widget is None:
                return True
            
            # 保存状态
            if hasattr(self.plugin, 'serialize_state'):
                self.state = self.plugin.serialize_state()
            
            # 销毁组件
            success = self.plugin.destroy_widget()
            
            if success:
                if self.widget:
                    self.widget.deleteLater()
                self.widget = None
                self.parent_widget = None
                self.is_visible = False
            
            return success
            
        except Exception as e:
            logging.error(f"Failed to destroy widget for plugin {self.plugin.metadata.name}: {e}")
            return False
    
    def show_widget(self) -> bool:
        """显示UI组件"""
        try:
            if self.widget is None:
                return False
            
            self.widget.show()
            self.is_visible = True
            self.last_accessed = time.time()
            
            return True
            
        except Exception:
            return False
    
    def hide_widget(self) -> bool:
        """隐藏UI组件"""
        try:
            if self.widget is None:
                return True
            
            self.widget.hide()
            self.is_visible = False
            
            return True
            
        except Exception:
            return False
    
    def configure_widget(self, config: Dict[str, Any]) -> bool:
        """配置UI组件"""
        try:
            if hasattr(self.plugin, 'configure_widget'):
                return self.plugin.configure_widget(config)
            return True
            
        except Exception:
            return False
    
    def apply_theme(self, theme_data: Dict[str, Any]) -> bool:
        """应用主题"""
        try:
            if hasattr(self.plugin, 'apply_theme'):
                return self.plugin.apply_theme(theme_data)
            return True
            
        except Exception:
            return False


@injectable(ServiceLifetime.SINGLETON)
class UIPluginLoader(UIComponentBase):
    """UI插件加载器
    
    专门负责UI插件的加载、管理和生命周期控制
    """
    
    # Qt信号定义
    plugin_loaded = Signal(str)
    plugin_unloaded = Signal(str)
    plugin_started = Signal(str)
    plugin_stopped = Signal(str)
    plugin_error = Signal(str, str)
    widget_created = Signal(str, QWidget)
    widget_destroyed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 依赖注入
        self.declare_dependency("plugin_manager", PluginManager, required=True)
        self.declare_dependency("event_bus", EventBus, required=False)
        
        # UI插件注册表
        self._ui_registry = get_ui_plugin_registry()
        
        # UI插件容器
        self._plugin_containers: Dict[str, UIPluginContainer] = {}
        
        # 位置管理器
        self._position_managers: Dict[str, List[str]] = {
            "center": [],
            "left": [],
            "right": [],
            "top": [],
            "bottom": []
        }
        
        # 主题管理
        self._current_theme: Optional[Dict[str, Any]] = None
        self._theme_plugins: Dict[str, IUIPlugin] = {}
        
        # 热重载支持
        self._hot_reload_enabled = True
        self._file_watchers: Dict[str, Any] = {}
        
        # 清理定时器
        self._cleanup_timer = QTimer()
        self._cleanup_timer.timeout.connect(self._cleanup_unused_widgets)
        
        # 性能监控
        self._load_times: Dict[str, float] = {}
        self._widget_creation_times: Dict[str, float] = {}
        
        print(f"🔌 UI插件加载器已创建: {self.component_id}")
    
    def _do_initialize(self) -> bool:
        """初始化UI插件加载器"""
        try:
            # 设置UI插件注册表事件监听
            self._ui_registry.subscribe_event("plugin_registered", self._on_ui_plugin_registered)
            self._ui_registry.subscribe_event("plugin_unregistered", self._on_ui_plugin_unregistered)
            
            # 启动清理定时器
            self._cleanup_timer.start(60000)  # 每分钟清理一次
            
            print("✅ UI插件加载器初始化完成")
            return True
            
        except Exception as e:
            print(f"❌ UI插件加载器初始化失败: {e}")
            return False
    
    def _do_start(self) -> bool:
        """启动UI插件加载器"""
        try:
            # 获取核心插件管理器
            plugin_manager = self.get_dependency("plugin_manager")
            if not plugin_manager:
                print("❌ 无法获取核心插件管理器")
                return False
            
            # 扫描并加载UI插件
            self._scan_and_load_ui_plugins(plugin_manager)
            
            print("✅ UI插件加载器启动完成")
            return True
            
        except Exception as e:
            print(f"❌ UI插件加载器启动失败: {e}")
            return False
    
    def _do_stop(self) -> bool:
        """停止UI插件加载器"""
        try:
            # 停止所有UI插件
            self.stop_all_ui_plugins()
            
            # 停止清理定时器
            self._cleanup_timer.stop()
            
            print("✅ UI插件加载器停止完成")
            return True
            
        except Exception as e:
            print(f"❌ UI插件加载器停止失败: {e}")
            return False
    
    def _do_cleanup(self) -> bool:
        """清理UI插件加载器资源"""
        try:
            # 销毁所有UI组件
            for container in list(self._plugin_containers.values()):
                container.destroy_widget()
            
            # 清理容器
            self._plugin_containers.clear()
            self._position_managers.clear()
            self._theme_plugins.clear()
            
            # 停止定时器
            if self._cleanup_timer:
                self._cleanup_timer.stop()
                self._cleanup_timer.deleteLater()
                self._cleanup_timer = None
            
            print("✅ UI插件加载器清理完成")
            return True
            
        except Exception as e:
            print(f"❌ UI插件加载器清理失败: {e}")
            return False
    
    def _scan_and_load_ui_plugins(self, plugin_manager: PluginManager):
        """扫描并加载UI插件"""
        try:
            # 获取所有插件元数据
            all_plugins = plugin_manager.list_plugins()
            
            for plugin_name in all_plugins:
                metadata = plugin_manager.get_plugin_metadata(plugin_name)
                if metadata and metadata.plugin_type.value == "ui_component":
                    # 尝试加载UI插件
                    self.load_ui_plugin(plugin_name)
            
        except Exception as e:
            print(f"⚠️ 扫描UI插件时发生错误: {e}")
    
    def load_ui_plugin(self, plugin_name: str) -> UIPluginLoadResult:
        """加载UI插件"""
        start_time = time.time()
        
        try:
            # 检查是否已加载
            if plugin_name in self._plugin_containers:
                return UIPluginLoadResult(
                    success=False,
                    error=f"UI plugin {plugin_name} is already loaded"
                )
            
            # 从核心插件管理器加载插件
            plugin_manager = self.get_dependency("plugin_manager")
            if not plugin_manager:
                return UIPluginLoadResult(
                    success=False,
                    error="Plugin manager not available"
                )
            
            # 加载基础插件
            base_result = plugin_manager.load_plugin(plugin_name)
            if not base_result.success:
                return UIPluginLoadResult(
                    success=False,
                    error=f"Failed to load base plugin: {base_result.error}"
                )
            
            # 获取插件实例
            plugin = plugin_manager.get_plugin(plugin_name)
            if not plugin:
                return UIPluginLoadResult(
                    success=False,
                    error="Plugin instance not found"
                )
            
            # 验证是否为UI插件
            if not isinstance(plugin, IUIPlugin):
                return UIPluginLoadResult(
                    success=False,
                    error=f"Plugin {plugin_name} is not a UI plugin"
                )
            
            # 创建UI插件容器
            container = UIPluginContainer(plugin)
            self._plugin_containers[plugin_name] = container
            
            # 注册到UI插件注册表
            self._ui_registry.register_plugin(plugin)
            
            # 按位置分组
            position = plugin.ui_metadata.default_position
            if position in self._position_managers:
                self._position_managers[position].append(plugin_name)
            
            # 如果是主题插件，特殊处理
            if plugin.ui_metadata.ui_type == UIPluginType.THEME:
                self._theme_plugins[plugin_name] = plugin
            
            load_time = time.time() - start_time
            self._load_times[plugin_name] = load_time
            
            print(f"✅ UI插件 {plugin_name} 加载成功，耗时 {load_time:.3f}秒")
            
            # 发射信号
            self.plugin_loaded.emit(plugin_name)
            
            return UIPluginLoadResult(
                success=True,
                plugin=plugin,
                load_time=load_time
            )
            
        except Exception as e:
            load_time = time.time() - start_time
            error_msg = f"Failed to load UI plugin {plugin_name}: {e}"
            
            print(f"❌ {error_msg}")
            
            # 发射错误信号
            self.plugin_error.emit(plugin_name, error_msg)
            
            return UIPluginLoadResult(
                success=False,
                error=error_msg,
                load_time=load_time
            )
    
    def unload_ui_plugin(self, plugin_name: str) -> bool:
        """卸载UI插件"""
        try:
            if plugin_name not in self._plugin_containers:
                return True
            
            container = self._plugin_containers[plugin_name]
            
            # 销毁UI组件
            container.destroy_widget()
            
            # 从位置管理器中移除
            for position_list in self._position_managers.values():
                if plugin_name in position_list:
                    position_list.remove(plugin_name)
            
            # 从主题插件中移除
            if plugin_name in self._theme_plugins:
                del self._theme_plugins[plugin_name]
            
            # 从UI注册表中注销
            self._ui_registry.unregister_plugin(plugin_name)
            
            # 从核心插件管理器卸载
            plugin_manager = self.get_dependency("plugin_manager")
            if plugin_manager:
                plugin_manager.unload_plugin(plugin_name)
            
            # 移除容器
            del self._plugin_containers[plugin_name]
            
            print(f"✅ UI插件 {plugin_name} 卸载成功")
            
            # 发射信号
            self.plugin_unloaded.emit(plugin_name)
            
            return True
            
        except Exception as e:
            print(f"❌ 卸载UI插件 {plugin_name} 失败: {e}")
            self.plugin_error.emit(plugin_name, str(e))
            return False
    
    def start_ui_plugin(self, plugin_name: str) -> bool:
        """启动UI插件"""
        try:
            if plugin_name not in self._plugin_containers:
                return False
            
            container = self._plugin_containers[plugin_name]
            plugin = container.plugin
            
            # 启动基础插件
            plugin_manager = self.get_dependency("plugin_manager")
            if plugin_manager:
                if not plugin_manager.start_plugin(plugin_name):
                    return False
            
            print(f"✅ UI插件 {plugin_name} 启动成功")
            
            # 发射信号
            self.plugin_started.emit(plugin_name)
            
            return True
            
        except Exception as e:
            print(f"❌ 启动UI插件 {plugin_name} 失败: {e}")
            self.plugin_error.emit(plugin_name, str(e))
            return False
    
    def stop_ui_plugin(self, plugin_name: str) -> bool:
        """停止UI插件"""
        try:
            if plugin_name not in self._plugin_containers:
                return True
            
            container = self._plugin_containers[plugin_name]
            
            # 隐藏UI组件
            container.hide_widget()
            
            # 停止基础插件
            plugin_manager = self.get_dependency("plugin_manager")
            if plugin_manager:
                plugin_manager.stop_plugin(plugin_name)
            
            print(f"✅ UI插件 {plugin_name} 停止成功")
            
            # 发射信号
            self.plugin_stopped.emit(plugin_name)
            
            return True
            
        except Exception as e:
            print(f"❌ 停止UI插件 {plugin_name} 失败: {e}")
            self.plugin_error.emit(plugin_name, str(e))
            return False
    
    def create_plugin_widget(self, plugin_name: str, parent: Optional[QWidget] = None) -> Optional[QWidget]:
        """创建插件UI组件"""
        start_time = time.time()
        
        try:
            if plugin_name not in self._plugin_containers:
                return None
            
            container = self._plugin_containers[plugin_name]
            
            # 创建UI组件
            if container.create_widget(parent):
                widget = container.widget
                
                # 应用当前主题
                if self._current_theme:
                    container.apply_theme(self._current_theme)
                
                creation_time = time.time() - start_time
                self._widget_creation_times[plugin_name] = creation_time
                
                print(f"✅ 插件 {plugin_name} UI组件创建成功，耗时 {creation_time:.3f}秒")
                
                # 发射信号
                self.widget_created.emit(plugin_name, widget)
                
                return widget
            
            return None
            
        except Exception as e:
            print(f"❌ 创建插件 {plugin_name} UI组件失败: {e}")
            self.plugin_error.emit(plugin_name, str(e))
            return None
    
    def destroy_plugin_widget(self, plugin_name: str) -> bool:
        """销毁插件UI组件"""
        try:
            if plugin_name not in self._plugin_containers:
                return True
            
            container = self._plugin_containers[plugin_name]
            
            if container.destroy_widget():
                print(f"✅ 插件 {plugin_name} UI组件销毁成功")
                
                # 发射信号
                self.widget_destroyed.emit(plugin_name)
                
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ 销毁插件 {plugin_name} UI组件失败: {e}")
            return False
    
    def show_plugin_widget(self, plugin_name: str) -> bool:
        """显示插件UI组件"""
        try:
            if plugin_name not in self._plugin_containers:
                return False
            
            container = self._plugin_containers[plugin_name]
            return container.show_widget()
            
        except Exception:
            return False
    
    def hide_plugin_widget(self, plugin_name: str) -> bool:
        """隐藏插件UI组件"""
        try:
            if plugin_name not in self._plugin_containers:
                return True
            
            container = self._plugin_containers[plugin_name]
            return container.hide_widget()
            
        except Exception:
            return False
    
    def get_plugin_widget(self, plugin_name: str) -> Optional[QWidget]:
        """获取插件UI组件"""
        if plugin_name in self._plugin_containers:
            return self._plugin_containers[plugin_name].widget
        return None
    
    def list_ui_plugins(self) -> List[str]:
        """列出所有UI插件"""
        return list(self._plugin_containers.keys())
    
    def list_plugins_by_position(self, position: str) -> List[str]:
        """按位置列出插件"""
        return self._position_managers.get(position, []).copy()
    
    def list_plugins_by_type(self, plugin_type: UIPluginType) -> List[str]:
        """按类型列出插件"""
        result = []
        for plugin_name, container in self._plugin_containers.items():
            if container.plugin.ui_metadata.ui_type == plugin_type:
                result.append(plugin_name)
        return result
    
    def apply_theme_to_all(self, theme_data: Dict[str, Any]):
        """为所有插件应用主题"""
        self._current_theme = theme_data
        
        for plugin_name, container in self._plugin_containers.items():
            try:
                container.apply_theme(theme_data)
            except Exception as e:
                print(f"⚠️ 为插件 {plugin_name} 应用主题失败: {e}")
    
    def configure_plugin(self, plugin_name: str, config: Dict[str, Any]) -> bool:
        """配置插件"""
        try:
            if plugin_name not in self._plugin_containers:
                return False
            
            container = self._plugin_containers[plugin_name]
            return container.configure_widget(config)
            
        except Exception:
            return False
    
    def get_plugin_status(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """获取插件状态"""
        if plugin_name not in self._plugin_containers:
            return None
        
        container = self._plugin_containers[plugin_name]
        plugin = container.plugin
        
        status = plugin.get_ui_status()
        status.update({
            'widget_created': container.widget is not None,
            'widget_visible': container.is_visible,
            'position': container.position,
            'created_at': container.created_at,
            'last_accessed': container.last_accessed
        })
        
        return status
    
    def reload_ui_plugin(self, plugin_name: str) -> bool:
        """重新加载UI插件（热重载）"""
        try:
            if not self._hot_reload_enabled:
                return False
            
            # 保存当前状态
            was_visible = False
            widget_parent = None
            
            if plugin_name in self._plugin_containers:
                container = self._plugin_containers[plugin_name]
                was_visible = container.is_visible
                if container.widget:
                    widget_parent = container.widget.parent()
            
            # 卸载插件
            if not self.unload_ui_plugin(plugin_name):
                return False
            
            # 重新加载插件
            result = self.load_ui_plugin(plugin_name)
            if not result.success:
                return False
            
            # 启动插件
            if not self.start_ui_plugin(plugin_name):
                return False
            
            # 恢复UI状态
            if was_visible:
                self.create_plugin_widget(plugin_name, widget_parent)
                self.show_plugin_widget(plugin_name)
            
            print(f"🔄 UI插件 {plugin_name} 热重载成功")
            return True
            
        except Exception as e:
            print(f"❌ UI插件 {plugin_name} 热重载失败: {e}")
            return False
    
    def stop_all_ui_plugins(self):
        """停止所有UI插件"""
        for plugin_name in list(self._plugin_containers.keys()):
            self.stop_ui_plugin(plugin_name)
    
    def _cleanup_unused_widgets(self):
        """清理未使用的UI组件"""
        current_time = time.time()
        
        for plugin_name, container in list(self._plugin_containers.items()):
            # 如果超过10分钟未访问且未显示，销毁组件
            if (not container.is_visible and 
                container.widget is not None and
                current_time - container.last_accessed > 600):  # 10分钟
                
                print(f"🧹 清理未使用的插件组件: {plugin_name}")
                container.destroy_widget()
    
    def _on_ui_plugin_registered(self, event):
        """UI插件注册事件处理"""
        plugin_name = event.plugin_name
        print(f"📝 UI插件已注册: {plugin_name}")
    
    def _on_ui_plugin_unregistered(self, event):
        """UI插件注销事件处理"""
        plugin_name = event.plugin_name
        print(f"📝 UI插件已注销: {plugin_name}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        base_metrics = super().get_performance_metrics()
        
        base_metrics.update({
            'total_ui_plugins': len(self._plugin_containers),
            'active_widgets': len([c for c in self._plugin_containers.values() if c.widget is not None]),
            'visible_widgets': len([c for c in self._plugin_containers.values() if c.is_visible]),
            'theme_plugins': len(self._theme_plugins),
            'load_times': self._load_times.copy(),
            'widget_creation_times': self._widget_creation_times.copy(),
            'average_load_time': sum(self._load_times.values()) / len(self._load_times) if self._load_times else 0,
            'average_widget_creation_time': sum(self._widget_creation_times.values()) / len(self._widget_creation_times) if self._widget_creation_times else 0
        })
        
        return base_metrics


# 便捷函数
def get_ui_plugin_loader() -> UIPluginLoader:
    """获取UI插件加载器实例"""
    # 尝试从组件管理器获取
    loader = ui_component_manager.get_component("UIPluginLoader")
    if loader:
        return loader
    
    # 如果没有注册，创建并注册
    loader = UIPluginLoader()
    ui_component_manager.register_component(loader, "UIPluginLoader")
    
    return loader