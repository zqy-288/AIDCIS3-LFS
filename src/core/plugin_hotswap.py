"""
动态插件加载和热插拔系统
提供插件的热加载、热卸载、热更新等功能，支持零停机时间的插件管理
"""

import os
import sys
import time
import threading
import importlib
import importlib.util
import inspect
import shutil
import hashlib
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Set, Callable, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import logging
import tempfile
import zipfile

from .plugin_manager import IPlugin, PluginMetadata, PluginState, PluginManager
from .plugin_lifecycle import PluginLifecycleManager, LifecycleTransition
from .plugin_communication import PluginCommunicationHub
from .application import EventBus, ApplicationEvent


class HotSwapOperation(Enum):
    """热插拔操作类型"""
    LOAD = "load"
    UNLOAD = "unload"
    RELOAD = "reload"
    UPDATE = "update"
    ROLLBACK = "rollback"


class HotSwapStrategy(Enum):
    """热插拔策略"""
    IMMEDIATE = "immediate"  # 立即执行
    GRACEFUL = "graceful"    # 优雅关闭
    SCHEDULED = "scheduled"  # 计划执行
    DEPENDENCY_AWARE = "dependency_aware"  # 依赖感知


@dataclass
class HotSwapRequest:
    """热插拔请求"""
    operation: HotSwapOperation
    plugin_id: str
    strategy: HotSwapStrategy = HotSwapStrategy.GRACEFUL
    source_path: Optional[str] = None
    target_version: Optional[str] = None
    force: bool = False
    backup: bool = True
    rollback_on_failure: bool = True
    timeout: float = 30.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'operation': self.operation.value,
            'plugin_id': self.plugin_id,
            'strategy': self.strategy.value,
            'source_path': self.source_path,
            'target_version': self.target_version,
            'force': self.force,
            'backup': self.backup,
            'rollback_on_failure': self.rollback_on_failure,
            'timeout': self.timeout,
            'metadata': self.metadata
        }


@dataclass
class HotSwapResult:
    """热插拔结果"""
    success: bool
    request: HotSwapRequest
    start_time: float
    end_time: float
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    backup_path: Optional[str] = None
    rollback_performed: bool = False
    affected_plugins: List[str] = field(default_factory=list)
    
    @property
    def duration(self) -> float:
        """执行时长"""
        return self.end_time - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'success': self.success,
            'request': self.request.to_dict(),
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'error': self.error,
            'warnings': self.warnings,
            'backup_path': self.backup_path,
            'rollback_performed': self.rollback_performed,
            'affected_plugins': self.affected_plugins
        }


class IHotSwapHandler(ABC):
    """热插拔处理器接口"""
    
    @abstractmethod
    def can_handle(self, request: HotSwapRequest) -> bool:
        """检查是否可以处理请求"""
        pass
    
    @abstractmethod
    def execute(self, request: HotSwapRequest) -> HotSwapResult:
        """执行热插拔操作"""
        pass
    
    @abstractmethod
    def get_priority(self) -> int:
        """获取处理器优先级"""
        pass


class PluginBackupManager:
    """插件备份管理器"""
    
    def __init__(self, backup_dir: str = "backups/plugins", logger: Optional[logging.Logger] = None):
        self._backup_dir = Path(backup_dir)
        self._backup_dir.mkdir(parents=True, exist_ok=True)
        self._logger = logger or logging.getLogger(__name__)
        self._backups: Dict[str, List[str]] = defaultdict(list)  # plugin_id -> [backup_paths]
        
        # 扫描现有备份
        self._scan_existing_backups()
    
    def _scan_existing_backups(self):
        """扫描现有备份"""
        try:
            for backup_file in self._backup_dir.glob("*.zip"):
                # 解析备份文件名：plugin_id_version_timestamp.zip
                parts = backup_file.stem.split('_')
                if len(parts) >= 3:
                    plugin_id = '_'.join(parts[:-2])
                    self._backups[plugin_id].append(str(backup_file))
            
            # 排序备份（按时间戳）
            for plugin_id in self._backups:
                self._backups[plugin_id].sort()
                
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to scan existing backups: {e}")
    
    def create_backup(self, plugin_id: str, plugin_path: str, version: str = "unknown") -> Optional[str]:
        """创建插件备份"""
        try:
            timestamp = int(time.time())
            backup_name = f"{plugin_id}_{version}_{timestamp}.zip"
            backup_path = self._backup_dir / backup_name
            
            # 创建ZIP备份
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                plugin_dir = Path(plugin_path)
                
                if plugin_dir.is_file():
                    # 单文件插件
                    zipf.write(plugin_dir, plugin_dir.name)
                elif plugin_dir.is_dir():
                    # 目录插件
                    for file_path in plugin_dir.rglob('*'):
                        if file_path.is_file():
                            arc_name = file_path.relative_to(plugin_dir.parent)
                            zipf.write(file_path, arc_name)
            
            # 记录备份
            backup_path_str = str(backup_path)
            self._backups[plugin_id].append(backup_path_str)
            
            if self._logger:
                self._logger.info(f"Created backup for plugin {plugin_id}: {backup_path}")
            
            return backup_path_str
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to create backup for plugin {plugin_id}: {e}")
            return None
    
    def restore_backup(self, plugin_id: str, backup_path: str, target_path: str) -> bool:
        """恢复插件备份"""
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                if self._logger:
                    self._logger.error(f"Backup file not found: {backup_path}")
                return False
            
            target_dir = Path(target_path)
            
            # 如果目标存在，先删除
            if target_dir.exists():
                if target_dir.is_file():
                    target_dir.unlink()
                else:
                    shutil.rmtree(target_dir)
            
            # 解压备份
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                zipf.extractall(target_dir.parent)
            
            if self._logger:
                self._logger.info(f"Restored backup for plugin {plugin_id} from {backup_path}")
            
            return True
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to restore backup for plugin {plugin_id}: {e}")
            return False
    
    def get_backups(self, plugin_id: str) -> List[str]:
        """获取插件的所有备份"""
        return self._backups.get(plugin_id, []).copy()
    
    def get_latest_backup(self, plugin_id: str) -> Optional[str]:
        """获取插件的最新备份"""
        backups = self.get_backups(plugin_id)
        return backups[-1] if backups else None
    
    def cleanup_old_backups(self, plugin_id: str, keep_count: int = 5):
        """清理旧备份，保留指定数量"""
        try:
            backups = self._backups.get(plugin_id, [])
            if len(backups) > keep_count:
                # 删除旧备份
                to_delete = backups[:-keep_count]
                for backup_path in to_delete:
                    try:
                        Path(backup_path).unlink()
                        self._backups[plugin_id].remove(backup_path)
                    except Exception as e:
                        if self._logger:
                            self._logger.warning(f"Failed to delete backup {backup_path}: {e}")
                
                if self._logger:
                    self._logger.info(f"Cleaned up {len(to_delete)} old backups for plugin {plugin_id}")
                    
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to cleanup backups for plugin {plugin_id}: {e}")


class PluginFileWatcher:
    """插件文件监控器"""
    
    def __init__(self, watch_dirs: List[str], callback: Callable[[str, str], None],
                 logger: Optional[logging.Logger] = None):
        self._watch_dirs = [Path(d) for d in watch_dirs]
        self._callback = callback
        self._logger = logger or logging.getLogger(__name__)
        
        # 文件状态跟踪
        self._file_states: Dict[str, Tuple[float, str]] = {}  # file_path -> (mtime, hash)
        self._running = False
        self._watch_thread: Optional[threading.Thread] = None
        self._check_interval = 1.0  # 检查间隔（秒）
        
        # 初始扫描
        self._initial_scan()
    
    def _initial_scan(self):
        """初始文件扫描"""
        try:
            for watch_dir in self._watch_dirs:
                if watch_dir.exists():
                    for file_path in watch_dir.rglob('*.py'):
                        if file_path.is_file():
                            self._update_file_state(str(file_path))
                            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to perform initial scan: {e}")
    
    def _update_file_state(self, file_path: str):
        """更新文件状态"""
        try:
            path = Path(file_path)
            if path.exists():
                mtime = path.stat().st_mtime
                with open(path, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                self._file_states[file_path] = (mtime, file_hash)
                
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to update file state for {file_path}: {e}")
    
    def _get_file_hash(self, file_path: str) -> Optional[str]:
        """获取文件哈希"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return None
    
    def start_watching(self):
        """开始监控"""
        if self._running:
            return
        
        self._running = True
        self._watch_thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._watch_thread.start()
        
        if self._logger:
            self._logger.info("Started plugin file watching")
    
    def stop_watching(self):
        """停止监控"""
        if not self._running:
            return
        
        self._running = False
        if self._watch_thread:
            self._watch_thread.join(timeout=5.0)
        
        if self._logger:
            self._logger.info("Stopped plugin file watching")
    
    def _watch_loop(self):
        """监控循环"""
        while self._running:
            try:
                self._check_file_changes()
                time.sleep(self._check_interval)
            except Exception as e:
                if self._logger:
                    self._logger.error(f"File watch error: {e}")
    
    def _check_file_changes(self):
        """检查文件变更"""
        try:
            current_files = set()
            
            # 扫描所有监控目录
            for watch_dir in self._watch_dirs:
                if watch_dir.exists():
                    for file_path in watch_dir.rglob('*.py'):
                        if file_path.is_file():
                            file_path_str = str(file_path)
                            current_files.add(file_path_str)
                            
                            # 检查文件是否已存在
                            if file_path_str in self._file_states:
                                # 检查是否有变更
                                old_mtime, old_hash = self._file_states[file_path_str]
                                current_mtime = file_path.stat().st_mtime
                                
                                if current_mtime > old_mtime:
                                    current_hash = self._get_file_hash(file_path_str)
                                    if current_hash and current_hash != old_hash:
                                        # 文件已变更
                                        self._update_file_state(file_path_str)
                                        self._callback(file_path_str, "modified")
                            else:
                                # 新文件
                                self._update_file_state(file_path_str)
                                self._callback(file_path_str, "created")
            
            # 检查删除的文件
            deleted_files = set(self._file_states.keys()) - current_files
            for deleted_file in deleted_files:
                del self._file_states[deleted_file]
                self._callback(deleted_file, "deleted")
                
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to check file changes: {e}")


class DefaultHotSwapHandler(IHotSwapHandler):
    """默认热插拔处理器"""
    
    def __init__(self, 
                 plugin_manager: PluginManager,
                 lifecycle_manager: PluginLifecycleManager,
                 backup_manager: PluginBackupManager,
                 logger: Optional[logging.Logger] = None):
        self._plugin_manager = plugin_manager
        self._lifecycle_manager = lifecycle_manager
        self._backup_manager = backup_manager
        self._logger = logger or logging.getLogger(__name__)
    
    def can_handle(self, request: HotSwapRequest) -> bool:
        """检查是否可以处理请求"""
        return True  # 默认处理器处理所有请求
    
    def execute(self, request: HotSwapRequest) -> HotSwapResult:
        """执行热插拔操作"""
        start_time = time.time()
        result = HotSwapResult(
            success=False,
            request=request,
            start_time=start_time,
            end_time=start_time
        )
        
        try:
            if request.operation == HotSwapOperation.LOAD:
                result = self._handle_load(request, result)
            elif request.operation == HotSwapOperation.UNLOAD:
                result = self._handle_unload(request, result)
            elif request.operation == HotSwapOperation.RELOAD:
                result = self._handle_reload(request, result)
            elif request.operation == HotSwapOperation.UPDATE:
                result = self._handle_update(request, result)
            elif request.operation == HotSwapOperation.ROLLBACK:
                result = self._handle_rollback(request, result)
            else:
                result.error = f"Unsupported operation: {request.operation}"
                
        except Exception as e:
            result.error = str(e)
            if self._logger:
                self._logger.error(f"HotSwap operation failed: {e}")
        
        finally:
            result.end_time = time.time()
        
        return result
    
    def _handle_load(self, request: HotSwapRequest, result: HotSwapResult) -> HotSwapResult:
        """处理加载操作"""
        try:
            plugin_id = request.plugin_id
            
            # 检查插件是否已加载
            if self._plugin_manager.get_plugin(plugin_id):
                result.error = f"Plugin {plugin_id} is already loaded"
                return result
            
            # 加载插件
            load_result = self._plugin_manager.load_plugin(plugin_id)
            if load_result.success:
                result.success = True
                if self._logger:
                    self._logger.info(f"Hot-loaded plugin: {plugin_id}")
            else:
                result.error = load_result.error
            
            return result
            
        except Exception as e:
            result.error = str(e)
            return result
    
    def _handle_unload(self, request: HotSwapRequest, result: HotSwapResult) -> HotSwapResult:
        """处理卸载操作"""
        try:
            plugin_id = request.plugin_id
            
            # 检查插件是否存在
            plugin = self._plugin_manager.get_plugin(plugin_id)
            if not plugin:
                result.error = f"Plugin {plugin_id} is not loaded"
                return result
            
            # 检查依赖关系
            if not request.force:
                dependents = self._lifecycle_manager.get_plugin_dependents(plugin_id)
                if dependents:
                    result.error = f"Plugin {plugin_id} has dependents: {list(dependents)}"
                    return result
            
            # 创建备份
            if request.backup:
                backup_path = self._backup_manager.create_backup(
                    plugin_id, 
                    str(getattr(plugin.metadata, 'plugin_dir', '')),
                    plugin.metadata.version
                )
                result.backup_path = backup_path
            
            # 卸载插件
            if self._plugin_manager.unload_plugin(plugin_id):
                result.success = True
                if self._logger:
                    self._logger.info(f"Hot-unloaded plugin: {plugin_id}")
            else:
                result.error = f"Failed to unload plugin {plugin_id}"
            
            return result
            
        except Exception as e:
            result.error = str(e)
            return result
    
    def _handle_reload(self, request: HotSwapRequest, result: HotSwapResult) -> HotSwapResult:
        """处理重载操作"""
        try:
            plugin_id = request.plugin_id
            
            # 检查插件是否存在
            plugin = self._plugin_manager.get_plugin(plugin_id)
            if not plugin:
                result.error = f"Plugin {plugin_id} is not loaded"
                return result
            
            # 创建备份
            if request.backup:
                backup_path = self._backup_manager.create_backup(
                    plugin_id,
                    str(getattr(plugin.metadata, 'plugin_dir', '')),
                    plugin.metadata.version
                )
                result.backup_path = backup_path
            
            # 执行重载
            if self._plugin_manager.reload_plugin(plugin_id):
                result.success = True
                if self._logger:
                    self._logger.info(f"Hot-reloaded plugin: {plugin_id}")
            else:
                result.error = f"Failed to reload plugin {plugin_id}"
                
                # 尝试回滚
                if request.rollback_on_failure and result.backup_path:
                    if self._attempt_rollback(plugin_id, result.backup_path):
                        result.rollback_performed = True
                        result.warnings.append("Rollback performed due to reload failure")
            
            return result
            
        except Exception as e:
            result.error = str(e)
            return result
    
    def _handle_update(self, request: HotSwapRequest, result: HotSwapResult) -> HotSwapResult:
        """处理更新操作"""
        try:
            plugin_id = request.plugin_id
            source_path = request.source_path
            
            if not source_path:
                result.error = "Source path is required for update operation"
                return result
            
            # 检查插件是否存在
            plugin = self._plugin_manager.get_plugin(plugin_id)
            if not plugin:
                result.error = f"Plugin {plugin_id} is not loaded"
                return result
            
            # 创建备份
            if request.backup:
                backup_path = self._backup_manager.create_backup(
                    plugin_id,
                    str(getattr(plugin.metadata, 'plugin_dir', '')),
                    plugin.metadata.version
                )
                result.backup_path = backup_path
            
            # 停止插件
            plugin_was_active = plugin.state == PluginState.ACTIVE
            if plugin_was_active:
                self._plugin_manager.stop_plugin(plugin_id)
            
            # 卸载插件
            self._plugin_manager.unload_plugin(plugin_id)
            
            # 复制新版本
            plugin_dir = getattr(plugin.metadata, 'plugin_dir', None)
            if plugin_dir:
                # 备份原有文件
                temp_backup = None
                if not request.backup:  # 如果没有创建正式备份，创建临时备份
                    temp_backup = self._create_temp_backup(str(plugin_dir))
                
                try:
                    # 复制新文件
                    self._copy_plugin_files(source_path, str(plugin_dir))
                    
                    # 重新加载插件
                    load_result = self._plugin_manager.load_plugin(plugin_id)
                    if load_result.success:
                        # 如果之前是活跃的，重新启动
                        if plugin_was_active:
                            self._plugin_manager.start_plugin(plugin_id)
                        
                        result.success = True
                        if self._logger:
                            self._logger.info(f"Hot-updated plugin: {plugin_id}")
                    else:
                        # 更新失败，恢复备份
                        if result.backup_path:
                            self._attempt_rollback(plugin_id, result.backup_path)
                        elif temp_backup:
                            self._restore_temp_backup(temp_backup, str(plugin_dir))
                        
                        result.error = f"Failed to load updated plugin: {load_result.error}"
                        result.rollback_performed = True
                
                except Exception as e:
                    # 复制失败，恢复备份
                    if result.backup_path:
                        self._attempt_rollback(plugin_id, result.backup_path)
                    elif temp_backup:
                        self._restore_temp_backup(temp_backup, str(plugin_dir))
                    
                    result.error = f"Failed to copy plugin files: {e}"
                    result.rollback_performed = True
                
                finally:
                    # 清理临时备份
                    if temp_backup:
                        shutil.rmtree(temp_backup, ignore_errors=True)
            
            return result
            
        except Exception as e:
            result.error = str(e)
            return result
    
    def _handle_rollback(self, request: HotSwapRequest, result: HotSwapResult) -> HotSwapResult:
        """处理回滚操作"""
        try:
            plugin_id = request.plugin_id
            
            # 获取最新备份
            backup_path = self._backup_manager.get_latest_backup(plugin_id)
            if not backup_path:
                result.error = f"No backup found for plugin {plugin_id}"
                return result
            
            # 获取当前插件
            plugin = self._plugin_manager.get_plugin(plugin_id)
            plugin_was_active = plugin and plugin.state == PluginState.ACTIVE
            
            # 停止并卸载插件
            if plugin:
                if plugin_was_active:
                    self._plugin_manager.stop_plugin(plugin_id)
                self._plugin_manager.unload_plugin(plugin_id)
            
            # 恢复备份
            plugin_dir = str(getattr(plugin.metadata, 'plugin_dir', '')) if plugin else f"plugins/{plugin_id}"
            if self._backup_manager.restore_backup(plugin_id, backup_path, plugin_dir):
                # 重新加载插件
                load_result = self._plugin_manager.load_plugin(plugin_id)
                if load_result.success:
                    if plugin_was_active:
                        self._plugin_manager.start_plugin(plugin_id)
                    
                    result.success = True
                    if self._logger:
                        self._logger.info(f"Rolled back plugin: {plugin_id}")
                else:
                    result.error = f"Failed to load rolled back plugin: {load_result.error}"
            else:
                result.error = f"Failed to restore backup for plugin {plugin_id}"
            
            return result
            
        except Exception as e:
            result.error = str(e)
            return result
    
    def _attempt_rollback(self, plugin_id: str, backup_path: str) -> bool:
        """尝试回滚"""
        try:
            plugin_dir = f"plugins/{plugin_id}"  # 简化处理
            return self._backup_manager.restore_backup(plugin_id, backup_path, plugin_dir)
        except Exception:
            return False
    
    def _create_temp_backup(self, plugin_dir: str) -> str:
        """创建临时备份"""
        temp_dir = tempfile.mkdtemp(prefix="plugin_temp_backup_")
        shutil.copytree(plugin_dir, os.path.join(temp_dir, "plugin"))
        return temp_dir
    
    def _restore_temp_backup(self, temp_backup: str, plugin_dir: str):
        """恢复临时备份"""
        backup_plugin_dir = os.path.join(temp_backup, "plugin")
        if os.path.exists(plugin_dir):
            shutil.rmtree(plugin_dir)
        shutil.copytree(backup_plugin_dir, plugin_dir)
    
    def _copy_plugin_files(self, source_path: str, target_path: str):
        """复制插件文件"""
        source = Path(source_path)
        target = Path(target_path)
        
        # 删除现有目标
        if target.exists():
            if target.is_file():
                target.unlink()
            else:
                shutil.rmtree(target)
        
        # 复制新文件
        if source.is_file():
            shutil.copy2(source, target)
        else:
            shutil.copytree(source, target)
    
    def get_priority(self) -> int:
        """获取处理器优先级"""
        return 1000  # 最低优先级


class PluginHotSwapManager:
    """插件热插拔管理器"""
    
    def __init__(self,
                 plugin_manager: PluginManager,
                 lifecycle_manager: PluginLifecycleManager,
                 communication_hub: Optional[PluginCommunicationHub] = None,
                 event_bus: Optional[EventBus] = None,
                 logger: Optional[logging.Logger] = None):
        self._plugin_manager = plugin_manager
        self._lifecycle_manager = lifecycle_manager
        self._communication_hub = communication_hub
        self._event_bus = event_bus
        self._logger = logger or logging.getLogger(__name__)
        
        # 组件
        self._backup_manager = PluginBackupManager(logger=logger)
        self._file_watcher: Optional[PluginFileWatcher] = None
        
        # 处理器
        self._handlers: List[IHotSwapHandler] = []
        self._add_default_handler()
        
        # 请求队列和处理
        self._request_queue: List[HotSwapRequest] = []
        self._request_lock = threading.RLock()
        self._processing_thread: Optional[threading.Thread] = None
        self._running = False
        
        # 操作历史
        self._operation_history: List[HotSwapResult] = []
        self._max_history = 100
        
        # 自动热重载设置
        self._auto_reload_enabled = False
        self._auto_reload_delay = 2.0  # 延迟时间避免频繁重载
        
        if self._logger:
            self._logger.info("PluginHotSwapManager initialized")
    
    def _add_default_handler(self):
        """添加默认处理器"""
        default_handler = DefaultHotSwapHandler(
            self._plugin_manager,
            self._lifecycle_manager,
            self._backup_manager,
            self._logger
        )
        self.add_handler(default_handler)
    
    def start(self):
        """启动热插拔管理器"""
        if self._running:
            return
        
        self._running = True
        
        # 启动请求处理线程
        self._processing_thread = threading.Thread(target=self._process_requests, daemon=True)
        self._processing_thread.start()
        
        if self._logger:
            self._logger.info("PluginHotSwapManager started")
    
    def stop(self):
        """停止热插拔管理器"""
        if not self._running:
            return
        
        self._running = False
        
        # 停止文件监控
        if self._file_watcher:
            self._file_watcher.stop_watching()
        
        # 等待处理线程结束
        if self._processing_thread:
            self._processing_thread.join(timeout=5.0)
        
        if self._logger:
            self._logger.info("PluginHotSwapManager stopped")
    
    def add_handler(self, handler: IHotSwapHandler):
        """添加热插拔处理器"""
        self._handlers.append(handler)
        self._handlers.sort(key=lambda h: h.get_priority())
        
        if self._logger:
            self._logger.debug(f"Added hotswap handler: {handler.__class__.__name__}")
    
    def remove_handler(self, handler: IHotSwapHandler):
        """移除热插拔处理器"""
        try:
            self._handlers.remove(handler)
        except ValueError:
            pass
    
    def enable_auto_reload(self, watch_dirs: List[str], delay: float = 2.0):
        """启用自动重载"""
        self._auto_reload_enabled = True
        self._auto_reload_delay = delay
        
        # 创建文件监控器
        self._file_watcher = PluginFileWatcher(
            watch_dirs,
            self._on_file_changed,
            self._logger
        )
        
        self._file_watcher.start_watching()
        
        if self._logger:
            self._logger.info(f"Enabled auto-reload for directories: {watch_dirs}")
    
    def disable_auto_reload(self):
        """禁用自动重载"""
        self._auto_reload_enabled = False
        
        if self._file_watcher:
            self._file_watcher.stop_watching()
            self._file_watcher = None
        
        if self._logger:
            self._logger.info("Disabled auto-reload")
    
    def _on_file_changed(self, file_path: str, change_type: str):
        """文件变更回调"""
        if not self._auto_reload_enabled:
            return
        
        try:
            # 从文件路径推断插件ID
            plugin_id = self._extract_plugin_id_from_path(file_path)
            if plugin_id and self._plugin_manager.get_plugin(plugin_id):
                # 延迟重载，避免频繁操作
                def delayed_reload():
                    time.sleep(self._auto_reload_delay)
                    request = HotSwapRequest(
                        operation=HotSwapOperation.RELOAD,
                        plugin_id=plugin_id,
                        strategy=HotSwapStrategy.GRACEFUL,
                        metadata={'trigger': 'file_change', 'file_path': file_path, 'change_type': change_type}
                    )
                    self.submit_request(request)
                
                reload_thread = threading.Thread(target=delayed_reload, daemon=True)
                reload_thread.start()
                
                if self._logger:
                    self._logger.info(f"Scheduled auto-reload for plugin {plugin_id} due to {change_type}: {file_path}")
                    
        except Exception as e:
            if self._logger:
                self._logger.error(f"Error handling file change {file_path}: {e}")
    
    def _extract_plugin_id_from_path(self, file_path: str) -> Optional[str]:
        """从文件路径提取插件ID"""
        # 简化实现：假设插件目录名就是插件ID
        path = Path(file_path)
        for part in path.parts:
            if self._plugin_manager.get_plugin_metadata(part):
                return part
        return None
    
    def submit_request(self, request: HotSwapRequest) -> bool:
        """提交热插拔请求"""
        try:
            with self._request_lock:
                self._request_queue.append(request)
            
            if self._logger:
                self._logger.info(f"Submitted hotswap request: {request.operation.value} {request.plugin_id}")
            
            return True
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to submit hotswap request: {e}")
            return False
    
    def _process_requests(self):
        """处理热插拔请求"""
        while self._running:
            try:
                request = None
                
                with self._request_lock:
                    if self._request_queue:
                        request = self._request_queue.pop(0)
                
                if request:
                    result = self._execute_request(request)
                    self._record_result(result)
                    self._notify_result(result)
                else:
                    time.sleep(0.1)
                    
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Request processing error: {e}")
    
    def _execute_request(self, request: HotSwapRequest) -> HotSwapResult:
        """执行热插拔请求"""
        if self._logger:
            self._logger.info(f"Executing hotswap request: {request.operation.value} {request.plugin_id}")
        
        # 查找合适的处理器
        handler = None
        for h in self._handlers:
            if h.can_handle(request):
                handler = h
                break
        
        if not handler:
            return HotSwapResult(
                success=False,
                request=request,
                start_time=time.time(),
                end_time=time.time(),
                error="No suitable handler found"
            )
        
        # 执行操作
        result = handler.execute(request)
        
        if self._logger:
            status = "SUCCESS" if result.success else "FAILED"
            self._logger.info(f"Hotswap request {status}: {request.operation.value} {request.plugin_id} ({result.duration:.3f}s)")
            if not result.success:
                self._logger.error(f"Hotswap error: {result.error}")
        
        return result
    
    def _record_result(self, result: HotSwapResult):
        """记录操作结果"""
        self._operation_history.append(result)
        
        # 限制历史记录数量
        if len(self._operation_history) > self._max_history:
            self._operation_history = self._operation_history[-self._max_history:]
    
    def _notify_result(self, result: HotSwapResult):
        """通知操作结果"""
        try:
            # 发布事件
            if self._event_bus:
                event_type = f"plugin_hotswap_{result.request.operation.value}_{'success' if result.success else 'failed'}"
                event = ApplicationEvent(event_type, {
                    'plugin_id': result.request.plugin_id,
                    'operation': result.request.operation.value,
                    'success': result.success,
                    'duration': result.duration,
                    'error': result.error
                })
                self._event_bus.post_event(event)
            
            # 通过通信中心广播
            if self._communication_hub:
                message = {
                    'type': 'hotswap_result',
                    'plugin_id': result.request.plugin_id,
                    'operation': result.request.operation.value,
                    'success': result.success,
                    'error': result.error
                }
                self._communication_hub.broadcast_message(message)
                
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to notify hotswap result: {e}")
    
    # 查询接口
    def get_operation_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取操作历史"""
        history = self._operation_history[-limit:] if limit > 0 else self._operation_history
        return [result.to_dict() for result in history]
    
    def get_plugin_backups(self, plugin_id: str) -> List[str]:
        """获取插件备份列表"""
        return self._backup_manager.get_backups(plugin_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_operations = len(self._operation_history)
        successful_operations = sum(1 for r in self._operation_history if r.success)
        
        operation_counts = defaultdict(int)
        for result in self._operation_history:
            operation_counts[result.request.operation.value] += 1
        
        return {
            'total_operations': total_operations,
            'successful_operations': successful_operations,
            'success_rate': successful_operations / total_operations if total_operations > 0 else 0.0,
            'operations_by_type': dict(operation_counts),
            'auto_reload_enabled': self._auto_reload_enabled,
            'pending_requests': len(self._request_queue),
            'active_handlers': len(self._handlers)
        }
    
    # 便捷方法
    def hot_load_plugin(self, plugin_id: str, **kwargs) -> bool:
        """热加载插件"""
        request = HotSwapRequest(
            operation=HotSwapOperation.LOAD,
            plugin_id=plugin_id,
            **kwargs
        )
        return self.submit_request(request)
    
    def hot_unload_plugin(self, plugin_id: str, **kwargs) -> bool:
        """热卸载插件"""
        request = HotSwapRequest(
            operation=HotSwapOperation.UNLOAD,
            plugin_id=plugin_id,
            **kwargs
        )
        return self.submit_request(request)
    
    def hot_reload_plugin(self, plugin_id: str, **kwargs) -> bool:
        """热重载插件"""
        request = HotSwapRequest(
            operation=HotSwapOperation.RELOAD,
            plugin_id=plugin_id,
            **kwargs
        )
        return self.submit_request(request)
    
    def hot_update_plugin(self, plugin_id: str, source_path: str, **kwargs) -> bool:
        """热更新插件"""
        request = HotSwapRequest(
            operation=HotSwapOperation.UPDATE,
            plugin_id=plugin_id,
            source_path=source_path,
            **kwargs
        )
        return self.submit_request(request)
    
    def rollback_plugin(self, plugin_id: str, **kwargs) -> bool:
        """回滚插件"""
        request = HotSwapRequest(
            operation=HotSwapOperation.ROLLBACK,
            plugin_id=plugin_id,
            **kwargs
        )
        return self.submit_request(request)


# 便捷函数
def create_hotswap_manager(plugin_manager: PluginManager,
                          lifecycle_manager: PluginLifecycleManager,
                          communication_hub: Optional[PluginCommunicationHub] = None,
                          event_bus: Optional[EventBus] = None,
                          logger: Optional[logging.Logger] = None) -> PluginHotSwapManager:
    """创建插件热插拔管理器"""
    return PluginHotSwapManager(
        plugin_manager,
        lifecycle_manager,
        communication_hub,
        event_bus,
        logger
    )