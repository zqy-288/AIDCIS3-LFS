"""
缓存服务模块
提供业务逻辑缓存管理功能
"""

from .business_cache_manager import BusinessCacheManager, cached_business_operation

__all__ = ['BusinessCacheManager', 'cached_business_operation']