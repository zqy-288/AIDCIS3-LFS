"""
数据服务层
封装数据访问和持久化逻辑
"""

from typing import Optional, Dict, Any, List


class DataService:
    """
    数据服务
    提供统一的数据访问接口
    """
    
    def __init__(self):
        # 数据缓存
        self._cache = {}
        
    def get_data(self, key: str) -> Optional[Any]:
        """获取数据"""
        return self._cache.get(key)
        
    def set_data(self, key: str, value: Any) -> bool:
        """设置数据"""
        try:
            self._cache[key] = value
            return True
        except Exception as e:
            print(f"Error setting data: {e}")
            return False
            
    def delete_data(self, key: str) -> bool:
        """删除数据"""
        try:
            if key in self._cache:
                del self._cache[key]
            return True
        except Exception as e:
            print(f"Error deleting data: {e}")
            return False
            
    def clear_cache(self) -> bool:
        """清空缓存"""
        try:
            self._cache.clear()
            return True
        except Exception as e:
            print(f"Error clearing cache: {e}")
            return False


# 全局数据服务实例
_global_data_service = None


def get_data_service() -> DataService:
    """获取全局数据服务实例"""
    global _global_data_service
    if _global_data_service is None:
        _global_data_service = DataService()
    return _global_data_service