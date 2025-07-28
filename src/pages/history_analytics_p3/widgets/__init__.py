"""
历史统计页面UI组件
"""

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Signal


class TrendChartWidget(QWidget):
    """趋势图表组件"""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("趋势图表"))
        
    def update_data(self, data):
        pass


class QualityDashboardWidget(QWidget):
    """质量仪表板组件"""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("质量仪表板"))
        
    def update_data(self, data):
        pass


class StatisticsTableWidget(QWidget):
    """统计表格组件"""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("统计表格"))
        
    def update_data(self, data):
        pass


class FilterPanelWidget(QWidget):
    """筛选面板组件"""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("筛选面板"))


class TimeRangeWidget(QWidget):
    """时间范围组件"""
    range_changed = Signal(object, object)
    
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("时间范围选择"))


__all__ = [
    'TrendChartWidget',
    'QualityDashboardWidget', 
    'StatisticsTableWidget',
    'FilterPanelWidget',
    'TimeRangeWidget'
]