#!/usr/bin/env python3
"""
扇形显示问题诊断测试
简化测试以找出显示不全的根本原因
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QSizePolicy, QGraphicsView
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QBrush, QPen, QColor, QFont

from aidcis2.graphics.sector_view import SectorOverviewWidget, SectorGraphicsItem
from aidcis2.graphics.sector_manager import SectorManager, SectorQuadrant, SectorProgress
from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus


class DiagnosticWindow(QMainWindow):
    """诊断窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("扇形显示诊断")
        self.setup_ui()
        self.run_diagnostics()
    
    def setup_ui(self):
        """设置界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # 诊断信息标签
        self.info_label = QLabel("扇形显示诊断信息：")
        self.info_label.setFont(QFont("Arial", 12))
        layout.addWidget(self.info_label)
        
        # 创建扇形概览组件
        self.sector_overview = SectorOverviewWidget()
        self.sector_overview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.sector_overview.setMinimumSize(400, 400)
        layout.addWidget(self.sector_overview)
        
        # 状态标签
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        self.resize(600, 700)
    
    def run_diagnostics(self):
        """运行诊断测试"""
        # 创建简单的测试数据
        holes = {}
        for i in range(10):
            holes[f"H{i:03d}"] = HoleData(
                hole_id=f"H{i:03d}",
                center_x=i * 10,
                center_y=i * 10,
                radius=1.5,
                status=HoleStatus.PENDING
            )
        
        hole_collection = HoleCollection(holes=holes)
        
        # 创建并设置扇形管理器
        sector_manager = SectorManager()
        sector_manager.load_hole_collection(hole_collection)
        self.sector_overview.set_sector_manager(sector_manager)
        
        # 手动触发进度更新
        for sector in SectorQuadrant:
            progress = SectorProgress(
                sector=sector,
                total_holes=100,
                completed_holes=25,
                qualified_holes=20,
                defective_holes=5,
                progress_percentage=25.0,
                status_color=QColor(100, 200, 100)
            )
            sector_manager.sector_progress_updated.emit(sector, progress)
        
        # 诊断信息
        self.diagnose_display()
    
    def diagnose_display(self):
        """诊断显示问题"""
        info_lines = []
        
        # 检查组件大小
        info_lines.append(f"扇形概览组件大小: {self.sector_overview.size()}")
        info_lines.append(f"图形视图大小: {self.sector_overview.graphics_view.size()}")
        
        # 检查场景设置
        scene = self.sector_overview.graphics_scene
        info_lines.append(f"场景矩形: {scene.sceneRect()}")
        info_lines.append(f"场景项数量: {len(scene.items())}")
        
        # 检查视口设置
        view = self.sector_overview.graphics_view
        info_lines.append(f"视口矩形: {view.viewport().rect()}")
        info_lines.append(f"视图变换: {view.transform()}")
        
        # 检查每个扇形项
        info_lines.append("\n各扇形项信息：")
        for sector, item in self.sector_overview.sector_items.items():
            info_lines.append(f"\n{sector.value}:")
            info_lines.append(f"  位置: {item.pos()}")
            info_lines.append(f"  边界: {item.boundingRect()}")
            info_lines.append(f"  场景边界: {item.sceneBoundingRect()}")
            info_lines.append(f"  路径边界: {item.path().boundingRect()}")
            
            # 检查是否在视口内
            view_rect = view.mapToScene(view.viewport().rect()).boundingRect()
            if not view_rect.contains(item.sceneBoundingRect()):
                info_lines.append(f"  ⚠️ 警告: 该扇形可能部分或完全在视口外！")
        
        # 显示诊断信息
        self.status_label.setText("\n".join(info_lines))
        
        # 尝试修复显示问题
        self.fix_display_issue()
    
    def fix_display_issue(self):
        """尝试修复显示问题"""
        # 强制重新适应视图
        view = self.sector_overview.graphics_view
        scene = self.sector_overview.graphics_scene
        
        # 获取所有项的边界
        all_items_rect = scene.itemsBoundingRect()
        
        # 添加边距
        margin = 20
        expanded_rect = all_items_rect.adjusted(-margin, -margin, margin, margin)
        
        # 更新场景矩形
        scene.setSceneRect(expanded_rect)
        
        # 适应视图
        view.fitInView(expanded_rect, Qt.KeepAspectRatio)
        
        print(f"\n修复后:")
        print(f"场景矩形: {scene.sceneRect()}")
        print(f"项边界: {all_items_rect}")
    
    def resizeEvent(self, event):
        """窗口大小改变时重新适应"""
        super().resizeEvent(event)
        if hasattr(self, 'sector_overview'):
            view = self.sector_overview.graphics_view
            scene = self.sector_overview.graphics_scene
            view.fitInView(scene.sceneRect(), Qt.KeepAspectRatio)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    window = DiagnosticWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()