"""
共享数据管理器
管理全局数据状态，避免重复处理和初始化
"""

from typing import Dict, Optional, Any, Tuple, List
from PySide6.QtCore import QObject, Signal

from src.core_business.graphics.unified_sector_adapter import UnifiedSectorAdapter
from src.core_business.models.hole_data import HoleCollection, HoleStatus
from src.core_business.graphics.sector_types import SectorQuadrant, SectorProgress
from src.core_business.hole_numbering_service import HoleNumberingService


class SharedDataManager(QObject):
    """
    共享数据管理器
    确保所有组件使用相同的处理后数据，避免重复计算
    """
    
    # 信号
    data_loaded = Signal(dict)  # 数据加载完成
    cache_hit = Signal(str)     # 缓存命中
    performance_updated = Signal(dict)  # 性能更新
    data_changed = Signal(str, object)  # 数据变化信号 (change_type, data)
    hole_status_updated = Signal(str, str)  # 孔位状态更新 (hole_id, status)
    
    # 单例模式
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # 避免重复初始化
        if hasattr(self, '_initialized'):
            return
            
        super().__init__()
        
        # 统一适配器实例（单例）
        self.unified_adapter = UnifiedSectorAdapter()
        
        # 孔位编号服务（单例）
        self.hole_numbering_service = HoleNumberingService()
        
        # 共享数据状态
        self.current_hole_collection: Optional[HoleCollection] = None
        self.sector_assignments: Dict[str, SectorQuadrant] = {}
        self.sector_progresses: Dict[SectorQuadrant, SectorProgress] = {}
        self.processed_data_available = False
        
        # 通用数据存储
        self._data_store: Dict[str, Any] = {}
        
        # 性能统计
        self.performance_stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'total_requests': 0,
            'duplicate_prevented': 0
        }
        
        # 连接适配器信号
        self.unified_adapter.overall_progress_updated.connect(self._on_progress_updated)
        self.unified_adapter.unified_debug_info.connect(self._on_debug_info)
        
        self._initialized = True
        print("🚀 [共享数据管理器] 初始化完成")
    
    def set_hole_collection(self, hole_collection: HoleCollection) -> None:
        """设置当前孔位集合"""
        self.current_hole_collection = hole_collection
        self.data_changed.emit("hole_collection", hole_collection)
        
    def get_hole_collection(self) -> Optional[HoleCollection]:
        """获取当前孔位集合"""
        return self.current_hole_collection
    
    def get_processed_data(self, hole_collection: HoleCollection) -> Tuple[HoleCollection, Dict[str, Any]]:
        """
        获取处理后的数据
        返回: (处理后的孔位集合, 扇形分配和相关数据)
        """
        self.performance_stats['total_requests'] += 1
        
        # 首先检查统一适配器的缓存状态，避免重复处理
        data_hash = self.unified_adapter._calculate_data_hash(hole_collection)
        adapter_cached = self.unified_adapter._is_cached_data_valid(data_hash)
        
        # 检查共享管理器是否是相同数据
        shared_manager_cached = self._is_same_data(hole_collection)
        
        if shared_manager_cached and adapter_cached:
            self.performance_stats['cache_hits'] += 1
            self.cache_hit.emit(f"缓存命中: {len(hole_collection.holes)} 个孔位")
            print(f"🎯 [共享数据管理器] 完全缓存命中，无需任何处理")
            
            # 返回共享数据
            shared_data = self.unified_adapter.get_shared_data()
            return hole_collection, shared_data
        
        # 需要处理数据
        self.performance_stats['cache_misses'] += 1
        print(f"🔄 [共享数据管理器] 处理数据: {len(hole_collection.holes)} 个孔位 (共享缓存:{shared_manager_cached}, 适配器缓存:{adapter_cached})")
        
        # 首先应用A/B侧网格编号（如果还没有编号）
        first_hole = next(iter(hole_collection.holes.values())) if hole_collection.holes else None
        has_no_ids = first_hole and first_hole.hole_id is None
        print(f"🔍 [共享数据管理器] 编号检查:")
        print(f"   - 孔位数量: {len(hole_collection.holes)}")
        print(f"   - 第一个孔位hole_id: {first_hole.hole_id if first_hole else 'None'}")
        print(f"   - 需要重新编号: {has_no_ids}")
        
        if hole_collection.holes and has_no_ids:
            print(f"🔢 [共享数据管理器] 应用A/B侧网格编号...")
            self.hole_numbering_service.apply_numbering(hole_collection)
            print(f"✅ [共享数据管理器] 编号完成")
        else:
            print(f"⏭️ [共享数据管理器] 跳过编号，孔位已有ID")
        
        # 使用统一适配器处理数据
        self.unified_adapter.load_hole_collection(hole_collection)
        
        # 更新共享状态并保存扇形分配结果
        self.current_hole_collection = hole_collection
        self.sector_assignments = self.unified_adapter.unified_manager.sector_assignments.copy()
        self.sector_progresses = self.unified_adapter.sector_progresses.copy()
        self.processed_data_available = True
        
        print(f"📊 [共享数据管理器] 扇形分配完成:")
        print(f"   - 总分配: {len(self.sector_assignments)} 个孔位")
        if self.sector_assignments:
            from collections import Counter
            sector_counts = Counter(self.sector_assignments.values())
            for sector, count in sector_counts.items():
                print(f"   - {sector.name}: {count} 个孔位")
        
        # 获取处理后的共享数据（包含扇形分配结果）
        shared_data = self.unified_adapter.get_shared_data()
        shared_data['sector_assignments'] = self.sector_assignments  # 直接提供扇形分配
        shared_data['ready_for_use'] = True  # 标记数据已就绪
        
        # 发射数据加载完成信号
        self.data_loaded.emit({
            'hole_count': len(hole_collection.holes),
            'sector_count': len(self.sector_assignments),
            'cache_used': shared_data.get('is_cached', False)
        })
        
        print(f"✅ [共享数据管理器] 数据处理完成，扇形分配已就绪")
        return hole_collection, shared_data
    
    def load_with_shared_data(self, component_name: str, hole_collection: HoleCollection) -> Dict[str, Any]:
        """
        为指定组件加载共享数据
        component_name: 组件名称（用于日志）
        """
        print(f"📊 [{component_name}] 请求共享数据")
        
        # 检查是否需要重复处理
        if self._is_same_data(hole_collection):
            self.performance_stats['duplicate_prevented'] += 1
            print(f"🎯 [{component_name}] 使用共享数据，避免重复处理")
        
        # 获取处理后的数据
        processed_collection, shared_data = self.get_processed_data(hole_collection)
        
        print(f"✅ [{component_name}] 共享数据加载完成")
        return shared_data
    
    def _is_same_data(self, hole_collection: HoleCollection) -> bool:
        """
        检查是否是相同的数据（基于孔位ID，而不是坐标）
        """
        if not self.current_hole_collection:
            return False
        
        # 比较孔位数量
        if len(hole_collection.holes) != len(self.current_hole_collection.holes):
            return False
        
        # 比较孔位ID（不比较坐标，因为坐标会被旋转修改）
        current_ids = set(self.current_hole_collection.holes.keys())
        new_ids = set(hole_collection.holes.keys())
        
        return current_ids == new_ids
    
    def _on_progress_updated(self, progress_data: dict):
        """处理进度更新"""
        self.sector_progresses = progress_data.get('sector_progresses', {})
    
    def _on_debug_info(self, debug_msg: str):
        """处理调试信息"""
        if "缓存" in debug_msg or "Cache" in debug_msg:
            print(f"💾 [共享数据管理器] {debug_msg}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        total = self.performance_stats['total_requests']
        cache_rate = (self.performance_stats['cache_hits'] / total * 100) if total > 0 else 0
        
        return {
            **self.performance_stats,
            'cache_hit_rate': f"{cache_rate:.1f}%",
            'duplicate_prevention_rate': f"{self.performance_stats['duplicate_prevented'] / total * 100:.1f}%" if total > 0 else "0.0%",
            'adapter_stats': self.unified_adapter.get_performance_stats() if hasattr(self.unified_adapter, 'get_performance_stats') else {}
        }
    
    def clear_cache(self):
        """清空所有缓存数据"""
        self.unified_adapter.clear_cache()
        self.current_hole_collection = None
        self.sector_assignments.clear()
        self.sector_progresses.clear()
        self.processed_data_available = False
        
        # 重置统计
        self.performance_stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'total_requests': 0,
            'duplicate_prevented': 0
        }
        
        print("🧹 [共享数据管理器] 缓存已清空")
    
    def get_sector_holes(self, sector: SectorQuadrant) -> List:
        """直接获取扇形孔位，避免重复处理"""
        if not self.processed_data_available or not self.sector_assignments:
            print(f"⚠️ [共享数据管理器] 扇形数据未就绪")
            return []
        
        # 从已处理的数据中筛选
        sector_hole_ids = [hole_id for hole_id, assigned_sector in self.sector_assignments.items() 
                          if assigned_sector == sector]
        
        if self.current_hole_collection:
            sector_holes = [self.current_hole_collection.holes[hole_id] 
                           for hole_id in sector_hole_ids 
                           if hole_id in self.current_hole_collection.holes]
            print(f"🎯 [共享数据管理器] 直接返回扇形 {sector.name}: {len(sector_holes)} 个孔位")
            return sector_holes
        
        return []
    
    def is_data_ready(self) -> bool:
        """检查扇形数据是否已就绪"""
        return self.processed_data_available and bool(self.sector_assignments)
    
    def get_current_data_summary(self) -> Dict[str, Any]:
        """获取当前数据摘要"""
        if not self.processed_data_available:
            return {'status': 'no_data', 'message': '暂无数据'}
        
        return {
            'status': 'data_available',
            'hole_count': len(self.current_hole_collection.holes) if self.current_hole_collection else 0,
            'sector_count': len(self.sector_assignments),
            'sectors': {
                sector.value: len([h for h, s in self.sector_assignments.items() if s == sector])
                for sector in SectorQuadrant
            },
            'performance': self.get_performance_stats()
        }
    
    def get_hole_collection(self) -> Optional[HoleCollection]:
        """
        获取当前的孔位集合
        供HoleDataAdapter使用
        """
        return self.current_hole_collection
    
    def set_data(self, key: str, value: Any):
        """
        设置通用数据
        
        Args:
            key: 数据键
            value: 数据值
        """
        self._data_store[key] = value
        
        # 特殊处理hole_collection
        if key == 'hole_collection' and isinstance(value, HoleCollection):
            self.current_hole_collection = value
            self.processed_data_available = True
            self.data_changed.emit("full_reload", value)
            print(f"📥 [共享数据管理器] 设置孔位集合: {len(value)} 个孔位")
    
    def get_data(self, key: str) -> Any:
        """
        获取通用数据
        
        Args:
            key: 数据键
            
        Returns:
            数据值或None
        """
        return self._data_store.get(key)
    
    def update_hole_status(self, hole_id: str, new_status: HoleStatus):
        """
        更新孔位状态
        
        Args:
            hole_id: 孔位ID
            new_status: 新状态
        """
        if self.current_hole_collection and hole_id in self.current_hole_collection.holes:
            hole = self.current_hole_collection.holes[hole_id]
            hole.status = new_status
            self.hole_status_updated.emit(hole_id, new_status.value)
            print(f"🔄 [共享数据管理器] 更新孔位 {hole_id} 状态为 {new_status.value}")
    
    def get_current_product(self):
        """获取当前产品信息（兼容接口）"""
        return self._data_store.get('current_product')
    
    def set_current_product(self, product):
        """设置当前产品信息"""
        # 只存储产品的基本信息，避免SQL查询错误
        if hasattr(product, 'to_dict'):
            # 如果是ProductModel对象，转换为字典
            product_data = product.to_dict()
        elif hasattr(product, '__dict__'):
            # 如果有__dict__属性，提取基本信息
            product_data = {
                'id': getattr(product, 'id', None),
                'model_name': getattr(product, 'model_name', None),
                'standard_diameter': getattr(product, 'standard_diameter', None),
                'tolerance_upper': getattr(product, 'tolerance_upper', None),
                'tolerance_lower': getattr(product, 'tolerance_lower', None),
                'dxf_file_path': getattr(product, 'dxf_file_path', None)
            }
        else:
            # 如果是简单值，直接存储
            product_data = product
            
        self._data_store['current_product'] = product_data
        self.data_changed.emit('current_product', product_data)
    
    def get_detection_data(self):
        """获取检测数据（兼容接口）"""
        return self._data_store.get('detection_data')
    
    def get_detection_params(self):
        """获取检测参数（兼容接口）"""
        return self._data_store.get('detection_params')