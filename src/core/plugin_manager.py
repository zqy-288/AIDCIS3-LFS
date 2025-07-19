"""
插件管理器
实现插件系统的核心管理功能，包括插件加载、生命周期管理、沙箱隔离等
"""

import os
import sys
import time
import json
import importlib
import importlib.util
import threading
import weakref
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Type, Union, Set
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict
import logging
import traceback

# 导入依赖注入框架
from .dependency_injection import DependencyContainer, injectable, ServiceLifetime
from .interfaces.service_interfaces import IService, ServiceStatus, ILogger, IConfigurationManager
from .application import EventBus, ApplicationEvent
from .plugin_security import PluginSecurityManager, SecurityLevel, create_security_manager


class PluginState(Enum):
    """插件状态枚举"""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    STARTING = "starting"
    ACTIVE = "active"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    DISABLED = "disabled"


class PluginType(Enum):
    """插件类型枚举"""
    UI_COMPONENT = "ui_component"
    DATA_PROCESSOR = "data_processor"
    HARDWARE_DRIVER = "hardware_driver"
    REPORT_GENERATOR = "report_generator"
    ALGORITHM = "algorithm"
    EXTENSION = "extension"


@dataclass
class PluginMetadata:
    """插件元数据"""
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    entry_point: str
    dependencies: List[str] = field(default_factory=list)
    api_version: str = "1.0.0"
    min_app_version: str = "1.0.0"
    max_app_version: Optional[str] = None
    permissions: List[str] = field(default_factory=list)
    config_schema: Optional[Dict[str, Any]] = None
    tags: List[str] = field(default_factory=list)
    enabled: bool = True
    auto_start: bool = True
    priority: int = 100  # 数值越小优先级越高

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginMetadata':
        """从字典创建元数据"""
        plugin_type = PluginType(data.get('plugin_type', 'extension'))
        return cls(
            name=data['name'],
            version=data['version'],
            description=data.get('description', ''),
            author=data.get('author', ''),
            plugin_type=plugin_type,
            entry_point=data['entry_point'],
            dependencies=data.get('dependencies', []),
            api_version=data.get('api_version', '1.0.0'),
            min_app_version=data.get('min_app_version', '1.0.0'),
            max_app_version=data.get('max_app_version'),
            permissions=data.get('permissions', []),
            config_schema=data.get('config_schema'),
            tags=data.get('tags', []),
            enabled=data.get('enabled', True),
            auto_start=data.get('auto_start', True),
            priority=data.get('priority', 100)
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'plugin_type': self.plugin_type.value,
            'entry_point': self.entry_point,
            'dependencies': self.dependencies,
            'api_version': self.api_version,
            'min_app_version': self.min_app_version,
            'max_app_version': self.max_app_version,
            'permissions': self.permissions,
            'config_schema': self.config_schema,
            'tags': self.tags,
            'enabled': self.enabled,
            'auto_start': self.auto_start,
            'priority': self.priority
        }


class IPlugin(ABC):
    """插件基础接口"""
    
    def __init__(self, metadata: PluginMetadata):
        self.metadata = metadata
        self._state = PluginState.UNLOADED
        self._container: Optional[DependencyContainer] = None
        self._config: Dict[str, Any] = {}
        self._logger: Optional[ILogger] = None
        self._event_handlers: Dict[str, List[Callable]] = defaultdict(list)
    
    @property
    def state(self) -> PluginState:
        """获取插件状态"""
        return self._state
    
    @property
    def container(self) -> Optional[DependencyContainer]:
        """获取依赖注入容器"""
        return self._container
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取插件配置"""
        return self._config
    
    @property
    def logger(self) -> Optional[ILogger]:
        """获取日志记录器"""
        return self._logger
    
    def set_dependencies(self, container: DependencyContainer, config: Dict[str, Any], logger: ILogger):
        """设置插件依赖"""
        self._container = container
        self._config = config
        self._logger = logger
    
    @abstractmethod
    def load(self) -> bool:
        """加载插件"""
        pass
    
    @abstractmethod
    def start(self) -> bool:
        """启动插件"""
        pass
    
    @abstractmethod
    def stop(self) -> bool:
        """停止插件"""
        pass
    
    @abstractmethod
    def unload(self) -> bool:
        """卸载插件"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """获取插件状态信息"""
        return {
            'name': self.metadata.name,
            'version': self.metadata.version,
            'state': self._state.value,
            'type': self.metadata.plugin_type.value,
            'enabled': self.metadata.enabled
        }
    
    def validate_dependencies(self, available_plugins: Set[str]) -> List[str]:
        """验证插件依赖，返回缺失的依赖列表"""
        missing = []
        for dep in self.metadata.dependencies:
            if dep not in available_plugins:
                missing.append(dep)
        return missing
    
    def subscribe_event(self, event_type: str, handler: Callable):
        """订阅事件"""
        self._event_handlers[event_type].append(handler)
    
    def unsubscribe_event(self, event_type: str, handler: Callable):
        """取消订阅事件"""
        if event_type in self._event_handlers:
            try:
                self._event_handlers[event_type].remove(handler)
            except ValueError:
                pass
    
    def handle_event(self, event: ApplicationEvent):
        """处理事件"""
        handlers = self._event_handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Plugin {self.metadata.name} event handler error: {e}")


class PluginLoadError(Exception):
    """插件加载错误"""
    pass


class PluginValidationError(Exception):
    """插件验证错误"""
    pass


@dataclass
class PluginLoadResult:
    """插件加载结果"""
    success: bool
    plugin: Optional[IPlugin] = None
    error: Optional[str] = None
    load_time: float = 0.0




@injectable(ServiceLifetime.SINGLETON)
class PluginManager(IService):
    """插件管理器 - 核心插件系统"""
    
    def __init__(self, 
                 container: DependencyContainer,
                 event_bus: EventBus,
                 config_manager: Optional[IConfigurationManager] = None,
                 logger: Optional[ILogger] = None):
        self._container = container
        self._event_bus = event_bus
        self._config_manager = config_manager
        self._logger = logger or logging.getLogger(__name__)
        
        # 插件存储
        self._plugins: Dict[str, IPlugin] = {}
        self._plugin_metadata: Dict[str, PluginMetadata] = {}
        self._plugin_modules: Dict[str, Any] = {}
        
        # 插件目录
        self._plugin_dirs: List[Path] = []
        self._default_plugin_dir = Path("plugins")
        
        # 安全管理器
        self._security_manager = create_security_manager(logger)
        self._security_manager.set_app_version("1.0.0")
        self._security_manager.set_api_version("1.0.0")
        
        # 状态管理
        self._status = ServiceStatus.INACTIVE
        self._lock = threading.RLock()
        
        # 性能监控
        self._load_times: Dict[str, float] = {}
        self._start_times: Dict[str, float] = {}
        
        # 事件处理
        self._setup_event_handlers()
        
        # 扩展点
        self._extension_points: Dict[str, List[Callable]] = defaultdict(list)
        
        if self._logger:
            self._logger.info("PluginManager initialized")
    
    def _setup_event_handlers(self):
        """设置事件处理器"""
        if self._event_bus:
            self._event_bus.subscribe('application_started', self._on_application_started)
            self._event_bus.subscribe('application_shutting_down', self._on_application_shutdown)
    
    def _on_application_started(self, event: ApplicationEvent):
        """应用启动时的处理"""
        self.auto_start_plugins()
    
    def _on_application_shutdown(self, event: ApplicationEvent):
        """应用关闭时的处理"""
        self.stop_all_plugins()
    
    # IService接口实现
    def start(self) -> None:
        """启动插件管理器"""
        with self._lock:
            if self._status == ServiceStatus.ACTIVE:
                return
            
            self._status = ServiceStatus.STARTING
            
            try:
                # 初始化插件目录
                self._initialize_plugin_directories()
                
                # 扫描并加载插件元数据
                self._scan_plugins()
                
                self._status = ServiceStatus.ACTIVE
                
                if self._logger:
                    self._logger.info("PluginManager started successfully")
                
                # 发布事件
                if self._event_bus:
                    event = ApplicationEvent("plugin_manager_started")
                    self._event_bus.post_event(event)
                    
            except Exception as e:
                self._status = ServiceStatus.ERROR
                if self._logger:
                    self._logger.error(f"Failed to start PluginManager: {e}")
                raise
    
    def stop(self) -> None:
        """停止插件管理器"""
        with self._lock:
            if self._status != ServiceStatus.ACTIVE:
                return
            
            self._status = ServiceStatus.STOPPING
            
            try:
                # 停止所有插件
                self.stop_all_plugins()
                
                # 卸载所有插件
                self.unload_all_plugins()
                
                self._status = ServiceStatus.INACTIVE
                
                if self._logger:
                    self._logger.info("PluginManager stopped")
                
                # 发布事件
                if self._event_bus:
                    event = ApplicationEvent("plugin_manager_stopped")
                    self._event_bus.post_event(event)
                    
            except Exception as e:
                self._status = ServiceStatus.ERROR
                if self._logger:
                    self._logger.error(f"Failed to stop PluginManager: {e}")
                raise
    
    def get_status(self) -> ServiceStatus:
        """获取服务状态"""
        return self._status
    
    def is_healthy(self) -> bool:
        """检查服务健康状态"""
        return self._status == ServiceStatus.ACTIVE
    
    # 插件目录管理
    def add_plugin_directory(self, directory: Union[str, Path]):
        """添加插件目录"""
        path = Path(directory)
        if path.exists() and path.is_dir():
            self._plugin_dirs.append(path)
            if self._logger:
                self._logger.info(f"Added plugin directory: {path}")
        else:
            if self._logger:
                self._logger.warning(f"Plugin directory does not exist: {path}")
    
    def _initialize_plugin_directories(self):
        """初始化插件目录"""
        # 添加默认插件目录
        if self._default_plugin_dir.exists():
            self.add_plugin_directory(self._default_plugin_dir)
        
        # 从配置中加载插件目录
        if self._config_manager:
            plugin_dirs = self._config_manager.get('plugin.directories', [])
            for dir_path in plugin_dirs:
                self.add_plugin_directory(dir_path)
    
    # 插件扫描和元数据加载
    def _scan_plugins(self):
        """扫描插件目录，加载元数据"""
        for plugin_dir in self._plugin_dirs:
            self._scan_directory(plugin_dir)
    
    def _scan_directory(self, directory: Path):
        """扫描单个目录"""
        for item in directory.iterdir():
            if item.is_dir():
                manifest_file = item / "plugin.json"
                if manifest_file.exists():
                    try:
                        self._load_plugin_metadata(manifest_file, item)
                    except Exception as e:
                        if self._logger:
                            self._logger.error(f"Failed to load plugin metadata from {manifest_file}: {e}")
    
    def _load_plugin_metadata(self, manifest_file: Path, plugin_dir: Path):
        """加载插件元数据"""
        try:
            with open(manifest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            metadata = PluginMetadata.from_dict(data)
            metadata.plugin_dir = plugin_dir  # 添加插件目录信息
            
            # 验证元数据
            self._validate_plugin_metadata(metadata)
            
            self._plugin_metadata[metadata.name] = metadata
            
            if self._logger:
                self._logger.info(f"Loaded plugin metadata: {metadata.name} v{metadata.version}")
                
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to load plugin metadata from {manifest_file}: {e}")
            raise PluginLoadError(f"Invalid plugin metadata: {e}")
    
    def _validate_plugin_metadata(self, metadata: PluginMetadata):
        """验证插件元数据"""
        if not metadata.name:
            raise PluginValidationError("Plugin name is required")
        
        if not metadata.version:
            raise PluginValidationError("Plugin version is required")
        
        if not metadata.entry_point:
            raise PluginValidationError("Plugin entry point is required")
        
        # 验证版本兼容性
        # TODO: 实现语义版本比较
    
    # 插件加载和管理
    def load_plugin(self, plugin_name: str) -> PluginLoadResult:
        """加载单个插件"""
        start_time = time.time()
        
        with self._lock:
            try:
                # 检查插件是否已加载
                if plugin_name in self._plugins:
                    return PluginLoadResult(
                        success=False,
                        error=f"Plugin {plugin_name} is already loaded"
                    )
                
                # 获取插件元数据
                if plugin_name not in self._plugin_metadata:
                    return PluginLoadResult(
                        success=False,
                        error=f"Plugin {plugin_name} metadata not found"
                    )
                
                metadata = self._plugin_metadata[plugin_name]
                
                # 检查插件是否启用
                if not metadata.enabled:
                    return PluginLoadResult(
                        success=False,
                        error=f"Plugin {plugin_name} is disabled"
                    )
                
                # 安全验证
                is_valid, security_message = self._security_manager.validate_plugin_metadata(metadata)
                if not is_valid:
                    return PluginLoadResult(
                        success=False,
                        error=f"Security validation failed: {security_message}"
                    )
                
                # 验证依赖
                missing_deps = self._check_dependencies(metadata)
                if missing_deps:
                    return PluginLoadResult(
                        success=False,
                        error=f"Missing dependencies: {missing_deps}"
                    )
                
                # 动态导入插件模块
                plugin_module = self._import_plugin_module(metadata)
                if not plugin_module:
                    return PluginLoadResult(
                        success=False,
                        error=f"Failed to import plugin module"
                    )
                
                # 创建插件实例
                plugin = self._create_plugin_instance(metadata, plugin_module)
                if not plugin:
                    return PluginLoadResult(
                        success=False,
                        error=f"Failed to create plugin instance"
                    )
                
                # 设置插件依赖
                plugin_config = self._get_plugin_config(plugin_name)
                plugin.set_dependencies(self._container, plugin_config, self._logger)
                
                # 执行插件加载
                plugin._state = PluginState.LOADING
                if not plugin.load():
                    return PluginLoadResult(
                        success=False,
                        error=f"Plugin load() method returned False"
                    )
                
                plugin._state = PluginState.LOADED
                
                # 注册插件
                self._plugins[plugin_name] = plugin
                self._plugin_modules[plugin_name] = plugin_module
                
                load_time = time.time() - start_time
                self._load_times[plugin_name] = load_time
                
                if self._logger:
                    self._logger.info(f"Plugin {plugin_name} loaded successfully in {load_time:.3f}s")
                
                # 发布事件
                if self._event_bus:
                    event = ApplicationEvent("plugin_loaded", {"plugin_name": plugin_name})
                    self._event_bus.post_event(event)
                
                return PluginLoadResult(
                    success=True,
                    plugin=plugin,
                    load_time=load_time
                )
                
            except Exception as e:
                load_time = time.time() - start_time
                error_msg = f"Failed to load plugin {plugin_name}: {e}"
                
                if self._logger:
                    self._logger.error(error_msg)
                    self._logger.debug(traceback.format_exc())
                
                return PluginLoadResult(
                    success=False,
                    error=error_msg,
                    load_time=load_time
                )
    
    def _check_dependencies(self, metadata: PluginMetadata) -> List[str]:
        """检查插件依赖"""
        available_plugins = set(self._plugins.keys())
        return [dep for dep in metadata.dependencies if dep not in available_plugins]
    
    def _import_plugin_module(self, metadata: PluginMetadata) -> Optional[Any]:
        """动态导入插件模块"""
        try:
            plugin_dir = getattr(metadata, 'plugin_dir', None)
            if not plugin_dir:
                return None
            
            # 构建模块路径
            module_file = plugin_dir / f"{metadata.entry_point}.py"
            if not module_file.exists():
                return None
            
            # 使用importlib动态加载
            spec = importlib.util.spec_from_file_location(
                f"plugin_{metadata.name}",
                module_file
            )
            
            if not spec or not spec.loader:
                return None
            
            module = importlib.util.module_from_spec(spec)
            
            # 安全检查
            sandbox = self._security_manager.create_sandbox(metadata.name)
            with open(module_file, 'r', encoding='utf-8') as f:
                code = f.read()
            
            is_safe, violations = sandbox.validate_code(code)
            if not is_safe:
                violation_details = "; ".join([v.description for v in violations])
                raise PluginLoadError(f"Plugin {metadata.name} contains unsafe code: {violation_details}")
            
            # 执行模块
            spec.loader.exec_module(module)
            
            return module
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to import plugin module {metadata.name}: {e}")
            return None
    
    def _create_plugin_instance(self, metadata: PluginMetadata, module: Any) -> Optional[IPlugin]:
        """创建插件实例"""
        try:
            # 查找插件类
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, IPlugin) and 
                    attr != IPlugin):
                    plugin_class = attr
                    break
            
            if not plugin_class:
                raise PluginLoadError(f"No plugin class found in module")
            
            # 创建实例
            plugin = plugin_class(metadata)
            return plugin
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to create plugin instance {metadata.name}: {e}")
            return None
    
    def _get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """获取插件配置"""
        if not self._config_manager:
            return {}
        
        return self._config_manager.get(f'plugin.{plugin_name}', {})
    
    # 插件生命周期管理
    def start_plugin(self, plugin_name: str) -> bool:
        """启动插件"""
        with self._lock:
            try:
                if plugin_name not in self._plugins:
                    if self._logger:
                        self._logger.error(f"Plugin {plugin_name} not loaded")
                    return False
                
                plugin = self._plugins[plugin_name]
                
                if plugin.state == PluginState.ACTIVE:
                    return True
                
                if plugin.state != PluginState.LOADED:
                    if self._logger:
                        self._logger.error(f"Plugin {plugin_name} is in invalid state: {plugin.state}")
                    return False
                
                start_time = time.time()
                plugin._state = PluginState.STARTING
                
                success = plugin.start()
                
                if success:
                    plugin._state = PluginState.ACTIVE
                    self._start_times[plugin_name] = time.time() - start_time
                    
                    if self._logger:
                        self._logger.info(f"Plugin {plugin_name} started successfully")
                    
                    # 发布事件
                    if self._event_bus:
                        event = ApplicationEvent("plugin_started", {"plugin_name": plugin_name})
                        self._event_bus.post_event(event)
                else:
                    plugin._state = PluginState.ERROR
                    if self._logger:
                        self._logger.error(f"Plugin {plugin_name} start() method returned False")
                
                return success
                
            except Exception as e:
                if plugin_name in self._plugins:
                    self._plugins[plugin_name]._state = PluginState.ERROR
                
                if self._logger:
                    self._logger.error(f"Failed to start plugin {plugin_name}: {e}")
                
                return False
    
    def stop_plugin(self, plugin_name: str) -> bool:
        """停止插件"""
        with self._lock:
            try:
                if plugin_name not in self._plugins:
                    return True
                
                plugin = self._plugins[plugin_name]
                
                if plugin.state in [PluginState.STOPPED, PluginState.LOADED]:
                    return True
                
                if plugin.state != PluginState.ACTIVE:
                    return False
                
                plugin._state = PluginState.STOPPING
                success = plugin.stop()
                
                if success:
                    plugin._state = PluginState.STOPPED
                    
                    if self._logger:
                        self._logger.info(f"Plugin {plugin_name} stopped successfully")
                    
                    # 发布事件
                    if self._event_bus:
                        event = ApplicationEvent("plugin_stopped", {"plugin_name": plugin_name})
                        self._event_bus.post_event(event)
                else:
                    plugin._state = PluginState.ERROR
                
                return success
                
            except Exception as e:
                if plugin_name in self._plugins:
                    self._plugins[plugin_name]._state = PluginState.ERROR
                
                if self._logger:
                    self._logger.error(f"Failed to stop plugin {plugin_name}: {e}")
                
                return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """卸载插件"""
        with self._lock:
            try:
                if plugin_name not in self._plugins:
                    return True
                
                plugin = self._plugins[plugin_name]
                
                # 先停止插件
                if plugin.state == PluginState.ACTIVE:
                    if not self.stop_plugin(plugin_name):
                        return False
                
                # 卸载插件
                success = plugin.unload()
                
                if success:
                    plugin._state = PluginState.UNLOADED
                    
                    # 从注册表中移除
                    del self._plugins[plugin_name]
                    if plugin_name in self._plugin_modules:
                        del self._plugin_modules[plugin_name]
                    
                    # 清理安全资源
                    self.cleanup_plugin_security(plugin_name)
                    
                    if self._logger:
                        self._logger.info(f"Plugin {plugin_name} unloaded successfully")
                    
                    # 发布事件
                    if self._event_bus:
                        event = ApplicationEvent("plugin_unloaded", {"plugin_name": plugin_name})
                        self._event_bus.post_event(event)
                
                return success
                
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Failed to unload plugin {plugin_name}: {e}")
                
                return False
    
    # 批量操作
    def load_all_plugins(self) -> Dict[str, PluginLoadResult]:
        """加载所有插件"""
        results = {}
        
        # 按优先级排序
        sorted_plugins = sorted(
            self._plugin_metadata.items(),
            key=lambda x: x[1].priority
        )
        
        for plugin_name, metadata in sorted_plugins:
            if metadata.enabled:
                results[plugin_name] = self.load_plugin(plugin_name)
        
        return results
    
    def auto_start_plugins(self):
        """自动启动需要自动启动的插件"""
        for plugin_name, plugin in self._plugins.items():
            if (plugin.metadata.auto_start and 
                plugin.metadata.enabled and 
                plugin.state == PluginState.LOADED):
                self.start_plugin(plugin_name)
    
    def stop_all_plugins(self):
        """停止所有插件"""
        for plugin_name in list(self._plugins.keys()):
            self.stop_plugin(plugin_name)
    
    def unload_all_plugins(self):
        """卸载所有插件"""
        for plugin_name in list(self._plugins.keys()):
            self.unload_plugin(plugin_name)
    
    # 查询和信息获取
    def get_plugin(self, plugin_name: str) -> Optional[IPlugin]:
        """获取插件实例"""
        return self._plugins.get(plugin_name)
    
    def get_plugin_metadata(self, plugin_name: str) -> Optional[PluginMetadata]:
        """获取插件元数据"""
        return self._plugin_metadata.get(plugin_name)
    
    def list_plugins(self) -> List[str]:
        """列出所有已发现的插件"""
        return list(self._plugin_metadata.keys())
    
    def list_loaded_plugins(self) -> List[str]:
        """列出已加载的插件"""
        return list(self._plugins.keys())
    
    def list_active_plugins(self) -> List[str]:
        """列出活跃的插件"""
        return [name for name, plugin in self._plugins.items() 
                if plugin.state == PluginState.ACTIVE]
    
    def get_plugin_status(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """获取插件状态"""
        if plugin_name in self._plugins:
            plugin = self._plugins[plugin_name]
            status = plugin.get_status()
            
            # 添加性能信息
            if plugin_name in self._load_times:
                status['load_time'] = self._load_times[plugin_name]
            if plugin_name in self._start_times:
                status['start_time'] = self._start_times[plugin_name]
            
            return status
        
        elif plugin_name in self._plugin_metadata:
            metadata = self._plugin_metadata[plugin_name]
            return {
                'name': metadata.name,
                'version': metadata.version,
                'state': PluginState.UNLOADED.value,
                'type': metadata.plugin_type.value,
                'enabled': metadata.enabled
            }
        
        return None
    
    def get_all_plugin_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有插件状态"""
        status = {}
        for plugin_name in self._plugin_metadata:
            plugin_status = self.get_plugin_status(plugin_name)
            if plugin_status:
                status[plugin_name] = plugin_status
        return status
    
    # 扩展点系统
    def register_extension_point(self, extension_point: str, handler: Callable):
        """注册扩展点处理器"""
        self._extension_points[extension_point].append(handler)
        
        if self._logger:
            self._logger.debug(f"Registered extension point handler: {extension_point}")
    
    def unregister_extension_point(self, extension_point: str, handler: Callable):
        """取消注册扩展点处理器"""
        if extension_point in self._extension_points:
            try:
                self._extension_points[extension_point].remove(handler)
            except ValueError:
                pass
    
    def call_extension_point(self, extension_point: str, *args, **kwargs) -> List[Any]:
        """调用扩展点"""
        results = []
        handlers = self._extension_points.get(extension_point, [])
        
        for handler in handlers:
            try:
                result = handler(*args, **kwargs)
                results.append(result)
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Extension point {extension_point} handler error: {e}")
        
        return results
    
    # 热插拔支持
    def reload_plugin(self, plugin_name: str) -> bool:
        """重新加载插件（热插拔）"""
        try:
            # 停止并卸载插件
            if plugin_name in self._plugins:
                was_active = self._plugins[plugin_name].state == PluginState.ACTIVE
                
                if not self.unload_plugin(plugin_name):
                    return False
            else:
                was_active = False
            
            # 重新扫描插件元数据
            if plugin_name in self._plugin_metadata:
                metadata = self._plugin_metadata[plugin_name]
                plugin_dir = getattr(metadata, 'plugin_dir', None)
                if plugin_dir:
                    manifest_file = plugin_dir / "plugin.json"
                    if manifest_file.exists():
                        self._load_plugin_metadata(manifest_file, plugin_dir)
            
            # 重新加载插件
            result = self.load_plugin(plugin_name)
            if not result.success:
                return False
            
            # 如果之前是活跃状态，重新启动
            if was_active:
                return self.start_plugin(plugin_name)
            
            return True
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to reload plugin {plugin_name}: {e}")
            return False
    
    # 性能监控
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        stats = {
            'total_plugins': len(self._plugin_metadata),
            'loaded_plugins': len(self._plugins),
            'active_plugins': len([p for p in self._plugins.values() 
                                 if p.state == PluginState.ACTIVE]),
            'load_times': self._load_times.copy(),
            'start_times': self._start_times.copy(),
            'average_load_time': 0.0,
            'average_start_time': 0.0
        }
        
        if self._load_times:
            stats['average_load_time'] = sum(self._load_times.values()) / len(self._load_times)
        
        if self._start_times:
            stats['average_start_time'] = sum(self._start_times.values()) / len(self._start_times)
        
        return stats
    
    # 安全管理方法
    def get_security_manager(self) -> PluginSecurityManager:
        """获取安全管理器"""
        return self._security_manager
    
    def set_plugin_security_policy(self, plugin_name: str, level: SecurityLevel):
        """设置插件安全策略"""
        from .plugin_security import create_default_policy
        policy = create_default_policy(level)
        self._security_manager.set_plugin_policy(plugin_name, policy)
        
        if self._logger:
            self._logger.info(f"设置插件 {plugin_name} 安全级别为: {level.value}")
    
    def get_security_violations(self, plugin_name: Optional[str] = None) -> List:
        """获取安全违规记录"""
        return self._security_manager.get_violations(plugin_name)
    
    def get_security_statistics(self) -> Dict[str, Any]:
        """获取安全统计信息"""
        return self._security_manager.get_security_statistics()
    
    def cleanup_plugin_security(self, plugin_name: str):
        """清理插件安全资源"""
        self._security_manager.remove_sandbox(plugin_name)
        
        if self._logger:
            self._logger.debug(f"清理插件 {plugin_name} 的安全资源")


# 便捷的插件基类
class BasePlugin(IPlugin):
    """插件基类，提供默认实现"""
    
    def __init__(self, metadata: PluginMetadata):
        super().__init__(metadata)
        self._is_loaded = False
        self._is_started = False
    
    def load(self) -> bool:
        """默认加载实现"""
        try:
            self._is_loaded = True
            return True
        except Exception as e:
            if self._logger:
                self._logger.error(f"Plugin {self.metadata.name} load failed: {e}")
            return False
    
    def start(self) -> bool:
        """默认启动实现"""
        try:
            if not self._is_loaded:
                return False
            
            self._is_started = True
            return True
        except Exception as e:
            if self._logger:
                self._logger.error(f"Plugin {self.metadata.name} start failed: {e}")
            return False
    
    def stop(self) -> bool:
        """默认停止实现"""
        try:
            self._is_started = False
            return True
        except Exception as e:
            if self._logger:
                self._logger.error(f"Plugin {self.metadata.name} stop failed: {e}")
            return False
    
    def unload(self) -> bool:
        """默认卸载实现"""
        try:
            if self._is_started:
                self.stop()
            
            self._is_loaded = False
            return True
        except Exception as e:
            if self._logger:
                self._logger.error(f"Plugin {self.metadata.name} unload failed: {e}")
            return False


# 全局插件管理器实例
_plugin_manager_instance: Optional[PluginManager] = None


def get_plugin_manager() -> Optional[PluginManager]:
    """获取全局插件管理器实例"""
    return _plugin_manager_instance


def initialize_plugin_manager(container: DependencyContainer, 
                             event_bus: EventBus,
                             config_manager: Optional[IConfigurationManager] = None,
                             logger: Optional[ILogger] = None) -> PluginManager:
    """初始化全局插件管理器"""
    global _plugin_manager_instance
    
    if _plugin_manager_instance is None:
        _plugin_manager_instance = PluginManager(container, event_bus, config_manager, logger)
        
        # 注册到依赖注入容器
        container.register_instance(PluginManager, _plugin_manager_instance)
    
    return _plugin_manager_instance