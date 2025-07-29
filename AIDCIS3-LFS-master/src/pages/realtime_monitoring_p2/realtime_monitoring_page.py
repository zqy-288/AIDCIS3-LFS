"""
实时监控页面 - 高保真度还原原项目RealtimeChart
基于原项目设计，使用高内聚、低耦合的架构重新实现
"""

import logging
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QGroupBox, QTextEdit, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, Signal

# 导入模块化组件
from .components import StatusPanel, ChartPanel, AnomalyPanel, EndoscopePanel
from .controllers import MonitoringController, AutomationController, DataController


class RealtimeMonitoringPage(QWidget):
    """
    实时监控页面主类
    使用模块化架构，高内聚、低耦合设计
    """

    # 信号定义
    hole_selected = Signal(str)  # 孔位选择信号
    monitoring_started = Signal()  # 监控开始信号
    monitoring_stopped = Signal()  # 监控停止信号

    def __init__(self, parent=None):
        super().__init__(parent)

        # 日志设置
        self.logger = logging.getLogger(__name__)

        # 初始化控制器
        self.monitoring_controller = MonitoringController()
        self.automation_controller = AutomationController()
        self.data_controller = DataController()

        # 初始化UI组件
        self.status_panel = None
        self.chart_panel = None
        self.anomaly_panel = None
        self.endoscope_panel = None
        self.log_text_edit = None

        # 设置UI
        self.setup_ui()
        self.setup_controllers()
        self.setup_connections()

        # 初始化状态
        self.setup_initial_state()

    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)

        # 状态监控面板
        self.status_panel = StatusPanel()
        layout.addWidget(self.status_panel)

        # 移除自动化控制日志窗口，匹配重构前的简洁布局
        # 日志信息将通过状态栏或其他方式显示
        self.log_text_edit = None

        # 双面板区域 - 垂直布局（A在上，B在下）
        splitter = QSplitter(Qt.Vertical)

        # 面板A: 管孔直径数据（图表 + 异常监控）
        panel_a_widget = QWidget()
        panel_a_widget.setObjectName("PanelAWidget")
        panel_a_layout = QHBoxLayout(panel_a_widget)
        panel_a_layout.setContentsMargins(8, 8, 8, 8)
        panel_a_layout.setSpacing(10)

        # 图表面板（左侧，占3/4空间）
        self.chart_panel = ChartPanel()
        panel_a_layout.addWidget(self.chart_panel, 3)

        # 异常监控面板（右侧，占1/4空间）
        self.anomaly_panel = AnomalyPanel()
        panel_a_layout.addWidget(self.anomaly_panel, 1)

        splitter.addWidget(panel_a_widget)

        # 面板B: 内窥镜图像
        self.endoscope_panel = EndoscopePanel()
        splitter.addWidget(self.endoscope_panel)

        layout.addWidget(splitter)
        self.main_splitter = splitter

        # 延迟设置分割器比例
        QTimer.singleShot(100, self.adjust_splitter_sizes)

    def setup_controllers(self):
        """设置控制器"""
        # 设置监控控制器的组件引用
        self.monitoring_controller.set_components(
            self.status_panel,
            self.chart_panel,
            self.anomaly_panel,
            self.endoscope_panel
        )

    def setup_connections(self):
        """设置信号连接"""
        # 状态面板信号连接 - 按照重构前的功能
        self.status_panel.start_clicked.connect(self.on_start_monitoring)
        self.status_panel.stop_clicked.connect(self.on_stop_monitoring)
        self.status_panel.clear_clicked.connect(self.on_clear_data)

        # 异常面板信号连接 - 按照重构前的功能
        self.anomaly_panel.next_sample_clicked.connect(self.on_next_sample)

        # 图表面板信号连接
        self.chart_panel.export_requested.connect(self.on_export_chart)
        self.chart_panel.refresh_requested.connect(self.on_refresh_chart)

        # 监控控制器信号连接
        self.monitoring_controller.monitoring_state_changed.connect(self.on_monitoring_state_changed)
        self.monitoring_controller.status_updated.connect(self.on_status_updated)
        self.monitoring_controller.hole_changed.connect(self.hole_selected.emit)

        # 自动化控制器信号连接
        self.automation_controller.automation_log.connect(self.add_log_message)
        self.automation_controller.error_occurred.connect(self.on_automation_error)
        self.automation_controller.csv_file_detected.connect(self.on_csv_file_detected)
        self.automation_controller.process_started.connect(self.on_process_started)
        self.automation_controller.process_stopped.connect(self.on_process_stopped)

        # 数据控制器信号连接
        self.data_controller.data_point_ready.connect(self.on_data_point_ready)
        self.data_controller.data_loaded.connect(self.on_data_loaded)
        self.data_controller.playback_started.connect(self.on_playback_started)
        self.data_controller.playback_stopped.connect(self.on_playback_stopped)
        self.data_controller.error_occurred.connect(self.on_data_error)

    def setup_initial_state(self):
        """设置初始状态"""
        # 设置标准直径和公差
        self.monitoring_controller.set_standard_diameter(17.73, 0.07, 0.05)

        # 添加初始日志消息
        self.add_log_message("🚀 实时监控系统已启动")
        self.add_log_message("📋 等待开始监控...")

    def adjust_splitter_sizes(self):
        """调整分割器大小"""
        try:
            # 设置面板A和面板B的比例为3:2
            total_height = self.main_splitter.height()
            if total_height > 100:
                panel_a_height = int(total_height * 0.6)
                panel_b_height = int(total_height * 0.4)
                self.main_splitter.setSizes([panel_a_height, panel_b_height])
        except Exception as e:
            self.logger.error(f"调整分割器大小失败: {e}")

    def add_log_message(self, message: str):
        """添加日志消息 - 简化版本，匹配重构前布局"""
        try:
            # 日志消息现在只在控制台输出，保持界面简洁
            print(f"[实时监控] {message}")
            self.logger.info(message)
        except Exception as e:
            self.logger.error(f"添加日志消息失败: {e}")

    # === 事件处理方法 ===

    def on_monitoring_state_changed(self, is_monitoring: bool):
        """监控状态变化处理"""
        try:
            if is_monitoring:
                self.add_log_message("▶️ 监控已开始")
                self.monitoring_started.emit()

                # 启动自动化任务
                if self.automation_controller.start_acquisition_program():
                    self.add_log_message("✅ 采集程序启动成功")
                else:
                    self.add_log_message("⚠️ 采集程序启动失败，使用数据播放模式")
                    # 回退到数据播放模式
                    self.start_data_playback_mode()
            else:
                self.add_log_message("⏸️ 监控已停止")
                self.monitoring_stopped.emit()

                # 停止自动化任务
                self.automation_controller.stop_acquisition_program()
                self.automation_controller.stop_remote_launcher()

                # 停止数据播放
                self.data_controller.stop_playback()

        except Exception as e:
            self.logger.error(f"处理监控状态变化失败: {e}")

    def on_status_updated(self, status_type: str, message: str):
        """状态更新处理"""
        try:
            if status_type == "error":
                self.add_log_message(f"❌ {message}")
            elif status_type == "warning":
                self.add_log_message(f"⚠️ {message}")
            elif status_type == "info":
                self.add_log_message(f"ℹ️ {message}")
            else:
                self.add_log_message(message)
        except Exception as e:
            self.logger.error(f"处理状态更新失败: {e}")

    def on_automation_error(self, error_message: str):
        """自动化错误处理"""
        try:
            self.add_log_message(f"❌ 自动化错误: {error_message}")
            QMessageBox.warning(self, "自动化错误", error_message)
        except Exception as e:
            self.logger.error(f"处理自动化错误失败: {e}")

    def on_csv_file_detected(self, file_path: str):
        """CSV文件检测处理"""
        try:
            self.add_log_message(f"📄 检测到CSV文件: {file_path}")

            # 加载并播放CSV数据
            if self.data_controller.load_csv_file(file_path):
                self.add_log_message("✅ CSV文件加载成功")
                self.data_controller.start_playback(50)  # 50ms间隔播放
            else:
                self.add_log_message("❌ CSV文件加载失败")

        except Exception as e:
            self.logger.error(f"处理CSV文件检测失败: {e}")

    def on_process_started(self, process_name: str):
        """进程启动处理"""
        self.add_log_message(f"🚀 进程已启动: {process_name}")

    def on_process_stopped(self, process_name: str):
        """进程停止处理"""
        self.add_log_message(f"⏹️ 进程已停止: {process_name}")

    def on_data_point_ready(self, depth: float, diameter: float):
        """数据点准备处理"""
        try:
            # 将数据点传递给监控控制器
            self.monitoring_controller.add_measurement_point(depth, diameter)
        except Exception as e:
            self.logger.error(f"处理数据点失败: {e}")

    def on_data_loaded(self, file_path: str, point_count: int):
        """数据加载完成处理"""
        self.add_log_message(f"📊 数据加载完成: {point_count} 个数据点")

    def on_playback_started(self):
        """播放开始处理"""
        self.add_log_message("▶️ 数据播放已开始")

    def on_playback_stopped(self):
        """播放停止处理"""
        self.add_log_message("⏸️ 数据播放已停止")

    def on_data_error(self, error_message: str):
        """数据错误处理"""
        self.add_log_message(f"❌ 数据错误: {error_message}")

    def start_data_playback_mode(self):
        """启动数据播放模式"""
        try:
            # 尝试加载默认孔位数据
            default_holes = ["AC002R001", "AC004R001", "BC001R001", "BC003R001"]

            for hole_id in default_holes:
                if self.data_controller.load_hole_data(hole_id):
                    self.add_log_message(f"✅ 加载孔位数据: {hole_id}")
                    self.monitoring_controller.set_current_hole(hole_id)
                    self.data_controller.start_playback(100)  # 100ms间隔播放
                    break
            else:
                self.add_log_message("⚠️ 没有可用的孔位数据")

        except Exception as e:
            self.logger.error(f"启动数据播放模式失败: {e}")

    # === 公共接口方法 ===

    def set_current_hole(self, hole_id: str):
        """设置当前孔位"""
        try:
            self.monitoring_controller.set_current_hole(hole_id)
            self.add_log_message(f"🎯 设置当前孔位: {hole_id}")

            # 如果有对应的数据，加载数据
            if self.data_controller.load_hole_data(hole_id):
                self.add_log_message(f"📊 加载孔位数据: {hole_id}")

        except Exception as e:
            self.logger.error(f"设置当前孔位失败: {e}")

    def start_measurement_for_hole(self, hole_id: str):
        """为指定孔位开始测量"""
        try:
            self.set_current_hole(hole_id)
            self.monitoring_controller.clear_data()
            self.monitoring_controller.start_monitoring()
        except Exception as e:
            self.logger.error(f"为孔位开始测量失败: {e}")

    def get_monitoring_state(self):
        """获取监控状态"""
        return self.monitoring_controller.get_monitoring_state()

    # 新增的信号处理方法 - 按照重构前的功能

    def on_start_monitoring(self):
        """开始监控按钮点击处理"""
        try:
            self.add_log_message("🚀 开始监控...")
            self.monitoring_controller.start_monitoring()
            self.status_panel.set_monitoring_state(True)
        except Exception as e:
            self.logger.error(f"开始监控失败: {e}")

    def on_stop_monitoring(self):
        """停止监控按钮点击处理"""
        try:
            self.add_log_message("⏸️ 停止监控...")
            self.monitoring_controller.stop_monitoring()
            self.status_panel.set_monitoring_state(False)
        except Exception as e:
            self.logger.error(f"停止监控失败: {e}")

    def on_clear_data(self):
        """清除数据按钮点击处理"""
        try:
            self.add_log_message("🗑️ 清除数据...")
            self.monitoring_controller.clear_data()
            self.chart_panel.clear_data()
            self.anomaly_panel.clear_anomalies()
        except Exception as e:
            self.logger.error(f"清除数据失败: {e}")

    def on_next_sample(self):
        """查看下一个样品按钮点击处理"""
        try:
            self.add_log_message("🔄 切换到下一个样品...")
            # 这里可以添加切换样品的逻辑
        except Exception as e:
            self.logger.error(f"切换样品失败: {e}")

    def on_export_chart(self):
        """导出图表按钮点击处理"""
        try:
            self.add_log_message("📊 导出图表...")
            # 这里可以添加导出图表的逻辑
        except Exception as e:
            self.logger.error(f"导出图表失败: {e}")

    def on_refresh_chart(self):
        """刷新图表按钮点击处理"""
        try:
            self.add_log_message("🔄 刷新图表...")
            self.chart_panel.refresh_chart()
        except Exception as e:
            self.logger.error(f"刷新图表失败: {e}")

    def clear_all_data(self):
        """清除所有数据"""
        try:
            self.monitoring_controller.clear_data()
            self.data_controller.clear_data()
            self.add_log_message("🗑️ 所有数据已清除")
        except Exception as e:
            self.logger.error(f"清除所有数据失败: {e}")


# 为了兼容性，创建别名
RealtimeChart = RealtimeMonitoringPage