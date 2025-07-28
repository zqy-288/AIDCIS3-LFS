"""
纯图表渲染组件
专注于matplotlib图表的绘制和交互
"""
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.patches as patches
from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import QWidget, QVBoxLayout
from typing import List, Tuple, Optional
from ..utils.constants import (
    CHART_FIGURE_SIZE, CHART_DPI, DEFAULT_STANDARD_DIAMETER, 
    DEFAULT_TOLERANCE
)
from ..utils.font_config import apply_matplotlib_dark_theme


class ChartWidget(QWidget):
    """纯matplotlib图表渲染组件"""
    
    # 信号定义
    zoom_changed = Signal(float, float, float, float)  # x_min, x_max, y_min, y_max
    data_point_clicked = Signal(float, float)  # depth, diameter
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._init_chart()
        self._init_interaction()
        
        # 数据存储
        self.depth_data = []
        self.diameter_data = []
        self.anomaly_points = []
        
        # 标准直径设置
        self.standard_diameter = DEFAULT_STANDARD_DIAMETER
        self.tolerance = DEFAULT_TOLERANCE
        self.show_tolerance_lines = False
        
        # 缩放状态
        self._is_panning = False
        self._pan_start = None
        self._zoom_level = 1.0
        
    def _setup_ui(self):
        """设置UI布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建matplotlib图形
        self.figure = Figure(figsize=CHART_FIGURE_SIZE, dpi=CHART_DPI)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
    def _init_chart(self):
        """初始化图表"""
        self.ax = self.figure.add_subplot(111)
        
        # 设置标签
        self.ax.set_xlabel('探头深度 (mm)', fontsize=14)
        self.ax.set_ylabel('管孔直径 (mm)', fontsize=14)
        self.ax.set_title('管孔直径实时监测', fontsize=16, pad=20)
        
        # 初始化数据线
        self.line, = self.ax.plot([], [], 'b-', linewidth=2, label='直径数据')
        self.anomaly_scatter = self.ax.scatter([], [], c='red', s=100, 
                                              marker='o', label='异常点', zorder=5)
        
        # 初始化误差线（隐藏）
        self.upper_line = self.ax.axhline(y=0, color='green', linestyle='--', 
                                         linewidth=2, alpha=0.7, visible=False)
        self.lower_line = self.ax.axhline(y=0, color='green', linestyle='--', 
                                         linewidth=2, alpha=0.7, visible=False)
        
        # 初始化误差带
        self.tolerance_band = None
        
        # 设置初始范围
        self.ax.set_xlim(0, 100)
        self.ax.set_ylim(15, 20)
        
        # 启用网格
        self.ax.grid(True, linestyle='--', alpha=0.3)
        
        # 应用深色主题
        apply_matplotlib_dark_theme(self.figure)
        
        # 初始绘制
        self.canvas.draw()
        
    def _init_interaction(self):
        """初始化交互功能"""
        # 连接鼠标事件
        self.canvas.mpl_connect('scroll_event', self._on_scroll)
        self.canvas.mpl_connect('button_press_event', self._on_mouse_press)
        self.canvas.mpl_connect('button_release_event', self._on_mouse_release)
        self.canvas.mpl_connect('motion_notify_event', self._on_mouse_motion)
        
    def update_data(self, depth_data: List[float], diameter_data: List[float]):
        """更新图表数据"""
        self.depth_data = depth_data
        self.diameter_data = diameter_data
        
        if depth_data and diameter_data:
            self.line.set_data(depth_data, diameter_data)
            
            # 自动调整范围（如果没有手动缩放）
            if self._zoom_level == 1.0:
                self._auto_scale()
        else:
            self.line.set_data([], [])
            
        self.canvas.draw_idle()
        
    def update_anomaly_points(self, anomaly_indices: List[int]):
        """更新异常点显示"""
        if anomaly_indices and self.depth_data and self.diameter_data:
            anomaly_depths = [self.depth_data[i] for i in anomaly_indices 
                             if i < len(self.depth_data)]
            anomaly_diameters = [self.diameter_data[i] for i in anomaly_indices 
                               if i < len(self.diameter_data)]
            self.anomaly_scatter.set_offsets(
                np.c_[anomaly_depths, anomaly_diameters]
            )
        else:
            self.anomaly_scatter.set_offsets(np.empty((0, 2)))
            
        self.canvas.draw_idle()
        
    def set_standard_diameter(self, diameter: float, tolerance: float):
        """设置标准直径和公差"""
        self.standard_diameter = diameter
        self.tolerance = tolerance
        self.show_tolerance_lines = True
        
        # 更新误差线位置
        upper_limit = diameter + tolerance
        lower_limit = diameter - tolerance
        
        self.upper_line.set_ydata([upper_limit, upper_limit])
        self.lower_line.set_ydata([lower_limit, lower_limit])
        self.upper_line.set_visible(True)
        self.lower_line.set_visible(True)
        
        # 更新或创建误差带
        if self.tolerance_band:
            self.tolerance_band.remove()
            
        xlim = self.ax.get_xlim()
        self.tolerance_band = patches.Rectangle(
            (xlim[0], lower_limit),
            xlim[1] - xlim[0],
            upper_limit - lower_limit,
            facecolor='green',
            alpha=0.1,
            edgecolor='none'
        )
        self.ax.add_patch(self.tolerance_band)
        
        # 调整Y轴范围
        self._adjust_y_axis_for_tolerance()
        
        self.canvas.draw_idle()
        
    def clear_chart(self):
        """清除图表数据"""
        self.depth_data = []
        self.diameter_data = []
        self.anomaly_points = []
        
        self.line.set_data([], [])
        self.anomaly_scatter.set_offsets(np.empty((0, 2)))
        
        # 重置缩放
        self._zoom_level = 1.0
        self.ax.set_xlim(0, 100)
        self.ax.set_ylim(15, 20)
        
        self.canvas.draw_idle()
        
    def reset_zoom(self):
        """重置缩放到默认视图"""
        self._zoom_level = 1.0
        self._auto_scale()
        self.canvas.draw_idle()
        
    def _auto_scale(self):
        """自动调整坐标轴范围"""
        if self.depth_data and self.diameter_data:
            # X轴范围
            x_margin = 5
            self.ax.set_xlim(0, max(self.depth_data) + x_margin)
            
            # Y轴范围
            if self.show_tolerance_lines:
                self._adjust_y_axis_for_tolerance()
            else:
                y_min = min(self.diameter_data)
                y_max = max(self.diameter_data)
                y_margin = (y_max - y_min) * 0.1 + 0.5
                self.ax.set_ylim(y_min - y_margin, y_max + y_margin)
                
    def _adjust_y_axis_for_tolerance(self):
        """根据公差线调整Y轴范围"""
        upper_limit = self.standard_diameter + self.tolerance
        lower_limit = self.standard_diameter - self.tolerance
        
        # 计算合适的Y轴范围
        y_range = upper_limit - lower_limit
        y_margin = y_range * 0.5  # 上下各留50%的边距
        
        self.ax.set_ylim(lower_limit - y_margin, upper_limit + y_margin)
        
    def _on_scroll(self, event):
        """处理鼠标滚轮缩放"""
        if event.inaxes != self.ax:
            return
            
        # 获取当前范围
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        
        # 计算缩放因子
        scale_factor = 0.9 if event.button == 'up' else 1.1
        
        # 计算新范围
        x_center = event.xdata
        y_center = event.ydata
        
        new_xlim = [
            x_center - (x_center - xlim[0]) * scale_factor,
            x_center + (xlim[1] - x_center) * scale_factor
        ]
        new_ylim = [
            y_center - (y_center - ylim[0]) * scale_factor,
            y_center + (ylim[1] - y_center) * scale_factor
        ]
        
        # 应用新范围
        self.ax.set_xlim(new_xlim)
        self.ax.set_ylim(new_ylim)
        
        # 更新缩放级别
        self._zoom_level *= scale_factor
        
        # 更新误差带位置
        if self.tolerance_band:
            self.tolerance_band.set_x(new_xlim[0])
            self.tolerance_band.set_width(new_xlim[1] - new_xlim[0])
            
        self.canvas.draw_idle()
        
        # 发送缩放变化信号
        self.zoom_changed.emit(*new_xlim, *new_ylim)
        
    def _on_mouse_press(self, event):
        """处理鼠标按下事件"""
        if event.button == 1 and event.inaxes == self.ax:  # 左键
            self._is_panning = True
            self._pan_start = (event.x, event.y)
            
    def _on_mouse_release(self, event):
        """处理鼠标释放事件"""
        if event.button == 1:  # 左键
            self._is_panning = False
            self._pan_start = None
            
        elif event.button == 3 and event.inaxes == self.ax:  # 右键
            # 发送点击信号
            if event.xdata is not None and event.ydata is not None:
                self.data_point_clicked.emit(event.xdata, event.ydata)
                
    def _on_mouse_motion(self, event):
        """处理鼠标移动事件"""
        if self._is_panning and self._pan_start and event.inaxes == self.ax:
            # 计算移动距离
            dx = event.x - self._pan_start[0]
            dy = event.y - self._pan_start[1]
            
            # 转换为数据坐标
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
            
            # 计算数据范围
            x_range = xlim[1] - xlim[0]
            y_range = ylim[1] - ylim[0]
            
            # 计算平移量
            x_shift = -dx / self.ax.bbox.width * x_range
            y_shift = dy / self.ax.bbox.height * y_range
            
            # 应用平移
            self.ax.set_xlim(xlim[0] + x_shift, xlim[1] + x_shift)
            self.ax.set_ylim(ylim[0] + y_shift, ylim[1] + y_shift)
            
            # 更新误差带位置
            if self.tolerance_band:
                new_xlim = self.ax.get_xlim()
                self.tolerance_band.set_x(new_xlim[0])
                self.tolerance_band.set_width(new_xlim[1] - new_xlim[0])
                
            self.canvas.draw_idle()
            
            # 更新起始点
            self._pan_start = (event.x, event.y)
            
    def export_chart(self, filepath: str):
        """导出图表为图片"""
        self.figure.savefig(filepath, dpi=300, bbox_inches='tight', 
                           facecolor=self.figure.get_facecolor())
        
    def get_current_range(self) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """获取当前显示范围"""
        return self.ax.get_xlim(), self.ax.get_ylim()