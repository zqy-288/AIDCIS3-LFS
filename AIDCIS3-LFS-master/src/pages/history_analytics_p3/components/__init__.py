"""
历史统计页面核心组件模块 - 重构前界面还原
"""

# 重构前界面组件
from .sidebar_panel import SidebarPanel
from .data_table_panel import DataTablePanel
from .visualization_panel import VisualizationPanel
from .scrollable_text_label import ScrollableTextLabel
from .defect_annotation_tool import DefectAnnotationTool
from .manual_review_dialog import ManualReviewDialog

# 原有组件（保留兼容性）
from .statistics_engine import StatisticsEngine
from .data_filter_manager import DataFilterManager
from .trend_analyzer import TrendAnalyzer
from .quality_metrics_calculator import QualityMetricsCalculator
from .export_manager import ExportManager

__all__ = [
    # 重构前界面组件
    'SidebarPanel',
    'DataTablePanel',
    'VisualizationPanel',
    'ScrollableTextLabel',
    'DefectAnnotationTool',
    'ManualReviewDialog',

    # 原有组件
    'StatisticsEngine',
    'DataFilterManager',
    'TrendAnalyzer',
    'QualityMetricsCalculator',
    'ExportManager'
]