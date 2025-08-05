"""
P2 增强图表组件
整合自 modules/realtime_chart_p2/components/chart_widget.py
专为P2实时监控页面优化
"""

import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Signal, QTimer, Slot
from PySide6.QtGui import QFont

import logging
from typing import List, Tuple, Optional, Dict, Any
from collections import deque
from datetime import datetime

# 设置matplotlib支持中文显示
def setup_chinese_font():
    """设置中文字体支持"""
    try:
        matplotlib.rcParams['font.family'] = 'sans-serif'
        matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC', 'SimHei', 'DejaVu Sans']
        matplotlib.rcParams['axes.unicode_minus'] = False
        matplotlib.rcParams['figure.facecolor'] = 'white'
        matplotlib.rcParams['axes.facecolor'] = 'white'
    except Exception as e:
        print(f"字体配置失败: {e}")

setup_chinese_font()


class EnhancedChartWidget(QWidget):
    """
    增强的实时图表组件
    
    功能：
    1. 实时数据显示和动态更新
    2. 异常点标记和分析
    3. 标准直径和容差带显示
    4. 交互式缩放和平移
    5. 数据导出和分析
    """
    
    # 信号定义
    zoom_changed = Signal(float, float, float, float)  # x_min, x_max, y_min, y_max
    data_point_clicked = Signal(float, float)  # depth, diameter
    anomaly_detected = Signal(dict)  # 异常信息
    data_updated = Signal(list, list)  # 数据更新
    export_requested = Signal(str)  # 导出请求
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 数据存储
        self.depth_data = deque(maxlen=10000)  # 最多存储10000个点
        self.diameter_data = deque(maxlen=10000)
        self.anomaly_points = []
        self.time_data = deque(maxlen=10000)
        
        # 图表配置
        self.standard_diameter = 17.6  # 标准直径
        self.tolerance = 0.2  # 公差
        self.show_tolerance_lines = True
        self.show_anomalies = True
        self.auto_scale = True
        
        # 动画和更新
        self.update_interval = 100  # ms
        self.animation_enabled = True
        self.last_update_time = datetime.now()
        
        # 缩放和交互
        self._zoom_level = 1.0
        self._is_panning = False
        self._pan_start = None
        
        # 初始化UI
        self._setup_ui()
        self._init_chart()
        self._init_interaction()
        
        # 更新定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_chart_animation)
        
    def _setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 创建工具栏
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
        
        # 创建matplotlib图表
        self.figure = Figure(figsize=(12, 6), dpi=100, facecolor='white')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setParent(self)
        
        layout.addWidget(self.canvas)
        
        # 状态栏
        status_bar = self._create_status_bar()
        layout.addWidget(status_bar)
        
    def _create_toolbar(self):
        """创建工具栏"""
        toolbar = QWidget()
        toolbar.setMaximumHeight(40)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(5, 5, 5, 5)
        
        # 控制按钮
        self.start_button = QPushButton("开始监测")
        self.start_button.clicked.connect(self.start_monitoring)
        
        self.stop_button = QPushButton("停止监测")
        self.stop_button.clicked.connect(self.stop_monitoring)
        self.stop_button.setEnabled(False)
        
        self.clear_button = QPushButton("清除数据")
        self.clear_button.clicked.connect(self.clear_data)
        
        self.export_button = QPushButton("导出数据")
        self.export_button.clicked.connect(self._export_data)
        
        # 设置按钮
        self.auto_scale_button = QPushButton("自动缩放")
        self.auto_scale_button.setCheckable(True)
        self.auto_scale_button.setChecked(self.auto_scale)
        self.auto_scale_button.clicked.connect(self._toggle_auto_scale)
        
        self.tolerance_button = QPushButton("显示公差")
        self.tolerance_button.setCheckable(True)
        self.tolerance_button.setChecked(self.show_tolerance_lines)
        self.tolerance_button.clicked.connect(self._toggle_tolerance_lines)
        
        toolbar_layout.addWidget(self.start_button)
        toolbar_layout.addWidget(self.stop_button)
        toolbar_layout.addWidget(self.clear_button)
        toolbar_layout.addWidget(self.export_button)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.auto_scale_button)
        toolbar_layout.addWidget(self.tolerance_button)
        
        return toolbar
        
    def _create_status_bar(self):
        """创建状态栏"""
        status_bar = QWidget()
        status_bar.setMaximumHeight(30)
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(5, 2, 5, 2)
        
        self.status_label = QLabel("就绪")
        self.data_count_label = QLabel("数据点: 0")
        self.anomaly_count_label = QLabel("异常: 0")
        self.zoom_label = QLabel("缩放: 100%")
        
        # 设置样式
        for label in [self.status_label, self.data_count_label, 
                     self.anomaly_count_label, self.zoom_label]:
            label.setStyleSheet("color: #666; font-size: 11px;")
        
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.data_count_label)
        status_layout.addWidget(self.anomaly_count_label)
        status_layout.addWidget(self.zoom_label)
        
        return status_bar
        
    def _init_chart(self):
        """初始化图表"""
        # 创建子图
        self.ax = self.figure.add_subplot(111)
        
        # 设置基本属性
        self.ax.set_xlabel('深度 (mm)', fontsize=12)
        self.ax.set_ylabel('直径 (mm)', fontsize=12)
        self.ax.set_title('实时直径监测', fontsize=14, fontweight='bold')
        self.ax.grid(True, alpha=0.3)
        
        # 初始化数据线
        self.data_line, = self.ax.plot([], [], 'b-', linewidth=2, label='测量数据')
        self.anomaly_scatter = self.ax.scatter([], [], c='red', s=50, marker='x', 
                                             label='异常点', zorder=5)
        
        # 添加标准直径线和公差带
        self._setup_tolerance_lines()
        
        # 设置图例
        self.ax.legend(loc='upper right')
        
        # 调整布局
        self.figure.tight_layout()
        
    def _setup_tolerance_lines(self):
        """设置公差线"""
        if self.show_tolerance_lines:
            # 标准直径线
            self.std_line = self.ax.axhline(y=self.standard_diameter, 
                                          color='green', linestyle='--', 
                                          linewidth=2, alpha=0.7, 
                                          label=f'标准直径 ({self.standard_diameter}mm)')
            
            # 上公差线
            self.upper_line = self.ax.axhline(y=self.standard_diameter + self.tolerance, 
                                            color='orange', linestyle=':', 
                                            linewidth=1.5, alpha=0.7,
                                            label=f'上限 (+{self.tolerance}mm)')
            
            # 下公差线
            self.lower_line = self.ax.axhline(y=self.standard_diameter - self.tolerance, 
                                            color='orange', linestyle=':', 
                                            linewidth=1.5, alpha=0.7,
                                            label=f'下限 (-{self.tolerance}mm)')
            
            # 公差带填充
            self.tolerance_fill = self.ax.fill_between([0, 1], 
                                                     self.standard_diameter - self.tolerance,
                                                     self.standard_diameter + self.tolerance,
                                                     alpha=0.1, color='green',
                                                     label='公差带')       
        
    def _init_interaction(self):
        """初始化交互功能"""
        # 连接事件
        self.canvas.mpl_connect('button_press_event', self._on_mouse_press)
        self.canvas.mpl_connect('button_release_event', self._on_mouse_release)
        self.canvas.mpl_connect('motion_notify_event', self._on_mouse_move)
        self.canvas.mpl_connect('scroll_event', self._on_scroll)
        
    def add_data_point(self, depth: float, diameter: float, timestamp: datetime = None):
        """添加数据点"""
        if timestamp is None:
            timestamp = datetime.now()
            
        self.depth_data.append(depth)
        self.diameter_data.append(diameter)
        self.time_data.append(timestamp)
        
        # 检测异常
        if self._is_anomaly(diameter):
            anomaly_info = {
                'depth': depth,
                'diameter': diameter,
                'timestamp': timestamp,
                'type': self._classify_anomaly(diameter)
            }
            self.anomaly_points.append(anomaly_info)
            self.anomaly_detected.emit(anomaly_info)
            
        # 更新状态栏
        self._update_status_bar()
        
        # 触发重绘
        if not self.update_timer.isActive():
            self._update_chart()
            
    def add_data_batch(self, depths: List[float], diameters: List[float], 
                      timestamps: List[datetime] = None):
        """批量添加数据点"""
        if timestamps is None:
            timestamps = [datetime.now()] * len(depths)
            
        for depth, diameter, timestamp in zip(depths, diameters, timestamps):
            self.add_data_point(depth, diameter, timestamp)
            
    def _is_anomaly(self, diameter: float) -> bool:
        """判断是否异常"""
        return abs(diameter - self.standard_diameter) > self.tolerance
        
    def _classify_anomaly(self, diameter: float) -> str:
        """分类异常类型"""
        if diameter > self.standard_diameter + self.tolerance:
            return "超上限"
        elif diameter < self.standard_diameter - self.tolerance:
            return "超下限"
        else:
            return "正常"
            
    def _update_chart(self):
        """更新图表显示"""
        try:
            if len(self.depth_data) == 0:
                return
                
            # 更新数据线
            self.data_line.set_data(list(self.depth_data), list(self.diameter_data))
            
            # 更新异常点
            if self.anomaly_points and self.show_anomalies:
                anomaly_depths = [p['depth'] for p in self.anomaly_points]
                anomaly_diameters = [p['diameter'] for p in self.anomaly_points]
                self.anomaly_scatter.set_offsets(np.column_stack([anomaly_depths, anomaly_diameters]))
            else:
                self.anomaly_scatter.set_offsets(np.empty((0, 2)))
                
            # 自动缩放
            if self.auto_scale:
                self._auto_scale_axes()
                
            # 更新公差带
            if self.show_tolerance_lines and hasattr(self, 'tolerance_fill'):
                x_min, x_max = self.ax.get_xlim()
                self.tolerance_fill.remove()
                self.tolerance_fill = self.ax.fill_between([x_min, x_max], 
                                                         self.standard_diameter - self.tolerance,
                                                         self.standard_diameter + self.tolerance,
                                                         alpha=0.1, color='green',
                                                         label='公差带')
                
            # 重绘
            self.canvas.draw()
            
        except Exception as e:
            self.logger.error(f"更新图表失败: {e}")
            
    def _auto_scale_axes(self):
        """自动缩放坐标轴"""
        if len(self.depth_data) == 0:
            return
            
        # X轴：深度
        x_min, x_max = min(self.depth_data), max(self.depth_data)
        x_margin = (x_max - x_min) * 0.05 if x_max > x_min else 1
        self.ax.set_xlim(x_min - x_margin, x_max + x_margin)
        
        # Y轴：直径
        y_min, y_max = min(self.diameter_data), max(self.diameter_data)
        y_margin = (y_max - y_min) * 0.1 if y_max > y_min else 0.1
        
        # 确保公差带可见
        if self.show_tolerance_lines:
            y_min = min(y_min, self.standard_diameter - self.tolerance - 0.1)
            y_max = max(y_max, self.standard_diameter + self.tolerance + 0.1)
            
        self.ax.set_ylim(y_min - y_margin, y_max + y_margin)
        
    def _update_status_bar(self):
        """更新状态栏"""
        data_count = len(self.depth_data)
        anomaly_count = len(self.anomaly_points)
        zoom_percent = int(self._zoom_level * 100)
        
        self.data_count_label.setText(f"数据点: {data_count}")
        self.anomaly_count_label.setText(f"异常: {anomaly_count}")
        self.zoom_label.setText(f"缩放: {zoom_percent}%")
        
    @Slot()
    def start_monitoring(self):
        """开始监测"""
        self.update_timer.start(self.update_interval)
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText("监测中...")
        self.logger.info("开始实时监测")
        
    @Slot()
    def stop_monitoring(self):
        """停止监测"""
        self.update_timer.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("已停止")
        self.logger.info("停止实时监测")
        
    @Slot()
    def clear_data(self):
        """清除所有数据"""
        self.depth_data.clear()
        self.diameter_data.clear()
        self.time_data.clear()
        self.anomaly_points.clear()
        
        self._update_chart()
        self._update_status_bar()
        self.status_label.setText("数据已清除")
        self.logger.info("清除所有数据")
        
    @Slot()
    def _export_data(self):
        """导出数据"""
        if len(self.depth_data) == 0:
            self.status_label.setText("无数据可导出")
            return
            
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chart_data_{timestamp}.csv"
            
            self.export_requested.emit(filename)
            self.status_label.setText(f"数据已导出: {filename}")
            
        except Exception as e:
            self.logger.error(f"导出数据失败: {e}")
            self.status_label.setText("导出失败")
            
    @Slot()
    def _toggle_auto_scale(self):
        """切换自动缩放"""
        self.auto_scale = self.auto_scale_button.isChecked()
        if self.auto_scale:
            self._auto_scale_axes()
            self.canvas.draw()
            
    @Slot()
    def _toggle_tolerance_lines(self):
        """切换公差线显示"""
        self.show_tolerance_lines = self.tolerance_button.isChecked()
        
        # 移除现有的公差线
        if hasattr(self, 'std_line'):
            self.std_line.remove()
            self.upper_line.remove()
            self.lower_line.remove()
            self.tolerance_fill.remove()
            
        # 重新设置
        if self.show_tolerance_lines:
            self._setup_tolerance_lines()
            
        self.ax.legend(loc='upper right')
        self.canvas.draw()
        
    def _update_chart_animation(self):
        """动画更新图表"""
        if self.animation_enabled:
            self._update_chart()
            
    # 鼠标交互事件
    def _on_mouse_press(self, event):
        """鼠标按下事件"""
        if event.button == 1:  # 左键
            self._is_panning = True
            self._pan_start = (event.xdata, event.ydata)
            
    def _on_mouse_release(self, event):
        """鼠标释放事件"""
        if event.button == 1:  # 左键
            self._is_panning = False
            self._pan_start = None
            
    def _on_mouse_move(self, event):
        """鼠标移动事件"""
        if self._is_panning and self._pan_start and event.xdata and event.ydata:
            dx = self._pan_start[0] - event.xdata
            dy = self._pan_start[1] - event.ydata
            
            x_min, x_max = self.ax.get_xlim()
            y_min, y_max = self.ax.get_ylim()
            
            self.ax.set_xlim(x_min + dx, x_max + dx)
            self.ax.set_ylim(y_min + dy, y_max + dy)
            
            self.canvas.draw()
            
    def _on_scroll(self, event):
        """滚轮缩放事件"""
        if event.xdata and event.ydata:
            scale_factor = 1.1 if event.step > 0 else 1 / 1.1
            
            x_min, x_max = self.ax.get_xlim()
            y_min, y_max = self.ax.get_ylim()
            
            x_center = event.xdata
            y_center = event.ydata
            
            x_range = (x_max - x_min) * scale_factor
            y_range = (y_max - y_min) * scale_factor
            
            self.ax.set_xlim(x_center - x_range/2, x_center + x_range/2)
            self.ax.set_ylim(y_center - y_range/2, y_center + y_range/2)
            
            self._zoom_level *= scale_factor
            self._update_status_bar()
            self.canvas.draw()
            
    # 配置方法
    def set_standard_diameter(self, diameter: float, tolerance: float):
        """设置标准直径和公差"""
        self.standard_diameter = diameter
        self.tolerance = tolerance
        
        # 更新公差线
        if self.show_tolerance_lines:
            self._toggle_tolerance_lines()
            self._toggle_tolerance_lines()
            
        self.logger.debug(f"设置标准直径: {diameter}±{tolerance}mm")
        
    def set_update_interval(self, interval_ms: int):
        """设置更新间隔"""
        self.update_interval = max(50, interval_ms)
        if self.update_timer.isActive():
            self.update_timer.stop()
            self.update_timer.start(self.update_interval)
            
    def get_data_summary(self) -> Dict[str, Any]:
        """获取数据摘要"""
        if len(self.diameter_data) == 0:
            return {}
            
        diameters = list(self.diameter_data)
        return {
            'count': len(diameters),
            'mean': np.mean(diameters),
            'std': np.std(diameters),
            'min': np.min(diameters),
            'max': np.max(diameters),
            'anomaly_count': len(self.anomaly_points),
            'anomaly_rate': len(self.anomaly_points) / len(diameters) * 100
        }