"""
实时图表包
重构后的模块化实时图表组件
"""

# 从主模块导入
from .realtime_chart import RealtimeChart

# 从组件模块导入
from .components import (
    ChartWidget,
    DataManager,
    CSVProcessor,
    AnomalyDetector,
    EndoscopeManager,
    ProcessController
)

# 从工具模块导入
from .utils import constants
from .utils.font_config import setup_safe_chinese_font

# 为了向后兼容，保留旧名称
RealTimeChart = RealtimeChart

# 版本信息
__version__ = '2.0.0'
__author__ = 'AIDCIS3 Team'

# 导出列表
__all__ = [
    # 主类
    'RealtimeChart',
    'RealTimeChart',  # 向后兼容
    
    # 组件类
    'ChartWidget',
    'DataManager',
    'CSVProcessor',
    'AnomalyDetector',
    'EndoscopeManager',
    'ProcessController',
    
    # 工具函数
    'setup_safe_chinese_font',
    
    # 常量模块
    'constants'
]