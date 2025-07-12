#!/usr/bin/env python3
"""简单测试扇形显示和高亮功能"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from PySide6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QWidget, QPushButton, QVBoxLayout
from PySide6.QtCore import QTimer
from aidcis2.graphics.dynamic_sector_view import DynamicSectorDisplayWidget, CompletePanoramaWidget
from aidcis2.graphics.sector_manager import SectorQuadrant
from aidcis2.integration.legacy_dxf_loader import LegacyDXFLoader

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("扇形高亮测试")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建水平布局
        layout = QHBoxLayout(central_widget)
        
        # 左侧：全景图
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        self.panorama = CompletePanoramaWidget()
        left_layout.addWidget(self.panorama)
        
        # 右侧：动态扇形显示
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        self.dynamic_display = DynamicSectorDisplayWidget()
        right_layout.addWidget(self.dynamic_display)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        for i, sector in enumerate(SectorQuadrant):
            btn = QPushButton(f"扇形{i+1}")
            btn.clicked.connect(lambda checked, s=sector: self.switch_sector(s))
            button_layout.addWidget(btn)
        right_layout.addLayout(button_layout)
        
        # 添加到主布局
        layout.addWidget(left_panel, 1)
        layout.addWidget(right_panel, 2)
        
        # 连接信号
        self.dynamic_display.sector_changed.connect(self.on_sector_changed)
        
        # 加载数据
        self.load_data()
    
    def load_data(self):
        """加载DXF数据"""
        dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-1/AIDCIS3-LFS/assets/dxf/DXF Graph/东重管板.dxf"
        loader = LegacyDXFLoader()
        hole_collection = loader.load_dxf_file(dxf_path)
        
        if hole_collection:
            print(f"✅ 加载了 {len(hole_collection)} 个孔位")
            # 设置数据
            self.panorama.load_complete_view(hole_collection)
            self.dynamic_display.set_hole_collection(hole_collection)
            
            # 默认显示扇形1
            QTimer.singleShot(500, lambda: self.switch_sector(SectorQuadrant.SECTOR_1))
    
    def switch_sector(self, sector):
        """切换扇形"""
        print(f"\n🔄 切换到 {sector.value}")
        self.dynamic_display.switch_to_sector(sector)
    
    def on_sector_changed(self, sector):
        """扇形切换事件"""
        print(f"📡 扇形已切换到: {sector.value}")
        # 同步高亮
        self.panorama.highlight_sector(sector)

def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()