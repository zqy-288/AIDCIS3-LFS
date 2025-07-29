"""
主检测页面组件模块
提供高内聚、低耦合的独立组件
"""

from .left_info_panel import LeftInfoPanel
from .center_visualization_panel import CenterVisualizationPanel
from .right_operations_panel import RightOperationsPanel
from .panorama_sector_coordinator import PanoramaSectorCoordinator
from .simulation_controller import SimulationController

# 保留旧的组件以兼容
__all__ = [
    'LeftInfoPanel',
    'CenterVisualizationPanel',
    'RightOperationsPanel',
    'PanoramaSectorCoordinator',
    'SimulationController',
    'EnhancedWorkpieceDiagram', 
    'DetectionStatus', 
    'ControlPanel'
]

def __getattr__(name):
    """延迟导入旧组件以避免循环依赖"""
    if name == 'EnhancedWorkpieceDiagram':
        from .enhanced_workpiece_diagram import EnhancedWorkpieceDiagram
        return EnhancedWorkpieceDiagram
    elif name == 'DetectionStatus':
        from .enhanced_workpiece_diagram import DetectionStatus
        return DetectionStatus
    elif name == 'ControlPanel':
        from .control_panel import ControlPanel
        return ControlPanel
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")