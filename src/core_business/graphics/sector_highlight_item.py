"""
扇形区域高亮显示图形项
用于在图形视图中高亮显示特定的扇形区域
"""

import math
from typing import Optional, Tuple
from PySide6.QtWidgets import QGraphicsPathItem
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPen, QBrush, QColor, QPainterPath

from src.core_business.graphics.sector_types import SectorQuadrant


class SectorHighlightItem(QGraphicsPathItem):
    """扇形区域高亮显示图形项"""
    
    def __init__(self, sector: SectorQuadrant, center: QPointF, radius: float, 
                 sector_bounds: Optional[Tuple[float, float, float, float]] = None, 
                 parent=None):
        """
        初始化扇形高亮项
        
        Args:
            sector: 扇形象限
            center: 中心点
            radius: 半径
            sector_bounds: 扇形边界 (min_x, min_y, max_x, max_y)
            parent: 父图形项
        """
        super().__init__(parent)
        self.sector = sector
        self.center = center
        self.radius = radius
        self.sector_bounds = sector_bounds
        self.highlight_mode = "sector"  # "sector" 或 "bounds"
        self.setup_highlight()
    
    def setup_highlight(self):
        """设置高亮显示样式"""
        path = QPainterPath()
        
        if self.highlight_mode == "bounds" and self.sector_bounds:
            # 使用边界框模式
            min_x, min_y, max_x, max_y = self.sector_bounds
            rect = QRectF(min_x, min_y, max_x - min_x, max_y - min_y)
            path.addRect(rect)
        else:
            # 使用扇形模式
            self._create_sector_path(path)
        
        self.setPath(path)
        
        # 设置样式 - 淡黄色半透明
        pen = QPen(QColor(255, 200, 0, 180))  # 增加不透明度
        pen.setWidth(5)  # 增加线宽
        pen.setCosmetic(True)  # 设置为设备坐标，不受缩放影响
        self.setPen(pen)
        
        brush = QBrush(QColor(255, 235, 100, 80))  # 增加填充不透明度
        self.setBrush(brush)
        
        # 设置Z值确保高亮在孔位之上
        self.setZValue(100)
        
        # 默认不可见
        self.setVisible(False)
    
    def _create_sector_path(self, path: QPainterPath):
        """创建扇形路径"""
        # 根据扇形获取角度范围
        start_angle, end_angle = self._get_sector_angles()
        
        # 移动到中心点
        path.moveTo(self.center)
        
        # 创建扇形（使用弧线）
        rect = QRectF(
            self.center.x() - self.radius,
            self.center.y() - self.radius,
            self.radius * 2,
            self.radius * 2
        )
        
        # Qt使用16分之一度作为单位，逆时针为正
        # 需要进行坐标系转换
        qt_start_angle = -(start_angle - 90) * 16
        qt_span_angle = -90 * 16  # 每个扇形90度
        
        path.arcTo(rect, qt_start_angle, qt_span_angle)
        
        # 闭合路径
        path.closeSubpath()
    
    def _get_sector_angles(self) -> Tuple[float, float]:
        """
        获取扇形的起始和结束角度
        
        Returns:
            (start_angle, end_angle) 单位：度
        """
        # 扇形角度映射（数学坐标系）
        angle_map = {
            SectorQuadrant.SECTOR_1: (0, 90),      # 右上
            SectorQuadrant.SECTOR_2: (90, 180),    # 左上
            SectorQuadrant.SECTOR_3: (180, 270),   # 左下
            SectorQuadrant.SECTOR_4: (270, 360)    # 右下
        }
        
        angles = angle_map.get(self.sector, (0, 90))
        
        # 直接使用角度映射，不需要特殊处理
        start_angle, end_angle = angles
            
        return start_angle, end_angle
    
    def update_geometry(self, center: QPointF, radius: float):
        """更新几何信息"""
        self.center = center
        self.radius = radius
        self.setup_highlight()
    
    def set_highlight_mode(self, mode: str):
        """设置高亮模式"""
        if mode in ["sector", "bounds"]:
            self.highlight_mode = mode
            self.setup_highlight()
    
    def highlight(self, visible: bool = True):
        """显示或隐藏高亮"""
        self.setVisible(visible)
        
    def update_bounds(self, bounds: Tuple[float, float, float, float]):
        """更新扇形边界"""
        self.sector_bounds = bounds
        if self.highlight_mode == "bounds":
            self.setup_highlight()
            
    def contains_angle(self, angle: float) -> bool:
        """检查角度是否在扇形范围内"""
        # 归一化角度到 0-360
        angle = angle % 360
        if angle < 0:
            angle += 360
            
        start_angle, end_angle = self._get_sector_angles()
        
        # 处理跨越360度的情况
        if end_angle == 360 and angle < 90:
            angle += 360
            
        return start_angle <= angle < end_angle
    
    def get_info(self) -> dict:
        """获取高亮项信息"""
        return {
            'sector': self.sector.value,
            'center': (self.center.x(), self.center.y()),
            'radius': self.radius,
            'mode': self.highlight_mode,
            'visible': self.isVisible(),
            'bounds': self.sector_bounds
        }