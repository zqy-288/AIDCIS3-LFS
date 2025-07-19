"""
控制器模块
提供UI管理和业务逻辑控制功能
"""

from .sidebar_controller import SidebarController
from .detection_controller import DetectionController
from .main_detection_coordinator import MainDetectionCoordinator

__all__ = [
    "SidebarController", 
    "DetectionController", 
    "MainDetectionCoordinator"
]