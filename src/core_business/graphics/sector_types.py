"""
扇形相关的类型定义
包含枚举、数据类等基础类型
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Tuple
from PySide6.QtGui import QColor


class SectorQuadrant(Enum):
    """扇形象限枚举"""
    SECTOR_1 = "sector_1"  # 右上 (0°-90°)
    SECTOR_2 = "sector_2"  # 左上 (90°-180°)
    SECTOR_3 = "sector_3"  # 左下 (180°-270°)
    SECTOR_4 = "sector_4"  # 右下 (270°-360°)
    
    @property
    def display_name(self) -> str:
        """获取显示名称"""
        names = {
            "sector_1": "扇形1 (右上)",
            "sector_2": "扇形2 (左上)",
            "sector_3": "扇形3 (左下)",
            "sector_4": "扇形4 (右下)"
        }
        return names.get(self.value, self.value)
    
    @property
    def angle_range(self) -> Tuple[float, float]:
        """获取扇形的角度范围（度）"""
        ranges = {
            "sector_1": (0, 90),      # 第一象限
            "sector_2": (90, 180),    # 第二象限
            "sector_3": (180, 270),   # 第三象限
            "sector_4": (270, 360)    # 第四象限
        }
        return ranges.get(self.value, (0, 90))
    
    @classmethod
    def from_angle(cls, angle: float) -> 'SectorQuadrant':
        """根据角度获取扇形象限"""
        # 归一化角度到 0-360 范围
        angle = angle % 360
        if angle < 0:
            angle += 360
            
        if 0 <= angle < 90:
            return cls.SECTOR_1
        elif 90 <= angle < 180:
            return cls.SECTOR_2
        elif 180 <= angle < 270:
            return cls.SECTOR_3
        else:
            return cls.SECTOR_4
    
    @classmethod
    def from_position(cls, x: float, y: float, center_x: float, center_y: float) -> 'SectorQuadrant':
        """根据位置相对于中心点确定扇形象限"""
        if x >= center_x and y < center_y:
            return cls.SECTOR_1
        elif x < center_x and y < center_y:
            return cls.SECTOR_2
        elif x < center_x and y >= center_y:
            return cls.SECTOR_3
        else:  # x >= center_x and y >= center_y
            return cls.SECTOR_4


@dataclass
class SectorProgress:
    """扇形进度数据类 - 完整版本（合并自 coordinate_system.py）"""
    sector: SectorQuadrant
    total_holes: int = 0
    completed_holes: int = 0
    qualified_holes: int = 0
    defective_holes: int = 0
    progress_percentage: float = 0.0
    status_color: Optional[QColor] = None
    
    # 保留原有的简化属性名，用于兼容性
    @property
    def completed(self) -> int:
        """兼容属性：已完成数"""
        return self.completed_holes
    
    @property
    def total(self) -> int:
        """兼容属性：总数"""
        return self.total_holes
    
    @property
    def percentage(self) -> float:
        """计算完成百分比"""
        if self.total_holes == 0:
            return 0.0
        return (self.completed_holes / self.total_holes) * 100
    
    @property
    def completion_rate(self) -> float:
        """完成率"""
        return (self.completed_holes / self.total_holes * 100) if self.total_holes > 0 else 0.0
    
    @property
    def qualification_rate(self) -> float:
        """合格率"""
        return (self.qualified_holes / self.completed_holes * 100) if self.completed_holes > 0 else 0.0
    
    @property
    def is_completed(self) -> bool:
        """是否已完成"""
        return self.completed_holes >= self.total_holes and self.total_holes > 0
    
    def increment(self):
        """增加完成数"""
        if self.completed_holes < self.total_holes:
            self.completed_holes += 1
            
    def reset(self):
        """重置进度"""
        self.completed_holes = 0
        self.qualified_holes = 0
        self.defective_holes = 0
        self.progress_percentage = 0.0
        
    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.completed_holes}/{self.total_holes} ({self.percentage:.1f}%)"


@dataclass
class SectorBounds:
    """扇形边界数据"""
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    
    @property
    def width(self) -> float:
        """宽度"""
        return self.max_x - self.min_x
    
    @property
    def height(self) -> float:
        """高度"""
        return self.max_y - self.min_y
    
    @property
    def center(self) -> Tuple[float, float]:
        """中心点"""
        return ((self.min_x + self.max_x) / 2, (self.min_y + self.max_y) / 2)
    
    def contains_point(self, x: float, y: float) -> bool:
        """检查点是否在边界内"""
        return self.min_x <= x <= self.max_x and self.min_y <= y <= self.max_y
    
    def expand(self, margin: float):
        """扩展边界"""
        self.min_x -= margin
        self.min_y -= margin
        self.max_x += margin
        self.max_y += margin
        
    def to_tuple(self) -> Tuple[float, float, float, float]:
        """转换为元组"""
        return (self.min_x, self.min_y, self.max_x, self.max_y)