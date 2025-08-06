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

# 整合的组件已移除，改为直接集成到主页面中
# from .endoscope import EndoscopeView, EndoscopeManager
# from .chart import EnhancedChartWidget, RealtimeDataManager, SmartAnomalyDetector, CSVDataProcessor

__all__ = [
    'StatusPanel',
    'ChartPanel',
    'AnomalyPanel',
    'EndoscopePanel',
    # 整合的组件已移至主页面实现
    # 'EndoscopeView',
    # 'EndoscopeManager',
    # 'EnhancedChartWidget',
    # 'RealtimeDataManager',
    # 'SmartAnomalyDetector',
    # 'CSVDataProcessor'
]