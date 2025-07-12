#!/usr/bin/env python3
"""测试全景预览与主视图同步"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import QTimer, Qt
from aidcis2.integration.legacy_dxf_loader import LegacyDXFLoader
from aidcis2.graphics.dynamic_sector_view import CompletePanoramaWidget, DynamicSectorDisplayWidget
from aidcis2.graphics.sector_manager import SectorQuadrant
from aidcis2.models.hole_data import HoleStatus
import random

class SyncTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("全景预览同步测试")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中心组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 信息标签
        self.info_label = QLabel("正在初始化...")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("padding: 10px; background-color: #e3f2fd; font-size: 14px;")
        layout.addWidget(self.info_label)
        
        # 创建主要视图区域
        views_layout = QHBoxLayout()
        
        # 左侧：全景预览
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.addWidget(QLabel("全景预览 (左侧)"))
        
        self.panorama = CompletePanoramaWidget()
        self.panorama.setFixedSize(350, 350)
        left_layout.addWidget(self.panorama)
        views_layout.addWidget(left_container)
        
        # 右侧：动态扇形显示
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.addWidget(QLabel("动态扇形显示 (右侧)"))
        
        self.dynamic_display = DynamicSectorDisplayWidget()
        self.dynamic_display.setMinimumSize(400, 400)
        right_layout.addWidget(self.dynamic_display)
        views_layout.addWidget(right_container)
        
        layout.addLayout(views_layout)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        
        self.load_btn = QPushButton("加载数据")
        self.load_btn.clicked.connect(self.load_dxf)
        button_layout.addWidget(self.load_btn)
        
        self.test_sync_btn = QPushButton("测试同步")
        self.test_sync_btn.clicked.connect(self.test_sync)
        self.test_sync_btn.setEnabled(False)
        button_layout.addWidget(self.test_sync_btn)
        
        self.auto_test_btn = QPushButton("自动测试")
        self.auto_test_btn.clicked.connect(self.start_auto_test)
        self.auto_test_btn.setEnabled(False)
        button_layout.addWidget(self.auto_test_btn)
        
        layout.addLayout(button_layout)
        
        # 测试数据
        self.hole_collection = None
        self.test_holes = []
        self.auto_test_timer = QTimer()
        self.auto_test_timer.timeout.connect(self.auto_update_hole)
        self.auto_test_count = 0
        
    def load_dxf(self):
        """加载DXF文件"""
        self.info_label.setText("正在加载DXF文件...")
        
        loader = LegacyDXFLoader()
        dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-1/AIDCIS3-LFS/assets/dxf/DXF Graph/东重管板.dxf"
        self.hole_collection = loader.load_dxf_file(dxf_path)
        
        if self.hole_collection:
            self.info_label.setText(f"✅ 加载了 {len(self.hole_collection)} 个孔位")
            
            # 加载到两个视图
            self.panorama.load_complete_view(self.hole_collection)
            self.dynamic_display.set_hole_collection(self.hole_collection)
            
            # 准备测试数据
            hole_ids = list(self.hole_collection.holes.keys())
            self.test_holes = hole_ids[:200]  # 使用前200个孔位进行测试
            
            # 启用测试按钮
            self.test_sync_btn.setEnabled(True)
            self.auto_test_btn.setEnabled(True)
            self.load_btn.setEnabled(False)
            
            print(f"✅ 数据加载完成，将使用 {len(self.test_holes)} 个孔位进行同步测试")
    
    def test_sync(self):
        """测试同步更新"""
        if not self.test_holes:
            return
        
        # 随机选择一些孔位进行更新
        test_holes = random.sample(self.test_holes, min(20, len(self.test_holes)))
        
        print(f"\n🔄 测试同步更新 {len(test_holes)} 个孔位")
        
        for hole_id in test_holes:
            status = random.choice([HoleStatus.QUALIFIED, HoleStatus.DEFECTIVE, HoleStatus.PROCESSING])
            
            # 更新全景预览
            self.panorama.update_hole_status(hole_id, status)
            
            # 更新主视图中的孔位（如果可见）
            if hasattr(self.dynamic_display, 'graphics_view') and hasattr(self.dynamic_display.graphics_view, 'hole_items'):
                if hole_id in self.dynamic_display.graphics_view.hole_items:
                    hole_item = self.dynamic_display.graphics_view.hole_items[hole_id]
                    if hasattr(hole_item, 'update_status'):
                        hole_item.update_status(status)
        
        self.info_label.setText(f"测试同步更新: {len(test_holes)} 个孔位")
    
    def start_auto_test(self):
        """开始自动测试"""
        if self.auto_test_timer.isActive():
            # 停止测试
            self.auto_test_timer.stop()
            self.auto_test_btn.setText("自动测试")
            self.info_label.setText("自动测试已停止")
        else:
            # 开始测试
            self.auto_test_count = 0
            self.auto_test_timer.start(100)  # 每100ms更新一个孔位
            self.auto_test_btn.setText("停止测试")
            self.info_label.setText("自动测试进行中...")
            print("\n🚀 开始自动同步测试")
    
    def auto_update_hole(self):
        """自动更新孔位状态"""
        if not self.test_holes or self.auto_test_count >= 100:
            # 测试完成
            self.auto_test_timer.stop()
            self.auto_test_btn.setText("自动测试")
            self.info_label.setText(f"自动测试完成: 更新了 {self.auto_test_count} 个孔位")
            return
        
        # 随机选择一个孔位更新
        hole_id = random.choice(self.test_holes)
        status = random.choice([HoleStatus.QUALIFIED, HoleStatus.DEFECTIVE, HoleStatus.PROCESSING, HoleStatus.BLIND])
        
        # 更新全景预览
        self.panorama.update_hole_status(hole_id, status)
        
        # 更新主视图（如果可见）
        if hasattr(self.dynamic_display, 'graphics_view') and hasattr(self.dynamic_display.graphics_view, 'hole_items'):
            if hole_id in self.dynamic_display.graphics_view.hole_items:
                hole_item = self.dynamic_display.graphics_view.hole_items[hole_id]
                if hasattr(hole_item, 'update_status'):
                    hole_item.update_status(status)
        
        self.auto_test_count += 1
        if self.auto_test_count % 10 == 0:
            print(f"✅ 自动测试进度: {self.auto_test_count}/100")

def main():
    app = QApplication(sys.argv)
    
    window = SyncTestWindow()
    window.show()
    
    print("\n" + "="*60)
    print("全景预览同步测试")
    print("="*60)
    print("功能说明:")
    print("• 加载数据: 加载DXF文件到两个视图")
    print("• 测试同步: 随机更新孔位状态，观察同步效果")
    print("• 自动测试: 持续更新孔位状态，验证1秒批量更新")
    print("")
    print("预期效果:")
    print("• 左侧全景预览每1秒批量更新状态颜色")
    print("• 右侧动态扇形显示实时更新")
    print("• 两者应该保持一致的状态显示")
    print("="*60 + "\n")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()