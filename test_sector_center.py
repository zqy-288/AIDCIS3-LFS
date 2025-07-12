#!/usr/bin/env python3
"""测试扇形中心对齐功能"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from PySide6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QWidget, QPushButton, QVBoxLayout, QLabel
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPainter, QPen, QColor
from aidcis2.graphics.dynamic_sector_view import DynamicSectorDisplayWidget, CompletePanoramaWidget
from aidcis2.graphics.sector_manager import SectorQuadrant
from aidcis2.integration.legacy_dxf_loader import LegacyDXFLoader

class CenterMarkWidget(QWidget):
    """在视图中心显示十字标记"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制中心十字线
        pen = QPen(QColor(255, 0, 0, 200), 2)
        painter.setPen(pen)
        
        center_x = self.width() / 2
        center_y = self.height() / 2
        
        # 水平线
        painter.drawLine(center_x - 20, center_y, center_x + 20, center_y)
        # 垂直线
        painter.drawLine(center_x, center_y - 20, center_x, center_y + 20)
        
        # 绘制中心圆圈
        painter.drawEllipse(center_x - 5, center_y - 5, 10, 10)

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("扇形中心对齐测试")
        self.setGeometry(100, 100, 1400, 900)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建水平布局
        layout = QHBoxLayout(central_widget)
        
        # 左侧：全景图
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.addWidget(QLabel("全景预览"))
        self.panorama = CompletePanoramaWidget()
        left_layout.addWidget(self.panorama)
        
        # 右侧：动态扇形显示
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.addWidget(QLabel("主检测视图"))
        
        # 创建包含动态显示和中心标记的容器
        display_container = QWidget()
        display_container.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        display_layout = QVBoxLayout(display_container)
        display_layout.setContentsMargins(0, 0, 0, 0)
        
        self.dynamic_display = DynamicSectorDisplayWidget()
        display_layout.addWidget(self.dynamic_display)
        
        # 在动态显示上添加中心标记
        self.center_mark = CenterMarkWidget(self.dynamic_display)
        
        right_layout.addWidget(display_container)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        self.sector_labels = ["扇形1(右上)", "扇形2(左上)", "扇形3(左下)", "扇形4(右下)"]
        for i, sector in enumerate(SectorQuadrant):
            btn = QPushButton(self.sector_labels[i])
            btn.clicked.connect(lambda checked, s=sector: self.switch_sector(s))
            button_layout.addWidget(btn)
        right_layout.addLayout(button_layout)
        
        # 状态标签
        self.status_label = QLabel("正在加载...")
        self.status_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.status_label)
        
        # 添加到主布局
        layout.addWidget(left_panel, 1)
        layout.addWidget(right_panel, 2)
        
        # 连接信号
        self.dynamic_display.sector_changed.connect(self.on_sector_changed)
        
        # 加载数据
        QTimer.singleShot(100, self.load_data)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 调整中心标记的大小
        if hasattr(self, 'center_mark') and hasattr(self, 'dynamic_display'):
            self.center_mark.resize(self.dynamic_display.size())
    
    def load_data(self):
        """加载DXF数据"""
        dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-1/AIDCIS3-LFS/assets/dxf/DXF Graph/东重管板.dxf"
        loader = LegacyDXFLoader()
        hole_collection = loader.load_dxf_file(dxf_path)
        
        if hole_collection:
            print(f"✅ 加载了 {len(hole_collection)} 个孔位")
            self.status_label.setText(f"已加载 {len(hole_collection)} 个孔位")
            
            # 设置数据
            self.panorama.load_complete_view(hole_collection)
            self.dynamic_display.set_hole_collection(hole_collection)
            
            # 延迟后默认显示扇形4（右下）
            QTimer.singleShot(1000, lambda: self.switch_sector(SectorQuadrant.SECTOR_4))
    
    def switch_sector(self, sector):
        """切换扇形"""
        sector_index = list(SectorQuadrant).index(sector)
        print(f"\n🔄 切换到 {self.sector_labels[sector_index]}")
        self.status_label.setText(f"当前显示: {self.sector_labels[sector_index]}")
        self.dynamic_display.switch_to_sector(sector)
    
    def on_sector_changed(self, sector):
        """扇形切换事件"""
        sector_index = list(SectorQuadrant).index(sector)
        print(f"📡 扇形已切换到: {self.sector_labels[sector_index]}")
        # 同步高亮
        self.panorama.highlight_sector(sector)

def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    
    # 提示信息
    print("\n" + "="*50)
    print("扇形中心对齐测试")
    print("="*50)
    print("红色十字标记显示视图中心位置")
    print("切换不同扇形，观察扇形中心是否与红色十字对齐")
    print("="*50 + "\n")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()