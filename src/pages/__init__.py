"""
平级P页面包模块
P1-主检测视图、P2-实时监控、P3-历史统计、P4-报告生成
"""

from .main_detection_p1 import MainDetectionPage
from .realtime_monitoring_p2 import RealtimeMonitoringPage
from .history_analytics_p3 import HistoryAnalyticsPage
from .report_generation_p4 import ReportGenerationPage

__all__ = [
    'MainDetectionPage',
    'RealtimeMonitoringPage',
    'HistoryAnalyticsPage', 
    'ReportGenerationPage'
]