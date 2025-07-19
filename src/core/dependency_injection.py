"""
依赖注入框架核心实现
提供依赖容器、服务生命周期管理和自动依赖解析功能
"""

from typing import Dict, Type, Any, Optional, Set, List, Callable, TypeVar, Generic, Union
from enum import Enum
import inspect
import threading
import weakref
from abc import ABC, abstractmethod
import time

T = TypeVar('T')


class ServiceLifetime(Enum):
    """服务生命周期枚举"""
    SINGLETON = "singleton"    # 单例模式 - 全局唯一实例
    TRANSIENT = "transient"    # 临时模式 - 每次请求创建新实例
    SCOPED = "scoped"          # 作用域模式 - 在特定作用域内单例


class DependencyRegistration:
    """依赖注册信息"""
    
    def __init__(self, 
                 service_type: Type,
                 implementation: Optional[Type] = None,
                 factory: Optional[Callable] = None,
                 lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
                 instance: Optional[Any] = None):
        self.service_type = service_type
        self.implementation = implementation or service_type
        self.factory = factory
        self.lifetime = lifetime
        self.instance = instance
        self.dependencies: List[Type] = []
        self._analyze_dependencies()
    
    def _analyze_dependencies(self):
        """分析依赖关系"""
        if self.factory:
            sig = inspect.signature(self.factory)
            func_module = inspect.getmodule(self.factory)
        else:
            sig = inspect.signature(self.implementation.__init__)
            func_module = inspect.getmodule(self.implementation)
        
        for param_name, param in sig.parameters.items():
            if param_name != 'self' and param.annotation != inspect.Parameter.empty:
                # 处理字符串注解
                annotation = param.annotation
                if isinstance(annotation, str):
                    # 尝试从模块全局命名空间解析字符串注解
                    try:
                        if func_module and hasattr(func_module, annotation):
                            annotation = getattr(func_module, annotation)
                    except:
                        # 如果无法解析，保持原样，稍后在解析时处理
                        pass
                
                self.dependencies.append(annotation)
    
    def _resolve_annotation(self, annotation, module_globals=None):
        """解析注解，处理字符串注解"""
        if isinstance(annotation, str):
            if module_globals:
                try:
                    # 尝试从模块全局命名空间解析
                    return eval(annotation, module_globals)
                except:
                    pass
            # 如果无法解析，返回原字符串
            return annotation
        return annotation


class CircularDependencyError(Exception):
    """循环依赖异常"""
    pass


class ServiceNotRegisteredException(Exception):
    """服务未注册异常"""
    pass


class DependencyContainer:
    """依赖注入容器 - 单例模式实现"""
    
    _instance: Optional['DependencyContainer'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'DependencyContainer':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._registrations: Dict[Type, DependencyRegistration] = {}
            self._singleton_instances: Dict[Type, Any] = {}
            self._scoped_instances: Dict[int, Dict[Type, Any]] = {}
            self._resolution_stack: Set[Type] = set()
            self._lock = threading.RLock()
            self._initialized = True
    
    def register(self, 
                 service_type: Type[T],
                 implementation: Optional[Type[T]] = None,
                 factory: Optional[Callable[[], T]] = None,
                 lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT) -> 'DependencyContainer':
        """注册服务"""
        with self._lock:
            if implementation is None and factory is None:
                implementation = service_type
            
            registration = DependencyRegistration(
                service_type=service_type,
                implementation=implementation,
                factory=factory,
                lifetime=lifetime
            )
            
            self._registrations[service_type] = registration
            return self
    
    def register_singleton(self, 
                          service_type: Type[T],
                          implementation: Optional[Type[T]] = None,
                          factory: Optional[Callable[[], T]] = None) -> 'DependencyContainer':
        """注册单例服务"""
        return self.register(service_type, implementation, factory, ServiceLifetime.SINGLETON)
    
    def register_transient(self, 
                          service_type: Type[T],
                          implementation: Optional[Type[T]] = None,
                          factory: Optional[Callable[[], T]] = None) -> 'DependencyContainer':
        """注册临时服务"""
        return self.register(service_type, implementation, factory, ServiceLifetime.TRANSIENT)
    
    def register_scoped(self, 
                       service_type: Type[T],
                       implementation: Optional[Type[T]] = None,
                       factory: Optional[Callable[[], T]] = None) -> 'DependencyContainer':
        """注册作用域服务"""
        return self.register(service_type, implementation, factory, ServiceLifetime.SCOPED)
    
    def register_instance(self, service_type: Type[T], instance: T) -> 'DependencyContainer':
        """注册实例"""
        with self._lock:
            registration = DependencyRegistration(
                service_type=service_type,
                lifetime=ServiceLifetime.SINGLETON,
                instance=instance
            )
            self._registrations[service_type] = registration
            self._singleton_instances[service_type] = instance
            return self
    
    def register_type(self, 
                     service_type: Type[T], 
                     lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
                     implementation: Optional[Type[T]] = None,
                     factory: Optional[Callable[[], T]] = None) -> 'DependencyContainer':
        """注册类型（与register方法相同，但参数顺序不同以匹配现有代码）"""
        return self.register(service_type, implementation, factory, lifetime)
    
    def resolve(self, service_type: Type[T], scope_id: Optional[int] = None) -> T:
        """解析服务"""
        with self._lock:
            # 检查循环依赖
            if service_type in self._resolution_stack:
                cycle_path = " -> ".join([getattr(cls, '__name__', str(cls)) for cls in self._resolution_stack]) + f" -> {getattr(service_type, '__name__', str(service_type))}"
                raise CircularDependencyError(f"检测到循环依赖: {cycle_path}")
            
            # 检查服务是否已注册
            if service_type not in self._registrations:
                service_name = getattr(service_type, '__name__', str(service_type))
                raise ServiceNotRegisteredException(f"服务 {service_name} 未注册")
            
            registration = self._registrations[service_type]
            
            # 如果已有实例，直接返回
            if registration.instance is not None:
                return registration.instance
            
            # 单例模式
            if registration.lifetime == ServiceLifetime.SINGLETON:
                if service_type in self._singleton_instances:
                    return self._singleton_instances[service_type]
                
                instance = self._create_instance(registration)
                self._singleton_instances[service_type] = instance
                return instance
            
            # 作用域模式
            elif registration.lifetime == ServiceLifetime.SCOPED:
                scope_id = scope_id or threading.current_thread().ident
                if scope_id not in self._scoped_instances:
                    self._scoped_instances[scope_id] = {}
                
                scoped_dict = self._scoped_instances[scope_id]
                if service_type in scoped_dict:
                    return scoped_dict[service_type]
                
                instance = self._create_instance(registration, scope_id)
                scoped_dict[service_type] = instance
                return instance
            
            # 临时模式
            else:
                return self._create_instance(registration, scope_id)
    
    def _create_instance(self, registration: DependencyRegistration, scope_id: Optional[int] = None) -> Any:
        """创建实例"""
        self._resolution_stack.add(registration.service_type)
        
        try:
            # 使用工厂方法
            if registration.factory:
                # 解析工厂方法的依赖
                sig = inspect.signature(registration.factory)
                kwargs = {}
                for param_name, param in sig.parameters.items():
                    if param.annotation != inspect.Parameter.empty:
                        # 处理字符串注解
                        annotation = param.annotation
                        if isinstance(annotation, str):
                            # 尝试从模块全局命名空间解析
                            try:
                                module = inspect.getmodule(registration.factory)
                                if module:
                                    annotation = registration._resolve_annotation(annotation, module.__dict__)
                            except:
                                continue
                        
                        if not isinstance(annotation, str):
                            try:
                                # 处理Optional类型
                                if hasattr(annotation, '__origin__') and annotation.__origin__ is Union:
                                    # 检查是否是Optional类型（Union[T, None]）
                                    args = getattr(annotation, '__args__', ())
                                    if len(args) == 2 and type(None) in args:
                                        # 这是Optional类型，获取实际类型
                                        actual_type = args[0] if args[1] is type(None) else args[1]
                                        try:
                                            kwargs[param_name] = self.resolve(actual_type, scope_id)
                                        except ServiceNotRegisteredException:
                                            kwargs[param_name] = None
                                    else:
                                        kwargs[param_name] = self.resolve(annotation, scope_id)
                                else:
                                    kwargs[param_name] = self.resolve(annotation, scope_id)
                            except ServiceNotRegisteredException:
                                # 对于可选依赖，设置为None
                                if param.default is not inspect.Parameter.empty:
                                    kwargs[param_name] = param.default
                                else:
                                    kwargs[param_name] = None
                
                return registration.factory(**kwargs)
            
            # 使用构造函数
            else:
                # 解析构造函数依赖
                sig = inspect.signature(registration.implementation.__init__)
                kwargs = {}
                for param_name, param in sig.parameters.items():
                    if param_name != 'self' and param.annotation != inspect.Parameter.empty:
                        # 处理字符串注解
                        annotation = param.annotation
                        if isinstance(annotation, str):
                            # 尝试从模块全局命名空间解析
                            try:
                                module = inspect.getmodule(registration.implementation)
                                if module:
                                    annotation = registration._resolve_annotation(annotation, module.__dict__)
                            except:
                                continue
                        
                        if not isinstance(annotation, str):
                            try:
                                # 处理Optional类型
                                if hasattr(annotation, '__origin__') and annotation.__origin__ is Union:
                                    # 检查是否是Optional类型（Union[T, None]）
                                    args = getattr(annotation, '__args__', ())
                                    if len(args) == 2 and type(None) in args:
                                        # 这是Optional类型，获取实际类型
                                        actual_type = args[0] if args[1] is type(None) else args[1]
                                        try:
                                            kwargs[param_name] = self.resolve(actual_type, scope_id)
                                        except ServiceNotRegisteredException:
                                            kwargs[param_name] = None
                                    else:
                                        kwargs[param_name] = self.resolve(annotation, scope_id)
                                else:
                                    kwargs[param_name] = self.resolve(annotation, scope_id)
                            except ServiceNotRegisteredException:
                                # 对于可选依赖，设置为None
                                if param.default is not inspect.Parameter.empty:
                                    kwargs[param_name] = param.default
                                else:
                                    kwargs[param_name] = None
                
                return registration.implementation(**kwargs)
        
        finally:
            self._resolution_stack.remove(registration.service_type)
    
    def get(self, service_type: Type[T], scope_id: Optional[int] = None) -> T:
        """获取服务 - resolve方法的别名，保持API兼容性"""
        return self.resolve(service_type, scope_id)
    
    def is_registered(self, service_type: Type) -> bool:
        """检查服务是否已注册"""
        return service_type in self._registrations
    
    def get_registration(self, service_type: Type) -> Optional[DependencyRegistration]:
        """获取注册信息"""
        return self._registrations.get(service_type)
    
    def clear_scope(self, scope_id: int):
        """清除作用域"""
        with self._lock:
            if scope_id in self._scoped_instances:
                del self._scoped_instances[scope_id]
    
    def clear_all_scopes(self):
        """清除所有作用域"""
        with self._lock:
            self._scoped_instances.clear()
    
    def reset(self):
        """重置容器"""
        with self._lock:
            self._registrations.clear()
            self._singleton_instances.clear()
            self._scoped_instances.clear()
            self._resolution_stack.clear()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        with self._lock:
            return {
                'registered_services': len(self._registrations),
                'singleton_instances': len(self._singleton_instances),
                'scoped_instances': sum(len(scoped_dict) for scoped_dict in self._scoped_instances.values()),
                'active_scopes': len(self._scoped_instances)
            }


def injectable(lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT):
    """依赖注入装饰器"""
    def decorator(cls: Type[T]) -> Type[T]:
        # 自动注册到容器
        container = DependencyContainer()
        container.register(cls, lifetime=lifetime)
        
        # 添加元数据
        cls.__di_lifetime__ = lifetime
        cls.__di_registered__ = True
        
        return cls
    
    return decorator


# 便捷函数
def get_container() -> DependencyContainer:
    """获取依赖注入容器实例"""
    return DependencyContainer()


def resolve(service_type: Type[T], scope_id: Optional[int] = None) -> T:
    """解析服务的便捷函数"""
    return get_container().resolve(service_type, scope_id)


def register(service_type: Type[T], 
            implementation: Optional[Type[T]] = None,
            factory: Optional[Callable[[], T]] = None,
            lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT) -> DependencyContainer:
    """注册服务的便捷函数"""
    return get_container().register(service_type, implementation, factory, lifetime)


class ScopeContext:
    """作用域上下文管理器"""
    
    def __init__(self, container: Optional[DependencyContainer] = None):
        self.container = container or get_container()
        self.scope_id = threading.current_thread().ident
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.container.clear_scope(self.scope_id)
    
    def resolve(self, service_type: Type[T]) -> T:
        """在当前作用域解析服务"""
        return self.container.resolve(service_type, self.scope_id)


# 性能监控装饰器
def performance_monitor(func):
    """性能监控装饰器"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = (end_time - start_time) * 1000  # 转换为毫秒
        
        # 记录性能数据
        if not hasattr(wrapper, 'performance_data'):
            wrapper.performance_data = []
        
        wrapper.performance_data.append({
            'timestamp': start_time,
            'execution_time_ms': execution_time,
            'args': len(args),
            'kwargs': len(kwargs)
        })
        
        return result
    
    return wrapper


# 应用性能监控到关键方法
DependencyContainer.resolve = performance_monitor(DependencyContainer.resolve)
DependencyContainer.register = performance_monitor(DependencyContainer.register)