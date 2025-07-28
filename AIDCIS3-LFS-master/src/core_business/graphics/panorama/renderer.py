"""
全景图渲染器实现
负责孔位和UI元素的渲染
"""

from typing import Dict, Any
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsLineItem
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPen, QBrush

from src.core_business.graphics.panorama.interfaces import IPanoramaRenderer
from src.core_business.models.hole_data import HoleData, HoleStatus


class PanoramaRenderer(IPanoramaRenderer):
    """全景图渲染器实现"""
    
    def __init__(self):
        # 默认主题配置
        self.theme_config = {
            'hole_colors': {
                HoleStatus.PENDING: QColor(169, 169, 169),      # 灰色
                HoleStatus.PROCESSING: QColor(255, 255, 0),     # 黄色
                HoleStatus.QUALIFIED: QColor(144, 238, 144),    # 绿色
                HoleStatus.DEFECTIVE: QColor(255, 99, 71),      # 红色
                HoleStatus.BLIND: QColor(135, 206, 235),        # 蓝色
                HoleStatus.TIE_ROD: QColor(128, 128, 128),      # 灰色
            },
            'divider_color': QColor(200, 200, 200, 100),
            'divider_width': 2,
            'hole_border_width': 1,
            'hole_border_color': QColor(80, 80, 80)
        }
    
    def render_holes(self, holes: Dict[str, HoleData], scene, hole_size: float) -> Dict[str, Any]:
        """
        渲染孔位
        
        Args:
            holes: 孔位数据字典
            scene: 图形场景
            hole_size: 孔位显示大小
            
        Returns:
            孔位图形项字典
        """
        hole_items = {}
        
        for hole_id, hole_data in holes.items():
            # 创建孔位图形项
            hole_item = self._create_hole_item(hole_data, hole_size)
            
            # 设置位置
            hole_item.setPos(hole_data.center_x, hole_data.center_y)
            
            # 设置Z值确保在最上层
            hole_item.setZValue(100)
            
            # 添加到场景
            scene.addItem(hole_item)
            
            # 保存引用
            hole_items[hole_id] = hole_item
        
        return hole_items
    
    def _create_hole_item(self, hole_data: HoleData, hole_size: float) -> QGraphicsEllipseItem:
        """
        创建单个孔位图形项
        
        Args:
            hole_data: 孔位数据
            hole_size: 显示大小
            
        Returns:
            孔位图形项
        """
        # 创建矩形（以原点为中心）
        rect = QRectF(-hole_size/2, -hole_size/2, hole_size, hole_size)
        
        # 创建椭圆项
        hole_item = QGraphicsEllipseItem(rect)
        
        # 设置填充颜色
        fill_color = self.theme_config['hole_colors'].get(
            hole_data.status, 
            self.theme_config['hole_colors'][HoleStatus.PENDING]
        )
        hole_item.setBrush(QBrush(fill_color))
        
        # 设置边框
        border_pen = QPen(
            self.theme_config['hole_border_color'],
            self.theme_config['hole_border_width']
        )
        hole_item.setPen(border_pen)
        
        # 设置工具提示
        hole_item.setToolTip(f"孔位: {hole_data.hole_id}\n状态: {hole_data.status.value}")
        
        return hole_item
    
    def render_sector_dividers(self, center: QPointF, radius: float, scene) -> None:
        """
        渲染扇区分隔线
        
        Args:
            center: 中心点
            radius: 半径
            scene: 图形场景
        """
        # 创建分隔线画笔
        divider_pen = QPen(
            self.theme_config['divider_color'],
            self.theme_config['divider_width']
        )
        divider_pen.setStyle(Qt.DashLine)
        
        # 水平分隔线
        h_line = QGraphicsLineItem(
            center.x() - radius, center.y(),
            center.x() + radius, center.y()
        )
        h_line.setPen(divider_pen)
        h_line.setZValue(50)
        scene.addItem(h_line)
        
        # 垂直分隔线
        v_line = QGraphicsLineItem(
            center.x(), center.y() - radius,
            center.x(), center.y() + radius
        )
        v_line.setPen(divider_pen)
        v_line.setZValue(50)
        scene.addItem(v_line)
    
    def apply_theme(self, theme_config: dict) -> None:
        """
        应用主题配置
        
        Args:
            theme_config: 主题配置字典
        """
        # 更新主题配置
        if 'hole_colors' in theme_config:
            self.theme_config['hole_colors'].update(theme_config['hole_colors'])
        
        if 'divider_color' in theme_config:
            self.theme_config['divider_color'] = theme_config['divider_color']
        
        if 'divider_width' in theme_config:
            self.theme_config['divider_width'] = theme_config['divider_width']
        
        if 'hole_border_width' in theme_config:
            self.theme_config['hole_border_width'] = theme_config['hole_border_width']
        
        if 'hole_border_color' in theme_config:
            self.theme_config['hole_border_color'] = theme_config['hole_border_color']
    
    def update_hole_color(self, hole_item: QGraphicsEllipseItem, status: HoleStatus) -> None:
        """
        更新孔位颜色
        
        Args:
            hole_item: 孔位图形项
            status: 新状态
        """
        fill_color = self.theme_config['hole_colors'].get(
            status, 
            self.theme_config['hole_colors'][HoleStatus.PENDING]
        )
        hole_item.setBrush(QBrush(fill_color))
    
    def get_theme_config(self) -> dict:
        """获取当前主题配置"""
        return self.theme_config.copy()