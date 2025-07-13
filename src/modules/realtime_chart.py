"""
实时图表组件兼容层
提供向后兼容的导入路径
"""

# 从新的模块化结构导入
from .realtime_chart.realtime_chart import RealtimeChart

# 保持向后兼容
__all__ = ['RealtimeChart']