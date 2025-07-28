"""
实时监控页面
基于现有重构后组件，重新组织UI布局以还原重构前的设计
"""

import logging
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSplitter, 
    QGroupBox, QComboBox, QPushButton, QTextEdit, QLineEdit
)
from PySide6.QtCore import Signal, Qt

# 导入现有的重构后组件
try:
    from src.modules.realtime_chart_p2.components.chart_widget import ChartWidget
    from src.modules.realtime_chart_p2.components.data_manager import DataManager
    from src.modules.realtime_chart_p2.components.endoscope_manager import EndoscopeManager
    from src.modules.realtime_chart_p2.components.anomaly_detector import AnomalyDetector
    from src.modules.realtime_chart_p2.components.process_controller import ProcessController
    HAS_COMPONENTS = True
except ImportError as e:
    logging.error(f"无法导入重构后组件: {e}")
    HAS_COMPONENTS = False

# 导入内窥镜视图
try:
    from src.modules.endoscope_view import EndoscopeView
    HAS_ENDOSCOPE = True
except ImportError as e:
    logging.error(f"无法导入内窥镜视图: {e}")
    HAS_ENDOSCOPE = False


class RealtimeMonitoringPage(QWidget):
    """实时监控页面 - 使用现有组件重新组织UI布局"""
    
    # 页面信号
    monitoring_started = Signal()
    monitoring_stopped = Signal()
    hole_selected = Signal(str)
    data_cleared = Signal()
    
    def __init__(self, shared_components=None, view_model=None, parent=None):
        super().__init__(parent)
        
        self.shared_components = shared_components
        self.view_model = view_model
        
        # 初始化现有组件
        self.init_existing_components()
        
        # 设置UI布局
        self.setup_ui()
        self.setup_connections()
        
    def init_existing_components(self):
        """初始化现有的重构后组件"""
        if HAS_COMPONENTS:
            self.chart_widget = ChartWidget()
            self.data_manager = DataManager()
            self.endoscope_manager = EndoscopeManager()
            self.anomaly_detector = AnomalyDetector()
            self.process_controller = ProcessController()
        else:
            self.chart_widget = None
            self.data_manager = None
            self.endoscope_manager = None
            self.anomaly_detector = None
            self.process_controller = None
            
        # 内窥镜视图
        if HAS_ENDOSCOPE:
            self.endoscope_view = EndoscopeView()
        else:
            self.endoscope_view = None
        
    def setup_ui(self):
        """设置用户界面 - 还原重构前的双面板布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 1. 状态信息面板（还原重构前的设计）
        self.create_status_panel(layout)
        
        # 2. 双面板区域（垂直分割：面板A在上，面板B在下）
        self.create_dual_panels(layout)
        
    def create_status_panel(self, parent_layout):
        """创建状态信息面板 - 使用现有组件"""
        status_group = QGroupBox("状态监控")
        status_layout = QHBoxLayout(status_group)
        status_layout.setSpacing(20)
        
        # 左侧：孔位选择（使用现有的内窥镜管理器功能）
        hole_layout = QVBoxLayout()
        hole_label = QLabel("当前孔位:")
        self.hole_selector = QComboBox()
        self.hole_selector.setMinimumWidth(120)
        self.hole_selector.addItems(["未选择", "A1", "A2", "A3", "B1", "B2", "B3"])
        hole_layout.addWidget(hole_label)
        hole_layout.addWidget(self.hole_selector)
        status_layout.addLayout(hole_layout)
        
        # 中间：状态显示（使用现有组件的状态）
        if self.data_manager:
            # 使用数据管理器的状态
            self.depth_label = QLabel("探头深度: -- mm")
            self.comm_status_label = QLabel("通信状态: 等待连接")
            self.standard_diameter_label = QLabel("标准直径: 17.6mm")
        else:
            # 占位符
            self.depth_label = QLabel("探头深度: -- mm")
            self.comm_status_label = QLabel("通信状态: 模块不可用")
            self.standard_diameter_label = QLabel("标准直径: 17.6mm")
            
        self.depth_label.setMinimumWidth(150)
        self.comm_status_label.setMinimumWidth(180)
        self.standard_diameter_label.setMinimumWidth(150)
        
        status_layout.addWidget(self.depth_label)
        status_layout.addWidget(self.comm_status_label)
        status_layout.addWidget(self.standard_diameter_label)
        
        # 右侧：控制按钮（使用现有进程控制器）
        control_layout = QHBoxLayout()
        self.start_button = QPushButton("开始监测")
        self.stop_button = QPushButton("停止监测")
        self.clear_button = QPushButton("清除数据")
        
        # 设置按钮状态
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.clear_button.setEnabled(True)
        
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.clear_button)
        status_layout.addLayout(control_layout)
        
        parent_layout.addWidget(status_group)
        
    def create_dual_panels(self, parent_layout):
        """创建双面板区域 - 使用现有组件"""
        # 垂直分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 面板A：图表和异常监控（使用现有组件）
        panel_a = self.create_panel_a()
        splitter.addWidget(panel_a)
        
        # 面板B：内窥镜图像（使用现有组件）
        panel_b = self.create_panel_b()
        splitter.addWidget(panel_b)
        
        # 设置分割比例（面板A占60%，面板B占40%）
        splitter.setSizes([600, 400])
        
        parent_layout.addWidget(splitter)
        
    def create_panel_a(self):
        """创建面板A - 使用现有图表组件和异常检测器"""
        panel_a = QWidget()
        panel_a_layout = QHBoxLayout(panel_a)
        panel_a_layout.setContentsMargins(5, 5, 5, 5)
        panel_a_layout.setSpacing(10)
        
        # 左侧：使用现有的图表组件
        if self.chart_widget:
            panel_a_layout.addWidget(self.chart_widget, 3)  # 占75%空间
        else:
            # 占位符
            chart_placeholder = QLabel("图表组件不可用")
            chart_placeholder.setAlignment(Qt.AlignCenter)
            chart_placeholder.setStyleSheet("border: 2px dashed #ccc; background: #f5f5f5;")
            panel_a_layout.addWidget(chart_placeholder, 3)
        
        # 右侧：异常数据显示（使用现有异常检测器）
        right_panel = self.create_anomaly_panel()
        panel_a_layout.addWidget(right_panel, 1)  # 占25%空间
        
        return panel_a
        
    def create_anomaly_panel(self):
        """创建异常数据面板 - 使用现有异常检测器"""
        anomaly_widget = QWidget()
        anomaly_widget.setMinimumWidth(300)
        anomaly_widget.setMaximumWidth(350)
        anomaly_layout = QVBoxLayout(anomaly_widget)
        anomaly_layout.setContentsMargins(5, 5, 5, 5)
        
        # 异常监控标题
        anomaly_title = QLabel("异常直径监控")
        anomaly_title.setStyleSheet("font-weight: bold; font-size: 10pt;")
        anomaly_layout.addWidget(anomaly_title)
        
        # 异常数据显示区域
        self.anomaly_text = QTextEdit()
        self.anomaly_text.setReadOnly(True)
        self.anomaly_text.setMaximumHeight(200)
        self.anomaly_text.setPlaceholderText("暂无异常数据...")
        anomaly_layout.addWidget(self.anomaly_text)
        
        # 异常统计信息（使用现有异常检测器的数据）
        stats_layout = QHBoxLayout()
        self.anomaly_count_label = QLabel("异常点数: 0")
        self.max_deviation_label = QLabel("最大偏差: --")
        stats_layout.addWidget(self.anomaly_count_label)
        stats_layout.addWidget(self.max_deviation_label)
        anomaly_layout.addLayout(stats_layout)
        
        # 标准参数设置
        std_layout = QVBoxLayout()
        std_title = QLabel("标准参数设置")
        std_title.setStyleSheet("font-weight: bold; font-size: 9pt;")
        std_layout.addWidget(std_title)
        
        # 标准直径输入
        std_input_layout = QHBoxLayout()
        std_input_layout.addWidget(QLabel("标准直径:"))
        self.std_diameter_input = QLineEdit("17.6")
        self.std_diameter_input.setMaximumWidth(80)
        std_input_layout.addWidget(self.std_diameter_input)
        std_input_layout.addWidget(QLabel("mm"))
        std_layout.addLayout(std_input_layout)
        
        # 公差输入
        tolerance_layout = QHBoxLayout()
        tolerance_layout.addWidget(QLabel("公差范围:"))
        self.tolerance_input = QLineEdit("±0.5")
        self.tolerance_input.setMaximumWidth(80)
        tolerance_layout.addWidget(self.tolerance_input)
        tolerance_layout.addWidget(QLabel("mm"))
        std_layout.addLayout(tolerance_layout)
        
        anomaly_layout.addLayout(std_layout)
        
        # 查看下一个样品按钮
        anomaly_layout.addSpacing(20)
        self.next_sample_button = QPushButton("查看下一个样品")
        anomaly_layout.addWidget(self.next_sample_button)
        
        anomaly_layout.addStretch()
        return anomaly_widget
        
    def create_panel_b(self):
        """创建面板B - 使用现有内窥镜组件"""
        if self.endoscope_view:
            # 使用现有的内窥镜视图
            self.endoscope_view.setMinimumHeight(300)
            return self.endoscope_view
        else:
            # 占位符
            placeholder = QWidget()
            placeholder_layout = QVBoxLayout(placeholder)
            placeholder_label = QLabel("内窥镜图像显示")
            placeholder_label.setAlignment(Qt.AlignCenter)
            placeholder_label.setStyleSheet("background-color: #f0f0f0; border: 2px dashed #ccc; font-size: 14pt;")
            placeholder_label.setMinimumHeight(300)
            placeholder_layout.addWidget(placeholder_label)
            return placeholder
        
    def setup_connections(self):
        """设置信号连接 - 连接现有组件的信号"""
        # 控制按钮连接
        self.start_button.clicked.connect(self.on_start_monitoring)
        self.stop_button.clicked.connect(self.on_stop_monitoring)
        self.clear_button.clicked.connect(self.on_clear_data)
        
        # 孔位选择连接
        self.hole_selector.currentTextChanged.connect(self.on_hole_selected)
        
        # 查看下一个样品按钮
        self.next_sample_button.clicked.connect(self.view_next_sample)
        
        # 参数输入连接
        self.std_diameter_input.textChanged.connect(self.update_standard_diameter)
        self.tolerance_input.textChanged.connect(self.update_tolerance)
        
        # 连接现有组件的信号
        if self.data_manager:
            # 如果数据管理器有相应信号，连接它们
            if hasattr(self.data_manager, 'data_updated'):
                self.data_manager.data_updated.connect(self.on_data_updated)
                
        if self.anomaly_detector:
            # 如果异常检测器有相应信号，连接它们
            if hasattr(self.anomaly_detector, 'anomaly_detected'):
                self.anomaly_detector.anomaly_detected.connect(self.on_anomaly_detected)
                
        if self.process_controller:
            # 如果进程控制器有相应信号，连接它们
            if hasattr(self.process_controller, 'status_changed'):
                self.process_controller.status_changed.connect(self.on_process_status_changed)
                
        if self.endoscope_manager:
            # 如果内窥镜管理器有相应信号，连接它们
            if hasattr(self.endoscope_manager, 'position_changed'):
                self.endoscope_manager.position_changed.connect(self.on_endoscope_position_changed)
            
    # === 事件处理方法 ===
    
    def on_start_monitoring(self):
        """开始监测 - 使用现有进程控制器"""
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        # 更新状态显示
        self.comm_status_label.setText("通信状态: 正在监测")
        
        # 使用现有进程控制器启动
        if self.process_controller and hasattr(self.process_controller, 'start_process'):
            try:
                self.process_controller.start_process()
            except Exception as e:
                logging.error(f"启动监测失败: {e}")
                
        # 发射信号
        self.monitoring_started.emit()
        print("✅ 开始实时监测")
        
    def on_stop_monitoring(self):
        """停止监测 - 使用现有进程控制器"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        # 更新状态显示
        self.comm_status_label.setText("通信状态: 监测已停止")
        
        # 使用现有进程控制器停止
        if self.process_controller and hasattr(self.process_controller, 'stop_process'):
            try:
                self.process_controller.stop_process()
            except Exception as e:
                logging.error(f"停止监测失败: {e}")
                
        # 发射信号
        self.monitoring_stopped.emit()
        print("⏸️ 停止实时监测")
        
    def on_clear_data(self):
        """清除数据 - 使用现有数据管理器"""
        # 使用现有数据管理器清除数据
        if self.data_manager and hasattr(self.data_manager, 'clear_data'):
            try:
                self.data_manager.clear_data()
            except Exception as e:
                logging.error(f"清除数据失败: {e}")
                
        # 清除UI显示
        self.anomaly_text.clear()
        self.anomaly_count_label.setText("异常点数: 0")
        self.max_deviation_label.setText("最大偏差: --")
        
        # 发射信号
        self.data_cleared.emit()
        print("🗑️ 数据已清除")
        
    def on_hole_selected(self, hole_id):
        """孔位选择事件 - 使用现有内窥镜管理器"""
        if hole_id == "未选择":
            hole_id = None
            
        # 使用现有内窥镜管理器设置位置
        if self.endoscope_manager and hasattr(self.endoscope_manager, 'set_current_position'):
            try:
                if hole_id:
                    self.endoscope_manager.set_current_position(hole_id)
            except Exception as e:
                logging.error(f"设置孔位失败: {e}")
                
        # 发射信号
        if hole_id:
            self.hole_selected.emit(hole_id)
            print(f"📍 选择孔位: {hole_id}")
            
    def view_next_sample(self):
        """查看下一个样品"""
        current_index = self.hole_selector.currentIndex()
        if current_index < self.hole_selector.count() - 1:
            self.hole_selector.setCurrentIndex(current_index + 1)
        else:
            # 回到第二个选项（跳过"未选择"）
            self.hole_selector.setCurrentIndex(1)
            
    def update_standard_diameter(self):
        """更新标准直径"""
        try:
            new_diameter = float(self.std_diameter_input.text())
            self.standard_diameter_label.setText(f"标准直径: {new_diameter}mm")
            
            # 如果异常检测器支持，更新其标准值
            if self.anomaly_detector and hasattr(self.anomaly_detector, 'set_standard_diameter'):
                self.anomaly_detector.set_standard_diameter(new_diameter)
                
        except ValueError:
            pass  # 忽略无效输入
            
    def update_tolerance(self):
        """更新公差范围"""
        try:
            tolerance_text = self.tolerance_input.text().replace("±", "").replace("+", "")
            tolerance = float(tolerance_text)
            
            # 如果异常检测器支持，更新其公差值
            if self.anomaly_detector and hasattr(self.anomaly_detector, 'set_tolerance'):
                self.anomaly_detector.set_tolerance(tolerance)
                
        except ValueError:
            pass  # 忽略无效输入
            
    # === 现有组件信号响应方法 ===
    
    def on_data_updated(self, *args):
        """数据更新信号响应"""
        # 更新深度显示等
        pass
        
    def on_anomaly_detected(self, *args):
        """异常检测信号响应"""
        # 更新异常显示
        if self.anomaly_detector:
            try:
                count = len(getattr(self.anomaly_detector, 'anomalies', []))
                self.anomaly_count_label.setText(f"异常点数: {count}")
            except:
                pass
                
    def on_process_status_changed(self, status):
        """进程状态变化响应"""
        self.comm_status_label.setText(f"通信状态: {status}")
        
    def on_endoscope_position_changed(self, position):
        """内窥镜位置变化响应"""
        print(f"内窥镜位置变化: {position}")
        
    # === 公共接口方法 ===
    
    def get_current_hole_id(self):
        """获取当前孔位ID"""
        current_text = self.hole_selector.currentText()
        return None if current_text == "未选择" else current_text
        
    def get_monitoring_status(self):
        """获取监测状态"""
        return not self.start_button.isEnabled()
        
    def add_data_point(self, time_val, diameter, depth=None):
        """添加数据点"""
        # 使用现有数据管理器添加数据
        if self.data_manager and hasattr(self.data_manager, 'add_data'):
            try:
                self.data_manager.add_data(time_val, diameter, depth)
            except Exception as e:
                logging.error(f"添加数据点失败: {e}")
                
        # 更新深度显示
        if depth is not None:
            self.depth_label.setText(f"探头深度: {depth:.2f} mm")
            
    def get_anomaly_count(self):
        """获取异常数量"""
        if self.anomaly_detector and hasattr(self.anomaly_detector, 'anomalies'):
            try:
                return len(self.anomaly_detector.anomalies)
            except:
                pass
        return 0
        
    def export_data(self):
        """导出数据"""
        if self.data_manager and hasattr(self.data_manager, 'export_data'):
            try:
                return self.data_manager.export_data()
            except Exception as e:
                logging.error(f"导出数据失败: {e}")
        return None