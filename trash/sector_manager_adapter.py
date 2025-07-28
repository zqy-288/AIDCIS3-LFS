"""
扇形管理器适配器
根据产品配置自动选择使用固定4扇形还是动态扇形管理器
"""

from typing import Optional, Union
from PySide6.QtCore import QObject, Signal

from .sector_manager import SectorManager, SectorQuadrant, SectorProgress
from .dynamic_sector_manager import DynamicSectorManager, DynamicSectorQuadrant, DynamicSectorProgress
from .enhanced_sector_manager import EnhancedSectorManager, EnhancedSectorConfig
from .sector_compatibility import create_compatible_sector_manager, CompatibilityMode
from src.core_business.models.hole_data import HoleCollection, HoleStatus


class SectorManagerAdapter(QObject):
    """扇形管理器适配器 - 统一接口
    
    更新：支持增强型扇形管理器和自适应角度计算
    """
    
    # 统一的信号（使用object类型以兼容多种实现）
    sector_progress_updated = Signal(object, object)  # sector, progress
    overall_progress_updated = Signal(dict)
    sector_count_changed = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._use_dynamic = False
        self._use_enhanced = True  # 默认使用增强型管理器
        self._sector_count = 4
        self._compatibility_mode = CompatibilityMode.HYBRID
        self._manager: Optional[Union[SectorManager, DynamicSectorManager, EnhancedSectorManager]] = None
        
        # 默认使用增强型管理器
        self._create_manager()
    
    def _create_manager(self):
        """创建管理器实例 - 支持增强型管理器"""
        if self._use_dynamic:
            self._manager = DynamicSectorManager(self._sector_count)
            self._manager.sector_progress_updated.connect(self._on_dynamic_progress_updated)
            self._manager.overall_progress_updated.connect(self.overall_progress_updated.emit)
            self._manager.sector_count_changed.connect(self.sector_count_changed.emit)
        elif self._use_enhanced:
            # 使用增强型管理器
            config = EnhancedSectorConfig(
                use_adaptive_angles=True,
                fallback_to_default=True,
                validate_angle_consistency=True
            )
            self._manager = EnhancedSectorManager(config)
            self._manager.sector_progress_updated.connect(self._on_enhanced_progress_updated)
            self._manager.overall_progress_updated.connect(self.overall_progress_updated.emit)
        else:
            # 使用传统管理器
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
    
    def _on_enhanced_progress_updated(self, sector: SectorQuadrant, progress: SectorProgress):
        """增强型扇形进度更新转换"""
        # 转换为统一的信号格式
        self.sector_progress_updated.emit(sector, progress)
    
    def set_dynamic_mode(self, enabled: bool, sector_count: int = 4):
        """设置是否使用动态扇形模式"""
        if enabled and (sector_count < 2 or sector_count > 12):
            raise ValueError(f"扇形数量必须在2-12之间，当前值: {sector_count}")
        
        if enabled != self._use_dynamic or sector_count != self._sector_count:
            self._use_dynamic = enabled
            self._use_enhanced = False  # 动态模式与增强模式互斥
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
    
    def set_enhanced_mode(self, enabled: bool, compatibility_mode: CompatibilityMode = CompatibilityMode.HYBRID):
        """设置是否使用增强型扇形模式"""
        if enabled != self._use_enhanced or compatibility_mode != self._compatibility_mode:
            self._use_enhanced = enabled
            self._use_dynamic = False  # 增强模式与动态模式互斥
            self._compatibility_mode = compatibility_mode
            
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
        """加载孔位集合 - 支持增强型管理器"""
        if self._manager:
            if isinstance(self._manager, EnhancedSectorManager):
                # 增强型管理器使用不同的方法
                self._manager.set_hole_collection(hole_collection)
            else:
                # 传统管理器使用load_hole_collection
                self._manager.load_hole_collection(hole_collection)
            print(f"✅ SectorManagerAdapter 成功加载 {len(hole_collection)} 个孔位数据")
        else:
            print(f"⚠️ SectorManagerAdapter 管理器不存在")
    
    def has_data(self):
        """检查是否有孔位数据"""
        if not self._manager:
            return False
        
        # 检查不同类型的管理器
        if hasattr(self._manager, 'hole_collection'):
            return (self._manager.hole_collection is not None and 
                   len(self._manager.hole_collection) > 0)
        elif hasattr(self._manager, 'sector_assignments'):
            return len(self._manager.sector_assignments) > 0
        
        return False
    
    def update_hole_status(self, hole_id: str, new_status: HoleStatus):
        """更新孔位状态"""
        if self._manager:
            self._manager.update_hole_status(hole_id, new_status)
    
    def get_manager_type(self) -> str:
        """获取当前管理器类型"""
        if self._use_dynamic:
            return "DynamicSectorManager"
        elif self._use_enhanced:
            return "EnhancedSectorManager"
        else:
            return "SectorManager"
    
    def is_enhanced_mode(self) -> bool:
        """检查是否为增强模式"""
        return self._use_enhanced
    
    def get_enhanced_manager(self) -> Optional[EnhancedSectorManager]:
        """获取增强型管理器实例"""
        if self._use_enhanced and isinstance(self._manager, EnhancedSectorManager):
            return self._manager
        return None
    
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
    
    def _recalculate_sector_progress(self, sector):
        """重新计算指定扇形区域的进度 - 委托给底层管理器"""
        if not self._manager:
            return
        
        # 检查底层管理器是否有此方法
        if hasattr(self._manager, '_recalculate_sector_progress'):
            self._manager._recalculate_sector_progress(sector)
        else:
            # 如果没有，则手动触发进度更新
            if hasattr(self._manager, 'get_sector_progress'):
                progress = self._manager.get_sector_progress(sector)
                if progress:
                    self.sector_progress_updated.emit(sector, progress)