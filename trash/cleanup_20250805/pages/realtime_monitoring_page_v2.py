"""
实时监控页面 V2 - 模块化架构版本
集成了所有新创建的组件和控制器
"""

import logging
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QGroupBox, QMessageBox, QPushButton
)
from PySide6.QtCore import Signal, Qt, Slot

# 导入新创建的组件
try:
    from .components import (
        StatusPanel, ChartPanel, AnomalyPanel, EndoscopePanel
    )
    from .controllers import (
        MonitoringController, DataController, AutomationController
    )
    HAS_NEW_COMPONENTS = True
except ImportError as e:
    logging.error(f"无法导入新组件: {e}")
    HAS_NEW_COMPONENTS = False


class RealtimeMonitoringPageV2(QWidget):
    """
    实时监控页面 V2版本
    
    特性：
    1. 模块化组件架构
    2. 高内聚低耦合设计
    3. 完整的监控功能
    4. 优雅的错误处理
    """
    
    # 页面信号
    page_initialized = Signal()
    monitoring_started = Signal()
    monitoring_stopped = Signal()
    data_exported = Signal(str)
    
    def __init__(self, shared_components=None, view_model=None, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        self.shared_components = shared_components
        self.view_model = view_model
        
        # 组件引用
        self.status_panel = None
        self.chart_panel = None
        self.anomaly_panel = None
        self.endoscope_panel = None
        
        # 控制器引用
        self.monitoring_controller = None
        self.data_controller = None
        self.automation_controller = None
        
        # 初始化
        self._init_components()
        self._init_ui()
        self._init_connections()
        
        self.page_initialized.emit()
        self.logger.info("实时监控页面V2初始化完成")
        
    def _init_components(self):
        """初始化组件和控制器"""
        if HAS_NEW_COMPONENTS:
            # 创建UI组件
            self.status_panel = StatusPanel()
            self.chart_panel = ChartPanel()
            self.anomaly_panel = AnomalyPanel()
            self.endoscope_panel = EndoscopePanel()
            
            # 创建控制器
            self.monitoring_controller = MonitoringController()
            self.data_controller = DataController()
            self.automation_controller = AutomationController()
            
            self.logger.info("✅ 所有组件和控制器创建成功")
        else:
            self.logger.error("❌ 组件创建失败，使用占位符")
            
    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        if HAS_NEW_COMPONENTS:
            # 创建主分割器（水平）
            main_splitter = QSplitter(Qt.Horizontal)
            
            # 左侧面板（状态和控制）
            left_widget = QWidget()
            left_layout = QVBoxLayout(left_widget)
            left_layout.addWidget(self.status_panel)
            
            # 添加自动化控制按钮
            automation_group = QGroupBox("自动化控制")
            automation_layout = QVBoxLayout(automation_group)
            
            self.auto_start_btn = QPushButton("启动自动化")
            self.auto_start_btn.clicked.connect(self._toggle_automation)
            automation_layout.addWidget(self.auto_start_btn)
            
            left_layout.addWidget(automation_group)
            left_layout.addStretch()
            
            # 中间面板（图表和异常）
            center_splitter = QSplitter(Qt.Vertical)
            center_splitter.addWidget(self.chart_panel)
            center_splitter.addWidget(self.anomaly_panel)
            center_splitter.setStretchFactor(0, 2)  # 图表占更多空间
            center_splitter.setStretchFactor(1, 1)
            
            # 右侧面板（内窥镜视图）
            right_widget = self.endoscope_panel
            
            # 添加到主分割器
            main_splitter.addWidget(left_widget)
            main_splitter.addWidget(center_splitter)
            main_splitter.addWidget(right_widget)
            
            # 设置分割比例
            main_splitter.setStretchFactor(0, 1)  # 左侧
            main_splitter.setStretchFactor(1, 3)  # 中间
            main_splitter.setStretchFactor(2, 2)  # 右侧
            
            layout.addWidget(main_splitter)
        else:
            # 显示错误信息
            error_label = QGroupBox("组件加载失败")
            error_layout = QVBoxLayout(error_label)
            error_layout.addWidget(QPushButton("请检查组件依赖"))
            layout.addWidget(error_label)
            
    def _init_connections(self):
        """初始化信号连接"""
        if not HAS_NEW_COMPONENTS:
            return
            
        # 状态面板信号
        self.status_panel.hole_changed.connect(self._on_hole_changed)
        self.status_panel.monitoring_toggled.connect(self._on_monitoring_toggled)
        
        # 监控控制器信号
        self.monitoring_controller.data_received.connect(self._on_data_received)
        self.monitoring_controller.status_changed.connect(self._on_status_changed)
        
        # 图表面板信号
        self.chart_panel.anomaly_detected.connect(self._on_anomaly_detected)
        
        # 异常面板信号
        self.anomaly_panel.export_requested.connect(self._on_export_anomalies)
        
        # 数据控制器信号
        self.data_controller.data_loaded.connect(self._on_data_loaded)
        self.data_controller.data_saved.connect(self._on_data_saved)
        
        # 自动化控制器信号
        self.automation_controller.file_detected.connect(self._on_file_detected)
        self.automation_controller.task_completed.connect(self._on_task_completed)
        
        self.logger.info("✅ 所有信号连接完成")
        
    @Slot(str)
    def _on_hole_changed(self, hole_id: str):
        """孔位改变处理"""
        self.logger.info(f"孔位改变: {hole_id}")
        self.monitoring_controller.set_hole_id(hole_id)
        self.endoscope_panel.set_hole_id(hole_id)
        
    @Slot(bool)
    def _on_monitoring_toggled(self, is_monitoring: bool):
        """监控开关处理"""
        if is_monitoring:
            current_hole = self.status_panel.current_hole
            self.monitoring_controller.start_monitoring(current_hole)
            self.chart_panel.start_monitoring()
            self.monitoring_started.emit()
        else:
            self.monitoring_controller.stop_monitoring()
            self.chart_panel.stop_monitoring()
            self._save_current_data()
            self.monitoring_stopped.emit()
            
    @Slot(dict)
    def _on_data_received(self, data: dict):
        """接收到新数据"""
        # 更新图表
        diameter = data.get('diameter', 0)
        probe_depth = data.get('probe_depth', 0)
        self.chart_panel.add_data_point(diameter, probe_depth)
        
        # 更新状态
        self.status_panel.set_probe_depth(probe_depth)
        self.status_panel.set_data_rate(self.monitoring_controller.sampling_rate)
        
    @Slot(str)
    def _on_status_changed(self, status: str):
        """状态改变处理"""
        self.logger.info(f"状态更新: {status}")
        
    @Slot(dict)
    def _on_anomaly_detected(self, anomaly: dict):
        """检测到异常"""
        self.anomaly_panel.add_anomaly(anomaly)
        self.logger.warning(f"检测到异常: {anomaly}")
        
    @Slot(list)
    def _on_export_anomalies(self, anomaly_list: list):
        """导出异常数据"""
        export_path = self.data_controller.export_anomaly_data(anomaly_list)
        if export_path:
            self.data_exported.emit(export_path)
            QMessageBox.information(self, "导出成功", f"异常数据已导出到:\n{export_path}")
            
    @Slot(list)
    def _on_data_loaded(self, data: list):
        """数据加载完成"""
        # 加载数据到图表
        self.chart_panel.clear_data()
        for point in data:
            if 'diameter' in point:
                diameter = float(point['diameter'])
                probe_depth = float(point.get('probe_depth', 0))
                self.chart_panel.add_data_point(diameter, probe_depth)
                
        self.logger.info(f"已加载 {len(data)} 个数据点")
        
    @Slot(str)
    def _on_data_saved(self, filepath: str):
        """数据保存完成"""
        self.logger.info(f"数据已保存: {filepath}")
        
    @Slot(str)
    def _on_file_detected(self, filepath: str):
        """检测到新文件"""
        self.logger.info(f"检测到新文件: {filepath}")
        # 可以自动加载文件
        reply = QMessageBox.question(
            self, "新文件检测", 
            f"检测到新文件:\n{filepath}\n是否立即加载？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.data_controller.load_csv_data(filepath)
            
    @Slot(str)
    def _on_task_completed(self, message: str):
        """任务完成"""
        self.logger.info(f"任务完成: {message}")
        
    def _toggle_automation(self):
        """切换自动化状态"""
        if self.automation_controller.is_automation_enabled:
            self.automation_controller.stop_automation()
            self.auto_start_btn.setText("启动自动化")
        else:
            self.automation_controller.start_automation()
            self.auto_start_btn.setText("停止自动化")
            
    def _save_current_data(self):
        """保存当前数据"""
        data = self.monitoring_controller.get_data_buffer()
        if data:
            hole_id = self.monitoring_controller.current_hole_id or "unknown"
            self.data_controller.save_monitoring_data(data, hole_id)
            
    def load_csv_file(self, filepath: str):
        """加载CSV文件（公共接口）"""
        self.data_controller.load_csv_data(filepath)
        
    def export_current_data(self):
        """导出当前数据（公共接口）"""
        self._save_current_data()
        
    def get_status(self) -> dict:
        """获取页面状态（公共接口）"""
        return {
            'monitoring': self.monitoring_controller.get_current_status() if self.monitoring_controller else {},
            'automation': self.automation_controller.get_automation_status() if self.automation_controller else {},
            'data': self.data_controller.get_data_summary() if self.data_controller else {},
            'anomalies': self.anomaly_panel.get_statistics() if self.anomaly_panel else {}
        }
        
    def cleanup(self):
        """清理资源"""
        if self.monitoring_controller and self.monitoring_controller.is_monitoring:
            self.monitoring_controller.stop_monitoring()
        if self.automation_controller and self.automation_controller.is_automation_enabled:
            self.automation_controller.stop_automation()
        self.logger.info("页面资源已清理")