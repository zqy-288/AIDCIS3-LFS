"""
依赖注入相关接口定义
为依赖注入框架提供标准化接口
"""

from abc import ABC, abstractmethod
from typing import Type, TypeVar, Optional, Dict, Any, Callable, List
from enum import Enum

T = TypeVar('T')


class IServiceRegistration(ABC):
    """服务注册接口"""
    
    @abstractmethod
    def register(self, 
                 service_type: Type[T],
                 implementation: Optional[Type[T]] = None,
                 factory: Optional[Callable[[], T]] = None,
                 lifetime: str = "transient") -> 'IServiceRegistration':
        """注册服务"""
        pass
    
    @abstractmethod
    def register_singleton(self, 
                          service_type: Type[T],
                          implementation: Optional[Type[T]] = None,
                          factory: Optional[Callable[[], T]] = None) -> 'IServiceRegistration':
        """注册单例服务"""
        pass
    
    @abstractmethod
    def register_instance(self, service_type: Type[T], instance: T) -> 'IServiceRegistration':
        """注册实例"""
        pass
    
    @abstractmethod
    def is_registered(self, service_type: Type) -> bool:
        """检查服务是否已注册"""
        pass


class IServiceResolver(ABC):
    """服务解析接口"""
    
    @abstractmethod
    def resolve(self, service_type: Type[T]) -> T:
        """解析服务"""
        pass
    
    @abstractmethod
    def try_resolve(self, service_type: Type[T]) -> Optional[T]:
        """尝试解析服务，失败返回None"""
        pass
    
    @abstractmethod
    def resolve_all(self, service_type: Type[T]) -> List[T]:
        """解析所有指定类型的服务"""
        pass


class ILifecycleManager(ABC):
    """生命周期管理接口"""
    
    @abstractmethod
    def create_scope(self) -> 'IServiceScope':
        """创建作用域"""
        pass
    
    @abstractmethod
    def dispose_scope(self, scope_id: str) -> None:
        """释放作用域"""
        pass
    
    @abstractmethod
    def get_active_scopes(self) -> List[str]:
        """获取活动作用域"""
        pass


class IServiceScope(ABC):
    """服务作用域接口"""
    
    @abstractmethod
    def resolve(self, service_type: Type[T]) -> T:
        """在作用域内解析服务"""
        pass
    
    @abstractmethod
    def dispose(self) -> None:
        """释放作用域"""
        pass
    
    @abstractmethod
    def get_scope_id(self) -> str:
        """获取作用域ID"""
        pass


class IDependencyContainer(IServiceRegistration, IServiceResolver, ILifecycleManager):
    """依赖注入容器接口"""
    
    @abstractmethod
    def reset(self) -> None:
        """重置容器"""
        pass
    
    @abstractmethod
    def get_registrations(self) -> Dict[Type, Any]:
        """获取所有注册信息"""
        pass
    
    @abstractmethod
    def validate_registrations(self) -> List[str]:
        """验证注册信息，返回错误列表"""
        pass
    
    @abstractmethod
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        pass


class IServiceInterceptor(ABC):
    """服务拦截器接口"""
    
    @abstractmethod
    def before_resolve(self, service_type: Type, context: Dict[str, Any]) -> None:
        """解析前拦截"""
        pass
    
    @abstractmethod
    def after_resolve(self, service_type: Type, instance: Any, context: Dict[str, Any]) -> Any:
        """解析后拦截"""
        pass
    
    @abstractmethod
    def on_error(self, service_type: Type, error: Exception, context: Dict[str, Any]) -> None:
        """错误拦截"""
        pass


class IServiceValidator(ABC):
    """服务验证器接口"""
    
    @abstractmethod
    def validate_service(self, service_type: Type, instance: Any) -> bool:
        """验证服务实例"""
        pass
    
    @abstractmethod
    def get_validation_errors(self, service_type: Type, instance: Any) -> List[str]:
        """获取验证错误"""
        pass


class IServiceDecorator(ABC):
    """服务装饰器接口"""
    
    @abstractmethod
    def decorate(self, service_type: Type, instance: Any) -> Any:
        """装饰服务实例"""
        pass
    
    @abstractmethod
    def can_decorate(self, service_type: Type) -> bool:
        """判断是否可以装饰"""
        pass


class IServiceProvider(ABC):
    """服务提供者接口"""
    
    @abstractmethod
    def get_service(self, service_type: Type[T]) -> T:
        """获取服务"""
        pass
    
    @abstractmethod
    def get_required_service(self, service_type: Type[T]) -> T:
        """获取必需服务（不存在时抛出异常）"""
        pass
    
    @abstractmethod
    def get_services(self, service_type: Type[T]) -> List[T]:
        """获取多个服务"""
        pass
    
    @abstractmethod
    def create_scope(self) -> 'IServiceScope':
        """创建服务作用域"""
        pass