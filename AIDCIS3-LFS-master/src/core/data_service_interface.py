"""
数据服务接口抽象层
解决SharedDataManager全局状态滥用问题
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus
from src.core_business.graphics.sector_types import SectorQuadrant


class IDataService(ABC):
    """数据服务接口 - 解决全局状态问题的抽象层"""
    
    @abstractmethod
    def get_hole_collection(self) -> Optional[HoleCollection]:
        """获取当前孔位集合"""
        pass
    
    @abstractmethod
    def set_hole_collection(self, collection: HoleCollection) -> None:
        """设置孔位集合"""
        pass
    
    @abstractmethod
    def get_sector_holes(self, sector: SectorQuadrant) -> List[HoleData]:
        """获取指定扇形的孔位"""
        pass
    
    @abstractmethod
    def update_hole_status(self, hole_id: str, status: HoleStatus) -> None:
        """更新孔位状态"""
        pass
    
    @abstractmethod
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        pass
    
    @abstractmethod
    def clear_cache(self) -> None:
        """清除缓存"""
        pass


class IDataServiceFactory(ABC):
    """数据服务工厂接口"""
    
    @abstractmethod
    def create_data_service(self) -> IDataService:
        """创建数据服务实例"""
        pass


class DataServiceAdapter(IDataService):
    """
    数据服务适配器
    将现有的SharedDataManager包装为服务接口
    """
    
    def __init__(self, shared_data_manager):
        self._shared_data_manager = shared_data_manager
        
    def get_hole_collection(self) -> Optional[HoleCollection]:
        return self._shared_data_manager.get_hole_collection()
    
    def set_hole_collection(self, collection: HoleCollection) -> None:
        self._shared_data_manager.set_data('hole_collection', collection)
    
    def get_sector_holes(self, sector: SectorQuadrant) -> List[HoleData]:
        return self._shared_data_manager.get_sector_holes(sector)
    
    def update_hole_status(self, hole_id: str, status: HoleStatus) -> None:
        self._shared_data_manager.update_hole_status(hole_id, status)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        return self._shared_data_manager.get_performance_stats()
    
    def clear_cache(self) -> None:
        self._shared_data_manager.clear_cache()


class DefaultDataServiceFactory(IDataServiceFactory):
    """默认数据服务工厂"""
    
    def __init__(self):
        self._shared_data_manager = None
    
    def create_data_service(self) -> IDataService:
        # 延迟创建，避免循环依赖
        if self._shared_data_manager is None:
            from src.core.shared_data_manager import SharedDataManager
            self._shared_data_manager = SharedDataManager()
        
        return DataServiceAdapter(self._shared_data_manager)


# 全局工厂实例（将逐步移除）
_data_service_factory: Optional[IDataServiceFactory] = None


def get_data_service_factory() -> IDataServiceFactory:
    """获取数据服务工厂（全局访问点，将逐步移除）"""
    global _data_service_factory
    if _data_service_factory is None:
        _data_service_factory = DefaultDataServiceFactory()
    return _data_service_factory


def set_data_service_factory(factory: IDataServiceFactory) -> None:
    """设置数据服务工厂（用于依赖注入）"""
    global _data_service_factory
    _data_service_factory = factory


# 便捷访问函数（过渡期使用，最终将移除）
def get_data_service() -> IDataService:
    """获取数据服务实例"""
    return get_data_service_factory().create_data_service()