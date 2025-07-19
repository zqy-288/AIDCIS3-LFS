"""
核心应用程序类
提供应用程序生命周期管理、事件系统和依赖注入集成
"""

import sys
import os
import signal
import time
import logging
from typing import Optional, Dict, Any, Callable, List
from pathlib import Path
from abc import ABC, abstractmethod
from enum import Enum

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QObject, Signal, QTimer, QThread
from PySide6.QtGui import QPalette, QColor

# 导入依赖注入框架
from .dependency_injection import DependencyContainer, ServiceLifetime, injectable
from .interfaces.service_interfaces import IService, ILogger, IConfigurationManager, ServiceStatus


class ApplicationState(Enum):
    """应用程序状态枚举"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    RUNNING = "running"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN = "shutdown"
    ERROR = "error"


class IApplicationService(IService):
    """应用程序服务接口"""
    
    @abstractmethod
    def initialize(self) -> bool:
        """初始化服务"""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """清理服务资源"""
        pass


class ApplicationEvent:
    """应用程序事件类"""
    
    def __init__(self, event_type: str, data: Optional[Dict[str, Any]] = None):
        self.event_type = event_type
        self.data = data or {}
        self.timestamp = time.time()
        self.handled = False
    
    def mark_handled(self):
        """标记事件已处理"""
        self.handled = True


class EventBus(QObject):
    """事件总线"""
    
    # 事件信号
    event_posted = Signal(object)  # ApplicationEvent
    
    def __init__(self):
        super().__init__()
        self._handlers: Dict[str, List[Callable]] = {}
        self._logger = logging.getLogger(__name__)
    
    def subscribe(self, event_type: str, handler: Callable):
        """订阅事件"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        self._logger.debug(f"Event handler subscribed: {event_type}")
    
    def unsubscribe(self, event_type: str, handler: Callable):
        """取消订阅事件"""
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                self._logger.debug(f"Event handler unsubscribed: {event_type}")
            except ValueError:
                pass
    
    def post_event(self, event: ApplicationEvent):
        """发布事件"""
        self._logger.debug(f"Event posted: {event.event_type}")
        self.event_posted.emit(event)
        self._handle_event(event)
    
    def _handle_event(self, event: ApplicationEvent):
        """处理事件"""
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                self._logger.error(f"Event handler error: {e}")
        
        if handlers:
            event.mark_handled()


@injectable(ServiceLifetime.SINGLETON)
class ApplicationCore(QObject):
    """应用程序核心类"""
    
    # 应用程序状态信号
    state_changed = Signal(str)  # ApplicationState
    startup_progress = Signal(int, str)  # progress, message
    shutdown_progress = Signal(int, str)  # progress, message
    error_occurred = Signal(str, str)  # error_type, message
    
    def __init__(self, config_manager: Optional[IConfigurationManager] = None):
        super().__init__()
        
        # 基础属性
        self._state = ApplicationState.UNINITIALIZED
        self._qt_app: Optional[QApplication] = None
        self._main_window = None
        self._start_time = None
        
        # 依赖注入容器
        self._container = DependencyContainer()
        
        # 配置管理器（通过依赖注入或直接传入）
        self._config_manager = config_manager
        if not self._config_manager:
            try:
                # 尝试导入AI-3的配置管理器
                from ..data.config_manager import config_manager as cm
                self._config_manager = cm
            except ImportError:
                try:
                    # 使用默认配置管理器
                    from .default_configuration_manager import DefaultConfigurationManager
                    self._config_manager = DefaultConfigurationManager()
                except ImportError:
                    self._config_manager = None
        
        # 日志系统
        self._setup_logging()
        self._logger = logging.getLogger(__name__)
        
        # 记录配置管理器状态
        if self._config_manager:
            self._logger.info(f"配置管理器初始化成功: {self._config_manager.__class__.__name__}")
        else:
            self._logger.warning("配置管理器未初始化")
        
        # 事件系统
        self._event_bus = EventBus()
        
        # 服务列表
        self._services: List[IApplicationService] = []
        
        # 错误恢复
        self._recovery_attempts = 0
        self._max_recovery_attempts = 3
        
        # 性能监控
        self._startup_time = 0
        self._memory_usage = 0
        
        # 主题管理器
        self._theme_manager = None
        
        self._logger.info("ApplicationCore initialized")
    
    def _setup_logging(self):
        """设置日志系统"""
        # 创建日志目录
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # 配置日志格式
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(log_dir / "application.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    @property
    def state(self) -> ApplicationState:
        """获取应用程序状态"""
        return self._state
    
    @property
    def container(self) -> DependencyContainer:
        """获取依赖注入容器"""
        return self._container
    
    @property
    def event_bus(self) -> EventBus:
        """获取事件总线"""
        return self._event_bus
    
    @property
    def config_manager(self) -> Optional[IConfigurationManager]:
        """获取配置管理器"""
        return self._config_manager
    
    def _set_state(self, new_state: ApplicationState):
        """设置应用程序状态"""
        if self._state != new_state:
            old_state = self._state
            self._state = new_state
            self._logger.info(f"Application state changed: {old_state.value} -> {new_state.value}")
            self.state_changed.emit(new_state.value)
            
            # 发布状态变更事件
            event = ApplicationEvent("state_changed", {
                "old_state": old_state.value,
                "new_state": new_state.value
            })
            self._event_bus.post_event(event)
    
    def initialize(self) -> bool:
        """初始化应用程序"""
        try:
            self._set_state(ApplicationState.INITIALIZING)
            self._start_time = time.time()
            
            # 1. 检查依赖
            self.startup_progress.emit(10, "检查依赖包...")
            if not self._check_dependencies():
                return False
            
            # 2. 初始化配置
            self.startup_progress.emit(20, "加载配置...")
            self._initialize_config()
            
            # 3. 创建Qt应用
            self.startup_progress.emit(30, "初始化Qt应用...")
            if not self._create_qt_application():
                return False
            
            # 4. 注册核心服务
            self.startup_progress.emit(40, "注册核心服务...")
            self._register_core_services()
            
            # 5. 初始化服务
            self.startup_progress.emit(60, "初始化服务...")
            if not self._initialize_services():
                return False
            
            # 6. 设置信号处理
            self.startup_progress.emit(80, "设置信号处理...")
            self._setup_signal_handlers()
            
            # 7. 应用主题
            self.startup_progress.emit(90, "应用主题...")
            self._apply_unified_theme()
            
            self.startup_progress.emit(100, "初始化完成")
            self._set_state(ApplicationState.RUNNING)
            
            # 记录启动时间
            self._startup_time = time.time() - self._start_time
            self._logger.info(f"Application initialized successfully in {self._startup_time:.2f}s")
            
            return True
            
        except Exception as e:
            self._logger.error(f"Application initialization failed: {e}")
            self.error_occurred.emit("initialization_error", str(e))
            self._set_state(ApplicationState.ERROR)
            return False
    
    def _check_dependencies(self) -> bool:
        """检查必要的依赖包"""
        required_packages = [
            ('PySide6', 'PySide6'),
            ('pyqtgraph', 'pyqtgraph'),
            ('numpy', 'numpy'),
        ]
        
        missing_packages = []
        
        for package_name, import_name in required_packages:
            try:
                __import__(import_name)
            except ImportError:
                missing_packages.append(package_name)
        
        if missing_packages:
            error_msg = f"缺少必要的依赖包：{', '.join(missing_packages)}"
            self._logger.error(error_msg)
            return False
        
        return True
    
    def _initialize_config(self):
        """初始化配置"""
        if self._config_manager:
            # 设置应用程序默认配置
            default_config = {
                'app.name': '上位机软件',
                'app.version': '1.0.0',
                'app.window.width': 1400,
                'app.window.height': 900,
                'app.theme': 'dark',
                'performance.max_workers': 4,
                'performance.cache_size': 100,
                'database.echo': False
            }
            
            for key, value in default_config.items():
                if not self._config_manager.has(key):
                    self._config_manager.set(key, value)
    
    def _create_qt_application(self) -> bool:
        """创建Qt应用程序"""
        try:
            self._qt_app = QApplication(sys.argv)
            
            # 设置应用程序信息
            if self._config_manager:
                app_name = self._config_manager.get('app.name', '上位机软件')
                app_version = self._config_manager.get('app.version', '1.0.0')
            else:
                app_name = '上位机软件'
                app_version = '1.0.0'
            
            self._qt_app.setApplicationName(app_name)
            self._qt_app.setApplicationDisplayName("管孔检测系统")
            self._qt_app.setApplicationVersion(app_version)
            self._qt_app.setOrganizationName("检测系统开发团队")
            self._qt_app.setOrganizationDomain("detection-system.com")
            
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to create Qt application: {e}")
            return False
    
    def _register_core_services(self):
        """注册核心服务到DI容器"""
        # 注册应用程序核心服务
        self._container.register_instance(ApplicationCore, self)
        self._container.register_instance(EventBus, self._event_bus)
        
        # 注册配置管理器（如果存在）
        if self._config_manager:
            self._container.register_instance(IConfigurationManager, self._config_manager)
            # 也注册为具体类型
            self._container.register_instance(type(self._config_manager), self._config_manager)
        
        # 注册Qt应用程序
        if self._qt_app:
            self._container.register_instance(QApplication, self._qt_app)
        
        # 注册错误恢复管理器
        try:
            from .error_recovery import ErrorRecoveryManager
            error_recovery_manager = ErrorRecoveryManager(self)
            self._container.register_instance(ErrorRecoveryManager, error_recovery_manager)
            self._logger.info("ErrorRecoveryManager registered successfully")
        except ImportError:
            self._logger.warning("ErrorRecoveryManager not available")
        
        # 注册MainWindowAdapter
        from .main_window_adapter import MainWindowAdapter
        self._container.register_type(MainWindowAdapter, ServiceLifetime.SINGLETON)
    
    def _initialize_services(self) -> bool:
        """初始化所有注册的服务"""
        for service in self._services:
            try:
                if not service.initialize():
                    self._logger.error(f"Service initialization failed: {service.__class__.__name__}")
                    return False
            except Exception as e:
                self._logger.error(f"Service initialization error: {service.__class__.__name__} - {e}")
                return False
        
        return True
    
    def _setup_signal_handlers(self):
        """设置系统信号处理"""
        def signal_handler(signum, frame):
            self._logger.info(f"Received signal {signum}, initiating shutdown...")
            self.shutdown()
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    
    def _apply_unified_theme(self):
        """应用统一主题管理器"""
        if not self._qt_app:
            return
        
        try:
            # 导入统一主题管理器
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from modules.theme_manager_unified import get_unified_theme_manager
            from modules.theme_orchestrator import initialize_theme_system
            
            # 获取主题管理器实例
            self._theme_manager = get_unified_theme_manager()
            
            # 应用深色主题
            self._theme_manager.apply_theme(self._qt_app, "dark")
            
            # 初始化主题协调器
            self._theme_orchestrator = initialize_theme_system(self._qt_app)
            
            # 验证主题应用
            stylesheet = self._qt_app.styleSheet()
            if len(stylesheet) > 1000:
                self._logger.info(f"主题样式表已应用成功 (长度: {len(stylesheet)})")
            else:
                self._logger.warning(f"主题样式表可能未正确应用 (长度: {len(stylesheet)})")
                
        except Exception as e:
            self._logger.error(f"统一主题应用失败: {e}")
            # 回退到基本主题
            self._apply_fallback_theme()
    
    def _apply_fallback_theme(self):
        """应用回退主题（基本深色主题）"""
        if not self._qt_app:
            return
        
        try:
            palette = QPalette()
            
            # 基本深色主题颜色
            colors = {
                'background_primary': '#2C313C',
                'background_secondary': '#313642',
                'background_tertiary': '#3A404E',
                'text_primary': '#D3D8E0',
                'text_secondary': '#313642',
                'accent_primary': '#007ACC',
                'border_normal': '#404552'
            }
            
            # 设置调色板
            palette.setColor(QPalette.Window, QColor(colors['background_primary']))
            palette.setColor(QPalette.WindowText, QColor(colors['text_primary']))
            palette.setColor(QPalette.Base, QColor(colors['background_secondary']))
            palette.setColor(QPalette.AlternateBase, QColor(colors['background_tertiary']))
            palette.setColor(QPalette.Text, QColor(colors['text_primary']))
            palette.setColor(QPalette.Button, QColor(colors['background_tertiary']))
            palette.setColor(QPalette.ButtonText, QColor(colors['text_primary']))
            palette.setColor(QPalette.Highlight, QColor(colors['accent_primary']))
            
            self._qt_app.setPalette(palette)
            self._logger.info("回退主题应用成功")
            
        except Exception as e:
            self._logger.error(f"回退主题应用失败: {e}")
    
    def register_service(self, service: IApplicationService):
        """注册应用程序服务"""
        self._services.append(service)
        self._logger.info(f"Service registered: {service.__class__.__name__}")
    
    def create_main_window(self):
        """创建主窗口（通过适配器）"""
        try:
            # 导入MainWindowAdapter
            from .main_window_adapter import MainWindowAdapter
            
            # 手动创建适配器实例，因为DI容器可能没有正确解析参数
            adapter = MainWindowAdapter(app_core=self)
            
            # 通过适配器创建主窗口
            self._main_window = adapter.create_window()
            self._main_window_adapter = adapter
            
            self._logger.info("Main window created through adapter successfully")
            return self._main_window
            
        except Exception as e:
            self._logger.error(f"Failed to create main window through adapter: {e}")
            # 降级到直接创建
            try:
                # 使用绝对导入路径
                sys.path.insert(0, str(Path(__file__).parent.parent))
                from src.main_window import MainWindow
                self._main_window = MainWindow()
                self._logger.warning("Fallback to direct MainWindow creation")
                return self._main_window
            except Exception as fallback_error:
                self._logger.error(f"Fallback creation also failed: {fallback_error}")
                return None
    
    def run(self) -> int:
        """运行应用程序"""
        if self._state != ApplicationState.RUNNING:
            self._logger.error("Application not properly initialized")
            return 1
        
        if not self._qt_app:
            self._logger.error("Qt application not created")
            return 1
        
        try:
            # 创建并显示主窗口
            main_window = self.create_main_window()
            if main_window:
                # 应用主题到主窗口
                self._apply_theme_to_main_window(main_window)
                main_window.show()
                self._logger.info("Main window shown")
            else:
                self._logger.error("Failed to create main window")
                return 1
            
            # 发布应用程序启动完成事件
            event = ApplicationEvent("application_started", {
                "startup_time": self._startup_time
            })
            self._event_bus.post_event(event)
            
            # 运行Qt事件循环
            exit_code = self._qt_app.exec()
            
            self._logger.info(f"Application finished with exit code: {exit_code}")
            return exit_code
            
        except Exception as e:
            self._logger.error(f"Application runtime error: {e}")
            self.error_occurred.emit("runtime_error", str(e))
            return 1
    
    def shutdown(self):
        """关闭应用程序"""
        if self._state == ApplicationState.SHUTTING_DOWN:
            return
        
        self._set_state(ApplicationState.SHUTTING_DOWN)
        self._logger.info("Starting application shutdown...")
        
        try:
            # 1. 发布关闭事件
            self.shutdown_progress.emit(10, "发布关闭事件...")
            event = ApplicationEvent("application_shutting_down")
            self._event_bus.post_event(event)
            
            # 2. 关闭主窗口
            self.shutdown_progress.emit(30, "关闭主窗口...")
            if self._main_window:
                self._main_window.close()
            
            # 3. 清理服务
            self.shutdown_progress.emit(50, "清理服务...")
            for service in reversed(self._services):
                try:
                    service.cleanup()
                except Exception as e:
                    self._logger.error(f"Service cleanup error: {e}")
            
            # 4. 清理DI容器
            self.shutdown_progress.emit(70, "清理依赖注入容器...")
            self._container.reset()
            
            # 5. 退出Qt应用
            self.shutdown_progress.emit(90, "退出应用程序...")
            if self._qt_app:
                self._qt_app.quit()
            
            self.shutdown_progress.emit(100, "关闭完成")
            self._set_state(ApplicationState.SHUTDOWN)
            
            self._logger.info("Application shutdown completed")
            
        except Exception as e:
            self._logger.error(f"Shutdown error: {e}")
            self._set_state(ApplicationState.ERROR)
    
    def _apply_theme_to_main_window(self, main_window):
        """应用主题到主窗口"""
        if not main_window:
            return
        
        try:
            # 如果有主题管理器，强制应用主题到主窗口
            if self._theme_manager:
                self._theme_manager.force_dark_theme(main_window)
                self._logger.info("主题已强制应用到主窗口")
            
            # 如果有主题协调器，注册主窗口
            if hasattr(self, '_theme_orchestrator') and self._theme_orchestrator:
                self._theme_orchestrator.set_main_window(main_window)
                self._theme_orchestrator.mark_application_ready()
                self._logger.info("主窗口已注册到主题协调器")
                
        except Exception as e:
            self._logger.warning(f"主窗口主题应用失败: {e}")


class Application:
    """应用程序便捷包装类"""
    
    def __init__(self):
        self._core: Optional[ApplicationCore] = None
    
    def initialize(self) -> bool:
        """初始化应用程序"""
        try:
            self._core = ApplicationCore()
            return self._core.initialize()
        except Exception as e:
            print(f"Application initialization failed: {e}")
            return False
    
    def run(self) -> int:
        """运行应用程序"""
        if not self._core:
            print("Application not initialized")
            return 1
        
        return self._core.run()
    
    def shutdown(self):
        """关闭应用程序"""
        if self._core:
            self._core.shutdown()
    
    @property
    def core(self) -> Optional[ApplicationCore]:
        """获取应用程序核心"""
        return self._core


# 全局应用程序实例
_app_instance: Optional[Application] = None


def get_application() -> Application:
    """获取全局应用程序实例"""
    global _app_instance
    if _app_instance is None:
        _app_instance = Application()
    return _app_instance


def initialize_application() -> bool:
    """初始化全局应用程序"""
    app = get_application()
    return app.initialize()


def run_application() -> int:
    """运行全局应用程序"""
    app = get_application()
    return app.run()


def shutdown_application():
    """关闭全局应用程序"""
    app = get_application()
    app.shutdown()