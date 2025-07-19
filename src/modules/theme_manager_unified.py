"""
统一主题管理器
整合所有主题管理器功能，提供单一的主题管理接口
替代所有其他主题管理器版本
"""

import logging
import weakref
import gc
from typing import Optional, Dict, Any, List
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtGui import QFont, QFontDatabase, QPalette, QColor
from PySide6.QtCore import Qt, QObject, QTimer, Signal

class UnifiedThemeManager(QObject):
    """统一主题管理器 - 整合所有主题管理功能"""
    
    # 信号定义
    theme_changed = Signal(str)  # 主题改变信号
    theme_applied = Signal()     # 主题应用完成信号
    
    _instance = None
    _widget_refs = None
    _cleanup_timer = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized') or not self._initialized:
            super().__init__()
            self.logger = logging.getLogger(__name__)
            self._widget_refs = weakref.WeakSet()
            self._cleanup_timer = None
            self._initialized = True
            self._current_theme = "dark"
            self._theme_config = {}
            self.logger.info("统一主题管理器已初始化")
            
            # 延迟初始化定时器，只有在QApplication存在时才创建
            self._init_cleanup_timer_deferred()
    
    def __del__(self):
        self.cleanup()
    
    def _init_cleanup_timer_deferred(self):
        """延迟初始化清理定时器"""
        try:
            from PySide6.QtWidgets import QApplication
            if QApplication.instance():
                self._cleanup_timer = QTimer()
                self._cleanup_timer.timeout.connect(self._cleanup_weak_refs)
                self._cleanup_timer.start(30000)  # 30秒清理一次
        except Exception as e:
            self.logger.warning(f"清理定时器初始化失败: {e}")
    
    def cleanup(self):
        """清理资源和内存"""
        if hasattr(self, '_cleanup_timer') and self._cleanup_timer:
            self._cleanup_timer.stop()
            self._cleanup_timer.deleteLater()
            self._cleanup_timer = None
        
        if hasattr(self, '_widget_refs') and self._widget_refs:
            self._widget_refs.clear()
            self._widget_refs = None
        
        gc.collect()
    
    def _cleanup_weak_refs(self):
        """清理弱引用集合中的死引用"""
        if self._widget_refs:
            gc.collect()
    
    def register_widget(self, widget: QWidget):
        """注册widget到弱引用集合中进行内存管理"""
        if self._widget_refs is not None:
            self._widget_refs.add(widget)
    
    # 现代科技蓝配色方案 - 完全符合UI设计规范文档
    COLORS = {
        # 主背景色 - 按文档规范
        'background_primary': '#2C313C',        # 主背景色
        'background_secondary': '#313642',      # 面板背景色
        'background_tertiary': '#3A404E',       # 标题栏/高亮背景
        
        # 强调色 - 按文档规范
        'accent_primary': '#007ACC',            # 主操作色/主题蓝
        'accent_secondary': '#4A90E2',          # 辅助蓝色
        'accent_hover': '#0099FF',              # 悬停状态
        'accent_pressed': '#005C99',            # 按下状态
        
        # 文本色 - 按文档规范
        'text_primary': '#D3D8E0',              # 主文本/图标色
        'text_secondary': '#313642',            # 标题/醒目文字
        'text_disabled': '#AAAAAA',             # 禁用文字
        
        # 状态色 - 按文档规范
        'success': '#2ECC71',                   # 成功/合格状态
        'warning': '#E67E22',                   # 警告/异常状态
        'error': '#E74C3C',                     # 错误/不合格状态
        'info': '#007ACC',                      # 信息状态使用主题蓝
        
        # 边框色 - 按文档规范
        'border_normal': '#404552',             # 边框/分割线
        'border_focus': '#007ACC',              # 焦点边框
        'border_disabled': '#555555',           # 禁用边框
        
        # 特殊背景
        'status_bar': '#1E222B',                # 状态栏背景
        'selection': '#007ACC',                 # 选中背景
        'hover': '#3A404E'                      # 悬停背景
    }
    
    def get_main_stylesheet(self) -> str:
        """获取主样式表"""
        return f"""
/* 整体窗口和字体设置 - 按文档规范 */
QWidget {{
    background-color: {self.COLORS['background_primary']} !important;
    color: {self.COLORS['text_primary']} !important;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "PingFang SC", "Microsoft YaHei", sans-serif;
    font-size: 15px;
}}

/* 强制所有QWidget子类使用深色背景 */
QMainWindow, QDialog, QFrame, QGraphicsView {{
    background-color: {self.COLORS['background_primary']} !important;
}}

/* 确保所有容器组件使用正确的背景色 */
QGroupBox, QTabWidget::pane, QScrollArea {{
    background-color: {self.COLORS['background_secondary']} !important;
}}

/* 默认按钮样式 */
QPushButton {{
    background-color: {self.COLORS['accent_primary']};
    color: white;
    border: none;
    border-radius: 5px;
    padding: 8px 20px;
    font-weight: bold;
    min-height: 24px;
}}
QPushButton:hover {{
    background-color: {self.COLORS['accent_hover']};
}}
QPushButton:pressed {{
    background-color: {self.COLORS['accent_pressed']};
}}
QPushButton:disabled {{
    background-color: {self.COLORS['border_disabled']};
    color: {self.COLORS['text_disabled']};
    opacity: 0.5;
}}

/* 输入框、下拉框等 */
QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox {{
    background-color: {self.COLORS['background_secondary']};
    border: 1px solid {self.COLORS['border_normal']};
    border-radius: 4px;
    padding: 6px;
    color: {self.COLORS['text_primary']};
    min-height: 20px;
}}
QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QSpinBox:focus {{
    border: 1px solid {self.COLORS['border_focus']};
}}

/* 表格和表头 */
QTableWidget, QTableView {{
    background-color: {self.COLORS['background_secondary']} !important;
    gridline-color: {self.COLORS['border_normal']} !important;
    border: 1px solid {self.COLORS['border_normal']} !important;
    selection-background-color: {self.COLORS['selection']} !important;
    selection-color: white !important;
    color: {self.COLORS['text_primary']} !important;
}}
QHeaderView::section {{
    background-color: {self.COLORS['background_tertiary']};
    color: {self.COLORS['text_primary']};
    padding: 6px;
    border: none;
    font-weight: bold;
    border-right: 1px solid {self.COLORS['border_normal']};
    border-bottom: 1px solid {self.COLORS['border_normal']};
}}

/* 组框 */
QGroupBox {{
    background-color: {self.COLORS['background_secondary']};
    color: {self.COLORS['text_primary']};
    border: 1px solid {self.COLORS['border_normal']};
    border-radius: 8px;
    margin-top: 10px;
    margin-bottom: 8px;
    font-weight: bold;
    padding: 10px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 8px 0 8px;
    color: {self.COLORS['text_secondary']};
    font-size: 16px;
    font-weight: bold;
}}

/* 标签 */
QLabel {{
    background-color: transparent;
    color: {self.COLORS['text_primary']} !important;
}}

/* 状态按钮样式 */
QPushButton#SuccessButton {{
    background-color: {self.COLORS['success']};
    color: white;
    border: none;
    border-radius: 5px;
    padding: 8px 20px;
    font-weight: bold;
    min-height: 24px;
}}
QPushButton#SuccessButton:hover {{
    background-color: #27AE60;
}}
QPushButton#SuccessButton:pressed {{
    background-color: #1E8449;
}}

QPushButton#ErrorButton {{
    background-color: {self.COLORS['error']};
    color: white;
    border: none;
    border-radius: 5px;
    padding: 8px 20px;
    font-weight: bold;
    min-height: 24px;
}}
QPushButton#ErrorButton:hover {{
    background-color: #C0392B;
}}
QPushButton#ErrorButton:pressed {{
    background-color: #922B21;
}}

QPushButton#WarningButton {{
    background-color: {self.COLORS['warning']};
    color: white;
    border: none;
    border-radius: 5px;
    padding: 8px 20px;
    font-weight: bold;
    min-height: 24px;
}}
QPushButton#WarningButton:hover {{
    background-color: #D35400;
}}
QPushButton#WarningButton:pressed {{
    background-color: #A04000;
}}

/* 菜单栏 */
QMenuBar {{
    background-color: {self.COLORS['background_secondary']};
    color: {self.COLORS['text_primary']};
    border-bottom: 1px solid {self.COLORS['border_normal']};
}}
QMenuBar::item {{
    background-color: transparent;
    padding: 4px 8px;
}}
QMenuBar::item:selected {{
    background-color: {self.COLORS['accent_primary']};
}}

/* 状态栏 */
QStatusBar {{
    background-color: {self.COLORS['status_bar']};
    color: {self.COLORS['text_primary']};
    border-top: 1px solid {self.COLORS['border_normal']};
}}

/* 强制覆盖所有白色背景和浅色背景 */
* {{
    background-color: transparent;
}}

/* 主要容器必须使用深色背景 */
QMainWindow > QWidget {{
    background-color: {self.COLORS['background_primary']} !important;
}}

/* 中央部件深色背景 */
QMainWindow > QWidget > QWidget {{
    background-color: {self.COLORS['background_primary']} !important;
}}

/* 强制所有图像和绘制区域使用深色背景 */
QGraphicsView, QAbstractItemView, QAbstractScrollArea {{
    background-color: {self.COLORS['background_primary']} !important;
}}

/* 强制所有滚动区域使用深色背景 */
QScrollArea > QWidget > QWidget {{
    background-color: {self.COLORS['background_primary']} !important;
}}

/* 强制所有分割器使用深色背景 */
QSplitter::handle {{
    background-color: {self.COLORS['background_tertiary']} !important;
}}

/* 强制所有文本编辑器使用深色背景 */
QTextEdit, QPlainTextEdit {{
    background-color: {self.COLORS['background_secondary']} !important;
    color: {self.COLORS['text_primary']} !important;
}}

/* 强制所有列表视图使用深色背景 */
QListView, QTreeView {{
    background-color: {self.COLORS['background_secondary']} !important;
    color: {self.COLORS['text_primary']} !important;
}}

/* 禁用所有可能的白色背景 */
*[style*="background-color: white"] {{
    background-color: {self.COLORS['background_primary']} !important;
}}
*[style*="background-color: #fff"] {{
    background-color: {self.COLORS['background_primary']} !important;
}}
*[style*="background-color: #ffffff"] {{
    background-color: {self.COLORS['background_primary']} !important;
}}
*[style*="color: black"] {{
    color: {self.COLORS['text_primary']} !important;
}}
*[style*="color: #000"] {{
    color: {self.COLORS['text_primary']} !important;
}}
*[style*="color: #000000"] {{
    color: {self.COLORS['text_primary']} !important;
}}
"""
    
    def apply_theme(self, app: QApplication, theme_type: str = "dark"):
        """应用主题到应用程序"""
        try:
            # 清理之前的主题资源
            self._cleanup_previous_theme()
            
            if theme_type == "dark":
                self._apply_dark_theme(app)
            else:
                self._apply_light_theme(app)
            
            self._current_theme = theme_type
            self.theme_changed.emit(theme_type)
            self.theme_applied.emit()
            self.logger.info(f"主题应用成功: {theme_type}")
            
        except Exception as e:
            self.logger.error(f"主题应用失败: {e}")
            raise
    
    def _cleanup_previous_theme(self):
        """清理之前主题的资源"""
        if self._widget_refs:
            dead_refs = []
            for widget_ref in list(self._widget_refs):
                try:
                    widget = widget_ref()
                    if widget is None:
                        dead_refs.append(widget_ref)
                    else:
                        widget.setStyleSheet("")
                except:
                    dead_refs.append(widget_ref)
            
            for dead_ref in dead_refs:
                self._widget_refs.discard(dead_ref)
        
        gc.collect()
    
    def _apply_dark_theme(self, app: QApplication):
        """应用深色主题"""
        # 获取完整的样式表
        stylesheet = self.get_main_stylesheet()
        
        # 应用到应用程序
        app.setStyleSheet(stylesheet)
        
        # 设置应用程序调色板为深色
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(self.COLORS['background_primary']))
        palette.setColor(QPalette.WindowText, QColor(self.COLORS['text_primary']))
        palette.setColor(QPalette.Base, QColor(self.COLORS['background_secondary']))
        palette.setColor(QPalette.AlternateBase, QColor(self.COLORS['background_tertiary']))
        palette.setColor(QPalette.Text, QColor(self.COLORS['text_primary']))
        palette.setColor(QPalette.BrightText, QColor(self.COLORS['text_secondary']))
        palette.setColor(QPalette.Button, QColor(self.COLORS['background_tertiary']))
        palette.setColor(QPalette.ButtonText, QColor(self.COLORS['text_primary']))
        palette.setColor(QPalette.Highlight, QColor(self.COLORS['accent_primary']))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        
        app.setPalette(palette)
        self.logger.info("深色主题应用成功")
    
    def _apply_light_theme(self, app: QApplication):
        """应用浅色主题"""
        light_stylesheet = self._get_light_stylesheet()
        app.setStyleSheet(light_stylesheet)
        
        # 设置浅色调色板
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#2C313C"))
        palette.setColor(QPalette.WindowText, QColor("#D3D8E0"))
        palette.setColor(QPalette.Base, QColor("#313642"))
        palette.setColor(QPalette.AlternateBase, QColor("#F0F0F0"))
        palette.setColor(QPalette.Text, QColor("#D3D8E0"))
        palette.setColor(QPalette.BrightText, QColor("#000000"))
        palette.setColor(QPalette.Button, QColor("#404552"))
        palette.setColor(QPalette.ButtonText, QColor("#D3D8E0"))
        palette.setColor(QPalette.Highlight, QColor(self.COLORS['accent_primary']))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        
        app.setPalette(palette)
        self.logger.info("浅色主题应用成功")
    
    def _get_light_stylesheet(self) -> str:
        """获取浅色主题样式表"""
        return f"""
/* 浅色主题样式表 */
QWidget {{
    background-color: #2C313C;
    color: #D3D8E0;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "PingFang SC", "Microsoft YaHei", sans-serif;
    font-size: 15px;
}}

QMainWindow, QDialog, QFrame {{
    background-color: #2C313C;
}}

QGroupBox {{
    background-color: #313642;
    border: 1px solid #404552;
    border-radius: 8px;
    margin-top: 10px;
    padding: 10px;
}}

QPushButton {{
    background-color: {self.COLORS['accent_primary']};
    color: white;
    border: none;
    border-radius: 5px;
    padding: 8px 20px;
    font-weight: bold;
    min-height: 24px;
}}

QPushButton:hover {{
    background-color: {self.COLORS['accent_hover']};
}}

QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: #313642;
    color: #D3D8E0;
    border: 1px solid #404552;
    border-radius: 4px;
    padding: 6px;
}}

QTableWidget, QTableView {{
    background-color: #313642;
    gridline-color: #404552;
    color: #D3D8E0;
}}

QLabel {{
    color: #D3D8E0;
}}
"""
    
    def force_dark_theme(self, widget: QWidget):
        """强制为特定widget应用深色主题"""
        self.register_widget(widget)
        
        # 清除现有样式表
        if widget.styleSheet():
            widget.setStyleSheet("")
            
        # 应用深色调色板
        palette = widget.palette()
        palette.setColor(QPalette.Window, QColor(self.COLORS['background_primary']))
        palette.setColor(QPalette.WindowText, QColor(self.COLORS['text_primary']))
        palette.setColor(QPalette.Base, QColor(self.COLORS['background_secondary']))
        palette.setColor(QPalette.Text, QColor(self.COLORS['text_primary']))
        widget.setPalette(palette)
        
        # 递归应用到所有子组件
        self._apply_theme_to_children(widget)
        
        try:
            widget.update()
        except TypeError:
            # 某些组件的update方法需要参数
            pass
        self.logger.info(f"强制深色主题应用到: {widget.__class__.__name__}")
    
    def _apply_theme_to_children(self, widget: QWidget):
        """递归应用主题到所有子组件"""
        for child in widget.findChildren(QWidget):
            try:
                # 清除子组件的样式表
                if child.styleSheet():
                    child.setStyleSheet("")
                
                # 应用深色调色板
                palette = child.palette()
                palette.setColor(QPalette.Window, QColor(self.COLORS['background_primary']))
                palette.setColor(QPalette.WindowText, QColor(self.COLORS['text_primary']))
                palette.setColor(QPalette.Base, QColor(self.COLORS['background_secondary']))
                palette.setColor(QPalette.Text, QColor(self.COLORS['text_primary']))
                child.setPalette(palette)
                
                # 特殊处理某些组件类型
                if hasattr(child, 'setAutoFillBackground'):
                    child.setAutoFillBackground(True)
                    
            except Exception as e:
                self.logger.warning(f"子组件主题应用失败: {child.__class__.__name__} - {e}")
                continue
    
    def get_current_theme(self) -> str:
        """获取当前主题"""
        return self._current_theme
    
    def get_theme_colors(self) -> Dict[str, str]:
        """获取当前主题颜色"""
        return self.COLORS.copy()
    
    def is_dark_theme(self) -> bool:
        """判断是否为深色主题"""
        return self._current_theme == "dark"


# 全局统一主题管理器实例
def get_unified_theme_manager() -> UnifiedThemeManager:
    """获取统一主题管理器实例"""
    return UnifiedThemeManager()

# 向后兼容
theme_manager = get_unified_theme_manager()