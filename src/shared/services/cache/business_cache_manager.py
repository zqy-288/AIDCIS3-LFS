"""
业务逻辑缓存管理器
协调AIDCIS2模块的缓存机制，实现<100ms响应时间要求
"""

import asyncio
import time
import threading
from typing import Dict, Any, Optional, List, Callable, Tuple
from functools import wraps, lru_cache
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import weakref
import hashlib
import json

from src.core.dependency_injection import injectable, ServiceLifetime, get_container
from src.core.error_handler import get_error_handler, error_handler, ErrorCategory
from src.core.data.config_manager import get_config
from src.shared.models.hole_data import HoleData, HoleCollection


@dataclass
class CacheEntry:
    """缓存条目"""
    value: Any
    created_at: datetime
    access_count: int = 0
    last_access: datetime = field(default_factory=datetime.now)
    ttl_seconds: Optional[int] = None
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl_seconds is None:
            return False
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl_seconds)
    
    def access(self) -> Any:
        """访问缓存并更新统计"""
        self.access_count += 1
        self.last_access = datetime.now()
        return self.value


@dataclass
class CacheStats:
    """缓存统计信息"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_operations: int = 0
    average_response_time: float = 0.0
    cache_size: int = 0
    
    @property
    def hit_rate(self) -> float:
        """缓存命中率"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class CacheLevel:
    """缓存级别枚举"""
    L1_MEMORY = "L1_memory"      # 内存缓存
    L2_SPATIAL = "L2_spatial"    # 空间索引缓存
    L3_BUSINESS = "L3_business"  # 业务逻辑缓存


@injectable(ServiceLifetime.SINGLETON)
class BusinessCacheManager:
    """业务逻辑缓存管理器"""
    
    def __init__(self):
        self.error_handler = get_error_handler()
        self._lock = threading.RLock()
        
        # 从配置获取缓存参数
        self.max_cache_size = get_config('aidcis2.cache.max_size', 1000)
        self.default_ttl = get_config('aidcis2.cache.default_ttl', 300)  # 5分钟
        self.enable_spatial_cache = get_config('aidcis2.cache.enable_spatial', True)
        self.enable_async_refresh = get_config('aidcis2.cache.enable_async_refresh', True)
        
        # 多级缓存存储
        self._caches: Dict[str, Dict[str, CacheEntry]] = {
            CacheLevel.L1_MEMORY: {},
            CacheLevel.L2_SPATIAL: {},
            CacheLevel.L3_BUSINESS: {}
        }
        
        # 缓存统计
        self._stats: Dict[str, CacheStats] = {
            level: CacheStats() for level in self._caches.keys()
        }
        
        # 空间索引缓存（用于几何查询优化）
        self._spatial_index = {}
        
        # 异步刷新任务队列
        self._refresh_queue = asyncio.Queue() if self.enable_async_refresh else None
        
        # 弱引用回调，用于自动清理
        self._cleanup_callbacks = weakref.WeakValueDictionary()
    
    @error_handler(component="BusinessCacheManager", category=ErrorCategory.BUSINESS)
    def get(self, key: str, level: str = CacheLevel.L1_MEMORY) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            level: 缓存级别
            
        Returns:
            缓存值，如果不存在或过期返回None
        """
        start_time = time.time()
        
        try:
            with self._lock:
                cache = self._caches.get(level, {})
                entry = cache.get(key)
                
                if entry is None:
                    self._stats[level].misses += 1
                    return None
                
                if entry.is_expired():
                    # 过期则删除
                    del cache[key]
                    self._stats[level].misses += 1
                    self._stats[level].evictions += 1
                    return None
                
                # 命中缓存
                self._stats[level].hits += 1
                value = entry.access()
                
                # 更新平均响应时间
                response_time = time.time() - start_time
                self._update_response_time(level, response_time)
                
                return value
                
        except Exception as e:
            self.error_handler.handle_error(e, component="BusinessCacheManager")
            return None
    
    @error_handler(component="BusinessCacheManager", category=ErrorCategory.BUSINESS)
    def set(self, key: str, value: Any, level: str = CacheLevel.L1_MEMORY, 
            ttl: Optional[int] = None) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            level: 缓存级别
            ttl: 生存时间（秒）
            
        Returns:
            是否设置成功
        """
        try:
            with self._lock:
                cache = self._caches.get(level, {})
                
                # 检查缓存大小限制
                if len(cache) >= self.max_cache_size:
                    self._evict_lru(level)
                
                # 创建缓存条目
                entry = CacheEntry(
                    value=value,
                    created_at=datetime.now(),
                    ttl_seconds=ttl or self.default_ttl
                )
                
                cache[key] = entry
                self._stats[level].cache_size = len(cache)
                return True
                
        except Exception as e:
            self.error_handler.handle_error(e, component="BusinessCacheManager")
            return False
    
    def _evict_lru(self, level: str) -> None:
        """LRU驱逐策略"""
        cache = self._caches[level]
        if not cache:
            return
        
        # 找到最久未访问的条目
        lru_key = min(cache.keys(), key=lambda k: cache[k].last_access)
        del cache[lru_key]
        self._stats[level].evictions += 1
    
    def _update_response_time(self, level: str, response_time: float) -> None:
        """更新平均响应时间"""
        stats = self._stats[level]
        stats.total_operations += 1
        
        # 计算移动平均
        alpha = 0.1  # 平滑因子
        stats.average_response_time = (
            alpha * response_time + 
            (1 - alpha) * stats.average_response_time
        )
    
    def generate_cache_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        def make_hashable(obj):
            """将对象转换为可哈希的形式"""
            if isinstance(obj, dict):
                return tuple(sorted((k, make_hashable(v)) for k, v in obj.items()))
            elif isinstance(obj, list):
                return tuple(make_hashable(item) for item in obj)
            elif isinstance(obj, set):
                return tuple(sorted(make_hashable(item) for item in obj))
            elif hasattr(obj, '__dict__'):
                # 处理自定义对象
                return str(obj)
            else:
                return obj
        
        try:
            # 创建稳定的键
            hashable_args = make_hashable(args)
            hashable_kwargs = make_hashable(kwargs)
            
            key_data = {
                'args': hashable_args,
                'kwargs': hashable_kwargs
            }
            key_str = json.dumps(key_data, sort_keys=True, default=str)
            return hashlib.md5(key_str.encode()).hexdigest()
        except Exception as e:
            # 如果仍然无法处理，使用简单的字符串化方法
            fallback_key = f"{str(args)}_{str(kwargs)}"
            return hashlib.md5(fallback_key.encode()).hexdigest()
    
    def cache_spatial_query(self, bounds: Tuple[float, float, float, float], 
                           holes: List[HoleData]) -> str:
        """
        缓存空间查询结果
        
        Args:
            bounds: 查询边界 (min_x, min_y, max_x, max_y)
            holes: 查询结果
            
        Returns:
            缓存键
        """
        if not self.enable_spatial_cache:
            return ""
        
        key = self.generate_cache_key("spatial_query", bounds)
        
        # 创建轻量级的空间索引条目
        spatial_entry = {
            'bounds': bounds,
            'hole_ids': [hole.hole_id for hole in holes],
            'count': len(holes)
        }
        
        self.set(key, spatial_entry, CacheLevel.L2_SPATIAL)
        return key
    
    def get_spatial_query(self, bounds: Tuple[float, float, float, float]) -> Optional[List[str]]:
        """获取空间查询缓存"""
        if not self.enable_spatial_cache:
            return None
        
        key = self.generate_cache_key("spatial_query", bounds)
        entry = self.get(key, CacheLevel.L2_SPATIAL)
        
        if entry and isinstance(entry, dict):
            return entry.get('hole_ids', [])
        
        return None
    
    def cache_business_operation(self, operation_name: str, params: Dict[str, Any], 
                                result: Any, ttl: Optional[int] = None) -> str:
        """
        缓存业务操作结果
        
        Args:
            operation_name: 操作名称
            params: 操作参数
            result: 操作结果
            ttl: 生存时间
            
        Returns:
            缓存键
        """
        key = self.generate_cache_key("business_op", operation_name, params)
        
        # 业务操作缓存通常生存时间较短
        cache_ttl = ttl or get_config('aidcis2.cache.business_ttl', 60)  # 1分钟
        
        self.set(key, result, CacheLevel.L3_BUSINESS, cache_ttl)
        return key
    
    def get_business_operation(self, operation_name: str, params: Dict[str, Any]) -> Optional[Any]:
        """获取业务操作缓存"""
        key = self.generate_cache_key("business_op", operation_name, params)
        return self.get(key, CacheLevel.L3_BUSINESS)
    
    def invalidate_pattern(self, pattern: str, level: Optional[str] = None) -> int:
        """
        按模式失效缓存
        
        Args:
            pattern: 匹配模式
            level: 缓存级别，None表示所有级别
            
        Returns:
            失效的条目数量
        """
        invalidated_count = 0
        
        with self._lock:
            levels_to_check = [level] if level else self._caches.keys()
            
            for cache_level in levels_to_check:
                cache = self._caches[cache_level]
                keys_to_remove = [
                    key for key in cache.keys() 
                    if pattern in key
                ]
                
                for key in keys_to_remove:
                    del cache[key]
                    invalidated_count += 1
                
                self._stats[cache_level].cache_size = len(cache)
        
        return invalidated_count
    
    def clear_cache(self, level: Optional[str] = None) -> None:
        """清空缓存"""
        with self._lock:
            if level:
                self._caches[level].clear()
                self._stats[level].cache_size = 0
            else:
                for cache_level in self._caches:
                    self._caches[cache_level].clear()
                    self._stats[cache_level].cache_size = 0
    
    def get_cache_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取缓存统计信息"""
        with self._lock:
            return {
                level: {
                    'hits': stats.hits,
                    'misses': stats.misses,
                    'hit_rate': stats.hit_rate,
                    'evictions': stats.evictions,
                    'cache_size': stats.cache_size,
                    'average_response_time_ms': stats.average_response_time * 1000,
                    'total_operations': stats.total_operations
                }
                for level, stats in self._stats.items()
            }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        stats = self.get_cache_stats()
        
        # 计算整体指标
        total_hits = sum(s['hits'] for s in stats.values())
        total_operations = sum(s['total_operations'] for s in stats.values())
        avg_response_time = sum(s['average_response_time_ms'] for s in stats.values()) / len(stats)
        
        return {
            'cache_stats': stats,
            'overall_metrics': {
                'total_cache_hits': total_hits,
                'total_operations': total_operations,
                'overall_hit_rate': total_hits / total_operations if total_operations > 0 else 0,
                'average_response_time_ms': avg_response_time,
                'response_time_target_met': avg_response_time < 100,  # <100ms目标
                'cache_efficiency': self._calculate_cache_efficiency()
            },
            'configuration': {
                'max_cache_size': self.max_cache_size,
                'default_ttl': self.default_ttl,
                'spatial_cache_enabled': self.enable_spatial_cache,
                'async_refresh_enabled': self.enable_async_refresh
            }
        }
    
    def _calculate_cache_efficiency(self) -> float:
        """计算缓存效率"""
        total_hits = sum(stats.hits for stats in self._stats.values())
        total_misses = sum(stats.misses for stats in self._stats.values())
        total_evictions = sum(stats.evictions for stats in self._stats.values())
        
        if total_hits + total_misses == 0:
            return 0.0
        
        # 效率 = (命中数 - 驱逐数) / 总操作数
        efficiency = (total_hits - total_evictions) / (total_hits + total_misses)
        return max(0.0, efficiency)
    
    async def async_refresh_cache(self, key: str, refresh_func: Callable, 
                                 level: str = CacheLevel.L1_MEMORY, 
                                 ttl: Optional[int] = None) -> None:
        """异步刷新缓存"""
        if not self.enable_async_refresh:
            return
        
        try:
            # 在后台刷新缓存
            new_value = await asyncio.get_event_loop().run_in_executor(
                None, refresh_func
            )
            
            if new_value is not None:
                self.set(key, new_value, level, ttl)
                
        except Exception as e:
            self.error_handler.handle_error(e, component="BusinessCacheManager")


def cached_business_operation(cache_manager: BusinessCacheManager = None, 
                            operation_name: str = None, 
                            ttl: Optional[int] = None):
    """业务操作缓存装饰器"""
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal cache_manager, operation_name
            
            if cache_manager is None:
                try:
                    cache_manager = get_container().resolve(BusinessCacheManager)
                except:
                    # 如果无法获取，直接执行原函数
                    return func(*args, **kwargs)
            
            if operation_name is None:
                operation_name = f"{func.__module__}.{func.__name__}"
            
            # 生成缓存参数 - 使用字符串化以避免unhashable类型
            cache_params = {
                'args': str(args),
                'kwargs': str(sorted(kwargs.items()) if kwargs else [])
            }
            
            # 尝试从缓存获取
            start_time = time.time()
            cached_result = cache_manager.get_business_operation(operation_name, cache_params)
            
            if cached_result is not None:
                return cached_result
            
            # 执行原函数
            result = func(*args, **kwargs)
            
            # 计算执行时间
            execution_time = time.time() - start_time
            
            # 缓存结果（只缓存成功的结果）
            if result is not None:
                cache_manager.cache_business_operation(operation_name, cache_params, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def spatial_cached(cache_manager: BusinessCacheManager = None):
    """空间查询缓存装饰器"""
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal cache_manager
            
            if cache_manager is None:
                try:
                    cache_manager = get_container().resolve(BusinessCacheManager)
                except:
                    # 如果无法获取，直接执行原函数
                    return func(*args, **kwargs)
            
            # 提取边界参数（假设是前4个参数）
            if len(args) >= 4:
                bounds = args[:4]
                cached_ids = cache_manager.get_spatial_query(bounds)
                
                if cached_ids is not None:
                    # 这里需要根据ID恢复完整对象，简化实现直接调用原函数
                    pass
            
            # 执行原函数
            result = func(*args, **kwargs)
            
            # 缓存空间查询结果
            if hasattr(result, '__iter__') and len(args) >= 4:
                bounds = args[:4]
                cache_manager.cache_spatial_query(bounds, list(result))
            
            return result
        
        return wrapper
    return decorator