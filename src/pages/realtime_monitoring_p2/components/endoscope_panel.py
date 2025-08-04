"""
内窥镜视图面板组件
显示内窥镜图像或模拟视图
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QGroupBox, QSlider, QComboBox
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QPixmap, QPainter, QBrush, QColor, QPen
import logging
import random
from pathlib import Path


class EndoscopePanel(QWidget):
    """
    内窥镜视图面板
    
    功能：
    1. 显示内窥镜实时图像
    2. 模拟内窥镜视图
    3. 图像亮度/对比度调节
    4. 图像捕获和保存
    """
    
    # 信号定义
    image_captured = Signal(str)  # 图像捕获
    view_mode_changed = Signal(str)  # 视图模式改变
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 视图状态
        self.view_mode = "simulation"  # simulation/real
        self.current_image_path = None
        self.brightness = 50
        self.contrast = 50
        
        # 初始化UI
        self._init_ui()
        
        # 模拟更新定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_simulation)
        self.update_timer.start(500)  # 500ms更新一次
        
    def _init_ui(self):
        """初始化UI布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 控制区域（紧凑设计）
        control_group = QGroupBox("视图控制")
        control_group.setMaximumHeight(80)  # 限制控制区域高度
        control_layout = QHBoxLayout(control_group)  # 改为水平布局
        
        # 模式选择（紧凑）
        mode_label = QLabel("模式:")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["模拟视图", "实际图像"])
        self.mode_combo.setMaximumWidth(80)
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        
        control_layout.addWidget(mode_label)
        control_layout.addWidget(self.mode_combo)
        control_layout.addSpacing(10)
        
        # 亮度调节（紧凑）
        brightness_label = QLabel("亮度:")
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(0, 100)
        self.brightness_slider.setValue(self.brightness)
        self.brightness_slider.setMaximumWidth(80)
        self.brightness_slider.valueChanged.connect(self._on_brightness_changed)
        self.brightness_value = QLabel(str(self.brightness))
        self.brightness_value.setMinimumWidth(25)
        
        control_layout.addWidget(brightness_label)
        control_layout.addWidget(self.brightness_slider)
        control_layout.addWidget(self.brightness_value)
        control_layout.addSpacing(10)
        
        # 对比度调节（紧凑）
        contrast_label = QLabel("对比度:")
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(0, 100)
        self.contrast_slider.setValue(self.contrast)
        self.contrast_slider.setMaximumWidth(80)
        self.contrast_slider.valueChanged.connect(self._on_contrast_changed)
        self.contrast_value = QLabel(str(self.contrast))
        self.contrast_value.setMinimumWidth(25)
        
        control_layout.addWidget(contrast_label)
        control_layout.addWidget(self.contrast_slider)
        control_layout.addWidget(self.contrast_value)
        control_layout.addSpacing(10)
        
        # 捕获按钮（紧凑）
        capture_btn = QPushButton("捕获图像")
        capture_btn.setMaximumHeight(30)
        capture_btn.clicked.connect(self._capture_image)
        
        control_layout.addWidget(capture_btn)
        control_layout.addStretch()
        
        # 视图区域
        view_group = QGroupBox("内窥镜视图")
        view_layout = QVBoxLayout(view_group)
        
        # 图像显示标签
        self.image_label = QLabel()
        self.image_label.setMinimumSize(400, 300)
        self.image_label.setMaximumSize(800, 600)
        self.image_label.setScaledContents(True)
        self.image_label.setStyleSheet("""
            QLabel {
                border: 2px solid #ccc;
                background-color: #000;
                border-radius: 5px;
            }
        """)
        self.image_label.setAlignment(Qt.AlignCenter)
        
        # 状态信息
        self.status_label = QLabel("状态: 准备就绪")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        view_layout.addWidget(self.image_label)
        view_layout.addWidget(self.status_label)
        
        # 添加到主布局
        layout.addWidget(control_group)
        layout.addWidget(view_group)
        
        # 初始化视图
        self._init_simulation_view()
        
    def _init_simulation_view(self):
        """初始化模拟视图"""
        # 创建模拟图像
        pixmap = QPixmap(640, 480)
        pixmap.fill(Qt.black)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制模拟管道内部视图
        center_x = pixmap.width() // 2
        center_y = pixmap.height() // 2
        
        # 绘制同心圆模拟管道深度
        for i in range(5):
            radius = 200 - i * 40
            color = QColor(50 + i * 20, 50 + i * 20, 50 + i * 20)
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(Qt.NoPen))
            painter.drawEllipse(center_x - radius, center_y - radius, 
                              radius * 2, radius * 2)
        
        # 添加一些模拟缺陷
        painter.setBrush(QBrush(QColor(200, 50, 50)))
        for _ in range(3):
            x = center_x + random.randint(-150, 150)
            y = center_y + random.randint(-150, 150)
            painter.drawEllipse(x - 5, y - 5, 10, 10)
        
        # 添加文字
        painter.setPen(QPen(Qt.white))
        painter.drawText(10, 20, "内窥镜模拟视图")
        painter.drawText(10, 40, f"亮度: {self.brightness}%")
        painter.drawText(10, 60, f"对比度: {self.contrast}%")
        
        painter.end()
        
        self.image_label.setPixmap(pixmap)
        
    def _update_simulation(self):
        """更新模拟视图"""
        if self.view_mode == "simulation":
            self._init_simulation_view()
            
    def _on_mode_changed(self, mode_text: str):
        """视图模式改变"""
        if mode_text == "模拟视图":
            self.view_mode = "simulation"
            self._init_simulation_view()
            self.status_label.setText("状态: 模拟视图模式")
        else:
            self.view_mode = "real"
            self._load_real_image()
            self.status_label.setText("状态: 实际图像模式")
            
        self.view_mode_changed.emit(self.view_mode)
        self.logger.info(f"视图模式切换到: {self.view_mode}")
        
    def _load_real_image(self):
        """加载实际图像"""
        # 这里应该连接到实际的内窥镜设备
        # 目前使用占位符图像
        pixmap = QPixmap(640, 480)
        pixmap.fill(Qt.darkGray)
        
        painter = QPainter(pixmap)
        painter.setPen(QPen(Qt.white))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, 
                        "内窥镜实际图像\n(未连接设备)")
        painter.end()
        
        self.image_label.setPixmap(pixmap)
        
    def _on_brightness_changed(self, value: int):
        """亮度改变"""
        self.brightness = value
        self.brightness_value.setText(str(value))
        self._apply_image_adjustments()
        
    def _on_contrast_changed(self, value: int):
        """对比度改变"""
        self.contrast = value
        self.contrast_value.setText(str(value))
        self._apply_image_adjustments()
        
    def _apply_image_adjustments(self):
        """应用图像调整"""
        # 在实际实现中，这里应该调整图像的亮度和对比度
        # 目前只更新显示
        if self.view_mode == "simulation":
            self._init_simulation_view()
            
    def _capture_image(self):
        """捕获当前图像"""
        # 获取当前显示的图像
        pixmap = self.image_label.pixmap()
        if pixmap:
            # 生成文件名
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"endoscope_capture_{timestamp}.png"
            
            # 保存图像（实际应用中应该让用户选择保存路径）
            save_path = Path("captured_images") / filename
            save_path.parent.mkdir(exist_ok=True)
            
            pixmap.save(str(save_path))
            
            self.image_captured.emit(str(save_path))
            self.status_label.setText(f"状态: 图像已捕获 - {filename}")
            self.logger.info(f"图像已捕获: {save_path}")
        else:
            self.logger.warning("没有图像可以捕获")
            
    def load_image(self, image_path: str):
        """加载外部图像"""
        if Path(image_path).exists():
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # 缩放到合适大小
                scaled_pixmap = pixmap.scaled(
                    self.image_label.size(), 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
                self.current_image_path = image_path
                self.status_label.setText(f"状态: 已加载图像 - {Path(image_path).name}")
                self.logger.info(f"已加载图像: {image_path}")
            else:
                self.logger.error(f"无法加载图像: {image_path}")
        else:
            self.logger.error(f"图像文件不存在: {image_path}")
            
    def set_hole_id(self, hole_id: str):
        """设置当前孔位ID"""
        self.status_label.setText(f"状态: 当前孔位 - {hole_id}")
        
    def clear_view(self):
        """清除视图"""
        self.image_label.clear()
        self.image_label.setText("无图像")
        self.status_label.setText("状态: 视图已清除")
        self.current_image_path = None