#!/usr/bin/env python3
"""
修复扇形可见性问题
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QPen, QColor
from src.core_business.graphics.complete_panorama_widget import CompletePanoramaWidget
from src.pages.main_detection_p1.services.dxf_loader_service import DXFLoaderService
from src.core_business.graphics.sector_types import SectorQuadrant


class EnhancedPanoramaWidget(CompletePanoramaWidget):
    """增强的全景图组件，改善扇形可见性"""
    
    def _create_sector_dividers(self):
        """创建更明显的扇形分隔线"""
        try:
            if not self.center_point or self.panorama_radius <= 0:
                return
                
            # 创建更明显的十字分隔线
            pen = QPen(QColor(50, 50, 50, 255))  # 深色，完全不透明
            pen.setWidth(3)  # 增加线宽
            pen.setStyle(Qt.SolidLine)  # 实线
            
            # 水平线
            scene = self._get_scene()
            if not scene:
                return
                
            h_line = scene.addLine(
                self.center_point.x() - self.panorama_radius,
                self.center_point.y(),
                self.center_point.x() + self.panorama_radius,
                self.center_point.y(),
                pen
            )
            h_line.setZValue(150)  # 确保在最上层
            
            # 垂直线
            v_line = scene.addLine(
                self.center_point.x(),
                self.center_point.y() - self.panorama_radius,
                self.center_point.x(),
                self.center_point.y() + self.panorama_radius,
                pen
            )
            v_line.setZValue(150)
            
            # 添加扇形标签
            self._add_sector_labels()
            
            self.logger.debug("增强扇形分隔线创建完成", "✅")
            
        except Exception as e:
            self.logger.error(f"扇形分隔线创建失败: {e}", "❌")
            
    def _add_sector_labels(self):
        """添加扇形标签"""
        if not self.center_point or self.panorama_radius <= 0:
            return
            
        scene = self._get_scene()
        if not scene:
            return
            
        # 扇形标签位置（相对于中心的偏移）
        label_positions = {
            SectorQuadrant.SECTOR_1: (0.7, -0.7),   # 右上
            SectorQuadrant.SECTOR_2: (-0.7, -0.7),  # 左上
            SectorQuadrant.SECTOR_3: (-0.7, 0.7),   # 左下
            SectorQuadrant.SECTOR_4: (0.7, 0.7),    # 右下
        }
        
        for sector, (dx, dy) in label_positions.items():
            # 计算标签位置
            label_x = self.center_point.x() + dx * self.panorama_radius * 0.5
            label_y = self.center_point.y() + dy * self.panorama_radius * 0.5
            
            # 创建文本项
            text = scene.addText(sector.value)
            text.setPos(label_x - 20, label_y - 10)  # 调整位置使文本居中
            text.setDefaultTextColor(QColor(0, 0, 0, 255))
            text.setZValue(160)  # 确保在最上层
            
            # 设置字体
            font = text.font()
            font.setPointSize(14)
            font.setBold(True)
            text.setFont(font)
            
    def _create_sector_highlights(self):
        """创建扇形高亮项（修改为始终可见的扇形边界）"""
        # 先调用父类方法
        super()._create_sector_highlights()
        
        # 为每个扇形添加可见的边界
        for sector in SectorQuadrant:
            self._create_visible_sector_boundary(sector)
            
    def _create_visible_sector_boundary(self, sector: SectorQuadrant):
        """创建可见的扇形边界"""
        try:
            if not self.center_point or self.panorama_radius <= 0:
                return
                
            scene = self._get_scene()
            if not scene:
                return
                
            # 创建扇形边界（使用较淡的颜色）
            pen = QPen(QColor(100, 100, 100, 100))  # 灰色半透明
            pen.setWidth(2)
            pen.setStyle(Qt.DashLine)
            
            # 根据扇形创建额外的分隔线
            if sector == SectorQuadrant.SECTOR_1:
                # 右上扇形不需要额外线条，十字线已经够了
                pass
            elif sector == SectorQuadrant.SECTOR_2:
                # 左上扇形不需要额外线条
                pass
            elif sector == SectorQuadrant.SECTOR_3:
                # 左下扇形不需要额外线条
                pass
            elif sector == SectorQuadrant.SECTOR_4:
                # 右下扇形不需要额外线条
                pass
                
        except Exception as e:
            self.logger.error(f"创建扇形边界失败: {e}", "❌")


class SectorVisibilityTestWindow(QMainWindow):
    """扇形可见性测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("扇形可见性修复测试")
        self.setGeometry(100, 100, 800, 900)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        
        # 标题
        title = QLabel("扇形可见性修复测试")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # 创建增强的全景图组件
        self.panorama = EnhancedPanoramaWidget()
        self.panorama.setFixedSize(600, 600)
        layout.addWidget(self.panorama)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        
        # 加载按钮
        load_btn = QPushButton("加载DXF数据")
        load_btn.clicked.connect(self.load_dxf_data)
        button_layout.addWidget(load_btn)
        
        # 扇形高亮按钮
        for i in range(1, 5):
            sector_btn = QPushButton(f"高亮扇形{i}")
            sector = getattr(SectorQuadrant, f"SECTOR_{i}")
            sector_btn.clicked.connect(lambda checked, s=sector: self.highlight_sector(s))
            button_layout.addWidget(sector_btn)
            
        layout.addLayout(button_layout)
        
        # 状态标签
        self.status_label = QLabel("准备就绪")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 自动加载
        QTimer.singleShot(500, self.load_dxf_data)
        
    def load_dxf_data(self):
        """加载DXF数据"""
        try:
            self.status_label.setText("正在加载DXF数据...")
            
            dxf_path = str(Path(__file__).parent / "assets" / "dxf" / "DXF Graph" / "东重管板.dxf")
            loader = DXFLoaderService()
            hole_collection = loader.load_dxf_file(dxf_path)
            
            if hole_collection:
                self.panorama.load_hole_collection(hole_collection)
                self.status_label.setText(f"✅ 加载成功: {len(hole_collection.holes)} 个孔位")
                
                # 连接扇形点击信号
                self.panorama.sector_clicked.connect(self.on_sector_clicked)
            else:
                self.status_label.setText("❌ DXF加载失败")
                
        except Exception as e:
            self.status_label.setText(f"❌ 错误: {str(e)}")
            import traceback
            traceback.print_exc()
            
    def highlight_sector(self, sector):
        """高亮指定扇形"""
        self.panorama.highlight_sector(sector)
        self.status_label.setText(f"高亮 {sector.value}")
        
    def on_sector_clicked(self, sector):
        """处理扇形点击"""
        self.status_label.setText(f"点击了 {sector.value}")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    window = SectorVisibilityTestWindow()
    window.show()
    
    # 60秒后退出
    QTimer.singleShot(60000, app.quit)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()