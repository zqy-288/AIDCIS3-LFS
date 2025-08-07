"""
图片浏览界面模块
用于人工复检的入口点，支持图片浏览和跳转到缺陷标注界面
"""

import os
from typing import List, Optional
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton, 
                               QLabel, QMessageBox, QFrame, QSizePolicy)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QFont


class ImageDisplayWidget(QLabel):
    """图片显示控件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                border: 2px solid #cccccc;
                background-color: #000000;
                border-radius: 5px;
                color: #ffffff;
            }
        """)
        self.setMinimumSize(600, 400)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # 移除setScaledContents，让我们手动控制缩放以保持宽高比
        
    def load_image(self, image_path: str) -> bool:
        """加载图片"""
        try:
            if not os.path.exists(image_path):
                self.setText("图片文件不存在")
                return False
                
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                self.setText("无法加载图片")
                return False
            
            # 保存原始图片用于后续缩放
            self._original_pixmap = pixmap
            
            # 获取控件的可用大小
            available_size = self.size()
            
            # 如果控件尺寸太小，使用最小尺寸
            if available_size.width() < 100 or available_size.height() < 100:
                available_size = self.minimumSize()
            
            # 计算缩放后的尺寸，保持宽高比
            scaled_pixmap = pixmap.scaled(
                available_size,
                Qt.KeepAspectRatio,  # 保持宽高比
                Qt.SmoothTransformation  # 平滑缩放
            )
            
            # 清除文本并设置图片
            self.clear()
            self.setPixmap(scaled_pixmap)
            
            # 设置对齐方式为居中
            self.setAlignment(Qt.AlignCenter)
            
            # 强制更新显示
            self.update()
            return True
            
        except Exception as e:
            self.setText(f"加载图片失败: {str(e)}")
            return False
    
    def clear_image(self):
        """清除图片"""
        self._original_pixmap = None
        self.clear()
        self.setText("无图片")
        
    def resizeEvent(self, event):
        """当控件大小改变时重新缩放图片"""
        super().resizeEvent(event)
        
        # 如果有图片，重新缩放以适应新尺寸
        if hasattr(self, '_original_pixmap') and self._original_pixmap:
            scaled_pixmap = self._original_pixmap.scaled(
                self.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.setPixmap(scaled_pixmap)


class ImageBrowser(QWidget):
    """图片浏览界面"""
    
    # 信号定义
    manual_review_requested = Signal(str)  # 请求人工复检，传递图片路径
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 图片相关
        self.image_directory = "result/panorama/without_axes"
        self.image_files: List[str] = []
        self.current_index = 0
        self.current_image_path: Optional[str] = None
        
        # 初始化UI
        self.init_ui()
        
        # 扫描图片文件
        self.scan_images()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("人工复检 - 图片浏览")
        self.setMinimumSize(1000, 700)
        
        # 创建主布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # 左侧图片显示区域
        self.create_image_display_area()
        main_layout.addWidget(self.image_display_frame, 7)  # 70%宽度
        
        # 右侧操作面板
        self.create_control_panel()
        main_layout.addWidget(self.control_panel, 3)  # 30%宽度
        
    def create_image_display_area(self):
        """创建左侧图片显示区域"""
        self.image_display_frame = QFrame()
        self.image_display_frame.setFrameStyle(QFrame.StyledPanel)
        
        layout = QVBoxLayout(self.image_display_frame)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        title_label = QLabel("当前图片")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 图片显示控件
        self.image_display = ImageDisplayWidget()
        layout.addWidget(self.image_display)
        
        # 图片信息显示
        self.image_info_label = QLabel("无图片")
        self.image_info_label.setAlignment(Qt.AlignCenter)
        self.image_info_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(self.image_info_label)
        
    def create_control_panel(self):
        """创建右侧操作面板"""
        self.control_panel = QFrame()
        self.control_panel.setFrameStyle(QFrame.StyledPanel)
        self.control_panel.setFixedWidth(300)
        
        layout = QVBoxLayout(self.control_panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)
        
        # 标题
        panel_title = QLabel("操作面板")
        panel_title.setFont(QFont("Arial", 14, QFont.Bold))
        panel_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(panel_title)
        
        # 图片导航信息
        self.navigation_label = QLabel("图片: 0 / 0")
        self.navigation_label.setAlignment(Qt.AlignCenter)
        self.navigation_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        layout.addWidget(self.navigation_label)
        
        # 当前图片文件名
        self.filename_label = QLabel("文件名: 无")
        self.filename_label.setWordWrap(True)
        self.filename_label.setStyleSheet("color: #333; font-size: 11px;")
        layout.addWidget(self.filename_label)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # 核心操作按钮
        button_layout = QVBoxLayout()
        button_layout.setSpacing(15)
        
        # 查看下一张按钮
        self.next_btn = QPushButton("查看下一张")
        self.next_btn.setFont(QFont("Arial", 12))
        self.next_btn.setMinimumHeight(50)
        self.next_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.next_btn.clicked.connect(self.load_next_image)
        button_layout.addWidget(self.next_btn)
        
        # 人工复检按钮
        self.review_btn = QPushButton("人工复检")
        self.review_btn.setFont(QFont("Arial", 12))
        self.review_btn.setMinimumHeight(50)
        self.review_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.review_btn.clicked.connect(self.start_manual_review)
        button_layout.addWidget(self.review_btn)
        
        layout.addLayout(button_layout)
        
        # 添加弹性空间
        layout.addStretch()
        
        # 目录信息
        directory_info = QLabel(f"图片目录:\n{self.image_directory}")
        directory_info.setWordWrap(True)
        directory_info.setStyleSheet("color: #666; font-size: 10px; border-top: 1px solid #ddd; padding-top: 10px;")
        layout.addWidget(directory_info)
        
    def scan_images(self):
        """扫描图片文件"""
        self.image_files.clear()
        self.current_index = 0
        
        if not os.path.exists(self.image_directory):
            QMessageBox.warning(self, "警告", f"图片目录不存在: {self.image_directory}")
            self.update_ui_state()
            return
            
        # 支持的图片格式
        supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.jfif'}
        
        try:
            # 获取目录中的所有图片文件
            for filename in os.listdir(self.image_directory):
                file_path = os.path.join(self.image_directory, filename)
                if (os.path.isfile(file_path) and 
                    any(filename.lower().endswith(ext) for ext in supported_formats)):
                    self.image_files.append(file_path)
            
            # 按文件名排序
            self.image_files.sort()
            
            if self.image_files:
                # 加载第一张图片
                self.load_current_image()
            else:
                QMessageBox.information(self, "信息", f"在目录 {self.image_directory} 中未找到图片文件")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"扫描图片文件时发生错误: {str(e)}")
            
        self.update_ui_state()
        
    def load_current_image(self):
        """加载当前索引的图片"""
        if not self.image_files or self.current_index >= len(self.image_files):
            self.current_image_path = None
            self.image_display.clear_image()
            return False
            
        image_path = self.image_files[self.current_index]
        self.current_image_path = image_path
        
        # 加载图片
        if self.image_display.load_image(image_path):
            # 更新信息显示
            filename = os.path.basename(image_path)
            try:
                file_size = os.path.getsize(image_path)
                size_mb = file_size / (1024 * 1024)
                info_text = f"{filename} ({size_mb:.1f} MB)"
            except OSError:
                info_text = filename
                
            self.image_info_label.setText(info_text)
            self.filename_label.setText(f"文件名: {filename}")
            return True
        else:
            self.image_info_label.setText("加载图片失败")
            self.filename_label.setText("文件名: 无")
            return False
            
    def load_next_image(self):
        """加载下一张图片"""
        if not self.image_files:
            QMessageBox.information(self, "提示", "没有可用的图片文件")
            return
            
        # 移动到下一张
        self.current_index = (self.current_index + 1) % len(self.image_files)
        
        # 加载图片
        self.load_current_image()
        self.update_ui_state()
        
    def start_manual_review(self):
        """启动人工复检"""
        if not self.current_image_path:
            QMessageBox.warning(self, "警告", "请先选择要复检的图片")
            return
            
        # 发送信号请求人工复检
        self.manual_review_requested.emit(self.current_image_path)
        
    def update_ui_state(self):
        """更新UI状态"""
        # 更新导航信息
        if self.image_files:
            nav_text = f"图片: {self.current_index + 1} / {len(self.image_files)}"
        else:
            nav_text = "图片: 0 / 0"
        self.navigation_label.setText(nav_text)
        
        # 更新按钮状态
        has_images = bool(self.image_files)
        self.next_btn.setEnabled(has_images)
        self.review_btn.setEnabled(has_images and self.current_image_path is not None)
        
    def get_current_image_path(self) -> Optional[str]:
        """获取当前图片路径"""
        return self.current_image_path
        
    def refresh_images(self):
        """刷新图片列表"""
        self.scan_images()