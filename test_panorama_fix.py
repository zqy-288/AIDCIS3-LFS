#!/usr/bin/env python3
"""
测试全景预览修复效果
"""

import sys
import time
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit
from PySide6.QtCore import QTimer

# 添加项目路径
sys.path.append('src')

from aidcis2.graphics.dynamic_sector_view import CompletePanoramaWidget
from aidcis2.models.hole_data import HoleStatus

class PanoramaFixTester(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("全景预览修复测试")
        self.setGeometry(100, 100, 800, 600)
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置测试界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 全景预览组件
        self.panorama = CompletePanoramaWidget()
        self.panorama.setFixedSize(400, 400)
        layout.addWidget(self.panorama)
        
        # 测试按钮
        self.btn_test = QPushButton("测试批量更新时间")
        self.btn_test.clicked.connect(self.test_update_timing)
        layout.addWidget(self.btn_test)
        
        self.btn_coverage = QPushButton("检查更新覆盖范围")
        self.btn_coverage.clicked.connect(self.check_coverage)
        layout.addWidget(self.btn_coverage)
        
        # 日志输出
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        self.log_widget.setMaximumHeight(200)
        layout.addWidget(self.log_widget)
        
    def test_update_timing(self):
        """测试批量更新时间"""
        self.log("开始测试批量更新时间...")
        
        # 模拟10个快速更新
        for i in range(10):
            hole_id = f"H{i+1:04d}"
            status = HoleStatus.QUALIFIED if i % 2 == 0 else HoleStatus.DEFECTIVE
            
            self.log(f"更新 {hole_id} -> {status.value}")
            self.panorama.update_hole_status(hole_id, status)
            
        # 检查定时器状态
        if hasattr(self.panorama, 'batch_update_timer'):
            is_active = self.panorama.batch_update_timer.isActive()
            interval = self.panorama.batch_update_interval
            self.log(f"\n批量更新定时器: {'激活' if is_active else '未激活'}")
            self.log(f"更新间隔: {interval}ms")
            
            if is_active:
                remaining = self.panorama.batch_update_timer.remainingTime()
                self.log(f"剩余时间: {remaining}ms")
                
        # 测试强制立即更新
        self.log("\n执行强制立即更新...")
        self.panorama.force_immediate_update()
        self.log("强制更新完成")
        
    def check_coverage(self):
        """检查更新覆盖范围"""
        self.log("\n检查更新覆盖范围...")
        
        if hasattr(self.panorama, 'debug_update_coverage'):
            self.panorama.debug_update_coverage()
        else:
            self.log("debug_update_coverage 方法不存在")
            
    def log(self, message):
        """输出日志"""
        self.log_widget.append(message)
        print(message)

def main():
    app = QApplication(sys.argv)
    window = PanoramaFixTester()
    window.show()
    
    # 显示修复说明
    print("\n全景预览修复内容:")
    print("1. 批量更新间隔从1000ms减少到100ms")
    print("2. 添加了force_immediate_update()方法")
    print("3. 改进了更新逻辑，优先使用update_status方法")
    print("4. 添加了更新后的强制重绘")
    print("5. 添加了debug_update_coverage()调试方法")
    print("\n请运行主程序测试实际效果")
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()