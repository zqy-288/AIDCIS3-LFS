"""
历史统计页面数据模型
"""

from PySide6.QtCore import QObject, Signal
from typing import List, Dict, Any


class HistoryDataModel(QObject):
    """历史数据模型"""
    data_loaded = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self.data = []
        
    def load_data_range(self, start_date, end_date):
        """加载指定时间范围的数据"""
        # 模拟数据加载
        self.data = [{'timestamp': '2024-01-01', 'depth': 10.0, 'diameter': 17.6, 'status': 'qualified'}]
        self.data_loaded.emit({'count': len(self.data)})
        
    def get_filtered_data(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取筛选后的数据"""
        return self.data
        
    def get_data_count(self) -> int:
        """获取数据数量"""
        return len(self.data)


class StatisticsDataModel(QObject):
    """统计数据模型"""
    def __init__(self):
        super().__init__()


class TrendDataModel(QObject):
    """趋势数据模型"""
    def __init__(self):
        super().__init__()


__all__ = [
    'HistoryDataModel',
    'StatisticsDataModel',
    'TrendDataModel'
]