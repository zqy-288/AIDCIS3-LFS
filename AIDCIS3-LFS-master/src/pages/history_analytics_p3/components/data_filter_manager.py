"""
数据筛选管理器
"""

from typing import Dict, Any, List
from PySide6.QtCore import QObject, Signal


class DataFilterManager(QObject):
    """数据筛选管理器"""
    
    filters_changed = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self.active_filters = {}
        
    def set_filter(self, key: str, value: Any):
        """设置筛选条件"""
        self.active_filters[key] = value
        self.filters_changed.emit(self.active_filters)
        
    def get_filters(self) -> Dict[str, Any]:
        """获取当前筛选条件"""
        return self.active_filters.copy()
        
    def clear_filters(self):
        """清除所有筛选条件"""
        self.active_filters.clear()
        self.filters_changed.emit(self.active_filters)