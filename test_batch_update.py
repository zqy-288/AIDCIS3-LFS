#!/usr/bin/env python3
"""测试全景预览批量更新功能"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import QTimer, Qt
from aidcis2.integration.legacy_dxf_loader import LegacyDXFLoader
from aidcis2.graphics.dynamic_sector_view import CompletePanoramaWidget
from aidcis2.models.hole_data import HoleStatus
import random

class BatchUpdateTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("全景预览批量更新测试")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中心组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 信息标签
        self.info_label = QLabel("正在初始化...")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("padding: 10px; background-color: #f0f0f0; font-size: 14px;")
        layout.addWidget(self.info_label)
        
        # 创建全景预览组件
        self.panorama = CompletePanoramaWidget()
        layout.addWidget(self.panorama)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        
        # 测试按钮
        self.test_single_btn = QPushButton("测试单个更新")
        self.test_single_btn.clicked.connect(self.test_single_update)
        self.test_single_btn.setEnabled(False)
        button_layout.addWidget(self.test_single_btn)
        
        self.test_batch_btn = QPushButton("测试批量更新")
        self.test_batch_btn.clicked.connect(self.test_batch_update)
        self.test_batch_btn.setEnabled(False)
        button_layout.addWidget(self.test_batch_btn)
        
        self.test_stress_btn = QPushButton("压力测试")
        self.test_stress_btn.clicked.connect(self.test_stress_update)
        self.test_stress_btn.setEnabled(False)
        button_layout.addWidget(self.test_stress_btn)
        
        # 设置批量更新间隔
        self.interval_btn = QPushButton("设置间隔(500ms)")
        self.interval_btn.clicked.connect(self.toggle_interval)
        self.interval_btn.setEnabled(False)
        button_layout.addWidget(self.interval_btn)
        
        layout.addLayout(button_layout)
        
        # 测试数据
        self.hole_collection = None
        self.test_holes = []
        self.current_interval = 1500
        
    def load_dxf(self):
        """加载DXF文件"""
        self.info_label.setText("正在加载DXF文件...")
        
        loader = LegacyDXFLoader()
        dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-1/AIDCIS3-LFS/assets/dxf/DXF Graph/东重管板.dxf"
        self.hole_collection = loader.load_dxf_file(dxf_path)
        
        if self.hole_collection:
            self.info_label.setText(f"✅ 加载了 {len(self.hole_collection)} 个孔位")
            self.panorama.load_complete_view(self.hole_collection)
            
            # 准备测试数据
            hole_ids = list(self.hole_collection.holes.keys())
            self.test_holes = hole_ids[:100]  # 使用前100个孔位进行测试
            
            # 启用测试按钮
            self.test_single_btn.setEnabled(True)
            self.test_batch_btn.setEnabled(True)
            self.test_stress_btn.setEnabled(True)
            self.interval_btn.setEnabled(True)
            
            print(f"✅ 测试准备完成，将使用 {len(self.test_holes)} 个孔位进行测试")
    
    def test_single_update(self):
        """测试单个状态更新"""
        if not self.test_holes:
            return
        
        print("\n" + "="*50)
        print("单个更新测试开始")
        print("="*50)
        
        hole_id = random.choice(self.test_holes)
        status = random.choice([HoleStatus.QUALIFIED, HoleStatus.DEFECTIVE, HoleStatus.PROCESSING])
        
        print(f"更新孔位: {hole_id} -> {status.value}")
        self.panorama.update_hole_status(hole_id, status)
        
        self.info_label.setText(f"单个更新: {hole_id} -> {status.value}")
    
    def test_batch_update(self):
        """测试批量更新"""
        if not self.test_holes:
            return
        
        print("\n" + "="*50)
        print("批量更新测试开始")
        print("="*50)
        
        # 准备批量更新数据
        batch_size = 20
        batch_holes = random.sample(self.test_holes, min(batch_size, len(self.test_holes)))
        status_updates = {}
        
        for hole_id in batch_holes:
            status = random.choice([HoleStatus.QUALIFIED, HoleStatus.DEFECTIVE, HoleStatus.BLIND])
            status_updates[hole_id] = status
        
        print(f"批量更新 {len(status_updates)} 个孔位")
        self.panorama.batch_update_hole_status(status_updates)
        
        self.info_label.setText(f"批量更新: {len(status_updates)} 个孔位")
    
    def test_stress_update(self):
        """压力测试：模拟高频更新"""
        if not self.test_holes:
            return
        
        print("\n" + "="*50)
        print("压力测试开始 - 模拟高频更新")
        print("="*50)
        
        self.info_label.setText("压力测试进行中...")
        
        # 快速连续更新
        for i in range(50):
            hole_id = random.choice(self.test_holes)
            status = random.choice([HoleStatus.QUALIFIED, HoleStatus.DEFECTIVE, HoleStatus.PROCESSING])
            self.panorama.update_hole_status(hole_id, status)
        
        print("✅ 压力测试完成 - 50个快速更新")
        QTimer.singleShot(2000, lambda: self.info_label.setText("压力测试完成"))
    
    def toggle_interval(self):
        """切换批量更新间隔"""
        if self.current_interval == 1500:
            self.current_interval = 500
            self.interval_btn.setText("设置间隔(2000ms)")
        elif self.current_interval == 500:
            self.current_interval = 2000
            self.interval_btn.setText("设置间隔(1500ms)")
        else:
            self.current_interval = 1500
            self.interval_btn.setText("设置间隔(500ms)")
        
        self.panorama.set_batch_update_interval(self.current_interval)
        self.info_label.setText(f"批量更新间隔设置为: {self.current_interval}ms")

def main():
    app = QApplication(sys.argv)
    
    window = BatchUpdateTestWindow()
    window.show()
    
    # 延迟加载DXF
    QTimer.singleShot(500, window.load_dxf)
    
    print("\n" + "="*60)
    print("全景预览批量更新测试")
    print("="*60)
    print("功能说明:")
    print("• 单个更新: 测试延迟批量更新机制")
    print("• 批量更新: 测试直接批量更新")
    print("• 压力测试: 模拟高频更新场景")
    print("• 设置间隔: 调整批量更新的时间间隔")
    print("="*60 + "\n")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()