"""
扇形区域管理器
负责将DXF管板划分成4个扇形区域，并管理各区域的进度统计
"""

import math
from enum import Enum
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal, QPointF
from PySide6.QtGui import QColor

from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus


class SectorQuadrant(Enum):
    """扇形象限枚举"""
    SECTOR_1 = "sector_1"  # 0°-90° (右上)
    SECTOR_2 = "sector_2"  # 90°-180° (左上) 
    SECTOR_3 = "sector_3"  # 180°-270° (左下)
    SECTOR_4 = "sector_4"  # 270°-360° (右下)


@dataclass
class SectorProgress:
    """区域划分进度数据"""
    sector: SectorQuadrant
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


class SectorManager(QObject):
    """扇形区域管理器"""
    
    # 信号
    sector_progress_updated = Signal(SectorQuadrant, SectorProgress)
    overall_progress_updated = Signal(dict)  # 整体进度更新
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hole_collection: Optional[HoleCollection] = None
        self.center_point: Optional[QPointF] = None
        self.sector_assignments: Dict[str, SectorQuadrant] = {}  # hole_id -> sector
        self.sector_progresses: Dict[SectorQuadrant, SectorProgress] = {}
        
        # 扇形颜色配置
        self.sector_colors = {
            SectorQuadrant.SECTOR_1: QColor(76, 175, 80),   # 绿色 - 右上
            SectorQuadrant.SECTOR_2: QColor(33, 150, 243),  # 蓝色 - 左上
            SectorQuadrant.SECTOR_3: QColor(255, 152, 0),   # 橙色 - 左下
            SectorQuadrant.SECTOR_4: QColor(156, 39, 176),  # 紫色 - 右下
        }
    
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
    
    def _get_hole_sector(self, hole: HoleData) -> SectorQuadrant:
        """确定孔位属于哪个扇形区域"""
        # 计算相对于中心点的向量
        dx = hole.center_x - self.center_point.x()
        dy = hole.center_y - self.center_point.y()
        
        # 计算角度 (0°指向右方，逆时针为正)
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        
        # 转换为0-360度范围
        if angle_deg < 0:
            angle_deg += 360
        
        # 根据角度确定扇形区域
        if 0 <= angle_deg < 90:
            return SectorQuadrant.SECTOR_1  # 右上
        elif 90 <= angle_deg < 180:
            return SectorQuadrant.SECTOR_2  # 左上
        elif 180 <= angle_deg < 270:
            return SectorQuadrant.SECTOR_3  # 左下
        else:  # 270 <= angle_deg < 360
            return SectorQuadrant.SECTOR_4  # 右下
    
    def _initialize_sector_progress(self):
        """初始化各扇形区域的进度统计"""
        # 统计各扇形的孔位数量
        sector_counts = {sector: 0 for sector in SectorQuadrant}
        
        for hole_id, sector in self.sector_assignments.items():
            sector_counts[sector] += 1
        
        # 创建进度对象
        for sector in SectorQuadrant:
            self.sector_progresses[sector] = SectorProgress(
                sector=sector,
                total_holes=sector_counts[sector],
                completed_holes=0,
                qualified_holes=0,
                defective_holes=0,
                progress_percentage=0.0,
                status_color=self.sector_colors[sector]
            )
    
    def update_hole_status(self, hole_id: str, new_status: HoleStatus):
        """更新孔位状态并重新计算区域进度"""
        if hole_id not in self.sector_assignments:
            return
        
        sector = self.sector_assignments[hole_id]
        self._recalculate_sector_progress(sector)
        
        # 发射更新信号
        self.sector_progress_updated.emit(sector, self.sector_progresses[sector])
        self._emit_overall_progress()
    
    def _recalculate_sector_progress(self, sector: SectorQuadrant):
        """重新计算指定扇形区域的进度"""
        if not self.hole_collection:
            return
        
        # 获取该扇形的所有孔位
        sector_holes = []
        for hole_id, hole_sector in self.sector_assignments.items():
            if hole_sector == sector:
                hole = self.hole_collection.holes.get(hole_id)
                if hole is not None:
                    sector_holes.append(hole)
        
        # 统计各状态数量
        completed = 0
        qualified = 0
        defective = 0
        
        for hole in sector_holes:
            if hole.status in [HoleStatus.QUALIFIED, HoleStatus.DEFECTIVE, 
                             HoleStatus.BLIND, HoleStatus.TIE_ROD]:
                completed += 1
                
                if hole.status == HoleStatus.QUALIFIED:
                    qualified += 1
                elif hole.status == HoleStatus.DEFECTIVE:
                    defective += 1
        
        # 更新进度数据
        progress = self.sector_progresses[sector]
        progress.completed_holes = completed
        progress.qualified_holes = qualified
        progress.defective_holes = defective
        progress.progress_percentage = progress.completion_rate
        
        # 根据进度更新状态颜色
        progress.status_color = self._get_progress_color(progress.completion_rate)
    
    def _get_progress_color(self, completion_rate: float) -> QColor:
        """根据完成率获取状态颜色"""
        if completion_rate >= 90:
            return QColor(76, 175, 80)    # 绿色 - 完成度高
        elif completion_rate >= 60:
            return QColor(255, 193, 7)    # 黄色 - 完成度中等
        elif completion_rate >= 30:
            return QColor(255, 152, 0)    # 橙色 - 完成度较低
        else:
            return QColor(244, 67, 54)    # 红色 - 完成度低
    
    def _emit_overall_progress(self):
        """发射整体进度更新信号"""
        overall_stats = {
            'total_holes': sum(p.total_holes for p in self.sector_progresses.values()),
            'completed_holes': sum(p.completed_holes for p in self.sector_progresses.values()),
            'qualified_holes': sum(p.qualified_holes for p in self.sector_progresses.values()),
            'defective_holes': sum(p.defective_holes for p in self.sector_progresses.values()),
            'sector_progresses': self.sector_progresses.copy()
        }
        
        self.overall_progress_updated.emit(overall_stats)
    
    def get_sector_holes(self, sector: SectorQuadrant) -> List[HoleData]:
        """获取指定扇形区域的所有孔位"""
        if not self.hole_collection:
            return []
        
        return [
            self.hole_collection.holes[hole_id]
            for hole_id, hole_sector in self.sector_assignments.items()
            if hole_sector == sector and hole_id in self.hole_collection.holes
        ]
    
    def get_hole_sector(self, hole_id: str) -> Optional[SectorQuadrant]:
        """获取孔位所属的扇形区域"""
        return self.sector_assignments.get(hole_id)
    
    def get_sector_progress(self, sector: SectorQuadrant) -> Optional[SectorProgress]:
        """获取指定扇形区域的进度信息"""
        return self.sector_progresses.get(sector)
    
    def get_all_sector_progresses(self) -> Dict[SectorQuadrant, SectorProgress]:
        """获取所有扇形区域的进度信息"""
        return self.sector_progresses.copy()
    
    def get_center_point(self) -> Optional[QPointF]:
        """获取管板中心点"""
        return self.center_point