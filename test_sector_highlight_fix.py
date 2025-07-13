#!/usr/bin/env python3
"""测试扇形高亮修复"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from PySide6.QtWidgets import QApplication
from main_window.main_window import MainWindow
from PySide6.QtCore import QTimer
from aidcis2.graphics.sector_manager import SectorQuadrant

def test_sector_highlight():
    """测试扇形高亮功能"""
    app = QApplication.instance() or QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    # 等待窗口初始化
    QTimer.singleShot(1000, lambda: load_test_data(window))
    
    def load_test_data(window):
        """加载测试数据"""
        dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-1/AIDCIS3-LFS/assets/dxf/DXF Graph/东重管板.dxf"
        window.load_dxf_file(dxf_path)
        
        # 等待数据加载完成
        QTimer.singleShot(2000, lambda: test_sectors(window))
    
    def test_sectors(window):
        """测试各个扇形的高亮"""
        sectors = [
            SectorQuadrant.SECTOR_1,  # 右上
            SectorQuadrant.SECTOR_2,  # 左上
            SectorQuadrant.SECTOR_3,  # 左下
            SectorQuadrant.SECTOR_4,  # 右下
        ]
        
        def test_next_sector(index=0):
            if index < len(sectors):
                sector = sectors[index]
                print(f"\n🔄 切换到扇形 {sector.value}")
                
                # 切换主视图到指定扇形
                if hasattr(window, 'dynamic_sector_display'):
                    window.dynamic_sector_display.switch_to_sector(sector)
                
                # 3秒后测试下一个扇形
                QTimer.singleShot(3000, lambda: test_next_sector(index + 1))
            else:
                print("\n✅ 测试完成！")
                # 保持窗口打开
        
        # 开始测试
        test_next_sector()
    
    app.exec()

if __name__ == "__main__":
    test_sector_highlight()