"""
简单依赖注入容器
解决全局状态滥用问题
"""

from typing import Dict, Any, TypeVar, Type, Callable, Optional
from abc import ABC, abstractmethod

T = TypeVar('T')


class IServiceContainer(ABC):
    """服务容器接口"""
    
    @abstractmethod
    def register_singleton(self, service_type: Type[T], factory: Callable[[], T]) -> None:
        """注册单例服务"""
        pass
    
    @abstractmethod
    def register_transient(self, service_type: Type[T], factory: Callable[[], T]) -> None:
        """注册瞬时服务"""
        pass
    
    @abstractmethod
    def get_service(self, service_type: Type[T]) -> T:
        """获取服务实例"""
        pass
    
    @abstractmethod
    def has_service(self, service_type: Type[T]) -> bool:
        """检查是否注册了服务"""
        pass


class SimpleServiceContainer(IServiceContainer):
    """简单服务容器实现"""
    
    def __init__(self):
        self._singletons: Dict[Type, Any] = {}
        self._transient_factories: Dict[Type, Callable] = {}
        self._singleton_factories: Dict[Type, Callable] = {}
    
    def register_singleton(self, service_type: Type[T], factory: Callable[[], T]) -> None:
        """注册单例服务"""
        self._singleton_factories[service_type] = factory
        # 清除已创建的实例，强制重新创建
        if service_type in self._singletons:
            del self._singletons[service_type]
    
    def register_transient(self, service_type: Type[T], factory: Callable[[], T]) -> None:
        """注册瞬时服务"""
        self._transient_factories[service_type] = factory
    
    def get_service(self, service_type: Type[T]) -> T:
        """获取服务实例"""
        # 检查单例
        if service_type in self._singleton_factories:
            if service_type not in self._singletons:
                self._singletons[service_type] = self._singleton_factories[service_type]()
            return self._singletons[service_type]
        
        # 检查瞬时服务
        if service_type in self._transient_factories:
            return self._transient_factories[service_type]()
        
        raise ValueError(f"Service type {service_type} not registered")
    
    def has_service(self, service_type: Type[T]) -> bool:
        """检查是否注册了服务"""
        return (service_type in self._singleton_factories or 
                service_type in self._transient_factories)
    
    def clear(self) -> None:
        """清除所有服务（测试用）"""
        self._singletons.clear()
        self._transient_factories.clear()
        self._singleton_factories.clear()


# 全局容器实例（将逐步移除）
_global_container: Optional[IServiceContainer] = None


def get_service_container() -> IServiceContainer:
    """获取全局服务容器"""
    global _global_container
    if _global_container is None:
        _global_container = SimpleServiceContainer()
        # 注册默认服务
        _register_default_services(_global_container)
    return _global_container


def set_service_container(container: IServiceContainer) -> None:
    """设置服务容器（用于测试）"""
    global _global_container
    _global_container = container


def _register_default_services(container: IServiceContainer) -> None:
    """注册默认服务"""
    from src.core.data_service_interface import IDataService, DefaultDataServiceFactory
    
    # 注册数据服务工厂为单例
    factory = DefaultDataServiceFactory()
    container.register_singleton(IDataService, lambda: factory.create_data_service())


# 便捷访问函数
def get_service(service_type: Type[T]) -> T:
    """获取服务实例的便捷函数"""
    return get_service_container().get_service(service_type)


def register_service(service_type: Type[T], factory: Callable[[], T], singleton: bool = True) -> None:
    """注册服务的便捷函数"""
    container = get_service_container()
    if singleton:
        container.register_singleton(service_type, factory)
    else:
        container.register_transient(service_type, factory)