"""
共享UI组件
包含可以在多个页面间复用的通用UI组件
"""

from .info_panel_component import InfoPanelComponent
from .operations_panel_component import OperationsPanelComponent

__all__ = [
    'InfoPanelComponent',
    'OperationsPanelComponent'
]