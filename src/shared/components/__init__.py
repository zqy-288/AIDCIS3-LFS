"""
共享UI组件统一模块
提供跨页面的通用UI组件和工厂
"""

from .base_components import InfoPanelComponent, ToolbarComponent
from .factories import get_ui_factory, ChartFactory, DialogFactory, ViewFactory
from .theme import theme_manager
from .annotation import annotation_tool

__all__ = [
    'InfoPanelComponent',
    'ToolbarComponent',
    'get_ui_factory',
    'ChartFactory',
    'DialogFactory', 
    'ViewFactory',
    'theme_manager',
    'annotation_tool'
]