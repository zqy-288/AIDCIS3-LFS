"""
紧凑型状态监控面板组件
专为顶部状态栏设计，水平布局
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QComboBox, QPushButton
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QFont
import logging


class CompactStatusPanel(QWidget):
    """
    紧凑型状态监控面板
    
    功能：
    1. 孔位选择和显示
    2. 通信状态监控
    3. 探头深度显示
    4. 监控控制按钮
    """
    
    # 信号定义
    hole_changed = Signal(str)  # 孔位改变
    monitoring_toggled = Signal(bool)  # 监控开关切换
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 状态变量
        self.is_monitoring = False
        self.current_hole = "ABC001R001"  # 使用实际的孔位编号格式
        self.probe_depth = 0.0
        self.data_rate = 0
        self.connection_status = "未连接"
        
        # 孔位列表（用于下一个样品功能）
        self.hole_list = ["ABC001R001", "ABC001R002", "ABC002R001", "ABC002R002", "ABC003R001", "ABC003R002"]
        self.current_hole_index = 0
        
        # UI初始化
        self._init_ui()
        
        # 定时器用于更新状态
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(1000)  # 1秒更新一次
        
    def _init_ui(self):
        """初始化UI布局 - 两行均等排布，去掉多余边框"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.setSpacing(8)  # 两行间距
        
        # 第一行：孔位和通信状态
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(40)
        
        # 1. 孔位显示（简化样式，去掉边框）
        hole_container = QHBoxLayout()
        hole_label = QLabel("当前孔位:")
        hole_label.setFont(QFont("Arial", 10))
        self.hole_display = QLabel(self.current_hole)
        self.hole_display.setFont(QFont("Arial", 10, QFont.Bold))
        self.hole_display.setStyleSheet("color: #0066cc;")  # 去掉边框和背景
        
        hole_container.addWidget(hole_label)
        hole_container.addWidget(self.hole_display)
        hole_container.addStretch()
        
        # 2. 通信状态
        comm_container = QHBoxLayout()
        comm_label = QLabel("通信状态:")
        comm_label.setFont(QFont("Arial", 10))
        self.comm_status_label = QLabel(self.connection_status)
        self.comm_status_label.setStyleSheet("color: red; font-weight: bold; font-size: 10pt;")
        
        comm_container.addWidget(comm_label)
        comm_container.addWidget(self.comm_status_label)
        comm_container.addStretch()
        
        row1_layout.addLayout(hole_container)
        row1_layout.addLayout(comm_container)
        row1_layout.addStretch()
        
        # 第二行：探头深度、数据频率和按钮
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(40)
        
        # 3. 探头深度
        depth_container = QHBoxLayout()
        depth_label = QLabel("探头深度:")
        depth_label.setFont(QFont("Arial", 10))
        self.depth_display = QLabel(f"{self.probe_depth:.1f} mm")
        self.depth_display.setFont(QFont("Arial", 10))
        
        depth_container.addWidget(depth_label)
        depth_container.addWidget(self.depth_display)
        depth_container.addStretch()
        
        # 4. 数据频率
        rate_container = QHBoxLayout()
        rate_label = QLabel("数据频率:")
        rate_label.setFont(QFont("Arial", 10))
        self.rate_display = QLabel(f"{self.data_rate} Hz")
        self.rate_display.setFont(QFont("Arial", 10))
        
        rate_container.addWidget(rate_label)
        rate_container.addWidget(self.rate_display)
        rate_container.addStretch()
        
        # 5. 监控控制按钮（统一高度）
        self.monitor_btn = QPushButton("开始监控")
        self.monitor_btn.setCheckable(True)
        self.monitor_btn.clicked.connect(self._on_monitor_toggle)
        self.monitor_btn.setFixedSize(80, 30)  # 稍微调高一点
        self.monitor_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 4px 8px;
                font-weight: bold;
                font-size: 9pt;
                border-radius: 4px;
                border: none;
            }
            QPushButton:checked {
                background-color: #f44336;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:checked:hover {
                background-color: #da190b;
            }
        """)
        
        row2_layout.addLayout(depth_container)
        row2_layout.addLayout(rate_container)
        row2_layout.addStretch()
        row2_layout.addWidget(self.monitor_btn)
        
        # 设置两行相同的高度
        row1_widget = QWidget()
        row1_widget.setLayout(row1_layout)
        row1_widget.setMinimumHeight(32)  # 给足够高度显示文字
        
        row2_widget = QWidget()
        row2_widget.setLayout(row2_layout)
        row2_widget.setMinimumHeight(32)  # 相同行高
        
        # 添加到主布局
        main_layout.addWidget(row1_widget)
        main_layout.addWidget(row2_widget)
        
    def _create_separator(self):
        """创建分隔线"""
        separator = QLabel("|")
        separator.setStyleSheet("color: #ccc; font-size: 12pt;")
        separator.setAlignment(Qt.AlignCenter)
        return separator
        
    def _update_hole_display(self):
        """更新孔位显示"""
        self.hole_display.setText(self.current_hole)
        
    def _on_hole_changed(self, hole_id: str):
        """孔位改变处理"""
        self.current_hole = hole_id
        # 更新索引
        if hole_id in self.hole_list:
            self.current_hole_index = self.hole_list.index(hole_id)
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
            self.comm_status_label.setStyleSheet("color: green; font-weight: bold; font-size: 9pt;")
        else:
            self.data_rate = 0
            self.connection_status = "未连接"
            self.comm_status_label.setStyleSheet("color: red; font-weight: bold; font-size: 9pt;")
            
        # 更新显示
        self.depth_display.setText(f"{self.probe_depth:.1f} mm")
        self.rate_display.setText(f"{self.data_rate} Hz")
        self.comm_status_label.setText(self.connection_status)
        
    def set_probe_depth(self, depth: float):
        """设置探头深度"""
        self.probe_depth = depth
        self.depth_display.setText(f"{depth:.1f} mm")
        
    def set_data_rate(self, rate: int):
        """设置数据频率"""
        self.data_rate = rate
        self.rate_display.setText(f"{rate} Hz")
        
    def set_connection_status(self, connected: bool):
        """设置连接状态"""
        if connected:
            self.connection_status = "已连接"
            self.comm_status_label.setStyleSheet("color: green; font-weight: bold; font-size: 9pt;")
        else:
            self.connection_status = "未连接"
            self.comm_status_label.setStyleSheet("color: red; font-weight: bold; font-size: 9pt;")
        self.comm_status_label.setText(self.connection_status)
        
    def select_next_hole(self):
        """选择下一个孔位（用于"查看下一个样品"功能）"""
        self.current_hole_index = (self.current_hole_index + 1) % len(self.hole_list)
        next_hole = self.hole_list[self.current_hole_index]
        
        # 更新当前孔位
        self.current_hole = next_hole
        self._update_hole_display()
        
        # 触发孔位改变事件
        self.hole_changed.emit(next_hole)
        
        self.logger.info(f"🔄 切换到下一个样品: {next_hole}")
        
    def set_current_hole(self, hole_id: str):
        """设置当前正在检测的孔位"""
        self.current_hole = hole_id
        self._update_hole_display()
        self.logger.info(f"设置当前孔位: {hole_id}")