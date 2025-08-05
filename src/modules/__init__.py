"""
功能模块包
包含所有GUI功能组件
"""

# 导出主要组件
from .unified_history_viewer import UnifiedHistoryViewer as HistoryViewer
# from .main_detection_view import MainDetectionView  # 已移至trash
from .endoscope_view import EndoscopeView
# from .annotation_tool import AnnotationTool  # 已迁移到 shared/components/annotation/
# from .workpiece_diagram import WorkpieceDiagram  # 已移至trash
# from .matplotlib_chart import MatplotlibChart  # 已删除(P2有更优版本)
# from .realtime_chart import RealtimeChart  # 已删除，使用P2增强版本
# from .worker_thread import WorkerThread  # 已迁移到 shared/services/threading/
from .models import db_manager

__all__ = [
    'HistoryViewer',
    # 'MainDetectionView',  # 已移至trash
    'EndoscopeView',
    # 'AnnotationTool',  # 已迁移到 shared/components/annotation/
    # 'WorkpieceDiagram',  # 已移至trash
    # 'MatplotlibChart',  # 已删除(P2有更优版本)
    # 'RealtimeChart',  # 已删除，使用P2增强版本
    # 'WorkerThread',  # 已迁移到 shared/services/threading/
    'db_manager'
]
