"""
实时图表面板组件
使用matplotlib显示直径数据和异常点
"""

import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
from collections import deque

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QLineEdit, QComboBox, QGroupBox, QSlider
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer
import logging

# 设置matplotlib支持中文显示
def setup_chinese_font():
    """设置中文字体支持"""
    try:
        matplotlib.rcParams['font.family'] = 'sans-serif'
        matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC', 'SimHei', 'DejaVu Sans']
        matplotlib.rcParams['axes.unicode_minus'] = False
    except Exception as e:
        print(f"字体配置失败: {e}")

setup_chinese_font()


class ChartPanel(QWidget):
    """
    实时图表面板
    
    功能：
    1. 实时显示直径数据曲线
    2. 标记异常数据点
    3. 显示标准直径和容差带
    4. 支持数据缩放和平移
    """
    
    # 信号定义
    anomaly_detected = Signal(dict)  # 检测到异常
    data_updated = Signal(list)  # 数据更新
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 数据存储
        self.data_buffer = deque(maxlen=1000)  # 最多保存1000个点
        self.anomaly_points = []  # 异常点列表
        
        # 图表参数
        self.standard_diameter = 376.0  # 标准直径
        self.tolerance = 0.15  # 容差（mm）
        self.display_points = 100  # 显示的数据点数
        
        # 初始化UI
        self._init_ui()
        
        # 初始化图表
        self._init_chart()
        
        # 定时器用于模拟数据更新
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._generate_mock_data)
        
    def _init_ui(self):
        """初始化UI布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 图表控制区域
        control_layout = QHBoxLayout()
        
        # 标准直径设置
        std_label = QLabel("标准直径:")
        self.std_diameter_edit = QLineEdit(str(self.standard_diameter))
        self.std_diameter_edit.setMaximumWidth(80)
        self.std_diameter_edit.editingFinished.connect(self._update_standard_diameter)
        
        # 容差设置
        tol_label = QLabel("容差(±):")
        self.tolerance_edit = QLineEdit(str(self.tolerance))
        self.tolerance_edit.setMaximumWidth(60)
        self.tolerance_edit.editingFinished.connect(self._update_tolerance)
        
        # 显示点数设置
        points_label = QLabel("显示点数:")
        self.points_slider = QSlider(Qt.Horizontal)
        self.points_slider.setRange(50, 500)
        self.points_slider.setValue(self.display_points)
        self.points_slider.setMaximumWidth(150)
        self.points_slider.valueChanged.connect(self._update_display_points)
        self.points_value_label = QLabel(str(self.display_points))
        
        # 清除按钮
        self.clear_btn = QPushButton("清除数据")
        self.clear_btn.clicked.connect(self.clear_data)
        
        control_layout.addWidget(std_label)
        control_layout.addWidget(self.std_diameter_edit)
        control_layout.addWidget(QLabel("mm"))
        control_layout.addSpacing(20)
        control_layout.addWidget(tol_label)
        control_layout.addWidget(self.tolerance_edit)
        control_layout.addWidget(QLabel("mm"))
        control_layout.addSpacing(20)
        control_layout.addWidget(points_label)
        control_layout.addWidget(self.points_slider)
        control_layout.addWidget(self.points_value_label)
        control_layout.addStretch()
        control_layout.addWidget(self.clear_btn)
        
        # 创建matplotlib画布
        self.figure = Figure(figsize=(10, 6))
        self.canvas = FigureCanvas(self.figure)
        
        # 添加到主布局
        layout.addLayout(control_layout)
        layout.addWidget(self.canvas)
        
    def _init_chart(self):
        """初始化图表"""
        self.ax = self.figure.add_subplot(111)
        
        # 设置标题和标签
        self.ax.set_title('管孔直径实时监测', fontsize=14, fontweight='bold')
        self.ax.set_xlabel('采样点', fontsize=12)
        self.ax.set_ylabel('直径 (mm)', fontsize=12)
        
        # 初始化曲线
        self.line, = self.ax.plot([], [], 'b-', linewidth=2, label='实测直径')
        self.anomaly_scatter = self.ax.scatter([], [], c='red', s=100, marker='o', label='异常点', zorder=5)
        
        # 绘制标准直径线和容差带
        self._draw_tolerance_band()
        
        # 设置图例
        self.ax.legend(loc='upper right')
        
        # 设置网格
        self.ax.grid(True, alpha=0.3)
        
        # 设置初始范围
        self.ax.set_xlim(0, self.display_points)
        self.ax.set_ylim(self.standard_diameter - 5, self.standard_diameter + 5)
        
        # 紧凑布局
        self.figure.tight_layout()
        
    def _draw_tolerance_band(self):
        """绘制容差带"""
        # 清除旧的容差带
        for patch in self.ax.patches:
            patch.remove()
            
        # 绘制新的容差带
        upper_limit = self.standard_diameter + self.tolerance
        lower_limit = self.standard_diameter - self.tolerance
        
        # 添加容差带（浅绿色区域）
        tolerance_band = patches.Rectangle(
            (0, lower_limit), 
            self.display_points, 
            2 * self.tolerance,
            alpha=0.2, 
            facecolor='green',
            label='容差带'
        )
        self.ax.add_patch(tolerance_band)
        
        # 标准直径线（绿色虚线）
        self.ax.axhline(y=self.standard_diameter, color='green', linestyle='--', linewidth=2, label='标准直径')
        
        # 容差上下限线（红色虚线）
        self.ax.axhline(y=upper_limit, color='red', linestyle=':', linewidth=1.5, alpha=0.7)
        self.ax.axhline(y=lower_limit, color='red', linestyle=':', linewidth=1.5, alpha=0.7)
        
    def add_data_point(self, diameter: float, probe_depth: float = None):
        """添加新的数据点"""
        # 添加到数据缓冲区
        timestamp = len(self.data_buffer)
        data_point = {
            'timestamp': timestamp,
            'diameter': diameter,
            'probe_depth': probe_depth
        }
        self.data_buffer.append(data_point)
        
        # 检测异常
        if abs(diameter - self.standard_diameter) > self.tolerance:
            anomaly = {
                'timestamp': timestamp,
                'diameter': diameter,
                'deviation': diameter - self.standard_diameter,
                'probe_depth': probe_depth
            }
            self.anomaly_points.append(anomaly)
            self.anomaly_detected.emit(anomaly)
        
        # 更新图表
        self._update_chart()
        
        # 发出数据更新信号
        self.data_updated.emit(list(self.data_buffer))
        
    def _update_chart(self):
        """更新图表显示"""
        if not self.data_buffer:
            return
            
        # 获取要显示的数据
        display_data = list(self.data_buffer)[-self.display_points:]
        
        # 提取x和y数据
        x_data = [d['timestamp'] for d in display_data]
        y_data = [d['diameter'] for d in display_data]
        
        # 更新主曲线
        self.line.set_data(x_data, y_data)
        
        # 更新异常点
        anomaly_x = []
        anomaly_y = []
        for anomaly in self.anomaly_points:
            if anomaly['timestamp'] in x_data:
                anomaly_x.append(anomaly['timestamp'])
                anomaly_y.append(anomaly['diameter'])
        
        if anomaly_x:
            self.anomaly_scatter.set_offsets(np.c_[anomaly_x, anomaly_y])
        else:
            self.anomaly_scatter.set_offsets(np.empty((0, 2)))
        
        # 调整x轴范围
        if x_data:
            self.ax.set_xlim(x_data[0], x_data[-1] + 1)
            
        # 调整y轴范围（自动缩放）
        if y_data:
            y_min = min(y_data + [self.standard_diameter - self.tolerance])
            y_max = max(y_data + [self.standard_diameter + self.tolerance])
            margin = (y_max - y_min) * 0.1
            self.ax.set_ylim(y_min - margin, y_max + margin)
        
        # 刷新画布
        self.canvas.draw()
        
    def _generate_mock_data(self):
        """生成模拟数据（用于测试）"""
        # 生成围绕标准直径的随机数据
        noise = np.random.normal(0, 0.1)
        # 偶尔产生异常值
        if np.random.random() < 0.05:  # 5%概率产生异常
            noise = np.random.choice([-1, 1]) * (self.tolerance + np.random.uniform(0.1, 0.5))
        
        diameter = self.standard_diameter + noise
        probe_depth = len(self.data_buffer) * 0.1  # 模拟探头深度
        
        self.add_data_point(diameter, probe_depth)
        
    def start_monitoring(self):
        """开始监控"""
        self.update_timer.start(100)  # 100ms更新一次
        self.logger.info("图表监控已启动")
        
    def stop_monitoring(self):
        """停止监控"""
        self.update_timer.stop()
        self.logger.info("图表监控已停止")
        
    def clear_data(self):
        """清除所有数据"""
        self.data_buffer.clear()
        self.anomaly_points.clear()
        self.line.set_data([], [])
        self.anomaly_scatter.set_offsets(np.empty((0, 2)))
        self.canvas.draw()
        self.logger.info("图表数据已清除")
        
    def _update_standard_diameter(self):
        """更新标准直径"""
        try:
            self.standard_diameter = float(self.std_diameter_edit.text())
            self._draw_tolerance_band()
            self._update_chart()
            self.logger.info(f"标准直径更新为: {self.standard_diameter} mm")
        except ValueError:
            self.std_diameter_edit.setText(str(self.standard_diameter))
            
    def _update_tolerance(self):
        """更新容差"""
        try:
            self.tolerance = float(self.tolerance_edit.text())
            self._draw_tolerance_band()
            self._update_chart()
            self.logger.info(f"容差更新为: ±{self.tolerance} mm")
        except ValueError:
            self.tolerance_edit.setText(str(self.tolerance))
            
    def _update_display_points(self, value):
        """更新显示点数"""
        self.display_points = value
        self.points_value_label.setText(str(value))
        self._draw_tolerance_band()
        self._update_chart()
        
    def load_csv_data(self, csv_data):
        """加载CSV数据"""
        self.clear_data()
        for row in csv_data:
            if 'diameter' in row:
                diameter = float(row['diameter'])
                probe_depth = float(row.get('probe_depth', 0))
                self.add_data_point(diameter, probe_depth)