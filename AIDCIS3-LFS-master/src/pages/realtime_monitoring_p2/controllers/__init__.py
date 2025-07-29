"""
实时监控页面控制器模块
包含所有业务逻辑控制器
"""

from .monitoring_controller import MonitoringController
from .automation_controller import AutomationController
from .data_controller import DataController

__all__ = [
    'MonitoringController',
    'AutomationController',
    'DataController'
]
