"""
实时图表组件 - 高保真度还原原项目设计
基于原项目架构，实现实时监控功能
"""

import os
import sys
import logging
import traceback
import numpy as np
from typing import Optional, Dict, List, Tuple
from collections import deque
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSplitter, 
    QGroupBox, QComboBox, QPushButton, QTextEdit, QLineEdit,
    QMessageBox, QToolButton, QScrollArea
)
from PySide6.QtCore import Signal, Qt, QTimer, QFileSystemWatcher, QThread, QObject
from PySide6.QtGui import QFont

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib

def setup_safe_chinese_font():
    """设置安全的中文字体"""
    try:
        matplotlib.rcParams['font.family'] = 'sans-serif'
        matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC', 'SimHei', 'DejaVu Sans']
        matplotlib.rcParams['axes.unicode_minus'] = False
        print("✅ 安全字体配置完成")
    except Exception as e:
        print(f"⚠️ 字体配置失败，使用默认: {e}")
        matplotlib.rcParams['font.family'] = 'DejaVu Sans'

setup_safe_chinese_font()


class AutomationWorker(QObject):
    """自动化工作线程"""
    file_found = Signal(str)
    data_loaded = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.is_running = False
        self.watched_directory = None
        
    def start_watching(self, directory):
        """开始监控目录"""
        self.watched_directory = directory
        self.is_running = True
        
    def stop_watching(self):
        """停止监控"""
        self.is_running = False
        
    def check_for_files(self):
        """检查文件"""
        if not self.is_running or not self.watched_directory:
            return
            
        try:
            # 实现文件检查逻辑
            pass
        except Exception as e:
            self.error_occurred.emit(str(e))


class RealtimeChart(QWidget):
    """
    实时图表组件 - 核心监控界面
    """
    
    # 信号定义
    hole_selected = Signal(str)
    monitoring_started = Signal()
    monitoring_stopped = Signal()
    data_updated = Signal(float, float)
    anomaly_detected = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_hole_id = None
        self.is_data_loaded = False
        
        # 线程和路径配置
        self.automation_thread = None
        self.automation_worker = None
        
        # 路径配置
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file_dir)))
        self.data_dir = os.path.join(project_root, "data", "diameter_data")
        
        # 数据存储
        self.time_data = deque(maxlen=1000)
        self.diameter_data = deque(maxlen=1000)
        self.depth_data = deque(maxlen=1000)
        self.anomaly_data = []
        
        # 标准参数
        self.standard_diameter = 17.6
        self.tolerance = 0.5
        
        # 文件监控
        self.file_watcher = QFileSystemWatcher()
        self.monitored_files = set()
        
        # 模拟数据
        self.simulation_timer = QTimer()
        self.simulation_timer.timeout.connect(self.generate_simulation_data)
        self.simulation_time = 0
        
        # 初始化UI
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """设置用户界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 1. 状态监控面板
        self.create_status_panel(main_layout)
        
        # 2. 主分割器（垂直分割）
        main_splitter = QSplitter(Qt.Vertical)
        
        # 面板A：图表和异常监控
        panel_a = self.create_panel_a()
        main_splitter.addWidget(panel_a)
        
        # 面板B：内窥镜图像（占位符）
        panel_b = self.create_panel_b()
        main_splitter.addWidget(panel_b)
        
        # 设置分割比例
        main_splitter.setSizes([600, 400])
        
        main_layout.addWidget(main_splitter)
        
    def create_status_panel(self, parent_layout):
        """创建状态监控面板"""
        status_group = QGroupBox("状态监控")
        status_layout = QHBoxLayout(status_group)
        status_layout.setSpacing(20)
        
        # 孔位选择
        hole_layout = QVBoxLayout()
        hole_label = QLabel("当前孔位:")
        self.hole_selector = QComboBox()
        self.hole_selector.setMinimumWidth(120)
        self.hole_selector.addItems(["未选择", "A1", "A2", "A3", "B1", "B2", "B3"])
        hole_layout.addWidget(hole_label)
        hole_layout.addWidget(self.hole_selector)
        status_layout.addLayout(hole_layout)
        
        # 状态显示
        self.depth_label = QLabel("探头深度: -- mm")
        self.comm_status_label = QLabel("通信状态: 等待连接")
        self.standard_diameter_label = QLabel(f"标准直径: {self.standard_diameter}mm")
        
        self.depth_label.setMinimumWidth(150)
        self.comm_status_label.setMinimumWidth(180)
        self.standard_diameter_label.setMinimumWidth(150)
        
        status_layout.addWidget(self.depth_label)
        status_layout.addWidget(self.comm_status_label)
        status_layout.addWidget(self.standard_diameter_label)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        self.start_button = QPushButton("开始监测")
        self.stop_button = QPushButton("停止监测")
        self.clear_button = QPushButton("清除数据")
        
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.clear_button.setEnabled(True)
        
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.clear_button)
        status_layout.addLayout(control_layout)
        
        parent_layout.addWidget(status_group)
        
    def create_panel_a(self):
        """创建面板A - 图表和异常监控"""
        panel_a = QWidget()
        panel_a_layout = QHBoxLayout(panel_a)
        panel_a_layout.setContentsMargins(5, 5, 5, 5)
        panel_a_layout.setSpacing(10)
        
        # 左侧：图表
        self.create_chart_widget()
        panel_a_layout.addWidget(self.canvas, 3)
        
        # 右侧：异常监控
        anomaly_widget = self.create_anomaly_panel()
        panel_a_layout.addWidget(anomaly_widget, 1)
        
        return panel_a
        
    def create_chart_widget(self):
        """创建图表组件"""
        self.figure = Figure(figsize=(10, 6))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        # 初始化图表
        self.setup_chart()
        
    def setup_chart(self):
        """设置图表"""
        self.ax.clear()
        
        # 设置标题和标签
        self.ax.set_title('实时直径监测', fontsize=14, fontweight='bold')
        self.ax.set_xlabel('时间 (秒)', fontsize=12)
        self.ax.set_ylabel('直径 (mm)', fontsize=12)
        
        # 设置网格
        self.ax.grid(True, alpha=0.3, linestyle='--')
        
        # 初始化线条
        self.line, = self.ax.plot([], [], 'b-', linewidth=2, label='直径数据')
        self.anomaly_scatter = self.ax.scatter([], [], c='red', s=50, label='异常点', zorder=5)
        
        # 绘制公差带
        self.update_tolerance_band()
        
        # 设置图例
        self.ax.legend(loc='upper right')
        
        # 设置初始范围
        self.ax.set_xlim(0, 60)
        self.ax.set_ylim(self.standard_diameter - 2, self.standard_diameter + 2)
        
        self.figure.tight_layout()
        
    def update_tolerance_band(self):
        """更新公差带"""
        # 移除旧的公差带
        for patch in self.ax.patches:
            patch.remove()
            
        # 添加新的公差带
        tolerance_band = patches.Rectangle(
            (0, self.standard_diameter - self.tolerance),
            60,
            2 * self.tolerance,
            alpha=0.2,
            facecolor='green',
            edgecolor='none',
            label='公差范围'
        )
        self.ax.add_patch(tolerance_band)
        
        # 添加标准线
        self.ax.axhline(y=self.standard_diameter, color='green', 
                       linestyle='--', alpha=0.8, label='标准直径')
        
    def create_anomaly_panel(self):
        """创建异常监控面板"""
        anomaly_widget = QWidget()
        anomaly_widget.setMinimumWidth(300)
        anomaly_widget.setMaximumWidth(350)
        anomaly_layout = QVBoxLayout(anomaly_widget)
        anomaly_layout.setContentsMargins(5, 5, 5, 5)
        
        # 标题
        anomaly_title = QLabel("异常直径监控")
        anomaly_title.setStyleSheet("font-weight: bold; font-size: 10pt;")
        anomaly_layout.addWidget(anomaly_title)
        
        # 异常数据显示
        self.anomaly_text = QTextEdit()
        self.anomaly_text.setReadOnly(True)
        self.anomaly_text.setMaximumHeight(200)
        self.anomaly_text.setPlaceholderText("暂无异常数据...")
        anomaly_layout.addWidget(self.anomaly_text)
        
        # 统计信息
        stats_layout = QHBoxLayout()
        self.anomaly_count_label = QLabel("异常点数: 0")
        self.max_deviation_label = QLabel("最大偏差: --")
        stats_layout.addWidget(self.anomaly_count_label)
        stats_layout.addWidget(self.max_deviation_label)
        anomaly_layout.addLayout(stats_layout)
        
        # 标准参数设置
        params_group = QGroupBox("标准参数设置")
        params_layout = QVBoxLayout(params_group)
        
        # 标准直径
        std_layout = QHBoxLayout()
        std_layout.addWidget(QLabel("标准直径:"))
        self.std_diameter_input = QLineEdit(str(self.standard_diameter))
        self.std_diameter_input.setMaximumWidth(80)
        std_layout.addWidget(self.std_diameter_input)
        std_layout.addWidget(QLabel("mm"))
        params_layout.addLayout(std_layout)
        
        # 公差
        tolerance_layout = QHBoxLayout()
        tolerance_layout.addWidget(QLabel("公差范围:"))
        self.tolerance_input = QLineEdit(f"±{self.tolerance}")
        self.tolerance_input.setMaximumWidth(80)
        tolerance_layout.addWidget(self.tolerance_input)
        tolerance_layout.addWidget(QLabel("mm"))
        params_layout.addLayout(tolerance_layout)
        
        anomaly_layout.addWidget(params_group)
        
        # 查看下一个样品按钮
        anomaly_layout.addSpacing(20)
        self.next_sample_button = QPushButton("查看下一个样品")
        anomaly_layout.addWidget(self.next_sample_button)
        
        anomaly_layout.addStretch()
        return anomaly_widget
        
    def create_panel_b(self):
        """创建面板B - 内窥镜图像占位符"""
        panel_b = QWidget()
        panel_b_layout = QVBoxLayout(panel_b)
        
        endoscope_label = QLabel("内窥镜图像显示")
        endoscope_label.setAlignment(Qt.AlignCenter)
        endoscope_label.setStyleSheet(
            "background-color: #f0f0f0; "
            "border: 2px dashed #ccc; "
            "font-size: 14pt;"
        )
        endoscope_label.setMinimumHeight(300)
        
        panel_b_layout.addWidget(endoscope_label)
        return panel_b
        
    def setup_connections(self):
        """设置信号连接"""
        # 控制按钮
        self.start_button.clicked.connect(self.start_monitoring)
        self.stop_button.clicked.connect(self.stop_monitoring)
        self.clear_button.clicked.connect(self.clear_data)
        
        # 孔位选择
        self.hole_selector.currentTextChanged.connect(self.on_hole_selected)
        
        # 参数设置
        self.std_diameter_input.editingFinished.connect(self.update_standard_diameter)
        self.tolerance_input.editingFinished.connect(self.update_tolerance)
        
        # 下一个样品
        self.next_sample_button.clicked.connect(self.view_next_sample)
        
    def start_monitoring(self):
        """开始监测"""
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.comm_status_label.setText("通信状态: 正在监测")
        
        # 启动模拟数据生成
        self.simulation_time = 0
        self.simulation_timer.start(100)  # 每100ms生成一个数据点
        
        # 启动更新定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_chart)
        self.update_timer.start(100)
        
        self.monitoring_started.emit()
        print("✅ 开始实时监测")
        
    def stop_monitoring(self):
        """停止监测"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.comm_status_label.setText("通信状态: 监测已停止")
        
        # 停止定时器
        self.simulation_timer.stop()
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
            
        self.monitoring_stopped.emit()
        print("⏸️ 停止实时监测")
        
    def clear_data(self):
        """清除数据"""
        self.time_data.clear()
        self.diameter_data.clear()
        self.depth_data.clear()
        self.anomaly_data.clear()
        
        self.anomaly_text.clear()
        self.anomaly_count_label.setText("异常点数: 0")
        self.max_deviation_label.setText("最大偏差: --")
        
        self.setup_chart()
        self.canvas.draw()
        
        print("🗑️ 数据已清除")
        
    def on_hole_selected(self, hole_id):
        """孔位选择事件"""
        if hole_id != "未选择":
            self.current_hole_id = hole_id
            self.hole_selected.emit(hole_id)
            print(f"📍 选择孔位: {hole_id}")
            
    def update_standard_diameter(self):
        """更新标准直径"""
        try:
            new_diameter = float(self.std_diameter_input.text())
            self.standard_diameter = new_diameter
            self.standard_diameter_label.setText(f"标准直径: {new_diameter}mm")
            self.update_tolerance_band()
            self.canvas.draw()
        except ValueError:
            self.std_diameter_input.setText(str(self.standard_diameter))
            
    def update_tolerance(self):
        """更新公差"""
        try:
            text = self.tolerance_input.text().replace("±", "").replace("+", "")
            new_tolerance = float(text)
            self.tolerance = new_tolerance
            self.tolerance_input.setText(f"±{new_tolerance}")
            self.update_tolerance_band()
            self.canvas.draw()
        except ValueError:
            self.tolerance_input.setText(f"±{self.tolerance}")
            
    def view_next_sample(self):
        """查看下一个样品"""
        current_index = self.hole_selector.currentIndex()
        if current_index < self.hole_selector.count() - 1:
            self.hole_selector.setCurrentIndex(current_index + 1)
        else:
            self.hole_selector.setCurrentIndex(1)  # 跳过"未选择"
            
    def generate_simulation_data(self):
        """生成模拟数据"""
        import random
        import math
        
        self.simulation_time += 0.1
        
        # 生成直径数据
        base_diameter = self.standard_diameter
        noise = random.gauss(0, 0.05)
        periodic = 0.2 * math.sin(self.simulation_time * 0.5)
        
        # 偶尔产生异常
        if random.random() < 0.05:
            diameter = base_diameter + random.uniform(-1.0, 1.0)
        else:
            diameter = base_diameter + noise + periodic
            
        # 生成深度数据
        depth = self.simulation_time * 2.0
        
        # 添加数据点
        self.add_data_point(self.simulation_time, diameter, depth)
        
    def add_data_point(self, time_val, diameter, depth=None):
        """添加数据点"""
        self.time_data.append(time_val)
        self.diameter_data.append(diameter)
        self.depth_data.append(depth if depth is not None else 0)
        
        # 更新深度显示
        if depth is not None:
            self.depth_label.setText(f"探头深度: {depth:.2f} mm")
            
        # 检查异常
        if abs(diameter - self.standard_diameter) > self.tolerance:
            anomaly = {
                'time': time_val,
                'diameter': diameter,
                'deviation': diameter - self.standard_diameter
            }
            self.anomaly_data.append(anomaly)
            self.add_anomaly_display(anomaly)
            self.anomaly_detected.emit(anomaly)
            
        self.data_updated.emit(time_val, diameter)
        
    def add_anomaly_display(self, anomaly):
        """添加异常显示"""
        time_str = f"{anomaly['time']:.2f}s"
        diameter_str = f"{anomaly['diameter']:.3f}mm"
        deviation_str = f"{anomaly['deviation']:+.3f}mm"
        
        color = "red" if abs(anomaly['deviation']) > self.tolerance * 2 else "orange"
        html = f'<span style="color: {color};">时间: {time_str}, 直径: {diameter_str}, 偏差: {deviation_str}</span><br>'
        
        cursor = self.anomaly_text.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertHtml(html)
        
        # 更新统计
        self.anomaly_count_label.setText(f"异常点数: {len(self.anomaly_data)}")
        if self.anomaly_data:
            max_deviation = max(abs(a['deviation']) for a in self.anomaly_data)
            self.max_deviation_label.setText(f"最大偏差: {max_deviation:.3f}mm")
            
    def update_chart(self):
        """更新图表"""
        if not self.time_data:
            return
            
        # 更新数据线
        self.line.set_data(list(self.time_data), list(self.diameter_data))
        
        # 更新异常点
        if self.anomaly_data:
            anomaly_times = [a['time'] for a in self.anomaly_data]
            anomaly_diameters = [a['diameter'] for a in self.anomaly_data]
            self.anomaly_scatter.set_offsets(np.c_[anomaly_times, anomaly_diameters])
            
        # 自动调整x轴
        if self.time_data:
            max_time = max(self.time_data)
            if max_time > 60:
                self.ax.set_xlim(max_time - 60, max_time)
            else:
                self.ax.set_xlim(0, 60)
                
        # 自动调整y轴
        if self.diameter_data:
            min_d = min(self.diameter_data)
            max_d = max(self.diameter_data)
            margin = 0.5
            self.ax.set_ylim(min_d - margin, max_d + margin)
            
        self.canvas.draw()