"""
孔位数据适配器
负责从SharedDataManager获取数据并适配为视图组件可用的格式
"""

from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal

from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus
from src.core_business.graphics.sector_controllers import UnifiedLogger
from src.core.shared_data_manager import SharedDataManager


@dataclass
class DataSnapshot:
    """数据快照"""
    hole_collection: Optional[HoleCollection] = None
    metadata: Dict[str, Any] = None
    timestamp: float = 0.0
    

class HoleDataAdapter(QObject):
    """
    孔位数据适配器
    
    作为SharedDataManager和视图组件之间的桥梁：
    1. 从SharedDataManager获取原始数据
    2. 转换为HoleCollection格式
    3. 提供数据变化通知机制
    4. 管理数据缓存和版本
    """
    
    # 信号
    data_loaded = Signal(HoleCollection)  # 数据加载完成
    data_updated = Signal(dict)           # 数据更新（增量）
    data_cleared = Signal()               # 数据清除
    status_changed = Signal(str, HoleStatus)  # 孔位状态变化
    
    def __init__(self, shared_data_manager: Optional[SharedDataManager] = None):
        super().__init__()
        self.logger = UnifiedLogger("HoleDataAdapter")
        self.shared_data_manager = shared_data_manager or SharedDataManager()
        
        # 数据缓存
        self._current_snapshot: Optional[DataSnapshot] = None
        self._hole_collection_cache: Optional[HoleCollection] = None
        self._listeners: List[Callable] = []
        
        # 连接SharedDataManager的信号
        self._connect_shared_data_signals()
        
    def _connect_shared_data_signals(self):
        """连接SharedDataManager的信号"""
        try:
            # 监听数据变化
            if hasattr(self.shared_data_manager, 'data_changed'):
                self.shared_data_manager.data_changed.connect(self._on_shared_data_changed)
                
            # 监听状态更新
            if hasattr(self.shared_data_manager, 'hole_status_updated'):
                self.shared_data_manager.hole_status_updated.connect(self._on_hole_status_updated)
                
            self.logger.info("已连接到SharedDataManager信号", "🔌")
        except Exception as e:
            self.logger.error(f"连接SharedDataManager信号失败: {e}", "❌")
    
    def get_hole_collection(self) -> Optional[HoleCollection]:
        """
        获取当前的孔位集合
        
        Returns:
            HoleCollection或None
        """
        # 优先返回缓存
        if self._hole_collection_cache:
            return self._hole_collection_cache
            
        # 从SharedDataManager获取数据
        try:
            # 获取孔位数据
            holes_data = self._extract_holes_from_shared_data()
            if not holes_data:
                self.logger.warning("SharedDataManager中没有孔位数据", "⚠️")
                return None
                
            # 创建HoleCollection
            hole_collection = self._create_hole_collection(holes_data)
            
            # 缓存结果
            self._hole_collection_cache = hole_collection
            
            # 创建快照
            import time
            self._current_snapshot = DataSnapshot(
                hole_collection=hole_collection,
                metadata=self._extract_metadata(),
                timestamp=time.time()
            )
            
            self.logger.info(f"成功获取孔位数据，共{len(hole_collection)}个孔", "✅")
            return hole_collection
            
        except Exception as e:
            self.logger.error(f"获取孔位数据失败: {e}", "❌")
            return None
    
    def _extract_holes_from_shared_data(self) -> Optional[Dict[str, Any]]:
        """从SharedDataManager提取孔位数据"""
        # 尝试多种可能的数据获取方式
        
        # 方式1：直接获取hole_collection
        if hasattr(self.shared_data_manager, 'get_hole_collection'):
            collection = self.shared_data_manager.get_hole_collection()
            if collection:
                return {'type': 'collection', 'data': collection}
                
        # 方式2：获取当前产品数据
        if hasattr(self.shared_data_manager, 'get_current_product'):
            product = self.shared_data_manager.get_current_product()
            if product and hasattr(product, 'holes'):
                return {'type': 'product', 'data': product.holes}
                
        # 方式3：获取检测数据
        if hasattr(self.shared_data_manager, 'get_detection_data'):
            detection_data = self.shared_data_manager.get_detection_data()
            if detection_data and 'holes' in detection_data:
                return {'type': 'detection', 'data': detection_data['holes']}
                
        # 方式4：通用数据获取
        if hasattr(self.shared_data_manager, 'get_data'):
            data = self.shared_data_manager.get_data('holes')
            if data:
                return {'type': 'generic', 'data': data}
                
        return None
    
    def _create_hole_collection(self, holes_data: Dict[str, Any]) -> HoleCollection:
        """创建HoleCollection对象"""
        data_type = holes_data.get('type')
        data = holes_data.get('data')
        
        # 如果已经是HoleCollection，直接返回
        if data_type == 'collection' and isinstance(data, HoleCollection):
            return data
            
        # 否则，需要转换数据
        hole_collection = HoleCollection(holes={})
        
        if isinstance(data, dict):
            # 字典格式的孔位数据
            for hole_id, hole_info in data.items():
                hole = self._create_hole_from_data(hole_id, hole_info)
                if hole:
                    hole_collection.add_hole(hole)
                    
        elif isinstance(data, list):
            # 列表格式的孔位数据
            for hole_info in data:
                hole = self._create_hole_from_data(None, hole_info)
                if hole:
                    hole_collection.add_hole(hole)
                    
        return hole_collection
    
    def _create_hole_from_data(self, hole_id: Optional[str], hole_info: Any) -> Optional[HoleData]:
        """从数据创建HoleData对象"""
        try:
            # 如果已经是HoleData对象
            if isinstance(hole_info, HoleData):
                return hole_info
                
            # 从字典创建
            if isinstance(hole_info, dict):
                return HoleData(
                    hole_id=hole_id or hole_info.get('hole_id') or hole_info.get('id'),
                    center_x=float(hole_info.get('center_x', 0)),
                    center_y=float(hole_info.get('center_y', 0)),
                    radius=float(hole_info.get('radius', 10)),
                    status=HoleStatus(hole_info.get('status', HoleStatus.PENDING.value)),
                    layer=hole_info.get('layer', '0'),
                    row=hole_info.get('row'),
                    column=hole_info.get('column'),
                    region=hole_info.get('region'),
                    metadata=hole_info.get('metadata', {})
                )
                
        except Exception as e:
            self.logger.error(f"创建HoleData失败: {e}", "❌")
            
        return None
    
    def _extract_metadata(self) -> Dict[str, Any]:
        """提取元数据"""
        metadata = {}
        
        # 从SharedDataManager获取产品信息
        if hasattr(self.shared_data_manager, 'get_current_product'):
            product = self.shared_data_manager.get_current_product()
            if product:
                metadata['product_name'] = getattr(product, 'name', 'Unknown')
                metadata['product_id'] = getattr(product, 'id', None)
                
        # 获取检测参数
        if hasattr(self.shared_data_manager, 'get_detection_params'):
            params = self.shared_data_manager.get_detection_params()
            if params:
                metadata['detection_params'] = params
                
        return metadata
    
    def refresh_data(self) -> bool:
        """
        刷新数据
        
        Returns:
            是否成功刷新
        """
        self.logger.info("刷新数据...", "🔄")
        
        # 清除缓存
        self._hole_collection_cache = None
        
        # 重新获取数据
        hole_collection = self.get_hole_collection()
        
        if hole_collection:
            # 发送数据加载信号
            self.data_loaded.emit(hole_collection)
            
            # 通知所有监听器
            for listener in self._listeners:
                try:
                    listener(hole_collection)
                except Exception as e:
                    self.logger.error(f"通知监听器失败: {e}", "❌")
                    
            return True
            
        return False
    
    def subscribe(self, callback: Callable[[HoleCollection], None]):
        """
        订阅数据变化
        
        Args:
            callback: 回调函数
        """
        if callback not in self._listeners:
            self._listeners.append(callback)
            self.logger.debug(f"添加数据订阅者: {callback.__name__}", "➕")
    
    def unsubscribe(self, callback: Callable[[HoleCollection], None]):
        """
        取消订阅
        
        Args:
            callback: 回调函数
        """
        if callback in self._listeners:
            self._listeners.remove(callback)
            self.logger.debug(f"移除数据订阅者: {callback.__name__}", "➖")
    
    def _on_shared_data_changed(self, change_type: str, data: Any):
        """处理SharedDataManager的数据变化"""
        self.logger.info(f"收到数据变化通知: {change_type}", "📨")
        
        if change_type == "full_reload":
            # 完全重新加载
            self.refresh_data()
        elif change_type == "incremental":
            # 增量更新
            self.data_updated.emit(data)
        elif change_type == "clear":
            # 清除数据
            self._hole_collection_cache = None
            self._current_snapshot = None
            self.data_cleared.emit()
    
    def _on_hole_status_updated(self, hole_id: str, new_status: str):
        """处理孔位状态更新"""
        try:
            status = HoleStatus(new_status)
            self.status_changed.emit(hole_id, status)
            
            # 更新缓存中的状态
            if self._hole_collection_cache:
                hole = self._hole_collection_cache.get_hole(hole_id)
                if hole:
                    hole.status = status
                    
        except Exception as e:
            self.logger.error(f"处理状态更新失败: {e}", "❌")
    
    def get_snapshot(self) -> Optional[DataSnapshot]:
        """获取当前数据快照"""
        return self._current_snapshot
    
    def clear_cache(self):
        """清除所有缓存"""
        self._hole_collection_cache = None
        self._current_snapshot = None
        self.logger.info("缓存已清除", "🗑️")