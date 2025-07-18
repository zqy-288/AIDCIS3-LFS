"""
插件系统接口定义
为插件开发提供标准化接口规范
支持异步操作、版本管理、热插拔等高级功能
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Union, TypeVar, Generic, Awaitable
from enum import Enum
from dataclasses import dataclass, field
import time
from datetime import datetime
from pathlib import Path

from .service_interfaces import IService, ServiceStatus
from ..application import ApplicationEvent

T = TypeVar('T')


class PluginHookType(Enum):
    """插件钩子类型"""
    BEFORE_START = "before_start"
    AFTER_START = "after_start"
    BEFORE_STOP = "before_stop"
    AFTER_STOP = "after_stop"
    DATA_PROCESS = "data_process"
    UI_RENDER = "ui_render"
    CONFIG_CHANGE = "config_change"
    ERROR_HANDLE = "error_handle"


class PluginPermission(Enum):
    """插件权限枚举"""
    READ_CONFIG = "read_config"
    WRITE_CONFIG = "write_config"
    ACCESS_DATABASE = "access_database"
    MODIFY_UI = "modify_ui"
    ACCESS_HARDWARE = "access_hardware"
    NETWORK_ACCESS = "network_access"
    FILE_SYSTEM = "file_system"
    SYSTEM_RESOURCES = "system_resources"
    INTER_PLUGIN_COMMUNICATION = "inter_plugin_communication"
    HOT_RELOAD = "hot_reload"
    EXTENSION_POINTS = "extension_points"


class PluginState(Enum):
    """插件状态枚举"""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    RELOADING = "reloading"
    ERROR = "error"
    DISABLED = "disabled"
    UPDATING = "updating"


class PluginCompatibility(Enum):
    """插件兼容性级别"""
    COMPATIBLE = "compatible"
    PARTIALLY_COMPATIBLE = "partially_compatible"
    INCOMPATIBLE = "incompatible"
    UNKNOWN = "unknown"


@dataclass
class PluginVersion:
    """插件版本信息"""
    major: int
    minor: int
    patch: int
    build: Optional[str] = None
    pre_release: Optional[str] = None
    
    def __str__(self) -> str:
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.pre_release:
            version += f"-{self.pre_release}"
        if self.build:
            version += f"+{self.build}"
        return version
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, PluginVersion):
            return False
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)
    
    def __lt__(self, other) -> bool:
        if not isinstance(other, PluginVersion):
            return NotImplemented
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
    
    def is_compatible_with(self, other: 'PluginVersion') -> PluginCompatibility:
        """检查版本兼容性"""
        if self.major != other.major:
            return PluginCompatibility.INCOMPATIBLE
        elif self.minor != other.minor:
            return PluginCompatibility.PARTIALLY_COMPATIBLE
        else:
            return PluginCompatibility.COMPATIBLE


@dataclass
class PluginMetadata:
    """增强的插件元数据"""
    id: str
    name: str
    version: PluginVersion
    description: str = ""
    author: str = ""
    homepage: str = ""
    repository: str = ""
    license: str = ""
    tags: List[str] = field(default_factory=list)
    
    # 技术信息
    entry_point: str = ""
    python_requires: str = ">=3.8"
    platform: List[str] = field(default_factory=list)
    
    # 依赖管理
    dependencies: List[str] = field(default_factory=list)
    optional_dependencies: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    provides: List[str] = field(default_factory=list)
    requires: List[str] = field(default_factory=list)
    
    # 版本兼容性
    min_core_version: Optional[PluginVersion] = None
    max_core_version: Optional[PluginVersion] = None
    api_version: PluginVersion = field(default_factory=lambda: PluginVersion(1, 0, 0))
    
    # 插件行为
    permissions: List[PluginPermission] = field(default_factory=list)
    priority: int = 100
    enabled: bool = True
    auto_start: bool = True
    hot_reload: bool = True
    sandboxed: bool = False
    
    # 配置和扩展
    config_schema: Dict[str, Any] = field(default_factory=dict)
    extension_points: List[str] = field(default_factory=list)
    extension_implementations: Dict[str, str] = field(default_factory=dict)
    
    # 时间戳
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    installed_at: Optional[datetime] = None
    
    # 路径信息
    plugin_dir: Optional[Path] = None
    manifest_path: Optional[Path] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
        # 确保版本对象正确
        if isinstance(self.version, str):
            self.version = self._parse_version(self.version)
        if isinstance(self.min_core_version, str):
            self.min_core_version = self._parse_version(self.min_core_version)
        if isinstance(self.max_core_version, str):
            self.max_core_version = self._parse_version(self.max_core_version)
        if isinstance(self.api_version, str):
            self.api_version = self._parse_version(self.api_version)
    
    def _parse_version(self, version_str: str) -> PluginVersion:
        """解析版本字符串"""
        parts = version_str.split('.')
        major = int(parts[0]) if len(parts) > 0 else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
        return PluginVersion(major, minor, patch)


@dataclass
class PluginHookResult:
    """插件钩子执行结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class PluginContext:
    """插件上下文数据类"""
    plugin_id: str
    plugin_metadata: PluginMetadata
    config: Dict[str, Any] = field(default_factory=dict)
    services: Dict[str, Any] = field(default_factory=dict)
    runtime_data: Dict[str, Any] = field(default_factory=dict)
    event_bus: Optional[Any] = None
    container: Optional[Any] = None
    logger: Optional[Any] = None
    security_context: Optional[Any] = None


class IPluginContext(ABC):
    """插件上下文接口"""
    
    @abstractmethod
    def get_application_info(self) -> Dict[str, Any]:
        """获取应用程序信息"""
        pass
    
    @abstractmethod
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        pass
    
    @abstractmethod
    def set_config(self, key: str, value: Any) -> None:
        """设置配置值"""
        pass
    
    @abstractmethod
    async def get_config_async(self, key: str, default: Any = None) -> Any:
        """异步获取配置值"""
        pass
    
    @abstractmethod
    async def set_config_async(self, key: str, value: Any) -> None:
        """异步设置配置值"""
        pass
    
    @abstractmethod
    def get_service(self, service_type: type) -> Optional[Any]:
        """获取服务实例"""
        pass
    
    @abstractmethod
    async def get_service_async(self, service_type: type) -> Optional[Any]:
        """异步获取服务实例"""
        pass
    
    @abstractmethod
    def publish_event(self, event: ApplicationEvent) -> None:
        """发布事件"""
        pass
    
    @abstractmethod
    async def publish_event_async(self, event: ApplicationEvent) -> None:
        """异步发布事件"""
        pass
    
    @abstractmethod
    def subscribe_event(self, event_type: str, handler: Callable) -> None:
        """订阅事件"""
        pass
    
    @abstractmethod
    async def subscribe_event_async(self, event_type: str, handler: Callable) -> None:
        """异步订阅事件"""
        pass
    
    @abstractmethod
    def has_permission(self, permission: PluginPermission) -> bool:
        """检查权限"""
        pass
    
    @abstractmethod
    def log(self, level: str, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """记录日志"""
        pass
    
    @abstractmethod
    async def log_async(self, level: str, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """异步记录日志"""
        pass
    
    @abstractmethod
    def get_plugin_metadata(self, plugin_id: str = None) -> Optional[PluginMetadata]:
        """获取插件元数据"""
        pass
    
    @abstractmethod
    def communicate_with_plugin(self, target_plugin_id: str, message: Any) -> Any:
        """与其他插件通信"""
        pass
    
    @abstractmethod
    async def communicate_with_plugin_async(self, target_plugin_id: str, message: Any) -> Any:
        """异步与其他插件通信"""
        pass
    
    @abstractmethod
    def get_extension_point(self, extension_point_id: str) -> Optional[Any]:
        """获取扩展点"""
        pass
    
    @abstractmethod
    def register_extension(self, extension_point_id: str, extension: Any) -> None:
        """注册扩展"""
        pass
    
    @abstractmethod
    def store_data(self, key: str, data: Any, persistent: bool = False) -> None:
        """存储插件数据"""
        pass
    
    @abstractmethod
    def retrieve_data(self, key: str, default: Any = None) -> Any:
        """检索插件数据"""
        pass
    
    @abstractmethod
    async def store_data_async(self, key: str, data: Any, persistent: bool = False) -> None:
        """异步存储插件数据"""
        pass
    
    @abstractmethod
    async def retrieve_data_async(self, key: str, default: Any = None) -> Any:
        """异步检索插件数据"""
        pass


class IPluginHook(ABC):
    """插件钩子接口"""
    
    @abstractmethod
    def get_hook_type(self) -> PluginHookType:
        """获取钩子类型"""
        pass
    
    @abstractmethod
    def get_priority(self) -> int:
        """获取执行优先级（数值越小优先级越高）"""
        pass
    
    @abstractmethod
    def execute(self, context: IPluginContext, data: Any = None) -> PluginHookResult:
        """执行钩子"""
        pass
    
    @abstractmethod
    def can_execute(self, context: IPluginContext, data: Any = None) -> bool:
        """检查是否可以执行"""
        pass


class IUIPlugin(ABC):
    """UI插件接口"""
    
    @abstractmethod
    def create_widget(self, parent=None) -> Any:
        """创建UI组件"""
        pass
    
    @abstractmethod
    def get_widget_info(self) -> Dict[str, Any]:
        """获取组件信息"""
        pass
    
    @abstractmethod
    def handle_ui_event(self, event_type: str, data: Any) -> None:
        """处理UI事件"""
        pass


class IDataPlugin(ABC):
    """数据处理插件接口"""
    
    @abstractmethod
    def process_data(self, data: Any) -> Any:
        """处理数据"""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """获取支持的数据格式"""
        pass
    
    @abstractmethod
    def validate_data(self, data: Any) -> bool:
        """验证数据"""
        pass
    
    @abstractmethod
    def transform_data(self, data: Any, target_format: str) -> Any:
        """转换数据格式"""
        pass


class IHardwarePlugin(ABC):
    """硬件插件接口"""
    
    @abstractmethod
    def initialize_hardware(self) -> bool:
        """初始化硬件"""
        pass
    
    @abstractmethod
    def connect(self) -> bool:
        """连接硬件"""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """断开硬件连接"""
        pass
    
    @abstractmethod
    def send_command(self, command: str, params: Dict[str, Any] = None) -> Any:
        """发送命令"""
        pass
    
    @abstractmethod
    def read_data(self) -> Any:
        """读取数据"""
        pass
    
    @abstractmethod
    def get_hardware_status(self) -> Dict[str, Any]:
        """获取硬件状态"""
        pass


class IReportPlugin(ABC):
    """报告生成插件接口"""
    
    @abstractmethod
    def generate_report(self, data: Any, template: str = None) -> Any:
        """生成报告"""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """获取支持的报告格式"""
        pass
    
    @abstractmethod
    def get_available_templates(self) -> List[str]:
        """获取可用模板"""
        pass
    
    @abstractmethod
    def preview_report(self, data: Any, template: str = None) -> Any:
        """预览报告"""
        pass


class IAlgorithmPlugin(ABC):
    """算法插件接口"""
    
    @abstractmethod
    def execute_algorithm(self, input_data: Any, parameters: Dict[str, Any] = None) -> Any:
        """执行算法"""
        pass
    
    @abstractmethod
    def get_algorithm_info(self) -> Dict[str, Any]:
        """获取算法信息"""
        pass
    
    @abstractmethod
    def get_parameters_schema(self) -> Dict[str, Any]:
        """获取参数模式"""
        pass
    
    @abstractmethod
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """验证参数"""
        pass


class IPluginRegistry(ABC):
    """插件注册表接口"""
    
    @abstractmethod
    def register_plugin(self, plugin_id: str, plugin: Any) -> None:
        """注册插件"""
        pass
    
    @abstractmethod
    def unregister_plugin(self, plugin_id: str) -> None:
        """注销插件"""
        pass
    
    @abstractmethod
    def get_plugin(self, plugin_id: str) -> Optional[Any]:
        """获取插件"""
        pass
    
    @abstractmethod
    def list_plugins(self, plugin_type: str = None) -> List[str]:
        """列出插件"""
        pass
    
    @abstractmethod
    def find_plugins_by_type(self, plugin_type: type) -> List[Any]:
        """按类型查找插件"""
        pass


class IPluginLoader(ABC):
    """插件加载器接口"""
    
    @abstractmethod
    def load_plugin(self, plugin_path: str) -> Optional[Any]:
        """加载插件"""
        pass
    
    @abstractmethod
    def unload_plugin(self, plugin_id: str) -> bool:
        """卸载插件"""
        pass
    
    @abstractmethod
    def reload_plugin(self, plugin_id: str) -> bool:
        """重新加载插件"""
        pass
    
    @abstractmethod
    def scan_plugins(self, directory: str) -> List[str]:
        """扫描插件目录"""
        pass


class IPluginValidator(ABC):
    """插件验证器接口"""
    
    @abstractmethod
    def validate_plugin(self, plugin: Any) -> bool:
        """验证插件"""
        pass
    
    @abstractmethod
    def validate_metadata(self, metadata: Dict[str, Any]) -> bool:
        """验证插件元数据"""
        pass
    
    @abstractmethod
    def validate_permissions(self, plugin: Any, permissions: List[PluginPermission]) -> bool:
        """验证插件权限"""
        pass
    
    @abstractmethod
    def validate_dependencies(self, plugin: Any, available_plugins: List[str]) -> List[str]:
        """验证插件依赖，返回缺失的依赖"""
        pass


class IPluginCommunicator(ABC):
    """插件间通信接口"""
    
    @abstractmethod
    def send_message(self, target_plugin: str, message: Any) -> bool:
        """发送消息到目标插件"""
        pass
    
    @abstractmethod
    def broadcast_message(self, message: Any, plugin_type: str = None) -> None:
        """广播消息"""
        pass
    
    @abstractmethod
    def register_message_handler(self, message_type: str, handler: Callable) -> None:
        """注册消息处理器"""
        pass
    
    @abstractmethod
    def unregister_message_handler(self, message_type: str, handler: Callable) -> None:
        """注销消息处理器"""
        pass


class IPluginStorage(ABC):
    """插件存储接口"""
    
    @abstractmethod
    def store_data(self, plugin_id: str, key: str, data: Any) -> None:
        """存储插件数据"""
        pass
    
    @abstractmethod
    def retrieve_data(self, plugin_id: str, key: str, default: Any = None) -> Any:
        """检索插件数据"""
        pass
    
    @abstractmethod
    def delete_data(self, plugin_id: str, key: str) -> bool:
        """删除插件数据"""
        pass
    
    @abstractmethod
    def list_keys(self, plugin_id: str) -> List[str]:
        """列出插件的所有键"""
        pass
    
    @abstractmethod
    def clear_plugin_data(self, plugin_id: str) -> None:
        """清除插件所有数据"""
        pass


# 插件生命周期事件
class PluginLifecycleEvent:
    """插件生命周期事件"""
    
    def __init__(self, plugin_id: str, event_type: str, data: Any = None):
        self.plugin_id = plugin_id
        self.event_type = event_type
        self.data = data
        self.timestamp = time.time()


# 插件配置接口
class IPluginConfiguration(ABC):
    """插件配置接口"""
    
    @abstractmethod
    def get_plugin_config(self, plugin_id: str) -> Dict[str, Any]:
        """获取插件配置"""
        pass
    
    @abstractmethod
    def set_plugin_config(self, plugin_id: str, config: Dict[str, Any]) -> None:
        """设置插件配置"""
        pass
    
    @abstractmethod
    def update_plugin_config(self, plugin_id: str, updates: Dict[str, Any]) -> None:
        """更新插件配置"""
        pass
    
    @abstractmethod
    def validate_config(self, plugin_id: str, config: Dict[str, Any]) -> bool:
        """验证插件配置"""
        pass
    
    @abstractmethod
    def get_config_schema(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """获取配置模式"""
        pass


# 插件事件监听器接口
class IPluginEventListener(ABC):
    """插件事件监听器接口"""
    
    @abstractmethod
    def on_plugin_loaded(self, plugin_id: str) -> None:
        """插件加载时调用"""
        pass
    
    @abstractmethod
    def on_plugin_started(self, plugin_id: str) -> None:
        """插件启动时调用"""
        pass
    
    @abstractmethod
    def on_plugin_stopped(self, plugin_id: str) -> None:
        """插件停止时调用"""
        pass
    
    @abstractmethod
    def on_plugin_unloaded(self, plugin_id: str) -> None:
        """插件卸载时调用"""
        pass
    
    @abstractmethod
    def on_plugin_error(self, plugin_id: str, error: Exception) -> None:
        """插件发生错误时调用"""
        pass


# 插件安全接口
class IPluginSecurity(ABC):
    """插件安全接口"""
    
    @abstractmethod
    def check_permission(self, plugin_id: str, permission: PluginPermission) -> bool:
        """检查插件权限"""
        pass
    
    @abstractmethod
    def grant_permission(self, plugin_id: str, permission: PluginPermission) -> None:
        """授予插件权限"""
        pass
    
    @abstractmethod
    def revoke_permission(self, plugin_id: str, permission: PluginPermission) -> None:
        """撤销插件权限"""
        pass
    
    @abstractmethod
    def get_plugin_permissions(self, plugin_id: str) -> List[PluginPermission]:
        """获取插件权限列表"""
        pass
    
    @abstractmethod
    def validate_plugin_code(self, code: str) -> bool:
        """验证插件代码安全性"""
        pass


# 插件性能监控接口
class IPluginPerformanceMonitor(ABC):
    """插件性能监控接口"""
    
    @abstractmethod
    def start_monitoring(self, plugin_id: str) -> None:
        """开始监控插件性能"""
        pass
    
    @abstractmethod
    def stop_monitoring(self, plugin_id: str) -> None:
        """停止监控插件性能"""
        pass
    
    @abstractmethod
    def get_performance_stats(self, plugin_id: str) -> Dict[str, Any]:
        """获取插件性能统计"""
        pass
    
    @abstractmethod
    def reset_stats(self, plugin_id: str) -> None:
        """重置插件统计"""
        pass


# 扩展点接口
class IExtensionPoint(ABC):
    """扩展点接口"""
    
    @abstractmethod
    def get_extension_point_id(self) -> str:
        """获取扩展点ID"""
        pass
    
    @abstractmethod
    def get_extension_point_description(self) -> str:
        """获取扩展点描述"""
        pass
    
    @abstractmethod
    def register_extension(self, extension_id: str, extension: Any) -> None:
        """注册扩展"""
        pass
    
    @abstractmethod
    def unregister_extension(self, extension_id: str) -> None:
        """注销扩展"""
        pass
    
    @abstractmethod
    def get_extensions(self) -> List[Any]:
        """获取所有扩展"""
        pass
    
    @abstractmethod
    def execute_extensions(self, context: Dict[str, Any]) -> List[Any]:
        """执行所有扩展"""
        pass


# 插件依赖管理接口
class IPluginDependencyManager(ABC):
    """插件依赖管理接口"""
    
    @abstractmethod
    def resolve_dependencies(self, plugin_id: str) -> List[str]:
        """解析插件依赖"""
        pass
    
    @abstractmethod
    def check_circular_dependencies(self, plugin_id: str) -> bool:
        """检查循环依赖"""
        pass
    
    @abstractmethod
    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """获取依赖图"""
        pass
    
    @abstractmethod
    def get_load_order(self, plugin_ids: List[str]) -> List[str]:
        """获取加载顺序"""
        pass


# 插件更新接口
class IPluginUpdater(ABC):
    """插件更新接口"""
    
    @abstractmethod
    def check_updates(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """检查插件更新"""
        pass
    
    @abstractmethod
    def update_plugin(self, plugin_id: str, version: str = None) -> bool:
        """更新插件"""
        pass
    
    @abstractmethod
    def rollback_plugin(self, plugin_id: str, version: str) -> bool:
        """回滚插件版本"""
        pass
    
    @abstractmethod
    def get_update_history(self, plugin_id: str) -> List[Dict[str, Any]]:
        """获取更新历史"""
        pass


# 增强的插件基础接口
class IAsyncPlugin(ABC):
    """异步插件接口"""
    
    def __init__(self, context: IPluginContext):
        self.context = context
        self.metadata: Optional[PluginMetadata] = None
        self._state = PluginState.UNLOADED
        self._start_time: Optional[datetime] = None
        self._stop_time: Optional[datetime] = None
    
    @property
    def state(self) -> PluginState:
        """获取插件状态"""
        return self._state
    
    @property
    def plugin_id(self) -> str:
        """获取插件ID"""
        return self.metadata.id if self.metadata else ""
    
    @property
    def uptime(self) -> Optional[float]:
        """获取运行时间（秒）"""
        if self._start_time and self._state == PluginState.RUNNING:
            return (datetime.now() - self._start_time).total_seconds()
        return None
    
    @abstractmethod
    async def initialize(self) -> bool:
        """初始化插件"""
        pass
    
    @abstractmethod
    async def start(self) -> bool:
        """启动插件"""
        pass
    
    @abstractmethod
    async def stop(self) -> bool:
        """停止插件"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> bool:
        """清理插件资源"""
        pass
    
    async def pause(self) -> bool:
        """暂停插件（可选实现）"""
        return True
    
    async def resume(self) -> bool:
        """恢复插件（可选实现）"""
        return True
    
    async def reload(self) -> bool:
        """重新加载插件（可选实现）"""
        return await self.stop() and await self.start()
    
    def get_provided_services(self) -> Dict[str, Any]:
        """获取插件提供的服务"""
        return {}
    
    async def get_provided_services_async(self) -> Dict[str, Any]:
        """异步获取插件提供的服务"""
        return self.get_provided_services()
    
    def on_plugin_loaded(self, plugin_id: str) -> None:
        """其他插件加载时的回调"""
        pass
    
    async def on_plugin_loaded_async(self, plugin_id: str) -> None:
        """其他插件加载时的异步回调"""
        self.on_plugin_loaded(plugin_id)
    
    def on_plugin_unloaded(self, plugin_id: str) -> None:
        """其他插件卸载时的回调"""
        pass
    
    async def on_plugin_unloaded_async(self, plugin_id: str) -> None:
        """其他插件卸载时的异步回调"""
        self.on_plugin_unloaded(plugin_id)
    
    def on_config_changed(self, key: str, old_value: Any, new_value: Any) -> None:
        """配置变更时的回调"""
        pass
    
    async def on_config_changed_async(self, key: str, old_value: Any, new_value: Any) -> None:
        """配置变更时的异步回调"""
        self.on_config_changed(key, old_value, new_value)
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取插件健康状态"""
        return {
            "status": "healthy" if self._state == PluginState.RUNNING else "unhealthy",
            "state": self._state.value,
            "uptime": self.uptime,
            "last_check": datetime.now().isoformat(),
            "memory_usage": 0,  # 可由子类实现
            "cpu_usage": 0,     # 可由子类实现
        }
    
    async def get_health_status_async(self) -> Dict[str, Any]:
        """异步获取插件健康状态"""
        return self.get_health_status()
    
    def handle_message(self, sender_id: str, message: Any) -> Any:
        """处理来自其他插件的消息"""
        return None
    
    async def handle_message_async(self, sender_id: str, message: Any) -> Any:
        """异步处理来自其他插件的消息"""
        return self.handle_message(sender_id, message)
    
    def get_extension_implementations(self) -> Dict[str, Callable]:
        """获取扩展点实现"""
        return {}
    
    async def execute_extension(self, extension_point_id: str, context: Dict[str, Any]) -> Any:
        """执行扩展点"""
        implementations = self.get_extension_implementations()
        if extension_point_id in implementations:
            impl = implementations[extension_point_id]
            if asyncio.iscoroutinefunction(impl):
                return await impl(context)
            else:
                return impl(context)
        return None


# 热插拔接口
class IHotSwappablePlugin(IAsyncPlugin):
    """支持热插拔的插件接口"""
    
    @abstractmethod
    async def prepare_hot_swap(self) -> Dict[str, Any]:
        """准备热插拔，返回状态数据"""
        pass
    
    @abstractmethod
    async def complete_hot_swap(self, state_data: Dict[str, Any]) -> bool:
        """完成热插拔，恢复状态"""
        pass
    
    @abstractmethod
    async def validate_hot_swap(self, new_version: PluginVersion) -> bool:
        """验证是否可以热插拔到新版本"""
        pass


# 版本管理接口
class IVersionAwarePlugin(IAsyncPlugin):
    """版本感知插件接口"""
    
    @abstractmethod
    def get_migration_path(self, from_version: PluginVersion, to_version: PluginVersion) -> List[str]:
        """获取版本迁移路径"""
        pass
    
    @abstractmethod
    async def migrate_data(self, from_version: PluginVersion, to_version: PluginVersion, data: Any) -> Any:
        """迁移数据到新版本"""
        pass
    
    @abstractmethod
    async def rollback_data(self, from_version: PluginVersion, to_version: PluginVersion, data: Any) -> Any:
        """回滚数据到旧版本"""
        pass
    
    @abstractmethod
    def is_backward_compatible(self, version: PluginVersion) -> bool:
        """检查是否向后兼容"""
        pass


# 插件通信接口
class IPluginMessaging(ABC):
    """插件消息传递接口"""
    
    @abstractmethod
    async def send_message(self, target_plugin_id: str, message_type: str, data: Any) -> Any:
        """发送消息到目标插件"""
        pass
    
    @abstractmethod
    async def broadcast_message(self, message_type: str, data: Any, filter_func: Optional[Callable] = None) -> List[Any]:
        """广播消息到所有插件"""
        pass
    
    @abstractmethod
    def register_message_handler(self, message_type: str, handler: Callable) -> None:
        """注册消息处理器"""
        pass
    
    @abstractmethod
    def unregister_message_handler(self, message_type: str, handler: Callable) -> None:
        """注销消息处理器"""
        pass
    
    @abstractmethod
    async def request_response(self, target_plugin_id: str, request: Any, timeout: float = 5.0) -> Any:
        """请求-响应模式通信"""
        pass


# 扩展管理器接口
class IExtensionManager(ABC):
    """扩展管理器接口"""
    
    @abstractmethod
    def register_extension_point(self, extension_point_id: str, description: str, 
                                schema: Optional[Dict[str, Any]] = None) -> None:
        """注册扩展点"""
        pass
    
    @abstractmethod
    def unregister_extension_point(self, extension_point_id: str) -> None:
        """注销扩展点"""
        pass
    
    @abstractmethod
    def register_extension(self, extension_point_id: str, plugin_id: str, 
                          extension_impl: Callable, priority: int = 100) -> None:
        """注册扩展实现"""
        pass
    
    @abstractmethod
    def unregister_extension(self, extension_point_id: str, plugin_id: str) -> None:
        """注销扩展实现"""
        pass
    
    @abstractmethod
    async def execute_extensions(self, extension_point_id: str, context: Dict[str, Any]) -> List[Any]:
        """执行扩展点的所有实现"""
        pass
    
    @abstractmethod
    def get_extension_points(self) -> List[str]:
        """获取所有扩展点"""
        pass
    
    @abstractmethod
    def get_extensions(self, extension_point_id: str) -> List[Dict[str, Any]]:
        """获取扩展点的所有实现"""
        pass


# 配置管理接口
class IPluginConfigManager(ABC):
    """插件配置管理接口"""
    
    @abstractmethod
    async def load_config(self, plugin_id: str) -> Dict[str, Any]:
        """加载插件配置"""
        pass
    
    @abstractmethod
    async def save_config(self, plugin_id: str, config: Dict[str, Any]) -> None:
        """保存插件配置"""
        pass
    
    @abstractmethod
    async def update_config(self, plugin_id: str, updates: Dict[str, Any]) -> None:
        """更新插件配置"""
        pass
    
    @abstractmethod
    async def validate_config(self, plugin_id: str, config: Dict[str, Any]) -> List[str]:
        """验证插件配置，返回错误信息列表"""
        pass
    
    @abstractmethod
    def watch_config_changes(self, plugin_id: str, callback: Callable) -> None:
        """监视配置变更"""
        pass
    
    @abstractmethod
    def unwatch_config_changes(self, plugin_id: str, callback: Callable) -> None:
        """停止监视配置变更"""
        pass
    
    @abstractmethod
    async def reset_config(self, plugin_id: str) -> None:
        """重置配置到默认值"""
        pass