#!/usr/bin/env python3
"""
测试实时监控界面修改
验证以下修改：
1. 当前孔位显示改为文本标签
2. 移除标准直径输入框，固定为17.6mm
3. 优化界面布局，明确的边框和标题
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / 'modules'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PySide6.QtCore import QTimer
from modules.realtime_chart import RealtimeChart


class TestMainWindow(QMainWindow):
    """测试主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("实时监控界面修改测试")
        self.setGeometry(100, 100, 1400, 900)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 添加测试按钮
        button_layout = QHBoxLayout()
        
        self.set_h00001_btn = QPushButton("设置孔位 H00001")
        self.set_h00001_btn.clicked.connect(lambda: self.set_hole("H00001"))
        button_layout.addWidget(self.set_h00001_btn)
        
        self.set_h00002_btn = QPushButton("设置孔位 H00002")
        self.set_h00002_btn.clicked.connect(lambda: self.set_hole("H00002"))
        button_layout.addWidget(self.set_h00002_btn)
        
        self.clear_btn = QPushButton("清除孔位")
        self.clear_btn.clicked.connect(lambda: self.set_hole(None))
        button_layout.addWidget(self.clear_btn)
        
        self.start_simulation_btn = QPushButton("开始模拟数据")
        self.start_simulation_btn.clicked.connect(self.start_simulation)
        button_layout.addWidget(self.start_simulation_btn)
        
        self.stop_simulation_btn = QPushButton("停止模拟数据")
        self.stop_simulation_btn.clicked.connect(self.stop_simulation)
        button_layout.addWidget(self.stop_simulation_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 创建实时监控组件
        self.realtime_chart = RealtimeChart()
        layout.addWidget(self.realtime_chart)
        
        # 模拟数据定时器
        self.simulation_timer = QTimer()
        self.simulation_timer.timeout.connect(self.generate_simulation_data)
        self.simulation_depth = 0
        self.simulation_running = False
        
        print("✅ 测试窗口初始化完成")
        print("📋 测试功能：")
        print("   1. 点击'设置孔位'按钮测试孔位显示")
        print("   2. 点击'开始模拟数据'测试误差线显示")
        print("   3. 观察界面布局和边框效果")
        
    def set_hole(self, hole_id):
        """设置当前孔位"""
        if hole_id:
            self.realtime_chart.set_current_hole(hole_id)
            print(f"🎯 测试设置孔位: {hole_id}")
        else:
            self.realtime_chart.clear_data()
            print("🧹 测试清除孔位")
    
    def start_simulation(self):
        """开始模拟数据"""
        if not self.simulation_running:
            self.simulation_running = True
            self.simulation_depth = 0
            self.simulation_timer.start(100)  # 每100ms生成一个数据点
            print("🚀 开始模拟数据生成")
    
    def stop_simulation(self):
        """停止模拟数据"""
        if self.simulation_running:
            self.simulation_running = False
            self.simulation_timer.stop()
            print("⏹️ 停止模拟数据生成")
    
    def generate_simulation_data(self):
        """生成模拟数据"""
        import random
        import math
        
        # 生成深度数据（递增）
        self.simulation_depth += random.uniform(5, 15)
        
        # 生成直径数据（围绕17.6mm波动，偶尔超出公差）
        base_diameter = 17.6
        
        # 90%的数据在公差范围内，10%超出公差
        if random.random() < 0.9:
            # 正常数据：在公差范围内
            diameter = base_diameter + random.uniform(-0.05, 0.05)
        else:
            # 异常数据：超出公差范围
            if random.random() < 0.5:
                diameter = base_diameter + random.uniform(0.08, 0.15)  # 超上限
            else:
                diameter = base_diameter - random.uniform(0.10, 0.20)  # 超下限
        
        # 添加一些周期性变化
        cycle_offset = 0.02 * math.sin(self.simulation_depth * 0.01)
        diameter += cycle_offset
        
        # 更新数据
        self.realtime_chart.update_data(self.simulation_depth, diameter)
        
        # 模拟其他状态更新
        self.realtime_chart.depth_label.setText(f"探头深度: {self.simulation_depth:.1f} mm")
        self.realtime_chart.comm_status_label.setText("通信状态: 连接正常")
        self.realtime_chart.comm_status_label.setStyleSheet("color: green;")
        
        # 限制模拟深度
        if self.simulation_depth > 1000:
            self.stop_simulation()


def main():
    """主函数"""
    print("=" * 60)
    print("实时监控界面修改测试")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    window = TestMainWindow()
    window.show()
    
    print("\n🎯 测试要点：")
    print("1. 检查'当前孔位'是否显示为文本标签而非下拉框")
    print("2. 确认显示'标准直径：17.6mm'")
    print("3. 验证误差线是否基于17.6mm绘制")
    print("4. 观察面板A和面板B的边框和标题样式")
    print("5. 测试异常数据检测功能")
    print("6. 检查字体大小是否增大，显示更清晰美观")
    
    return app.exec()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
