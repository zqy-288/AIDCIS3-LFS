"""
实时监控页面控制器包
包含所有P2页面的业务逻辑控制器
"""

# 导出主要控制器
from .monitoring_controller import MonitoringController
from .data_controller import DataController
from .automation_controller import AutomationController

__all__ = [
    'MonitoringController',
    'DataController', 
    'AutomationController'
]