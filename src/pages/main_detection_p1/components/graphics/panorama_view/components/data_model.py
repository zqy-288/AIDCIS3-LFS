"""
全景图数据模型实现
负责管理孔位数据，提供数据访问接口
"""

from typing import Dict, Optional
from PySide6.QtCore import QObject, Signal
from ..core.interfaces import IPanoramaDataModel
from src.core_business.models.hole_data import HoleData, HoleStatus, HoleCollection


class PanoramaDataModel(QObject):
    """全景图数据模型实现"""
    
    # 信号
    hole_status_changed = Signal(str, object)  # hole_id, status
    data_loaded = Signal()
    data_cleared = Signal()
    
    def __init__(self):
        super().__init__()
        self._holes: Dict[str, HoleData] = {}
        self._hole_collection: Optional[HoleCollection] = None
    
    def get_holes(self) -> Dict[str, HoleData]:
        """获取所有孔位数据"""
        return self._holes.copy()
    
    def get_hole(self, hole_id: str) -> Optional[HoleData]:
        """获取指定孔位"""
        return self._holes.get(hole_id)
    
    def update_hole_status(self, hole_id: str, status: HoleStatus) -> bool:
        """
        更新孔位状态
        
        Args:
            hole_id: 孔位ID
            status: 新状态
            
        Returns:
            是否更新成功
        """
        if hole_id not in self._holes:
            return False
        
        hole = self._holes[hole_id]
        old_status = hole.status
        
        if old_status != status:
            hole.status = status
            self.hole_status_changed.emit(hole_id, status)
            
        return True
    
    def load_hole_collection(self, hole_collection: HoleCollection) -> None:
        """
        加载孔位集合
        
        Args:
            hole_collection: 孔位集合对象
        """
        # 清空旧数据
        self._holes.clear()
        self._hole_collection = hole_collection
        
        if hole_collection and hole_collection.holes:
            # 复制孔位数据
            for hole_id, hole_data in hole_collection.holes.items():
                self._holes[hole_id] = hole_data
            
            self.data_loaded.emit()
        else:
            self.data_cleared.emit()
    
    def get_hole_count(self) -> int:
        """获取孔位数量"""
        return len(self._holes)
    
    def get_holes_by_status(self, status: HoleStatus) -> Dict[str, HoleData]:
        """
        根据状态获取孔位
        
        Args:
            status: 孔位状态
            
        Returns:
            符合状态的孔位字典
        """
        return {
            hole_id: hole 
            for hole_id, hole in self._holes.items() 
            if hole.status == status
        }
    
    def clear_data(self) -> None:
        """清空数据"""
        self._holes.clear()
        self._hole_collection = None
        self.data_cleared.emit()