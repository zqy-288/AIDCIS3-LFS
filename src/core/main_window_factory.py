"""
主窗口工厂
统一管理多个主窗口实现，解决架构重复问题
"""

from typing import Optional, Dict, Any, Union
from enum import Enum
from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import QObject


class MainWindowType(Enum):
    """主窗口类型枚举"""
    STANDARD = "standard"       # 标准主窗口
    AIDCIS2 = "aidcis2"        # AIDCIS2专用主窗口
    ADAPTED = "adapted"         # 适配器主窗口


class MainWindowFactory:
    """主窗口工厂类"""
    
    _instances: Dict[MainWindowType, QMainWindow] = {}
    _default_type = MainWindowType.STANDARD
    
    @classmethod
    def create_main_window(cls, 
                          window_type: MainWindowType = None,
                          config: Optional[Dict[str, Any]] = None) -> QMainWindow:
        """
        创建主窗口实例
        
        Args:
            window_type: 窗口类型
            config: 配置参数
            
        Returns:
            QMainWindow: 主窗口实例
        """
        if window_type is None:
            window_type = cls._default_type
        
        # 检查是否已有实例（单例模式）
        if window_type in cls._instances:
            return cls._instances[window_type]
        
        # 根据类型创建对应的窗口
        if window_type == MainWindowType.STANDARD:
            window = cls._create_standard_window(config)
        elif window_type == MainWindowType.AIDCIS2:
            window = cls._create_aidcis2_window(config)
        elif window_type == MainWindowType.ADAPTED:
            window = cls._create_adapted_window(config)
        else:
            raise ValueError(f"不支持的窗口类型: {window_type}")
        
        # 缓存实例
        cls._instances[window_type] = window
        
        return window
    
    @classmethod
    def _create_standard_window(cls, config: Optional[Dict[str, Any]] = None) -> QMainWindow:
        """创建标准主窗口"""
        try:
            from src.main_window import MainWindow
            window = MainWindow()
            
            if config:
                cls._apply_window_config(window, config)
            
            return window
        except ImportError as e:
            raise ImportError(f"无法导入标准主窗口: {e}")
    
    @classmethod
    def _create_aidcis2_window(cls, config: Optional[Dict[str, Any]] = None) -> QMainWindow:
        """创建AIDCIS2主窗口"""
        try:
            from src.core_business.ui.main_window import AIDCIS2MainWindow
            window = AIDCIS2MainWindow()
            
            if config:
                cls._apply_window_config(window, config)
            
            return window
        except ImportError as e:
            raise ImportError(f"无法导入AIDCIS2主窗口: {e}")
    
    @classmethod
    def _create_adapted_window(cls, config: Optional[Dict[str, Any]] = None) -> QMainWindow:
        """创建适配器主窗口"""
        try:
            from src.core.main_window_adapter import MainWindowAdapter
            
            # 需要先获取ApplicationCore
            from src.core.application import ApplicationCore, get_application
            
            app = get_application()
            if app and app.core:
                adapter = MainWindowAdapter(app.core)
                window = adapter.create_window()
            else:
                raise RuntimeError("ApplicationCore未初始化")
            
            if config:
                cls._apply_window_config(window, config)
            
            return window
        except ImportError as e:
            raise ImportError(f"无法导入适配器主窗口: {e}")
    
    @classmethod
    def _apply_window_config(cls, window: QMainWindow, config: Dict[str, Any]):
        """应用窗口配置"""
        # 设置窗口标题
        if 'title' in config:
            window.setWindowTitle(config['title'])
        
        # 设置窗口尺寸
        if 'geometry' in config:
            geometry = config['geometry']
            if isinstance(geometry, (list, tuple)) and len(geometry) == 4:
                window.setGeometry(*geometry)
        
        # 设置窗口大小
        if 'size' in config:
            size = config['size']
            if isinstance(size, (list, tuple)) and len(size) == 2:
                window.resize(*size)
        
        # 设置最小尺寸
        if 'min_size' in config:
            min_size = config['min_size']
            if isinstance(min_size, (list, tuple)) and len(min_size) == 2:
                window.setMinimumSize(*min_size)
        
        # 设置最大尺寸
        if 'max_size' in config:
            max_size = config['max_size']
            if isinstance(max_size, (list, tuple)) and len(max_size) == 2:
                window.setMaximumSize(*max_size)
        
        # 设置窗口状态
        if 'maximized' in config and config['maximized']:
            window.showMaximized()
        
        if 'fullscreen' in config and config['fullscreen']:
            window.showFullScreen()
    
    @classmethod
    def get_main_window(cls, window_type: MainWindowType = None) -> Optional[QMainWindow]:
        """
        获取已创建的主窗口实例
        
        Args:
            window_type: 窗口类型
            
        Returns:
            Optional[QMainWindow]: 主窗口实例或None
        """
        if window_type is None:
            window_type = cls._default_type
        
        return cls._instances.get(window_type)
    
    @classmethod
    def destroy_window(cls, window_type: MainWindowType):
        """
        销毁指定类型的主窗口
        
        Args:
            window_type: 窗口类型
        """
        if window_type in cls._instances:
            window = cls._instances[window_type]
            window.close()
            window.deleteLater()
            del cls._instances[window_type]
    
    @classmethod
    def destroy_all_windows(cls):
        """销毁所有主窗口"""
        for window_type in list(cls._instances.keys()):
            cls.destroy_window(window_type)
    
    @classmethod
    def set_default_type(cls, window_type: MainWindowType):
        """
        设置默认窗口类型
        
        Args:
            window_type: 窗口类型
        """
        cls._default_type = window_type
    
    @classmethod
    def get_available_types(cls) -> list:
        """获取可用的窗口类型列表"""
        return list(MainWindowType)
    
    @classmethod
    def is_window_available(cls, window_type: MainWindowType) -> bool:
        """
        检查指定类型的窗口是否可用
        
        Args:
            window_type: 窗口类型
            
        Returns:
            bool: 是否可用
        """
        try:
            if window_type == MainWindowType.STANDARD:
                from src.main_window import MainWindow
                return True
            elif window_type == MainWindowType.AIDCIS2:
                from src.core_business.ui.main_window import AIDCIS2MainWindow
                return True
            elif window_type == MainWindowType.ADAPTED:
                from src.core.main_window_adapter import MainWindowAdapter
                return True
            else:
                return False
        except ImportError:
            return False


class MainWindowManager:
    """主窗口管理器 - 提供统一的窗口管理接口"""
    
    def __init__(self, default_type: MainWindowType = MainWindowType.STANDARD):
        self._factory = MainWindowFactory
        self._factory.set_default_type(default_type)
        self._current_window: Optional[QMainWindow] = None
    
    def create_window(self, 
                     window_type: MainWindowType = None,
                     config: Optional[Dict[str, Any]] = None) -> QMainWindow:
        """创建并返回主窗口"""
        self._current_window = self._factory.create_main_window(window_type, config)
        return self._current_window
    
    def get_current_window(self) -> Optional[QMainWindow]:
        """获取当前窗口"""
        return self._current_window
    
    def switch_window_type(self, window_type: MainWindowType, 
                          config: Optional[Dict[str, Any]] = None) -> QMainWindow:
        """切换窗口类型"""
        # 销毁当前窗口
        if self._current_window:
            current_type = None
            for wtype, window in self._factory._instances.items():
                if window == self._current_window:
                    current_type = wtype
                    break
            if current_type:
                self._factory.destroy_window(current_type)
        
        # 创建新窗口
        return self.create_window(window_type, config)
    
    def cleanup(self):
        """清理所有窗口"""
        self._factory.destroy_all_windows()
        self._current_window = None


# 便捷函数
def create_standard_main_window(config: Optional[Dict[str, Any]] = None) -> QMainWindow:
    """创建标准主窗口"""
    return MainWindowFactory.create_main_window(MainWindowType.STANDARD, config)

def create_aidcis2_main_window(config: Optional[Dict[str, Any]] = None) -> QMainWindow:
    """创建AIDCIS2主窗口"""
    return MainWindowFactory.create_main_window(MainWindowType.AIDCIS2, config)

def get_main_window_manager(default_type: MainWindowType = MainWindowType.STANDARD) -> MainWindowManager:
    """获取主窗口管理器"""
    return MainWindowManager(default_type)