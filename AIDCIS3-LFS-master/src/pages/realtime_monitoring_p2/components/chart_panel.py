"""
图表面板组件
负责显示实时的管孔直径数据图表
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib
import numpy as np
from collections import deque
from typing import List, Tuple, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QToolButton
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPainter

# 设置matplotlib支持中文显示
def setup_safe_chinese_font():
    """设置安全的中文字体支持"""
    try:
        matplotlib.rcParams['font.family'] = 'sans-serif'
        matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC', 'SimHei', 'DejaVu Sans']
        matplotlib.rcParams['axes.unicode_minus'] = False
    except Exception as e:
        matplotlib.rcParams['font.family'] = 'DejaVu Sans'

# 初始化字体配置
setup_safe_chinese_font()


class ChartPanel(QWidget):
    """
    图表面板组件
    使用matplotlib实现实时数据显示
    """
    
    # 信号定义
    export_requested = Signal()
    refresh_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 数据存储
        self.depth_data = deque(maxlen=1000)
        self.diameter_data = deque(maxlen=1000)
        
        # 图表参数
        self.standard_diameter = 17.73
        self.tolerance = 0.07
        self.upper_tolerance = 0.07
        self.lower_tolerance = 0.05
        
        # 误差线
        self.max_error_line = None
        self.min_error_line = None
        
        self.setup_ui()
        self.setup_chart()
        
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建图表标题栏 - 更紧凑的样式，匹配重构前布局
        chart_header = QWidget()
        chart_header.setObjectName("PanelHeader")
        chart_header_layout = QHBoxLayout(chart_header)
        chart_header_layout.setContentsMargins(10, 0, 10, 0)  # 减少边距
        chart_header_layout.setSpacing(8)  # 减少间距

        chart_title = QLabel("管孔直径实时监测")
        chart_title.setObjectName("PanelHeaderText")

        # 添加工具按钮 - 更小的按钮
        export_chart_button = QToolButton()
        export_chart_button.setObjectName("HeaderToolButton")
        export_chart_button.setText("📊")
        export_chart_button.setToolTip("导出图表为图片")
        export_chart_button.clicked.connect(self.export_requested.emit)
        export_chart_button.setFixedSize(24, 24)  # 固定小尺寸

        refresh_chart_button = QToolButton()
        refresh_chart_button.setObjectName("HeaderToolButton")
        refresh_chart_button.setText("🔄")
        refresh_chart_button.setToolTip("刷新图表")
        refresh_chart_button.clicked.connect(self.refresh_requested.emit)
        refresh_chart_button.setFixedSize(24, 24)  # 固定小尺寸

        chart_header_layout.addWidget(chart_title)
        chart_header_layout.addStretch()
        chart_header_layout.addWidget(refresh_chart_button)
        chart_header_layout.addWidget(export_chart_button)

        layout.addWidget(chart_header)
        
        # 创建matplotlib图形 - 更紧凑的尺寸，匹配重构前布局
        self.figure = Figure(figsize=(20, 10), dpi=100)  # 减少图表尺寸
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # 连接鼠标事件
        self.canvas.mpl_connect('scroll_event', self.on_scroll)
        self.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        
    def setup_chart(self):
        """设置图表"""
        # 创建子图
        self.ax = self.figure.add_subplot(111)
        self.apply_matplotlib_dark_theme()
        self.ax.set_xlabel('深度 (mm)', fontsize=14, fontweight='bold')
        self.ax.set_ylabel('直径 (mm)', fontsize=14, fontweight='bold')
        self.ax.grid(True, alpha=0.3)

        # 设置坐标轴刻度字体大小
        self.ax.tick_params(axis='both', which='major', labelsize=12)
        self.ax.tick_params(axis='both', which='minor', labelsize=10)

        # 设置初始范围
        self.ax.set_ylim(16.5, 20.5)
        self.ax.set_xlim(0, 950)

        # 初始化数据线
        self.data_line, = self.ax.plot([], [], color='#4A90E2', linewidth=3, label='直径数据')

        # 设置图形样式
        self.figure.subplots_adjust(left=0.12, bottom=0.15, right=0.95, top=0.85)

        # 设置图例位置
        self.ax.legend(loc='upper right', bbox_to_anchor=(0.95, 0.95), fontsize=12)
        
        # 绘制误差线
        self.draw_error_lines()
        
        # 刷新画布
        self.canvas.draw()
        
    def apply_matplotlib_dark_theme(self):
        """应用深色主题"""
        try:
            self.figure.patch.set_facecolor('#2b2b2b')
            self.ax.set_facecolor('#1e1e1e')
            self.ax.xaxis.label.set_color('white')
            self.ax.yaxis.label.set_color('white')
            self.ax.tick_params(colors='white')
            for spine in self.ax.spines.values():
                spine.set_color('white')
        except Exception as e:
            print(f"⚠️ 应用深色主题失败: {e}")
            
    def draw_error_lines(self):
        """绘制误差线"""
        try:
            # 清除现有误差线
            if self.max_error_line:
                self.max_error_line.remove()
            if self.min_error_line:
                self.min_error_line.remove()
                
            # 计算误差范围
            max_diameter = self.standard_diameter + self.upper_tolerance
            min_diameter = self.standard_diameter - self.lower_tolerance
            
            # 绘制误差线
            xlim = self.ax.get_xlim()
            self.max_error_line = self.ax.axhline(y=max_diameter, color='red', linestyle='--', 
                                                 linewidth=2, alpha=0.7, label=f'上限 {max_diameter:.2f}mm')
            self.min_error_line = self.ax.axhline(y=min_diameter, color='red', linestyle='--', 
                                                 linewidth=2, alpha=0.7, label=f'下限 {min_diameter:.2f}mm')
            
            # 更新图例
            self.ax.legend(loc='upper right', bbox_to_anchor=(0.95, 0.95), fontsize=12)
            
        except Exception as e:
            print(f"⚠️ 绘制误差线失败: {e}")
            
    def add_data_point(self, depth: float, diameter: float):
        """添加数据点"""
        self.depth_data.append(depth)
        self.diameter_data.append(diameter)
        self.update_plot()
        
    def update_plot(self):
        """更新图表显示"""
        try:
            if self.depth_data and self.diameter_data:
                self.data_line.set_data(list(self.depth_data), list(self.diameter_data))
                
                # 自动调整X轴范围
                if len(self.depth_data) > 0:
                    max_depth = max(self.depth_data)
                    if max_depth > 0:
                        self.ax.set_xlim(0, max(950, max_depth * 1.1))
                
                self.canvas.draw()
        except Exception as e:
            print(f"⚠️ 更新图表失败: {e}")
            
    def clear_data(self):
        """清除数据"""
        self.depth_data.clear()
        self.diameter_data.clear()
        self.data_line.set_data([], [])
        self.canvas.draw()
        
    def set_standard_diameter(self, diameter: float, upper_tol: float = 0.07, lower_tol: float = 0.05):
        """设置标准直径和公差"""
        self.standard_diameter = diameter
        self.upper_tolerance = upper_tol
        self.lower_tolerance = lower_tol
        self.draw_error_lines()
        self.canvas.draw()
        
    def on_scroll(self, event):
        """鼠标滚轮缩放"""
        try:
            if event.inaxes != self.ax:
                return
                
            scale_factor = 1.1 if event.button == 'up' else 1/1.1
            
            # 获取当前范围
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
            
            # 计算新范围
            x_center = (xlim[0] + xlim[1]) / 2
            y_center = (ylim[0] + ylim[1]) / 2
            
            x_range = (xlim[1] - xlim[0]) * scale_factor / 2
            y_range = (ylim[1] - ylim[0]) * scale_factor / 2
            
            self.ax.set_xlim(x_center - x_range, x_center + x_range)
            self.ax.set_ylim(y_center - y_range, y_center + y_range)
            
            self.canvas.draw()
        except Exception as e:
            print(f"⚠️ 缩放失败: {e}")
            
    def on_mouse_press(self, event):
        """鼠标点击重置视图"""
        try:
            if event.button == 2:  # 中键点击重置
                self.ax.set_ylim(16.5, 20.5)
                self.ax.set_xlim(0, 950)
                self.canvas.draw()
        except Exception as e:
            print(f"⚠️ 重置视图失败: {e}")
            
    def get_data_statistics(self) -> Tuple[Optional[float], Optional[float]]:
        """获取数据统计信息"""
        if not self.diameter_data:
            return None, None
            
        return max(self.diameter_data), min(self.diameter_data)
