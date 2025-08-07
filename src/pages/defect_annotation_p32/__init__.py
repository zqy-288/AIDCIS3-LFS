"""
P3.2缺陷标注页面模块
完全基于重构前代码恢复，实现图片浏览和缺陷标注功能
"""

from .defect_annotation_with_browser import DefectAnnotationWithBrowser
from .image_browser import ImageBrowser
from .defect_annotation_tool import DefectAnnotationTool

__all__ = [
    'DefectAnnotationWithBrowser',
    'ImageBrowser', 
    'DefectAnnotationTool'
]