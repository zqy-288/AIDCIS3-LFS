"""
实时监控页面 - 还原重构前的UI布局和功能
基于原始realtime_chart.py的双面板设计
"""

import sys
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib
import numpy as np
from pathlib import Path
from collections import deque

# 设置matplotlib支持中文显示
def setup_safe_chinese_font():
    """设置安全的中文字体支持"""
    try:
        matplotlib.rcParams['font.family'] = 'sans-serif'
        matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC', 'SimHei', 'DejaVu Sans']
        matplotlib.rcParams['axes.unicode_minus'] = False
        print("✅ 安全字体配置完成")
    except Exception as e:
        print(f"⚠️ 字体配置失败，使用默认: {e}")
        matplotlib.rcParams['font.family'] = 'DejaVu Sans'

# 初始化安全字体配置
setup_safe_chinese_font()

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QSplitter, QGroupBox, QLineEdit, QMessageBox, QComboBox,
    QTextEdit, QSizePolicy
)
from PySide6.QtCore import Qt, Slot, QTimer, Signal
from PySide6.QtGui import QFont

try:
    from src.modules.endoscope_view import EndoscopeView
except ImportError:
    print("⚠️ EndoscopeView模块导入失败，将使用占位符")
    EndoscopeView = None


class LegacyRealtimeMonitoringPage(QWidget):
    """
    实时监控页面 - 还原重构前的UI布局
    
    布局结构：
    ┌─────────────────────────────────────────────────────────────┐
    │ 状态信息面板: 孔位选择 | 探头深度 | 通信状态 | 标准直径      │
    ├─────────────────────────────────────────────────────────────┤
    │ 面板A (上半部分): matplotlib图表 │ 异常数据列表               │
    │                                  │ [查看下一个样品]按钮       │
    ├─────────────────────────────────────────────────────────────┤
    │ 面板B (下半部分): 内窥镜图像显示                             │
    └─────────────────────────────────────────────────────────────┘
    """
    
    # 信号定义
    hole_selected = Signal(str)  # 孔位选择信号
    start_monitoring = Signal()  # 开始监测信号
    stop_monitoring = Signal()   # 停止监测信号
    clear_data = Signal()        # 清除数据信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 数据属性
        self.current_hole_id = None
        self.is_monitoring = False
        self.data_buffers = {
            'time': deque(maxlen=1000),
            'diameter': deque(maxlen=1000),
            'depth': deque(maxlen=1000)
        }
        
        # 异常数据存储
        self.anomaly_data = []
        
        # 标准参数
        self.standard_diameter = 17.6  # mm
        self.tolerance_upper = 0.5     # mm
        self.tolerance_lower = 0.5     # mm
        
        self.setup_ui()
        self.setup_chart()
        self.setup_connections()
        self.init_hole_mapping()
        
    def setup_ui(self):
        """设置用户界面布局 - 按照重构前的设计"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 1. 状态信息面板
        self.create_status_panel(layout)
        
        # 2. 双面板区域（垂直分割）
        self.create_dual_panels(layout)
        
    def create_status_panel(self, parent_layout):
        """创建状态信息面板"""
        status_group = QGroupBox("状态监控")
        status_group.setObjectName("StatusPanel")
        status_layout = QHBoxLayout(status_group)
        status_layout.setSpacing(20)
        
        # 左侧：孔位选择
        hole_layout = QVBoxLayout()
        hole_label = QLabel("当前孔位:")
        self.hole_selector = QComboBox()
        self.hole_selector.setMinimumWidth(120)
        self.hole_selector.addItems(["未选择", "A1", "A2", "A3", "B1", "B2", "B3"])
        hole_layout.addWidget(hole_label)
        hole_layout.addWidget(self.hole_selector)
        status_layout.addLayout(hole_layout)
        
        # 中间：探头深度显示
        self.depth_label = QLabel("探头深度: -- mm")
        self.depth_label.setMinimumWidth(150)
        status_layout.addWidget(self.depth_label)
        
        # 通信状态显示
        self.comm_status_label = QLabel("通信状态: 等待连接")
        self.comm_status_label.setMinimumWidth(180)
        status_layout.addWidget(self.comm_status_label)
        
        # 标准直径显示
        self.standard_diameter_label = QLabel(f"标准直径: {self.standard_diameter}mm")
        self.standard_diameter_label.setMinimumWidth(150)
        status_layout.addWidget(self.standard_diameter_label)
        
        # 右侧：主控制按钮
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
        """创建双面板区域"""
        # 垂直分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 面板A：图表和异常监控
        panel_a = self.create_panel_a()
        splitter.addWidget(panel_a)
        
        # 面板B：内窥镜图像
        panel_b = self.create_panel_b()
        splitter.addWidget(panel_b)
        
        # 设置分割比例（面板A占60%，面板B占40%）
        splitter.setSizes([600, 400])
        
        parent_layout.addWidget(splitter)
        
    def create_panel_a(self):
        """创建面板A - 图表和异常监控"""
        panel_a = QWidget()
        panel_a_layout = QHBoxLayout(panel_a)
        panel_a_layout.setContentsMargins(5, 5, 5, 5)
        panel_a_layout.setSpacing(10)
        
        # 左侧：matplotlib图表
        chart_widget = self.create_chart_widget()
        panel_a_layout.addWidget(chart_widget, 3)  # 占75%空间
        
        # 右侧：异常数据显示和控制
        right_panel = self.create_anomaly_panel()
        panel_a_layout.addWidget(right_panel, 1)  # 占25%空间
        
        return panel_a
        
    def create_chart_widget(self):
        """创建matplotlib图表组件"""
        chart_widget = QWidget()
        chart_layout = QVBoxLayout(chart_widget)
        chart_layout.setContentsMargins(0, 0, 0, 0)
        
        # 图表标题
        chart_title = QLabel("管孔直径实时监测")
        chart_title.setAlignment(Qt.AlignCenter)
        chart_title.setFont(QFont("Arial", 12, QFont.Bold))
        chart_layout.addWidget(chart_title)
        
        # matplotlib画布
        self.figure = Figure(figsize=(10, 6))
        self.canvas = FigureCanvas(self.figure)
        chart_layout.addWidget(self.canvas)
        
        # 图表专用控制按钮
        chart_controls = QHBoxLayout()
        self.zoom_in_button = QPushButton("放大")
        self.zoom_out_button = QPushButton("缩小")
        self.reset_view_button = QPushButton("重置视图")
        
        chart_controls.addWidget(self.zoom_in_button)
        chart_controls.addWidget(self.zoom_out_button)
        chart_controls.addWidget(self.reset_view_button)
        chart_controls.addStretch()
        
        chart_layout.addLayout(chart_controls)
        
        return chart_widget
        
    def create_anomaly_panel(self):
        """创建异常数据面板"""
        anomaly_widget = QWidget()
        anomaly_widget.setMinimumWidth(300)
        anomaly_widget.setMaximumWidth(350)
        anomaly_layout = QVBoxLayout(anomaly_widget)
        anomaly_layout.setContentsMargins(5, 5, 5, 5)
        
        # 异常监控标题
        anomaly_title = QLabel("异常直径监控")
        anomaly_title.setFont(QFont("Arial", 10, QFont.Bold))
        anomaly_layout.addWidget(anomaly_title)
        
        # 异常数据显示区域
        self.anomaly_text = QTextEdit()
        self.anomaly_text.setReadOnly(True)
        self.anomaly_text.setMaximumHeight(200)
        self.anomaly_text.setPlaceholderText("暂无异常数据...")
        anomaly_layout.addWidget(self.anomaly_text)
        
        # 异常统计信息
        stats_layout = QHBoxLayout()
        self.anomaly_count_label = QLabel("异常点数: 0")
        self.max_deviation_label = QLabel("最大偏差: --")
        stats_layout.addWidget(self.anomaly_count_label)
        stats_layout.addWidget(self.max_deviation_label)
        anomaly_layout.addLayout(stats_layout)
        
        # 标准直径输入区域
        std_layout = QVBoxLayout()
        std_title = QLabel("标准参数设置")
        std_title.setFont(QFont("Arial", 9, QFont.Bold))
        std_layout.addWidget(std_title)
        
        # 标准直径输入
        std_input_layout = QHBoxLayout()
        std_input_layout.addWidget(QLabel("标准直径:"))
        self.std_diameter_input = QLineEdit(str(self.standard_diameter))
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
        self.next_sample_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        anomaly_layout.addWidget(self.next_sample_button)
        
        anomaly_layout.addStretch()
        return anomaly_widget
        
    def create_panel_b(self):
        """创建面板B - 内窥镜图像"""
        if EndoscopeView:
            self.endoscope_view = EndoscopeView()
            self.endoscope_view.setMinimumHeight(300)
            return self.endoscope_view
        else:
            # 占位符
            placeholder = QWidget()
            placeholder_layout = QVBoxLayout(placeholder)
            placeholder_label = QLabel("内窥镜图像显示")
            placeholder_label.setAlignment(Qt.AlignCenter)
            placeholder_label.setFont(QFont("Arial", 14))
            placeholder_label.setStyleSheet("background-color: #f0f0f0; border: 2px dashed #ccc;")
            placeholder_label.setMinimumHeight(300)
            placeholder_layout.addWidget(placeholder_label)
            return placeholder
            
    def setup_chart(self):
        """设置matplotlib图表"""
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        
        # 初始化空图表
        self.ax.set_title('管孔直径实时监测', fontsize=14, fontweight='bold')
        self.ax.set_xlabel('时间 (s)', fontsize=12)
        self.ax.set_ylabel('直径 (mm)', fontsize=12)
        self.ax.grid(True, alpha=0.3)
        
        # 初始化数据线
        self.data_line, = self.ax.plot([], [], 'b-', linewidth=2, label='实测直径')
        
        # 添加标准直径参考线
        self.std_line = self.ax.axhline(y=self.standard_diameter, 
                                       color='green', linestyle='--', 
                                       linewidth=2, label='标准直径')
        
        # 添加公差区域
        self.tolerance_fill = self.ax.fill_between(
            [], [], [], alpha=0.2, color='green', label='公差范围'
        )
        
        self.ax.legend(loc='upper right')
        self.ax.set_xlim(0, 100)
        self.ax.set_ylim(self.standard_diameter - 2, self.standard_diameter + 2)
        
        self.canvas.draw()
        
    def setup_connections(self):
        """设置信号连接"""
        # 按钮连接
        self.start_button.clicked.connect(self.on_start_monitoring)
        self.stop_button.clicked.connect(self.on_stop_monitoring)
        self.clear_button.clicked.connect(self.on_clear_data)
        
        # 图表控制按钮
        self.zoom_in_button.clicked.connect(self.zoom_in_chart)
        self.zoom_out_button.clicked.connect(self.zoom_out_chart)
        self.reset_view_button.clicked.connect(self.reset_chart_view)
        
        # 孔位选择
        self.hole_selector.currentTextChanged.connect(self.on_hole_selected)
        
        # 参数输入
        self.std_diameter_input.textChanged.connect(self.update_standard_diameter)
        self.tolerance_input.textChanged.connect(self.update_tolerance)
        
        # 查看下一个样品按钮
        self.next_sample_button.clicked.connect(self.view_next_sample)
        
    def init_hole_mapping(self):
        """初始化孔位映射"""
        self.hole_mapping = {
            "A1": {"csv_file": "hole_A1.csv", "description": "A区域第1孔"},
            "A2": {"csv_file": "hole_A2.csv", "description": "A区域第2孔"},
            "A3": {"csv_file": "hole_A3.csv", "description": "A区域第3孔"},
            "B1": {"csv_file": "hole_B1.csv", "description": "B区域第1孔"},
            "B2": {"csv_file": "hole_B2.csv", "description": "B区域第2孔"},
            "B3": {"csv_file": "hole_B3.csv", "description": "B区域第3孔"},
        }
        
    # === 事件处理方法 ===
    
    @Slot()
    def on_start_monitoring(self):
        """开始监测"""
        self.is_monitoring = True
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        # 更新状态显示
        self.comm_status_label.setText("通信状态: 正在监测")
        
        # 发射信号
        self.start_monitoring.emit()
        
        print("✅ 开始实时监测")
        
    @Slot()
    def on_stop_monitoring(self):
        """停止监测"""
        self.is_monitoring = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        # 更新状态显示
        self.comm_status_label.setText("通信状态: 监测已停止")
        
        # 发射信号
        self.stop_monitoring.emit()
        
        print("⏸️ 停止实时监测")
        
    @Slot()
    def on_clear_data(self):
        """清除数据"""
        # 清空数据缓冲区
        for buffer in self.data_buffers.values():
            buffer.clear()
            
        # 清空异常数据
        self.anomaly_data.clear()
        self.anomaly_text.clear()
        self.anomaly_count_label.setText("异常点数: 0")
        self.max_deviation_label.setText("最大偏差: --")
        
        # 重置图表
        self.reset_chart_view()
        
        # 发射信号
        self.clear_data.emit()
        
        print("🗑️ 数据已清除")
        
    @Slot(str)
    def on_hole_selected(self, hole_id):
        """孔位选择事件"""
        if hole_id == "未选择":
            self.current_hole_id = None
            return
            
        self.current_hole_id = hole_id
        
        # 更新显示
        if hole_id in self.hole_mapping:
            description = self.hole_mapping[hole_id]["description"]
            print(f"📍 选择孔位: {hole_id} ({description})")
            
        # 发射信号
        self.hole_selected.emit(hole_id)
        
    @Slot()
    def update_standard_diameter(self):
        """更新标准直径"""
        try:
            new_diameter = float(self.std_diameter_input.text())
            self.standard_diameter = new_diameter
            self.standard_diameter_label.setText(f"标准直径: {new_diameter}mm")
            
            # 更新图表中的参考线
            self.std_line.set_ydata([new_diameter, new_diameter])
            self.canvas.draw()
            
        except ValueError:
            pass  # 忽略无效输入
            
    @Slot()
    def update_tolerance(self):
        """更新公差范围"""
        try:
            tolerance_text = self.tolerance_input.text().replace("±", "").replace("+", "")
            tolerance = float(tolerance_text)
            self.tolerance_upper = tolerance
            self.tolerance_lower = tolerance
            
        except ValueError:
            pass  # 忽略无效输入
            
    @Slot()
    def view_next_sample(self):
        """查看下一个样品"""
        current_index = self.hole_selector.currentIndex()
        if current_index < self.hole_selector.count() - 1:
            self.hole_selector.setCurrentIndex(current_index + 1)
        else:
            # 回到第二个选项（跳过"未选择"）
            self.hole_selector.setCurrentIndex(1)
            
    # === 图表控制方法 ===
    
    @Slot()
    def zoom_in_chart(self):
        """放大图表"""
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        
        x_center = (xlim[0] + xlim[1]) / 2
        y_center = (ylim[0] + ylim[1]) / 2
        x_range = (xlim[1] - xlim[0]) * 0.8
        y_range = (ylim[1] - ylim[0]) * 0.8
        
        self.ax.set_xlim(x_center - x_range/2, x_center + x_range/2)
        self.ax.set_ylim(y_center - y_range/2, y_center + y_range/2)
        self.canvas.draw()
        
    @Slot()
    def zoom_out_chart(self):
        """缩小图表"""
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        
        x_center = (xlim[0] + xlim[1]) / 2
        y_center = (ylim[0] + ylim[1]) / 2
        x_range = (xlim[1] - xlim[0]) * 1.25
        y_range = (ylim[1] - ylim[0]) * 1.25
        
        self.ax.set_xlim(x_center - x_range/2, x_center + x_range/2)
        self.ax.set_ylim(y_center - y_range/2, y_center + y_range/2)
        self.canvas.draw()
        
    @Slot()
    def reset_chart_view(self):
        """重置图表视图"""
        self.ax.clear()
        self.setup_chart()
        
    # === 数据更新方法 ===
    
    def add_data_point(self, time_val, diameter, depth=None):
        """添加数据点"""
        # 添加数据到缓冲区
        self.data_buffers['time'].append(time_val)
        self.data_buffers['diameter'].append(diameter)
        if depth is not None:
            self.data_buffers['depth'].append(depth)
            self.depth_label.setText(f"探头深度: {depth:.2f} mm")
            
        # 检查异常
        self.check_anomaly(time_val, diameter)
        
        # 更新图表
        self.update_chart()
        
    def check_anomaly(self, time_val, diameter):
        """检查异常数据"""
        upper_limit = self.standard_diameter + self.tolerance_upper
        lower_limit = self.standard_diameter - self.tolerance_lower
        
        if diameter > upper_limit or diameter < lower_limit:
            deviation = abs(diameter - self.standard_diameter)
            anomaly_info = {
                'time': time_val,
                'diameter': diameter,
                'deviation': deviation,
                'type': 'over' if diameter > upper_limit else 'under'
            }
            
            self.anomaly_data.append(anomaly_info)
            self.update_anomaly_display()
            
    def update_anomaly_display(self):
        """更新异常显示"""
        # 更新异常计数
        self.anomaly_count_label.setText(f"异常点数: {len(self.anomaly_data)}")
        
        # 更新最大偏差
        if self.anomaly_data:
            max_deviation = max(item['deviation'] for item in self.anomaly_data)
            self.max_deviation_label.setText(f"最大偏差: {max_deviation:.3f}mm")
            
            # 更新异常文本显示（只显示最近10条）
            recent_anomalies = self.anomaly_data[-10:]
            anomaly_text = ""
            for anomaly in recent_anomalies:
                anomaly_text += f"时间: {anomaly['time']:.1f}s, "
                anomaly_text += f"直径: {anomaly['diameter']:.3f}mm, "
                anomaly_text += f"偏差: {anomaly['deviation']:.3f}mm\\n"
                
            self.anomaly_text.setPlainText(anomaly_text)
            
    def update_chart(self):
        """更新图表显示"""
        if len(self.data_buffers['time']) > 0:
            times = list(self.data_buffers['time'])
            diameters = list(self.data_buffers['diameter'])
            
            # 更新数据线
            self.data_line.set_data(times, diameters)
            
            # 自动调整X轴范围
            if len(times) > 1:
                self.ax.set_xlim(min(times), max(times))
                
            # 标记异常点
            if self.anomaly_data:
                anomaly_times = [item['time'] for item in self.anomaly_data]
                anomaly_diameters = [item['diameter'] for item in self.anomaly_data]
                
                # 清除之前的异常点标记
                for child in self.ax.get_children():
                    if hasattr(child, 'get_label') and child.get_label() == 'anomaly_points':
                        child.remove()
                        
                # 添加新的异常点标记
                self.ax.scatter(anomaly_times, anomaly_diameters, 
                              color='red', s=50, zorder=5, 
                              label='anomaly_points', alpha=0.8)
                              
            self.canvas.draw()
            
    # === 公共接口方法 ===
    
    def get_current_hole_id(self):
        """获取当前选择的孔位ID"""
        return self.current_hole_id
        
    def get_monitoring_status(self):
        """获取监测状态"""
        return self.is_monitoring
        
    def get_anomaly_count(self):
        """获取异常数据数量"""
        return len(self.anomaly_data)
        
    def export_data(self):
        """导出数据"""
        if not self.data_buffers['time']:
            return None
            
        data = {
            'time': list(self.data_buffers['time']),
            'diameter': list(self.data_buffers['diameter']),
            'depth': list(self.data_buffers['depth']) if self.data_buffers['depth'] else [],
            'anomalies': self.anomaly_data.copy()
        }
        
        return data