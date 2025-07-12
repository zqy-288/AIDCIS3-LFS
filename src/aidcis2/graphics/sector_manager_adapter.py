"""
扇形管理器适配器
根据产品配置自动选择使用固定4扇形还是动态扇形管理器
"""

from typing import Optional, Union
from PySide6.QtCore import QObject, Signal

from .sector_manager import SectorManager, SectorQuadrant, SectorProgress
from .dynamic_sector_manager import DynamicSectorManager, DynamicSectorQuadrant, DynamicSectorProgress
from aidcis2.models.hole_data import HoleCollection, HoleStatus


class SectorManagerAdapter(QObject):
    """扇形管理器适配器 - 统一接口"""
    
    # 统一的信号（使用object类型以兼容两种实现）
    sector_progress_updated = Signal(object, object)  # sector, progress
    overall_progress_updated = Signal(dict)
    sector_count_changed = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._use_dynamic = False
        self._sector_count = 4
        self._manager: Optional[Union[SectorManager, DynamicSectorManager]] = None
        
        # 默认使用固定4扇形管理器
        self._create_manager()
    
    def _create_manager(self):
        """创建管理器实例"""
        if self._use_dynamic:
            self._manager = DynamicSectorManager(self._sector_count)
            self._manager.sector_progress_updated.connect(self._on_dynamic_progress_updated)
            self._manager.overall_progress_updated.connect(self.overall_progress_updated.emit)
            self._manager.sector_count_changed.connect(self.sector_count_changed.emit)
        else:
            self._manager = SectorManager()
            self._manager.sector_progress_updated.connect(self._on_fixed_progress_updated)
            self._manager.overall_progress_updated.connect(self.overall_progress_updated.emit)
    
    def _on_dynamic_progress_updated(self, sector: DynamicSectorQuadrant, progress: DynamicSectorProgress):
        """动态扇形进度更新转换"""
        # 转换为统一的信号格式
        self.sector_progress_updated.emit(sector, progress)
    
    def _on_fixed_progress_updated(self, sector: SectorQuadrant, progress: SectorProgress):
        """固定扇形进度更新转换"""
        # 转换为统一的信号格式
        self.sector_progress_updated.emit(sector, progress)
    
    def set_dynamic_mode(self, enabled: bool, sector_count: int = 4):
        """设置是否使用动态扇形模式"""
        if enabled and (sector_count < 2 or sector_count > 12):
            raise ValueError(f"扇形数量必须在2-12之间，当前值: {sector_count}")
        
        if enabled != self._use_dynamic or sector_count != self._sector_count:
            self._use_dynamic = enabled
            self._sector_count = sector_count
            
            # 保存当前的孔位集合（如果有）
            hole_collection = None
            if self._manager and hasattr(self._manager, 'hole_collection'):
                hole_collection = self._manager.hole_collection
            
            # 重新创建管理器
            self._create_manager()
            
            # 恢复孔位集合
            if hole_collection:
                self.load_hole_collection(hole_collection)
    
    def load_hole_collection(self, hole_collection: HoleCollection):
        """加载孔位集合"""
        if self._manager:
            self._manager.load_hole_collection(hole_collection)
    
    def update_hole_status(self, hole_id: str, new_status: HoleStatus):
        """更新孔位状态"""
        if self._manager:
            self._manager.update_hole_status(hole_id, new_status)
    
    def get_sector_by_index(self, index: int):
        """根据索引获取扇形"""
        if isinstance(self._manager, DynamicSectorManager):
            sectors = self._manager.get_all_sectors()
            if 0 <= index < len(sectors):
                return sectors[index]
        else:
            # 固定扇形
            sector_map = {
                0: SectorQuadrant.SECTOR_1,
                1: SectorQuadrant.SECTOR_2,
                2: SectorQuadrant.SECTOR_3,
                3: SectorQuadrant.SECTOR_4
            }
            return sector_map.get(index)
    
    def get_sector_count(self) -> int:
        """获取扇形数量"""
        if isinstance(self._manager, DynamicSectorManager):
            return self._manager.sector_count
        else:
            return 4
    
    def get_manager(self) -> Union[SectorManager, DynamicSectorManager]:
        """获取实际的管理器实例"""
        return self._manager
    
    # 委托方法
    def get_sector_holes(self, sector):
        """获取扇形内的孔位"""
        if not self._manager:
            return []
        
        if isinstance(self._manager, DynamicSectorManager):
            # 动态扇形管理器
            sector_holes = []
            for hole_id, assigned_sector in self._manager.sector_assignments.items():
                if assigned_sector == sector:
                    hole = self._manager.hole_collection.holes.get(hole_id)
                    if hole:
                        sector_holes.append(hole)
            return sector_holes
        else:
            # 固定扇形管理器
            return self._manager.get_sector_holes(sector)
    
    @property
    def hole_collection(self):
        """获取孔位集合"""
        if self._manager:
            return self._manager.hole_collection
        return None
    
    def get_sector_progress(self, sector):
        """获取扇形进度"""
        if not self._manager:
            return None
        return self._manager.get_sector_progress(sector)
    
    def get_overall_progress(self):
        """获取整体进度"""
        if not self._manager:
            return None
        return self._manager.get_overall_progress()
    
    @property
    def sector_assignments(self):
        """获取扇形分配信息"""
        if not self._manager:
            return {}
        return getattr(self._manager, 'sector_assignments', {})