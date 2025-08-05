"""
扇形数据分发器
负责将孔位数据分配到各个扇形，并管理扇形数据的更新
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict
from PySide6.QtCore import QObject, Signal

from src.shared.models.hole_data import HoleCollection, HoleData
from src.pages.main_detection_p1.graphics.core.sector_controllers import UnifiedLogger
from src.pages.main_detection_p1.graphics.core.hole_data_adapter import HoleDataAdapter
from src.pages.main_detection_p1.graphics.core.sector_types import SectorQuadrant


@dataclass
class SectorData:
    """扇形数据"""
    quadrant: SectorQuadrant
    holes: List[HoleData] = field(default_factory=list)
    hole_ids: set = field(default_factory=set)
    bounds: Optional[Tuple[float, float, float, float]] = None
    center: Optional[Tuple[float, float]] = None
    hole_count: int = 0
    

class SectorDataDistributor(QObject):
    """
    扇形数据分发器
    
    负责：
    1. 从HoleDataAdapter获取孔位数据
    2. 根据位置将孔分配到4个扇形
    3. 管理每个扇形的数据缓存
    4. 提供扇形数据访问接口
    """
    
    # 信号
    data_distributed = Signal()  # 数据分发完成
    sector_updated = Signal(SectorQuadrant, SectorData)  # 扇形数据更新
    distribution_stats = Signal(dict)  # 分发统计信息
    
    def __init__(self, hole_data_adapter: HoleDataAdapter):
        super().__init__()
        self.logger = UnifiedLogger("SectorDataDistributor")
        self.hole_data_adapter = hole_data_adapter
        
        # 扇形数据存储
        self.sector_data: Dict[SectorQuadrant, SectorData] = {
            SectorQuadrant.SECTOR_1: SectorData(SectorQuadrant.SECTOR_1),
            SectorQuadrant.SECTOR_2: SectorData(SectorQuadrant.SECTOR_2),
            SectorQuadrant.SECTOR_3: SectorData(SectorQuadrant.SECTOR_3),
            SectorQuadrant.SECTOR_4: SectorData(SectorQuadrant.SECTOR_4)
        }
        
        # 全局数据
        self.global_center: Optional[Tuple[float, float]] = None
        self.global_bounds: Optional[Tuple[float, float, float, float]] = None
        self.total_holes: int = 0
        
        # 连接适配器信号
        self._connect_adapter_signals()
        
    def _connect_adapter_signals(self):
        """连接数据适配器的信号"""
        self.hole_data_adapter.data_loaded.connect(self._on_data_loaded)
        self.hole_data_adapter.data_updated.connect(self._on_data_updated)
        self.hole_data_adapter.data_cleared.connect(self._on_data_cleared)
        self.hole_data_adapter.status_changed.connect(self._on_status_changed)
        
    def distribute_data(self, force_refresh: bool = False):
        """
        分发数据到各个扇形
        
        Args:
            force_refresh: 是否强制刷新
        """
        # 获取孔位集合
        hole_collection = self.hole_data_adapter.get_hole_collection()
        if not hole_collection:
            self.logger.warning("没有可分发的孔位数据", "⚠️")
            return
            
        self.logger.info(f"开始分发{len(hole_collection)}个孔位到扇形", "📊")
        
        # 清除现有数据
        if force_refresh:
            self._clear_sector_data()
            
        # 计算全局中心和边界
        self._calculate_global_metrics(hole_collection)
        
        # 分配孔位到扇形
        distribution_count = self._distribute_holes_to_sectors(hole_collection)
        
        # 更新扇形统计信息
        self._update_sector_statistics()
        
        # 发送完成信号
        self.data_distributed.emit()
        
        # 发送统计信息
        stats = self._get_distribution_statistics()
        self.distribution_stats.emit(stats)
        
        self.logger.info(f"数据分发完成: {stats}", "✅")
        
    def _calculate_global_metrics(self, hole_collection: HoleCollection):
        """计算全局度量信息"""
        if not hole_collection or len(hole_collection) == 0:
            return
            
        # 获取边界
        self.global_bounds = hole_collection.get_bounds()
        
        # 计算中心
        min_x, min_y, max_x, max_y = self.global_bounds
        self.global_center = ((min_x + max_x) / 2, (min_y + max_y) / 2)
        
        # 记录总数
        self.total_holes = len(hole_collection)
        
        self.logger.debug(f"全局中心: {self.global_center}, 边界: {self.global_bounds}", "📐")
        
    def _distribute_holes_to_sectors(self, hole_collection: HoleCollection) -> Dict[SectorQuadrant, int]:
        """
        将孔位分配到扇形
        
        扇形划分规则（基于中心点）：
        - 扇形1：右上 (x >= center_x, y < center_y)
        - 扇形2：左上 (x < center_x, y < center_y)
        - 扇形3：左下 (x < center_x, y >= center_y)
        - 扇形4：右下 (x >= center_x, y >= center_y)
        """
        if not self.global_center:
            return {}
            
        center_x, center_y = self.global_center
        distribution_count = defaultdict(int)
        
        for hole in hole_collection.holes.values():
            # 确定扇形
            if hole.center_x >= center_x and hole.center_y < center_y:
                sector = SectorQuadrant.SECTOR_1
            elif hole.center_x < center_x and hole.center_y < center_y:
                sector = SectorQuadrant.SECTOR_2
            elif hole.center_x < center_x and hole.center_y >= center_y:
                sector = SectorQuadrant.SECTOR_3
            else:  # x >= center_x and y >= center_y
                sector = SectorQuadrant.SECTOR_4
                
            # 添加到对应扇形
            sector_data = self.sector_data[sector]
            sector_data.holes.append(hole)
            sector_data.hole_ids.add(hole.hole_id)
            distribution_count[sector] += 1
            
        return dict(distribution_count)
        
    def _update_sector_statistics(self):
        """更新每个扇形的统计信息"""
        for sector, data in self.sector_data.items():
            if not data.holes:
                continue
                
            # 计算边界
            x_coords = [h.center_x for h in data.holes]
            y_coords = [h.center_y for h in data.holes]
            data.bounds = (min(x_coords), min(y_coords), max(x_coords), max(y_coords))
            
            # 计算中心
            data.center = (sum(x_coords) / len(data.holes), sum(y_coords) / len(data.holes))
            
            # 更新计数
            data.hole_count = len(data.holes)
            
            # 发送更新信号
            self.sector_updated.emit(sector, data)
            
    def get_sector_data(self, sector: SectorQuadrant) -> SectorData:
        """
        获取指定扇形的数据
        
        Args:
            sector: 扇形枚举
            
        Returns:
            扇形数据
        """
        return self.sector_data.get(sector, SectorData(sector))
        
    def get_sector_holes(self, sector: SectorQuadrant) -> List[HoleData]:
        """
        获取指定扇形的孔位列表
        
        Args:
            sector: 扇形枚举
            
        Returns:
            孔位列表
        """
        return self.sector_data[sector].holes
        
    def get_hole_sector(self, hole_id: str) -> Optional[SectorQuadrant]:
        """
        获取指定孔位所在的扇形
        
        Args:
            hole_id: 孔位ID
            
        Returns:
            扇形枚举或None
        """
        for sector, data in self.sector_data.items():
            if hole_id in data.hole_ids:
                return sector
        return None
        
    def get_all_sector_data(self) -> Dict[SectorQuadrant, SectorData]:
        """
        获取所有扇形数据
        
        Returns:
            所有扇形数据的字典
        """
        return self.sector_data.copy()
        
    def _clear_sector_data(self):
        """清除所有扇形数据"""
        for data in self.sector_data.values():
            data.holes.clear()
            data.hole_ids.clear()
            data.bounds = None
            data.center = None
            data.hole_count = 0
            
    def _get_distribution_statistics(self) -> Dict[str, Any]:
        """获取分发统计信息"""
        stats = {
            'total_holes': self.total_holes,
            'sectors': {}
        }
        
        for sector, data in self.sector_data.items():
            stats['sectors'][sector.name] = {
                'count': data.hole_count,
                'percentage': (data.hole_count / self.total_holes * 100) if self.total_holes > 0 else 0,
                'bounds': data.bounds,
                'center': data.center
            }
            
        return stats
        
    def _on_data_loaded(self, hole_collection: HoleCollection):
        """处理数据加载完成"""
        self.logger.info("收到数据加载通知，开始分发", "📥")
        self.distribute_data(force_refresh=True)
        
    def _on_data_updated(self, update_data: dict):
        """处理数据更新"""
        self.logger.info("收到数据更新通知", "🔄")
        # 根据更新类型处理
        # 这里可以实现增量更新逻辑
        
    def _on_data_cleared(self):
        """处理数据清除"""
        self.logger.info("收到数据清除通知", "🗑️")
        self._clear_sector_data()
        self.total_holes = 0
        self.global_center = None
        self.global_bounds = None
        
    def _on_status_changed(self, hole_id: str, new_status):
        """处理孔位状态变化"""
        # 找到孔位所在扇形并更新
        for sector, data in self.sector_data.items():
            for hole in data.holes:
                if hole.hole_id == hole_id:
                    hole.status = new_status
                    self.logger.debug(f"更新扇形{sector.value}中孔位{hole_id}的状态", "🔄")
                    return
                    
    def get_sector_visibility_info(self, sector: SectorQuadrant) -> Dict[str, bool]:
        """
        获取扇形内孔位的可见性信息
        
        Args:
            sector: 扇形枚举
            
        Returns:
            {hole_id: is_visible} 的映射
        """
        visibility_info = {}
        sector_data = self.sector_data[sector]
        
        for hole in sector_data.holes:
            # 这里可以根据具体规则判断可见性
            # 目前简单返回True
            visibility_info[hole.hole_id] = True
            
        return visibility_info
        
    def update_hole_visibility(self, sector: SectorQuadrant, hole_id: str, visible: bool):
        """
        更新孔位可见性
        
        Args:
            sector: 扇形枚举
            hole_id: 孔位ID
            visible: 是否可见
        """
        # 这里可以实现可见性管理逻辑
        # 可能需要额外的数据结构来存储可见性状态
        pass