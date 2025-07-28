"""
主题切换器模块
提供运行时主题切换功能用于调试
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QPushButton, QLabel, 
                               QTextEdit, QGroupBox, QHBoxLayout, QCheckBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
import logging

class ThemeSwitcher(QDialog):
    """主题切换对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("主题调试工具")
        self.setGeometry(100, 100, 600, 800)
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("主题调试和切换工具")
        title.setAlignment(Qt.AlignCenter)
        font = title.font()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)
        
        # 主题切换按钮组
        theme_group = QGroupBox("主题切换")
        theme_layout = QVBoxLayout(theme_group)
        
        # 深色主题按钮（默认主题）
        dark_btn = QPushButton("应用深色主题（默认）")
        dark_btn.clicked.connect(self.apply_dark_theme)
        theme_layout.addWidget(dark_btn)
        
        # 浅色主题按钮（可选主题）
        light_btn = QPushButton("切换到浅色主题")
        light_btn.clicked.connect(self.apply_light_theme)
        theme_layout.addWidget(light_btn)
        
        # 强制深色主题按钮
        force_dark_btn = QPushButton("强制深色主题（清除所有内联样式）")
        force_dark_btn.clicked.connect(self.force_dark_theme)
        theme_layout.addWidget(force_dark_btn)
        
        # 恢复系统默认按钮
        default_btn = QPushButton("恢复系统默认样式")
        default_btn.clicked.connect(self.restore_default)
        theme_layout.addWidget(default_btn)
        
        layout.addWidget(theme_group)
        
        # 调试选项
        debug_group = QGroupBox("调试选项")
        debug_layout = QVBoxLayout(debug_group)
        
        self.remove_inline_cb = QCheckBox("移除所有内联样式")
        self.remove_inline_cb.setChecked(True)
        debug_layout.addWidget(self.remove_inline_cb)
        
        self.force_palette_cb = QCheckBox("强制使用调色板")
        self.force_palette_cb.setChecked(True)
        debug_layout.addWidget(self.force_palette_cb)
        
        self.debug_log_cb = QCheckBox("启用详细日志")
        self.debug_log_cb.setChecked(True)
        debug_layout.addWidget(self.debug_log_cb)
        
        layout.addWidget(debug_group)
        
        # 调试信息显示
        info_group = QGroupBox("调试信息")
        info_layout = QVBoxLayout(info_group)
        
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        info_layout.addWidget(self.info_text)
        
        layout.addWidget(info_group)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("刷新信息")
        refresh_btn.clicked.connect(self.refresh_info)
        button_layout.addWidget(refresh_btn)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # 初始化显示信息
        self.refresh_info()
        
    def apply_dark_theme(self):
        """应用深色主题（默认主题）"""
        try:
            from modules.theme_manager import theme_manager
            from PySide6.QtWidgets import QApplication
            
            app = QApplication.instance()
            if app:
                # 应用深色主题
                theme_manager.apply_dark_theme(app)
                
                # 如果选中，移除内联样式
                if self.remove_inline_cb.isChecked():
                    self.remove_all_inline_styles(self.parent())
                    
                # 如果选中，强制调色板
                if self.force_palette_cb.isChecked():
                    self.force_dark_palette(app)
                    
                self.log_info("深色主题已应用（默认主题）")
                self.refresh_info()
            else:
                self.log_info("错误：无法获取应用程序实例")
                
        except Exception as e:
            self.log_info(f"应用深色主题失败: {e}")
    
    def apply_light_theme(self):
        """应用浅色主题（可选主题）"""
        try:
            from modules.theme_manager import theme_manager
            from PySide6.QtWidgets import QApplication
            
            app = QApplication.instance()
            if app:
                # 应用浅色主题
                theme_manager.apply_light_theme(app)
                
                # 如果选中，移除内联样式
                if self.remove_inline_cb.isChecked():
                    self.remove_all_inline_styles(self.parent())
                    
                self.log_info("浅色主题已应用（可选主题）")
                self.refresh_info()
            else:
                self.log_info("错误：无法获取应用程序实例")
                
        except Exception as e:
            self.log_info(f"应用浅色主题失败: {e}")
            
    def force_dark_theme(self):
        """强制深色主题"""
        try:
            from PySide6.QtWidgets import QApplication, QWidget
            
            app = QApplication.instance()
            if app:
                # 移除所有内联样式
                self.log_info("移除所有内联样式...")
                count = self.remove_all_inline_styles(app)
                self.log_info(f"已移除 {count} 个内联样式")
                
                # 重新应用主题
                self.apply_dark_theme()
                
                # 强制刷新
                for widget in app.allWidgets():
                    widget.style().unpolish(widget)
                    widget.style().polish(widget)
                    widget.update()
                    
                self.log_info("强制深色主题完成")
                
        except Exception as e:
            self.log_info(f"强制主题失败: {e}")
            
    def remove_all_inline_styles(self, widget, count=0):
        """递归移除所有内联样式"""
        if widget and hasattr(widget, 'styleSheet'):
            if widget.styleSheet():
                widget.setStyleSheet("")
                count += 1
                
        # 递归处理子widget
        if hasattr(widget, 'findChildren'):
            from PySide6.QtWidgets import QWidget
            for child in widget.findChildren(QWidget):
                count = self.remove_all_inline_styles(child, count)
                
        return count
        
    def force_dark_palette(self, app):
        """强制应用深色调色板"""
        from modules.theme_manager import theme_manager
        
        palette = QPalette()
        colors = theme_manager.COLORS
        
        # 设置所有颜色角色
        palette.setColor(QPalette.Window, QColor(colors['background_primary']))
        palette.setColor(QPalette.WindowText, QColor(colors['text_primary']))
        palette.setColor(QPalette.Base, QColor(colors['background_secondary']))
        palette.setColor(QPalette.AlternateBase, QColor(colors['background_tertiary']))
        palette.setColor(QPalette.ToolTipBase, QColor(colors['background_tertiary']))
        palette.setColor(QPalette.ToolTipText, QColor(colors['text_primary']))
        palette.setColor(QPalette.Text, QColor(colors['text_primary']))
        palette.setColor(QPalette.BrightText, QColor(colors['text_secondary']))
        palette.setColor(QPalette.Button, QColor(colors['background_tertiary']))
        palette.setColor(QPalette.ButtonText, QColor(colors['text_primary']))
        palette.setColor(QPalette.Link, QColor(colors['accent_primary']))
        palette.setColor(QPalette.Highlight, QColor(colors['accent_primary']))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        
        app.setPalette(palette)
        
        # 对所有widget应用
        for widget in app.allWidgets():
            widget.setPalette(palette)
            
    def restore_default(self):
        """恢复默认主题"""
        try:
            from PySide6.QtWidgets import QApplication
            
            app = QApplication.instance()
            if app:
                app.setStyleSheet("")
                app.setPalette(app.style().standardPalette())
                self.log_info("已恢复默认主题")
                self.refresh_info()
                
        except Exception as e:
            self.log_info(f"恢复默认失败: {e}")
            
    def refresh_info(self):
        """刷新调试信息"""
        info = []
        
        try:
            from PySide6.QtWidgets import QApplication
            from modules.theme_manager import theme_manager
            
            app = QApplication.instance()
            if app:
                # 应用程序信息
                info.append("=== 应用程序信息 ===")
                stylesheet = app.styleSheet()
                info.append(f"样式表长度: {len(stylesheet)} 字符")
                
                if stylesheet:
                    # 检查关键颜色
                    colors_found = []
                    for color in ['#2C313C', '#313642', '#007ACC']:
                        if color in stylesheet:
                            colors_found.append(color)
                    info.append(f"找到的主题颜色: {', '.join(colors_found)}")
                    
                # 调色板信息
                palette = app.palette()
                info.append(f"\n调色板颜色:")
                info.append(f"  Window: {palette.color(QPalette.Window).name()}")
                info.append(f"  Base: {palette.color(QPalette.Base).name()}")
                info.append(f"  Text: {palette.color(QPalette.Text).name()}")
                
                # 主窗口信息
                if self.parent():
                    info.append(f"\n=== 主窗口信息 ===")
                    info.append(f"类名: {self.parent().__class__.__name__}")
                    parent_style = self.parent().styleSheet()
                    info.append(f"内联样式: {'有' if parent_style else '无'}")
                    
                # Widget统计
                all_widgets = app.allWidgets()
                widgets_with_style = sum(1 for w in all_widgets if w.styleSheet())
                info.append(f"\n=== Widget统计 ===")
                info.append(f"总数: {len(all_widgets)}")
                info.append(f"有内联样式的: {widgets_with_style}")
                
        except Exception as e:
            info.append(f"获取信息失败: {e}")
            
        self.info_text.setPlainText("\n".join(info))
        
    def log_info(self, message):
        """记录信息"""
        current = self.info_text.toPlainText()
        self.info_text.setPlainText(current + f"\n{message}")
        # 滚动到底部
        scrollbar = self.info_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


def show_theme_switcher(parent=None):
    """显示主题切换器"""
    dialog = ThemeSwitcher(parent)
    dialog.exec()