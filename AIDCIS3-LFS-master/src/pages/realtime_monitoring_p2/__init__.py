"""
实时监控页面P2模块
高保真度还原原项目RealtimeChart功能，使用模块化架构
"""

from .realtime_monitoring_page import RealtimeMonitoringPage, RealtimeChart
from .components import StatusPanel, ChartPanel, AnomalyPanel, EndoscopePanel
from .controllers import MonitoringController, AutomationController, DataController

__all__ = [
    'RealtimeMonitoringPage',
    'RealtimeChart',  # 兼容性别名
    'StatusPanel',
    'ChartPanel',
    'AnomalyPanel',
    'EndoscopePanel',
    'MonitoringController',
    'AutomationController',
    'DataController'
]