"""
扇形分配管理器
负责根据Qt坐标系正确分配孔位到对应扇形
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import Counter

from PySide6.QtCore import QObject, Signal, QPointF
from PySide6.QtGui import QColor

from src.core_business.models.hole_data import HoleData, HoleCollection
from src.core_business.graphics.sector_types import SectorQuadrant


@dataclass
class SectorInfo:
    """扇形信息"""
    sector: SectorQuadrant
    center_point: QPointF
    hole_count: int
    quadrant_definition: str
    color: QColor
    

class SectorAssignmentManager(QObject):
    """扇形分配管理器 - 处理Qt坐标系下的扇形分配"""
    
    # 信号
    sector_assignments_updated = Signal(dict)  # 扇形分配更新信号
    debug_info_updated = Signal(str)  # 调试信息更新信号
    
    def __init__(self):
        super().__init__()
        
        # 数据存储
        self.hole_collection: Optional[HoleCollection] = None
        self.sector_assignments: Dict[str, SectorQuadrant] = {}  # hole_id -> sector
        self.sector_info: Dict[SectorQuadrant, SectorInfo] = {}
        self.sector_center: Optional[QPointF] = None
        self.center_point: Optional[QPointF] = None  # 为兼容性添加
        
        # 扇形颜色配置
        self.sector_colors = {
            SectorQuadrant.SECTOR_1: QColor(76, 175, 80),   # 绿色 - 右上
            SectorQuadrant.SECTOR_2: QColor(33, 150, 243),  # 蓝色 - 左上
            SectorQuadrant.SECTOR_3: QColor(255, 152, 0),   # 橙色 - 左下
            SectorQuadrant.SECTOR_4: QColor(156, 39, 176),  # 紫色 - 右下
        }
        
        # Qt坐标系下的象限定义
        self.quadrant_definitions = {
            SectorQuadrant.SECTOR_1: "dx>=0, dy<=0 (Qt右上)",
            SectorQuadrant.SECTOR_2: "dx<0,  dy<=0 (Qt左上)",
            SectorQuadrant.SECTOR_3: "dx<0,  dy>0  (Qt左下)",
            SectorQuadrant.SECTOR_4: "dx>=0, dy>0  (Qt右下)"
        }
        
    def set_hole_collection(self, hole_collection: HoleCollection) -> None:
        """设置孔位集合并执行扇形分配"""
        self.hole_collection = hole_collection
        self._calculate_sector_center()
        self._perform_sector_assignment()
        self._generate_sector_info()
        self._emit_update_signal()
        
    def _calculate_sector_center(self) -> None:
        """计算扇形中心点"""
        if not self.hole_collection:
            return
            
        center_x = 0
        center_y = 0
        
        # 优先使用几何中心（如果有）
        geometric_center = getattr(self.hole_collection, 'geometric_center', None)
        
        if geometric_center:
            center_x, center_y = geometric_center
        else:
            # 使用边界计算中心
            if hasattr(self.hole_collection, 'get_bounds'):
                bounds = self.hole_collection.get_bounds()
                center_x = (bounds[0] + bounds[2]) / 2
                center_y = (bounds[1] + bounds[3]) / 2
            else:
                # 手动计算边界
                holes = list(self.hole_collection.holes.values())
                if holes:
                    min_x = min(h.center_x for h in holes)
                    max_x = max(h.center_x for h in holes)
                    min_y = min(h.center_y for h in holes)
                    max_y = max(h.center_y for h in holes)
                    center_x = (min_x + max_x) / 2
                    center_y = (min_y + max_y) / 2
                    
        self.sector_center = QPointF(center_x, center_y)
        self.center_point = self.sector_center  # 保持兼容性
            
        print(f"计算中心点: ({center_x}, {center_y}), sector_center设置为: {self.sector_center}")
            
    def _perform_sector_assignment(self) -> None:
        """执行扇形分配 - 考虑Qt坐标系"""
        if not self.hole_collection:
            print("警告：无法执行扇形分配，缺少孔位集合")
            return
        if self.sector_center is None:
            print(f"警告：无法执行扇形分配，缺少中心点。sector_center={self.sector_center}")
            return
            
        self.sector_assignments.clear()
        center_x = self.sector_center.x()
        center_y = self.sector_center.y()
        
        print(f"开始扇形分配，中心点: ({center_x}, {center_y})")
        
        for hole_id, hole in self.hole_collection.holes.items():
            # 计算相对坐标
            dx = hole.center_x - center_x
            dy = hole.center_y - center_y
            
            # 确定扇形（考虑Qt坐标系Y轴向下）
            # 在数据中 y>0 表示上方，但在Qt显示中会在下方
            if dx >= 0 and dy <= 0:
                sector = SectorQuadrant.SECTOR_1  # Qt显示的右上（y<0在屏幕上方）
            elif dx < 0 and dy <= 0:
                sector = SectorQuadrant.SECTOR_2  # Qt显示的左上（y<0在屏幕上方）
            elif dx < 0 and dy > 0:
                sector = SectorQuadrant.SECTOR_3  # Qt显示的左下（y>0在屏幕下方）
            else:  # dx >= 0 and dy > 0
                sector = SectorQuadrant.SECTOR_4  # Qt显示的右下（y>0在屏幕下方）
                
            self.sector_assignments[hole_id] = sector
            
        print(f"扇形分配完成，总共分配了 {len(self.sector_assignments)} 个孔位")
            
    def _generate_sector_info(self) -> None:
        """生成扇形信息"""
        sector_counts = Counter(self.sector_assignments.values())
        
        for sector in SectorQuadrant:
            self.sector_info[sector] = SectorInfo(
                sector=sector,
                center_point=self.sector_center,
                hole_count=sector_counts.get(sector, 0),
                quadrant_definition=self.quadrant_definitions[sector],
                color=self.sector_colors[sector]
            )
            
    def _emit_update_signal(self) -> None:
        """发射更新信号"""
        sector_counts = Counter(self.sector_assignments.values())
        update_data = {
            'sector_counts': {s.value: c for s, c in sector_counts.items()},
            'sector_info': {
                s.value: {
                    'hole_count': info.hole_count,
                    'quadrant_definition': info.quadrant_definition,
                    'center_point': (info.center_point.x(), info.center_point.y()) if info.center_point else None,
                    'color': info.color.name()
                } for s, info in self.sector_info.items()
            },
            'total_holes': len(self.hole_collection.holes) if self.hole_collection else 0
        }
        
        self.sector_assignments_updated.emit(update_data)
        
    def get_hole_sector(self, hole_id: str) -> Optional[SectorQuadrant]:
        """获取孔位所属扇形"""
        return self.sector_assignments.get(hole_id)
        
    def get_sector_holes(self, sector: SectorQuadrant) -> List[HoleData]:
        """获取指定扇形的所有孔位"""
        if not self.hole_collection:
            return []
            
        return [
            self.hole_collection.holes[hole_id]
            for hole_id, assigned_sector in self.sector_assignments.items()
            if assigned_sector == sector and hole_id in self.hole_collection.holes
        ]
        
    def get_sector_count(self, sector: SectorQuadrant) -> int:
        """获取指定扇形的孔位数量"""
        return sum(1 for s in self.sector_assignments.values() if s == sector)
        
    def get_all_sector_counts(self) -> Dict[SectorQuadrant, int]:
        """获取所有扇形的孔位数量"""
        return dict(Counter(self.sector_assignments.values()))
    
    def get_holes_by_sector(self, sector: SectorQuadrant) -> List[HoleData]:
        """获取指定扇形的所有孔位（get_sector_holes的别名）"""
        return self.get_sector_holes(sector)
        
    def get_sector_info(self, sector: SectorQuadrant) -> Optional[SectorInfo]:
        """获取扇形信息"""
        info = self.sector_info.get(sector)
        if info:
            # 返回字典格式以保持兼容性
            holes = self.get_sector_holes(sector)
            sample_holes = [{
                'hole_id': hole.hole_id,
                'center_x': hole.center_x,
                'center_y': hole.center_y
            } for hole in holes[:5]]  # 前5个作为样本
            
            return {
                'quadrant_definition': info.quadrant_definition,
                'sample_holes': sample_holes,
                'hole_count': info.hole_count
            }
        return None
        
    def get_all_sector_info(self) -> Dict[SectorQuadrant, SectorInfo]:
        """获取所有扇形信息"""
        result = {}
        for sector in SectorQuadrant:
            info = self.get_sector_info(sector)
            if info:
                result[sector] = info
        return result
        
    def enable_debug(self, enabled: bool = True) -> None:
        """启用/禁用调试模式"""
        if enabled:
            self.debug_info_updated.emit("调试模式已启用")
    
    def clear(self) -> None:
        """清空所有数据"""
        self.hole_collection = None
        self.sector_assignments.clear()
        self.sector_info.clear()
        self.sector_center = None
        self.center_point = None