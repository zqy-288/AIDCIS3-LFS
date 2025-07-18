"""
插件动态加载和热重载系统
提供插件的热插拔、动态加载、实时更新等功能
"""

import os
import sys
import time
import importlib
import importlib.util
import threading
import shutil
import hashlib
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Set, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import logging
import watchdog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .plugin_manager import PluginManager, IPlugin, PluginMetadata, PluginState
from .plugin_lifecycle import PluginLifecycleManager, LifecycleTransition
from .application import EventBus, ApplicationEvent


class ReloadTrigger(Enum):
    """重载触发器类型"""
    FILE_CHANGE = "file_change"
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    DEPENDENCY_CHANGE = "dependency_change"
    CONFIG_CHANGE = "config_change"


class ReloadStrategy(Enum):
    """重载策略"""
    IMMEDIATE = "immediate"        # 立即重载
    GRACEFUL = "graceful"         # 优雅重载
    LAZY = "lazy"                 # 懒重载
    BATCH = "batch"               # 批量重载


@dataclass
class ReloadEvent:
    """重载事件"""
    plugin_id: str
    trigger: ReloadTrigger
    strategy: ReloadStrategy
    timestamp: float = field(default_factory=time.time)
    file_path: Optional[str] = None
    changes: List[str] = field(default_factory=list)
    success: bool = False
    error: Optional[str] = None
    duration: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'plugin_id': self.plugin_id,
            'trigger': self.trigger.value,
            'strategy': self.strategy.value,
            'timestamp': self.timestamp,
            'file_path': self.file_path,
            'changes': self.changes,
            'success': self.success,
            'error': self.error,
            'duration': self.duration
        }


@dataclass
class HotReloadConfig:
    """热重载配置"""
    enabled: bool = True
    watch_directories: List[str] = field(default_factory=list)
    watch_extensions: Set[str] = field(default_factory=lambda: {'.py', '.json', '.yaml', '.yml'})
    ignore_patterns: Set[str] = field(default_factory=lambda: {'__pycache__', '.git', '.pyc'})
    debounce_delay: float = 1.0  # 防抖延迟（秒）
    default_strategy: ReloadStrategy = ReloadStrategy.GRACEFUL
    max_reload_attempts: int = 3
    backup_enabled: bool = True
    rollback_enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'enabled': self.enabled,
            'watch_directories': self.watch_directories,
            'watch_extensions': list(self.watch_extensions),
            'ignore_patterns': list(self.ignore_patterns),
            'debounce_delay': self.debounce_delay,
            'default_strategy': self.default_strategy.value,
            'max_reload_attempts': self.max_reload_attempts,
            'backup_enabled': self.backup_enabled,
            'rollback_enabled': self.rollback_enabled
        }


class IReloadHandler(ABC):
    """重载处理器接口"""
    
    @abstractmethod
    def can_handle(self, plugin_id: str, trigger: ReloadTrigger) -> bool:
        """检查是否可以处理重载"""
        pass
    
    @abstractmethod
    def handle_reload(self, plugin_id: str, reload_event: ReloadEvent) -> bool:
        """处理重载"""
        pass
    
    @abstractmethod
    def get_priority(self) -> int:
        """获取处理器优先级"""
        pass


class PluginFileWatcher(FileSystemEventHandler):
    """插件文件监控器"""
    
    def __init__(self, hot_reload_manager: 'PluginHotReloadManager'):
        self.hot_reload_manager = hot_reload_manager
        self.logger = hot_reload_manager._logger
        self._last_modified: Dict[str, float] = {}
        self._debounce_timers: Dict[str, threading.Timer] = {}
    
    def on_modified(self, event):
        """文件修改事件"""
        if event.is_directory:
            return
        
        self._handle_file_event(event.src_path, 'modified')
    
    def on_created(self, event):
        """文件创建事件"""
        if event.is_directory:
            return
        
        self._handle_file_event(event.src_path, 'created')
    
    def on_deleted(self, event):
        """文件删除事件"""
        if event.is_directory:
            return
        
        self._handle_file_event(event.src_path, 'deleted')
    
    def _handle_file_event(self, file_path: str, event_type: str):
        """处理文件事件"""
        try:
            # 检查文件扩展名
            if not self._should_watch_file(file_path):
                return
            
            # 检查是否需要防抖
            current_time = time.time()
            last_modified = self._last_modified.get(file_path, 0)
            
            if current_time - last_modified < self.hot_reload_manager._config.debounce_delay:
                # 取消之前的定时器
                if file_path in self._debounce_timers:
                    self._debounce_timers[file_path].cancel()
                
                # 设置新的定时器
                timer = threading.Timer(
                    self.hot_reload_manager._config.debounce_delay,
                    self._process_file_change,
                    args=(file_path, event_type)
                )
                timer.start()
                self._debounce_timers[file_path] = timer
                return
            
            self._last_modified[file_path] = current_time
            self._process_file_change(file_path, event_type)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error handling file event {file_path}: {e}")
    
    def _should_watch_file(self, file_path: str) -> bool:
        """检查是否应该监控文件"""
        path = Path(file_path)
        
        # 检查扩展名
        if path.suffix not in self.hot_reload_manager._config.watch_extensions:
            return False
        
        # 检查忽略模式
        for pattern in self.hot_reload_manager._config.ignore_patterns:
            if pattern in str(path):
                return False
        
        return True
    
    def _process_file_change(self, file_path: str, event_type: str):
        """处理文件变更"""
        try:
            # 查找受影响的插件
            affected_plugins = self.hot_reload_manager._find_affected_plugins(file_path)
            
            for plugin_id in affected_plugins:
                self.hot_reload_manager.trigger_reload(
                    plugin_id, 
                    ReloadTrigger.FILE_CHANGE,
                    file_path=file_path,
                    changes=[f"{event_type}: {file_path}"]
                )
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error processing file change {file_path}: {e}")


class PluginBackupManager:
    """插件备份管理器"""
    
    def __init__(self, backup_dir: str = "plugin_backups", logger: Optional[logging.Logger] = None):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.logger = logger or logging.getLogger(__name__)
        self._backups: Dict[str, List[str]] = defaultdict(list)  # plugin_id -> [backup_paths]
    
    def create_backup(self, plugin_id: str, plugin_path: str) -> str:
        """创建插件备份"""
        try:
            timestamp = int(time.time())
            backup_name = f"{plugin_id}_{timestamp}"
            backup_path = self.backup_dir / backup_name
            
            # 复制插件文件
            if os.path.isfile(plugin_path):
                shutil.copy2(plugin_path, backup_path)
            else:
                shutil.copytree(plugin_path, backup_path)
            
            # 记录备份
            self._backups[plugin_id].append(str(backup_path))
            
            # 限制备份数量
            max_backups = 10
            if len(self._backups[plugin_id]) > max_backups:
                old_backup = self._backups[plugin_id].pop(0)
                self._remove_backup_file(old_backup)
            
            if self.logger:
                self.logger.info(f"Created backup for plugin {plugin_id}: {backup_path}")
            
            return str(backup_path)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to create backup for plugin {plugin_id}: {e}")
            return ""
    
    def restore_backup(self, plugin_id: str, backup_path: str, target_path: str) -> bool:
        """恢复插件备份"""
        try:
            if not os.path.exists(backup_path):
                return False
            
            # 删除当前版本
            if os.path.exists(target_path):
                if os.path.isfile(target_path):
                    os.remove(target_path)
                else:
                    shutil.rmtree(target_path)
            
            # 恢复备份
            if os.path.isfile(backup_path):
                shutil.copy2(backup_path, target_path)
            else:
                shutil.copytree(backup_path, target_path)
            
            if self.logger:
                self.logger.info(f"Restored backup for plugin {plugin_id} from {backup_path}")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to restore backup for plugin {plugin_id}: {e}")
            return False
    
    def get_backups(self, plugin_id: str) -> List[str]:
        """获取插件备份列表"""
        return self._backups.get(plugin_id, []).copy()
    
    def cleanup_backups(self, plugin_id: str):
        """清理插件备份"""
        backups = self._backups.get(plugin_id, [])
        for backup_path in backups:
            self._remove_backup_file(backup_path)
        
        self._backups.pop(plugin_id, None)
        
        if self.logger:
            self.logger.info(f"Cleaned up backups for plugin {plugin_id}")
    
    def _remove_backup_file(self, backup_path: str):
        """删除备份文件"""
        try:
            if os.path.exists(backup_path):
                if os.path.isfile(backup_path):
                    os.remove(backup_path)
                else:
                    shutil.rmtree(backup_path)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to remove backup {backup_path}: {e}")


class DefaultReloadHandler(IReloadHandler):
    """默认重载处理器"""
    
    def __init__(self, plugin_manager: PluginManager, lifecycle_manager: PluginLifecycleManager,
                 logger: Optional[logging.Logger] = None):
        self.plugin_manager = plugin_manager
        self.lifecycle_manager = lifecycle_manager
        self.logger = logger or logging.getLogger(__name__)
    
    def can_handle(self, plugin_id: str, trigger: ReloadTrigger) -> bool:
        """可以处理所有重载请求"""
        return True
    
    def handle_reload(self, plugin_id: str, reload_event: ReloadEvent) -> bool:
        """处理重载"""
        try:
            # 获取插件实例
            plugin = self.plugin_manager.get_plugin(plugin_id)
            if not plugin:
                return False
            
            # 根据策略处理重载
            if reload_event.strategy == ReloadStrategy.IMMEDIATE:
                return self._immediate_reload(plugin)
            elif reload_event.strategy == ReloadStrategy.GRACEFUL:
                return self._graceful_reload(plugin)
            elif reload_event.strategy == ReloadStrategy.LAZY:
                return self._lazy_reload(plugin)
            else:
                return self._graceful_reload(plugin)
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Reload handler error for {plugin_id}: {e}")
            return False
    
    def _immediate_reload(self, plugin: IPlugin) -> bool:
        """立即重载"""
        return self.lifecycle_manager.transition_plugin(plugin, LifecycleTransition.RELOAD)
    
    def _graceful_reload(self, plugin: IPlugin) -> bool:
        """优雅重载"""
        # 先停止插件
        if not self.lifecycle_manager.transition_plugin(plugin, LifecycleTransition.STOP):
            return False
        
        # 等待一段时间让插件完成清理
        time.sleep(0.1)
        
        # 重新加载
        return self.lifecycle_manager.transition_plugin(plugin, LifecycleTransition.RELOAD)
    
    def _lazy_reload(self, plugin: IPlugin) -> bool:
        """懒重载（标记为需要重载，但不立即执行）"""
        # 实际实现中可以设置标志，在下次使用时重载
        return True
    
    def get_priority(self) -> int:
        """最低优先级"""
        return 1000


class PluginHotReloadManager:
    """插件热重载管理器"""
    
    def __init__(self, 
                 plugin_manager: PluginManager,
                 lifecycle_manager: Optional[PluginLifecycleManager] = None,
                 event_bus: Optional[EventBus] = None,
                 config: Optional[HotReloadConfig] = None,
                 logger: Optional[logging.Logger] = None):
        self.plugin_manager = plugin_manager
        self.lifecycle_manager = lifecycle_manager
        self._event_bus = event_bus
        self._config = config or HotReloadConfig()
        self._logger = logger or logging.getLogger(__name__)
        
        # 文件监控
        self._observer: Optional[Observer] = None
        self._file_watcher = PluginFileWatcher(self)
        
        # 重载处理
        self._reload_handlers: List[IReloadHandler] = []
        self._reload_queue: List[ReloadEvent] = []
        self._reload_lock = threading.RLock()
        
        # 插件文件映射
        self._plugin_files: Dict[str, Set[str]] = defaultdict(set)  # plugin_id -> {file_paths}
        self._file_plugins: Dict[str, Set[str]] = defaultdict(set)  # file_path -> {plugin_ids}
        
        # 重载历史
        self._reload_history: List[ReloadEvent] = []
        self._max_history_size = 1000
        
        # 备份管理
        self._backup_manager = PluginBackupManager(logger=logger)
        
        # 模块缓存
        self._module_cache: Dict[str, Any] = {}
        self._module_checksums: Dict[str, str] = {}
        
        # 添加默认处理器
        if self.lifecycle_manager:
            self.add_reload_handler(DefaultReloadHandler(plugin_manager, lifecycle_manager, logger))
        
        if self._logger:
            self._logger.info("PluginHotReloadManager initialized")
    
    def start(self):
        """启动热重载管理器"""
        if not self._config.enabled:
            return
        
        # 启动文件监控
        self._start_file_watching()
        
        if self._logger:
            self._logger.info("PluginHotReloadManager started")
    
    def stop(self):
        """停止热重载管理器"""
        # 停止文件监控
        self._stop_file_watching()
        
        if self._logger:
            self._logger.info("PluginHotReloadManager stopped")
    
    def _start_file_watching(self):
        """启动文件监控"""
        if self._observer:
            return
        
        try:
            self._observer = Observer()
            
            # 添加监控目录
            for directory in self._config.watch_directories:
                if os.path.exists(directory):
                    self._observer.schedule(self._file_watcher, directory, recursive=True)
                    if self._logger:
                        self._logger.info(f"Watching directory: {directory}")
            
            self._observer.start()
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to start file watching: {e}")
    
    def _stop_file_watching(self):
        """停止文件监控"""
        if self._observer:
            try:
                self._observer.stop()
                self._observer.join(timeout=5.0)
                self._observer = None
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Failed to stop file watching: {e}")
    
    def add_reload_handler(self, handler: IReloadHandler):
        """添加重载处理器"""
        self._reload_handlers.append(handler)
        # 按优先级排序
        self._reload_handlers.sort(key=lambda h: h.get_priority())
        
        if self._logger:
            self._logger.debug(f"Added reload handler: {handler.__class__.__name__}")
    
    def remove_reload_handler(self, handler: IReloadHandler):
        """移除重载处理器"""
        try:
            self._reload_handlers.remove(handler)
        except ValueError:
            pass
    
    def register_plugin_files(self, plugin_id: str, file_paths: List[str]):
        """注册插件文件"""
        with self._reload_lock:
            self._plugin_files[plugin_id].update(file_paths)
            
            for file_path in file_paths:
                self._file_plugins[file_path].add(plugin_id)
                
                # 计算文件校验和
                self._update_file_checksum(file_path)
        
        if self._logger:
            self._logger.debug(f"Registered {len(file_paths)} files for plugin {plugin_id}")
    
    def unregister_plugin_files(self, plugin_id: str):
        """注销插件文件"""
        with self._reload_lock:
            file_paths = self._plugin_files.get(plugin_id, set())
            
            for file_path in file_paths:
                self._file_plugins[file_path].discard(plugin_id)
                if not self._file_plugins[file_path]:
                    del self._file_plugins[file_path]
            
            self._plugin_files.pop(plugin_id, None)
        
        if self._logger:
            self._logger.debug(f"Unregistered files for plugin {plugin_id}")
    
    def _update_file_checksum(self, file_path: str):
        """更新文件校验和"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    content = f.read()
                    checksum = hashlib.md5(content).hexdigest()
                    self._module_checksums[file_path] = checksum
        except Exception as e:
            if self._logger:
                self._logger.warning(f"Failed to update checksum for {file_path}: {e}")
    
    def _find_affected_plugins(self, file_path: str) -> List[str]:
        """查找受文件变更影响的插件"""
        affected_plugins = []
        
        # 直接影响
        if file_path in self._file_plugins:
            affected_plugins.extend(self._file_plugins[file_path])
        
        # 查找依赖关系影响（简化实现）
        for plugin_id, plugin_files in self._plugin_files.items():
            if file_path in plugin_files:
                affected_plugins.append(plugin_id)
        
        return list(set(affected_plugins))
    
    def trigger_reload(self, plugin_id: str, trigger: ReloadTrigger, 
                      strategy: Optional[ReloadStrategy] = None,
                      file_path: Optional[str] = None,
                      changes: Optional[List[str]] = None) -> bool:
        """触发插件重载"""
        try:
            if not self._config.enabled:
                return False
            
            # 创建重载事件
            reload_event = ReloadEvent(
                plugin_id=plugin_id,
                trigger=trigger,
                strategy=strategy or self._config.default_strategy,
                file_path=file_path,
                changes=changes or []
            )
            
            # 执行重载
            start_time = time.time()
            success = self._execute_reload(reload_event)
            reload_event.duration = time.time() - start_time
            reload_event.success = success
            
            # 记录历史
            self._record_reload_event(reload_event)
            
            # 发布事件
            if self._event_bus:
                app_event = ApplicationEvent(
                    "plugin_reload_" + ("success" if success else "failed"),
                    reload_event.to_dict()
                )
                self._event_bus.post_event(app_event)
            
            if self._logger:
                level = logging.INFO if success else logging.ERROR
                self._logger.log(level, 
                    f"Plugin {plugin_id} reload {'succeeded' if success else 'failed'} "
                    f"({reload_event.duration:.3f}s)")
            
            return success
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to trigger reload for {plugin_id}: {e}")
            return False
    
    def _execute_reload(self, reload_event: ReloadEvent) -> bool:
        """执行重载"""
        plugin_id = reload_event.plugin_id
        
        # 创建备份
        if self._config.backup_enabled:
            plugin_files = self._plugin_files.get(plugin_id, set())
            for file_path in plugin_files:
                if os.path.exists(file_path):
                    self._backup_manager.create_backup(plugin_id, file_path)
        
        # 查找合适的处理器
        handler = None
        for h in self._reload_handlers:
            if h.can_handle(plugin_id, reload_event.trigger):
                handler = h
                break
        
        if not handler:
            reload_event.error = f"No reload handler found for plugin {plugin_id}"
            return False
        
        # 执行重载
        try:
            success = handler.handle_reload(plugin_id, reload_event)
            
            if success:
                # 更新模块缓存
                self._update_module_cache(plugin_id)
            else:
                # 回滚处理
                if self._config.rollback_enabled:
                    self._attempt_rollback(plugin_id)
            
            return success
            
        except Exception as e:
            reload_event.error = str(e)
            
            # 回滚处理
            if self._config.rollback_enabled:
                self._attempt_rollback(plugin_id)
            
            return False
    
    def _update_module_cache(self, plugin_id: str):
        """更新模块缓存"""
        try:
            # 清除模块缓存
            modules_to_remove = []
            for module_name in sys.modules:
                if plugin_id in module_name:
                    modules_to_remove.append(module_name)
            
            for module_name in modules_to_remove:
                del sys.modules[module_name]
            
            # 更新文件校验和
            plugin_files = self._plugin_files.get(plugin_id, set())
            for file_path in plugin_files:
                self._update_file_checksum(file_path)
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to update module cache for {plugin_id}: {e}")
    
    def _attempt_rollback(self, plugin_id: str) -> bool:
        """尝试回滚插件"""
        try:
            backups = self._backup_manager.get_backups(plugin_id)
            if not backups:
                return False
            
            # 使用最新的备份
            latest_backup = backups[-1]
            plugin_files = self._plugin_files.get(plugin_id, set())
            
            for file_path in plugin_files:
                if self._backup_manager.restore_backup(plugin_id, latest_backup, file_path):
                    if self._logger:
                        self._logger.info(f"Rolled back plugin {plugin_id} file: {file_path}")
            
            return True
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to rollback plugin {plugin_id}: {e}")
            return False
    
    def _record_reload_event(self, reload_event: ReloadEvent):
        """记录重载事件"""
        self._reload_history.append(reload_event)
        
        # 限制历史记录大小
        if len(self._reload_history) > self._max_history_size:
            self._reload_history = self._reload_history[-self._max_history_size:]
    
    def reload_plugin(self, plugin_id: str, strategy: Optional[ReloadStrategy] = None) -> bool:
        """手动重载插件"""
        return self.trigger_reload(plugin_id, ReloadTrigger.MANUAL, strategy)
    
    def reload_all_plugins(self, strategy: Optional[ReloadStrategy] = None) -> Dict[str, bool]:
        """重载所有插件"""
        results = {}
        
        for plugin_id in self._plugin_files.keys():
            results[plugin_id] = self.reload_plugin(plugin_id, strategy)
        
        return results
    
    def check_file_changes(self) -> List[str]:
        """检查文件变更"""
        changed_plugins = []
        
        for plugin_id, file_paths in self._plugin_files.items():
            for file_path in file_paths:
                if self._has_file_changed(file_path):
                    changed_plugins.append(plugin_id)
                    break
        
        return changed_plugins
    
    def _has_file_changed(self, file_path: str) -> bool:
        """检查文件是否发生变更"""
        try:
            if not os.path.exists(file_path):
                return True
            
            current_checksum = ""
            with open(file_path, 'rb') as f:
                content = f.read()
                current_checksum = hashlib.md5(content).hexdigest()
            
            old_checksum = self._module_checksums.get(file_path, "")
            return current_checksum != old_checksum
            
        except Exception:
            return False
    
    def add_watch_directory(self, directory: str):
        """添加监控目录"""
        if directory not in self._config.watch_directories:
            self._config.watch_directories.append(directory)
            
            # 如果观察者已启动，添加新的监控
            if self._observer and os.path.exists(directory):
                self._observer.schedule(self._file_watcher, directory, recursive=True)
                if self._logger:
                    self._logger.info(f"Added watch directory: {directory}")
    
    def remove_watch_directory(self, directory: str):
        """移除监控目录"""
        try:
            self._config.watch_directories.remove(directory)
            # 注意：watchdog不支持动态移除监控，需要重启观察者
        except ValueError:
            pass
    
    # 查询和统计
    def get_reload_history(self, plugin_id: Optional[str] = None, limit: int = 100) -> List[ReloadEvent]:
        """获取重载历史"""
        history = self._reload_history
        
        if plugin_id:
            history = [event for event in history if event.plugin_id == plugin_id]
        
        # 按时间倒序排列
        history.sort(key=lambda e: e.timestamp, reverse=True)
        
        return history[:limit]
    
    def get_reload_statistics(self) -> Dict[str, Any]:
        """获取重载统计"""
        total_reloads = len(self._reload_history)
        successful_reloads = sum(1 for event in self._reload_history if event.success)
        failed_reloads = total_reloads - successful_reloads
        
        # 按触发器类型统计
        by_trigger = defaultdict(int)
        for event in self._reload_history:
            by_trigger[event.trigger.value] += 1
        
        # 按插件统计
        by_plugin = defaultdict(int)
        for event in self._reload_history:
            by_plugin[event.plugin_id] += 1
        
        # 计算平均重载时间
        avg_duration = 0.0
        if total_reloads > 0:
            total_duration = sum(event.duration for event in self._reload_history)
            avg_duration = total_duration / total_reloads
        
        return {
            'total_reloads': total_reloads,
            'successful_reloads': successful_reloads,
            'failed_reloads': failed_reloads,
            'success_rate': successful_reloads / total_reloads if total_reloads > 0 else 0.0,
            'average_duration': avg_duration,
            'by_trigger': dict(by_trigger),
            'by_plugin': dict(by_plugin),
            'watched_plugins': len(self._plugin_files),
            'watched_files': sum(len(files) for files in self._plugin_files.values()),
            'config': self._config.to_dict()
        }
    
    def get_plugin_files(self, plugin_id: str) -> Set[str]:
        """获取插件文件列表"""
        return self._plugin_files.get(plugin_id, set()).copy()
    
    def update_config(self, config: HotReloadConfig):
        """更新配置"""
        old_enabled = self._config.enabled
        self._config = config
        
        # 如果启用状态发生变化，重启/停止文件监控
        if old_enabled != config.enabled:
            if config.enabled:
                self.start()
            else:
                self.stop()
    
    def get_backups(self, plugin_id: str) -> List[str]:
        """获取插件备份"""
        return self._backup_manager.get_backups(plugin_id)
    
    def cleanup_plugin_backups(self, plugin_id: str):
        """清理插件备份"""
        self._backup_manager.cleanup_backups(plugin_id)


# 便捷函数
def create_hot_reload_manager(plugin_manager: PluginManager,
                            lifecycle_manager: Optional[PluginLifecycleManager] = None,
                            event_bus: Optional[EventBus] = None,
                            config: Optional[HotReloadConfig] = None,
                            logger: Optional[logging.Logger] = None) -> PluginHotReloadManager:
    """创建插件热重载管理器"""
    return PluginHotReloadManager(plugin_manager, lifecycle_manager, event_bus, config, logger)


def create_reload_config(enabled: bool = True,
                        watch_directories: List[str] = None,
                        debounce_delay: float = 1.0,
                        default_strategy: ReloadStrategy = ReloadStrategy.GRACEFUL) -> HotReloadConfig:
    """创建重载配置"""
    return HotReloadConfig(
        enabled=enabled,
        watch_directories=watch_directories or [],
        debounce_delay=debounce_delay,
        default_strategy=default_strategy
    )