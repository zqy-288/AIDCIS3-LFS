#!/usr/bin/env python3
"""测试扇形视觉中心对齐"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPainter, QPen, QColor, QBrush
from aidcis2.graphics.dynamic_sector_view import DynamicSectorDisplayWidget
from aidcis2.graphics.sector_manager import SectorQuadrant
from aidcis2.integration.legacy_dxf_loader import LegacyDXFLoader

class CenterCrossWidget(QWidget):
    """在视图中心显示十字线"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 中心点
        center_x = self.width() / 2
        center_y = self.height() / 2
        
        # 绘制十字线
        pen = QPen(QColor(255, 0, 0, 180), 2)
        painter.setPen(pen)
        
        # 水平线
        painter.drawLine(0, center_y, self.width(), center_y)
        # 垂直线
        painter.drawLine(center_x, 0, center_x, self.height())
        
        # 绘制中心圆
        painter.setBrush(QBrush(QColor(255, 0, 0, 100)))
        painter.drawEllipse(center_x - 10, center_y - 10, 20, 20)
        
        # 绘制文字
        painter.setPen(QPen(QColor(255, 0, 0)))
        painter.drawText(center_x + 15, center_y - 15, "视图中心")

def main():
    app = QApplication(sys.argv)
    
    # 创建主窗口
    window = QMainWindow()
    window.setWindowTitle("扇形视觉中心测试")
    window.setGeometry(100, 100, 1000, 800)
    
    # 创建中心部件
    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    layout = QVBoxLayout(central_widget)
    
    # 创建动态扇形显示
    display_container = QWidget()
    display_container.setStyleSheet("background-color: white; border: 2px solid #333;")
    display_layout = QVBoxLayout(display_container)
    display_layout.setContentsMargins(0, 0, 0, 0)
    
    dynamic_display = DynamicSectorDisplayWidget()
    display_layout.addWidget(dynamic_display)
    
    # 添加中心十字线
    center_cross = CenterCrossWidget(dynamic_display)
    
    layout.addWidget(display_container)
    
    # 控制按钮
    button_widget = QWidget()
    button_layout = QHBoxLayout(button_widget)
    
    sectors = [
        (SectorQuadrant.SECTOR_1, "扇形1 (右上)"),
        (SectorQuadrant.SECTOR_2, "扇形2 (左上)"),
        (SectorQuadrant.SECTOR_3, "扇形3 (左下)"),
        (SectorQuadrant.SECTOR_4, "扇形4 (右下)")
    ]
    
    for sector, label in sectors:
        btn = QPushButton(label)
        btn.clicked.connect(lambda checked, s=sector: dynamic_display.switch_to_sector(s))
        button_layout.addWidget(btn)
    
    layout.addWidget(button_widget)
    
    # 调整中心十字线大小
    def resize_cross():
        center_cross.resize(dynamic_display.size())
    
    # 窗口大小改变时调整十字线
    window.resizeEvent = lambda event: (resize_cross(), QMainWindow.resizeEvent(window, event))
    
    # 加载数据
    def load_data():
        dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-1/AIDCIS3-LFS/assets/dxf/DXF Graph/东重管板.dxf"
        loader = LegacyDXFLoader()
        hole_collection = loader.load_dxf_file(dxf_path)
        
        if hole_collection:
            print(f"✅ 加载了 {len(hole_collection)} 个孔位")
            dynamic_display.set_hole_collection(hole_collection)
            
            # 默认显示扇形4
            QTimer.singleShot(500, lambda: dynamic_display.switch_to_sector(SectorQuadrant.SECTOR_4))
            QTimer.singleShot(600, resize_cross)
    
    QTimer.singleShot(100, load_data)
    
    window.show()
    
    print("\n" + "="*60)
    print("扇形视觉中心对齐测试")
    print("="*60)
    print("红色十字线标记视图中心")
    print("每个扇形的视觉中心应该与红色圆圈对齐")
    print("="*60 + "\n")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()