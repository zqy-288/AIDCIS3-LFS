"""
页面包模块
包含四个主要页面的实现
"""

from .main_detection import MainDetectionPage
from .realtime_monitoring import RealtimeMonitoringPage
from .history_analytics_p3 import HistoryAnalyticsPage
from .report_generation_p4 import ReportGenerationPage

__all__ = [
    'MainDetectionPage',
    'RealtimeMonitoringPage',
    'HistoryAnalyticsPage', 
    'ReportGenerationPage'
]