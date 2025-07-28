"""
数据接口定义 - 用于替代全局SharedDataManager
遵循接口隔离原则(ISP)和依赖倒置原则(DIP)
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Callable
from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus


class IHoleDataProvider(ABC):
    """孔位数据提供者接口"""
    
    @abstractmethod
    def get_hole_collection(self) -> Optional[HoleCollection]:
        """获取孔位集合"""
        pass
    
    @abstractmethod
    def get_hole_by_id(self, hole_id: str) -> Optional[HoleData]:
        """根据ID获取单个孔位"""
        pass
    
    @abstractmethod
    def subscribe_to_changes(self, callback: Callable[[HoleCollection], None]) -> str:
        """订阅数据变化，返回订阅ID"""
        pass
    
    @abstractmethod
    def unsubscribe(self, subscription_id: str):
        """取消订阅"""
        pass


class IHoleDataWriter(ABC):
    """孔位数据写入者接口"""
    
    @abstractmethod
    def update_hole_status(self, hole_id: str, status: HoleStatus) -> bool:
        """更新孔位状态"""
        pass
    
    @abstractmethod
    def update_hole_collection(self, collection: HoleCollection):
        """更新整个孔位集合"""
        pass


class ISectorDataProvider(ABC):
    """扇形数据提供者接口"""
    
    @abstractmethod
    def get_sector_assignments(self) -> Dict[str, int]:
        """获取孔位到扇形的分配"""
        pass
    
    @abstractmethod
    def get_holes_by_sector(self, sector_id: int) -> List[HoleData]:
        """获取指定扇形的孔位"""
        pass


class IProjectDataProvider(ABC):
    """项目数据提供者接口"""
    
    @abstractmethod
    def get_current_project(self) -> Optional[str]:
        """获取当前项目名称"""
        pass
    
    @abstractmethod
    def get_current_workpiece(self) -> Optional[str]:
        """获取当前工件ID"""
        pass
    
    @abstractmethod
    def get_project_metadata(self) -> Dict[str, Any]:
        """获取项目元数据"""
        pass


class IDataEventBus(ABC):
    """数据事件总线接口 - 用于组件间通信"""
    
    @abstractmethod
    def publish(self, event_type: str, data: Any):
        """发布事件"""
        pass
    
    @abstractmethod
    def subscribe(self, event_type: str, handler: Callable[[Any], None]) -> str:
        """订阅事件，返回订阅ID"""
        pass
    
    @abstractmethod
    def unsubscribe(self, subscription_id: str):
        """取消订阅"""
        pass


class IDataRepository(IHoleDataProvider, IHoleDataWriter, ISectorDataProvider, IProjectDataProvider):
    """综合数据仓库接口 - 聚合所有数据操作"""
    pass