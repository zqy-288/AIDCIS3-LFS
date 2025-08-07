"""
历史数据页面组件模块
"""

from .history.history_viewer import HistoryViewer
from src.pages.defect_annotation_p32.defect_annotation_tool import DefectAnnotationTool

__all__ = [
    'HistoryViewer',
    'DefectAnnotationTool'
]