"""
功能模块包
包含所有GUI功能组件
"""

# 导出主要组件
from .history_viewer import HistoryViewer
from .main_detection_view import MainDetectionView
from .endoscope_view import EndoscopeView
from .annotation_tool import AnnotationTool
# from .workpiece_diagram import WorkpieceDiagram  # 已移至trash
from .matplotlib_chart import MatplotlibChart
from .realtime_chart import RealtimeChart
from .worker_thread import WorkerThread
from .models import db_manager

__all__ = [
    'HistoryViewer',
    'MainDetectionView', 
    'EndoscopeView',
    'AnnotationTool',
    # 'WorkpieceDiagram',  # 已移至trash
    'MatplotlibChart',
    'RealtimeChart',
    'WorkerThread',
    'db_manager'
]
