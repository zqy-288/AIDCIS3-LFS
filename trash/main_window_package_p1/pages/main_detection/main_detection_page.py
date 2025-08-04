"""
主检测视图页面
"""

from typing import Optional
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Signal


class MainDetectionPage(QWidget):
    """主检测视图页面"""
    
    def __init__(self, shared_components=None, view_model=None, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("主检测视图页面 - P1架构"))
        
    def load_dxf(self):
        """加载DXF文件"""
        pass