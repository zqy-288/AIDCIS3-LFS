"""
核心接口定义模块
为AI-2和AI-3提供接口定义，包含系统级接口契约
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

from .main_interfaces import (
    IMainViewController,
    IMainBusinessController, 
    IMainViewModel,
    IMainWindowCoordinator,
    UserAction
)

from .ui_plugin_interface import (
    IUIPlugin,
    IUIThemePlugin,
    IUIToolPlugin,
    IUIDialogPlugin,
    UIPluginType,
    UIPluginCapability,
    UIPluginMetadata,
    UIPluginEvent,
    UIPluginRegistry,
    get_ui_plugin_registry,
    register_ui_plugin,
    unregister_ui_plugin,
    get_ui_plugin,
    list_ui_plugins_by_type,
    list_ui_plugins_by_capability
)

__all__ = [
    # Core system interfaces
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
    'ILifecycleManager',
    
    # Main MVVM interfaces
    'IMainViewController',
    'IMainBusinessController',
    'IMainViewModel', 
    'IMainWindowCoordinator',
    'UserAction',
    
    # UI Plugin system
    'IUIPlugin',
    'IUIThemePlugin',
    'IUIToolPlugin', 
    'IUIDialogPlugin',
    'UIPluginType',
    'UIPluginCapability',
    'UIPluginMetadata',
    'UIPluginEvent',
    'UIPluginRegistry',
    'get_ui_plugin_registry',
    'register_ui_plugin',
    'unregister_ui_plugin',
    'get_ui_plugin',
    'list_ui_plugins_by_type',
    'list_ui_plugins_by_capability'
]