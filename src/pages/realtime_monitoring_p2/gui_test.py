#!/usr/bin/env python3
"""
P2页面GUI测试程序
用于测试和展示实时监控页面功能
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit
from PySide6.QtCore import Qt
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class TestMainWindow(QMainWindow):
    """测试主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("P2实时监控页面测试")
        self.setGeometry(100, 100, 1400, 900)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        
        # 创建日志显示区域
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setMaximumHeight(150)
        
        # 添加自定义日志处理器
        self.setup_logging()
        
        try:
            # 创建P2页面
            from src.pages.realtime_monitoring_p2.realtime_monitoring_page import RealtimeMonitoringPage
            self.p2_page = RealtimeMonitoringPage()
            
            # 连接信号用于日志显示
            self.p2_page.monitoring_started.connect(lambda: self.log("监控已启动"))
            self.p2_page.monitoring_stopped.connect(lambda: self.log("监控已停止"))
            self.p2_page.hole_selected.connect(lambda h: self.log(f"选择孔位: {h}"))
            self.p2_page.data_exported.connect(lambda p: self.log(f"数据导出: {p}"))
            
            # 添加到布局
            layout.addWidget(self.p2_page)
            layout.addWidget(self.log_display)
            
            self.log("✅ P2页面加载成功")
            self.log("提示：点击'开始监控'按钮启动实时数据生成")
            
        except Exception as e:
            self.log(f"❌ P2页面加载失败: {e}")
            import traceback
            traceback.print_exc()
            
            # 显示错误信息
            error_btn = QPushButton("页面加载失败")
            layout.addWidget(error_btn)
            layout.addWidget(self.log_display)
            
    def setup_logging(self):
        """设置日志处理器"""
        class GuiLogHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget
                
            def emit(self, record):
                msg = self.format(record)
                self.text_widget.append(msg)
                
        # 添加GUI日志处理器
        gui_handler = GuiLogHandler(self.log_display)
        gui_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        logging.getLogger().addHandler(gui_handler)
        
    def log(self, message):
        """添加日志信息"""
        self.log_display.append(f"{message}")
        
    def closeEvent(self, event):
        """关闭事件处理"""
        if hasattr(self, 'p2_page'):
            self.p2_page.cleanup()
        event.accept()


def print_usage():
    """打印使用说明"""
    print("\n" + "="*60)
    print("P2实时监控页面功能说明")
    print("="*60)
    print("\n功能特性：")
    print("1. 实时直径监控")
    print("   - 点击'开始监控'按钮启动数据采集")
    print("   - 自动生成模拟数据并显示在图表中")
    print("   - 红色点表示超出容差的异常数据")
    print("\n2. 异常检测")
    print("   - 自动检测超出容差的数据")
    print("   - 在异常列表中显示详细信息")
    print("   - 支持导出异常数据")
    print("\n3. 数据管理")
    print("   - '加载历史数据'：加载CSV文件")
    print("   - '导出当前数据'：保存监控数据")
    print("   - 自动保存停止监控时的数据")
    print("\n4. 自动化功能")
    print("   - '启动自动化'：监控文件夹变化")
    print("   - 自动导入新的CSV文件")
    print("\n5. 内窥镜视图")
    print("   - 模拟内窥镜图像显示")
    print("   - 支持亮度/对比度调节")
    print("   - 图像捕获功能")
    print("="*60)


def main():
    """主函数"""
    print_usage()
    
    # 创建应用
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    # 创建主窗口
    window = TestMainWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()