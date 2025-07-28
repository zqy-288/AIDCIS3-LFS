"""
管孔数据模型
定义管孔的基本数据结构
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Tuple
from enum import Enum
from functools import lru_cache
from datetime import datetime


# AI员工1号修改开始 - 2025-01-14
# 修改目的：添加标准孔位ID转换函数
def convert_hole_id(row: int, column: int) -> str:
    """标准转换函数"""
    return f"C{column:03d}R{row:03d}"
# AI员工1号修改结束


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
    # 必需字段（无默认值）
    center_x: float                 # 中心X坐标
    center_y: float                 # 中心Y坐标
    radius: float                   # 半径
    # 可选字段（有默认值）
    hole_id: Optional[str] = None   # 孔的唯一标识（可选，由HoleNumberingService生成）
    status: HoleStatus = HoleStatus.PENDING  # 状态
    layer: str = "0"               # DXF图层
    row: Optional[int] = None      # 行号
    column: Optional[int] = None   # 列号
    region: Optional[str] = None   # 区域编号
    metadata: Optional[Dict[str, Any]] = None  # 额外元数据
    
    # 缓存字段
    _cached_position: Optional[Tuple[float, float]] = field(default=None, init=False, repr=False)
    _cached_diameter: Optional[float] = field(default=None, init=False, repr=False)
    _last_modified: Optional[datetime] = field(default=None, init=False, repr=False)
    
    def __post_init__(self):
        """初始化后处理"""
        if self.metadata is None:
            self.metadata = {}
        
        # 不再自动生成ID，由HoleNumberingService负责
        # hole_id现在是可选的，初始时可以为None
    
    @property
    def position(self) -> tuple[float, float]:
        """返回位置坐标元组 - 缓存优化版本"""
        if self._cached_position is None:
            self._cached_position = (self.center_x, self.center_y)
        return self._cached_position
    
    @property
    def diameter(self) -> float:
        """返回直径 - 缓存优化版本"""
        if self._cached_diameter is None:
            self._cached_diameter = self.radius * 2
        return self._cached_diameter
    
    @lru_cache(maxsize=1000)
    def distance_to(self, other: 'HoleData') -> float:
        """计算到另一个孔的距离 - LRU缓存优化"""
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
        
        # 恢复时间戳
        if 'last_modified' in data and data['last_modified']:
            instance._last_modified = datetime.fromisoformat(data['last_modified'])
        
        return instance
    
    def update_position(self, x: float, y: float) -> None:
        """更新位置并invalidate缓存"""
        self.center_x = x
        self.center_y = y
        self._invalidate_cache()
    
    def update_radius(self, radius: float) -> None:
        """更新半径并invalidate缓存"""
        self.radius = radius
        self._invalidate_cache()
    
    def _invalidate_cache(self) -> None:
        """使缓存失效"""
        self._cached_position = None
        self._cached_diameter = None
        self._last_modified = datetime.now()
        
        # 清除LRU缓存
        if hasattr(self.distance_to, 'cache_clear'):
            self.distance_to.cache_clear()
    
    def get_performance_info(self) -> Dict[str, Any]:
        """获取性能信息"""
        cache_info = {}
        if hasattr(self.distance_to, 'cache_info'):
            cache_info['distance_cache'] = self.distance_to.cache_info()._asdict()
        
        return {
            'cache_info': cache_info,
            'cached_fields': {
                'position_cached': self._cached_position is not None,
                'diameter_cached': self._cached_diameter is not None
            },
            'last_modified': self._last_modified.isoformat() if self._last_modified else None
        }
    
    def __hash__(self):
        """哈希函数用于缓存 - 优化版本"""
        return hash((self.hole_id, self.center_x, self.center_y, self.radius))
    
    def __eq__(self, other):
        """相等比较 - 优化版本"""
        if not isinstance(other, HoleData):
            return False
        return (
            self.hole_id == other.hole_id and
            abs(self.center_x - other.center_x) < 1e-6 and
            abs(self.center_y - other.center_y) < 1e-6 and
            abs(self.radius - other.radius) < 1e-6
        )
    
    def __str__(self):
        """简洁的字符串表示"""
        return f"Hole[{self.hole_id}@({self.center_x:.1f},{self.center_y:.1f})-{self.status.value}]"
    
    def __repr__(self):
        """根据配置返回详细或简洁的表示"""
        # 检查是否启用详细模式
        try:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
            from debug_config import get_debug_setting
            if get_debug_setting('hole_details', False):
                # 详细模式：显示所有字段
                return (f"HoleData(hole_id='{self.hole_id}', center_x={self.center_x}, "
                       f"center_y={self.center_y}, radius={self.radius}, status={self.status}, "
                       f"layer='{self.layer}', row={self.row}, column={self.column}, "
                       f"region={self.region}, metadata={self.metadata})")
            else:
                # 简洁模式：只显示关键信息
                return str(self)
        except ImportError:
            # 如果没有debug_config模块，使用简洁模式
            return str(self)
    
    def get_summary(self) -> str:
        """获取摘要信息"""
        position_str = f"({self.center_x:.1f},{self.center_y:.1f})"
        if self.row is not None and self.column is not None:
            position_str += f"[R{self.row}C{self.column}]"
        return f"{self.hole_id}@{position_str}-{self.status.value}"
    
    def get_detailed_info(self) -> str:
        """获取详细信息"""
        return (f"HoleData: {self.hole_id}\n"
               f"  Position: ({self.center_x:.3f}, {self.center_y:.3f})\n"
               f"  Radius: {self.radius:.3f}\n"
               f"  Status: {self.status.value}\n"
               f"  Layer: {self.layer}\n"
               f"  Grid: Row={self.row}, Column={self.column}\n"
               f"  Region: {self.region}\n"
               f"  Metadata: {self.metadata}")


@dataclass
class HoleCollection:
    """管孔集合类 - 空间索引优化版本"""
    holes: Dict[str, HoleData]      # 孔数据字典，key为hole_id
    total_count: int = 0            # 总数量
    metadata: Optional[Dict[str, Any]] = None  # 集合元数据
    
    # 空间索引缓存
    _spatial_index: Optional[Dict[str, Any]] = field(default=None, init=False, repr=False)
    _bounds_cache: Optional[Tuple[float, float, float, float]] = field(default=None, init=False, repr=False)
    
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
    
    def __str__(self) -> str:
        """简洁的字符串表示"""
        status_counts = self.get_status_counts()
        status_summary = ", ".join([f"{status.value}:{count}" for status, count in status_counts.items() if count > 0])
        return f"HoleCollection[{len(self.holes)} holes: {status_summary}]"
    
    def __repr__(self) -> str:
        """根据配置返回详细或简洁的表示"""
        try:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
            from debug_config import get_debug_setting
            if get_debug_setting('hole_details', False):
                # 详细模式：显示前几个孔位的详细信息
                sample_holes = list(self.holes.values())[:3]
                holes_repr = [repr(hole) for hole in sample_holes]
                if len(self.holes) > 3:
                    holes_repr.append(f"... and {len(self.holes) - 3} more holes")
                return f"HoleCollection(holes={{{', '.join(holes_repr)}}}, total_count={self.total_count})"
            else:
                # 简洁模式
                return str(self)
        except ImportError:
            # 如果没有debug_config模块，使用简洁模式
            return str(self)
    
    def get_summary(self) -> str:
        """获取摘要信息"""
        if not self.holes:
            return "Empty HoleCollection"
        
        status_counts = self.get_status_counts()
        bounds = self.get_bounds()
        
        return (f"HoleCollection Summary:\n"
               f"  Total holes: {len(self.holes)}\n"
               f"  Status distribution: {dict(status_counts)}\n"
               f"  Bounds: ({bounds[0]:.1f}, {bounds[1]:.1f}) to ({bounds[2]:.1f}, {bounds[3]:.1f})\n"
               f"  Area: {(bounds[2] - bounds[0]):.1f} × {(bounds[3] - bounds[1]):.1f}")
