"""图表组件模块"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal, QTimer

from ..utils.chart_config import ChartConfig


class ChartWidget(QWidget):
    """
    matplotlib图表组件
    负责实时数据可视化
    """
    
    # 信号定义
    zoom_changed = Signal(float, float)  # x_min, x_max
    mouse_pressed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = ChartConfig()
        
        # 图表元素
        self.figure = None
        self.canvas = None
        self.ax = None
        self.data_line = None
        self.upper_limit_line = None
        self.lower_limit_line = None
        self.fill_between = None
        
        # 缩放状态
        self.is_zooming = False
        self.zoom_start_x = None
        
        # 数据范围
        self.y_min = None
        self.y_max = None
        
        # 更新定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_plot)
        
        self.setup_ui()
        self.setup_chart()
        
    def setup_ui(self):
        """设置UI布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
    def setup_chart(self):
        """设置matplotlib图表"""
        # 创建图形和画布
        self.figure = Figure(figsize=(8, 4))
        self.canvas = FigureCanvas(self.figure)
        self.layout().addWidget(self.canvas)
        
        # 创建子图
        self.ax = self.figure.add_subplot(111)
        
        # 设置样式
        self.figure.patch.set_facecolor(self.config.FIGURE_BGCOLOR)
        self.ax.set_facecolor(self.config.AXES_BGCOLOR)
        
        # 设置标签
        self.ax.set_xlabel('探测长度 (mm)', fontsize=12)
        self.ax.set_ylabel('管孔直径 (mm)', fontsize=12)
        self.ax.set_title('管孔直径实时数据', fontsize=14, fontweight='bold')
        
        # 创建数据线
        self.data_line, = self.ax.plot([], [], 
                                       color=self.config.LINE_COLOR,
                                       linewidth=self.config.LINE_WIDTH,
                                       label='实测直径')
        
        # 设置网格
        self.ax.grid(True, alpha=0.3)
        
        # 设置图例
        self.ax.legend(loc='upper right')
        
        # 绑定事件
        self.canvas.mpl_connect('scroll_event', self._on_scroll)
        self.canvas.mpl_connect('button_press_event', self._on_mouse_press)
        self.canvas.mpl_connect('button_release_event', self._on_mouse_release)
        self.canvas.mpl_connect('motion_notify_event', self._on_mouse_motion)
        
        # 调整布局
        self.figure.tight_layout()
        
        # 启动更新定时器
        self.update_timer.start(self.config.UPDATE_INTERVAL)
        
    def draw_error_lines(self, standard_diameter: float, upper_tol: float, lower_tol: float):
        """绘制误差线和公差区域"""
        # 移除旧的误差线和填充
        if self.upper_limit_line:
            self.upper_limit_line.remove()
            self.upper_limit_line = None
        if self.lower_limit_line:
            self.lower_limit_line.remove()
            self.lower_limit_line = None
        if self.fill_between:
            self.fill_between.remove()
            self.fill_between = None
            
        # 获取x轴范围
        xlim = self.ax.get_xlim()
        x_range = np.array(xlim)
        
        # 计算上下限
        upper_limit = standard_diameter + upper_tol
        lower_limit = standard_diameter - lower_tol
        
        # 绘制上限线
        self.upper_limit_line = self.ax.axhline(
            y=upper_limit,
            color=self.config.ERROR_LINE_COLOR,
            linestyle=self.config.ERROR_LINE_STYLE,
            linewidth=self.config.ERROR_LINE_WIDTH,
            label=f'上公差 ({upper_limit:.2f}mm)'
        )
        
        # 绘制下限线
        self.lower_limit_line = self.ax.axhline(
            y=lower_limit,
            color=self.config.ERROR_LINE_COLOR,
            linestyle=self.config.ERROR_LINE_STYLE,
            linewidth=self.config.ERROR_LINE_WIDTH,
            label=f'下公差 ({lower_limit:.2f}mm)'
        )
        
        # 绘制公差区域
        self.fill_between = self.ax.fill_between(
            x_range,
            lower_limit,
            upper_limit,
            color=self.config.TOLERANCE_FILL_COLOR,
            alpha=self.config.TOLERANCE_FILL_ALPHA,
            label='公差范围'
        )
        
        # 调整Y轴范围
        self._adjust_y_axis_for_tolerance(standard_diameter, upper_tol, lower_tol)
        
        # 更新图例
        self.ax.legend(loc='upper right')
        
        # 刷新画布
        self.canvas.draw_idle()
        
    def _adjust_y_axis_for_tolerance(self, standard_diameter: float, upper_tol: float, lower_tol: float):
        """调整Y轴范围以适应公差显示"""
        # 计算合适的Y轴范围
        center = standard_diameter
        margin = max(upper_tol, lower_tol) + self.config.Y_AXIS_FOCUS_PADDING
        
        y_min = center - margin - self.config.Y_AXIS_PADDING
        y_max = center + margin + self.config.Y_AXIS_PADDING
        
        self.ax.set_ylim(y_min, y_max)
        
    def update_plot(self):
        """更新图表显示（由定时器触发）"""
        # 这个方法将由主窗口调用来更新数据
        # 实际的数据更新逻辑在主窗口中
        self.canvas.draw_idle()
        
    def update_data(self, x_data: list, y_data: list):
        """更新图表数据"""
        if not x_data or not y_data:
            return
            
        self.data_line.set_data(x_data, y_data)
        
        # 自动调整坐标轴
        self.ax.relim()
        self.ax.autoscale_view()
        
        # 如果设置了Y轴范围，使用固定范围
        if self.y_min is not None and self.y_max is not None:
            self.ax.set_ylim(self.y_min, self.y_max)
            
        self.canvas.draw_idle()
        
    def set_y_range(self, y_min: float, y_max: float):
        """设置Y轴范围"""
        self.y_min = y_min
        self.y_max = y_max
        self.ax.set_ylim(y_min, y_max)
        
    def reset_zoom(self):
        """重置缩放"""
        self.ax.autoscale()
        self.canvas.draw_idle()
        
    def _on_scroll(self, event):
        """处理鼠标滚轮事件（缩放）"""
        if event.inaxes != self.ax:
            return
            
        scale_factor = 1.1 if event.button == 'down' else 0.9
        
        # 获取当前范围
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        
        # 计算新范围
        xdata = event.xdata
        ydata = event.ydata
        
        new_xlim = [xdata - (xdata - xlim[0]) * scale_factor,
                    xdata + (xlim[1] - xdata) * scale_factor]
        new_ylim = [ydata - (ydata - ylim[0]) * scale_factor,
                    ydata + (ylim[1] - ydata) * scale_factor]
        
        self.ax.set_xlim(new_xlim)
        self.ax.set_ylim(new_ylim)
        
        self.canvas.draw_idle()
        self.zoom_changed.emit(new_xlim[0], new_xlim[1])
        
    def _on_mouse_press(self, event):
        """处理鼠标按下事件"""
        if event.inaxes == self.ax and event.button == 1:
            self.is_zooming = True
            self.zoom_start_x = event.xdata
            self.mouse_pressed.emit()
            
    def _on_mouse_release(self, event):
        """处理鼠标释放事件"""
        self.is_zooming = False
        self.zoom_start_x = None
        
    def _on_mouse_motion(self, event):
        """处理鼠标移动事件"""
        # 可以实现拖拽缩放等功能
        pass
        
    def clear_chart(self):
        """清除图表数据"""
        self.data_line.set_data([], [])
        self.canvas.draw_idle()
        
    def cleanup(self):
        """清理资源"""
        self.update_timer.stop()