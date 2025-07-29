"""
右侧操作面板组件 - 独立高内聚模块
负责检测控制、模拟检测、文件操作、视图控制等操作按钮
"""

import logging

from PySide6.QtWidgets import (
    QScrollArea, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QGroupBox
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont


class RightOperationsPanel(QScrollArea):
    """右侧操作面板 - 完全还原old版本 (高内聚组件)"""
    
    # 信号定义
    start_detection = Signal()
    pause_detection = Signal()
    stop_detection = Signal()
    reset_detection = Signal()
    start_simulation = Signal()  # 模拟检测信号
    pause_simulation = Signal()
    stop_simulation = Signal()
    file_operation_requested = Signal(str, dict)
    view_control_requested = Signal(str)  # 视图控制信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 组件状态
        self.detection_running = False
        self.simulation_running = False
        
        # 设置滚动区域属性 (old版本样式)
        self.setWidgetResizable(True)
        self.setMaximumWidth(350)  # old版本精确宽度
        
        # 初始化UI
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """设置UI布局 - 严格按照old版本结构"""
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # 设置字体
        panel_font = QFont()
        panel_font.setPointSize(11)
        
        group_title_font = QFont()
        group_title_font.setPointSize(12)
        group_title_font.setBold(True)
        
        button_font = QFont()
        button_font.setPointSize(11)

        # 1. 检测控制组 (old版本第一组)
        detection_group = self._create_detection_control_group(group_title_font, button_font)
        layout.addWidget(detection_group)

        # 2. 模拟检测组 (恢复模拟检测功能)
        simulation_group = self._create_simulation_group(group_title_font, button_font)
        layout.addWidget(simulation_group)

        # 3. 文件操作组 (old版本第三组)
        file_group = self._create_file_operations_group(group_title_font, button_font)
        layout.addWidget(file_group)

        # 4. 视图控制组 (old版本第四组)
        view_group = self._create_view_control_group(group_title_font, button_font)
        layout.addWidget(view_group)

        # 5. 孔位操作组已删除 (按用户要求)

        # 6. 其他操作组
        other_group = self._create_other_operations_group(group_title_font, button_font)
        layout.addWidget(other_group)

        layout.addStretch()
        self.setWidget(content_widget)

    def _create_detection_control_group(self, group_font, button_font):
        """创建检测控制组 - old版本样式"""
        group = QGroupBox("检测控制")
        group.setFont(group_font)
        layout = QVBoxLayout(group)

        # 检测按钮 (old版本样式和尺寸)
        self.start_detection_btn = QPushButton("开始检测")
        self.start_detection_btn.setMinimumHeight(45)
        self.start_detection_btn.setFont(button_font)
        self.start_detection_btn.setEnabled(False)  # old版本初始状态
        self.start_detection_btn.setStyleSheet("background-color: green; color: white;")

        self.pause_detection_btn = QPushButton("暂停检测")
        self.pause_detection_btn.setMinimumHeight(45)
        self.pause_detection_btn.setFont(button_font)
        self.pause_detection_btn.setEnabled(False)
        self.pause_detection_btn.setStyleSheet("background-color: orange; color: white;")

        self.stop_detection_btn = QPushButton("停止检测")
        self.stop_detection_btn.setMinimumHeight(45)
        self.stop_detection_btn.setFont(button_font)
        self.stop_detection_btn.setEnabled(False)
        self.stop_detection_btn.setStyleSheet("background-color: red; color: white;")

        layout.addWidget(self.start_detection_btn)
        layout.addWidget(self.pause_detection_btn)
        layout.addWidget(self.stop_detection_btn)

        return group

    def _create_simulation_group(self, group_font, button_font):
        """创建模拟检测组"""
        group = QGroupBox("模拟检测")
        group.setFont(group_font)
        layout = QVBoxLayout(group)

        # 模拟检测按钮
        self.start_simulation_btn = QPushButton("开始模拟")
        self.start_simulation_btn.setMinimumHeight(40)
        self.start_simulation_btn.setFont(button_font)
        self.start_simulation_btn.setToolTip("启动模拟检测，按蛇形路径顺序渲染")

        self.pause_simulation_btn = QPushButton("暂停模拟")
        self.pause_simulation_btn.setMinimumHeight(40)
        self.pause_simulation_btn.setFont(button_font)
        self.pause_simulation_btn.setEnabled(False)

        self.stop_simulation_btn = QPushButton("停止模拟")
        self.stop_simulation_btn.setMinimumHeight(40)
        self.stop_simulation_btn.setFont(button_font)
        self.stop_simulation_btn.setEnabled(False)

        layout.addWidget(self.start_simulation_btn)
        layout.addWidget(self.pause_simulation_btn)
        layout.addWidget(self.stop_simulation_btn)

        return group

    def _create_file_operations_group(self, group_font, button_font):
        """创建文件操作组"""
        group = QGroupBox("文件操作")
        group.setFont(group_font)
        layout = QVBoxLayout(group)

        # 文件操作按钮
        self.load_dxf_btn = QPushButton("加载DXF文件")
        self.load_dxf_btn.setMinimumHeight(40)
        self.load_dxf_btn.setFont(button_font)

        self.load_product_btn = QPushButton("选择产品型号")
        self.load_product_btn.setMinimumHeight(40)
        self.load_product_btn.setFont(button_font)

        self.export_data_btn = QPushButton("导出数据")
        self.export_data_btn.setMinimumHeight(40)
        self.export_data_btn.setFont(button_font)

        layout.addWidget(self.load_dxf_btn)
        layout.addWidget(self.load_product_btn)
        layout.addWidget(self.export_data_btn)

        return group

    def _create_view_control_group(self, group_font, button_font):
        """创建视图控制组"""
        group = QGroupBox("视图控制")
        group.setFont(group_font)
        layout = QHBoxLayout(group)

        self.zoom_in_button = QPushButton("放大")
        self.zoom_out_button = QPushButton("缩小")  
        self.reset_zoom_button = QPushButton("重置")

        for btn in [self.zoom_in_button, self.zoom_out_button, self.reset_zoom_button]:
            btn.setMinimumHeight(35)
            btn.setFont(button_font)

        layout.addWidget(self.zoom_in_button)
        layout.addWidget(self.zoom_out_button)
        layout.addWidget(self.reset_zoom_button)

        return group

    def _create_other_operations_group(self, group_font, button_font):
        """创建其他操作组"""
        group = QGroupBox("其他操作")
        group.setFont(group_font)
        layout = QVBoxLayout(group)

        # 报告相关按钮
        self.generate_report_btn = QPushButton("生成报告")
        self.generate_report_btn.setMinimumHeight(40)
        self.generate_report_btn.setFont(button_font)

        self.export_report_btn = QPushButton("导出报告")
        self.export_report_btn.setMinimumHeight(40)
        self.export_report_btn.setFont(button_font)

        layout.addWidget(self.generate_report_btn)
        layout.addWidget(self.export_report_btn)

        return group

    def setup_connections(self):
        """设置信号连接"""
        # 检测控制信号
        self.start_detection_btn.clicked.connect(self.start_detection.emit)
        self.pause_detection_btn.clicked.connect(self.pause_detection.emit)
        self.stop_detection_btn.clicked.connect(self.stop_detection.emit)

        # 模拟控制信号
        self.start_simulation_btn.clicked.connect(self.start_simulation.emit)
        self.pause_simulation_btn.clicked.connect(self.pause_simulation.emit)
        self.stop_simulation_btn.clicked.connect(self.stop_simulation.emit)

        # 文件操作信号
        self.load_dxf_btn.clicked.connect(lambda: self.file_operation_requested.emit("load_dxf", {}))
        self.load_product_btn.clicked.connect(lambda: self.file_operation_requested.emit("load_product", {}))
        self.export_data_btn.clicked.connect(lambda: self.file_operation_requested.emit("export_data", {}))

        # 视图控制信号
        self.zoom_in_button.clicked.connect(lambda: self.view_control_requested.emit("zoom_in"))
        self.zoom_out_button.clicked.connect(lambda: self.view_control_requested.emit("zoom_out"))
        self.reset_zoom_button.clicked.connect(lambda: self.view_control_requested.emit("reset_zoom"))

        # 其他操作信号
        self.generate_report_btn.clicked.connect(lambda: self.file_operation_requested.emit("generate_report", {}))
        self.export_report_btn.clicked.connect(lambda: self.file_operation_requested.emit("export_report", {}))

    def update_detection_state(self, running=False):
        """更新检测状态"""
        self.detection_running = running
        
        # 更新按钮状态 (old版本逻辑)
        self.start_detection_btn.setEnabled(not running)
        self.pause_detection_btn.setEnabled(running)
        self.stop_detection_btn.setEnabled(running)

    def update_simulation_state(self, running=False):
        """更新模拟状态"""
        self.simulation_running = running
        
        # 更新按钮状态
        self.start_simulation_btn.setEnabled(not running)
        self.pause_simulation_btn.setEnabled(running)
        self.stop_simulation_btn.setEnabled(running)

    def enable_detection_controls(self, enabled=True):
        """启用/禁用检测控制按钮"""
        if not self.detection_running:
            self.start_detection_btn.setEnabled(enabled)

    def enable_simulation_controls(self, enabled=True):
        """启用/禁用模拟控制按钮"""
        if not self.simulation_running:
            self.start_simulation_btn.setEnabled(enabled)