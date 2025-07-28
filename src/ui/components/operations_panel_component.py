"""
Operations panel component for the main window.

This module implements the right operations panel widget extracted from
the original main window, providing detection controls, simulation functions,
and file operations.
"""

import logging
from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox,
    QComboBox, QCheckBox, QTextEdit, QFileDialog, QMessageBox
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from ..view_models.main_view_model import MainViewModel


class DetectionControlGroup(QGroupBox):
    """Detection control group widget."""
    
    # Signals
    start_requested = Signal()
    pause_requested = Signal()
    stop_requested = Signal()
    
    def __init__(self, parent: Optional = None):
        """Initialize detection control group."""
        super().__init__("检测控制", parent)
        self.logger = logging.getLogger(__name__)
        
        # Control buttons
        self.start_btn: Optional[QPushButton] = None
        self.pause_btn: Optional[QPushButton] = None
        self.stop_btn: Optional[QPushButton] = None
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self) -> None:
        """Setup detection control UI."""
        group_title_font = QFont()
        group_title_font.setPointSize(12)
        group_title_font.setBold(True)
        self.setFont(group_title_font)
        
        layout = QVBoxLayout(self)
        
        button_font = QFont()
        button_font.setPointSize(11)
        
        self.start_btn = QPushButton("开始检测")
        self.start_btn.setMinimumHeight(45)
        self.start_btn.setFont(button_font)
        self.start_btn.setEnabled(False)
        
        self.pause_btn = QPushButton("暂停检测")
        self.pause_btn.setMinimumHeight(45)
        self.pause_btn.setFont(button_font)
        self.pause_btn.setEnabled(False)
        
        self.stop_btn = QPushButton("停止检测")
        self.stop_btn.setMinimumHeight(45)
        self.stop_btn.setFont(button_font)
        self.stop_btn.setEnabled(False)
        
        layout.addWidget(self.start_btn)
        layout.addWidget(self.pause_btn)
        layout.addWidget(self.stop_btn)
    
    def _connect_signals(self) -> None:
        """Connect internal signals."""
        if self.start_btn:
            self.start_btn.clicked.connect(self.start_requested.emit)
        if self.pause_btn:
            self.pause_btn.clicked.connect(self.pause_requested.emit)
        if self.stop_btn:
            self.stop_btn.clicked.connect(self.stop_requested.emit)
    
    def update_from_view_model(self, view_model: MainViewModel) -> None:
        """Update controls from view model."""
        try:
            detection_running = view_model.detection_running
            has_data = view_model.hole_collection is not None
            
            # Update button states
            if self.start_btn:
                self.start_btn.setEnabled(has_data and not detection_running)
                self.start_btn.setText("继续检测" if view_model.detection_progress > 0 and not detection_running else "开始检测")
            
            if self.pause_btn:
                self.pause_btn.setEnabled(detection_running)
            
            if self.stop_btn:
                self.stop_btn.setEnabled(detection_running or view_model.detection_progress > 0)
            
        except Exception as e:
            self.logger.error(f"Failed to update detection controls: {e}")


class SimulationControlGroup(QGroupBox):
    """Simulation control group widget."""
    
    # Signals
    start_requested = Signal(dict)  # simulation parameters
    stop_requested = Signal()
    
    def __init__(self, parent: Optional = None):
        """Initialize simulation control group."""
        super().__init__("模拟功能", parent)
        self.logger = logging.getLogger(__name__)
        
        # Control widgets
        self.start_simulation_btn: Optional[QPushButton] = None
        self.stop_simulation_btn: Optional[QPushButton] = None
        self.speed_spinbox: Optional[QSpinBox] = None
        self.auto_mode_checkbox: Optional[QCheckBox] = None
        self.interval_spinbox: Optional[QSpinBox] = None
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self) -> None:
        """Setup simulation control UI."""
        group_title_font = QFont()
        group_title_font.setPointSize(12)
        group_title_font.setBold(True)
        self.setFont(group_title_font)
        
        layout = QVBoxLayout(self)
        
        button_font = QFont()
        button_font.setPointSize(11)
        
        label_font = QFont()
        label_font.setPointSize(10)
        
        # Speed control
        speed_layout = QHBoxLayout()
        speed_label = QLabel("模拟速度:")
        speed_label.setFont(label_font)
        
        self.speed_spinbox = QSpinBox()
        self.speed_spinbox.setRange(1, 10)
        self.speed_spinbox.setValue(3)
        self.speed_spinbox.setSuffix("x")
        
        speed_layout.addWidget(speed_label)
        speed_layout.addWidget(self.speed_spinbox)
        speed_layout.addStretch()
        layout.addLayout(speed_layout)
        
        # Auto mode
        self.auto_mode_checkbox = QCheckBox("自动模式")
        self.auto_mode_checkbox.setFont(label_font)
        layout.addWidget(self.auto_mode_checkbox)
        
        # Interval control
        interval_layout = QHBoxLayout()
        interval_label = QLabel("间隔时间:")
        interval_label.setFont(label_font)
        
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(100, 5000)
        self.interval_spinbox.setValue(500)
        self.interval_spinbox.setSuffix("ms")
        
        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.interval_spinbox)
        interval_layout.addStretch()
        layout.addLayout(interval_layout)
        
        # Control buttons
        self.start_simulation_btn = QPushButton("开始模拟")
        self.start_simulation_btn.setMinimumHeight(40)
        self.start_simulation_btn.setFont(button_font)
        
        self.stop_simulation_btn = QPushButton("停止模拟")
        self.stop_simulation_btn.setMinimumHeight(40)
        self.stop_simulation_btn.setFont(button_font)
        self.stop_simulation_btn.setEnabled(False)
        
        layout.addWidget(self.start_simulation_btn)
        layout.addWidget(self.stop_simulation_btn)
    
    def _connect_signals(self) -> None:
        """Connect internal signals."""
        if self.start_simulation_btn:
            self.start_simulation_btn.clicked.connect(self._on_start_simulation)
        if self.stop_simulation_btn:
            self.stop_simulation_btn.clicked.connect(self.stop_requested.emit)
    
    def _on_start_simulation(self) -> None:
        """Handle start simulation button click."""
        parameters = {
            "speed": self.speed_spinbox.value() if self.speed_spinbox else 3,
            "auto_mode": self.auto_mode_checkbox.isChecked() if self.auto_mode_checkbox else False,
            "interval": self.interval_spinbox.value() if self.interval_spinbox else 500
        }
        self.start_requested.emit(parameters)
    
    def update_simulation_state(self, running: bool) -> None:
        """Update simulation control state."""
        if self.start_simulation_btn:
            self.start_simulation_btn.setEnabled(not running)
        if self.stop_simulation_btn:
            self.stop_simulation_btn.setEnabled(running)


class FileOperationsGroup(QGroupBox):
    """File operations group widget."""
    
    # Signals
    dxf_load_requested = Signal(str)  # file path
    product_load_requested = Signal()
    settings_requested = Signal()
    
    def __init__(self, parent: Optional = None):
        """Initialize file operations group."""
        super().__init__("文件操作", parent)
        self.logger = logging.getLogger(__name__)
        
        # Control buttons
        self.load_dxf_btn: Optional[QPushButton] = None
        self.load_product_btn: Optional[QPushButton] = None
        self.settings_btn: Optional[QPushButton] = None
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self) -> None:
        """Setup file operations UI."""
        group_title_font = QFont()
        group_title_font.setPointSize(12)
        group_title_font.setBold(True)
        self.setFont(group_title_font)
        
        layout = QVBoxLayout(self)
        
        button_font = QFont()
        button_font.setPointSize(11)
        
        self.load_dxf_btn = QPushButton("加载DXF文件")
        self.load_dxf_btn.setMinimumHeight(40)
        self.load_dxf_btn.setFont(button_font)
        
        self.load_product_btn = QPushButton("加载产品型号")
        self.load_product_btn.setMinimumHeight(40)
        self.load_product_btn.setFont(button_font)
        
        self.settings_btn = QPushButton("系统设置")
        self.settings_btn.setMinimumHeight(40)
        self.settings_btn.setFont(button_font)
        
        layout.addWidget(self.load_dxf_btn)
        layout.addWidget(self.load_product_btn)
        layout.addWidget(self.settings_btn)
    
    def _connect_signals(self) -> None:
        """Connect internal signals."""
        if self.load_dxf_btn:
            self.load_dxf_btn.clicked.connect(self._on_load_dxf)
        if self.load_product_btn:
            self.load_product_btn.clicked.connect(self.product_load_requested.emit)
        if self.settings_btn:
            self.settings_btn.clicked.connect(self.settings_requested.emit)
    
    def _on_load_dxf(self) -> None:
        """Handle load DXF button click."""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "选择DXF文件",
            "",
            "DXF文件 (*.dxf);;所有文件 (*)"
        )
        
        if file_path:
            self.dxf_load_requested.emit(file_path)


class ReportExportGroup(QGroupBox):
    """Report export group widget."""
    
    # Signals
    export_requested = Signal(dict)  # export parameters
    
    def __init__(self, parent: Optional = None):
        """Initialize report export group."""
        super().__init__("报告导出", parent)
        self.logger = logging.getLogger(__name__)
        
        # Control widgets
        self.format_combo: Optional[QComboBox] = None
        self.include_images_checkbox: Optional[QCheckBox] = None
        self.export_btn: Optional[QPushButton] = None
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self) -> None:
        """Setup report export UI."""
        group_title_font = QFont()
        group_title_font.setPointSize(12)
        group_title_font.setBold(True)
        self.setFont(group_title_font)
        
        layout = QVBoxLayout(self)
        
        button_font = QFont()
        button_font.setPointSize(11)
        
        label_font = QFont()
        label_font.setPointSize(10)
        
        # Format selection
        format_layout = QHBoxLayout()
        format_label = QLabel("导出格式:")
        format_label.setFont(label_font)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PDF报告", "Excel报告", "Word报告", "数据CSV"])
        self.format_combo.setFont(label_font)
        
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.format_combo)
        layout.addLayout(format_layout)
        
        # Options
        self.include_images_checkbox = QCheckBox("包含图像")
        self.include_images_checkbox.setFont(label_font)
        self.include_images_checkbox.setChecked(True)
        layout.addWidget(self.include_images_checkbox)
        
        # Export button
        self.export_btn = QPushButton("导出报告")
        self.export_btn.setMinimumHeight(40)
        self.export_btn.setFont(button_font)
        self.export_btn.setEnabled(False)
        
        layout.addWidget(self.export_btn)
    
    def _connect_signals(self) -> None:
        """Connect internal signals."""
        if self.export_btn:
            self.export_btn.clicked.connect(self._on_export_report)
    
    def _on_export_report(self) -> None:
        """Handle export report button click."""
        parameters = {
            "format": self.format_combo.currentText() if self.format_combo else "PDF报告",
            "include_images": self.include_images_checkbox.isChecked() if self.include_images_checkbox else True
        }
        self.export_requested.emit(parameters)
    
    def update_from_view_model(self, view_model: MainViewModel) -> None:
        """Update export controls from view model."""
        # Enable export only if there's data
        has_data = view_model.hole_collection is not None
        if self.export_btn:
            self.export_btn.setEnabled(has_data)


class OperationsPanelComponent(QScrollArea):
    """
    Main operations panel component for the right area.
    
    This component provides detection controls, simulation functions,
    file operations, and report export functionality.
    """
    
    # Signals for user interactions
    detection_start_requested = Signal()
    detection_pause_requested = Signal()
    detection_stop_requested = Signal()
    simulation_start_requested = Signal(dict)  # parameters
    simulation_stop_requested = Signal()
    file_load_requested = Signal(str)  # file path
    report_export_requested = Signal(dict)  # parameters
    product_load_requested = Signal()
    settings_requested = Signal()
    
    def __init__(self, parent: Optional = None):
        """
        Initialize the operations panel component.
        
        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # Component groups
        self.detection_control_group: Optional[DetectionControlGroup] = None
        self.simulation_control_group: Optional[SimulationControlGroup] = None
        self.file_operations_group: Optional[FileOperationsGroup] = None
        self.report_export_group: Optional[ReportExportGroup] = None
        
        self._setup_ui()
        self._connect_signals()
        self.logger.debug("Operations panel component initialized")
    
    def _setup_ui(self) -> None:
        """Setup the operations panel UI."""
        self.setWidgetResizable(True)
        self.setMaximumWidth(350)
        
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # Setup panel fonts
        panel_font = QFont()
        panel_font.setPointSize(11)
        
        # Detection control group
        self.detection_control_group = DetectionControlGroup()
        layout.addWidget(self.detection_control_group)
        
        # Simulation control group
        self.simulation_control_group = SimulationControlGroup()
        layout.addWidget(self.simulation_control_group)
        
        # File operations group
        self.file_operations_group = FileOperationsGroup()
        layout.addWidget(self.file_operations_group)
        
        # Report export group
        self.report_export_group = ReportExportGroup()
        layout.addWidget(self.report_export_group)
        
        # Add stretch to push content to top
        layout.addStretch()
        
        self.setWidget(content_widget)
    
    def _connect_signals(self) -> None:
        """Connect component signals."""
        try:
            # Detection control signals
            if self.detection_control_group:
                self.detection_control_group.start_requested.connect(self.detection_start_requested.emit)
                self.detection_control_group.pause_requested.connect(self.detection_pause_requested.emit)
                self.detection_control_group.stop_requested.connect(self.detection_stop_requested.emit)
            
            # Simulation control signals
            if self.simulation_control_group:
                self.simulation_control_group.start_requested.connect(self.simulation_start_requested.emit)
                self.simulation_control_group.stop_requested.connect(self.simulation_stop_requested.emit)
            
            # File operations signals
            if self.file_operations_group:
                self.file_operations_group.dxf_load_requested.connect(self.file_load_requested.emit)
                self.file_operations_group.product_load_requested.connect(self.product_load_requested.emit)
                self.file_operations_group.settings_requested.connect(self.settings_requested.emit)
            
            # Report export signals
            if self.report_export_group:
                self.report_export_group.export_requested.connect(self.report_export_requested.emit)
            
            self.logger.debug("Operations panel signals connected")
            
        except Exception as e:
            self.logger.error(f"Failed to connect operations panel signals: {e}")
    
    def update_from_view_model(self, view_model: MainViewModel) -> None:
        """
        Update operations panel from view model.
        
        Args:
            view_model: Current view model state
        """
        try:
            # Update detection controls
            if self.detection_control_group:
                self.detection_control_group.update_from_view_model(view_model)
            
            # Update simulation controls based on detection state
            if self.simulation_control_group:
                # Disable simulation during detection
                simulation_enabled = not view_model.detection_running
                self.simulation_control_group.setEnabled(simulation_enabled)
            
            # Update report export controls
            if self.report_export_group:
                self.report_export_group.update_from_view_model(view_model)
            
            self.logger.debug("Operations panel updated from view model")
            
        except Exception as e:
            self.logger.error(f"Failed to update operations panel from view model: {e}")
    
    def set_loading_state(self, loading: bool) -> None:
        """
        Set loading state for the operations panel.
        
        Args:
            loading: True to show loading state, False to hide
        """
        try:
            # Disable/enable all controls during loading
            self.setEnabled(not loading)
            
            # Update individual groups if needed
            if loading:
                # Show loading indicators or disable specific controls
                pass
            else:
                # Re-enable controls based on current state
                pass
            
            self.logger.debug(f"Operations panel loading state set to: {loading}")
            
        except Exception as e:
            self.logger.error(f"Failed to set loading state: {e}")
    
    def reset_controls(self) -> None:
        """Reset all controls to initial state."""
        try:
            # Reset detection controls
            if self.detection_control_group:
                for btn in [self.detection_control_group.start_btn,
                           self.detection_control_group.pause_btn,
                           self.detection_control_group.stop_btn]:
                    if btn:
                        btn.setEnabled(False)
            
            # Reset simulation controls
            if self.simulation_control_group:
                self.simulation_control_group.update_simulation_state(False)
            
            # Reset export controls
            if self.report_export_group and self.report_export_group.export_btn:
                self.report_export_group.export_btn.setEnabled(False)
            
            self.logger.debug("Operations panel controls reset")
            
        except Exception as e:
            self.logger.error(f"Failed to reset controls: {e}")