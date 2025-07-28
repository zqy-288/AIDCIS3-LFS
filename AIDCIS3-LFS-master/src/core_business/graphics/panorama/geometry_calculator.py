"""
全景图几何计算器实现
负责所有几何相关的计算，包括中心点、半径、缩放等
"""

import math
from typing import Dict
from PySide6.QtCore import QPointF
from src.core_business.graphics.panorama.interfaces import IPanoramaGeometryCalculator
from src.core_business.models.hole_data import HoleData


class PanoramaGeometryCalculator(IPanoramaGeometryCalculator):
    """几何计算器实现"""
    
    def __init__(self):
        # 基础半径范围配置
        self.min_hole_radius = 8.0   # 最小显示半径
        self.max_hole_radius = 16.0  # 最大显示半径
        self.margin_ratio = 1.2      # 边距比例
    
    def calculate_center(self, holes: Dict[str, HoleData]) -> QPointF:
        """
        计算中心点
        
        Args:
            holes: 孔位数据字典
            
        Returns:
            中心点坐标
        """
        if not holes:
            return QPointF(0, 0)
        
        # 计算所有孔位的平均位置
        sum_x = sum(hole.center_x for hole in holes.values())
        sum_y = sum(hole.center_y for hole in holes.values())
        count = len(holes)
        
        center_x = sum_x / count
        center_y = sum_y / count
        
        return QPointF(center_x, center_y)
    
    def calculate_radius(self, holes: Dict[str, HoleData], center: QPointF) -> float:
        """
        计算半径
        
        Args:
            holes: 孔位数据字典
            center: 中心点
            
        Returns:
            包含所有孔位的半径
        """
        if not holes:
            return 100.0  # 默认半径
        
        # 找出最远的孔位
        max_distance = 0.0
        
        for hole in holes.values():
            distance = math.sqrt(
                (hole.center_x - center.x()) ** 2 +
                (hole.center_y - center.y()) ** 2
            )
            max_distance = max(max_distance, distance)
        
        # 添加边距
        return max_distance * self.margin_ratio
    
    def calculate_hole_display_size(self, hole_count: int, radius: float, density: float) -> float:
        """
        计算孔位显示大小
        使用连续函数实现自适应缩放
        
        Args:
            hole_count: 孔位数量
            radius: 全景图半径
            density: 孔位密度
            
        Returns:
            最优显示半径（像素）
        """
        if hole_count <= 0:
            return self.max_hole_radius
        
        # 微小数据集特殊处理
        if hole_count <= 50:
            return self.max_hole_radius
        
        # 连续对数函数计算
        normalized_count = (hole_count - 50) / 30000
        log_factor = math.log(normalized_count * 5 + 1) / math.log(6)
        
        # 密度因子微调
        density_factor = min(0.5, density * 0.0005)
        
        # 计算半径缩减量
        radius_reduction = (self.max_hole_radius - self.min_hole_radius) * \
                          (log_factor * 0.7 + density_factor * 0.2)
        
        # 计算最终半径
        display_radius = self.max_hole_radius - radius_reduction
        
        # 确保在合理范围内
        return max(self.min_hole_radius, min(self.max_hole_radius, display_radius))
    
    def get_scale_factor(self, data_scale: str) -> float:
        """
        获取缩放因子
        
        Args:
            data_scale: 数据规模分类 ("small", "medium", "large", "massive")
            
        Returns:
            缩放因子
        """
        scale_factors = {
            "small": 1.5,     # 小数据集
            "medium": 1.3,    # 中等数据集
            "large": 1.2,     # 大数据集
            "massive": 1.1    # 超大数据集
        }
        
        return scale_factors.get(data_scale, 1.0)
    
    def calculate_data_density(self, hole_count: int, radius: float) -> float:
        """
        计算数据密度
        
        Args:
            hole_count: 孔位数量
            radius: 半径
            
        Returns:
            密度值
        """
        if radius <= 0:
            return hole_count / 1000000  # 备用密度
        
        area = math.pi * (radius ** 2)
        return hole_count / area
    
    def detect_data_scale(self, hole_count: int) -> str:
        """
        检测数据规模
        
        Args:
            hole_count: 孔位数量
            
        Returns:
            数据规模分类
        """
        if hole_count <= 100:
            return "small"
        elif hole_count <= 1000:
            return "medium"
        elif hole_count <= 10000:
            return "large"
        else:
            return "massive"