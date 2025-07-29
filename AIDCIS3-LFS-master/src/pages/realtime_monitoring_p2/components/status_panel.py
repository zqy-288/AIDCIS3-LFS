"""
状态监控面板组件
负责显示当前孔位、标准直径、最大最小直径等状态信息，以及控制按钮
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QGroupBox
)
from PySide6.QtCore import Signal, Qt


class StatusPanel(QWidget):
    """
    状态监控与主控制区面板
    完全按照原项目的水平布局设计
    """
    
    # 信号定义
    start_clicked = Signal()
    stop_clicked = Signal()
    clear_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """设置用户界面 - 完全按照重构前的原始布局"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 状态信息面板 - 完全按照重构前的"状态监控与主控制区"设计
        status_group = QGroupBox("状态监控与主控制区")
        status_group.setObjectName("StatusDashboard")
        status_layout = QHBoxLayout(status_group)
        status_layout.setContentsMargins(10, 10, 10, 10)
        status_layout.setSpacing(15)

        # 左侧：核心状态信息 - 按照重构前的精确布局
        status_info_layout = QHBoxLayout()
        status_info_layout.setSpacing(20)

        # 当前孔位显示 - 按照重构前样式
        self.current_hole_label = QLabel("当前孔位：未选择")
        self.current_hole_label.setObjectName("InfoLabel")
        self.current_hole_label.setMinimumWidth(140)
        status_info_layout.addWidget(self.current_hole_label)

        # 通信状态显示 - 重构前的重要组件
        self.comm_status_label = QLabel("通信状态: 等待连接")
        self.comm_status_label.setObjectName("CommStatusLabel")
        self.comm_status_label.setMinimumWidth(150)
        status_info_layout.addWidget(self.comm_status_label)

        # 标准直径显示 - 按照重构前样式
        self.standard_diameter_label = QLabel("标准直径：17.73mm")
        self.standard_diameter_label.setObjectName("StaticInfoLabel")
        self.standard_diameter_label.setMinimumWidth(140)
        status_info_layout.addWidget(self.standard_diameter_label)

        status_layout.addLayout(status_info_layout)
        status_layout.addStretch(1)

        # 中间：实时数据显示 - 重构前的关键信息
        realtime_info_layout = QHBoxLayout()
        realtime_info_layout.setSpacing(15)

        self.depth_label = QLabel("📏 探头深度: -- mm")
        self.max_diameter_label = QLabel("📈 最大直径: -- mm")
        self.min_diameter_label = QLabel("📉 最小直径: -- mm")

        # 使用重构前的样式设置
        self.depth_label.setObjectName("StatusLabel")
        self.max_diameter_label.setObjectName("StatusLabel")
        self.min_diameter_label.setObjectName("StatusLabel")

        # 设置最小宽度，让文本窗口适当放长
        self.depth_label.setMinimumWidth(180)
        self.max_diameter_label.setMinimumWidth(180)
        self.min_diameter_label.setMinimumWidth(180)

        realtime_info_layout.addWidget(self.depth_label)
        realtime_info_layout.addWidget(self.max_diameter_label)
        realtime_info_layout.addWidget(self.min_diameter_label)

        status_layout.addLayout(realtime_info_layout)
        status_layout.addStretch(1)

        # 右侧：主控制按钮区域 - 按照重构前样式
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)

        # 创建主控制按钮 - 添加图标，按照重构前样式
        self.start_button = QPushButton("▶️ 开始监测")
        self.stop_button = QPushButton("⏸️ 停止监测")
        self.clear_button = QPushButton("🗑️ 清除数据")

        # 设置按钮样式
        self.start_button.setObjectName("StartButton")
        self.stop_button.setObjectName("StopButton")
        self.clear_button.setObjectName("ClearDataButton")

        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.clear_button)

        status_layout.addLayout(control_layout)
        layout.addWidget(status_group)
        
        # 初始状态设置
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.clear_button.setEnabled(True)

        # 设置按钮提示
        self.start_button.setToolTip("启动采集控制程序 (LEConfocalDemo.exe)")
        self.stop_button.setToolTip("停止采集控制程序")
        self.clear_button.setToolTip("清除当前数据")
        
    def setup_connections(self):
        """设置信号连接"""
        self.start_button.clicked.connect(self.start_clicked.emit)
        self.stop_button.clicked.connect(self.stop_clicked.emit)
        self.clear_button.clicked.connect(self.clear_clicked.emit)
        
    def update_current_hole(self, hole_id: str):
        """更新当前孔位显示 - 按照重构前样式"""
        if hole_id:
            self.current_hole_label.setText(f"当前孔位：{hole_id}")
        else:
            self.current_hole_label.setText("当前孔位：未选择")

    def update_comm_status(self, status_type: str, message: str):
        """更新通信状态显示 - 重构前的重要功能"""
        self.comm_status_label.setText(f"通信状态: {message}")

        # 根据状态类型设置不同的样式（可选）
        if status_type == "connected":
            self.comm_status_label.setStyleSheet("color: green;")
        elif status_type == "disconnected":
            self.comm_status_label.setStyleSheet("color: red;")
        elif status_type == "waiting":
            self.comm_status_label.setStyleSheet("color: orange;")
        else:
            self.comm_status_label.setStyleSheet("")

    def update_depth(self, depth: float):
        """更新探头深度显示 - 重构前的重要信息"""
        if depth is not None:
            self.depth_label.setText(f"📏 探头深度: {depth:.1f} mm")
        else:
            self.depth_label.setText("📏 探头深度: -- mm")

    def update_standard_diameter(self, diameter: float):
        """更新标准直径显示 - 按照重构前样式"""
        self.standard_diameter_label.setText(f"标准直径：{diameter:.2f}mm")

    def update_max_diameter(self, diameter: float):
        """更新最大直径显示 - 按照重构前样式"""
        if diameter is not None:
            self.max_diameter_label.setText(f"📈 最大直径: {diameter:.3f} mm")
        else:
            self.max_diameter_label.setText("📈 最大直径: -- mm")

    def update_min_diameter(self, diameter: float):
        """更新最小直径显示 - 按照重构前样式"""
        if diameter is not None:
            self.min_diameter_label.setText(f"📉 最小直径: {diameter:.3f} mm")
        else:
            self.min_diameter_label.setText("📉 最小直径: -- mm")
            
    def set_monitoring_state(self, is_monitoring: bool):
        """设置监控状态"""
        self.start_button.setEnabled(not is_monitoring)
        self.stop_button.setEnabled(is_monitoring)
        
        if is_monitoring:
            self.start_button.setText("监测中...")
        else:
            self.start_button.setText("开始监测")
