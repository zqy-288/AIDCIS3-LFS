"""
主窗口包 P1版本
四页面聚合架构：主检测视图、实时监控、历史统计、报告生成
"""

# 从各个页面包导入主要组件
from .pages.main_detection import MainDetectionPage
from .pages.realtime_monitoring import RealtimeMonitoringPage  
from .pages.history_analytics_p3 import HistoryAnalyticsPage
from .pages.report_generation_p4 import ReportGenerationPage

# 从共享模块导入
from .shared import SharedComponents, ViewModelManager

# 主窗口聚合器
from .main_window_aggregator import MainWindowAggregator

# 版本信息
__version__ = '1.0.0'
__author__ = 'AIDCIS3 Team'

# 导出列表
__all__ = [
    # 主要类
    'MainWindowAggregator',
    
    # 页面类
    'MainDetectionPage',
    'RealtimeMonitoringPage', 
    'HistoryAnalyticsPage',
    'ReportGenerationPage',
    
    # 共享组件
    'SharedComponents',
    'ViewModelManager'
]