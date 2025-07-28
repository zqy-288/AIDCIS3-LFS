"""
实时图表模块
重定向到包含内窥镜功能的版本
"""

# 导入包含内窥镜功能的原始版本
try:
    from src.modules.realtime_chart import RealtimeChart as OriginalRealtimeChart
    
    # 使用原始版本
    RealtimeChart = OriginalRealtimeChart
    RealTimeChart = RealtimeChart  # 向后兼容
    
    print("✅ 成功导入包含内窥镜功能的RealtimeChart")
    
except ImportError as e:
    print(f"⚠️ 导入原始RealtimeChart失败: {e}")
    # 回退到包版本
    from .realtime_chart import RealtimeChart
    RealTimeChart = RealtimeChart

__all__ = [
    'RealtimeChart',
    'RealTimeChart',  # 向后兼容
]