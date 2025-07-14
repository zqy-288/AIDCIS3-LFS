"""
主题调试器模块
提供详细的调试信息来定位主题问题
"""

import logging
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import QObject
from PySide6.QtGui import QPalette

class ThemeDebugger:
    """主题调试器"""
    
    @staticmethod
    def setup_debug_logging():
        """设置调试日志"""
        logging.basicConfig(
            level=logging.DEBUG,
            format='[%(levelname)s] %(asctime)s - %(name)s - %(message)s',
            handlers=[
                logging.FileHandler('theme_debug.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger('ThemeDebugger')
    
    @staticmethod
    def debug_widget(widget, logger):
        """调试widget的样式信息"""
        logger.debug(f"\n{'='*60}")
        logger.debug(f"调试Widget: {widget.__class__.__name__}")
        logger.debug(f"ObjectName: {widget.objectName()}")
        
        # 检查内联样式
        stylesheet = widget.styleSheet()
        if stylesheet:
            logger.warning(f"发现内联样式表 ({len(stylesheet)} 字符):")
            logger.warning(f"前100字符: {stylesheet[:100]}...")
        else:
            logger.info("没有内联样式表")
            
        # 检查调色板
        palette = widget.palette()
        window_color = palette.color(QPalette.Window)
        base_color = palette.color(QPalette.Base)
        text_color = palette.color(QPalette.Text)
        
        logger.info(f"调色板颜色:")
        logger.info(f"  Window: {window_color.name()}")
        logger.info(f"  Base: {base_color.name()}")
        logger.info(f"  Text: {text_color.name()}")
        
        # 检查父级
        parent = widget.parent()
        if parent:
            logger.debug(f"父级: {parent.__class__.__name__}")
        else:
            logger.debug("无父级")
            
        return stylesheet
    
    @staticmethod
    def debug_application(app, logger):
        """调试应用程序级别的样式"""
        logger.info(f"\n{'='*60}")
        logger.info("应用程序级别调试")
        
        # 检查应用样式表
        app_stylesheet = app.styleSheet()
        if app_stylesheet:
            logger.info(f"应用程序样式表长度: {len(app_stylesheet)} 字符")
            
            # 检查关键特征
            features = {
                '#2C313C': '深色背景',
                '#313642': '面板背景',
                '#007ACC': '主题蓝',
                '!important': '强制覆盖',
                'QWidget': '全局widget样式',
                'background-color': '背景色设置'
            }
            
            logger.info("关键特征检查:")
            for feature, desc in features.items():
                if feature in app_stylesheet:
                    logger.info(f"  ✓ {desc}: 存在")
                else:
                    logger.warning(f"  ✗ {desc}: 缺失")
        else:
            logger.error("应用程序没有样式表!")
            
        # 检查调色板
        app_palette = app.palette()
        logger.info(f"应用程序调色板:")
        logger.info(f"  Window: {app_palette.color(QPalette.Window).name()}")
        logger.info(f"  Base: {app_palette.color(QPalette.Base).name()}")
        
    @staticmethod
    def find_style_conflicts(widget, logger, depth=0):
        """递归查找样式冲突"""
        if depth > 5:  # 防止递归过深
            return
            
        indent = "  " * depth
        widget_name = widget.__class__.__name__
        object_name = widget.objectName() or "no-name"
        
        # 检查样式
        if widget.styleSheet():
            logger.warning(f"{indent}{widget_name}[{object_name}] 有内联样式!")
            
        # 递归检查子widget
        for child in widget.findChildren(QWidget):
            if child.parent() == widget:  # 只检查直接子级
                ThemeDebugger.find_style_conflicts(child, logger, depth + 1)
                
    @staticmethod
    def inject_debug_hooks(widget):
        """注入调试钩子"""
        original_show = widget.show
        original_setStyleSheet = widget.setStyleSheet
        
        def debug_show():
            logger = logging.getLogger('ThemeDebugger')
            logger.debug(f"{widget.__class__.__name__}.show() 被调用")
            return original_show()
            
        def debug_setStyleSheet(stylesheet):
            logger = logging.getLogger('ThemeDebugger')
            logger.warning(f"{widget.__class__.__name__}.setStyleSheet() 被调用!")
            logger.warning(f"设置样式: {stylesheet[:100]}...")
            return original_setStyleSheet(stylesheet)
            
        widget.show = debug_show
        widget.setStyleSheet = debug_setStyleSheet
        
    @staticmethod
    def create_debug_report(main_window):
        """创建调试报告"""
        logger = ThemeDebugger.setup_debug_logging()
        
        logger.info("="*80)
        logger.info("AIDCIS3-LFS 主题调试报告")
        logger.info("="*80)
        
        # 调试应用程序
        app = QApplication.instance()
        if app:
            ThemeDebugger.debug_application(app, logger)
        else:
            logger.error("无法获取应用程序实例!")
            
        # 调试主窗口
        if main_window:
            logger.info("\n主窗口调试:")
            ThemeDebugger.debug_widget(main_window, logger)
            
            # 查找样式冲突
            logger.info("\n查找样式冲突:")
            ThemeDebugger.find_style_conflicts(main_window, logger)
            
        logger.info("\n调试报告完成 - 请查看 theme_debug.log")
        
        return logger


# 全局调试器实例
theme_debugger = ThemeDebugger()