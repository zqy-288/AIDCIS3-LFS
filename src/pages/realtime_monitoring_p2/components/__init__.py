"""
实时监控页面组件包
包含所有P2页面的UI组件
"""

# 导出主要组件
from .status_panel import StatusPanel
from .chart_panel import ChartPanel
from .anomaly_panel import AnomalyPanel
from .endoscope_panel import EndoscopePanel

__all__ = [
    'StatusPanel',
    'ChartPanel',
    'AnomalyPanel',
    'EndoscopePanel'
]