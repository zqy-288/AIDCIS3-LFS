"""
管孔数据模型
定义管孔的基本数据结构
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum


class HoleStatus(Enum):
    """管孔状态枚举"""
    PENDING = "pending"      # 待检
    QUALIFIED = "qualified"  # 合格
    DEFECTIVE = "defective"  # 异常
    BLIND = "blind"          # 盲孔
    TIE_ROD = "tie_rod"     # 拉杆孔
    PROCESSING = "processing" # 检测中


@dataclass
class HoleData:
    """管孔数据类"""
    hole_id: str                    # 孔的唯一标识
    center_x: float                 # 中心X坐标
    center_y: float                 # 中心Y坐标
    radius: float                   # 半径
    status: HoleStatus = HoleStatus.PENDING  # 状态
    layer: str = "0"               # DXF图层
    row: Optional[int] = None      # 行号
    column: Optional[int] = None   # 列号
    region: Optional[str] = None   # 区域编号
    metadata: Optional[Dict[str, Any]] = None  # 额外元数据
    
    def __post_init__(self):
        """初始化后处理"""
        if self.metadata is None:
            self.metadata = {}
        
        # 生成默认ID（如果未提供）
        if not self.hole_id:
            self.hole_id = f"hole_{self.center_x:.3f}_{self.center_y:.3f}"
    
    @property
    def position(self) -> tuple[float, float]:
        """返回位置坐标元组"""
        return (self.center_x, self.center_y)
    
    def distance_to(self, other: 'HoleData') -> float:
        """计算到另一个孔的距离"""
        import math
        dx = self.center_x - other.center_x
        dy = self.center_y - other.center_y
        return math.sqrt(dx * dx + dy * dy)
    
    def is_near(self, x: float, y: float, tolerance: float = 1.0) -> bool:
        """判断是否在指定位置附近"""
        import math
        dx = self.center_x - x
        dy = self.center_y - y
        distance = math.sqrt(dx * dx + dy * dy)
        return distance <= tolerance
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'hole_id': self.hole_id,
            'center_x': self.center_x,
            'center_y': self.center_y,
            'radius': self.radius,
            'status': self.status.value,
            'layer': self.layer,
            'row': self.row,
            'column': self.column,
            'region': self.region,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HoleData':
        """从字典创建实例"""
        status = HoleStatus(data.get('status', HoleStatus.PENDING.value))
        return cls(
            hole_id=data['hole_id'],
            center_x=data['center_x'],
            center_y=data['center_y'],
            radius=data['radius'],
            status=status,
            layer=data.get('layer', '0'),
            row=data.get('row'),
            column=data.get('column'),
            region=data.get('region'),
            metadata=data.get('metadata', {})
        )


@dataclass
class HoleCollection:
    """管孔集合类"""
    holes: Dict[str, HoleData]      # 孔数据字典，key为hole_id
    total_count: int = 0            # 总数量
    metadata: Optional[Dict[str, Any]] = None  # 集合元数据
    
    def __post_init__(self):
        """初始化后处理"""
        if self.metadata is None:
            self.metadata = {}
        self.total_count = len(self.holes)
    
    def add_hole(self, hole: HoleData) -> None:
        """添加孔"""
        self.holes[hole.hole_id] = hole
        self.total_count = len(self.holes)
    
    def get_hole(self, hole_id: str) -> Optional[HoleData]:
        """获取指定孔"""
        return self.holes.get(hole_id)
    
    def get_holes_by_status(self, status: HoleStatus) -> list[HoleData]:
        """按状态获取孔列表"""
        return [hole for hole in self.holes.values() if hole.status == status]
    
    def get_holes_in_region(self, region: str) -> list[HoleData]:
        """获取指定区域的孔"""
        return [hole for hole in self.holes.values() if hole.region == region]
    
    def find_holes_near(self, x: float, y: float, radius: float) -> list[HoleData]:
        """查找指定位置附近的孔"""
        return [hole for hole in self.holes.values() 
                if hole.is_near(x, y, radius)]
    
    def get_status_counts(self) -> Dict[HoleStatus, int]:
        """获取各状态的数量统计"""
        counts = {status: 0 for status in HoleStatus}
        for hole in self.holes.values():
            counts[hole.status] += 1
        return counts
    
    def get_bounds(self) -> tuple[float, float, float, float]:
        """获取边界框 (min_x, min_y, max_x, max_y)"""
        if not self.holes:
            return (0, 0, 0, 0)
        
        x_coords = [hole.center_x for hole in self.holes.values()]
        y_coords = [hole.center_y for hole in self.holes.values()]
        
        return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))
    
    def clear(self) -> None:
        """清空所有孔"""
        self.holes.clear()
        self.total_count = 0
    
    def __len__(self) -> int:
        """返回孔的数量"""
        return len(self.holes)
    
    def __iter__(self):
        """迭代器"""
        return iter(self.holes.values())
    
    def __contains__(self, hole_id: str) -> bool:
        """检查是否包含指定孔"""
        return hole_id in self.holes
