#!/usr/bin/env python3
"""测试最终修复效果"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PySide6.QtCore import QTimer
from aidcis2.integration.legacy_dxf_loader import LegacyDXFLoader
from aidcis2.graphics.dynamic_sector_view import DynamicSectorDisplayWidget
from aidcis2.graphics.sector_manager import SectorQuadrant

def main():
    app = QApplication(sys.argv)
    
    # 创建主窗口
    window = QMainWindow()
    window.setWindowTitle("扇形大小稳定性测试")
    window.setGeometry(100, 100, 800, 600)
    
    # 创建中心组件
    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    layout = QVBoxLayout(central_widget)
    
    # 创建动态扇形显示
    dynamic_display = DynamicSectorDisplayWidget()
    dynamic_display.setStyleSheet("background-color: white; border: 2px solid #333;")
    layout.addWidget(dynamic_display)
    
    window.show()
    
    # 记录缩放历史
    scale_history = []
    
    def check_scale():
        """检查并记录缩放"""
        if hasattr(dynamic_display, 'graphics_view'):
            scale = dynamic_display.graphics_view.transform().m11()
            scale_history.append(scale)
            if len(scale_history) > 10:  # 只保留最近10个值
                scale_history.pop(0)
    
    def load_and_test():
        """加载并测试"""
        print("\n" + "="*60)
        print("开始测试扇形大小稳定性")
        print("="*60)
        
        # 加载DXF
        dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-1/AIDCIS3-LFS/assets/dxf/DXF Graph/东重管板.dxf"
        loader = LegacyDXFLoader()
        hole_collection = loader.load_dxf_file(dxf_path)
        
        if hole_collection:
            print(f"✅ 加载了 {len(hole_collection)} 个孔位")
            dynamic_display.set_hole_collection(hole_collection)
            
            # 切换到扇形4
            print("\n切换到扇形4...")
            dynamic_display.switch_to_sector(SectorQuadrant.SECTOR_4)
            
            # 开始监控缩放
            timer = QTimer()
            timer.timeout.connect(check_scale)
            timer.start(100)  # 每100ms检查一次
            
            # 3秒后报告结果
            QTimer.singleShot(3000, lambda: report_result())
    
    def report_result():
        """报告测试结果"""
        print("\n" + "="*60)
        print("测试结果")
        print("="*60)
        
        if scale_history:
            # 统计不同的缩放值
            unique_scales = []
            for s in scale_history:
                if not unique_scales or abs(s - unique_scales[-1]) > 0.01:
                    unique_scales.append(s)
            
            print(f"缩放历史: {[f'{s:.3f}' for s in unique_scales]}")
            print(f"最终缩放: {scale_history[-1]:.3f}x")
            
            if len(unique_scales) == 1:
                print("✅ 测试通过：缩放保持稳定")
            elif len(unique_scales) <= 2:
                print("⚠️ 测试基本通过：缩放有轻微变化")
            else:
                print("❌ 测试失败：缩放变化过多")
        
        print("="*60 + "\n")
        
        # 测试完成后退出
        QTimer.singleShot(1000, app.quit)
    
    # 启动测试
    QTimer.singleShot(100, load_and_test)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()