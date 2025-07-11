#!/usr/bin/env python3
"""
扇形区域显示完整性端到端测试
测试扇形图显示是否被截断的问题
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QScreen

from aidcis2.graphics.sector_view import SectorOverviewWidget, SectorDetailView
from aidcis2.graphics.sector_manager import SectorManager, SectorQuadrant
from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus


def create_test_holes():
    """创建测试孔位数据"""
    holes = {}
    hole_id = 1
    
    # 为每个扇形区域创建孔位
    # 区域1 (右上): x > 0, y > 0
    for i in range(20):
        for j in range(20):
            x = 10 + i * 5
            y = 10 + j * 5
            holes[f"H{hole_id:05d}"] = HoleData(
                hole_id=f"H{hole_id:05d}",
                center_x=x,
                center_y=y,
                radius=1.5,
                status=HoleStatus.PENDING
            )
            hole_id += 1
    
    # 区域2 (左上): x < 0, y > 0
    for i in range(20):
        for j in range(20):
            x = -10 - i * 5
            y = 10 + j * 5
            holes[f"H{hole_id:05d}"] = HoleData(
                hole_id=f"H{hole_id:05d}",
                center_x=x,
                center_y=y,
                radius=1.5,
                status=HoleStatus.QUALIFIED
            )
            hole_id += 1
    
    # 区域3 (左下): x < 0, y < 0
    for i in range(20):
        for j in range(20):
            x = -10 - i * 5
            y = -10 - j * 5
            holes[f"H{hole_id:05d}"] = HoleData(
                hole_id=f"H{hole_id:05d}",
                center_x=x,
                center_y=y,
                radius=1.5,
                status=HoleStatus.DEFECTIVE
            )
            hole_id += 1
    
    # 区域4 (右下): x > 0, y < 0
    for i in range(20):
        for j in range(20):
            x = 10 + i * 5
            y = -10 - j * 5
            holes[f"H{hole_id:05d}"] = HoleData(
                hole_id=f"H{hole_id:05d}",
                center_x=x,
                center_y=y,
                radius=1.5,
                status=HoleStatus.QUALIFIED if i % 2 == 0 else HoleStatus.PENDING
            )
            hole_id += 1
    
    return HoleCollection(holes=holes)


class SectorDisplayTestWindow(QMainWindow):
    """扇形显示测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("扇形区域显示完整性测试")
        self.setup_ui()
        self.load_test_data()
    
    def setup_ui(self):
        """设置界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(20)
        
        # 左侧：扇形概览组件
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # 创建扇形概览组件 - 不设置固定大小
        self.sector_overview = SectorOverviewWidget()
        self.sector_overview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.sector_overview.setMinimumSize(300, 300)  # 设置最小大小
        
        left_layout.addWidget(self.sector_overview)
        
        # 右侧：扇形详情
        self.sector_detail = SectorDetailView()
        self.sector_detail.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.sector_detail.setMinimumWidth(400)
        
        # 添加到主布局
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(self.sector_detail, 1)
        
        # 连接信号
        self.sector_overview.sector_selected.connect(self.on_sector_selected)
        
        # 设置窗口大小
        self.resize(1000, 600)
        
        # 居中显示
        self.center_on_screen()
    
    def center_on_screen(self):
        """将窗口居中显示"""
        screen = QApplication.primaryScreen()
        if screen:
            screen_rect = screen.availableGeometry()
            window_rect = self.frameGeometry()
            window_rect.moveCenter(screen_rect.center())
            self.move(window_rect.topLeft())
    
    def load_test_data(self):
        """加载测试数据"""
        # 创建测试孔位
        hole_collection = create_test_holes()
        
        # 创建扇形管理器
        self.sector_manager = SectorManager()
        self.sector_manager.load_hole_collection(hole_collection)
        
        # 设置扇形管理器
        self.sector_overview.set_sector_manager(self.sector_manager)
        self.sector_detail.set_sector_manager(self.sector_manager)
        
        # 模拟进度更新
        self.simulate_progress()
    
    def simulate_progress(self):
        """模拟进度更新"""
        # 模拟各扇形的进度
        progress_map = {
            SectorQuadrant.SECTOR_1: 0.3,
            SectorQuadrant.SECTOR_2: 0.6,
            SectorQuadrant.SECTOR_3: 0.9,
            SectorQuadrant.SECTOR_4: 0.45
        }
        
        for sector, progress_ratio in progress_map.items():
            holes = self.sector_manager.get_sector_holes(sector)
            completed_count = int(len(holes) * progress_ratio)
            
            # 更新部分孔位状态
            for i, hole in enumerate(holes):
                if i < completed_count:
                    hole.status = HoleStatus.QUALIFIED
                    self.sector_manager.update_hole_status(hole.hole_id, HoleStatus.QUALIFIED)
        
        print("\n=== 扇形显示测试信息 ===")
        print(f"扇形概览组件大小: {self.sector_overview.size()}")
        print(f"图形视图大小: {self.sector_overview.graphics_view.size()}")
        print(f"场景矩形: {self.sector_overview.graphics_scene.sceneRect()}")
        
        # 检查每个扇形项的边界
        for sector, item in self.sector_overview.sector_items.items():
            print(f"\n{sector.value}:")
            print(f"  边界矩形: {item.boundingRect()}")
            print(f"  场景位置: {item.scenePos()}")
            print(f"  路径边界: {item.path().boundingRect()}")
    
    def on_sector_selected(self, sector: SectorQuadrant):
        """处理扇形选择"""
        print(f"\n选中扇形: {sector.value}")
        self.sector_detail.show_sector_detail(sector)
    
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        print(f"\n窗口大小改变: {event.size()}")
        
        # 确保扇形视图适应新大小
        if hasattr(self, 'sector_overview'):
            self.sector_overview.graphics_view.fitInView(
                self.sector_overview.graphics_scene.sceneRect(), 
                Qt.KeepAspectRatio
            )


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle('Fusion')
    
    # 创建并显示测试窗口
    window = SectorDisplayTestWindow()
    window.show()
    
    # 打印初始状态
    print("\n=== 扇形显示完整性测试 ===")
    print("测试目标：")
    print("1. 检查扇形图是否完整显示")
    print("2. 验证扇形不被截断")
    print("3. 确保文本标签可见")
    print("4. 测试窗口缩放时的适应性")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()