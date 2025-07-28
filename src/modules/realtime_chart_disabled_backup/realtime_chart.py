"""
实时图表主类
整合所有组件，提供统一的接口
"""
from typing import Optional, Dict, List, Tuple
from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox
from .components import (
    ChartWidget, DataManager, CSVProcessor, AnomalyDetector,
    EndoscopeManager, ProcessController
)
from .utils.constants import CHART_UPDATE_INTERVAL, STATUS_UPDATE_INTERVAL
from .utils.font_config import setup_safe_chinese_font


class RealtimeChart(QWidget):
    """实时监测图表主窗口"""
    
    # 信号定义
    data_updated = Signal(list, list)  # 深度数据，直径数据
    anomaly_detected = Signal(int, float, float)  # 索引，深度，直径
    process_status_changed = Signal(str)  # 进程状态
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 设置中文字体
        setup_safe_chinese_font()
        
        # 初始化组件
        self._init_components()
        
        # 设置UI
        self._setup_ui()
        
        # 连接信号
        self._connect_signals()
        
        # 初始化定时器
        self._init_timers()
        
        # 状态标志
        self._is_monitoring = False
        self._auto_update_enabled = True
        
    def _init_components(self):
        """初始化所有组件"""
        # 核心组件
        self.chart_widget = ChartWidget()
        self.data_manager = DataManager()
        self.csv_processor = CSVProcessor()
        self.anomaly_detector = AnomalyDetector()
        self.endoscope_manager = EndoscopeManager()
        self.process_controller = ProcessController()
        
        # UI组件
        self.status_label = QLabel("状态: 就绪")
        self.data_count_label = QLabel("数据点: 0")
        self.anomaly_count_label = QLabel("异常点: 0")
        self.process_status_label = QLabel("进程: 未启动")
        
    def _setup_ui(self):
        """设置UI布局"""
        main_layout = QVBoxLayout(self)
        
        # 状态栏
        status_layout = QHBoxLayout()
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.data_count_label)
        status_layout.addWidget(self.anomaly_count_label)
        status_layout.addWidget(self.process_status_label)
        status_layout.addStretch()
        
        status_group = QGroupBox("状态信息")
        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)
        
        # 图表区域
        main_layout.addWidget(self.chart_widget, 1)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("开始监测")
        self.stop_button = QPushButton("停止监测")
        self.clear_button = QPushButton("清除数据")
        self.export_button = QPushButton("导出数据")
        
        self.stop_button.setEnabled(False)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.export_button)
        button_layout.addStretch()
        
        control_group = QGroupBox("控制面板")
        control_group.setLayout(button_layout)
        main_layout.addWidget(control_group)
        
        # 连接按钮信号
        self.start_button.clicked.connect(self.start_monitoring)
        self.stop_button.clicked.connect(self.stop_monitoring)
        self.clear_button.clicked.connect(self.clear_data)
        self.export_button.clicked.connect(self.export_data)
        
    def _connect_signals(self):
        """连接组件信号"""
        # 数据管理器信号
        self.data_manager.data_updated.connect(self._on_data_updated)
        self.data_manager.statistics_updated.connect(self._on_statistics_updated)
        
        # CSV处理器信号
        self.csv_processor.new_data_available.connect(self._on_csv_data_available)
        self.csv_processor.error_occurred.connect(self._on_error)
        
        # 异常检测器信号
        self.anomaly_detector.anomaly_detected.connect(self._on_anomaly_detected)
        self.anomaly_detector.anomalies_updated.connect(self._on_anomalies_updated)
        
        # 内窥镜管理器信号
        self.endoscope_manager.error_occurred.connect(self._on_error)
        
        # 进程控制器信号
        self.process_controller.process_started.connect(self._on_process_started)
        self.process_controller.process_stopped.connect(self._on_process_stopped)
        self.process_controller.process_error.connect(self._on_error)
        self.process_controller.status_changed.connect(self._on_process_status_changed)
        
        # 图表组件信号
        self.chart_widget.zoom_changed.connect(self._on_zoom_changed)
        self.chart_widget.data_point_clicked.connect(self._on_data_point_clicked)
        
    def _init_timers(self):
        """初始化定时器"""
        # 图表更新定时器
        self._chart_update_timer = QTimer()
        self._chart_update_timer.timeout.connect(self._update_chart)
        self._chart_update_timer.setInterval(CHART_UPDATE_INTERVAL)
        
        # 状态更新定时器
        self._status_update_timer = QTimer()
        self._status_update_timer.timeout.connect(self._update_status)
        self._status_update_timer.setInterval(STATUS_UPDATE_INTERVAL)
        self._status_update_timer.start()
        
    def start_monitoring(self):
        """开始监测"""
        self._is_monitoring = True
        
        # 启动CSV监控
        self.csv_processor.start_monitoring()
        
        # 启动图表更新
        if self._auto_update_enabled:
            self._chart_update_timer.start()
            
        # 更新UI
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText("状态: 监测中")
        
    def stop_monitoring(self):
        """停止监测"""
        self._is_monitoring = False
        
        # 停止CSV监控
        self.csv_processor.stop_monitoring()
        
        # 停止图表更新
        self._chart_update_timer.stop()
        
        # 更新UI
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("状态: 已停止")
        
    def clear_data(self):
        """清除所有数据"""
        # 清除数据管理器
        self.data_manager.clear_data()
        
        # 清除图表
        self.chart_widget.clear_chart()
        
        # 清除异常检测器
        self.anomaly_detector.clear_anomalies()
        
        # 更新状态
        self._update_status()
        
    def export_data(self):
        """导出数据"""
        # 获取数据
        data = self.data_manager.export_data()
        
        if data['depth'] and data['diameter']:
            # 添加异常信息
            anomaly_indices = self.anomaly_detector._anomaly_indices
            data['is_anomaly'] = [i in anomaly_indices for i in range(len(data['depth']))]
            
            # 使用CSV处理器导出
            from datetime import datetime
            filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            if self.csv_processor.export_data_to_csv(
                data['depth'], 
                data['diameter'],
                filename,
                {'异常': data['is_anomaly']}
            ):
                self.status_label.setText(f"状态: 数据已导出到 {filename}")
            else:
                self._on_error("导出数据失败")
        else:
            self._on_error("没有数据可导出")
            
    def set_csv_file(self, file_path: str):
        """设置CSV文件路径"""
        self.csv_processor.set_csv_file(file_path)
        
    def set_standard_diameter(self, diameter: float, tolerance: float):
        """设置标准直径和公差"""
        # 设置到图表
        self.chart_widget.set_standard_diameter(diameter, tolerance)
        
        # 设置到异常检测器
        self.anomaly_detector.set_tolerance_parameters(diameter, tolerance)
        
    def set_detection_method(self, method: str):
        """设置异常检测方法"""
        self.anomaly_detector.set_detection_method(method)
        
    def start_process(self, command: str, working_dir: Optional[str] = None):
        """启动外部进程"""
        return self.process_controller.start_process(command, working_dir)
        
    def stop_process(self):
        """停止外部进程"""
        return self.process_controller.stop_process()
        
    def set_endoscope_position(self, position_id: str):
        """设置内窥镜位置"""
        self.endoscope_manager.set_current_position(position_id)
        
    def get_current_data(self) -> Tuple[List[float], List[float]]:
        """获取当前数据"""
        return self.data_manager.get_display_data()
        
    def get_statistics(self) -> Dict[str, any]:
        """获取统计信息"""
        return {
            'data': self.data_manager.get_statistics(),
            'anomaly': self.anomaly_detector.get_anomaly_statistics(),
            'process': self.process_controller.get_status(),
            'endoscope': self.endoscope_manager.get_probe_status()
        }
        
    def _update_chart(self):
        """更新图表显示"""
        # 获取数据
        depth_data, diameter_data = self.data_manager.get_display_data()
        
        if depth_data and diameter_data:
            # 更新图表
            self.chart_widget.update_data(depth_data, diameter_data)
            
            # 检测异常
            anomalies = self.anomaly_detector.detect_anomalies(depth_data, diameter_data)
            
            # 更新异常显示
            self.chart_widget.update_anomaly_points(anomalies)
            
    def _update_status(self):
        """更新状态显示"""
        # 更新数据统计
        buffer_info = self.data_manager.get_buffer_info()
        self.data_count_label.setText(f"数据点: {buffer_info['display_points']}")
        
        # 更新异常统计
        anomaly_stats = self.anomaly_detector.get_anomaly_statistics()
        self.anomaly_count_label.setText(f"异常点: {anomaly_stats['total_count']}")
        
        # 更新进程状态
        process_status = self.process_controller.get_status()
        self.process_status_label.setText(f"进程: {process_status['status']}")
        
    def _on_data_updated(self):
        """数据更新回调"""
        if not self._auto_update_enabled:
            self._update_chart()
            
        self.data_updated.emit(*self.data_manager.get_display_data())
        
    def _on_statistics_updated(self, stats: Dict[str, float]):
        """统计信息更新回调"""
        # 可以在这里添加统计信息的显示逻辑
        pass
        
    def _on_csv_data_available(self, depth_data: List[float], diameter_data: List[float]):
        """CSV数据可用回调"""
        # 批量添加数据
        self.data_manager.add_data_batch(depth_data, diameter_data)
        
    def _on_anomaly_detected(self, index: int, depth: float, diameter: float):
        """异常检测回调"""
        self.anomaly_detected.emit(index, depth, diameter)
        
    def _on_anomalies_updated(self, anomaly_indices: List[int]):
        """异常更新回调"""
        # 更新显示
        self._update_status()
        
    def _on_zoom_changed(self, x_min: float, x_max: float, y_min: float, y_max: float):
        """缩放变化回调"""
        # 可以在这里添加缩放相关的逻辑
        pass
        
    def _on_data_point_clicked(self, depth: float, diameter: float):
        """数据点点击回调"""
        # 查找最近的数据点
        result = self.data_manager.find_nearest_point(depth)
        if result:
            index, actual_depth, actual_diameter = result
            # 可以在这里添加点击数据点的处理逻辑
            
    def _on_process_started(self, pid: int):
        """进程启动回调"""
        self.process_status_changed.emit("running")
        
    def _on_process_stopped(self, pid: int, exit_code: int):
        """进程停止回调"""
        self.process_status_changed.emit("stopped")
        
    def _on_process_status_changed(self, status: str):
        """进程状态变化回调"""
        self._update_status()
        
    def _on_error(self, error_msg: str):
        """错误处理"""
        self.status_label.setText(f"状态: 错误 - {error_msg}")
        
    # 配置方法
    def set_auto_update(self, enabled: bool):
        """设置是否自动更新图表"""
        self._auto_update_enabled = enabled
        if enabled and self._is_monitoring:
            self._chart_update_timer.start()
        else:
            self._chart_update_timer.stop()
            
    def set_update_interval(self, interval: int):
        """设置更新间隔（毫秒）"""
        self._chart_update_timer.setInterval(interval)
        
    def set_max_display_points(self, max_points: int):
        """设置最大显示点数"""
        self.data_manager.set_max_display_points(max_points)