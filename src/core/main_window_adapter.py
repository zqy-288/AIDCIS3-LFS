"""
MainWindow适配器
使现有的MainWindow支持依赖注入，而不修改原始代码
"""

from typing import Optional
from PySide6.QtCore import QObject, Signal

from .dependency_injection import DependencyContainer, injectable, ServiceLifetime
from .interfaces.service_interfaces import IConfigurationManager, ILogger
from .application import ApplicationCore, EventBus, ApplicationEvent


@injectable(ServiceLifetime.SINGLETON)
class MainWindowAdapter(QObject):
    """MainWindow适配器类"""
    
    # 窗口事件信号
    window_created = Signal()
    window_shown = Signal()
    window_closed = Signal()
    
    def __init__(self, 
                 app_core: ApplicationCore):
        super().__init__()
        
        self._app_core = app_core
        self._config_manager = None
        self._container = app_core.container
        self._event_bus = app_core.event_bus
        
        # 尝试获取配置管理器（如果已注册）
        try:
            from .interfaces.service_interfaces import IConfigurationManager
            if self._container.is_registered(IConfigurationManager):
                self._config_manager = self._container.resolve(IConfigurationManager)
        except:
            pass
        
        # 延迟导入主窗口类
        self._main_window_class = None
        self._main_window_instance = None
        
        # 订阅应用程序事件
        self._event_bus.subscribe("application_started", self._on_application_started)
        self._event_bus.subscribe("application_shutting_down", self._on_application_shutting_down)
    
    def _get_main_window_class(self):
        """延迟获取MainWindow类"""
        if self._main_window_class is None:
            try:
                import sys
                import os
                from pathlib import Path
                # 添加项目根目录到路径
                project_root = Path(__file__).parent.parent
                sys.path.insert(0, str(project_root))
                from src.main_window import MainWindow
                self._main_window_class = MainWindow
            except ImportError as e:
                raise ImportError(f"Cannot import MainWindow: {e}")
        return self._main_window_class
    
    def create_window(self):
        """创建主窗口实例"""
        if self._main_window_instance is not None:
            return self._main_window_instance
        
        try:
            # 获取MainWindow类
            MainWindowClass = self._get_main_window_class()
            
            # 创建实例
            self._main_window_instance = MainWindowClass()
            
            # 应用配置
            self._apply_window_config()
            
            # 设置事件连接
            self._setup_window_connections()
            
            # 发射窗口创建事件
            self.window_created.emit()
            
            # 发布应用程序事件
            event = ApplicationEvent("main_window_created", {
                "window": self._main_window_instance
            })
            self._event_bus.post_event(event)
            
            return self._main_window_instance
            
        except Exception as e:
            raise RuntimeError(f"Failed to create main window: {e}")
    
    def _apply_window_config(self):
        """应用窗口配置"""
        if not self._main_window_instance or not self._config_manager:
            return
        
        try:
            # 设置窗口尺寸
            width = self._config_manager.get('app.window.width', 1400)
            height = self._config_manager.get('app.window.height', 900)
            self._main_window_instance.resize(width, height)
            
            # 设置窗口标题
            app_name = self._config_manager.get('app.name', '上位机软件')
            self._main_window_instance.setWindowTitle(f"{app_name} - 管孔检测系统")
            
        except Exception as e:
            print(f"Warning: Failed to apply window config: {e}")
    
    def _setup_window_connections(self):
        """设置窗口事件连接"""
        if not self._main_window_instance:
            return
        
        # 连接窗口关闭事件
        original_close_event = self._main_window_instance.closeEvent
        
        def enhanced_close_event(event):
            # 发射窗口关闭信号
            self.window_closed.emit()
            
            # 发布应用程序事件
            app_event = ApplicationEvent("main_window_closing")
            self._event_bus.post_event(app_event)
            
            # 调用原始关闭事件
            if original_close_event:
                original_close_event(event)
            
            # 发布窗口已关闭事件
            app_event = ApplicationEvent("main_window_closed")
            self._event_bus.post_event(app_event)
            
            # 触发应用程序关闭
            self._app_core.shutdown()
        
        self._main_window_instance.closeEvent = enhanced_close_event
    
    def show_window(self):
        """显示主窗口"""
        if not self._main_window_instance:
            self.create_window()
        
        if self._main_window_instance:
            self._main_window_instance.show()
            self.window_shown.emit()
            
            # 发布窗口显示事件
            event = ApplicationEvent("main_window_shown")
            self._event_bus.post_event(event)
    
    def hide_window(self):
        """隐藏主窗口"""
        if self._main_window_instance:
            self._main_window_instance.hide()
    
    def close_window(self):
        """关闭主窗口"""
        if self._main_window_instance:
            self._main_window_instance.close()
    
    def get_window(self):
        """获取主窗口实例"""
        return self._main_window_instance
    
    def _on_application_started(self, event: ApplicationEvent):
        """应用程序启动完成事件处理"""
        pass
    
    def _on_application_shutting_down(self, event: ApplicationEvent):
        """应用程序关闭事件处理"""
        if self._main_window_instance:
            # 保存窗口配置
            self._save_window_config()
    
    def _save_window_config(self):
        """保存窗口配置"""
        if not self._main_window_instance or not self._config_manager:
            return
        
        try:
            # 保存窗口尺寸
            size = self._main_window_instance.size()
            self._config_manager.set('app.window.width', size.width())
            self._config_manager.set('app.window.height', size.height())
            
            # 保存窗口位置
            pos = self._main_window_instance.pos()
            self._config_manager.set('app.window.x', pos.x())
            self._config_manager.set('app.window.y', pos.y())
            
        except Exception as e:
            print(f"Warning: Failed to save window config: {e}")


# 修改ApplicationCore以使用MainWindowAdapter
def patch_application_core():
    """为ApplicationCore添加MainWindowAdapter支持"""
    from .application import ApplicationCore
    
    # 保存原始的create_main_window方法
    original_create_main_window = ApplicationCore.create_main_window
    
    def create_main_window(self):
        """创建主窗口（使用适配器）"""
        try:
            # 创建MainWindowAdapter实例
            adapter = self._container.resolve(MainWindowAdapter)
            
            # 创建并返回主窗口
            main_window = adapter.create_window()
            
            return main_window
            
        except Exception as e:
            self._logger.error(f"Failed to create main window through adapter: {e}")
            # 回退到原始方法
            return original_create_main_window(self)
    
    # 替换方法
    ApplicationCore.create_main_window = create_main_window


# 自动应用补丁
patch_application_core()