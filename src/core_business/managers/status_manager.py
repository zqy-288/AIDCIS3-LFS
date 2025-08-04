"""
状态管理器
管理孔位状态的更新和同步
"""

from typing import Dict, Any, Optional, Callable
from enum import Enum
import logging


class StatusManager:
    """状态管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.status_callbacks = []
        self.hole_collection = None
    
    def set_hole_collection(self, hole_collection):
        """设置孔位集合"""
        self.hole_collection = hole_collection
    
    def update_status(self, hole_id: str, new_status, **kwargs) -> bool:
        """更新孔位状态"""
        try:
            if self.hole_collection and hasattr(self.hole_collection, 'update_hole_status'):
                result = self.hole_collection.update_hole_status(hole_id, new_status)
                
                # 触发回调
                for callback in self.status_callbacks:
                    try:
                        callback(hole_id, new_status)
                    except Exception as e:
                        self.logger.error(f"状态回调失败: {e}")
                
                return result
            else:
                self.logger.warning("孔位集合未设置或缺少更新方法")
                return False
                
        except Exception as e:
            self.logger.error(f"更新状态失败: {e}")
            return False
    
    def add_status_callback(self, callback: Callable):
        """添加状态变更回调"""
        if callback not in self.status_callbacks:
            self.status_callbacks.append(callback)
    
    def remove_status_callback(self, callback: Callable):
        """移除状态变更回调"""
        if callback in self.status_callbacks:
            self.status_callbacks.remove(callback)
    
    def get_hole_status(self, hole_id: str):
        """获取孔位状态"""
        try:
            if self.hole_collection and hasattr(self.hole_collection, 'get_hole_by_id'):
                hole = self.hole_collection.get_hole_by_id(hole_id)
                return hole.status if hole else None
            return None
        except Exception as e:
            self.logger.error(f"获取孔位状态失败: {e}")
            return None
    
    def batch_update_status(self, updates: Dict[str, Any]) -> int:
        """批量更新状态"""
        success_count = 0
        for hole_id, status in updates.items():
            if self.update_status(hole_id, status):
                success_count += 1
        return success_count
