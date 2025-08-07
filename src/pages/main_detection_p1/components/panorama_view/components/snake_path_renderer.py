"""
蛇形路径渲染器实现
负责计算和渲染蛇形路径
"""

from typing import List, Tuple, Dict, Any
from PySide6.QtWidgets import QGraphicsLineItem, QGraphicsPathItem
from PySide6.QtCore import QObject, Qt
from PySide6.QtGui import QPen, QColor, QPainterPath

from ..core.interfaces import ISnakePathRenderer
from src.shared.models.hole_data import HoleData


class SnakePathRenderer(QObject):
    """蛇形路径渲染器实现"""
    
    def __init__(self):
        super().__init__()
        
        # 路径配置
        self.enabled = False
        self.current_strategy = "hybrid"
        self.current_style = "simple_line"
        
        # 渲染配置
        self.path_config = {
            'simple_line': {
                'color': QColor(255, 0, 0, 180),  # 半透明红色
                'width': 2,
                'z_value': 75
            },
            'arrow_line': {
                'color': QColor(0, 0, 255, 180),  # 半透明蓝色
                'width': 3,
                'z_value': 75
            },
            'dashed_line': {
                'color': QColor(0, 255, 0, 180),  # 半透明绿色
                'width': 2,
                'z_value': 75
            }
        }
        
        # 当前路径项列表
        self.path_items: List[Any] = []
    
    def calculate_path(self, holes: List[HoleData], strategy: str) -> List[Tuple[float, float]]:
        """
        计算蛇形路径
        
        Args:
            holes: 孔位数据列表
            strategy: 路径策略 ("linear", "zigzag", "hybrid")
            
        Returns:
            路径点列表
        """
        if not holes:
            return []
        
        self.current_strategy = strategy
        
        if strategy == "linear":
            return self._calculate_linear_path(holes)
        elif strategy == "zigzag":
            return self._calculate_zigzag_path(holes)
        elif strategy == "hybrid":
            return self._calculate_hybrid_path(holes)
        else:
            return self._calculate_linear_path(holes)  # 默认策略
    
    def _calculate_linear_path(self, holes: List[HoleData]) -> List[Tuple[float, float]]:
        """计算线性路径"""
        # 简单的按ID排序路径
        sorted_holes = sorted(holes, key=lambda h: h.hole_id)
        return [(hole.center_x, hole.center_y) for hole in sorted_holes]
    
    def _calculate_zigzag_path(self, holes: List[HoleData]) -> List[Tuple[float, float]]:
        """计算Z字形路径"""
        # 按Y坐标分组，然后交替排序
        holes_by_row = {}
        for hole in holes:
            row = int(hole.center_y // 50)  # 假设每50像素一行
            if row not in holes_by_row:
                holes_by_row[row] = []
            holes_by_row[row].append(hole)
        
        path = []
        for i, row in enumerate(sorted(holes_by_row.keys())):
            row_holes = holes_by_row[row]
            if i % 2 == 0:
                # 偶数行：从左到右
                row_holes.sort(key=lambda h: h.center_x)
            else:
                # 奇数行：从右到左
                row_holes.sort(key=lambda h: h.center_x, reverse=True)
            
            for hole in row_holes:
                path.append((hole.center_x, hole.center_y))
        
        return path
    
    def _calculate_hybrid_path(self, holes: List[HoleData]) -> List[Tuple[float, float]]:
        """计算混合路径（结合距离和效率的优化路径）"""
        if not holes:
            return []
        
        # 使用贪心算法找到相对较短的路径
        unvisited = holes.copy()
        path = []
        
        # 从第一个孔位开始
        current = unvisited.pop(0)
        path.append((current.center_x, current.center_y))
        
        while unvisited:
            # 找到距离当前位置最近的孔位
            min_distance = float('inf')
            next_hole = None
            next_index = -1
            
            for i, hole in enumerate(unvisited):
                distance = ((hole.center_x - current.center_x) ** 2 + 
                           (hole.center_y - current.center_y) ** 2) ** 0.5
                if distance < min_distance:
                    min_distance = distance
                    next_hole = hole
                    next_index = i
            
            if next_hole:
                unvisited.pop(next_index)
                current = next_hole
                path.append((current.center_x, current.center_y))
        
        return path
    
    def render_path(self, path: List[Tuple[float, float]], scene, style: str) -> None:
        """
        渲染路径
        
        Args:
            path: 路径点列表
            scene: 图形场景
            style: 渲染样式
        """
        if not self.enabled or not path or len(path) < 2:
            return
        
        # 清除旧路径
        self._clear_path_items(scene)
        
        self.current_style = style
        
        if style == "simple_line":
            self._render_simple_line(path, scene)
        elif style == "arrow_line":
            self._render_arrow_line(path, scene)
        elif style == "dashed_line":
            self._render_dashed_line(path, scene)
        else:
            self._render_simple_line(path, scene)  # 默认样式
    
    def _render_simple_line(self, path: List[Tuple[float, float]], scene):
        """渲染简单线条"""
        config = self.path_config['simple_line']
        pen = QPen(config['color'], config['width'])
        
        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i + 1]
            
            line_item = QGraphicsLineItem(x1, y1, x2, y2)
            line_item.setPen(pen)
            line_item.setZValue(config['z_value'])
            
            scene.addItem(line_item)
            self.path_items.append(line_item)
    
    def _render_arrow_line(self, path: List[Tuple[float, float]], scene):
        """渲染带箭头的线条"""
        config = self.path_config['arrow_line']
        pen = QPen(config['color'], config['width'])
        
        # 创建路径
        painter_path = QPainterPath()
        if path:
            painter_path.moveTo(path[0][0], path[0][1])
            for x, y in path[1:]:
                painter_path.lineTo(x, y)
        
        path_item = QGraphicsPathItem(painter_path)
        path_item.setPen(pen)
        path_item.setZValue(config['z_value'])
        
        scene.addItem(path_item)
        self.path_items.append(path_item)
    
    def _render_dashed_line(self, path: List[Tuple[float, float]], scene):
        """渲染虚线"""
        config = self.path_config['dashed_line']
        pen = QPen(config['color'], config['width'])
        pen.setStyle(Qt.DashLine)
        
        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i + 1]
            
            line_item = QGraphicsLineItem(x1, y1, x2, y2)
            line_item.setPen(pen)
            line_item.setZValue(config['z_value'])
            
            scene.addItem(line_item)
            self.path_items.append(line_item)
    
    def _clear_path_items(self, scene):
        """清除路径项"""
        for item in self.path_items:
            if item.scene():
                scene.removeItem(item)
        self.path_items.clear()
    
    def set_enabled(self, enabled: bool) -> None:
        """
        设置是否启用
        
        Args:
            enabled: 是否启用
        """
        self.enabled = enabled
        
        if not enabled:
            # 禁用时清除所有路径项
            for item in self.path_items:
                if item.scene():
                    item.scene().removeItem(item)
            self.path_items.clear()
    
    def set_path_style(self, style: str, config: Dict[str, Any]):
        """
        设置路径样式配置
        
        Args:
            style: 样式名称
            config: 样式配置
        """
        if style in self.path_config:
            self.path_config[style].update(config)
    
    def get_path_length(self, path: List[Tuple[float, float]]) -> float:
        """
        计算路径总长度
        
        Args:
            path: 路径点列表
            
        Returns:
            路径长度
        """
        if len(path) < 2:
            return 0.0
        
        total_length = 0.0
        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i + 1]
            distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
            total_length += distance
        
        return total_length