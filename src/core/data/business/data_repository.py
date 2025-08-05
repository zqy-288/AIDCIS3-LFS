"""
数据仓库实现 - SharedDataManager的替代品
使用依赖注入而非单例模式
"""

from typing import Optional, Dict, Any, List, Callable
from PySide6.QtCore import QObject, Signal

from src.core_business.data.interfaces import IDataRepository
from src.shared.models.hole_data import HoleCollection, HoleData, HoleStatus
from src.core.shared_data_manager import SharedDataManager


class DataRepository(QObject, IDataRepository):
    """
    数据仓库实现
    作为SharedDataManager的包装器，逐步迁移功能
    """
    
    # 信号定义
    hole_collection_changed = Signal(HoleCollection)
    hole_status_changed = Signal(str, HoleStatus)  # hole_id, new_status
    project_changed = Signal(str)  # project_name
    
    def __init__(self, shared_data_manager: Optional[SharedDataManager] = None):
        """
        初始化数据仓库
        
        Args:
            shared_data_manager: 可选的SharedDataManager实例，如果不提供则创建新的
        """
        super().__init__()
        
        # 使用依赖注入而非单例
        self._shared_data = shared_data_manager or SharedDataManager()
        self._subscribers: Dict[str, Callable] = {}
        self._subscription_counter = 0
        
        # 连接SharedDataManager的信号
        self._setup_signal_forwarding()
    
    def _setup_signal_forwarding(self):
        """设置信号转发"""
        # 转发SharedDataManager的信号到本地信号
        if hasattr(self._shared_data, 'data_changed'):
            self._shared_data.data_changed.connect(self._on_shared_data_changed)
    
    def _on_shared_data_changed(self, key: str, value: Any):
        """处理SharedDataManager的数据变化"""
        if key == 'hole_collection' and isinstance(value, HoleCollection):
            self.hole_collection_changed.emit(value)
        elif key == 'current_project':
            self.project_changed.emit(value)
    
    # IHoleDataProvider 实现
    def get_hole_collection(self) -> Optional[HoleCollection]:
        """获取孔位集合"""
        data = self._shared_data.get_data('hole_collection')
        return data if isinstance(data, HoleCollection) else None
    
    def get_hole_by_id(self, hole_id: str) -> Optional[HoleData]:
        """根据ID获取单个孔位"""
        collection = self.get_hole_collection()
        if collection:
            for hole in collection.holes:
                if hole.hole_id == hole_id:
                    return hole
        return None
    
    def subscribe_to_changes(self, callback: Callable[[HoleCollection], None]) -> str:
        """订阅数据变化"""
        subscription_id = f"sub_{self._subscription_counter}"
        self._subscription_counter += 1
        self._subscribers[subscription_id] = callback
        
        # 连接到信号
        self.hole_collection_changed.connect(callback)
        
        return subscription_id
    
    def unsubscribe(self, subscription_id: str):
        """取消订阅"""
        if subscription_id in self._subscribers:
            callback = self._subscribers.pop(subscription_id)
            try:
                self.hole_collection_changed.disconnect(callback)
            except:
                pass
    
    # IHoleDataWriter 实现
    def update_hole_status(self, hole_id: str, status: HoleStatus) -> bool:
        """更新孔位状态"""
        collection = self.get_hole_collection()
        if collection:
            for hole in collection.holes:
                if hole.hole_id == hole_id:
                    hole.status = status
                    self.hole_status_changed.emit(hole_id, status)
                    # 触发集合更新
                    self.hole_collection_changed.emit(collection)
                    return True
        return False
    
    def update_hole_collection(self, collection: HoleCollection):
        """更新整个孔位集合"""
        self._shared_data.set_data('hole_collection', collection)
    
    # ISectorDataProvider 实现
    def get_sector_assignments(self) -> Dict[str, int]:
        """获取孔位到扇形的分配"""
        return self._shared_data.get_data('sector_assignments') or {}
    
    def get_holes_by_sector(self, sector_id: int) -> List[HoleData]:
        """获取指定扇形的孔位"""
        collection = self.get_hole_collection()
        assignments = self.get_sector_assignments()
        
        if not collection or not assignments:
            return []
        
        result = []
        for hole in collection.holes:
            if assignments.get(hole.hole_id) == sector_id:
                result.append(hole)
        
        return result
    
    # IProjectDataProvider 实现
    def get_current_project(self) -> Optional[str]:
        """获取当前项目名称"""
        return self._shared_data.get_data('current_project')
    
    def get_current_workpiece(self) -> Optional[str]:
        """获取当前工件ID"""
        return self._shared_data.get_data('current_workpiece')
    
    def get_project_metadata(self) -> Dict[str, Any]:
        """获取项目元数据"""
        return {
            'project': self.get_current_project(),
            'workpiece': self.get_current_workpiece(),
            'dxf_file': self._shared_data.get_data('dxf_file'),
            'hole_count': len(self.get_hole_collection().holes) if self.get_hole_collection() else 0
        }