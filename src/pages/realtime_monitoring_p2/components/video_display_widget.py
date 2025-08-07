#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频显示组件 - 用于在左侧面板显示预览视频
"""

from PySide6.QtWidgets import QLabel, QWidget, QVBoxLayout
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage
import numpy as np
import cv2


class VideoDisplayWidget(QWidget):
    """视频显示组件"""
    
    clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 视频显示标签
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("""
            QLabel {
                background-color: #000;
                border: 2px solid #4A90E2;
                border-radius: 4px;
            }
        """)
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setText("等待视频流...")
        self.video_label.setStyleSheet("""
            QLabel {
                background-color: #000;
                border: 2px solid #4A90E2;
                border-radius: 4px;
                color: #4A90E2;
                font-size: 18px;
            }
        """)
        
        layout.addWidget(self.video_label)
        
    def update_frame(self, frame):
        """更新显示帧"""
        try:
            if isinstance(frame, np.ndarray):
                height, width, channel = frame.shape
                bytes_per_line = 3 * width
                
                # BGR转RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # 创建QImage
                q_image = QImage(rgb_frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
                
                # 转换为QPixmap并缩放显示
                pixmap = QPixmap.fromImage(q_image)
                scaled_pixmap = pixmap.scaled(
                    self.video_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                
                self.video_label.setPixmap(scaled_pixmap)
        except Exception as e:
            print(f"[ERROR] 更新视频帧失败: {e}")
            
    def clear_display(self):
        """清除显示"""
        self.video_label.clear()
        self.video_label.setText("视频已停止")
        
    def set_message(self, message):
        """设置文本消息"""
        self.video_label.clear()
        self.video_label.setText(message)