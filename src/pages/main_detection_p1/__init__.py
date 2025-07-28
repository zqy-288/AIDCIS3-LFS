"""
P1级别主检测视图页面包
集成AIDCIS2的完整检测功能
"""

from .main_detection_page import MainDetectionPage
from .components import (
    ToolbarComponent,
    InfoPanelComponent, 
    VisualizationPanelComponent,
    OperationsPanelComponent
)

__all__ = [
    'MainDetectionPage',
    'ToolbarComponent',
    'InfoPanelComponent',
    'VisualizationPanelComponent', 
    'OperationsPanelComponent'
]