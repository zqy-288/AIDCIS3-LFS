"""
业务服务层
封装所有业务逻辑，减少MainWindow的直接业务依赖
整合了缓存管理功能，提供统一的业务服务接口
"""

from typing import Optional, Dict, Any, List, Callable
from pathlib import Path
from functools import wraps
import time
import logging

# 业务服务接口
class BusinessService:
    """
    统一的业务服务接口
    聚合所有业务功能，提供简洁的API
    集成了BusinessCacheManager的缓存功能
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 延迟初始化各个服务组件
        self._dxf_parser = None
        self._data_adapter = None
        self._status_manager = None
        self._hole_numbering_service = None
        self._product_manager = None
        self._shared_data_manager = None
        self._path_manager = None
        self._cache_manager = None
        
        self.current_product = None  # 当前选择的产品
        
        # 缓存配置
        self._cache_enabled = True
        self._cache_ttl = 300  # 5分钟默认TTL
        self._performance_stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'total_operations': 0,
            'average_response_time': 0.0
        }
        
    @property
    def dxf_parser(self):
        """获取DXF解析器（延迟加载）"""
        if self._dxf_parser is None:
            from src.shared.services.parsers.dxf_parser import DXFParser
            self._dxf_parser = DXFParser()
        return self._dxf_parser
        
    @property
    def data_adapter(self):
        """获取数据适配器（延迟加载）"""
        if self._data_adapter is None:
            from src.shared.services.adapters.data_model_adapter import DataAdapter
            self._data_adapter = DataAdapter()
        return self._data_adapter
        
    @property
    def status_manager(self):
        """获取状态管理器（延迟加载）"""
        if self._status_manager is None:
            from src.shared.services.status_manager import StatusManager
            self._status_manager = StatusManager()
        return self._status_manager
        
    @property
    def hole_numbering_service(self):
        """获取孔位编号服务（延迟加载）"""
        if self._hole_numbering_service is None:
            from src.core.services.numbering.hole_numbering_service import HoleNumberingService
            self._hole_numbering_service = HoleNumberingService()
        return self._hole_numbering_service
        
    @property
    def product_manager(self):
        """获取产品管理器（延迟加载）"""
        if self._product_manager is None:
            from src.shared.models.product_model import ProductModelManager
            # 创建ProductModelManager实例
            self._product_manager = ProductModelManager()
        return self._product_manager
        
    @property
    def shared_data_manager(self):
        """获取共享数据管理器（延迟加载）"""
        if self._shared_data_manager is None:
            from src.core.shared_data_manager import SharedDataManager
            self._shared_data_manager = SharedDataManager()
        return self._shared_data_manager
    
    @property
    def path_manager(self):
        """获取路径管理器（延迟加载）"""
        if self._path_manager is None:
            from src.core.data_path_manager import DataPathManager
            self._path_manager = DataPathManager()
        return self._path_manager
    
    @property
    def cache_manager(self):
        """获取缓存管理器（延迟加载）"""
        if self._cache_manager is None:
            try:
                from src.shared.services.cache.business_cache_manager import BusinessCacheManager
                self._cache_manager = BusinessCacheManager()
            except ImportError:
                self.logger.warning("BusinessCacheManager not available, caching disabled")
                self._cache_enabled = False
        return self._cache_manager
        
    # 缓存装饰器
    def cached_operation(self, cache_key: str = None, ttl: int = None):
        """缓存操作装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self._cache_enabled or not self.cache_manager:
                    return func(*args, **kwargs)
                
                # 生成缓存键
                if cache_key:
                    final_key = cache_key
                else:
                    # 基于函数名和参数生成键
                    final_key = f"{func.__name__}_{str(args)}_{str(kwargs)}"
                
                # 尝试从缓存获取
                cached_result = self.cache_manager.get(final_key, level="L3_business")
                if cached_result is not None:
                    self._performance_stats['cache_hits'] += 1
                    return cached_result
                
                self._performance_stats['cache_misses'] += 1
                
                # 执行实际操作
                start_time = time.time()
                result = func(*args, **kwargs)
                elapsed_time = time.time() - start_time
                
                # 更新性能统计
                self._update_performance_stats(elapsed_time)
                
                # 缓存结果
                if result is not None:
                    self.cache_manager.set(
                        final_key, 
                        result, 
                        ttl=ttl or self._cache_ttl,
                        level="L3_business"
                    )
                
                return result
            return wrapper
        return decorator
    
    def _update_performance_stats(self, elapsed_time: float):
        """更新性能统计"""
        self._performance_stats['total_operations'] += 1
        total = self._performance_stats['total_operations']
        current_avg = self._performance_stats['average_response_time']
        self._performance_stats['average_response_time'] = (
            (current_avg * (total - 1) + elapsed_time) / total
        )
    
    # 业务方法封装
    def parse_dxf_file(self, file_path: str) -> Optional[Any]:
        """
        解析DXF文件（带缓存）
        
        Args:
            file_path: DXF文件路径
            
        Returns:
            解析后的孔位集合
        """
        # 使用缓存装饰器的手动版本
        if self._cache_enabled and self.cache_manager:
            cache_key = f"dxf_parse_{file_path}"
            cached_result = self.cache_manager.get(cache_key, level="L3_business")
            if cached_result is not None:
                self._performance_stats['cache_hits'] += 1
                self.logger.info(f"DXF解析命中缓存: {file_path}")
                return cached_result
        
        self._performance_stats['cache_misses'] += 1
        
        try:
            start_time = time.time()
            # 使用正确的方法名 parse_file 而不是 parse
            result = self.dxf_parser.parse_file(file_path)
            elapsed_time = time.time() - start_time
            
            self._update_performance_stats(elapsed_time)
            
            # 缓存结果
            if result and self._cache_enabled and self.cache_manager:
                self.cache_manager.set(
                    cache_key,
                    result,
                    ttl=600,  # DXF解析结果缓存10分钟
                    level="L3_business"
                )
            
            return result
        except Exception as e:
            self.logger.error(f"Error parsing DXF file: {e}")
            return None
            
    def update_hole_status(self, hole_id: str, status: str) -> bool:
        """
        更新孔位状态
        
        Args:
            hole_id: 孔位ID
            status: 新状态
            
        Returns:
            是否更新成功
        """
        try:
            self.status_manager.update_status(hole_id, status)
            return True
        except Exception as e:
            print(f"Error updating hole status: {e}")
            return False
            
    def get_product_list(self) -> List[str]:
        """获取产品列表"""
        try:
            # 使用get_all_products方法获取所有产品
            products = self.product_manager.get_all_products()
            # 返回产品名称列表
            return [product.model_name for product in products]
        except Exception as e:
            print(f"Error getting product list: {e}")
            return []
        
    def select_product(self, product_identifier: str) -> bool:
        """选择产品"""
        try:
            # 支持通过产品名称或ID选择产品
            product = None
            
            # 首先尝试按名称查找
            if not product_identifier.isdigit():
                product = self.product_manager.get_product_by_name(product_identifier)
                print(f"🔍 [BusinessService] 按名称查找产品: {product_identifier}")
            
            # 如果按名称未找到，或者输入是数字，尝试按ID查找
            if not product and product_identifier.isdigit():
                product = self.product_manager.get_product_by_id(int(product_identifier))
                print(f"🔍 [BusinessService] 按ID查找产品: {product_identifier}")
            
            if not product:
                print(f"❌ [BusinessService] 产品未找到: {product_identifier}")
                return False
            
            print(f"✅ [BusinessService] 找到产品: {product.model_name} (ID: {product.id})")
            
            # 保存当前选择的产品
            self.current_product = product
            
            # 可以在shared_data_manager中保存当前产品信息
            if hasattr(self.shared_data_manager, 'set_current_product'):
                self.shared_data_manager.set_current_product(product)
                
            # 如果产品有关联的DXF文件，自动加载
            if product.dxf_file_path:
                print(f"🔍 [BusinessService] 产品有关联的DXF文件: {product.dxf_file_path}")
                # 使用路径管理器解析DXF路径
                resolved_path = self.path_manager.resolve_dxf_path(product.dxf_file_path)
                print(f"🔍 [BusinessService] 解析后的DXF路径: {resolved_path}")
                if resolved_path and Path(resolved_path).exists():
                    print(f"✅ [BusinessService] 自动加载产品关联的DXF文件: {resolved_path}")
                    hole_collection = self.parse_dxf_file(resolved_path)
                    print(f"🔍 [BusinessService] DXF解析结果: {hole_collection}")
                    if hole_collection:
                        # 应用孔位编号
                        hole_collection = self.apply_hole_numbering(hole_collection, strategy="grid")
                        # 保存到shared_data_manager
                        self.set_hole_collection(hole_collection)
                        print(f"✅ [BusinessService] 成功加载 {len(hole_collection.holes)} 个孔位")
                        # 通知数据已加载
                        self.shared_data_manager.data_changed.emit("hole_collection", hole_collection)
                    else:
                        print(f"❌ [BusinessService] DXF文件解析失败")
                else:
                    print(f"❌ [BusinessService] 产品关联的DXF文件不存在或路径解析失败")
                    print(f"   原始路径: {product.dxf_file_path}")
                    print(f"   解析路径: {resolved_path}")
                    print(f"   文件存在: {Path(resolved_path).exists() if resolved_path else False}")
            else:
                print(f"🔍 [BusinessService] 产品没有关联的DXF文件")
                
            return True
        except Exception as e:
            print(f"Error selecting product: {e}")
            return False
            
    def get_hole_collection(self) -> Optional[Any]:
        """获取当前孔位集合"""
        return self.shared_data_manager.get_hole_collection()
        
    def set_hole_collection(self, collection: Any) -> bool:
        """设置孔位集合"""
        try:
            self.shared_data_manager.set_hole_collection(collection)
            return True
        except Exception as e:
            print(f"Error setting hole collection: {e}")
            return False
            
    def apply_hole_numbering(self, collection: Any, strategy: str = "grid") -> Any:
        """
        应用孔位编号
        
        Args:
            collection: 孔位集合
            strategy: 编号策略
            
        Returns:
            编号后的孔位集合
        """
        try:
            # apply_numbering 只接受一个参数
            self.hole_numbering_service.apply_numbering(collection)
            return collection
        except Exception as e:
            print(f"Error applying hole numbering: {e}")
            return collection
            
    def cleanup(self):
        """清理资源"""
        # 清理各个服务的资源
        if self._status_manager:
            self._status_manager.cleanup()
        if self._shared_data_manager:
            self._shared_data_manager.cleanup()
        if self._cache_manager:
            self._cache_manager.clear_all_caches()
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        stats = self._performance_stats.copy()
        
        if self._cache_enabled and self.cache_manager:
            cache_stats = self.cache_manager.get_cache_stats()
            stats['cache_details'] = cache_stats
        
        # 计算缓存命中率
        total = stats['cache_hits'] + stats['cache_misses']
        stats['cache_hit_rate'] = (
            stats['cache_hits'] / total if total > 0 else 0.0
        )
        
        return stats
    
    def clear_cache(self, level: str = None):
        """清空缓存"""
        if self._cache_enabled and self.cache_manager:
            if level:
                self.cache_manager.clear_cache(level)
            else:
                self.cache_manager.clear_all_caches()
            self.logger.info(f"缓存已清空: {level or '所有级别'}")
    
    def set_cache_enabled(self, enabled: bool):
        """启用/禁用缓存"""
        self._cache_enabled = enabled
        self.logger.info(f"缓存{'已启用' if enabled else '已禁用'}")
    
    def set_cache_ttl(self, ttl: int):
        """设置默认缓存TTL"""
        self._cache_ttl = ttl
        self.logger.info(f"默认缓存TTL设置为: {ttl}秒")
            
    def prefetch_product_data(self, product_name: str):
        """预取产品数据到缓存"""
        if not self._cache_enabled or not self.cache_manager:
            return
        
        try:
            # 预取产品信息
            product = self.product_manager.get_product_by_name(product_name)
            if product:
                cache_key = f"product_{product_name}"
                self.cache_manager.set(
                    cache_key,
                    product,
                    ttl=3600,  # 产品信息缓存1小时
                    level="L3_business"
                )
                
                # 如果有关联的DXF文件，也预取
                if product.dxf_file_path:
                    resolved_path = self.path_manager.resolve_dxf_path(product.dxf_file_path)
                    if resolved_path and Path(resolved_path).exists():
                        self.parse_dxf_file(resolved_path)  # 这会自动缓存
                        
                self.logger.info(f"产品数据已预取到缓存: {product_name}")
        except Exception as e:
            self.logger.error(f"预取产品数据失败: {e}")
            
# 全局业务服务实例
_global_business_service = None


def get_business_service() -> BusinessService:
    """获取全局业务服务实例"""
    global _global_business_service
    if _global_business_service is None:
        _global_business_service = BusinessService()
    return _global_business_service