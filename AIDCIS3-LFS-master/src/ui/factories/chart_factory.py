"""
图表工厂
管理图表组件的创建
"""

from typing import Optional, Any
from PySide6.QtWidgets import QWidget


class ChartFactory:
    """
    图表工厂类
    创建各种图表组件
    """
    
    def __init__(self):
        self._chart_cache = {}
        
    def create_realtime_chart(self, parent: Optional[QWidget] = None) -> Any:
        """创建实时图表"""
        try:
            from src.modules.realtime_chart import RealtimeChart
            return RealtimeChart(parent)
        except ImportError:
            # 如果模块不存在，返回占位组件
            from PySide6.QtWidgets import QLabel
            label = QLabel("实时图表占位", parent)
            label.setStyleSheet("border: 1px solid gray; padding: 20px;")
            return label
            
    def create_history_chart(self, parent: Optional[QWidget] = None) -> Any:
        """创建历史图表"""
        try:
            # 假设有历史图表组件
            from src.modules.history_chart import HistoryChart
            return HistoryChart(parent)
        except ImportError:
            from PySide6.QtWidgets import QLabel
            label = QLabel("历史图表占位", parent)
            label.setStyleSheet("border: 1px solid gray; padding: 20px;")
            return label
            
    def create_statistics_chart(self, parent: Optional[QWidget] = None) -> Any:
        """创建统计图表"""
        try:
            from src.modules.statistics_chart import StatisticsChart
            return StatisticsChart(parent)
        except ImportError:
            from PySide6.QtWidgets import QLabel
            label = QLabel("统计图表占位", parent)
            label.setStyleSheet("border: 1px solid gray; padding: 20px;")
            return label


# 全局图表工厂实例
_global_chart_factory = None


def get_chart_factory() -> ChartFactory:
    """获取全局图表工厂实例"""
    global _global_chart_factory
    if _global_chart_factory is None:
        _global_chart_factory = ChartFactory()
    return _global_chart_factory