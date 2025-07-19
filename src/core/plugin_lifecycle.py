"""
插件生命周期管理系统
提供插件生命周期的精细化管理和监控
支持异步操作、热插拔、性能监控等高级功能
"""

import asyncio
import time
import threading
import weakref
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Set, Tuple, Union
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque
import logging
from datetime import datetime, timedelta
import uuid

from .plugin_manager import PluginState, IPlugin, PluginMetadata
from .interfaces.plugin_interfaces import (
    IPluginContext, IPluginHook, PluginHookType, PluginHookResult,
    IPluginEventListener, PluginLifecycleEvent, IAsyncPlugin, IHotSwappablePlugin,
    PluginState as NewPluginState, PluginMetadata as NewPluginMetadata
)
from .application import EventBus, ApplicationEvent
from .error_handler import get_error_handler, error_handler, ErrorCategory


class LifecyclePhase(Enum):
    """生命周期阶段"""
    DISCOVERY = "discovery"
    VALIDATION = "validation"
    LOADING = "loading"
    DEPENDENCY_RESOLUTION = "dependency_resolution"
    INITIALIZATION = "initialization"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    CLEANUP = "cleanup"
    UNLOADING = "unloading"


class LifecycleTransition(Enum):
    """生命周期转换"""
    LOAD = "load"
    START = "start"
    STOP = "stop"
    UNLOAD = "unload"
    RESTART = "restart"
    RELOAD = "reload"


@dataclass
class LifecycleEvent:
    """生命周期事件"""
    plugin_id: str
    phase: LifecyclePhase
    transition: Optional[LifecycleTransition]
    timestamp: float
    success: bool
    duration: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LifecycleMetrics:
    """增强的生命周期指标"""
    plugin_id: str
    total_transitions: int = 0
    successful_transitions: int = 0
    failed_transitions: int = 0
    average_load_time: float = 0.0
    average_start_time: float = 0.0
    average_stop_time: float = 0.0
    average_reload_time: float = 0.0
    last_error: Optional[str] = None
    last_transition_time: float = 0.0
    uptime: float = 0.0
    restart_count: int = 0
    hot_swap_count: int = 0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    
    # 性能阈值监控
    load_time_threshold: float = 1.0
    start_time_threshold: float = 0.5
    memory_threshold: float = 100.0  # MB
    
    # 历史数据
    transition_history: List[Dict[str, Any]] = field(default_factory=list)
    error_history: List[Dict[str, Any]] = field(default_factory=list)
    performance_history: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_transitions == 0:
            return 0.0
        return self.successful_transitions / self.total_transitions
    
    @property
    def is_stable(self) -> bool:
        """是否稳定"""
        return (self.success_rate >= 0.95 and 
                self.restart_count <= 3 and
                self.average_load_time < self.load_time_threshold and
                self.average_start_time < self.start_time_threshold)
    
    @property
    def is_performance_critical(self) -> bool:
        """是否性能关键"""
        return (self.average_load_time > self.load_time_threshold * 2 or
                self.memory_usage > self.memory_threshold)
    
    def add_transition_record(self, transition: str, success: bool, duration: float, error: Optional[str] = None):
        """添加转换记录"""
        record = {
            "timestamp": time.time(),
            "transition": transition,
            "success": success,
            "duration": duration,
            "error": error
        }
        self.transition_history.append(record)
        
        # 保持历史记录大小
        if len(self.transition_history) > 100:
            self.transition_history.pop(0)
    
    def add_error_record(self, error: str, context: Dict[str, Any]):
        """添加错误记录"""
        record = {
            "timestamp": time.time(),
            "error": error,
            "context": context
        }
        self.error_history.append(record)
        
        # 保持历史记录大小
        if len(self.error_history) > 50:
            self.error_history.pop(0)
    
    def add_performance_record(self, cpu_usage: float, memory_usage: float):
        """添加性能记录"""
        record = {
            "timestamp": time.time(),
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage
        }
        self.performance_history.append(record)
        
        # 保持历史记录大小
        if len(self.performance_history) > 200:
            self.performance_history.pop(0)
    
    def get_recent_errors(self, hours: int = 24) -> List[Dict[str, Any]]:
        """获取最近的错误"""
        cutoff_time = time.time() - (hours * 3600)
        return [error for error in self.error_history if error["timestamp"] > cutoff_time]
    
    def get_average_performance(self, hours: int = 1) -> Dict[str, float]:
        """获取平均性能"""
        cutoff_time = time.time() - (hours * 3600)
        recent_records = [record for record in self.performance_history if record["timestamp"] > cutoff_time]
        
        if not recent_records:
            return {"cpu_usage": 0.0, "memory_usage": 0.0}
        
        total_cpu = sum(record["cpu_usage"] for record in recent_records)
        total_memory = sum(record["memory_usage"] for record in recent_records)
        count = len(recent_records)
        
        return {
            "cpu_usage": total_cpu / count,
            "memory_usage": total_memory / count
        }


class ILifecycleHandler(ABC):
    """生命周期处理器接口"""
    
    @abstractmethod
    def can_handle(self, plugin: IPlugin, phase: LifecyclePhase) -> bool:
        """检查是否可以处理指定阶段"""
        pass
    
    @abstractmethod
    def handle(self, plugin: IPlugin, phase: LifecyclePhase, context: Dict[str, Any]) -> bool:
        """处理生命周期阶段"""
        pass
    
    @abstractmethod
    def get_priority(self) -> int:
        """获取处理优先级"""
        pass


class DefaultLifecycleHandler(ILifecycleHandler):
    """默认生命周期处理器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self._logger = logger or logging.getLogger(__name__)
    
    def can_handle(self, plugin: IPlugin, phase: LifecyclePhase) -> bool:
        """所有插件和阶段都可以处理"""
        return True
    
    def handle(self, plugin: IPlugin, phase: LifecyclePhase, context: Dict[str, Any]) -> bool:
        """处理生命周期阶段"""
        try:
            if phase == LifecyclePhase.LOADING:
                return plugin.load()
            elif phase == LifecyclePhase.STARTING:
                return plugin.start()
            elif phase == LifecyclePhase.STOPPING:
                return plugin.stop()
            elif phase == LifecyclePhase.UNLOADING:
                return plugin.unload()
            else:
                # 其他阶段默认返回成功
                return True
                
        except Exception as e:
            if self._logger:
                self._logger.error(f"Lifecycle handler error for {plugin.metadata.name} in {phase}: {e}")
            return False
    
    def get_priority(self) -> int:
        """最低优先级"""
        return 1000


class PluginDependencyResolver:
    """插件依赖解析器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self._logger = logger or logging.getLogger(__name__)
        self._dependency_graph: Dict[str, Set[str]] = {}
        self._reverse_graph: Dict[str, Set[str]] = {}
    
    def add_plugin(self, plugin_id: str, dependencies: List[str]):
        """添加插件及其依赖"""
        self._dependency_graph[plugin_id] = set(dependencies)
        
        # 更新反向依赖图
        if plugin_id not in self._reverse_graph:
            self._reverse_graph[plugin_id] = set()
        
        for dep in dependencies:
            if dep not in self._reverse_graph:
                self._reverse_graph[dep] = set()
            self._reverse_graph[dep].add(plugin_id)
    
    def remove_plugin(self, plugin_id: str):
        """移除插件"""
        if plugin_id in self._dependency_graph:
            # 移除对其他插件的依赖
            dependencies = self._dependency_graph[plugin_id]
            for dep in dependencies:
                if dep in self._reverse_graph:
                    self._reverse_graph[dep].discard(plugin_id)
            
            del self._dependency_graph[plugin_id]
        
        # 移除其他插件对此插件的依赖
        if plugin_id in self._reverse_graph:
            dependents = self._reverse_graph[plugin_id]
            for dependent in dependents:
                if dependent in self._dependency_graph:
                    self._dependency_graph[dependent].discard(plugin_id)
            
            del self._reverse_graph[plugin_id]
    
    def get_load_order(self, plugin_ids: List[str]) -> List[str]:
        """获取加载顺序（拓扑排序）"""
        # 过滤出实际存在的插件
        valid_plugins = [pid for pid in plugin_ids if pid in self._dependency_graph]
        
        if not valid_plugins:
            return []
        
        # 拓扑排序
        in_degree = {}
        for plugin_id in valid_plugins:
            in_degree[plugin_id] = 0
        
        for plugin_id in valid_plugins:
            for dep in self._dependency_graph[plugin_id]:
                if dep in in_degree:
                    in_degree[plugin_id] += 1
        
        queue = deque([pid for pid in valid_plugins if in_degree[pid] == 0])
        result = []
        
        while queue:
            current = queue.popleft()
            result.append(current)
            
            # 更新依赖此插件的其他插件
            if current in self._reverse_graph:
                for dependent in self._reverse_graph[current]:
                    if dependent in in_degree:
                        in_degree[dependent] -= 1
                        if in_degree[dependent] == 0:
                            queue.append(dependent)
        
        # 检查是否有循环依赖
        if len(result) != len(valid_plugins):
            remaining = [pid for pid in valid_plugins if pid not in result]
            if self._logger:
                self._logger.error(f"Circular dependency detected: {remaining}")
            # 添加剩余插件到结果中
            result.extend(remaining)
        
        return result
    
    def get_stop_order(self, plugin_ids: List[str]) -> List[str]:
        """获取停止顺序（加载顺序的逆序）"""
        load_order = self.get_load_order(plugin_ids)
        return load_order[::-1]
    
    def check_dependencies(self, plugin_id: str, available_plugins: Set[str]) -> List[str]:
        """检查插件依赖，返回缺失的依赖"""
        if plugin_id not in self._dependency_graph:
            return []
        
        dependencies = self._dependency_graph[plugin_id]
        missing = []
        
        for dep in dependencies:
            if dep not in available_plugins:
                missing.append(dep)
        
        return missing
    
    def get_dependents(self, plugin_id: str) -> Set[str]:
        """获取依赖此插件的其他插件"""
        return self._reverse_graph.get(plugin_id, set())
    
    def has_circular_dependency(self, plugin_id: str) -> bool:
        """检查是否存在循环依赖"""
        visited = set()
        rec_stack = set()
        
        def dfs(current: str) -> bool:
            visited.add(current)
            rec_stack.add(current)
            
            if current in self._dependency_graph:
                for neighbor in self._dependency_graph[current]:
                    if neighbor not in visited:
                        if dfs(neighbor):
                            return True
                    elif neighbor in rec_stack:
                        return True
            
            rec_stack.remove(current)
            return False
        
        return dfs(plugin_id)


class IAsyncLifecycleHandler(ABC):
    """异步生命周期处理器接口"""
    
    @abstractmethod
    async def can_handle_async(self, plugin: Union[IPlugin, IAsyncPlugin], phase: LifecyclePhase) -> bool:
        """异步检查是否可以处理指定阶段"""
        pass
    
    @abstractmethod
    async def handle_async(self, plugin: Union[IPlugin, IAsyncPlugin], 
                          phase: LifecyclePhase, context: Dict[str, Any]) -> bool:
        """异步处理生命周期阶段"""
        pass
    
    @abstractmethod
    def get_priority(self) -> int:
        """获取处理优先级"""
        pass


class DefaultAsyncLifecycleHandler(IAsyncLifecycleHandler):
    """默认异步生命周期处理器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self._logger = logger or logging.getLogger(__name__)
    
    async def can_handle_async(self, plugin: Union[IPlugin, IAsyncPlugin], phase: LifecyclePhase) -> bool:
        """所有插件和阶段都可以处理"""
        return True
    
    async def handle_async(self, plugin: Union[IPlugin, IAsyncPlugin], 
                          phase: LifecyclePhase, context: Dict[str, Any]) -> bool:
        """异步处理生命周期阶段"""
        try:
            if isinstance(plugin, IAsyncPlugin):
                if phase == LifecyclePhase.INITIALIZATION:
                    return await plugin.initialize()
                elif phase == LifecyclePhase.STARTING:
                    return await plugin.start()
                elif phase == LifecyclePhase.STOPPING:
                    return await plugin.stop()
                elif phase == LifecyclePhase.CLEANUP:
                    return await plugin.cleanup()
                else:
                    return True
            else:
                # 同步插件的处理
                if phase == LifecyclePhase.LOADING:
                    return plugin.load()
                elif phase == LifecyclePhase.STARTING:
                    return plugin.start()
                elif phase == LifecyclePhase.STOPPING:
                    return plugin.stop()
                elif phase == LifecyclePhase.UNLOADING:
                    return plugin.unload()
                else:
                    return True
                    
        except Exception as e:
            if self._logger:
                self._logger.error(f"Async lifecycle handler error for {plugin.plugin_id if hasattr(plugin, 'plugin_id') else 'unknown'} in {phase}: {e}")
            return False
    
    def get_priority(self) -> int:
        """最低优先级"""
        return 1000


class HotSwapManager:
    """热插拔管理器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self._logger = logger or logging.getLogger(__name__)
        self.error_handler = get_error_handler()
        self._swap_states: Dict[str, Dict[str, Any]] = {}
        self._rollback_data: Dict[str, Dict[str, Any]] = {}
    
    @error_handler(component="HotSwapManager", category=ErrorCategory.SYSTEM)
    async def prepare_hot_swap(self, plugin: IHotSwappablePlugin) -> bool:
        """准备热插拔"""
        try:
            plugin_id = plugin.plugin_id
            
            # 验证是否支持热插拔
            if not hasattr(plugin, 'prepare_hot_swap'):
                return False
            
            # 保存当前状态
            state_data = await plugin.prepare_hot_swap()
            self._swap_states[plugin_id] = state_data
            
            # 创建回滚数据
            self._rollback_data[plugin_id] = {
                "state": plugin.state,
                "metadata": plugin.metadata,
                "timestamp": time.time()
            }
            
            if self._logger:
                self._logger.info(f"Hot swap prepared for plugin {plugin_id}")
            
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, component="HotSwapManager")
            return False
    
    @error_handler(component="HotSwapManager", category=ErrorCategory.SYSTEM)
    async def execute_hot_swap(self, old_plugin: IHotSwappablePlugin, 
                              new_plugin: IHotSwappablePlugin) -> bool:
        """执行热插拔"""
        try:
            plugin_id = old_plugin.plugin_id
            
            if plugin_id not in self._swap_states:
                return False
            
            # 验证新版本兼容性
            if hasattr(old_plugin, 'validate_hot_swap'):
                if not await old_plugin.validate_hot_swap(new_plugin.metadata.version):
                    return False
            
            # 停止旧插件
            await old_plugin.stop()
            
            # 启动新插件并恢复状态
            await new_plugin.initialize()
            state_data = self._swap_states[plugin_id]
            
            if await new_plugin.complete_hot_swap(state_data):
                await new_plugin.start()
                
                # 清理交换状态
                del self._swap_states[plugin_id]
                
                if self._logger:
                    self._logger.info(f"Hot swap completed successfully for plugin {plugin_id}")
                
                return True
            else:
                # 回滚
                await self.rollback_hot_swap(old_plugin, plugin_id)
                return False
                
        except Exception as e:
            self.error_handler.handle_error(e, component="HotSwapManager")
            await self.rollback_hot_swap(old_plugin, plugin_id)
            return False
    
    @error_handler(component="HotSwapManager", category=ErrorCategory.SYSTEM)
    async def rollback_hot_swap(self, plugin: IHotSwappablePlugin, plugin_id: str) -> bool:
        """回滚热插拔"""
        try:
            if plugin_id in self._rollback_data:
                rollback_data = self._rollback_data[plugin_id]
                
                # 恢复到原始状态
                if hasattr(plugin, 'complete_hot_swap'):
                    await plugin.complete_hot_swap(rollback_data)
                
                # 清理数据
                del self._rollback_data[plugin_id]
                if plugin_id in self._swap_states:
                    del self._swap_states[plugin_id]
                
                if self._logger:
                    self._logger.info(f"Hot swap rolled back for plugin {plugin_id}")
                
                return True
            
            return False
            
        except Exception as e:
            self.error_handler.handle_error(e, component="HotSwapManager")
            return False


class AsyncPluginLifecycleManager:
    """异步插件生命周期管理器"""
    
    def __init__(self, 
                 event_bus: Optional[EventBus] = None,
                 logger: Optional[logging.Logger] = None):
        self._event_bus = event_bus
        self._logger = logger or logging.getLogger(__name__)
        self.error_handler = get_error_handler()
        
        # 生命周期状态
        self._plugin_states: Dict[str, NewPluginState] = {}
        self._plugin_phases: Dict[str, LifecyclePhase] = {}
        self._plugin_instances: Dict[str, Union[IPlugin, IAsyncPlugin]] = {}
        
        # 事件和指标
        self._lifecycle_events: deque = deque(maxlen=1000)
        self._lifecycle_metrics: Dict[str, LifecycleMetrics] = {}
        
        # 生命周期处理器
        self._handlers: List[ILifecycleHandler] = []
        self._async_handlers: List['IAsyncLifecycleHandler'] = []
        self._hooks: Dict[PluginHookType, List[IPluginHook]] = defaultdict(list)
        
        # 依赖解析
        self._dependency_resolver = PluginDependencyResolver(logger)
        
        # 事件监听器
        self._event_listeners: List[IPluginEventListener] = []
        
        # 异步任务管理
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._task_lock = asyncio.Lock()
        
        # 热插拔支持
        self._hot_swap_states: Dict[str, Dict[str, Any]] = {}
        self._rollback_data: Dict[str, Dict[str, Any]] = {}
        
        # 性能监控
        self._performance_monitor_task: Optional[asyncio.Task] = None
        self._monitoring_enabled = True
        self._monitoring_interval = 30.0  # 秒
        
        # 线程安全
        self._lock = threading.RLock()
        
        # 健康检查
        self._health_check_interval = 60.0  # 秒
        self._health_check_task: Optional[asyncio.Task] = None
        
        # 添加默认处理器
        self.add_handler(DefaultLifecycleHandler(logger))
        
        if self._logger:
            self._logger.info("AsyncPluginLifecycleManager initialized")
    
    async def initialize(self) -> None:
        """初始化生命周期管理器"""
        try:
            # 启动性能监控
            if self._monitoring_enabled:
                self._performance_monitor_task = asyncio.create_task(self._performance_monitor_loop())
            
            # 启动健康检查
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            
            if self._logger:
                self._logger.info("AsyncPluginLifecycleManager initialized successfully")
                
        except Exception as e:
            self.error_handler.handle_error(e, component="AsyncPluginLifecycleManager")
            raise
    
    async def shutdown(self) -> None:
        """关闭生命周期管理器"""
        try:
            # 取消所有任务
            if self._performance_monitor_task:
                self._performance_monitor_task.cancel()
            
            if self._health_check_task:
                self._health_check_task.cancel()
            
            # 等待活动任务完成
            if self._active_tasks:
                await asyncio.gather(*self._active_tasks.values(), return_exceptions=True)
            
            if self._logger:
                self._logger.info("AsyncPluginLifecycleManager shutdown completed")
                
        except Exception as e:
            self.error_handler.handle_error(e, component="AsyncPluginLifecycleManager")
    
    async def _performance_monitor_loop(self) -> None:
        """性能监控循环"""
        while True:
            try:
                await asyncio.sleep(self._monitoring_interval)
                await self._collect_performance_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.error_handler.handle_error(e, component="PerformanceMonitor")
    
    async def _health_check_loop(self) -> None:
        """健康检查循环"""
        while True:
            try:
                await asyncio.sleep(self._health_check_interval)
                await self._perform_health_checks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.error_handler.handle_error(e, component="HealthCheck")
    
    async def _collect_performance_metrics(self) -> None:
        """收集性能指标"""
        for plugin_id, plugin in self._plugin_instances.items():
            try:
                if isinstance(plugin, IAsyncPlugin):
                    health_status = await plugin.get_health_status_async()
                else:
                    health_status = plugin.get_health_status()
                
                if plugin_id in self._lifecycle_metrics:
                    metrics = self._lifecycle_metrics[plugin_id]
                    cpu_usage = health_status.get("cpu_usage", 0.0)
                    memory_usage = health_status.get("memory_usage", 0.0)
                    
                    metrics.cpu_usage = cpu_usage
                    metrics.memory_usage = memory_usage
                    metrics.add_performance_record(cpu_usage, memory_usage)
                    
            except Exception as e:
                self.error_handler.handle_error(
                    e, 
                    component="PerformanceMonitor",
                    context={"plugin_id": plugin_id}
                )
    
    async def _perform_health_checks(self) -> None:
        """执行健康检查"""
        for plugin_id, plugin in self._plugin_instances.items():
            try:
                if isinstance(plugin, IAsyncPlugin):
                    health_status = await plugin.get_health_status_async()
                else:
                    health_status = plugin.get_health_status()
                
                # 检查健康状态
                if health_status.get("status") != "healthy":
                    await self._handle_unhealthy_plugin(plugin_id, health_status)
                    
            except Exception as e:
                await self._handle_unhealthy_plugin(plugin_id, {"error": str(e)})
    
    async def _handle_unhealthy_plugin(self, plugin_id: str, health_status: Dict[str, Any]) -> None:
        """处理不健康的插件"""
        try:
            if self._logger:
                self._logger.warning(f"Plugin {plugin_id} is unhealthy: {health_status}")
            
            # 记录错误
            if plugin_id in self._lifecycle_metrics:
                metrics = self._lifecycle_metrics[plugin_id]
                error_msg = health_status.get("error", "Plugin unhealthy")
                metrics.add_error_record(error_msg, health_status)
            
            # 可以在这里实现自动重启等策略
            
        except Exception as e:
            self.error_handler.handle_error(e, component="HealthCheck")
    
    def add_handler(self, handler: ILifecycleHandler):
        """添加生命周期处理器"""
        with self._lock:
            self._handlers.append(handler)
            # 按优先级排序
            self._handlers.sort(key=lambda h: h.get_priority())
            
            if self._logger:
                self._logger.debug(f"Added lifecycle handler: {handler.__class__.__name__}")
    
    def remove_handler(self, handler: ILifecycleHandler):
        """移除生命周期处理器"""
        with self._lock:
            try:
                self._handlers.remove(handler)
            except ValueError:
                pass
    
    def add_hook(self, hook: IPluginHook):
        """添加插件钩子"""
        hook_type = hook.get_hook_type()
        self._hooks[hook_type].append(hook)
        # 按优先级排序
        self._hooks[hook_type].sort(key=lambda h: h.get_priority())
        
        if self._logger:
            self._logger.debug(f"Added plugin hook: {hook_type}")
    
    def remove_hook(self, hook: IPluginHook):
        """移除插件钩子"""
        hook_type = hook.get_hook_type()
        try:
            self._hooks[hook_type].remove(hook)
        except ValueError:
            pass
    
    def add_event_listener(self, listener: IPluginEventListener):
        """添加事件监听器"""
        self._event_listeners.append(listener)
    
    def remove_event_listener(self, listener: IPluginEventListener):
        """移除事件监听器"""
        try:
            self._event_listeners.remove(listener)
        except ValueError:
            pass
    
    def register_plugin(self, plugin: IPlugin):
        """注册插件到生命周期管理"""
        plugin_id = plugin.metadata.name
        
        with self._lock:
            self._plugin_states[plugin_id] = plugin.state
            self._plugin_phases[plugin_id] = LifecyclePhase.DISCOVERY
            
            # 初始化指标
            if plugin_id not in self._lifecycle_metrics:
                self._lifecycle_metrics[plugin_id] = LifecycleMetrics(plugin_id=plugin_id)
            
            # 添加到依赖解析器
            self._dependency_resolver.add_plugin(plugin_id, plugin.metadata.dependencies)
            
            if self._logger:
                self._logger.info(f"Registered plugin for lifecycle management: {plugin_id}")
    
    def unregister_plugin(self, plugin_id: str):
        """从生命周期管理中注销插件"""
        with self._lock:
            self._plugin_states.pop(plugin_id, None)
            self._plugin_phases.pop(plugin_id, None)
            self._lifecycle_metrics.pop(plugin_id, None)
            
            # 从依赖解析器中移除
            self._dependency_resolver.remove_plugin(plugin_id)
            
            if self._logger:
                self._logger.info(f"Unregistered plugin from lifecycle management: {plugin_id}")
    
    def transition_plugin(self, plugin: IPlugin, transition: LifecycleTransition, 
                         context: Optional[Dict[str, Any]] = None) -> bool:
        """执行插件生命周期转换"""
        plugin_id = plugin.metadata.name
        start_time = time.time()
        success = False
        error = None
        
        try:
            with self._lock:
                current_state = self._plugin_states.get(plugin_id, PluginState.UNLOADED)
                
                # 验证转换是否有效
                if not self._is_valid_transition(current_state, transition):
                    error = f"Invalid transition {transition} from state {current_state}"
                    if self._logger:
                        self._logger.error(f"Plugin {plugin_id}: {error}")
                    return False
                
                # 确定目标阶段
                target_phases = self._get_transition_phases(transition)
                
                # 执行转换的各个阶段
                success = True
                for phase in target_phases:
                    if not self._execute_phase(plugin, phase, context or {}):
                        success = False
                        error = f"Failed in phase {phase}"
                        break
                    
                    # 更新当前阶段
                    self._plugin_phases[plugin_id] = phase
                
                # 更新插件状态
                if success:
                    new_state = self._get_target_state(transition)
                    self._plugin_states[plugin_id] = new_state
                    plugin._state = new_state
                else:
                    self._plugin_states[plugin_id] = PluginState.ERROR
                    plugin._state = PluginState.ERROR
        
        except Exception as e:
            success = False
            error = str(e)
            if self._logger:
                self._logger.error(f"Plugin {plugin_id} transition error: {e}")
        
        finally:
            duration = time.time() - start_time
            
            # 记录生命周期事件
            event = LifecycleEvent(
                plugin_id=plugin_id,
                phase=self._plugin_phases.get(plugin_id, LifecyclePhase.DISCOVERY),
                transition=transition,
                timestamp=start_time,
                success=success,
                duration=duration,
                error=error
            )
            
            self._record_lifecycle_event(event)
            self._update_metrics(plugin_id, transition, success, duration, error)
            
            # 通知事件监听器
            self._notify_listeners(plugin_id, transition, success, error)
            
            # 发布应用程序事件
            if self._event_bus:
                app_event = ApplicationEvent(
                    f"plugin_{transition.value}{'_success' if success else '_failed'}",
                    {
                        "plugin_id": plugin_id,
                        "transition": transition.value,
                        "duration": duration,
                        "error": error
                    }
                )
                self._event_bus.post_event(app_event)
        
        return success
    
    def _is_valid_transition(self, current_state: PluginState, transition: LifecycleTransition) -> bool:
        """检查转换是否有效"""
        valid_transitions = {
            PluginState.UNLOADED: [LifecycleTransition.LOAD],
            PluginState.LOADED: [LifecycleTransition.START, LifecycleTransition.UNLOAD, LifecycleTransition.RELOAD],
            PluginState.ACTIVE: [LifecycleTransition.STOP, LifecycleTransition.RESTART],
            PluginState.STOPPED: [LifecycleTransition.START, LifecycleTransition.UNLOAD],
            PluginState.ERROR: [LifecycleTransition.UNLOAD, LifecycleTransition.RELOAD, LifecycleTransition.RESTART]
        }
        
        return transition in valid_transitions.get(current_state, [])
    
    def _get_transition_phases(self, transition: LifecycleTransition) -> List[LifecyclePhase]:
        """获取转换需要的阶段"""
        phase_map = {
            LifecycleTransition.LOAD: [
                LifecyclePhase.VALIDATION,
                LifecyclePhase.LOADING,
                LifecyclePhase.DEPENDENCY_RESOLUTION,
                LifecyclePhase.INITIALIZATION
            ],
            LifecycleTransition.START: [
                LifecyclePhase.STARTING
            ],
            LifecycleTransition.STOP: [
                LifecyclePhase.STOPPING
            ],
            LifecycleTransition.UNLOAD: [
                LifecyclePhase.CLEANUP,
                LifecyclePhase.UNLOADING
            ],
            LifecycleTransition.RESTART: [
                LifecyclePhase.STOPPING,
                LifecyclePhase.STARTING
            ],
            LifecycleTransition.RELOAD: [
                LifecyclePhase.STOPPING,
                LifecyclePhase.CLEANUP,
                LifecyclePhase.UNLOADING,
                LifecyclePhase.LOADING,
                LifecyclePhase.DEPENDENCY_RESOLUTION,
                LifecyclePhase.INITIALIZATION,
                LifecyclePhase.STARTING
            ]
        }
        
        return phase_map.get(transition, [])
    
    def _get_target_state(self, transition: LifecycleTransition) -> PluginState:
        """获取转换的目标状态"""
        state_map = {
            LifecycleTransition.LOAD: PluginState.LOADED,
            LifecycleTransition.START: PluginState.ACTIVE,
            LifecycleTransition.STOP: PluginState.STOPPED,
            LifecycleTransition.UNLOAD: PluginState.UNLOADED,
            LifecycleTransition.RESTART: PluginState.ACTIVE,
            LifecycleTransition.RELOAD: PluginState.ACTIVE
        }
        
        return state_map.get(transition, PluginState.ERROR)
    
    def _execute_phase(self, plugin: IPlugin, phase: LifecyclePhase, context: Dict[str, Any]) -> bool:
        """执行生命周期阶段"""
        plugin_id = plugin.metadata.name
        
        # 执行前置钩子
        hook_type = self._get_hook_type_for_phase(phase, True)
        if hook_type and not self._execute_hooks(plugin, hook_type, context):
            return False
        
        # 查找合适的处理器
        handler = None
        for h in self._handlers:
            if h.can_handle(plugin, phase):
                handler = h
                break
        
        if not handler:
            if self._logger:
                self._logger.error(f"No handler found for plugin {plugin_id} phase {phase}")
            return False
        
        # 执行阶段处理
        success = handler.handle(plugin, phase, context)
        
        # 执行后置钩子
        hook_type = self._get_hook_type_for_phase(phase, False)
        if hook_type and success:
            self._execute_hooks(plugin, hook_type, context)
        
        return success
    
    def _get_hook_type_for_phase(self, phase: LifecyclePhase, is_before: bool) -> Optional[PluginHookType]:
        """获取阶段对应的钩子类型"""
        hook_map = {
            LifecyclePhase.STARTING: PluginHookType.BEFORE_START if is_before else PluginHookType.AFTER_START,
            LifecyclePhase.STOPPING: PluginHookType.BEFORE_STOP if is_before else PluginHookType.AFTER_STOP
        }
        
        return hook_map.get(phase)
    
    def _execute_hooks(self, plugin: IPlugin, hook_type: PluginHookType, context: Dict[str, Any]) -> bool:
        """执行插件钩子"""
        hooks = self._hooks.get(hook_type, [])
        success = True
        
        # 创建插件上下文
        plugin_context = self._create_plugin_context(plugin)
        
        for hook in hooks:
            try:
                if hook.can_execute(plugin_context, context):
                    result = hook.execute(plugin_context, context)
                    if not result.success:
                        success = False
                        if self._logger:
                            self._logger.warning(f"Hook {hook.__class__.__name__} failed for plugin {plugin.metadata.name}: {result.error}")
            except Exception as e:
                success = False
                if self._logger:
                    self._logger.error(f"Hook {hook.__class__.__name__} error for plugin {plugin.metadata.name}: {e}")
        
        return success
    
    def _create_plugin_context(self, plugin: IPlugin) -> IPluginContext:
        """创建插件上下文"""
        # 这里应该返回一个具体的上下文实现
        # 暂时返回None，在实际使用时需要实现
        return None
    
    def _record_lifecycle_event(self, event: LifecycleEvent):
        """记录生命周期事件"""
        self._lifecycle_events.append(event)
        
        if self._logger:
            level = logging.INFO if event.success else logging.ERROR
            self._logger.log(
                level,
                f"Plugin {event.plugin_id}: {event.transition.value if event.transition else 'phase'} "
                f"{event.phase.value} - {'SUCCESS' if event.success else 'FAILED'} "
                f"({event.duration:.3f}s)"
            )
    
    def _update_metrics(self, plugin_id: str, transition: LifecycleTransition, 
                       success: bool, duration: float, error: Optional[str]):
        """更新插件指标"""
        if plugin_id not in self._lifecycle_metrics:
            self._lifecycle_metrics[plugin_id] = LifecycleMetrics(plugin_id=plugin_id)
        
        metrics = self._lifecycle_metrics[plugin_id]
        metrics.total_transitions += 1
        
        if success:
            metrics.successful_transitions += 1
        else:
            metrics.failed_transitions += 1
            metrics.last_error = error
        
        metrics.last_transition_time = time.time()
        
        # 更新特定转换的平均时间
        if transition == LifecycleTransition.LOAD:
            if metrics.average_load_time == 0:
                metrics.average_load_time = duration
            else:
                metrics.average_load_time = (metrics.average_load_time + duration) / 2
        elif transition == LifecycleTransition.START:
            if metrics.average_start_time == 0:
                metrics.average_start_time = duration
            else:
                metrics.average_start_time = (metrics.average_start_time + duration) / 2
        elif transition == LifecycleTransition.STOP:
            if metrics.average_stop_time == 0:
                metrics.average_stop_time = duration
            else:
                metrics.average_stop_time = (metrics.average_stop_time + duration) / 2
        elif transition in [LifecycleTransition.RESTART, LifecycleTransition.RELOAD]:
            metrics.restart_count += 1
    
    def _notify_listeners(self, plugin_id: str, transition: LifecycleTransition, 
                         success: bool, error: Optional[str]):
        """通知事件监听器"""
        for listener in self._event_listeners:
            try:
                if transition == LifecycleTransition.LOAD and success:
                    listener.on_plugin_loaded(plugin_id)
                elif transition == LifecycleTransition.START and success:
                    listener.on_plugin_started(plugin_id)
                elif transition == LifecycleTransition.STOP and success:
                    listener.on_plugin_stopped(plugin_id)
                elif transition == LifecycleTransition.UNLOAD and success:
                    listener.on_plugin_unloaded(plugin_id)
                elif not success:
                    listener.on_plugin_error(plugin_id, Exception(error or "Unknown error"))
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Event listener error: {e}")
    
    # 查询接口
    def get_plugin_state(self, plugin_id: str) -> Optional[PluginState]:
        """获取插件状态"""
        return self._plugin_states.get(plugin_id)
    
    def get_plugin_phase(self, plugin_id: str) -> Optional[LifecyclePhase]:
        """获取插件当前阶段"""
        return self._plugin_phases.get(plugin_id)
    
    def get_lifecycle_metrics(self, plugin_id: str) -> Optional[LifecycleMetrics]:
        """获取插件生命周期指标"""
        return self._lifecycle_metrics.get(plugin_id)
    
    def get_all_metrics(self) -> Dict[str, LifecycleMetrics]:
        """获取所有插件的生命周期指标"""
        return self._lifecycle_metrics.copy()
    
    def get_lifecycle_events(self, plugin_id: Optional[str] = None, 
                            limit: int = 100) -> List[LifecycleEvent]:
        """获取生命周期事件"""
        events = list(self._lifecycle_events)
        
        if plugin_id:
            events = [e for e in events if e.plugin_id == plugin_id]
        
        # 按时间倒序排列
        events.sort(key=lambda e: e.timestamp, reverse=True)
        
        return events[:limit]
    
    def get_dependency_order(self, plugin_ids: List[str], operation: str = "load") -> List[str]:
        """获取插件的依赖顺序"""
        if operation == "load":
            return self._dependency_resolver.get_load_order(plugin_ids)
        elif operation == "stop":
            return self._dependency_resolver.get_stop_order(plugin_ids)
        else:
            return plugin_ids
    
    def check_plugin_dependencies(self, plugin_id: str, available_plugins: Set[str]) -> List[str]:
        """检查插件依赖"""
        return self._dependency_resolver.check_dependencies(plugin_id, available_plugins)
    
    def get_plugin_dependents(self, plugin_id: str) -> Set[str]:
        """获取依赖指定插件的其他插件"""
        return self._dependency_resolver.get_dependents(plugin_id)
    
    def has_circular_dependency(self, plugin_id: str) -> bool:
        """检查是否存在循环依赖"""
        return self._dependency_resolver.has_circular_dependency(plugin_id)
    
    # 批量操作
    def batch_transition(self, plugins: List[IPlugin], transition: LifecycleTransition, 
                        respect_dependencies: bool = True) -> Dict[str, bool]:
        """批量执行插件生命周期转换"""
        results = {}
        
        if respect_dependencies:
            plugin_ids = [p.metadata.name for p in plugins]
            ordered_ids = self.get_dependency_order(plugin_ids, transition.value)
            
            # 按依赖顺序执行
            for plugin_id in ordered_ids:
                plugin = next((p for p in plugins if p.metadata.name == plugin_id), None)
                if plugin:
                    results[plugin_id] = self.transition_plugin(plugin, transition)
        else:
            # 并行执行
            for plugin in plugins:
                results[plugin.metadata.name] = self.transition_plugin(plugin, transition)
        
        return results
    
    def restart_failed_plugins(self) -> Dict[str, bool]:
        """重启失败的插件"""
        failed_plugins = []
        
        for plugin_id, state in self._plugin_states.items():
            if state == PluginState.ERROR:
                # 这里需要从某个地方获取插件实例
                # 在实际实现中，需要与PluginManager集成
                pass
        
        # 暂时返回空结果
        return {}


# 便捷函数
def create_lifecycle_manager(event_bus: Optional[EventBus] = None,
                           logger: Optional[logging.Logger] = None) -> PluginLifecycleManager:
    """创建插件生命周期管理器"""
    return PluginLifecycleManager(event_bus, logger)