#!/usr/bin/env python3
"""
历史数据功能激活测试脚本
让主目录中的历史数据相关功能"动起来"
"""

import sys
import os
import numpy as np
from datetime import datetime, timedelta

# 添加模块路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'modules'))
sys.path.insert(0, os.path.join(current_dir, 'aidcis2'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QTextEdit
from PySide6.QtCore import QTimer

def test_database_operations():
    """测试数据库操作"""
    print("🔧 测试数据库操作...")
    
    try:
        from modules.models import db_manager
        
        # 初始化数据库
        print("📊 初始化数据库...")
        db_manager.create_sample_data()
        
        # 添加测试数据
        print("📝 添加测试数据...")
        for i in range(20):
            depth = i * 2.0
            diameter = 25.0 + 0.1 * np.sin(depth * 0.1) + np.random.normal(0, 0.02)
            success = db_manager.add_measurement_data("H001", depth, diameter, f"操作员{i%3+1}")
            if success:
                print(f"  ✅ 添加测量数据: 深度={depth:.1f}mm, 直径={diameter:.3f}mm")
        
        # 查询数据
        print("🔍 查询历史数据...")
        measurements = db_manager.get_hole_measurements("H001")
        print(f"  📊 H001的测量数据: {len(measurements)}条")
        
        holes = db_manager.get_workpiece_holes("WP-2024-001")
        print(f"  🕳️ 工件孔数: {len(holes)}个")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库操作失败: {e}")
        return False

def test_realtime_bridge():
    """测试实时数据桥接"""
    print("🌉 测试实时数据桥接...")
    
    try:
        from aidcis2.data_management.realtime_bridge import RealtimeBridge
        
        # 创建实时桥接实例
        bridge = RealtimeBridge()
        
        # 测试历史数据加载
        print("📚 加载历史数据...")
        historical_data = bridge.load_historical_data("H00001", "WP-2024-001")
        print(f"  📊 加载历史数据: {len(historical_data)}条")
        
        # 显示部分数据
        if historical_data:
            print("  📋 数据样例:")
            for i, data in enumerate(historical_data[:3]):
                print(f"    {i+1}. 深度: {data.get('depth', 'N/A')}, 直径: {data.get('diameter', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 实时桥接测试失败: {e}")
        return False

def test_csv_data_loading():
    """测试CSV数据加载"""
    print("📄 测试CSV数据加载...")
    
    try:
        # 检查数据目录
        data_dirs = ["Data/H00001/CCIDM", "Data/H00002/CCIDM"]
        
        for data_dir in data_dirs:
            if os.path.exists(data_dir):
                print(f"  📁 找到数据目录: {data_dir}")
                csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
                print(f"    📄 CSV文件: {len(csv_files)}个")
                
                for csv_file in csv_files:
                    csv_path = os.path.join(data_dir, csv_file)
                    print(f"      📋 {csv_file}")
                    
                    # 尝试读取CSV文件的前几行
                    try:
                        import csv
                        with open(csv_path, 'r', encoding='utf-8') as f:
                            reader = csv.reader(f)
                            lines = list(reader)
                            print(f"        📊 数据行数: {len(lines)}")
                            if lines:
                                print(f"        📝 表头: {lines[0][:5]}...")  # 显示前5列
                    except Exception as e:
                        print(f"        ❌ 读取失败: {e}")
            else:
                print(f"  ❌ 数据目录不存在: {data_dir}")
        
        return True
        
    except Exception as e:
        print(f"❌ CSV数据加载测试失败: {e}")
        return False

def create_history_viewer_window():
    """创建历史数据查看器窗口"""
    print("🖥️ 创建历史数据查看器...")
    
    try:
        from modules.history_viewer import HistoryViewer
        
        # 创建历史数据查看器
        viewer = HistoryViewer()
        viewer.setWindowTitle("AIDCIS - 历史数据查看器")
        viewer.resize(1200, 800)
        viewer.show()
        
        print("✅ 历史数据查看器已启动")
        return viewer
        
    except Exception as e:
        print(f"❌ 创建历史数据查看器失败: {e}")
        return None

class HistoryDataActivator(QMainWindow):
    """历史数据功能激活器"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AIDCIS - 历史数据功能激活器")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 标题
        title = QLabel("🚀 AIDCIS 历史数据功能激活器")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # 日志显示
        self.log_display = QTextEdit()
        self.log_display.setStyleSheet("font-family: monospace; background-color: #f0f0f0;")
        layout.addWidget(self.log_display)
        
        # 按钮区域
        button_layout = QVBoxLayout()
        
        # 测试按钮
        self.test_db_btn = QPushButton("🔧 测试数据库操作")
        self.test_db_btn.clicked.connect(self.run_database_test)
        button_layout.addWidget(self.test_db_btn)
        
        self.test_bridge_btn = QPushButton("🌉 测试实时桥接")
        self.test_bridge_btn.clicked.connect(self.run_bridge_test)
        button_layout.addWidget(self.test_bridge_btn)
        
        self.test_csv_btn = QPushButton("📄 测试CSV数据")
        self.test_csv_btn.clicked.connect(self.run_csv_test)
        button_layout.addWidget(self.test_csv_btn)
        
        self.open_viewer_btn = QPushButton("🖥️ 打开历史数据查看器")
        self.open_viewer_btn.clicked.connect(self.open_history_viewer)
        button_layout.addWidget(self.open_viewer_btn)
        
        self.run_all_btn = QPushButton("🚀 运行所有测试")
        self.run_all_btn.clicked.connect(self.run_all_tests)
        button_layout.addWidget(self.run_all_btn)
        
        layout.addLayout(button_layout)
        
        # 历史查看器引用
        self.history_viewer = None
        
    def log(self, message):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_display.append(f"[{timestamp}] {message}")
        
    def run_database_test(self):
        """运行数据库测试"""
        self.log("开始数据库测试...")
        success = test_database_operations()
        if success:
            self.log("✅ 数据库测试完成")
        else:
            self.log("❌ 数据库测试失败")
            
    def run_bridge_test(self):
        """运行桥接测试"""
        self.log("开始实时桥接测试...")
        success = test_realtime_bridge()
        if success:
            self.log("✅ 实时桥接测试完成")
        else:
            self.log("❌ 实时桥接测试失败")
            
    def run_csv_test(self):
        """运行CSV测试"""
        self.log("开始CSV数据测试...")
        success = test_csv_data_loading()
        if success:
            self.log("✅ CSV数据测试完成")
        else:
            self.log("❌ CSV数据测试失败")
            
    def open_history_viewer(self):
        """打开历史数据查看器"""
        self.log("正在打开历史数据查看器...")
        self.history_viewer = create_history_viewer_window()
        if self.history_viewer:
            self.log("✅ 历史数据查看器已打开")
        else:
            self.log("❌ 历史数据查看器打开失败")
            
    def run_all_tests(self):
        """运行所有测试"""
        self.log("🚀 开始运行所有测试...")
        
        tests = [
            ("数据库操作", self.run_database_test),
            ("实时桥接", self.run_bridge_test),
            ("CSV数据", self.run_csv_test),
        ]
        
        for test_name, test_func in tests:
            self.log(f"正在运行: {test_name}")
            test_func()
            
        self.log("🎉 所有测试完成！")

def main():
    """主函数"""
    print("🚀 启动AIDCIS历史数据功能激活器...")
    
    app = QApplication(sys.argv)
    
    # 创建激活器窗口
    activator = HistoryDataActivator()
    activator.show()
    
    # 自动运行初始测试
    QTimer.singleShot(1000, activator.run_all_tests)
    
    return app.exec()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
