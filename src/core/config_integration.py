"""
配置集成模块
集成AI-3的配置管理系统，添加热重载支持
"""

from typing import Optional, Callable, Dict, Any
from PySide6.QtCore import QObject, Signal, QTimer

from .dependency_injection import injectable, ServiceLifetime
from .application import ApplicationCore, EventBus, ApplicationEvent


@injectable(ServiceLifetime.SINGLETON)
class ConfigurationService(QObject):
    """配置服务类"""
    
    # 配置变更信号
    config_changed = Signal(str, object)  # key, value
    config_reloaded = Signal()
    
    def __init__(self, app_core: ApplicationCore):
        super().__init__()
        
        self._app_core = app_core
        self._event_bus = app_core.event_bus
        self._config_manager = None
        
        # 配置监听器
        self._config_listeners: Dict[str, list] = {}
        
        # 热重载定时器
        self._reload_timer = QTimer()
        self._reload_timer.timeout.connect(self._check_config_changes)
        self._reload_enabled = False
        
        # 初始化配置管理器
        self._initialize_config_manager()
        
        # 订阅应用程序事件
        self._event_bus.subscribe("application_started", self._on_application_started)
    
    def _initialize_config_manager(self):
        """初始化配置管理器"""
        try:
            # 导入AI-3的配置管理器
            from ..data.config_manager import config_manager
            self._config_manager = config_manager
            
            # 设置变更回调
            if hasattr(self._config_manager, 'add_change_callback'):
                self._config_manager.add_change_callback(self._on_config_changed)
            
        except ImportError:
            print("Warning: AI-3 config manager not available")
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        if self._config_manager and hasattr(self._config_manager, 'get_config'):
            return self._config_manager.get_config(key, default)
        return default
    
    def set_config(self, key: str, value: Any) -> None:
        """设置配置值"""
        if self._config_manager and hasattr(self._config_manager, 'set_config'):
            self._config_manager.set_config(key, value)
    
    def get_config_by_prefix(self, prefix: str) -> Dict[str, Any]:
        """根据前缀获取配置"""
        if self._config_manager and hasattr(self._config_manager, 'get_config_by_prefix'):
            return self._config_manager.get_config_by_prefix(prefix)
        return {}
    
    def enable_hot_reload(self, interval_ms: int = 1000):
        """启用配置热重载"""
        self._reload_enabled = True
        self._reload_timer.start(interval_ms)
        print(f"Configuration hot reload enabled (interval: {interval_ms}ms)")
    
    def disable_hot_reload(self):
        """禁用配置热重载"""
        self._reload_enabled = False
        self._reload_timer.stop()
        print("Configuration hot reload disabled")
    
    def add_config_listener(self, key_pattern: str, callback: Callable[[str, Any], None]):
        """添加配置监听器"""
        if key_pattern not in self._config_listeners:
            self._config_listeners[key_pattern] = []
        self._config_listeners[key_pattern].append(callback)
    
    def remove_config_listener(self, key_pattern: str, callback: Callable[[str, Any], None]):
        """移除配置监听器"""
        if key_pattern in self._config_listeners:
            try:
                self._config_listeners[key_pattern].remove(callback)
            except ValueError:
                pass
    
    def _on_config_changed(self, key: str, value: Any):
        """配置变更回调"""
        # 发射信号
        self.config_changed.emit(key, value)
        
        # 发布应用程序事件
        event = ApplicationEvent("config_changed", {
            "key": key,
            "value": value
        })
        self._event_bus.post_event(event)
        
        # 调用监听器
        self._notify_listeners(key, value)
    
    def _notify_listeners(self, key: str, value: Any):
        """通知配置监听器"""
        for pattern, callbacks in self._config_listeners.items():
            if self._key_matches_pattern(key, pattern):
                for callback in callbacks:
                    try:
                        callback(key, value)
                    except Exception as e:
                        print(f"Config listener error: {e}")
    
    def _key_matches_pattern(self, key: str, pattern: str) -> bool:
        """检查键是否匹配模式"""
        if pattern == "*":
            return True
        if pattern.endswith("*"):
            return key.startswith(pattern[:-1])
        return key == pattern
    
    def _check_config_changes(self):
        """检查配置变更（用于热重载）"""
        if not self._reload_enabled:
            return
        
        try:
            # 如果配置管理器支持检查变更
            if hasattr(self._config_manager, 'check_file_changes'):
                if self._config_manager.check_file_changes():
                    self._reload_config()
        except Exception as e:
            print(f"Config change check error: {e}")
    
    def _reload_config(self):
        """重新加载配置"""
        try:
            if hasattr(self._config_manager, 'reload'):
                self._config_manager.reload()
                
                # 发射重载信号
                self.config_reloaded.emit()
                
                # 发布重载事件
                event = ApplicationEvent("config_reloaded")
                self._event_bus.post_event(event)
                
                print("Configuration reloaded")
                
        except Exception as e:
            print(f"Config reload error: {e}")
    
    def _on_application_started(self, event: ApplicationEvent):
        """应用程序启动完成事件处理"""
        # 启用热重载
        self.enable_hot_reload(2000)  # 2秒检查一次


class ThemeConfigHandler:
    """主题配置处理器"""
    
    def __init__(self, config_service: ConfigurationService, app_core: ApplicationCore):
        self._config_service = config_service
        self._app_core = app_core
        
        # 监听主题相关配置变更
        self._config_service.add_config_listener("app.theme", self._on_theme_changed)
        self._config_service.add_config_listener("ui.*", self._on_ui_config_changed)
    
    def _on_theme_changed(self, key: str, value: Any):
        """主题配置变更处理"""
        print(f"Theme changed: {key} = {value}")
        
        # 重新应用主题
        if hasattr(self._app_core, '_apply_theme'):
            self._app_core._apply_theme()
    
    def _on_ui_config_changed(self, key: str, value: Any):
        """UI配置变更处理"""
        print(f"UI config changed: {key} = {value}")
        
        # 发布UI配置变更事件
        event = ApplicationEvent("ui_config_changed", {
            "key": key,
            "value": value
        })
        self._app_core.event_bus.post_event(event)


class WindowConfigHandler:
    """窗口配置处理器"""
    
    def __init__(self, config_service: ConfigurationService):
        self._config_service = config_service
        self._main_window = None
        
        # 监听窗口相关配置变更
        self._config_service.add_config_listener("app.window.*", self._on_window_config_changed)
    
    def set_main_window(self, main_window):
        """设置主窗口引用"""
        self._main_window = main_window
    
    def _on_window_config_changed(self, key: str, value: Any):
        """窗口配置变更处理"""
        if not self._main_window:
            return
        
        print(f"Window config changed: {key} = {value}")
        
        try:
            if key == "app.window.width" or key == "app.window.height":
                width = self._config_service.get_config("app.window.width", 1400)
                height = self._config_service.get_config("app.window.height", 900)
                self._main_window.resize(width, height)
            
            elif key == "app.window.title":
                self._main_window.setWindowTitle(str(value))
                
        except Exception as e:
            print(f"Window config update error: {e}")


def setup_config_integration(app_core: ApplicationCore) -> ConfigurationService:
    """设置配置集成"""
    
    # 创建配置服务
    config_service = ConfigurationService(app_core)
    
    # 注册到DI容器
    app_core.container.register_instance(ConfigurationService, config_service)
    
    # 创建配置处理器
    theme_handler = ThemeConfigHandler(config_service, app_core)
    window_handler = WindowConfigHandler(config_service)
    
    # 订阅主窗口创建事件
    def on_main_window_created(event: ApplicationEvent):
        main_window = event.data.get("window")
        if main_window:
            window_handler.set_main_window(main_window)
    
    app_core.event_bus.subscribe("main_window_created", on_main_window_created)
    
    return config_service