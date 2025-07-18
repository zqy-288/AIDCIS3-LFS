"""
核心接口定义模块
为AI-2和AI-3提供接口定义
"""

from .service_interfaces import (
    IService,
    IRepository,
    IDataProcessor,
    IEventHandler,
    ILogger,
    IConfigurationManager,
    IHealthChecker
)

from .di_interfaces import (
    IDependencyContainer,
    IServiceRegistration,
    IServiceResolver,
    ILifecycleManager
)

__all__ = [
    'IService',
    'IRepository', 
    'IDataProcessor',
    'IEventHandler',
    'ILogger',
    'IConfigurationManager',
    'IHealthChecker',
    'IDependencyContainer',
    'IServiceRegistration',
    'IServiceResolver',
    'ILifecycleManager'
]