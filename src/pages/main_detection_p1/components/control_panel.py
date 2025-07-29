"""
控制面板组件 - 从old版本直接复制
提供检测操作的控制按钮
"""

from PySide6.QtWidgets import QGroupBox, QPushButton, QGridLayout
from PySide6.QtCore import Signal


class ControlPanel(QGroupBox):
    """控制面板组件"""
    start_detection = Signal()
    pause_detection = Signal()
    stop_detection = Signal()
    reset_detection = Signal()
    
    def __init__(self, title="检测操作", parent=None):
        super().__init__(title, parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QGridLayout(self)
        self.start_button = QPushButton("开始检测")
        self.pause_button = QPushButton("暂停检测")
        self.stop_button = QPushButton("停止检测")
        self.reset_button = QPushButton("重置")
        
        self.start_button.setStyleSheet("background-color: green; color: white;")
        self.pause_button.setStyleSheet("background-color: orange; color: white;")
        self.stop_button.setStyleSheet("background-color: red; color: white;")
        
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        
        layout.addWidget(self.start_button, 0, 0)
        layout.addWidget(self.pause_button, 0, 1)
        layout.addWidget(self.stop_button, 1, 0)
        layout.addWidget(self.reset_button, 1, 1)
        
        self.start_button.clicked.connect(self.start_detection.emit)
        self.pause_button.clicked.connect(self.pause_detection.emit)
        self.stop_button.clicked.connect(self.stop_detection.emit)
        self.reset_button.clicked.connect(self.reset_detection.emit)