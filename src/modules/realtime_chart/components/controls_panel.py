"""控制面板组件"""
from PySide6.QtWidgets import (
    QWidget, QGroupBox, QHBoxLayout, QVBoxLayout, QPushButton,
    QLabel, QSlider, QCheckBox
)
from PySide6.QtCore import Signal, Qt


class ControlsPanel(QGroupBox):
    """
    控制面板
    提供播放控制、缩放控制等功能
    """
    
    # 信号定义
    play_clicked = Signal()
    pause_clicked = Signal()
    stop_clicked = Signal()
    reset_clicked = Signal()
    zoom_changed = Signal(int)
    auto_switch_toggled = Signal(bool)
    
    def __init__(self, parent=None):
        super().__init__("控制面板", parent)
        self.setup_ui()
        self.apply_styles()
        
    def setup_ui(self):
        """设置UI布局"""
        layout = QHBoxLayout(self)
        
        # 播放控制组
        playback_group = self._create_playback_controls()
        layout.addWidget(playback_group)
        
        # 缩放控制组
        zoom_group = self._create_zoom_controls()
        layout.addWidget(zoom_group)
        
        # 其他控制
        other_group = self._create_other_controls()
        layout.addWidget(other_group)
        
        layout.addStretch()
        
    def _create_playback_controls(self) -> QWidget:
        """创建播放控制组"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel("数据播放:")
        layout.addWidget(label)
        
        button_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("播放")
        self.play_btn.clicked.connect(self.play_clicked.emit)
        button_layout.addWidget(self.play_btn)
        
        self.pause_btn = QPushButton("暂停")
        self.pause_btn.clicked.connect(self.pause_clicked.emit)
        self.pause_btn.setEnabled(False)
        button_layout.addWidget(self.pause_btn)
        
        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(self.stop_clicked.emit)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        layout.addLayout(button_layout)
        
        return widget
        
    def _create_zoom_controls(self) -> QWidget:
        """创建缩放控制组"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel("图表缩放:")
        layout.addWidget(label)
        
        zoom_layout = QHBoxLayout()
        
        zoom_layout.addWidget(QLabel("25%"))
        
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(25, 200)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setTickInterval(25)
        self.zoom_slider.setTickPosition(QSlider.TicksBelow)
        self.zoom_slider.valueChanged.connect(self.zoom_changed.emit)
        zoom_layout.addWidget(self.zoom_slider)
        
        zoom_layout.addWidget(QLabel("200%"))
        
        self.zoom_label = QLabel("100%")
        zoom_layout.addWidget(self.zoom_label)
        
        layout.addLayout(zoom_layout)
        
        # 重置按钮
        self.reset_btn = QPushButton("重置视图")
        self.reset_btn.clicked.connect(self.reset_clicked.emit)
        layout.addWidget(self.reset_btn)
        
        return widget
        
    def _create_other_controls(self) -> QWidget:
        """创建其他控制"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel("其他选项:")
        layout.addWidget(label)
        
        self.auto_switch_check = QCheckBox("自动切换图像")
        self.auto_switch_check.toggled.connect(self.auto_switch_toggled.emit)
        layout.addWidget(self.auto_switch_check)
        
        return widget
        
    def apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #333333;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 12px;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #cccccc;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #2196F3;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::sub-page:horizontal {
                background: #2196F3;
                border-radius: 3px;
            }
        """)
        
    def set_playing_state(self, is_playing: bool):
        """设置播放状态"""
        self.play_btn.setEnabled(not is_playing)
        self.pause_btn.setEnabled(is_playing)
        self.stop_btn.setEnabled(is_playing)
        
    def update_zoom_label(self, value: int):
        """更新缩放标签"""
        self.zoom_label.setText(f"{value}%")
        
    def reset_controls(self):
        """重置控制状态"""
        self.set_playing_state(False)
        self.zoom_slider.setValue(100)
        self.auto_switch_check.setChecked(False)