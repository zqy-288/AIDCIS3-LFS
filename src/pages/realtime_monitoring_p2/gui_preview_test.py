#!/usr/bin/env python3
"""
P2页面GUI预览测试
显示真实的界面效果，包含模拟数据
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class PreviewMainWindow(QMainWindow):
    """预览主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("P2实时监控页面预览测试 - 包含模拟数据")
        self.setGeometry(100, 100, 1400, 900)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 添加说明标签
        info_label = QLabel("🔍 P2页面UI预览 - 将自动填充模拟数据展示界面效果")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setFont(QFont("Arial", 12, QFont.Bold))
        info_label.setStyleSheet("color: blue; padding: 10px;")
        layout.addWidget(info_label)
        
        try:
            # 创建P2页面
            from src.pages.realtime_monitoring_p2.realtime_monitoring_page import RealtimeMonitoringPage
            self.p2_page = RealtimeMonitoringPage()
            layout.addWidget(self.p2_page)
            
            # 设置定时器来模拟数据
            self.setup_simulation()
            
            print("✅ P2页面创建成功")
            print("📊 即将开始模拟数据生成...")
            
        except Exception as e:
            error_label = QLabel(f"❌ 页面加载失败: {e}")
            error_label.setStyleSheet("color: red; padding: 20px;")
            layout.addWidget(error_label)
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            
    def setup_simulation(self):
        """设置模拟数据"""
        # 自动开始监控
        QTimer.singleShot(1000, self.start_monitoring)
        
        # 定时添加异常数据用于展示
        self.anomaly_timer = QTimer()
        self.anomaly_timer.timeout.connect(self.add_sample_anomaly)
        self.anomaly_timer.start(3000)  # 每3秒添加一个异常
        
        self.anomaly_count = 0
        
    def start_monitoring(self):
        """开始监控"""
        if hasattr(self.p2_page, 'status_panel'):
            # 模拟点击开始监控按钮
            self.p2_page.status_panel.monitor_btn.click()
            print("🔄 自动开始监控")
            
    def add_sample_anomaly(self):
        """添加示例异常数据"""
        if self.anomaly_count < 5:  # 只添加5个示例
            import random
            from datetime import datetime
            
            # 生成模拟异常数据
            anomaly_data = {
                'diameter': 376.0 + random.uniform(-0.8, 0.8),
                'deviation': random.uniform(0.1, 0.5),
                'probe_depth': random.uniform(50, 200),
                'time': datetime.now().strftime('%H:%M:%S'),
                'type': '超上限' if random.random() > 0.5 else '超下限'
            }
            
            # 添加到异常面板
            if hasattr(self.p2_page, 'anomaly_panel'):
                self.p2_page.anomaly_panel.add_anomaly(anomaly_data)
                print(f"➕ 添加异常数据 #{self.anomaly_count + 1}: 直径={anomaly_data['diameter']:.3f}mm")
                
            self.anomaly_count += 1
        else:
            # 停止添加异常
            self.anomaly_timer.stop()
            print("✅ 异常数据展示完成")
            
    def closeEvent(self, event):
        """关闭事件处理"""
        if hasattr(self, 'p2_page'):
            self.p2_page.cleanup()
        event.accept()


def print_preview_info():
    """打印预览信息"""
    print("\n" + "="*70)
    print("P2页面GUI预览测试")
    print("="*70)
    print("\n📋 预览内容:")
    print("1. ✅ 紧凑型状态面板 - 水平布局，高度50px")
    print("2. ✅ 图表显示区域 - 占75%垂直空间")
    print("3. ✅ 紧凑型异常面板 - 280px宽度，包含示例数据")
    print("4. ✅ 内窥镜控制面板 - 水平布局，高度80px")
    print("5. ✅ 内窥镜视图区域 - 占25%垂直空间")
    
    print("\n🔄 自动操作:")
    print("- 1秒后自动开始监控")
    print("- 每3秒添加一个示例异常数据")
    print("- 总共添加5个异常示例用于展示")
    
    print("\n💡 观察要点:")
    print("- 状态面板是否足够紧凑")
    print("- 图表区域是否得到充分利用")
    print("- 异常面板是否显示正常（不再空白）")
    print("- 内窥镜控制是否在一行内显示")
    print("- 整体布局是否合理美观")
    
    print("\n⚠️  如果发现任何布局问题，请截图反馈！")
    print("="*70 + "\n")


def main():
    """主函数"""
    print_preview_info()
    
    # 创建应用
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # 创建预览窗口
    window = PreviewMainWindow()
    window.show()
    
    print("🚀 GUI预览窗口已启动")
    print("💡 窗口将显示包含模拟数据的P2页面")
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()