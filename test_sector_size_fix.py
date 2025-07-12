#!/usr/bin/env python3
"""测试扇形大小稳定性修复"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QHBoxLayout
from PySide6.QtCore import QTimer, Qt
from aidcis2.integration.legacy_dxf_loader import LegacyDXFLoader
from aidcis2.graphics.dynamic_sector_view import DynamicSectorDisplayWidget
from aidcis2.graphics.sector_manager import SectorQuadrant

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("扇形大小稳定性测试")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中心组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 创建动态扇形显示
        self.dynamic_display = DynamicSectorDisplayWidget()
        self.dynamic_display.setStyleSheet("background-color: white; border: 2px solid #333;")
        layout.addWidget(self.dynamic_display)
        
        # 创建按钮面板
        button_panel = QWidget()
        button_layout = QHBoxLayout(button_panel)
        
        # 扇形切换按钮
        self.sector_buttons = []
        for i, sector in enumerate([SectorQuadrant.SECTOR_1, SectorQuadrant.SECTOR_2, 
                                    SectorQuadrant.SECTOR_3, SectorQuadrant.SECTOR_4]):
            btn = QPushButton(f"扇形{i+1}")
            btn.clicked.connect(lambda _, s=sector: self.switch_sector(s))
            button_layout.addWidget(btn)
            self.sector_buttons.append(btn)
        
        layout.addWidget(button_panel)
        
        # 用于记录缩放变化
        self.scale_history = []
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_scale)
        self.check_timer.start(100)  # 每100ms检查一次
        
    def load_dxf(self, path):
        """加载DXF文件"""
        loader = LegacyDXFLoader()
        hole_collection = loader.load_dxf_file(path)
        
        if hole_collection:
            print(f"✅ 加载了 {len(hole_collection)} 个孔位")
            self.dynamic_display.set_hole_collection(hole_collection)
            
            # 延迟切换到扇形4
            QTimer.singleShot(500, lambda: self.switch_sector(SectorQuadrant.SECTOR_4))
    
    def switch_sector(self, sector):
        """切换扇形"""
        print(f"\n{'='*60}")
        print(f"切换到 {sector.value}")
        print(f"{'='*60}")
        self.scale_history.clear()  # 清空历史记录
        self.dynamic_display.switch_to_sector(sector)
    
    def check_scale(self):
        """检查当前缩放比例"""
        if hasattr(self.dynamic_display, 'graphics_view'):
            current_scale = self.dynamic_display.graphics_view.transform().m11()
            
            # 只记录有意义的变化
            if not self.scale_history or abs(current_scale - self.scale_history[-1]) > 0.01:
                self.scale_history.append(current_scale)
                
                # 如果有多次变化，输出历史
                if len(self.scale_history) > 1:
                    print(f"📊 缩放历史: {[f'{s:.3f}' for s in self.scale_history]}")
                    print(f"   当前缩放: {current_scale:.3f}x")

def main():
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    # 加载测试数据
    dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-1/AIDCIS3-LFS/assets/dxf/DXF Graph/东重管板.dxf"
    QTimer.singleShot(100, lambda: window.load_dxf(dxf_path))
    
    print("\n" + "="*60)
    print("扇形大小稳定性测试")
    print("="*60)
    print("观察扇形切换时的缩放变化")
    print("如果缩放保持稳定，说明修复成功")
    print("="*60 + "\n")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()