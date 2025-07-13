"""状态信息面板组件"""
from PySide6.QtWidgets import (
    QGroupBox, QHBoxLayout, QVBoxLayout, QLabel, QComboBox
)
from PySide6.QtCore import Signal


class StatusPanel(QGroupBox):
    """
    状态信息面板
    显示当前孔位、标准直径、实时状态等信息
    """
    
    # 信号定义
    hole_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__("检测状态", parent)
        self.setup_ui()
        self.apply_styles()
        
    def setup_ui(self):
        """设置UI布局"""
        layout = QHBoxLayout(self)
        
        # 当前孔位显示
        self.current_hole_label = QLabel("当前孔位：未选择")
        self.current_hole_label.setMinimumWidth(140)
        layout.addWidget(self.current_hole_label)
        
        # 标准直径显示
        self.standard_diameter_label = QLabel("标准直径：17.6mm")
        layout.addWidget(self.standard_diameter_label)
        
        # 孔位选择下拉框
        hole_select_layout = QVBoxLayout()
        hole_select_label = QLabel("选择孔位:")
        self.hole_selector = QComboBox()
        self.hole_selector.setMinimumWidth(120)
        self.hole_selector.currentTextChanged.connect(self._on_hole_selected)
        
        hole_select_layout.addWidget(hole_select_label)
        hole_select_layout.addWidget(self.hole_selector)
        layout.addLayout(hole_select_layout)
        
        # 最大最小直径显示
        diameter_layout = QVBoxLayout()
        self.max_diameter_label = QLabel("最大圆直径: --")
        self.min_diameter_label = QLabel("最小圆直径: --")
        diameter_layout.addWidget(self.max_diameter_label)
        diameter_layout.addWidget(self.min_diameter_label)
        layout.addLayout(diameter_layout)
        
        # 实时状态显示
        status_layout = QVBoxLayout()
        self.depth_label = QLabel("探头深度: -- mm")
        self.comm_status_label = QLabel("通信状态: --")
        status_layout.addWidget(self.depth_label)
        status_layout.addWidget(self.comm_status_label)
        layout.addLayout(status_layout)
        
        layout.addStretch()
        
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
        """)
        
        # 当前孔位标签样式
        self.current_hole_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2196F3;
                padding: 8px 12px;
                background-color: #f0f8ff;
                border: 2px solid #2196F3;
                border-radius: 6px;
            }
        """)
        
        # 标准直径标签样式
        self.standard_diameter_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #4CAF50;
                padding: 8px 12px;
                background-color: #f8fff8;
                border: 2px solid #4CAF50;
                border-radius: 6px;
            }
        """)
        
        # 最大最小直径标签样式
        diameter_style = """
            QLabel {
                font-size: 12px;
                padding: 4px;
                color: #666666;
            }
        """
        self.max_diameter_label.setStyleSheet(diameter_style)
        self.min_diameter_label.setStyleSheet(diameter_style)
        
    def set_current_hole(self, hole_id: str):
        """设置当前孔位"""
        self.current_hole_label.setText(f"当前孔位：{hole_id}")
        
        # 同步下拉框
        index = self.hole_selector.findText(hole_id)
        if index >= 0:
            self.hole_selector.blockSignals(True)
            self.hole_selector.setCurrentIndex(index)
            self.hole_selector.blockSignals(False)
            
    def set_standard_diameter(self, diameter: float):
        """设置标准直径"""
        self.standard_diameter_label.setText(f"标准直径：{diameter:.1f}mm")
        
    def update_extremes(self, min_diameter: float, max_diameter: float):
        """更新最大最小直径"""
        self.max_diameter_label.setText(f"最大圆直径: {max_diameter:.3f} mm")
        self.min_diameter_label.setText(f"最小圆直径: {min_diameter:.3f} mm")
        
    def update_depth(self, depth: float):
        """更新探头深度"""
        self.depth_label.setText(f"探头深度: {depth:.1f} mm")
        
    def update_comm_status(self, status: str):
        """更新通信状态"""
        self.comm_status_label.setText(f"通信状态: {status}")
        
        # 根据状态改变颜色
        if status == "连接正常":
            self.comm_status_label.setStyleSheet("color: green; font-size: 12px;")
        else:
            self.comm_status_label.setStyleSheet("color: red; font-size: 12px;")
            
    def add_hole_options(self, hole_ids: list):
        """添加孔位选项"""
        self.hole_selector.clear()
        self.hole_selector.addItems(["请选择孔位"] + hole_ids)
        
    def _on_hole_selected(self, hole_id: str):
        """处理孔位选择"""
        if hole_id and hole_id != "请选择孔位":
            self.hole_changed.emit(hole_id)
            
    def clear_status(self):
        """清除状态信息"""
        self.current_hole_label.setText("当前孔位：未选择")
        self.max_diameter_label.setText("最大圆直径: --")
        self.min_diameter_label.setText("最小圆直径: --")
        self.depth_label.setText("探头深度: -- mm")
        self.comm_status_label.setText("通信状态: --")
        self.comm_status_label.setStyleSheet("font-size: 12px;")