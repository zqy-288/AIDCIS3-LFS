#!/usr/bin/env python3
"""
强力深色主题应用工具
彻底移除所有内联样式并强制应用深色主题
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt, QTimer

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'modules'))

def force_remove_all_styles(widget, removed_count=0):
    """暴力移除所有内联样式"""
    if widget and hasattr(widget, 'setStyleSheet'):
        try:
            if widget.styleSheet():
                print(f"🗑️  移除样式: {widget.__class__.__name__} - {widget.styleSheet()[:50]}...")
                widget.setStyleSheet("")
                removed_count += 1
        except Exception as e:
            print(f"⚠️  移除样式失败: {e}")
    
    # 递归处理所有子组件
    if hasattr(widget, 'findChildren'):
        for child in widget.findChildren(QWidget):
            removed_count = force_remove_all_styles(child, removed_count)
    
    return removed_count

def apply_nuclear_dark_theme(app):
    """核心级别的深色主题应用"""
    try:
        from modules.theme_manager import theme_manager
        colors = theme_manager.COLORS
        
        print("🎨 应用核心深色主题...")
        
        # 1. 创建深色调色板
        palette = QPalette()
        
        # 设置所有可能的颜色角色
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
        
        # 2. 应用到应用程序
        app.setPalette(palette)
        
        # 3. 设置全局样式表 - 使用!important强制覆盖
        global_style = f"""
        QMainWindow, QWidget {{
            background-color: {colors['background_primary']} !important;
            color: {colors['text_primary']} !important;
        }}
        
        QLabel {{
            background-color: transparent !important;
            color: {colors['text_primary']} !important;
        }}
        
        QPushButton {{
            background-color: {colors['background_tertiary']} !important;
            color: {colors['text_primary']} !important;
            border: 1px solid {colors['border_normal']} !important;
            padding: 5px !important;
        }}
        
        QPushButton:hover {{
            background-color: {colors['hover']} !important;
        }}
        
        QTabWidget::pane {{
            background-color: {colors['background_secondary']} !important;
            border: 1px solid {colors['border_normal']} !important;
        }}
        
        QTabBar::tab {{
            background-color: {colors['background_tertiary']} !important;
            color: {colors['text_primary']} !important;
            padding: 8px !important;
            margin: 2px !important;
        }}
        
        QTabBar::tab:selected {{
            background-color: {colors['accent_primary']} !important;
            color: white !important;
        }}
        
        QMenuBar {{
            background-color: {colors['background_secondary']} !important;
            color: {colors['text_primary']} !important;
        }}
        
        QMenuBar::item:selected {{
            background-color: {colors['accent_primary']} !important;
        }}
        
        QStatusBar {{
            background-color: {colors['status_bar']} !important;
            color: {colors['text_primary']} !important;
        }}
        
        QGroupBox {{
            background-color: {colors['background_secondary']} !important;
            color: {colors['text_primary']} !important;
            border: 1px solid {colors['border_normal']} !important;
            padding-top: 10px !important;
        }}
        
        QGroupBox::title {{
            color: {colors['text_secondary']} !important;
        }}
        
        QLineEdit, QTextEdit, QComboBox {{
            background-color: {colors['background_secondary']} !important;
            color: {colors['text_primary']} !important;
            border: 1px solid {colors['border_normal']} !important;
            padding: 5px !important;
        }}
        
        QTableWidget {{
            background-color: {colors['background_secondary']} !important;
            color: {colors['text_primary']} !important;
            gridline-color: {colors['border_normal']} !important;
        }}
        
        QHeaderView::section {{
            background-color: {colors['background_tertiary']} !important;
            color: {colors['text_primary']} !important;
            border: 1px solid {colors['border_normal']} !important;
        }}
        
        QListWidget {{
            background-color: {colors['background_secondary']} !important;
            color: {colors['text_primary']} !important;
            border: 1px solid {colors['border_normal']} !important;
        }}
        
        QScrollBar:vertical {{
            background-color: {colors['background_tertiary']} !important;
            width: 12px !important;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {colors['accent_primary']} !important;
            border-radius: 6px !important;
        }}
        """
        
        app.setStyleSheet(global_style)
        print("✅ 全局深色样式表已应用")
        
        return True
        
    except Exception as e:
        print(f"❌ 深色主题应用失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def continuous_force_theme(app, main_window):
    """持续强制应用深色主题"""
    def force_theme():
        try:
            print("🔄 持续强制深色主题...")
            
            # 1. 移除所有内联样式
            count = force_remove_all_styles(main_window)
            if count > 0:
                print(f"🗑️  移除了 {count} 个内联样式")
            
            # 2. 重新应用深色主题
            apply_nuclear_dark_theme(app)
            
            # 3. 强制刷新所有组件
            for widget in app.allWidgets():
                if widget:
                    try:
                        widget.style().unpolish(widget)
                        widget.style().polish(widget)
                        if hasattr(widget, 'update'):
                            try:
                                widget.update()
                            except:
                                pass
                    except:
                        pass
            
            print("✅ 强制主题应用完成")
            
        except Exception as e:
            print(f"❌ 强制主题失败: {e}")
    
    # 立即执行一次
    force_theme()
    
    # 每隔1秒执行一次，共执行5次
    timer = QTimer()
    timer.timeout.connect(force_theme)
    timer.start(1000)
    
    # 5秒后停止
    QTimer.singleShot(5000, timer.stop)

if __name__ == "__main__":
    print("🚀 启动强力深色主题应用工具...")
    
    app = QApplication(sys.argv)
    
    # 立即应用深色主题
    apply_nuclear_dark_theme(app)
    
    # 导入主窗口
    from main_window import MainWindow
    
    # 创建主窗口
    main_window = MainWindow()
    
    # 强制移除所有内联样式
    print("🗑️  强制移除所有内联样式...")
    count = force_remove_all_styles(main_window)
    print(f"✅ 移除了 {count} 个内联样式")
    
    # 再次应用深色主题
    apply_nuclear_dark_theme(app)
    
    # 显示主窗口
    main_window.show()
    
    # 启动持续强制主题
    continuous_force_theme(app, main_window)
    
    print("🎨 深色主题强制应用完成！应用程序应该显示为深色主题。")
    
    sys.exit(app.exec())