"""
P3级界面 - 历史数据分析页面 (模块化架构)
数据分析和历史回顾功能
"""

# 新的模块化主界面
from .history_main_view import HistoryMainView

# 保持向后兼容性
from .history_analytics_page import HistoryAnalyticsPage

__all__ = ['HistoryMainView', 'HistoryAnalyticsPage']