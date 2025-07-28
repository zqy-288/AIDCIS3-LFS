"""
UI组件工厂模块
提供统一的UI组件创建接口，减少MainWindow的直接依赖
"""

from .ui_component_factory import UIComponentFactory, get_ui_factory
from .chart_factory import ChartFactory, get_chart_factory
from .dialog_factory import DialogFactory, get_dialog_factory
from .view_factory import ViewFactory, get_view_factory

__all__ = [
    'UIComponentFactory',
    'ChartFactory', 
    'DialogFactory',
    'ViewFactory',
    'get_ui_factory',
    'get_chart_factory',
    'get_dialog_factory', 
    'get_view_factory'
]