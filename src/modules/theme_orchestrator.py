"""
主题协调器 - 统一管理主题应用时机和流程
解决主题应用时机问题，确保主题在正确的时间点应用
"""

import logging
from typing import Optional, List, Callable
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import QTimer, QObject, Signal
from PySide6.QtGui import QPalette

class ThemeOrchestrator(QObject):
    """主题协调器 - 管理主题应用的完整生命周期"""
    
    # 信号定义
    theme_applied = Signal(str)  # 主题应用完成信号
    theme_failed = Signal(str)   # 主题应用失败信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._app_instance = None
        self._theme_manager = None
        self._main_window = None
        self._theme_applied = False
        self._pending_widgets = []
        self._application_ready = False
        
    def set_application(self, app: QApplication):
        """设置应用程序实例"""
        self._app_instance = app
        self.logger.info(f"应用程序实例已设置: {app.__class__.__name__}")
        
    def set_theme_manager(self, theme_manager):
        """设置主题管理器"""
        self._theme_manager = theme_manager
        self.logger.info("主题管理器已设置")
        
    def set_main_window(self, main_window: QWidget):
        """设置主窗口"""
        self._main_window = main_window
        self.logger.info(f"主窗口已设置: {main_window.__class__.__name__}")
        
    def apply_theme_early(self) -> bool:
        """早期主题应用 - 在创建主要UI组件之前"""
        if not self._app_instance or not self._theme_manager:
            self.logger.error("应用程序实例或主题管理器未设置")
            return False
            
        try:
            # 应用基础主题
            self._theme_manager.apply_theme(self._app_instance, "dark")
            self._theme_applied = True
            self.logger.info("✅ 早期主题应用成功")
            self.theme_applied.emit("早期主题应用完成")
            return True
        except Exception as e:
            self.logger.error(f"❌ 早期主题应用失败: {e}")
            self.theme_failed.emit(str(e))
            return False
    
    def apply_theme_late(self) -> bool:
        """延迟主题应用 - 在所有UI组件创建完成后"""
        if not self._app_instance or not self._theme_manager:
            self.logger.error("应用程序实例或主题管理器未设置")
            return False
            
        try:
            # 重新应用主题到应用程序
            self._theme_manager.apply_theme(self._app_instance, "dark")
            
            # 如果有主窗口，强制应用主题
            if self._main_window:
                self._theme_manager.force_dark_theme(self._main_window)
                self.logger.info("✅ 主窗口强制主题应用成功")
            
            # 应用主题到所有待处理的组件
            for widget in self._pending_widgets:
                try:
                    self._theme_manager.force_dark_theme(widget)
                except Exception as e:
                    self.logger.warning(f"组件主题应用失败: {e}")
            
            self._pending_widgets.clear()
            self._theme_applied = True
            self.logger.info("✅ 延迟主题应用成功")
            self.theme_applied.emit("延迟主题应用完成")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 延迟主题应用失败: {e}")
            self.theme_failed.emit(str(e))
            return False
    
    def schedule_delayed_theme_application(self, delay_ms: int = 500):
        """调度延迟主题应用"""
        def delayed_apply():
            self.apply_theme_late()
            
        QTimer.singleShot(delay_ms, delayed_apply)
        self.logger.info(f"已调度延迟主题应用，延迟时间: {delay_ms}ms")
    
    def register_widget_for_theming(self, widget: QWidget):
        """注册组件等待主题应用"""
        if self._theme_applied and self._theme_manager:
            # 如果主题已应用，立即应用到组件
            try:
                self._theme_manager.force_dark_theme(widget)
                self.logger.info(f"立即应用主题到组件: {widget.__class__.__name__}")
            except Exception as e:
                self.logger.warning(f"组件主题应用失败: {e}")
        else:
            # 否则添加到待处理列表
            self._pending_widgets.append(widget)
            self.logger.info(f"组件已注册等待主题应用: {widget.__class__.__name__}")
    
    def mark_application_ready(self):
        """标记应用程序准备就绪"""
        self._application_ready = True
        self.logger.info("应用程序已标记为准备就绪")
        
        # 自动触发延迟主题应用
        if not self._theme_applied:
            self.schedule_delayed_theme_application()
    
    def get_theme_status(self) -> dict:
        """获取主题状态信息"""
        return {
            "theme_applied": self._theme_applied,
            "app_ready": self._application_ready,
            "has_app": self._app_instance is not None,
            "has_theme_manager": self._theme_manager is not None,
            "has_main_window": self._main_window is not None,
            "pending_widgets": len(self._pending_widgets)
        }
    
    def reset(self):
        """重置协调器状态"""
        self._theme_applied = False
        self._application_ready = False
        self._pending_widgets.clear()
        self.logger.info("主题协调器已重置")


# 全局主题协调器实例
_theme_orchestrator = None

def get_theme_orchestrator() -> ThemeOrchestrator:
    """获取全局主题协调器实例"""
    global _theme_orchestrator
    if _theme_orchestrator is None:
        _theme_orchestrator = ThemeOrchestrator()
    return _theme_orchestrator

def initialize_theme_system(app: QApplication, theme_manager=None):
    """初始化主题系统"""
    orchestrator = get_theme_orchestrator()
    orchestrator.set_application(app)
    
    if theme_manager is None:
        try:
            from .theme_manager_unified import get_unified_theme_manager
            theme_manager = get_unified_theme_manager()
        except ImportError:
            try:
                from .theme_manager import theme_manager as default_theme_manager
                theme_manager = default_theme_manager
            except ImportError:
                raise ImportError("无法导入任何主题管理器")
    
    orchestrator.set_theme_manager(theme_manager)
    
    # 应用早期主题
    success = orchestrator.apply_theme_early()
    if success:
        print("✅ 主题系统初始化成功")
    else:
        print("❌ 主题系统初始化失败")
    
    return orchestrator