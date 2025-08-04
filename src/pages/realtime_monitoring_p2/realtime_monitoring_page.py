"""
实时监控页面
基于模块化架构，集成完整的实时监控功能
"""

import logging
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QGroupBox, QMessageBox, QPushButton, QLabel
)
from PySide6.QtCore import Signal, Qt, Slot

# 导入本地组件
from .components import (
    ChartPanel, EndoscopePanel
)
from .components.compact_status_panel import CompactStatusPanel
from .components.compact_anomaly_panel import CompactAnomalyPanel
from .controllers import (
    MonitoringController, DataController, AutomationController
)


class RealtimeMonitoringPage(QWidget):
    """
    实时监控页面
    
    功能特性：
    1. 实时直径监控
    2. 异常检测和统计
    3. 数据导入导出
    4. 自动化文件监控
    5. 内窥镜视图集成
    """
    
    # 页面信号
    page_initialized = Signal()
    monitoring_started = Signal()
    monitoring_stopped = Signal()
    hole_selected = Signal(str)
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
        self.logger.info("✅ 实时监控页面初始化完成")
        
    def _init_components(self):
        """初始化组件和控制器"""
        try:
            # 创建UI组件
            self.status_panel = CompactStatusPanel()
            self.chart_panel = ChartPanel()
            self.anomaly_panel = CompactAnomalyPanel()
            self.endoscope_panel = EndoscopePanel()
            
            # 创建控制器
            self.monitoring_controller = MonitoringController()
            self.data_controller = DataController()
            self.automation_controller = AutomationController()
            
            self.logger.info("✅ 所有组件和控制器创建成功")
            
        except Exception as e:
            self.logger.error(f"❌ 组件初始化失败: {e}")
            raise
            
    def _init_ui(self):
        """初始化用户界面 - 按照GitHub原版布局设计"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 1. 顶部状态面板（横向布局）
        self._create_top_status_panel(layout)
        
        # 2. 主要内容区域（垂直分割）
        main_splitter = QSplitter(Qt.Vertical)
        
        # 面板A：图表和异常监控（上半部分）
        panel_a = self._create_panel_a()
        main_splitter.addWidget(panel_a)
        
        # 面板B：内窥镜视图（下半部分）
        panel_b = self.endoscope_panel
        panel_b.setMinimumHeight(300)
        main_splitter.addWidget(panel_b)
        
        # 设置分割比例（面板A占75%，面板B占25%）
        main_splitter.setSizes([750, 250])
        
        layout.addWidget(main_splitter)
        
        self.logger.info("✅ UI布局创建完成")
        
    def _create_top_status_panel(self, parent_layout):
        """创建顶部状态信息面板"""
        # 创建包装容器
        status_container = QWidget()
        status_container.setMinimumHeight(80)  # 给足够的高度
        status_container.setMaximumHeight(100)  # 但不要过高
        container_layout = QHBoxLayout(status_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        # 左侧：紧凑状态面板
        container_layout.addWidget(self.status_panel, 3)
        
        # 右侧：功能按钮组
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setSpacing(10)
        
        # 功能按钮（样式简化）
        self.auto_start_btn = QPushButton("启动自动化")
        self.auto_start_btn.setMaximumHeight(30)
        self.auto_start_btn.clicked.connect(self._toggle_automation)
        
        self.load_data_btn = QPushButton("加载历史数据")
        self.load_data_btn.setMaximumHeight(30)
        self.load_data_btn.clicked.connect(self._load_data)
        
        self.export_data_btn = QPushButton("导出当前数据")
        self.export_data_btn.setMaximumHeight(30)
        self.export_data_btn.clicked.connect(self._export_data)
        
        button_layout.addWidget(self.auto_start_btn)
        button_layout.addWidget(self.load_data_btn)
        button_layout.addWidget(self.export_data_btn)
        
        container_layout.addWidget(button_container, 1)
        
        parent_layout.addWidget(status_container)
        
    def _create_panel_a(self):
        """创建面板A - 图表和异常监控（水平布局）"""
        panel_a = QWidget()
        panel_a_layout = QHBoxLayout(panel_a)
        panel_a_layout.setContentsMargins(5, 5, 5, 5)
        panel_a_layout.setSpacing(10)
        
        # 左侧：图表面板（占80%空间）
        panel_a_layout.addWidget(self.chart_panel, 4)
        
        # 右侧：异常监控面板（占20%空间）
        anomaly_widget = QWidget()
        anomaly_widget.setMaximumWidth(280)  # 减小异常面板宽度
        anomaly_widget.setMinimumWidth(250)   # 设置最小宽度
        anomaly_layout = QVBoxLayout(anomaly_widget)
        
        # 异常面板
        anomaly_layout.addWidget(self.anomaly_panel)
        
        # 添加"查看下一个样品"按钮（GitHub原版特有）
        self.next_sample_btn = QPushButton("查看下一个样品")
        self.next_sample_btn.clicked.connect(self._view_next_sample)
        anomaly_layout.addWidget(self.next_sample_btn)
        
        panel_a_layout.addWidget(anomaly_widget, 1)
        
        return panel_a
        
    def _view_next_sample(self):
        """查看下一个样品 - GitHub原版功能"""
        # 这个功能可以触发切换到下一个孔位
        if hasattr(self.status_panel, 'select_next_hole'):
            self.status_panel.select_next_hole()
        self.logger.info("📍 切换到下一个样品")
        
    def _init_connections(self):
        """初始化信号连接"""
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
        
        self.logger.info("✅ 信号连接完成")
        
    @Slot(str)
    def _on_hole_changed(self, hole_id: str):
        """孔位改变处理"""
        self.logger.info(f"孔位改变: {hole_id}")
        self.monitoring_controller.set_hole_id(hole_id)
        self.endoscope_panel.set_hole_id(hole_id)
        self.hole_selected.emit(hole_id)
        
    @Slot(bool)
    def _on_monitoring_toggled(self, is_monitoring: bool):
        """监控开关处理"""
        if is_monitoring:
            current_hole = self.status_panel.current_hole
            self.monitoring_controller.start_monitoring(current_hole)
            self.chart_panel.start_monitoring()
            self.monitoring_started.emit()
            self.logger.info(f"✅ 开始监控孔位: {current_hole}")
        else:
            self.monitoring_controller.stop_monitoring()
            self.chart_panel.stop_monitoring()
            self._save_current_data()
            self.monitoring_stopped.emit()
            self.logger.info("⏹️ 监控已停止")
            
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
        self.logger.warning(f"⚠️ 检测到异常: 直径={anomaly.get('diameter'):.3f}mm, 偏差={anomaly.get('deviation'):.3f}mm")
        
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
        # 清除旧数据
        self.chart_panel.clear_data()
        self.anomaly_panel.clear_anomalies()
        
        # 加载新数据
        for point in data:
            if 'diameter' in point:
                diameter = float(point['diameter'])
                probe_depth = float(point.get('probe_depth', 0))
                self.chart_panel.add_data_point(diameter, probe_depth)
                
        self.logger.info(f"✅ 已加载 {len(data)} 个数据点")
        QMessageBox.information(self, "加载成功", f"已加载 {len(data)} 个数据点")
        
    @Slot(str)
    def _on_data_saved(self, filepath: str):
        """数据保存完成"""
        self.logger.info(f"✅ 数据已保存: {filepath}")
        
    @Slot(str)
    def _on_file_detected(self, filepath: str):
        """检测到新文件"""
        self.logger.info(f"📄 检测到新文件: {filepath}")
        # 自动加载文件
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
        self.logger.info(f"✅ {message}")
        
    def _toggle_automation(self):
        """切换自动化状态"""
        if self.automation_controller.is_automation_enabled:
            self.automation_controller.stop_automation()
            self.auto_start_btn.setText("启动自动化")
            self.logger.info("⏹️ 自动化已停止")
        else:
            self.automation_controller.start_automation()
            self.auto_start_btn.setText("停止自动化")
            self.logger.info("▶️ 自动化已启动")
            
    def _save_current_data(self):
        """保存当前数据"""
        data = self.monitoring_controller.get_data_buffer()
        if data:
            hole_id = self.monitoring_controller.current_hole_id or "unknown"
            filepath = self.data_controller.save_monitoring_data(data, hole_id)
            if filepath:
                self.logger.info(f"✅ 数据已自动保存: {filepath}")
                
    def _load_data(self):
        """加载数据对话框"""
        from PySide6.QtWidgets import QFileDialog
        
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "选择数据文件",
            str(self.data_controller.data_root),
            "CSV文件 (*.csv);;所有文件 (*.*)"
        )
        
        if filepath:
            self.data_controller.load_csv_data(filepath)
            
    def _export_data(self):
        """导出当前数据"""
        data = self.monitoring_controller.get_data_buffer()
        if not data:
            QMessageBox.warning(self, "无数据", "当前没有数据可导出")
            return
            
        hole_id = self.monitoring_controller.current_hole_id or "export"
        filepath = self.data_controller.save_monitoring_data(data, hole_id)
        
        if filepath:
            self.data_exported.emit(filepath)
            QMessageBox.information(self, "导出成功", f"数据已导出到:\n{filepath}")
            
    def get_status(self) -> dict:
        """获取页面状态（公共接口）"""
        return {
            'monitoring': self.monitoring_controller.get_current_status(),
            'automation': self.automation_controller.get_automation_status(),
            'data': self.data_controller.get_data_summary(),
            'anomalies': self.anomaly_panel.get_statistics()
        }
        
    def cleanup(self):
        """清理资源"""
        if self.monitoring_controller.is_monitoring:
            self.monitoring_controller.stop_monitoring()
        if self.automation_controller.is_automation_enabled:
            self.automation_controller.stop_automation()
        self.logger.info("✅ 页面资源已清理")