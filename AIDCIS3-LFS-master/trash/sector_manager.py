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

from src.core_business.models.hole_data import HoleData, HoleCollection, HoleStatus


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
        # 静默加载，只记录关键信息
        import time
        start_time = time.perf_counter()
        
        self.hole_collection = hole_collection
        
        # 计算管板中心点
        self.center_point = self._calculate_center_point()
        
        # 执行扇形划分
        self._assign_holes_to_sectors()
        
        # 初始化进度统计
        self._initialize_sector_progress()
        
        elapsed_time = time.perf_counter() - start_time
        
        # 只在处理大数据集时输出简化信息
        if len(hole_collection.holes) > 10000:
            print(f"✅ 扇形分配完成: {len(hole_collection.holes)} 个孔位，耗时 {elapsed_time:.1f}秒")
        
        # 输出扇形分配结果（简化）
        from collections import Counter
        sector_counts = Counter(self.sector_assignments.values())
        if len(hole_collection.holes) > 10000:
            sector_summary = ', '.join([f"{s.value.split('_')[1]}区:{c}个" for s, c in sector_counts.items()])
            print(f"📊 扇形分配: {sector_summary}")
        
    def _calculate_center_point(self) -> QPointF:
        """计算管板的几何中心点"""
        if not self.hole_collection:
            return QPointF(0, 0)
        
        bounds = self.hole_collection.get_bounds()
        center_x = (bounds[0] + bounds[2]) / 2
        center_y = (bounds[1] + bounds[3]) / 2
        
        return QPointF(center_x, center_y)
    
    def _assign_holes_to_sectors(self):
        """将孔位分配到对应的扇形区域（超高性能版本）"""
        if not self.hole_collection or self.center_point is None:
            return
        
        # 静默执行扇形分配
        import time
        start_time = time.perf_counter()
        
        self.sector_assignments.clear()
        
        # 预计算中心点坐标（避免重复访问）
        center_x = self.center_point.x()
        center_y = self.center_point.y()
        
        print(f"🎯 [扇形分配调试] 管板中心点: ({center_x:.2f}, {center_y:.2f})")
        
        # 扇形查找表（使用位运算索引）
        sector_lookup = [
            SectorQuadrant.SECTOR_4,  # 00: dx>=0, dy>=0 右下
            SectorQuadrant.SECTOR_1,  # 01: dx>=0, dy<0  右上
            SectorQuadrant.SECTOR_3,  # 10: dx<0,  dy>=0 左下
            SectorQuadrant.SECTOR_2   # 11: dx<0,  dy<0  左上
        ]
        
        # 调试：输出坐标系定义
        print(f"🧭 [扇形分配调试] 坐标系定义:")
        print(f"   - 右下 (dx>=0, dy>=0) → SECTOR_4")
        print(f"   - 右上 (dx>=0, dy<0)  → SECTOR_1") 
        print(f"   - 左下 (dx<0,  dy>=0) → SECTOR_3")
        print(f"   - 左上 (dx<0,  dy<0)  → SECTOR_2")
        
        # 批量处理：使用向量化操作
        hole_items = list(self.hole_collection.holes.items())
        batch_size = 10000  # 增大批处理大小以提高效率
        
        # 调试：记录每个扇形的样本孔位坐标
        sector_samples = {sector: [] for sector in SectorQuadrant}
        
        for i in range(0, len(hole_items), batch_size):
            batch = hole_items[i:i + batch_size]
            
            # 批量计算扇形分配
            for hole_id, hole in batch:
                # 计算相对坐标
                dx = hole.center_x - center_x
                dy = hole.center_y - center_y
                
                # 使用位运算快速确定象限（比条件判断快约2-3倍）
                sector_index = (dx < 0) << 1 | (dy < 0)
                sector = sector_lookup[sector_index]
                
                self.sector_assignments[hole_id] = sector
                
                # 收集每个扇形的样本坐标（前5个）
                if len(sector_samples[sector]) < 5:
                    sector_samples[sector].append({
                        'hole_id': hole_id,
                        'abs_coords': (hole.center_x, hole.center_y),
                        'rel_coords': (dx, dy),
                        'conditions': f"dx={dx:.1f}{'>=0' if dx >= 0 else '<0'}, dy={dy:.1f}{'>=0' if dy >= 0 else '<0'}"
                    })
        
        elapsed_time = time.perf_counter() - start_time
        
        # 输出调试信息：每个扇形的样本坐标
        print(f"🔍 [扇形分配调试] 各扇形样本坐标:")
        for sector, samples in sector_samples.items():
            if samples:
                print(f"   {sector.value}:")
                for sample in samples:
                    print(f"     {sample['hole_id']}: 绝对({sample['abs_coords'][0]:.1f},{sample['abs_coords'][1]:.1f}) → 相对({sample['rel_coords'][0]:.1f},{sample['rel_coords'][1]:.1f}) [{sample['conditions']}]")
        
        # 统计结果
        from collections import Counter
        sector_counts = Counter(self.sector_assignments.values())
        print(f"📊 [扇形分配调试] 分配结果: {dict((s.value, c) for s, c in sector_counts.items())}")
        
        # 只在调试模式或大数据集时输出关键信息
        if len(self.hole_collection.holes) > 20000:
            print(f"⚡ 高性能扇形分配: {len(self.hole_collection.holes)} 个孔位，{elapsed_time:.2f}秒，{len(self.hole_collection.holes)/elapsed_time:.0f} 孔位/秒")
    
    def _get_hole_sector(self, hole: HoleData) -> SectorQuadrant:
        """确定孔位属于哪个扇形区域（高性能版本）"""
        # 计算相对于中心点的向量
        dx = hole.center_x - self.center_point.x()
        dy = hole.center_y - self.center_point.y()
        
        # 使用位运算快速确定象限（避免三角函数计算）
        sector_index = (dx < 0) << 1 | (dy < 0)
        sector_lookup = [
            SectorQuadrant.SECTOR_1,  # 00: dx>=0, dy>=0 - 右上
            SectorQuadrant.SECTOR_4,  # 01: dx>=0, dy<0  - 右下
            SectorQuadrant.SECTOR_2,  # 10: dx<0,  dy>=0 - 左上
            SectorQuadrant.SECTOR_3   # 11: dx<0,  dy<0  - 左下
        ]
        
        return sector_lookup[sector_index]
    
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
    
    def get_overall_progress(self) -> Dict:
        """获取整体进度信息"""
        return {
            'total_holes': sum(p.total_holes for p in self.sector_progresses.values()),
            'completed_holes': sum(p.completed_holes for p in self.sector_progresses.values()),
            'qualified_holes': sum(p.qualified_holes for p in self.sector_progresses.values()),
            'defective_holes': sum(p.defective_holes for p in self.sector_progresses.values()),
            'sector_progresses': self.sector_progresses.copy()
        }
    
    def cleanup_resources(self) -> None:
        """清理资源 - 内存优化"""
        # 清理扇形分配
        assignments_count = len(self.sector_assignments)
        self.sector_assignments.clear()
        
        # 清理进度信息
        self.sector_progresses.clear()
        
        # 清理孔位集合引用
        self.hole_collection = None
        self.center_point = None
        
        # 主动垃圾回收
        import gc
        gc.collect()
        
        # 只在处理大数据集时输出清理信息
        if assignments_count > 10000:
            print(f"🧹 扇形管理器资源已清理: {assignments_count} 个分配项")
    
    def get_sector_for_hole(self, hole_id: str) -> Optional[SectorQuadrant]:
        """获取指定孔位所属的扇形区域"""
        return self.sector_assignments.get(hole_id)
    
    def get_sector_holes(self, sector: SectorQuadrant) -> List[HoleData]:
        """获取指定扇形区域的所有孔位"""
        if not self.hole_collection:
            return []
        
        sector_holes = []
        for hole_id, assigned_sector in self.sector_assignments.items():
            if assigned_sector == sector:
                hole = self.hole_collection.holes.get(hole_id)
                if hole:
                    sector_holes.append(hole)
        
        return sector_holes