#!/usr/bin/env python3
"""
测试扇形显示的缩放效果
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt

from aidcis2.graphics.sector_view import SectorOverviewWidget
from aidcis2.graphics.sector_manager import SectorManager, SectorQuadrant, SectorProgress
from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus
from PySide6.QtGui import QColor


def create_test_hole_collection():
    """创建测试用的孔位集合"""
    holes = {}
    
    # 创建分布在4个象限的孔位
    for i in range(100):
        x = (i % 10 - 5) * 50
        y = (i // 10 - 5) * 50
        
        hole_id = f"H{i+1:03d}"
        status = HoleStatus.QUALIFIED if i % 3 == 0 else HoleStatus.NOT_DETECTED
        
        holes[hole_id] = HoleData(
            hole_id=hole_id,
            center_x=x,
            center_y=y,
            radius=10,
            status=status
        )
    
    return HoleCollection(holes)


class TestWindow(QMainWindow):
    """测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("扇形显示测试")
        self.setup_ui()
        
    def setup_ui(self):
        """设置界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        
        # 创建扇形概览组件
        self.sector_overview = SectorOverviewWidget()
        self.sector_overview.setFixedSize(200, 250)  # 设置固定大小以模拟实际使用场景
        layout.addWidget(self.sector_overview)
        
        # 创建扇形管理器并加载数据
        self.sector_manager = SectorManager()
        hole_collection = create_test_hole_collection()
        self.sector_manager.load_hole_collection(hole_collection)
        
        # 连接扇形管理器
        self.sector_overview.set_sector_manager(self.sector_manager)
        
        # 更新进度显示
        for sector in SectorQuadrant:
            holes = self.sector_manager.get_sector_holes(sector)
            total = len(holes)
            completed = sum(1 for h in holes if h.status != HoleStatus.NOT_DETECTED)
            qualified = sum(1 for h in holes if h.status == HoleStatus.QUALIFIED)
            
            progress = SectorProgress(
                sector=sector,
                total_holes=total,
                completed_holes=completed,
                qualified_holes=qualified,
                defective_holes=completed - qualified,
                progress_percentage=(completed / total * 100) if total > 0 else 0,
                qualification_rate=(qualified / completed * 100) if completed > 0 else 0,
                status_color=QColor(0, 255, 0) if qualified > 0 else QColor(128, 128, 128)
            )
            
            self.sector_manager.sector_progress_updated.emit(sector, progress)
        
        # 设置窗口大小
        self.resize(400, 300)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = TestWindow()
    window.show()
    
    print("\n=== 扇形显示测试 ===")
    print("检查扇形是否完整显示")
    print("应该能看到4个扇形，每个显示区域编号和进度百分比")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()