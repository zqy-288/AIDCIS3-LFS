#!/usr/bin/env python3
"""
简单的DXF可视化测试
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QMainWindow, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QBrush, QColor, QPen, QPainter

from src.core_business.dxf_parser import DXFParser
from src.core_business.hole_numbering_service import HoleNumberingService
from src.core_business.graphics.hole_item import HoleGraphicsItem


class SimpleDXFViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("简单DXF查看器")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 布局
        layout = QVBoxLayout(central_widget)
        
        # 信息标签
        self.info_label = QLabel()
        layout.addWidget(self.info_label)
        
        # 创建图形视图
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        layout.addWidget(self.view)
        
        # 加载DXF
        self.load_dxf()
        
    def load_dxf(self):
        """加载并显示DXF文件"""
        dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-LFS/assets/dxf/DXF Graph/测试管板.dxf"
        
        try:
            # 解析DXF
            parser = DXFParser()
            hole_collection = parser.parse_file(dxf_path)
            
            if not hole_collection:
                self.info_label.setText("未找到孔位数据")
                return
            
            # 应用编号
            numbering_service = HoleNumberingService()
            numbering_service.apply_numbering(hole_collection)
            
            # 显示信息
            stats = numbering_service.get_statistics()
            self.info_label.setText(
                f"加载成功！总孔位: {stats['total_count']} | "
                f"A侧: {stats['a_side_count']} | B侧: {stats['b_side_count']}"
            )
            
            # 添加孔位到场景
            for hole in hole_collection.holes.values():
                # 创建孔位图形项
                hole_item = HoleGraphicsItem(hole)
                self.scene.addItem(hole_item)
                
                # 添加标签
                text = self.scene.addText(hole.hole_id)
                text.setPos(hole.center_x + 15, hole.center_y - 5)
                text.setDefaultTextColor(QColor(100, 100, 100))
                text.setScale(0.5)
            
            # 设置场景背景
            self.scene.setBackgroundBrush(QBrush(QColor(240, 240, 240)))
            
            # 适应视图
            self.view.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)
            
        except Exception as e:
            self.info_label.setText(f"加载失败: {str(e)}")
            import traceback
            traceback.print_exc()


def main():
    app = QApplication(sys.argv)
    viewer = SimpleDXFViewer()
    viewer.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()