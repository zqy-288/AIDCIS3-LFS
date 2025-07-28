"""
实时监控页面
基于第二季realtime_chart_s2的包装
"""

import logging
from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Signal

try:
    from src.modules.realtime_chart_p2 import RealtimeChart
except ImportError as e:
    logging.error(f"无法导入第二季实时图表: {e}")
    RealtimeChart = None


class RealtimeMonitoringPage(QWidget):
    """实时监控页面"""
    
    def __init__(self, shared_components=None, view_model=None, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        
        if RealtimeChart:
            # 使用第二季模块化架构
            self.realtime_chart = RealtimeChart()
            layout.addWidget(self.realtime_chart)
        else:
            # 回退显示
            layout.addWidget(QLabel("实时监控页面 - 第二季模块加载失败"))