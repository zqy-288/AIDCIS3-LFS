"""状态栏组件"""
from PySide6.QtWidgets import QStatusBar, QLabel
from PySide6.QtCore import QTimer
from datetime import datetime


class StatusBarWidget(QStatusBar):
    """
    自定义状态栏
    显示状态消息、检测时间和系统时间
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        # 状态消息标签
        self.status_label = QLabel("就绪")
        self.addWidget(self.status_label, 1)
        
        # 检测时间标签
        self.detection_time_label = QLabel("检测时间: 00:00:00")
        self.addPermanentWidget(self.detection_time_label)
        
        # 估计剩余时间标签
        self.estimated_time_label = QLabel("估计剩余: --:--:--")
        self.addPermanentWidget(self.estimated_time_label)
        
        # 系统时间标签
        self.time_label = QLabel()
        self.addPermanentWidget(self.time_label)
        
        # 启动时间更新定时器
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)  # 每秒更新
        
        # 初始更新
        self.update_time()
        
    def update_time(self):
        """更新系统时间显示"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(current_time)
        
    def set_status_message(self, message: str):
        """设置状态消息"""
        self.status_label.setText(message)
        
    def update_detection_time(self, elapsed_time: str):
        """更新检测时间"""
        self.detection_time_label.setText(f"检测时间: {elapsed_time}")
        
    def update_estimated_time(self, estimated_time: str):
        """更新估计剩余时间"""
        self.estimated_time_label.setText(f"估计剩余: {estimated_time}")