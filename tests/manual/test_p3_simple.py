#!/usr/bin/env python3
"""
P3页面简单测试程序
用于验证统一历史数据查看器的基本功能
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import Qt

# 添加项目路径
sys.path.insert(0, '/Users/vsiyo/Desktop/AIDCIS3-LFS')

from src.pages.history_analytics_p3.history_analytics_page import HistoryAnalyticsPage


class TestMainWindow(QMainWindow):
    """测试主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("P3页面测试 - 统一历史数据查看器")
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
            }
            QComboBox:hover {
                background-color: #5a5a5a;
            }
            QComboBox::drop-down {
                border: none;
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
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #505050;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #666666;
            }
            QTextEdit {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
            }
        """)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建P3页面实例
        self.p3_page = HistoryAnalyticsPage()
        layout.addWidget(self.p3_page)
        
        print("✅ 测试窗口创建成功")
        print(f"📋 P3页面信息: {self.p3_page.get_page_info()}")


def main():
    """主函数"""
    print("🚀 启动P3页面简单测试...")
    
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    window = TestMainWindow()
    window.show()
    
    print("✅ 测试窗口已显示")
    print("💡 测试说明:")
    print("   - 顶部下拉框可以切换'管孔直径'和'缺陷标注'模式")
    print("   - 管孔直径模式: 显示历史数据表格和统计信息")
    print("   - 缺陷标注模式: 显示缺陷列表和编辑面板")
    print("   - 右上角状态标签会显示当前模式")
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == '__main__':
    main()