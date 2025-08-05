"""
实时监控页面组件包
包含所有P2页面的UI组件
整合了内窥镜和实时图表功能
"""

# 导出主要组件
from .status_panel import StatusPanel
from .chart_panel import ChartPanel
from .anomaly_panel import AnomalyPanel
from .endoscope_panel import EndoscopePanel

# 导出整合的组件
from .endoscope import EndoscopeView, EndoscopeManager
from .chart import EnhancedChartWidget, RealtimeDataManager, SmartAnomalyDetector, CSVDataProcessor

__all__ = [
    'StatusPanel',
    'ChartPanel',
    'AnomalyPanel',
    'EndoscopePanel',
    # 整合的内窥镜组件
    'EndoscopeView',
    'EndoscopeManager',
    # 整合的图表组件
    'EnhancedChartWidget',
    'RealtimeDataManager',
    'SmartAnomalyDetector',
    'CSVDataProcessor'
]