"""
核心服务接口定义
为AI-2和AI-3提供标准化接口
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic, Union
from enum import Enum
import asyncio

T = TypeVar('T')


class ServiceStatus(Enum):
    """服务状态枚举"""
    INACTIVE = "inactive"
    STARTING = "starting"
    ACTIVE = "active"
    STOPPING = "stopping"
    ERROR = "error"


class IService(ABC):
    """基础服务接口"""
    
    @abstractmethod
    def start(self) -> None:
        """启动服务"""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """停止服务"""
        pass
    
    @abstractmethod
    def get_status(self) -> ServiceStatus:
        """获取服务状态"""
        pass
    
    @abstractmethod
    def is_healthy(self) -> bool:
        """检查服务健康状态"""
        pass


class IRepository(ABC, Generic[T]):
    """数据仓库接口"""
    
    @abstractmethod
    def create(self, entity: T) -> T:
        """创建实体"""
        pass
    
    @abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[T]:
        """根据ID获取实体"""
        pass
    
    @abstractmethod
    def get_all(self) -> List[T]:
        """获取所有实体"""
        pass
    
    @abstractmethod
    def update(self, entity: T) -> T:
        """更新实体"""
        pass
    
    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """删除实体"""
        pass
    
    @abstractmethod
    def find_by_criteria(self, criteria: Dict[str, Any]) -> List[T]:
        """根据条件查找实体"""
        pass


class IDataProcessor(ABC):
    """数据处理接口"""
    
    @abstractmethod
    def process(self, data: Any) -> Any:
        """处理数据"""
        pass
    
    @abstractmethod
    def validate(self, data: Any) -> bool:
        """验证数据"""
        pass
    
    @abstractmethod
    def transform(self, data: Any, target_format: str) -> Any:
        """转换数据格式"""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """获取支持的格式"""
        pass


class IEventHandler(ABC):
    """事件处理接口"""
    
    @abstractmethod
    def handle(self, event: Any) -> None:
        """处理事件"""
        pass
    
    @abstractmethod
    def can_handle(self, event: Any) -> bool:
        """判断是否可以处理事件"""
        pass
    
    @abstractmethod
    def get_event_types(self) -> List[str]:
        """获取支持的事件类型"""
        pass


class LogLevel(Enum):
    """日志级别枚举"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ILogger(ABC):
    """日志记录接口"""
    
    @abstractmethod
    def log(self, level: LogLevel, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """记录日志"""
        pass
    
    @abstractmethod
    def debug(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """记录调试日志"""
        pass
    
    @abstractmethod
    def info(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """记录信息日志"""
        pass
    
    @abstractmethod
    def warning(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """记录警告日志"""
        pass
    
    @abstractmethod
    def error(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """记录错误日志"""
        pass
    
    @abstractmethod
    def critical(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """记录严重错误日志"""
        pass


class IConfigurationManager(ABC):
    """配置管理接口"""
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        pass
    
    @abstractmethod
    def has(self, key: str) -> bool:
        """检查配置是否存在"""
        pass
    
    @abstractmethod
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        pass
    
    @abstractmethod
    def load_from_file(self, file_path: str) -> None:
        """从文件加载配置"""
        pass
    
    @abstractmethod
    def save_to_file(self, file_path: str) -> None:
        """保存配置到文件"""
        pass


class HealthStatus(Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthCheckResult:
    """健康检查结果"""
    
    def __init__(self, status: HealthStatus, message: str = "", details: Optional[Dict[str, Any]] = None):
        self.status = status
        self.message = message
        self.details = details or {}
        self.timestamp = None  # 将由具体实现设置


class IHealthChecker(ABC):
    """健康检查接口"""
    
    @abstractmethod
    def check_health(self) -> HealthCheckResult:
        """检查健康状态"""
        pass
    
    @abstractmethod
    def get_health_status(self) -> HealthStatus:
        """获取健康状态"""
        pass
    
    @abstractmethod
    def get_health_details(self) -> Dict[str, Any]:
        """获取健康详情"""
        pass


# 异步服务接口
class IAsyncService(ABC):
    """异步服务接口"""
    
    @abstractmethod
    async def start_async(self) -> None:
        """异步启动服务"""
        pass
    
    @abstractmethod
    async def stop_async(self) -> None:
        """异步停止服务"""
        pass
    
    @abstractmethod
    async def process_async(self, data: Any) -> Any:
        """异步处理数据"""
        pass


# 缓存接口
class ICacheService(ABC):
    """缓存服务接口"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除缓存值"""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清除所有缓存"""
        pass


# 消息队列接口
class IMessageQueue(ABC):
    """消息队列接口"""
    
    @abstractmethod
    def publish(self, topic: str, message: Any) -> None:
        """发布消息"""
        pass
    
    @abstractmethod
    def subscribe(self, topic: str, handler: callable) -> None:
        """订阅消息"""
        pass
    
    @abstractmethod
    def unsubscribe(self, topic: str, handler: callable) -> None:
        """取消订阅"""
        pass