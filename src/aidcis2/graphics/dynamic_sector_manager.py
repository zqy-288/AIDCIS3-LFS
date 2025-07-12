"""
动态扇形区域管理器
支持根据产品配置动态设置扇形数量（2、4、6、8等）
"""

import math
from enum import Enum
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal, QPointF
from PySide6.QtGui import QColor

from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus


class DynamicSectorQuadrant:
    """动态扇形象限类"""
    def __init__(self, index: int, total_sectors: int):
        self.index = index
        self.total_sectors = total_sectors
        self.name = f"sector_{index + 1}"
        self.value = self.name
        
        # 计算角度范围
        angle_per_sector = 360.0 / total_sectors
        self.start_angle = index * angle_per_sector
        self.end_angle = (index + 1) * angle_per_sector
        
    def __str__(self):
        return self.name
        
    def __eq__(self, other):
        if isinstance(other, DynamicSectorQuadrant):
            return self.name == other.name
        return False
        
    def __hash__(self):
        return hash(self.name)


@dataclass
class DynamicSectorProgress:
    """动态区域划分进度数据"""
    sector: DynamicSectorQuadrant
    total_holes: int
    completed_holes: int
    qualified_holes: int
    defective_holes: int
    progress_percentage: float
    status_color: QColor
    
    @property
    def completion_rate(self) -> float:
        """完成率"""
        return (self.completed_holes / self.total_holes * 100) if self.total_holes > 0 else 0.0
    
    @property
    def qualification_rate(self) -> float:
        """合格率"""
        return (self.qualified_holes / self.completed_holes * 100) if self.completed_holes > 0 else 0.0


class DynamicSectorManager(QObject):
    """动态扇形区域管理器"""
    
    # 信号
    sector_progress_updated = Signal(object, object)  # DynamicSectorQuadrant, DynamicSectorProgress
    overall_progress_updated = Signal(dict)  # 整体进度更新
    sector_count_changed = Signal(int)  # 扇形数量变化
    
    # 预定义的颜色方案（最多支持12个扇形）
    SECTOR_COLORS = [
        QColor(76, 175, 80),    # 绿色
        QColor(33, 150, 243),   # 蓝色
        QColor(255, 152, 0),    # 橙色
        QColor(156, 39, 176),   # 紫色
        QColor(255, 87, 34),    # 深橙色
        QColor(0, 188, 212),    # 青色
        QColor(255, 193, 7),    # 琥珀色
        QColor(96, 125, 139),   # 蓝灰色
        QColor(205, 220, 57),   # 黄绿色
        QColor(121, 85, 72),    # 棕色
        QColor(244, 67, 54),    # 红色
        QColor(63, 81, 181),    # 靛蓝色
    ]
    
    def __init__(self, sector_count: int = 4, parent=None):
        super().__init__(parent)
        # 验证扇形数量
        if sector_count < 2 or sector_count > 12:
            raise ValueError(f"扇形数量必须在2-12之间，当前值: {sector_count}")
        
        self.sector_count = sector_count
        self.hole_collection: Optional[HoleCollection] = None
        self.center_point: Optional[QPointF] = None
        self.sectors: List[DynamicSectorQuadrant] = []
        self.sector_assignments: Dict[str, DynamicSectorQuadrant] = {}  # hole_id -> sector
        self.sector_progresses: Dict[DynamicSectorQuadrant, DynamicSectorProgress] = {}
        
        # 初始化扇形
        self._initialize_sectors()
    
    def _initialize_sectors(self):
        """初始化扇形列表"""
        self.sectors = []
        for i in range(self.sector_count):
            sector = DynamicSectorQuadrant(i, self.sector_count)
            self.sectors.append(sector)
    
    def set_sector_count(self, count: int):
        """设置扇形数量"""
        if count < 2 or count > 12:
            raise ValueError(f"扇形数量必须在2-12之间，当前值: {count}")
        
        if count != self.sector_count:
            self.sector_count = count
            self._initialize_sectors()
            
            # 如果已经加载了孔位数据，重新进行分配
            if self.hole_collection:
                self._assign_holes_to_sectors()
                self._initialize_sector_progress()
            
            self.sector_count_changed.emit(count)
    
    def get_sector_color(self, sector: DynamicSectorQuadrant) -> QColor:
        """获取扇形颜色"""
        color_index = sector.index % len(self.SECTOR_COLORS)
        return self.SECTOR_COLORS[color_index]
    
    def load_hole_collection(self, hole_collection: HoleCollection):
        """加载孔位集合并进行扇形划分"""
        self.hole_collection = hole_collection
        
        # 计算管板中心点
        self.center_point = self._calculate_center_point()
        
        # 执行扇形划分
        self._assign_holes_to_sectors()
        
        # 初始化进度统计
        self._initialize_sector_progress()
    
    def _calculate_center_point(self) -> QPointF:
        """计算管板的几何中心点"""
        if not self.hole_collection:
            return QPointF(0, 0)
        
        bounds = self.hole_collection.get_bounds()
        center_x = (bounds[0] + bounds[2]) / 2
        center_y = (bounds[1] + bounds[3]) / 2
        
        return QPointF(center_x, center_y)
    
    def _assign_holes_to_sectors(self):
        """将孔位分配到对应的扇形区域"""
        if not self.hole_collection or self.center_point is None:
            return
        
        self.sector_assignments.clear()
        
        for hole in self.hole_collection.holes.values():
            sector = self._get_hole_sector(hole)
            self.sector_assignments[hole.hole_id] = sector
    
    def _get_hole_sector(self, hole: HoleData) -> DynamicSectorQuadrant:
        """根据孔位坐标确定所属扇形"""
        # 计算相对于中心点的角度
        dx = hole.center_x - self.center_point.x()
        dy = hole.center_y - self.center_point.y()
        
        # 计算角度（0-360度）
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        
        # 转换为0-360度范围
        if angle_deg < 0:
            angle_deg += 360
        
        # 确定所属扇形
        for sector in self.sectors:
            if sector.start_angle <= angle_deg < sector.end_angle:
                return sector
        
        # 边界情况：返回最后一个扇形
        return self.sectors[-1]
    
    def _initialize_sector_progress(self):
        """初始化各扇形区域的进度统计"""
        self.sector_progresses.clear()
        
        for sector in self.sectors:
            # 统计该扇形的孔位
            sector_holes = [
                hole for hole_id, assigned_sector in self.sector_assignments.items()
                if assigned_sector == sector
                for hole in [self.hole_collection.holes.get(hole_id)]
                if hole
            ]
            
            # 统计各状态数量
            total = len(sector_holes)
            qualified = sum(1 for h in sector_holes if h.status == HoleStatus.QUALIFIED)
            defective = sum(1 for h in sector_holes if h.status == HoleStatus.DEFECTIVE)
            blind = sum(1 for h in sector_holes if h.status == HoleStatus.BLIND)
            tie_rod = sum(1 for h in sector_holes if h.status == HoleStatus.TIE_ROD)
            completed = qualified + defective + blind + tie_rod
            
            progress = DynamicSectorProgress(
                sector=sector,
                total_holes=total,
                completed_holes=completed,
                qualified_holes=qualified,
                defective_holes=defective,
                progress_percentage=(completed / total * 100) if total > 0 else 0,
                status_color=self.get_sector_color(sector)
            )
            
            self.sector_progresses[sector] = progress
            self.sector_progress_updated.emit(sector, progress)
        
        # 发送整体进度更新
        self._emit_overall_progress()
    
    def update_hole_status(self, hole_id: str, new_status: HoleStatus):
        """更新孔位状态并重新计算进度"""
        if hole_id not in self.sector_assignments:
            return
        
        sector = self.sector_assignments[hole_id]
        
        # 重新计算该扇形的进度
        self._update_sector_progress(sector)
        
        # 发送整体进度更新
        self._emit_overall_progress()
    
    def _update_sector_progress(self, sector: DynamicSectorQuadrant):
        """更新指定扇形的进度"""
        # 获取该扇形的所有孔位
        sector_holes = [
            hole for hole_id, assigned_sector in self.sector_assignments.items()
            if assigned_sector == sector
            for hole in [self.hole_collection.holes.get(hole_id)]
            if hole
        ]
        
        # 统计各状态数量
        total = len(sector_holes)
        qualified = sum(1 for h in sector_holes if h.status == HoleStatus.QUALIFIED)
        defective = sum(1 for h in sector_holes if h.status == HoleStatus.DEFECTIVE)
        blind = sum(1 for h in sector_holes if h.status == HoleStatus.BLIND)
        tie_rod = sum(1 for h in sector_holes if h.status == HoleStatus.TIE_ROD)
        completed = qualified + defective + blind + tie_rod
        
        progress = DynamicSectorProgress(
            sector=sector,
            total_holes=total,
            completed_holes=completed,
            qualified_holes=qualified,
            defective_holes=defective,
            progress_percentage=(completed / total * 100) if total > 0 else 0,
            status_color=self.get_sector_color(sector)
        )
        
        self.sector_progresses[sector] = progress
        self.sector_progress_updated.emit(sector, progress)
    
    def _emit_overall_progress(self):
        """发送整体进度信息"""
        total_holes = sum(p.total_holes for p in self.sector_progresses.values())
        completed_holes = sum(p.completed_holes for p in self.sector_progresses.values())
        qualified_holes = sum(p.qualified_holes for p in self.sector_progresses.values())
        defective_holes = sum(p.defective_holes for p in self.sector_progresses.values())
        
        overall_data = {
            'total_holes': total_holes,
            'completed_holes': completed_holes,
            'qualified_holes': qualified_holes,
            'defective_holes': defective_holes,
            'completion_rate': (completed_holes / total_holes * 100) if total_holes > 0 else 0,
            'qualification_rate': (qualified_holes / completed_holes * 100) if completed_holes > 0 else 0,
            'sector_count': self.sector_count
        }
        
        self.overall_progress_updated.emit(overall_data)
    
    def get_hole_sector(self, hole_id: str) -> Optional[DynamicSectorQuadrant]:
        """获取指定孔位所属的扇形"""
        return self.sector_assignments.get(hole_id)
    
    def get_sector_progress(self, sector: DynamicSectorQuadrant) -> Optional[DynamicSectorProgress]:
        """获取指定扇形的进度信息"""
        return self.sector_progresses.get(sector)
    
    def get_all_sectors(self) -> List[DynamicSectorQuadrant]:
        """获取所有扇形"""
        return self.sectors.copy()
    
    def get_sector_by_name(self, name: str) -> Optional[DynamicSectorQuadrant]:
        """根据名称获取扇形"""
        for sector in self.sectors:
            if sector.name == name:
                return sector
        return None