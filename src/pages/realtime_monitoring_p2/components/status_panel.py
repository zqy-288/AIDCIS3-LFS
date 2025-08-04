"""
状态监控面板组件
显示当前孔位、通信状态、探头深度等信息
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QPushButton, QGroupBox, QLineEdit
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QFont
import logging


class StatusPanel(QWidget):
    """
    状态监控面板
    
    功能：
    1. 孔位选择和显示
    2. 通信状态监控
    3. 探头深度显示
    4. 实时数据频率显示
    """
    
    # 信号定义
    hole_changed = Signal(str)  # 孔位改变
    monitoring_toggled = Signal(bool)  # 监控开关切换
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 状态变量
        self.is_monitoring = False
        self.current_hole = "A-001"
        self.probe_depth = 0.0
        self.data_rate = 0
        self.connection_status = "未连接"
        
        # 孔位列表（用于下一个样品功能）
        self.hole_list = ["A-001", "A-002", "A-003", "B-001", "B-002", "B-003"]
        self.current_hole_index = 0
        
        # UI初始化
        self._init_ui()
        
        # 定时器用于更新状态
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(1000)  # 1秒更新一次
        
    def _init_ui(self):
        """初始化UI布局"""
        layout = QHBoxLayout(self)  # 改为水平布局，更紧凑
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 孔位选择区域
        hole_group = QGroupBox("孔位选择")
        hole_layout = QHBoxLayout(hole_group)
        
        hole_label = QLabel("当前孔位:")
        self.hole_combo = QComboBox()
        self.hole_combo.setMinimumWidth(120)
        self._init_hole_list()
        self.hole_combo.currentTextChanged.connect(self._on_hole_changed)
        
        hole_layout.addWidget(hole_label)
        hole_layout.addWidget(self.hole_combo)
        hole_layout.addStretch()
        
        # 状态信息区域
        status_group = QGroupBox("状态信息")
        status_layout = QVBoxLayout(status_group)
        
        # 通信状态
        comm_layout = QHBoxLayout()
        comm_label = QLabel("通信状态:")
        self.comm_status_label = QLabel(self.connection_status)
        self.comm_status_label.setStyleSheet("color: red; font-weight: bold;")
        comm_layout.addWidget(comm_label)
        comm_layout.addWidget(self.comm_status_label)
        comm_layout.addStretch()
        
        # 探头深度
        depth_layout = QHBoxLayout()
        depth_label = QLabel("探头深度:")
        self.depth_display = QLineEdit()
        self.depth_display.setReadOnly(True)
        self.depth_display.setMaximumWidth(100)
        self.depth_display.setText(f"{self.probe_depth:.2f} mm")
        depth_unit = QLabel("mm")
        depth_layout.addWidget(depth_label)
        depth_layout.addWidget(self.depth_display)
        depth_layout.addWidget(depth_unit)
        depth_layout.addStretch()
        
        # 数据频率
        rate_layout = QHBoxLayout()
        rate_label = QLabel("数据频率:")
        self.rate_display = QLabel(f"{self.data_rate} Hz")
        rate_layout.addWidget(rate_label)
        rate_layout.addWidget(self.rate_display)
        rate_layout.addStretch()
        
        status_layout.addLayout(comm_layout)
        status_layout.addLayout(depth_layout)
        status_layout.addLayout(rate_layout)
        
        # 控制按钮
        control_group = QGroupBox("监控控制")
        control_layout = QHBoxLayout(control_group)
        
        self.monitor_btn = QPushButton("开始监控")
        self.monitor_btn.setCheckable(True)
        self.monitor_btn.clicked.connect(self._on_monitor_toggle)
        self.monitor_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:checked {
                background-color: #f44336;
            }
        """)
        
        control_layout.addWidget(self.monitor_btn)
        control_layout.addStretch()
        
        # 添加到主布局
        layout.addWidget(hole_group)
        layout.addWidget(status_group)
        layout.addWidget(control_group)
        layout.addStretch()
        
    def _init_hole_list(self):
        """初始化孔位列表"""
        # 模拟孔位数据
        holes = [f"{chr(65+i//10)}-{i%10+1:03d}" for i in range(50)]
        self.hole_combo.addItems(holes)
        self.hole_combo.setCurrentText(self.current_hole)
        
    def _on_hole_changed(self, hole_id: str):
        """孔位改变处理"""
        self.current_hole = hole_id
        self.logger.info(f"孔位切换到: {hole_id}")
        self.hole_changed.emit(hole_id)
        
    def _on_monitor_toggle(self):
        """监控开关切换"""
        self.is_monitoring = self.monitor_btn.isChecked()
        if self.is_monitoring:
            self.monitor_btn.setText("停止监控")
            self.logger.info("开始监控")
        else:
            self.monitor_btn.setText("开始监控")
            self.logger.info("停止监控")
        self.monitoring_toggled.emit(self.is_monitoring)
        
    def _update_status(self):
        """更新状态显示"""
        if self.is_monitoring:
            # 模拟状态更新
            import random
            self.probe_depth = random.uniform(0, 1000)
            self.data_rate = random.randint(10, 100)
            self.connection_status = "已连接"
            self.comm_status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.data_rate = 0
            self.connection_status = "未连接"
            self.comm_status_label.setStyleSheet("color: red; font-weight: bold;")
            
        # 更新显示
        self.depth_display.setText(f"{self.probe_depth:.2f}")
        self.rate_display.setText(f"{self.data_rate} Hz")
        self.comm_status_label.setText(self.connection_status)
        
    def set_probe_depth(self, depth: float):
        """设置探头深度"""
        self.probe_depth = depth
        self.depth_display.setText(f"{depth:.2f}")
        
    def set_data_rate(self, rate: int):
        """设置数据频率"""
        self.data_rate = rate
        self.rate_display.setText(f"{rate} Hz")
        
    def set_connection_status(self, connected: bool):
        """设置连接状态"""
        if connected:
            self.connection_status = "已连接"
            self.comm_status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.connection_status = "未连接"
            self.comm_status_label.setStyleSheet("color: red; font-weight: bold;")
        self.comm_status_label.setText(self.connection_status)
        
    def select_next_hole(self):
        """选择下一个孔位（用于"查看下一个样品"功能）"""
        self.current_hole_index = (self.current_hole_index + 1) % len(self.hole_list)
        next_hole = self.hole_list[self.current_hole_index]
        
        # 更新下拉框选择
        self.hole_combo.setCurrentText(next_hole)
        
        # 触发孔位改变事件
        self._on_hole_changed(next_hole)
        
        self.logger.info(f"🔄 切换到下一个样品: {next_hole}")