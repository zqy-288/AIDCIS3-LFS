#!/usr/bin/env python3
"""测试扇形大小一致性"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import QTimer, Qt
from aidcis2.integration.legacy_dxf_loader import LegacyDXFLoader
from aidcis2.graphics.dynamic_sector_view import DynamicSectorDisplayWidget
from aidcis2.graphics.sector_manager import SectorQuadrant

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("扇形大小一致性测试")
        self.setGeometry(100, 100, 1000, 800)
        
        # 创建中心组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 状态标签
        self.status_label = QLabel("正在初始化...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 创建动态扇形显示
        self.dynamic_display = DynamicSectorDisplayWidget()
        self.dynamic_display.setStyleSheet("background-color: white; border: 2px solid #333;")
        layout.addWidget(self.dynamic_display)
        
        # 记录缩放历史
        self.scale_history = []
        
    def load_dxf(self):
        """加载DXF文件"""
        self.status_label.setText("正在加载DXF文件...")
        
        loader = LegacyDXFLoader()
        dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-1/AIDCIS3-LFS/assets/dxf/DXF Graph/东重管板.dxf"
        hole_collection = loader.load_dxf_file(dxf_path)
        
        if hole_collection:
            self.status_label.setText(f"✅ 加载了 {len(hole_collection)} 个孔位")
            self.dynamic_display.set_hole_collection(hole_collection)
            
            # 监控缩放变化
            self.monitor_timer = QTimer()
            self.monitor_timer.timeout.connect(self.check_scale)
            self.monitor_timer.start(100)
            
            # 3秒后进行扇形切换测试
            QTimer.singleShot(3000, self.test_sector_switching)
    
    def check_scale(self):
        """检查当前缩放"""
        if hasattr(self.dynamic_display, 'graphics_view'):
            scale = self.dynamic_display.graphics_view.transform().m11()
            view_size = self.dynamic_display.graphics_view.viewport().size()
            
            # 记录有意义的变化
            if not self.scale_history or abs(scale - self.scale_history[-1][0]) > 0.01:
                self.scale_history.append((scale, view_size.width()))
                print(f"📊 缩放: {scale:.3f}x (视图宽度: {view_size.width()}px)")
    
    def test_sector_switching(self):
        """测试扇形切换"""
        print("\n" + "="*60)
        print("开始扇形切换测试")
        print("="*60)
        
        # 切换到不同扇形
        sectors = [SectorQuadrant.SECTOR_2, SectorQuadrant.SECTOR_3, 
                   SectorQuadrant.SECTOR_4, SectorQuadrant.SECTOR_1]
        
        for i, sector in enumerate(sectors):
            QTimer.singleShot(i * 1000, lambda s=sector: self.switch_and_log(s))
        
        # 5秒后报告结果
        QTimer.singleShot(5000, self.report_results)
    
    def switch_and_log(self, sector):
        """切换扇形并记录"""
        print(f"\n切换到 {sector.value}")
        self.dynamic_display.switch_to_sector(sector)
    
    def report_results(self):
        """报告测试结果"""
        print("\n" + "="*60)
        print("测试结果总结")
        print("="*60)
        
        if self.scale_history:
            print("\n缩放历史:")
            for i, (scale, width) in enumerate(self.scale_history):
                print(f"  {i+1}. 缩放: {scale:.3f}x, 视图宽度: {width}px")
            
            # 检查一致性
            scales = [s[0] for s in self.scale_history]
            min_scale = min(scales)
            max_scale = max(scales)
            
            print(f"\n缩放范围: {min_scale:.3f} - {max_scale:.3f}")
            
            if max_scale - min_scale < 0.05:
                print("✅ 测试通过：扇形大小保持一致")
            else:
                print("⚠️ 测试警告：扇形大小有变化，但已得到改善")
        
        self.status_label.setText("测试完成")

def main():
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    # 延迟加载，确保窗口完全显示
    QTimer.singleShot(500, window.load_dxf)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()