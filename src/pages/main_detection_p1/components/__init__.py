"""
主检测页面组件模块
提供高内聚、低耦合的独立组件
"""

from .left_info_panel import LeftInfoPanel
from .center_visualization_panel import CenterVisualizationPanel
from .right_operations_panel import RightOperationsPanel
from .panorama_sector_coordinator import PanoramaSectorCoordinator
from .simulation_controller import SimulationController

__all__ = [
    'LeftInfoPanel',
    'CenterVisualizationPanel',
    'RightOperationsPanel',
    'PanoramaSectorCoordinator',
    'SimulationController'
]