"""
可滚动文本标签组件
基于重构前的ScrollableTextLabel实现
"""

from PySide6.QtWidgets import QLabel
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFontMetrics


class ScrollableTextLabel(QLabel):
    """可滚动的文本标签 - 基于像素的丝滑滑动"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.full_text = ""
        self.placeholder_text = ""
        self.scroll_timer = QTimer()
        self.scroll_timer.timeout.connect(self.scroll_text)
        self.scroll_position = 0
        self.scroll_direction = 1  # 1为向左，-1为向右
        self.scroll_speed = 1  # 每次滚动的像素数
        self.pause_duration = 2000  # 到达边界时的暂停时间（毫秒）
        self.scroll_interval = 50  # 滚动间隔（毫秒）
        self.is_paused = False
        self.pause_timer = QTimer()
        self.pause_timer.timeout.connect(self.resume_scroll)
        self.pause_timer.setSingleShot(True)
        
        # 设置样式
        self.setStyleSheet("""
            QLabel {
                background-color: #2a2d35;
                color: #D3D8E0;
                border: 1px solid #505869;
                padding: 4px 8px;
                border-radius: 3px;
            }
        """)
        
    def setText(self, text):
        """设置文本内容"""
        self.full_text = text
        self.scroll_position = 0
        self.scroll_direction = 1
        self.is_paused = False
        self.update_display()
        
        # 检查是否需要滚动
        if self.needs_scrolling():
            self.start_scrolling()
        else:
            self.stop_scrolling()
            
    def setPlaceholderText(self, text):
        """设置占位符文本"""
        self.placeholder_text = text
        if not self.full_text:
            super().setText(text)
            
    def needs_scrolling(self):
        """检查文本是否需要滚动"""
        if not self.full_text:
            return False
            
        font_metrics = QFontMetrics(self.font())
        text_width = font_metrics.horizontalAdvance(self.full_text)
        available_width = self.width() - 16  # 减去padding
        
        return text_width > available_width
        
    def start_scrolling(self):
        """开始滚动"""
        if not self.scroll_timer.isActive():
            self.scroll_timer.start(self.scroll_interval)
            
    def stop_scrolling(self):
        """停止滚动"""
        self.scroll_timer.stop()
        self.pause_timer.stop()
        self.scroll_position = 0
        self.is_paused = False
        
    def scroll_text(self):
        """滚动文本"""
        if self.is_paused or not self.full_text:
            return
            
        font_metrics = QFontMetrics(self.font())
        text_width = font_metrics.horizontalAdvance(self.full_text)
        available_width = self.width() - 16  # 减去padding
        
        if text_width <= available_width:
            self.stop_scrolling()
            return
            
        # 计算滚动边界
        max_scroll = text_width - available_width
        
        # 更新滚动位置
        self.scroll_position += self.scroll_speed * self.scroll_direction
        
        # 检查边界并处理反弹
        if self.scroll_position >= max_scroll:
            self.scroll_position = max_scroll
            self.scroll_direction = -1
            self.pause_scroll()
        elif self.scroll_position <= 0:
            self.scroll_position = 0
            self.scroll_direction = 1
            self.pause_scroll()
            
        self.update_display()
        
    def pause_scroll(self):
        """暂停滚动"""
        self.is_paused = True
        self.pause_timer.start(self.pause_duration)
        
    def resume_scroll(self):
        """恢复滚动"""
        self.is_paused = False
        
    def update_display(self):
        """更新显示内容"""
        if not self.full_text:
            super().setText(self.placeholder_text)
            return
            
        if not self.needs_scrolling():
            super().setText(self.full_text)
            return
            
        # 计算显示的文本片段
        font_metrics = QFontMetrics(self.font())
        available_width = self.width() - 16  # 减去padding
        
        # 从滚动位置开始，找到能显示的文本
        display_text = ""
        current_width = 0
        start_pos = 0
        
        # 找到滚动位置对应的字符位置
        for i, char in enumerate(self.full_text):
            char_width = font_metrics.horizontalAdvance(char)
            if current_width + char_width > self.scroll_position:
                start_pos = i
                break
            current_width += char_width
            
        # 从start_pos开始构建显示文本
        current_width = 0
        for i in range(start_pos, len(self.full_text)):
            char = self.full_text[i]
            char_width = font_metrics.horizontalAdvance(char)
            if current_width + char_width > available_width:
                break
            display_text += char
            current_width += char_width
            
        super().setText(display_text)
        
    def resizeEvent(self, event):
        """处理大小改变事件"""
        super().resizeEvent(event)
        
        # 重新检查是否需要滚动
        if self.full_text:
            if self.needs_scrolling():
                self.start_scrolling()
            else:
                self.stop_scrolling()
            self.update_display()
            
    def enterEvent(self, event):
        """鼠标进入时暂停滚动"""
        super().enterEvent(event)
        if self.scroll_timer.isActive():
            self.scroll_timer.stop()
            
    def leaveEvent(self, event):
        """鼠标离开时恢复滚动"""
        super().leaveEvent(event)
        if self.full_text and self.needs_scrolling():
            self.start_scrolling()
