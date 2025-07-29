"""
实时监控页面组件模块
包含所有UI组件的实现
"""

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
