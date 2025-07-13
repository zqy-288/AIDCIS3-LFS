"""中央可视化面板组件"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QComboBox
)
from PySide6.QtCore import Signal

from aidcis2.graphics.graphics_view import OptimizedGraphicsView
from aidcis2.models.hole_data import HoleCollection


class VisualizationPanel(QWidget):
    """
    中央可视化面板
    包含图形视图和视图控制
    """
    
    # 信号定义
    view_mode_changed = Signal(str)
    zoom_in_clicked = Signal()
    zoom_out_clicked = Signal()
    fit_view_clicked = Signal()
    reset_view_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建视图控制栏
        controls = self._create_view_controls()
        layout.addWidget(controls)
        
        # 创建图形视图
        self.graphics_view = OptimizedGraphicsView()
        layout.addWidget(self.graphics_view)
        
        # 创建状态图例
        legend = self._create_status_legend()
        layout.addWidget(legend)
        
    def _create_view_controls(self) -> QWidget:
        """创建视图控制栏"""
        container = QFrame()
        container.setFrameStyle(QFrame.StyledPanel)
        container.setMaximumHeight(50)
        
        layout = QHBoxLayout(container)
        
        # 视图模式选择
        layout.addWidget(QLabel("视图模式:"))
        self.view_mode_combo = QComboBox()
        self.view_mode_combo.addItems(["宏观视图", "微观视图", "扇形视图"])
        self.view_mode_combo.currentTextChanged.connect(self.view_mode_changed.emit)
        layout.addWidget(self.view_mode_combo)
        
        layout.addSpacing(20)
        
        # 缩放控制按钮
        self.zoom_in_btn = QPushButton("放大")
        self.zoom_in_btn.clicked.connect(self.zoom_in_clicked.emit)
        layout.addWidget(self.zoom_in_btn)
        
        self.zoom_out_btn = QPushButton("缩小")
        self.zoom_out_btn.clicked.connect(self.zoom_out_clicked.emit)
        layout.addWidget(self.zoom_out_btn)
        
        self.fit_view_btn = QPushButton("适应窗口")
        self.fit_view_btn.clicked.connect(self.fit_view_clicked.emit)
        layout.addWidget(self.fit_view_btn)
        
        self.reset_view_btn = QPushButton("重置视图")
        self.reset_view_btn.clicked.connect(self.reset_view_clicked.emit)
        layout.addWidget(self.reset_view_btn)
        
        layout.addStretch()
        
        return container
        
    def _create_status_legend(self) -> QWidget:
        """创建状态图例"""
        container = QFrame()
        container.setFrameStyle(QFrame.StyledPanel)
        container.setMaximumHeight(50)
        
        layout = QHBoxLayout(container)
        
        # 添加图例说明
        layout.addWidget(QLabel("状态图例:"))
        
        legend_items = [
            ("待检", "#808080"),
            ("检测中", "#0080FF"),
            ("合格", "#00FF00"),
            ("异常", "#FF0000"),
            ("盲孔", "#FFFF00"),
            ("拉杆孔", "#00FFFF")
        ]
        
        for text, color in legend_items:
            # 创建颜色标记
            color_label = QLabel()
            color_label.setFixedSize(20, 20)
            color_label.setStyleSheet(
                f"background-color: {color}; "
                f"border: 1px solid black; "
                f"border-radius: 10px;"
            )
            layout.addWidget(color_label)
            
            # 添加文字
            layout.addWidget(QLabel(text))
            layout.addSpacing(15)
            
        layout.addStretch()
        
        return container
        
    def set_hole_collection(self, hole_collection: HoleCollection):
        """设置孔位集合"""
        if self.graphics_view and hole_collection:
            self.graphics_view.load_holes(hole_collection)
            
    def get_view_mode(self) -> str:
        """获取当前视图模式"""
        return self.view_mode_combo.currentText()
        
    def enable_controls(self, enabled: bool):
        """启用/禁用控制按钮"""
        self.zoom_in_btn.setEnabled(enabled)
        self.zoom_out_btn.setEnabled(enabled)
        self.fit_view_btn.setEnabled(enabled)
        self.reset_view_btn.setEnabled(enabled)