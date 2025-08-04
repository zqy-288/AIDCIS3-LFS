"""
报告状态小部件
提供报告生成状态的实时显示
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QProgressBar, QPushButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class ReportStatusWidget(QWidget):
    """报告状态小部件"""
    
    # 信号
    cancel_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.reset_status()
    
    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        
        status_group = QGroupBox("生成状态")
        status_layout = QVBoxLayout(status_group)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.status_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self.cancel_requested.emit)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addStretch()
        
        status_layout.addLayout(button_layout)
        layout.addWidget(status_group)
    
    def set_status(self, status_text: str):
        """设置状态文本"""
        self.status_label.setText(status_text)
    
    def set_progress(self, value: int):
        """设置进度值 (0-100)"""
        self.progress_bar.setValue(value)
        if value > 0:
            self.progress_bar.setVisible(True)
        else:
            self.progress_bar.setVisible(False)
    
    def start_generation(self):
        """开始生成状态"""
        self.status_label.setText("正在生成报告...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.cancel_btn.setVisible(True)
    
    def complete_generation(self, success: bool, message: str = ""):
        """完成生成状态"""
        if success:
            self.status_label.setText(f"✅ 生成成功: {message}")
            self.progress_bar.setValue(100)
        else:
            self.status_label.setText(f"❌ 生成失败: {message}")
            self.progress_bar.setValue(0)
        
        self.cancel_btn.setVisible(False)
    
    def reset_status(self):
        """重置状态"""
        self.status_label.setText("就绪")
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        self.cancel_btn.setVisible(False)
    
    def set_error_status(self, error_message: str):
        """设置错误状态"""
        self.status_label.setText(f"❌ 错误: {error_message}")
        self.progress_bar.setVisible(False)
        self.cancel_btn.setVisible(False)