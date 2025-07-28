"""
UI组件热重载系统
提供UI插件和组件的热重载功能，支持开发时的快速迭代
"""

import os
import sys
import time
import threading
import importlib
import importlib.util
from typing import Dict, List, Any, Optional, Callable, Set
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
import logging
import weakref

from PySide6.QtCore import QObject, Signal, QTimer, QFileSystemWatcher
from PySide6.QtWidgets import QWidget

try:
    from ..core.dependency_injection import injectable, ServiceLifetime
    from ..modules.ui_component_base import UIComponentBase, ComponentState
    from ..modules.ui_plugin_loader import UIPluginLoader
    from ..interfaces.ui_plugin_interface import IUIPlugin
except ImportError:
    # 从项目根目录运行时的导入路径
    from core.dependency_injection import injectable, ServiceLifetime
    from modules.ui_component_base import UIComponentBase, ComponentState
    from modules.ui_plugin_loader import UIPluginLoader
    from interfaces.ui_plugin_interface import IUIPlugin


class ReloadTrigger(Enum):
    """重载触发器类型"""
    FILE_CHANGE = "file_change"        # 文件变化
    MANUAL = "manual"                  # 手动触发
    TIME_BASED = "time_based"          # 基于时间
    DEPENDENCY_CHANGE = "dependency_change"  # 依赖变化


@dataclass
class ReloadEvent:
    """重载事件"""
    trigger: ReloadTrigger
    component_name: str
    file_path: Optional[str] = None
    timestamp: float = 0.0
    success: bool = False
    error: Optional[str] = None


class FileWatcher:
    """文件监控器"""
    
    def __init__(self):
        self._watcher = QFileSystemWatcher()
        self._watched_files: Dict[str, Set[str]] = {}  # component_name -> file_paths
        self._file_to_components: Dict[str, Set[str]] = {}  # file_path -> component_names
        self._callbacks: List[Callable] = []
        
        # 连接信号
        self._watcher.fileChanged.connect(self._on_file_changed)
        self._watcher.directoryChanged.connect(self._on_directory_changed)
    
    def add_callback(self, callback: Callable):
        """添加文件变化回调"""
        self._callbacks.append(callback)
    
    def watch_component(self, component_name: str, file_paths: List[str]):
        """监控组件相关文件"""
        self._watched_files[component_name] = set()
        
        for file_path in file_paths:
            if os.path.exists(file_path):
                # 添加到文件监控
                self._watcher.addPath(file_path)
                
                # 记录映射关系
                self._watched_files[component_name].add(file_path)
                
                if file_path not in self._file_to_components:
                    self._file_to_components[file_path] = set()
                self._file_to_components[file_path].add(component_name)
                
                print(f"📁 开始监控文件: {file_path} (组件: {component_name})")
    
    def unwatch_component(self, component_name: str):
        """停止监控组件"""
        if component_name not in self._watched_files:
            return
        
        # 移除文件监控
        for file_path in self._watched_files[component_name]:
            # 检查是否还有其他组件需要这个文件
            self._file_to_components[file_path].discard(component_name)
            
            if not self._file_to_components[file_path]:
                self._watcher.removePath(file_path)
                del self._file_to_components[file_path]
                print(f"📁 停止监控文件: {file_path}")
        
        del self._watched_files[component_name]
        print(f"📁 停止监控组件: {component_name}")
    
    def _on_file_changed(self, file_path: str):
        """文件变化处理"""
        if file_path in self._file_to_components:
            components = self._file_to_components[file_path].copy()
            
            for component_name in components:
                event = ReloadEvent(
                    trigger=ReloadTrigger.FILE_CHANGE,
                    component_name=component_name,
                    file_path=file_path,
                    timestamp=time.time()
                )
                
                # 调用所有回调
                for callback in self._callbacks:
                    try:
                        callback(event)
                    except Exception as e:
                        print(f"❌ 文件变化回调执行失败: {e}")
    
    def _on_directory_changed(self, dir_path: str):
        """目录变化处理"""
        print(f"📁 目录变化: {dir_path}")
    
    def get_watched_files(self) -> Dict[str, Set[str]]:
        """获取监控的文件列表"""
        return self._watched_files.copy()


class ReloadHistory:
    """重载历史记录"""
    
    def __init__(self, max_records: int = 100):
        self._max_records = max_records
        self._records: List[ReloadEvent] = []
        self._lock = threading.Lock()
    
    def add_record(self, event: ReloadEvent):
        """添加重载记录"""
        with self._lock:
            self._records.append(event)
            
            # 保持最大记录数限制
            if len(self._records) > self._max_records:
                self._records = self._records[-self._max_records:]
    
    def get_records(self, component_name: Optional[str] = None, 
                   limit: Optional[int] = None) -> List[ReloadEvent]:
        """获取重载记录"""
        with self._lock:
            records = self._records.copy()
        
        # 按组件过滤
        if component_name:
            records = [r for r in records if r.component_name == component_name]
        
        # 限制数量
        if limit:
            records = records[-limit:]
        
        return records
    
    def get_success_rate(self, component_name: Optional[str] = None) -> float:
        """获取重载成功率"""
        records = self.get_records(component_name)
        if not records:
            return 0.0
        
        success_count = sum(1 for r in records if r.success)
        return success_count / len(records) * 100
    
    def clear_history(self):
        """清空历史记录"""
        with self._lock:
            self._records.clear()


@injectable(ServiceLifetime.SINGLETON)
class UIHotReload(UIComponentBase):
    """UI组件热重载系统"""
    
    # Qt信号
    reload_started = Signal(str)        # 开始重载
    reload_completed = Signal(str, bool)  # 重载完成 (component_name, success)
    reload_failed = Signal(str, str)    # 重载失败 (component_name, error)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 依赖注入
        self.declare_dependency("ui_plugin_loader", UIPluginLoader, required=True)
        
        # 核心组件
        self._file_watcher = FileWatcher()
        self._reload_history = ReloadHistory()
        
        # 热重载配置
        self._enabled = True
        self._auto_reload = True
        self._reload_delay = 1.0  # 重载延迟（秒）
        self._debounce_interval = 0.5  # 防抖间隔（秒）
        
        # 重载状态
        self._reloading_components: Set[str] = set()
        self._pending_reloads: Dict[str, float] = {}  # component_name -> timestamp
        
        # 重载定时器
        self._reload_timer = QTimer()
        self._reload_timer.timeout.connect(self._process_pending_reloads)
        self._reload_timer.start(100)  # 每100ms检查一次
        
        # 监控的组件类型
        self._monitored_types = {
            'ui_plugin',
            'ui_component',
            'theme_plugin'
        }
        
        # 排除的文件模式
        self._excluded_patterns = {
            '*.pyc',
            '*.pyo',
            '*.pyd',
            '__pycache__',
            '.git',
            '.svn',
            '*.tmp'
        }
        
        # 设置文件监控回调
        self._file_watcher.add_callback(self._on_file_change_event)
        
        print(f"🔥 UI热重载系统已创建: {self.component_id}")
    
    def _do_initialize(self) -> bool:
        """初始化热重载系统"""
        try:
            print("✅ UI热重载系统初始化完成")
            return True
            
        except Exception as e:
            print(f"❌ UI热重载系统初始化失败: {e}")
            return False
    
    def _do_start(self) -> bool:
        """启动热重载系统"""
        try:
            # 开始监控现有组件
            self._start_monitoring_existing_components()
            
            print("✅ UI热重载系统启动完成")
            return True
            
        except Exception as e:
            print(f"❌ UI热重载系统启动失败: {e}")
            return False
    
    def _do_stop(self) -> bool:
        """停止热重载系统"""
        try:
            # 停止所有监控
            self._stop_all_monitoring()
            
            # 停止定时器
            self._reload_timer.stop()
            
            print("✅ UI热重载系统停止完成")
            return True
            
        except Exception as e:
            print(f"❌ UI热重载系统停止失败: {e}")
            return False
    
    def _do_cleanup(self) -> bool:
        """清理热重载系统资源"""
        try:
            # 清理文件监控
            if self._file_watcher:
                # 停止所有监控（在FileWatcher中实现具体清理逻辑）
                for component_name in list(self._file_watcher.get_watched_files().keys()):
                    self._file_watcher.unwatch_component(component_name)
            
            # 清理定时器
            if self._reload_timer:
                self._reload_timer.stop()
                self._reload_timer.deleteLater()
                self._reload_timer = None
            
            # 清理状态
            self._reloading_components.clear()
            self._pending_reloads.clear()
            
            print("✅ UI热重载系统清理完成")
            return True
            
        except Exception as e:
            print(f"❌ UI热重载系统清理失败: {e}")
            return False
    
    def enable_hot_reload(self, enabled: bool = True):
        """启用/禁用热重载"""
        self._enabled = enabled
        print(f"🔥 热重载系统{'启用' if enabled else '禁用'}")
    
    def set_auto_reload(self, auto: bool = True):
        """设置自动重载"""
        self._auto_reload = auto
        print(f"🔄 自动重载{'启用' if auto else '禁用'}")
    
    def set_reload_delay(self, delay: float):
        """设置重载延迟"""
        self._reload_delay = max(0.1, delay)
        print(f"⏱️ 重载延迟设置为 {self._reload_delay}秒")
    
    def add_component_monitoring(self, component_name: str, file_paths: List[str]):
        """添加组件文件监控"""
        if not self._enabled:
            return
        
        # 过滤有效文件
        valid_files = []
        for file_path in file_paths:
            if self._should_monitor_file(file_path):
                valid_files.append(file_path)
        
        if valid_files:
            self._file_watcher.watch_component(component_name, valid_files)
            print(f"🔍 开始监控组件 {component_name}，文件数: {len(valid_files)}")
    
    def remove_component_monitoring(self, component_name: str):
        """移除组件文件监控"""
        self._file_watcher.unwatch_component(component_name)
        
        # 清理待重载列表
        if component_name in self._pending_reloads:
            del self._pending_reloads[component_name]
        
        self._reloading_components.discard(component_name)
        
        print(f"🔍 停止监控组件 {component_name}")
    
    def reload_component(self, component_name: str, trigger: ReloadTrigger = ReloadTrigger.MANUAL) -> bool:
        """重载指定组件"""
        if not self._enabled:
            print(f"⚠️ 热重载已禁用，无法重载组件 {component_name}")
            return False
        
        if component_name in self._reloading_components:
            print(f"⚠️ 组件 {component_name} 正在重载中，跳过")
            return False
        
        try:
            self._reloading_components.add(component_name)
            
            # 发射开始信号
            self.reload_started.emit(component_name)
            
            # 执行重载
            success = self._perform_reload(component_name)
            
            # 记录重载事件
            event = ReloadEvent(
                trigger=trigger,
                component_name=component_name,
                timestamp=time.time(),
                success=success
            )
            
            if not success:
                event.error = f"重载失败"
            
            self._reload_history.add_record(event)
            
            # 发射完成信号
            if success:
                self.reload_completed.emit(component_name, True)
                print(f"✅ 组件 {component_name} 重载成功")
            else:
                self.reload_failed.emit(component_name, event.error or "未知错误")
                print(f"❌ 组件 {component_name} 重载失败")
            
            return success
            
        except Exception as e:
            error_msg = f"重载组件 {component_name} 时发生异常: {e}"
            print(f"❌ {error_msg}")
            
            # 记录错误事件
            event = ReloadEvent(
                trigger=trigger,
                component_name=component_name,
                timestamp=time.time(),
                success=False,
                error=error_msg
            )
            self._reload_history.add_record(event)
            
            # 发射失败信号
            self.reload_failed.emit(component_name, error_msg)
            
            return False
            
        finally:
            self._reloading_components.discard(component_name)
    
    def reload_all_components(self) -> Dict[str, bool]:
        """重载所有监控的组件"""
        results = {}
        
        # 获取所有监控的组件
        monitored_components = list(self._file_watcher.get_watched_files().keys())
        
        for component_name in monitored_components:
            results[component_name] = self.reload_component(component_name, ReloadTrigger.MANUAL)
        
        return results
    
    def get_reload_history(self, component_name: Optional[str] = None, 
                          limit: Optional[int] = None) -> List[ReloadEvent]:
        """获取重载历史"""
        return self._reload_history.get_records(component_name, limit)
    
    def get_reload_statistics(self) -> Dict[str, Any]:
        """获取重载统计信息"""
        monitored_components = list(self._file_watcher.get_watched_files().keys())
        
        stats = {
            'enabled': self._enabled,
            'auto_reload': self._auto_reload,
            'monitored_components': len(monitored_components),
            'reloading_components': len(self._reloading_components),
            'pending_reloads': len(self._pending_reloads),
            'total_reloads': len(self._reload_history.get_records()),
            'overall_success_rate': self._reload_history.get_success_rate(),
            'component_success_rates': {}
        }
        
        # 计算每个组件的成功率
        for component_name in monitored_components:
            stats['component_success_rates'][component_name] = \
                self._reload_history.get_success_rate(component_name)
        
        return stats
    
    def _start_monitoring_existing_components(self):
        """开始监控现有组件"""
        try:
            ui_plugin_loader = self.get_dependency("ui_plugin_loader")
            if not ui_plugin_loader:
                return
            
            # 监控所有UI插件
            ui_plugins = ui_plugin_loader.list_ui_plugins()
            for plugin_name in ui_plugins:
                self._setup_plugin_monitoring(plugin_name)
                
        except Exception as e:
            print(f"⚠️ 开始监控现有组件时发生错误: {e}")
    
    def _setup_plugin_monitoring(self, plugin_name: str):
        """设置插件监控"""
        try:
            ui_plugin_loader = self.get_dependency("ui_plugin_loader")
            if not ui_plugin_loader:
                return
            
            # 获取插件状态
            plugin_status = ui_plugin_loader.get_plugin_status(plugin_name)
            if not plugin_status:
                return
            
            # 推测插件文件路径（这里简化处理）
            plugin_files = [
                f"src/plugins/{plugin_name}.py",
                f"src/plugins/{plugin_name}_plugin.py",
                f"plugins/{plugin_name}.py",
                f"plugins/{plugin_name}_plugin.py"
            ]
            
            # 过滤存在的文件
            existing_files = []
            for file_path in plugin_files:
                if os.path.exists(file_path):
                    existing_files.append(os.path.abspath(file_path))
            
            if existing_files:
                self.add_component_monitoring(plugin_name, existing_files)
                
        except Exception as e:
            print(f"⚠️ 设置插件 {plugin_name} 监控时发生错误: {e}")
    
    def _stop_all_monitoring(self):
        """停止所有监控"""
        monitored_components = list(self._file_watcher.get_watched_files().keys())
        for component_name in monitored_components:
            self._file_watcher.unwatch_component(component_name)
    
    def _should_monitor_file(self, file_path: str) -> bool:
        """检查是否应该监控文件"""
        file_path = file_path.lower()
        
        # 检查排除模式
        for pattern in self._excluded_patterns:
            if pattern.replace('*', '') in file_path:
                return False
        
        # 只监控Python文件
        return file_path.endswith('.py')
    
    def _on_file_change_event(self, event: ReloadEvent):
        """文件变化事件处理"""
        if not self._enabled or not self._auto_reload:
            return
        
        component_name = event.component_name
        
        # 防抖处理：如果组件已在待重载列表中，更新时间戳
        current_time = time.time()
        self._pending_reloads[component_name] = current_time
        
        print(f"📝 检测到文件变化: {event.file_path} (组件: {component_name})")
    
    def _process_pending_reloads(self):
        """处理待重载的组件"""
        if not self._auto_reload:
            return
        
        current_time = time.time()
        components_to_reload = []
        
        # 检查哪些组件需要重载
        for component_name, timestamp in list(self._pending_reloads.items()):
            # 如果超过防抖间隔且延迟时间已到
            if (current_time - timestamp >= self._debounce_interval and
                current_time - timestamp >= self._reload_delay):
                components_to_reload.append(component_name)
                del self._pending_reloads[component_name]
        
        # 执行重载
        for component_name in components_to_reload:
            if component_name not in self._reloading_components:
                self.reload_component(component_name, ReloadTrigger.FILE_CHANGE)
    
    def _perform_reload(self, component_name: str) -> bool:
        """执行组件重载"""
        try:
            ui_plugin_loader = self.get_dependency("ui_plugin_loader")
            if not ui_plugin_loader:
                return False
            
            # 重载UI插件
            return ui_plugin_loader.reload_ui_plugin(component_name)
            
        except Exception as e:
            print(f"❌ 执行组件 {component_name} 重载失败: {e}")
            return False
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        base_metrics = super().get_performance_metrics()
        
        base_metrics.update({
            'hot_reload_enabled': self._enabled,
            'auto_reload_enabled': self._auto_reload,
            'monitored_components': len(self._file_watcher.get_watched_files()),
            'pending_reloads': len(self._pending_reloads),
            'reloading_components': len(self._reloading_components),
            'reload_delay': self._reload_delay,
            'debounce_interval': self._debounce_interval,
            'total_reload_events': len(self._reload_history.get_records()),
            'success_rate': self._reload_history.get_success_rate()
        })
        
        return base_metrics


# 便捷函数
def get_ui_hot_reload() -> UIHotReload:
    """获取UI热重载系统实例"""
    from .ui_component_base import ui_component_manager
    
    # 尝试从组件管理器获取
    hot_reload = ui_component_manager.get_component("UIHotReload")
    if hot_reload:
        return hot_reload
    
    # 如果没有注册，创建并注册
    hot_reload = UIHotReload()
    ui_component_manager.register_component(hot_reload, "UIHotReload")
    
    return hot_reload


def enable_ui_hot_reload(enabled: bool = True):
    """启用/禁用UI热重载"""
    hot_reload = get_ui_hot_reload()
    hot_reload.enable_hot_reload(enabled)


def reload_ui_component(component_name: str) -> bool:
    """重载指定UI组件"""
    hot_reload = get_ui_hot_reload()
    return hot_reload.reload_component(component_name)


def add_ui_component_monitoring(component_name: str, file_paths: List[str]):
    """添加UI组件文件监控"""
    hot_reload = get_ui_hot_reload()
    hot_reload.add_component_monitoring(component_name, file_paths)