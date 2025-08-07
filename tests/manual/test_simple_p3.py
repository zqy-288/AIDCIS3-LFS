#!/usr/bin/env python3
"""
简化P3页面测试程序
测试固定布局的统一历史数据查看器
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import Qt

# 添加项目路径
sys.path.insert(0, '/Users/vsiyo/Desktop/AIDCIS3-LFS')

from src.pages.history_analytics_p3.simple_history_page import SimpleHistoryPage


class TestMainWindow(QMainWindow):
    """测试主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("简化P3页面测试 - 统一历史数据查看器")
        self.setGeometry(100, 100, 1400, 900)
        
        # 设置深色主题样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #3c3c3c;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #ffffff;
            }
            QComboBox {
                background-color: #4a4a4a;
                border: 1px solid #666666;
                border-radius: 3px;
                padding: 5px;
                color: #ffffff;
                min-height: 20px;
            }
            QComboBox:hover {
                background-color: #5a5a5a;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
            QLabel {
                color: #ffffff;
            }
            QTableWidget {
                background-color: #3c3c3c;
                alternate-background-color: #484848;
                color: #ffffff;
                border: 1px solid #555555;
                selection-background-color: #0078d4;
                gridline-color: #555555;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #555555;
            }
            QHeaderView::section {
                background-color: #505050;
                color: #ffffff;
                padding: 8px;
                border: 1px solid #666666;
                font-weight: bold;
            }
            QTextEdit {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
            }
            QListWidget {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                alternate-background-color: #484848;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #555555;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
            }
            QPushButton {
                background-color: #4a4a4a;
                color: #ffffff;
                border: 1px solid #666666;
                border-radius: 3px;
                padding: 8px 16px;
                font-weight: bold;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
            QPushButton:pressed {
                background-color: #3a3a3a;
            }
            QSplitter::handle {
                background-color: #555555;
                width: 3px;
                height: 3px;
            }
            QSplitter::handle:horizontal {
                width: 3px;
            }
            QSplitter::handle:vertical {
                height: 3px;
            }
        """)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建简化P3页面实例
        self.simple_p3_page = SimpleHistoryPage()
        layout.addWidget(self.simple_p3_page)
        
        print("✅ 简化测试窗口创建成功")
        print(f"📋 页面信息: {self.simple_p3_page.get_page_info()}")


def main():
    """主函数"""
    print("🚀 启动简化P3页面测试...")
    
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    window = TestMainWindow()
    window.show()
    
    print("✅ 简化测试窗口已显示")
    print("💡 测试说明:")
    print("   - 顶部有固定的控制面板，包含下拉框和状态标签")
    print("   - 管孔直径模式: 左侧数据表格，右侧统计信息")
    print("   - 缺陷标注模式: 左侧缺陷列表，右侧缺陷详情")
    print("   - 布局使用固定分割比例，应该更稳定")
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == '__main__':
    main()