"""
二维公差带图表组件 - 高内聚低耦合设计
职责：专门负责二维公差带散点图的绘制和交互
基于重构前代码完全恢复功能
"""

import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont
import logging


class ToleranceChartWidget(FigureCanvas):
    """
    二维公差带图表组件
    高内聚：专注于公差带图表的绘制和数据可视化
    低耦合：通过信号与外部组件通信，不依赖具体的数据源
    """
    
    # 信号定义
    point_clicked = Signal(int, float, float)  # 点击数据点时发射 (index, depth, diameter)
    chart_zoomed = Signal(float, float, float, float)  # 图表缩放时发射 (x_min, x_max, y_min, y_max)
    
    def __init__(self, parent=None):
        """初始化二维公差带图表"""
        # 创建matplotlib图形
        self.figure = Figure(figsize=(12, 8), dpi=100)
        super().__init__(self.figure)
        self.setParent(parent)
        
        # 日志记录器
        self.logger = logging.getLogger(__name__)
        
        # 创建子图
        self.ax = self.figure.add_subplot(111)
        
        # 数据存储
        self.measurement_data = []
        self.depths = []
        self.diameters = []
        
        # 公差参数 - 基于重构前的实际值（非对称公差）
        self.standard_diameter = 17.73  # mm
        self.upper_tolerance = 0.07     # +0.07mm
        self.lower_tolerance = 0.05     # -0.05mm (这是负公差)
        
        # 图表状态
        self.is_data_loaded = False
        
        # 初始化图表
        self.setup_chart()
        self.apply_dark_theme()
        self.init_empty_chart()
        
        # 连接鼠标事件
        self.setup_mouse_events()
        
        self.logger.info("二维公差带图表组件初始化完成")
        
    def setup_chart(self):
        """设置图表基本属性"""
        # 设置中文字体支持
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 设置图表布局
        self.figure.subplots_adjust(left=0.1, bottom=0.1, right=0.95, top=0.9)
        
    def apply_dark_theme(self):
        """应用深色主题 - 基于重构前代码"""
        # 设置图形背景色
        self.figure.patch.set_facecolor('#313642')
        self.ax.set_facecolor('#313642')
        
        # 设置坐标轴边框颜色
        for spine in self.ax.spines.values():
            spine.set_color('#505869')
            
        # 设置坐标轴刻度颜色
        self.ax.tick_params(axis='x', colors='#D3D8E0')
        self.ax.tick_params(axis='y', colors='#D3D8E0')
        
        # 设置坐标轴标签颜色
        self.ax.xaxis.label.set_color('#D3D8E0')
        self.ax.yaxis.label.set_color('#D3D8E0')
        self.ax.title.set_color('#FFFFFF')
        
        # 设置网格颜色
        self.ax.grid(True, color='#505869', alpha=0.3)
        
    def init_empty_chart(self):
        """初始化空的二维公差带图表 - 不显示公差线和提示信息"""
        self.ax.clear()
        self.apply_dark_theme()
        
        # 设置坐标轴范围
        self.ax.set_xlim(0, 1000)  # 深度范围 0-1000mm
        self.ax.set_ylim(17.0, 18.0)  # 直径范围，围绕标准直径
        
        # 设置坐标轴标签
        self.ax.set_xlabel('深度 (mm)', fontsize=14, fontweight='bold')
        self.ax.set_ylabel('直径 (mm)', fontsize=14, fontweight='bold')
        self.ax.set_title('二维公差带包络图', fontsize=16, fontweight='bold')
        
        # 不绘制默认公差线和提示文本，保持空白状态
        
        self.draw()
        
    def clear_chart_with_message(self, message="请选择孔位加载数据"):
        """清空图表并显示提示信息，不显示公差线"""
        self.ax.clear()
        self.apply_dark_theme()
        
        # 设置基本样式
        self.ax.set_xlabel('深度 (mm)', color='#D3D8E0', fontsize=12)
        self.ax.set_ylabel('直径 (mm)', color='#D3D8E0', fontsize=12)
        self.ax.set_title('二维公差带包络图', fontsize=16, fontweight='bold')
        
        # 设置轴范围（默认范围）
        self.ax.set_xlim(0, 1000)
        self.ax.set_ylim(17.0, 18.0)
        
        # 显示提示消息
        self.ax.text(0.5, 0.5, message, 
                    transform=self.ax.transAxes,
                    ha='center', va='center',
                    fontsize=12, color='#888888',
                    bbox=dict(boxstyle='round,pad=0.5', 
                             facecolor='#3a3d45', 
                             edgecolor='#505869',
                             alpha=0.8))
                             
        self.draw()
        
    def set_tolerance_parameters(self, standard_diameter: float, upper_tolerance: float, lower_tolerance: float):
        """设置公差参数"""
        self.standard_diameter = standard_diameter
        self.upper_tolerance = upper_tolerance
        self.lower_tolerance = lower_tolerance
        
        self.logger.info(f"公差参数已更新: {standard_diameter}mm (+{upper_tolerance}/-{lower_tolerance})")
        
        # 如果有数据，重新绘制
        if self.is_data_loaded:
            self.redraw_chart()
            
    def load_measurement_data(self, measurements: list, hole_id: str = ""):
        """
        加载测量数据
        measurements: 测量数据列表，每个元素包含 {'depth': float, 'diameter': float}
        """
        if not measurements:
            self.init_empty_chart()
            return
            
        self.measurement_data = measurements
        
        # 提取深度和直径数据
        self.depths = []
        self.diameters = []
        
        for measurement in measurements:
            # 支持不同的键名格式
            depth = measurement.get('depth', measurement.get('position', measurement.get('深度', 0)))
            diameter = measurement.get('diameter', measurement.get('直径', 0))
            
            self.depths.append(float(depth))
            self.diameters.append(float(diameter))
            
        if not self.depths or not self.diameters:
            self.init_empty_chart()
            return
            
        # 转换为numpy数组便于处理
        self.depths = np.array(self.depths)
        self.diameters = np.array(self.diameters)
        
        self.is_data_loaded = True
        
        # 绘制图表
        self.plot_measurement_data(hole_id)
        
        self.logger.info(f"已加载测量数据: {len(measurements)} 个数据点")
        
    def plot_measurement_data(self, hole_id: str = ""):
        """绘制二维公差带包络图 - 基于重构前代码完全恢复"""
        # 清除当前图表
        self.ax.clear()
        self.apply_dark_theme()
        
        # 计算坐标轴范围
        depth_margin = (max(self.depths) - min(self.depths)) * 0.05 if len(self.depths) > 1 else 50
        diameter_margin = (max(self.diameters) - min(self.diameters)) * 0.1 if len(self.diameters) > 1 else 0.05
        
        x_min = max(0, min(self.depths) - depth_margin)
        x_max = max(self.depths) + depth_margin
        y_min = min(min(self.diameters), self.standard_diameter - self.lower_tolerance) - diameter_margin
        y_max = max(max(self.diameters), self.standard_diameter + self.upper_tolerance) + diameter_margin
        
        self.ax.set_xlim(x_min, x_max)
        self.ax.set_ylim(y_min, y_max)
        
        # 绘制公差线
        depth_range = [x_min, x_max]
        self._draw_tolerance_lines(depth_range)
        
        # 绘制测量数据曲线
        self.ax.plot(self.depths, self.diameters, 'b-', linewidth=2, 
                    marker='o', markersize=4, markerfacecolor='#4A90E2',
                    markeredgecolor='white', markeredgewidth=0.5,
                    label='测量数据', alpha=0.8)
        
        # 标记超出公差的点
        self._mark_outliers()
        
        # 设置坐标轴标签和标题
        self.ax.set_xlabel('深度 (mm)', fontsize=14, fontweight='bold')
        self.ax.set_ylabel('直径 (mm)', fontsize=14, fontweight='bold')
        
        title = f'二维公差带包络图'
        if hole_id:
            title += f' - {hole_id}'
        self.ax.set_title(title, fontsize=16, fontweight='bold')
        
        # 设置网格和图例
        self.ax.grid(True, alpha=0.3, color='#505869')
        
        # 创建图例
        legend = self.ax.legend(loc='upper right', fontsize=12, 
                               fancybox=True, shadow=True, framealpha=0.9)
        legend.get_frame().set_facecolor('#3a3d45')
        legend.get_frame().set_edgecolor('#505869')
        for text in legend.get_texts():
            text.set_color('#D3D8E0')
            
        # 添加统计信息文本框
        self._add_statistics_textbox()
        
        # 刷新画布
        self.draw()
        
    def _draw_tolerance_lines(self, depth_range: list):
        """绘制公差线"""
        # 上公差线
        upper_line = np.full(2, self.standard_diameter + self.upper_tolerance)
        self.ax.plot(depth_range, upper_line, 'r--', linewidth=2, alpha=0.8,
                    label=f'上公差线 ({self.standard_diameter + self.upper_tolerance:.3f}mm)')
        
        # 下公差线 - 修正为负公差
        lower_line = np.full(2, self.standard_diameter - self.lower_tolerance)
        self.ax.plot(depth_range, lower_line, 'r--', linewidth=2, alpha=0.8,
                    label=f'下公差线 ({self.standard_diameter - self.lower_tolerance:.3f}mm)')
        
        # 标准直径线
        standard_line = np.full(2, self.standard_diameter)
        self.ax.plot(depth_range, standard_line, 'g-', linewidth=1.5, alpha=0.7,
                    label=f'标准直径 ({self.standard_diameter:.2f}mm)')
        
        # 填充公差带区域
        self.ax.fill_between(depth_range, 
                            self.standard_diameter - self.lower_tolerance,
                            self.standard_diameter + self.upper_tolerance,
                            alpha=0.1, color='green', label='合格区域')
                            
    def _mark_outliers(self):
        """标记超出公差的点"""
        outlier_count = 0
        for i, (depth, diameter) in enumerate(zip(self.depths, self.diameters)):
            # 检查是否超出公差
            if (diameter > self.standard_diameter + self.upper_tolerance or 
                diameter < self.standard_diameter - self.lower_tolerance):
                self.ax.plot(depth, diameter, 'ro', markersize=8, alpha=0.9, 
                           markeredgecolor='white', markeredgewidth=1)
                outlier_count += 1
                
        if outlier_count > 0:
            self.logger.warning(f"发现 {outlier_count} 个超出公差的数据点")
            
    def _add_statistics_textbox(self):
        """添加统计信息文本框"""
        if len(self.diameters) == 0:
            return
            
        # 计算统计量
        mean_diameter = np.mean(self.diameters)
        std_diameter = np.std(self.diameters)
        min_diameter = np.min(self.diameters)
        max_diameter = np.max(self.diameters)
        
        # 计算合格率
        in_tolerance = np.sum((self.diameters >= self.standard_diameter - self.lower_tolerance) & 
                             (self.diameters <= self.standard_diameter + self.upper_tolerance))
        pass_rate = (in_tolerance / len(self.diameters)) * 100
        
        # 创建统计文本
        stats_text = (
            f'数据统计:\n'
            f'数据点数: {len(self.diameters)}\n'
            f'平均直径: {mean_diameter:.3f}mm\n'
            f'标准偏差: {std_diameter:.3f}mm\n'
            f'最小值: {min_diameter:.3f}mm\n'
            f'最大值: {max_diameter:.3f}mm\n'
            f'合格率: {pass_rate:.1f}%'
        )
        
        # 添加文本框
        props = dict(boxstyle='round', facecolor='#3a3d45', alpha=0.9, edgecolor='#505869')
        self.ax.text(0.02, 0.98, stats_text, transform=self.ax.transAxes,
                    fontsize=10, verticalalignment='top', bbox=props,
                    color='#D3D8E0')
                    
    def setup_mouse_events(self):
        """设置鼠标事件"""
        self.mpl_connect('scroll_event', self.on_scroll)
        self.mpl_connect('button_press_event', self.on_click)
        
    def on_scroll(self, event):
        """处理鼠标滚轮缩放事件"""
        if event.inaxes != self.ax:
            return
            
        # 获取当前坐标轴范围
        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()
        
        # 获取鼠标位置
        xdata = event.xdata
        ydata = event.ydata
        
        if xdata is None or ydata is None:
            return
            
        # 设置缩放因子
        if event.button == 'up':
            scale_factor = 0.9  # 放大
        elif event.button == 'down':
            scale_factor = 1.1  # 缩小
        else:
            return
            
        # 计算新的坐标轴范围
        new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
        new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor
        
        relx = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])
        rely = (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])
        
        new_xlim = [xdata - new_width * (1 - relx), xdata + new_width * relx]
        new_ylim = [ydata - new_height * (1 - rely), ydata + new_height * rely]
        
        # 应用新的坐标轴范围
        self.ax.set_xlim(new_xlim)
        self.ax.set_ylim(new_ylim)
        self.draw()
        
        # 发射缩放信号
        self.chart_zoomed.emit(new_xlim[0], new_xlim[1], new_ylim[0], new_ylim[1])
        
    def on_click(self, event):
        """处理鼠标点击事件"""
        if event.inaxes != self.ax or not self.is_data_loaded:
            return
            
        # 双击重置视图
        if event.dblclick:
            self.reset_view()
            return
            
        # 查找最近的数据点
        if len(self.depths) > 0:
            click_x = event.xdata
            click_y = event.ydata
            
            if click_x is None or click_y is None:
                return
                
            # 计算到所有数据点的距离
            distances = np.sqrt((self.depths - click_x)**2 + (self.diameters - click_y)**2)
            closest_index = np.argmin(distances)
            
            # 如果点击距离足够近，发射信号
            if distances[closest_index] < (max(self.depths) - min(self.depths)) * 0.02:
                self.point_clicked.emit(closest_index, 
                                      float(self.depths[closest_index]), 
                                      float(self.diameters[closest_index]))
                                      
    def reset_view(self):
        """重置视图到初始状态"""
        if self.is_data_loaded:
            self.plot_measurement_data()
        else:
            self.init_empty_chart()
            
    def redraw_chart(self):
        """重新绘制图表"""
        if self.is_data_loaded:
            self.plot_measurement_data()
        else:
            self.init_empty_chart()
            
    def clear_chart(self):
        """清除图表数据"""
        self.measurement_data = []
        self.depths = []
        self.diameters = []
        self.is_data_loaded = False
        self.init_empty_chart()
        
    def export_chart(self, file_path: str):
        """导出图表为图片"""
        try:
            self.figure.savefig(file_path, dpi=300, bbox_inches='tight', 
                              facecolor=self.figure.get_facecolor())
            self.logger.info(f"图表已导出: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"导出图表失败: {e}")
            return False
            
    def get_chart_data(self):
        """获取当前图表数据"""
        return {
            'depths': self.depths.tolist() if len(self.depths) > 0 else [],
            'diameters': self.diameters.tolist() if len(self.diameters) > 0 else [],
            'standard_diameter': self.standard_diameter,
            'upper_tolerance': self.upper_tolerance,
            'lower_tolerance': self.lower_tolerance,
            'data_count': len(self.depths)
        }


class ToleranceChartContainer(QWidget):
    """
    二维公差带图表容器组件
    高内聚：专门负责图表的布局和标题显示
    低耦合：封装图表组件，提供统一的外部接口
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(0)
        
        # 创建图表组件
        self.chart_widget = ToleranceChartWidget()
        layout.addWidget(self.chart_widget)
        
    def load_data(self, measurements: list, hole_id: str = ""):
        """加载数据到图表"""
        self.chart_widget.load_measurement_data(measurements, hole_id)
        
    def clear_chart_with_message(self, message="请选择孔位加载数据"):
        """清空图表并显示提示信息"""
        self.chart_widget.clear_chart_with_message(message)
        
    def set_tolerance_parameters(self, standard_diameter: float, upper_tolerance: float, lower_tolerance: float):
        """设置公差参数"""
        self.chart_widget.set_tolerance_parameters(standard_diameter, upper_tolerance, lower_tolerance)
        
    def clear_data(self):
        """清除图表数据"""
        self.chart_widget.clear_chart()
        
    def export_chart(self, file_path: str):
        """导出图表"""
        return self.chart_widget.export_chart(file_path)
        
    def get_chart_data(self):
        """获取图表数据"""
        return self.chart_widget.get_chart_data()