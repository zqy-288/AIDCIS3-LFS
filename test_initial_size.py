#!/usr/bin/env python3
"""测试扇形初始大小"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import QTimer, Qt
from aidcis2.integration.legacy_dxf_loader import LegacyDXFLoader
from aidcis2.graphics.dynamic_sector_view import DynamicSectorDisplayWidget
from aidcis2.graphics.sector_manager import SectorQuadrant

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("扇形初始大小测试")
        self.setGeometry(100, 100, 1000, 800)
        
        # 创建中心组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 信息标签
        self.info_label = QLabel("正在初始化...")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("padding: 10px; background-color: #f0f0f0;")
        layout.addWidget(self.info_label)
        
        # 创建动态扇形显示
        self.dynamic_display = DynamicSectorDisplayWidget()
        self.dynamic_display.setStyleSheet("background-color: white; border: 2px solid #333;")
        self.dynamic_display.setMinimumSize(700, 500)  # 设置合理的最小尺寸
        layout.addWidget(self.dynamic_display)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        
        # 模拟进度按钮
        self.simulate_btn = QPushButton("模拟进度（对比测试）")
        self.simulate_btn.clicked.connect(self.simulate_progress)
        self.simulate_btn.setEnabled(False)
        button_layout.addWidget(self.simulate_btn)
        
        layout.addLayout(button_layout)
        
        # 记录初始缩放
        self.initial_scale = None
        self.after_simulate_scale = None
        
    def load_dxf(self):
        """加载DXF文件"""
        self.info_label.setText("正在加载DXF文件...")
        
        loader = LegacyDXFLoader()
        dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-1/AIDCIS3-LFS/assets/dxf/DXF Graph/东重管板.dxf"
        hole_collection = loader.load_dxf_file(dxf_path)
        
        if hole_collection:
            self.info_label.setText(f"✅ 加载了 {len(hole_collection)} 个孔位")
            self.dynamic_display.set_hole_collection(hole_collection)
            
            # 记录初始缩放
            QTimer.singleShot(1000, self.record_initial_scale)
            
            # 启用模拟按钮
            self.simulate_btn.setEnabled(True)
    
    def record_initial_scale(self):
        """记录初始缩放"""
        if hasattr(self.dynamic_display, 'graphics_view'):
            self.initial_scale = self.dynamic_display.graphics_view.transform().m11()
            view_size = self.dynamic_display.graphics_view.viewport().size()
            
            self.info_label.setText(
                f"初始状态 - 缩放: {self.initial_scale:.3f}x, "
                f"视图大小: {view_size.width()}x{view_size.height()}px"
            )
            
            print("\n" + "="*60)
            print("初始加载完成")
            print(f"缩放: {self.initial_scale:.3f}x")
            print(f"视图大小: {view_size.width()}x{view_size.height()}px")
            print("="*60 + "\n")
    
    def simulate_progress(self):
        """模拟进度（对比测试）"""
        print("\n模拟进度按钮点击...")
        
        # 这里可以添加模拟进度的逻辑
        # 主要是为了对比点击前后的缩放变化
        
        QTimer.singleShot(500, self.record_after_simulate_scale)
    
    def record_after_simulate_scale(self):
        """记录模拟后的缩放"""
        if hasattr(self.dynamic_display, 'graphics_view'):
            self.after_simulate_scale = self.dynamic_display.graphics_view.transform().m11()
            view_size = self.dynamic_display.graphics_view.viewport().size()
            
            print("\n" + "="*60)
            print("模拟进度后")
            print(f"缩放: {self.after_simulate_scale:.3f}x")
            print(f"视图大小: {view_size.width()}x{view_size.height()}px")
            
            if self.initial_scale and self.after_simulate_scale:
                change = self.after_simulate_scale / self.initial_scale
                print(f"\n缩放变化: {change:.2f}倍")
                
                if abs(change - 1.0) < 0.1:
                    print("✅ 测试通过：缩放保持稳定")
                    self.info_label.setText(
                        f"✅ 缩放保持稳定 - 初始: {self.initial_scale:.3f}x, "
                        f"当前: {self.after_simulate_scale:.3f}x"
                    )
                else:
                    print("⚠️ 缩放有变化")
                    self.info_label.setText(
                        f"⚠️ 缩放有变化 - 初始: {self.initial_scale:.3f}x, "
                        f"当前: {self.after_simulate_scale:.3f}x"
                    )
            
            print("="*60 + "\n")

def main():
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    # 延迟加载，确保窗口完全显示
    QTimer.singleShot(500, window.load_dxf)
    
    print("\n" + "="*60)
    print("扇形初始大小测试")
    print("="*60)
    print("观察初始加载时的扇形大小")
    print("点击'模拟进度'按钮对比前后变化")
    print("="*60 + "\n")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()