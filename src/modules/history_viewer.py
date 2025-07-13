"""
3.1页面 - 光谱共焦历史数据查看器
允许操作员查询、审查任一已检测孔的光谱共焦内径测量历史数据
"""

import numpy as np
import matplotlib
# 修复后端问题 - 使用PySide6兼容的后端
import threading
try:
    # 如果不是主线程，强制使用Agg后端
    if threading.current_thread() != threading.main_thread():
        matplotlib.use('Agg')
    else:
        matplotlib.use('Qt5Agg')  # 首选Qt5Agg
except ImportError:
    try:
        matplotlib.use('TkAgg')  # 备选TkAgg
    except ImportError:
        matplotlib.use('Agg')  # 最后使用Agg（无GUI）

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 使用统一的字体配置模块
try:
    from .font_config import configure_matplotlib_for_chinese, suppress_font_warnings
    # 配置中文字体并抑制警告
    suppress_font_warnings()
    CHINESE_FONT = configure_matplotlib_for_chinese()
except ImportError:
    # 如果字体配置模块不可用，使用基本配置
    CHINESE_FONT = 'Arial Unicode MS'
    plt.rcParams['font.sans-serif'] = [CHINESE_FONT, 'SimHei', 'Microsoft YaHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

import os
import platform

# 修复matplotlib后端导入
try:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
except ImportError:
    try:
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigureCanvas
    except ImportError:
        from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from scipy.optimize import least_squares
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QLabel, QPushButton, QLineEdit, QComboBox,
                               QGroupBox, QTableWidget, QTableWidgetItem,
                               QSplitter, QTextEdit, QMessageBox, QFileDialog,
                               QDialog, QFormLayout, QDoubleSpinBox, QDialogButtonBox,
                               QScrollArea, QFrame, QTabWidget)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import csv
import os
import glob
from datetime import datetime

from .models import db_manager

# 导入三维模型渲染器
try:
    from .hole_3d_renderer import Hole3DViewer
    HAS_3D_RENDERER = True
except ImportError:
    HAS_3D_RENDERER = False
    print("警告: 三维模型渲染器不可用")


class ProbeCircleFitter:
    """基于探头测量的拟合圆算法 - 根据matlab代码实现"""

    @staticmethod
    def circle_from_polar(p1, p2, p3):
        """
        根据三个极坐标点拟合圆
        p1, p2, p3: [r, theta] 格式的极坐标点
        返回: (xc, yc, D) - 圆心坐标和直径
        """
        # 将极坐标转换为直角坐标
        x1 = p1[0] * np.cos(p1[1])
        y1 = p1[0] * np.sin(p1[1])
        x2 = p2[0] * np.cos(p2[1])
        y2 = p2[0] * np.sin(p2[1])
        x3 = p3[0] * np.cos(p3[1])
        y3 = p3[0] * np.sin(p3[1])

        # 计算分母
        D = 2 * (x1*(y2 - y3) + x2*(y3 - y1) + x3*(y1 - y2))

        if abs(D) < 1e-10:
            raise ValueError("三点共线，无法拟合圆")

        # 计算平方和
        x1s = x1**2 + y1**2
        x2s = x2**2 + y2**2
        x3s = x3**2 + y3**2

        # 计算圆心坐标
        xc = (x1s*(y2 - y3) + x2s*(y3 - y1) + x3s*(y1 - y2)) / D
        yc = (x1s*(x3 - x2) + x2s*(x1 - x3) + x3s*(x2 - x1)) / D

        # 计算半径和直径
        R = np.sqrt((x1 - xc)**2 + (y1 - yc)**2)
        diameter = 2 * R

        return xc, yc, diameter

    @staticmethod
    def process_channel_data(measure_list, probe_r=18.85, probe_small_r=4):
        """
        处理通道数据，计算拟合圆
        measure_list: [channel1, channel2, channel3] 三个通道的测量值
        probe_r: 探头主圆半径 (mm)
        probe_small_r: 子探头小圆半径 (mm)
        返回: 拟合结果字典
        """
        if len(measure_list) != 3:
            raise ValueError("需要三个通道的测量数据")

        # 三个子探头的方向角度
        theta_list = [0, 2*np.pi/3, 4*np.pi/3]

        # 构建三个极坐标点
        p1 = [probe_r + measure_list[0], theta_list[0]]
        p2 = [probe_r + measure_list[1], theta_list[1]]
        p3 = [probe_r + measure_list[2], theta_list[2]]

        # 拟合圆
        xc, yc, diameter = ProbeCircleFitter.circle_from_polar(p1, p2, p3)
        radius = diameter / 2

        return {
            'center_x': xc,
            'center_y': yc,
            'diameter': diameter,
            'radius': radius,
            'measure_points': [p1, p2, p3],
            'probe_r': probe_r,
            'probe_small_r': probe_small_r,
            'theta_list': theta_list
        }


class CircleFitter:
    """圆形拟合算法"""

    @staticmethod
    def fit_circle(x, y):
        """
        使用最小二乘法拟合圆
        返回: (center_x, center_y, radius, residual)
        """
        def calc_R(xc, yc):
            """计算到圆心的距离"""
            return np.sqrt((x - xc)**2 + (y - yc)**2)

        def f_2(c):
            """目标函数"""
            Ri = calc_R(*c)
            return Ri - Ri.mean()

        # 初始估计
        x_m = np.mean(x)
        y_m = np.mean(y)
        center_estimate = x_m, y_m

        # 拟合
        center_2, _ = least_squares(f_2, center_estimate).x, _
        xc_2, yc_2 = center_2
        Ri_2 = calc_R(*center_2)
        R_2 = Ri_2.mean()
        residual = np.sum((Ri_2 - R_2)**2)

        return xc_2, yc_2, R_2, residual

    @staticmethod
    def generate_circle_points(center_x, center_y, radius, num_points=100):
        """生成圆的点坐标"""
        theta = np.linspace(0, 2*np.pi, num_points)
        x = center_x + radius * np.cos(theta)
        y = center_y + radius * np.sin(theta)
        return x, y


class HistoryDataPlot(FigureCanvas):
    """历史数据绘图组件"""

    def __init__(self, parent=None):
        self.figure = Figure(figsize=(12, 8))
        super().__init__(self.figure)
        self.setParent(parent)

        # 设置图表的默认字体
        self.figure.patch.set_facecolor('white')

        # 创建一个占满整个区域的坐标图
        self.ax = self.figure.add_subplot(111)  # 单个坐标图占满整个区域

        # 启用鼠标滚轮缩放
        self.setup_mouse_interaction()

        # 初始化时显示空的坐标图
        self.init_empty_plot()

        self.figure.tight_layout(pad=3.0)

    def setup_mouse_interaction(self):
        """设置鼠标交互功能"""
        # 连接鼠标滚轮事件
        self.mpl_connect('scroll_event', self.on_scroll)

    def on_scroll(self, event):
        """鼠标滚轮缩放事件处理"""
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

    def init_empty_plot(self):
        """初始化空的二维公差带包络图"""
        # 设置坐标图为深度-直径关系图
        self.ax.clear()
        self.ax.set_xlim(0, 1000)  # 深度范围 0-1000mm
        self.ax.set_ylim(17.0, 18.0)  # 直径范围，围绕标准直径17.6mm
        self.ax.set_xlabel('深度 (mm)')
        self.ax.set_ylabel('直径 (mm)')
        self.ax.set_title('二维公差带包络图')
        self.ax.grid(True, alpha=0.3)
        # 移除等比例设置，允许X轴和Y轴有不同的比例
        self.draw()

    def plot_measurement_data(self, measurements, hole_info):
        """绘制二维公差带包络图"""
        if not measurements:
            self.init_empty_plot()
            return

        # 清除当前图表
        self.ax.clear()

        # 提取深度和直径数据
        depths = []
        diameters = []

        for measurement in measurements:
            # 获取深度（位置）
            depth = measurement.get('position', measurement.get('depth', 0))
            # 获取直径
            diameter = measurement.get('diameter', 0)

            depths.append(depth)
            diameters.append(diameter)

        if not depths or not diameters:
            self.init_empty_plot()
            return

        # 转换为numpy数组
        depths = np.array(depths)
        diameters = np.array(diameters)

        # 标准直径和公差
        standard_diameter = 17.6  # mm
        upper_tolerance = 0.05    # +0.05mm
        lower_tolerance = -0.07   # -0.07mm

        # 绘制公差带曲线
        depth_range = np.linspace(min(depths), max(depths), 100)

        # 上公差线 (标准直径 + 0.05mm)
        upper_line = np.full_like(depth_range, standard_diameter + upper_tolerance)
        self.ax.plot(depth_range, upper_line, 'r--', linewidth=2,
                    label=f'上公差线 ({standard_diameter + upper_tolerance:.2f}mm)')

        # 下公差线 (标准直径 - 0.07mm)
        lower_line = np.full_like(depth_range, standard_diameter + lower_tolerance)
        self.ax.plot(depth_range, lower_line, 'r--', linewidth=2,
                    label=f'下公差线 ({standard_diameter + lower_tolerance:.2f}mm)')

        # 标准直径线
        standard_line = np.full_like(depth_range, standard_diameter)
        self.ax.plot(depth_range, standard_line, 'g-', linewidth=1.5, alpha=0.7,
                    label=f'标准直径 ({standard_diameter:.1f}mm)')

        # 绘制测量数据曲线
        self.ax.plot(depths, diameters, 'b-', linewidth=2, marker='o',
                    markersize=3, label='测量数据')

        # 标记超出公差的点
        for i, (depth, diameter) in enumerate(zip(depths, diameters)):
            if diameter > standard_diameter + upper_tolerance or diameter < standard_diameter + lower_tolerance:
                self.ax.plot(depth, diameter, 'ro', markersize=5, alpha=0.8)

        # 设置坐标轴
        self.ax.set_xlabel('深度 (mm)', fontsize=12)
        self.ax.set_ylabel('直径 (mm)', fontsize=12)
        self.ax.set_title('二维公差带包络图', fontsize=14, fontweight='bold')

        # 设置坐标轴范围
        depth_margin = (max(depths) - min(depths)) * 0.05
        diameter_margin = (max(diameters) - min(diameters)) * 0.1

        self.ax.set_xlim(min(depths) - depth_margin, max(depths) + depth_margin)

        # Y轴范围要包含公差带
        y_min = min(min(diameters), standard_diameter + lower_tolerance) - diameter_margin
        y_max = max(max(diameters), standard_diameter + upper_tolerance) + diameter_margin
        self.ax.set_ylim(y_min, y_max)

        # 设置网格和图例
        self.ax.grid(True, alpha=0.3)
        self.ax.legend(loc='best', fontsize=10)

        # 刷新画布
        self.draw()



    def plot_statistics(self, diameters, target_diameter=17.6, upper_tolerance=0.05, lower_tolerance=0.07):
        """在二维图表上显示统计信息"""
        if not diameters:
            return

        # 计算统计量
        mean_diameter = np.mean(diameters)
        std_diameter = np.std(diameters)
        min_diameter = np.min(diameters)
        max_diameter = np.max(diameters)

        # 合格率（使用非对称公差）
        qualified_count = sum(1 for d in diameters
                            if target_diameter - lower_tolerance <= d <= target_diameter + upper_tolerance)
        qualification_rate = qualified_count / len(diameters) * 100

        # 创建统计文本
        stats_text = f"""统计信息:

测量点数: {len(diameters)}
平均直径: {mean_diameter:.3f} mm
标准偏差: {std_diameter:.3f} mm
最小值: {min_diameter:.3f} mm
最大值: {max_diameter:.3f} mm

标准直径: {target_diameter:.1f} mm
公差范围: -{lower_tolerance:.2f}/+{upper_tolerance:.2f} mm
合格点数: {qualified_count}
合格率: {qualification_rate:.1f}%

偏差统计:
平均偏差: {mean_diameter - target_diameter:.3f} mm
最大正偏差: {max_diameter - target_diameter:.3f} mm
最大负偏差: {min_diameter - target_diameter:.3f} mm"""

        # 清除之前的统计信息
        if hasattr(self, '_stats_text_box'):
            self._stats_text_box.remove()

        # 在图表左上角添加统计信息文本框（避免与图例重叠）
        self._stats_text_box = self.ax.text(0.02, 0.98, stats_text,
                                           transform=self.ax.transAxes,
                                           fontsize=9, verticalalignment='top',
                                           horizontalalignment='left',
                                           bbox=dict(boxstyle='round,pad=0.5',
                                                   facecolor='lightblue',
                                                   alpha=0.8))

    def clear_plots(self):
        """清除图表"""
        self.ax.clear()
        # 清除统计信息文本框
        if hasattr(self, '_stats_text_box'):
            delattr(self, '_stats_text_box')


class HistoryViewer(QWidget):
    """历史数据查看器 - 3.1页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_hole_data = None
        self.circle_plot_index = 0  # 用于跟踪当前绘制拟合圆的子图索引 (0-3)
        self.setup_ui()
        self.load_workpiece_list()

    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)

        # 标题
        title_label = QLabel("光谱共焦历史数据查看器")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)

        # 查询面板
        self.create_query_panel(layout)

        # 主内容区域
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：数据表格
        self.create_data_table(splitter)

        # 右侧：标签页显示（二维图表和三维模型）
        self.create_visualization_tabs(splitter)

        # 设置分割器比例
        splitter.setSizes([300, 700])
        layout.addWidget(splitter)

    def create_visualization_tabs(self, parent):
        """创建可视化标签页（二维图表和三维模型）"""
        # 创建标签页控件
        tab_widget = QTabWidget()

        # 二维图表标签页
        self.plot_widget = HistoryDataPlot()
        tab_widget.addTab(self.plot_widget, "二维公差带图表")

        # 三维模型标签页
        if HAS_3D_RENDERER:
            self.model_3d_viewer = Hole3DViewer()
            tab_widget.addTab(self.model_3d_viewer, "三维模型渲染")
        else:
            # 如果三维渲染器不可用，显示提示
            placeholder = QLabel("三维模型渲染器不可用\n请检查相关依赖")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("color: #666; font-size: 14px;")
            tab_widget.addTab(placeholder, "三维模型渲染")

        parent.addWidget(tab_widget)

    def create_query_panel(self, layout):
        """创建查询面板"""
        query_group = QGroupBox("查询条件")
        query_layout = QGridLayout(query_group)

        # 设置列间距为较小值，减少标签和下拉框之间的间隔
        query_layout.setHorizontalSpacing(8)   # 设置水平间距为8像素
        query_layout.setVerticalSpacing(10)    # 设置垂直间距为10像素
        query_layout.setContentsMargins(10, 10, 10, 10)  # 设置内边距

        # 将所有控件排列在一行中，从左到右依次为：
        # 工件ID → 合格孔ID → 不合格孔ID → 查询数据 → 导出数据

        # 工件ID
        query_layout.addWidget(QLabel("工件ID:"), 0, 0)
        self.workpiece_combo = QComboBox()
        self.workpiece_combo.setFixedSize(120, 30)  # 调整宽度以显示完整文本
        self.workpiece_combo.currentTextChanged.connect(self.on_workpiece_changed)
        query_layout.addWidget(self.workpiece_combo, 0, 1)

        # 合格管孔ID选择
        query_layout.addWidget(QLabel("合格孔ID:"), 0, 2)
        self.qualified_hole_combo = QComboBox()
        self.qualified_hole_combo.setFixedSize(140, 30)  # 调整宽度以显示完整默认文本
        self.qualified_hole_combo.setEditable(False)  # 改为不可编辑，与工件ID样式一致
        self.qualified_hole_combo.setPlaceholderText("请选择合格孔ID")  # 设置默认文本
        self.qualified_hole_combo.currentTextChanged.connect(self.on_qualified_hole_changed)
        query_layout.addWidget(self.qualified_hole_combo, 0, 3)

        # 不合格管孔ID选择
        query_layout.addWidget(QLabel("不合格孔ID:"), 0, 4)
        self.unqualified_hole_combo = QComboBox()
        self.unqualified_hole_combo.setFixedSize(140, 30)  # 调整宽度以显示完整默认文本
        self.unqualified_hole_combo.setEditable(False)  # 改为不可编辑，与工件ID样式一致
        self.unqualified_hole_combo.setPlaceholderText("请选择不合格孔ID")  # 设置默认文本
        self.unqualified_hole_combo.currentTextChanged.connect(self.on_unqualified_hole_changed)
        query_layout.addWidget(self.unqualified_hole_combo, 0, 5)

        # 查询按钮
        self.query_button = QPushButton("查询数据")
        self.query_button.setFixedSize(80, 30)  # 设置固定大小
        self.query_button.clicked.connect(self.query_data)
        query_layout.addWidget(self.query_button, 0, 6)

        # 导出按钮
        self.export_button = QPushButton("导出数据")
        self.export_button.setFixedSize(80, 30)  # 设置与查询按钮相同的大小
        self.export_button.clicked.connect(self.export_data)
        query_layout.addWidget(self.export_button, 0, 7)

        # 人工复查按钮
        self.manual_review_button = QPushButton("人工复查")
        self.manual_review_button.setFixedSize(80, 30)  # 设置与其他按钮相同的大小
        self.manual_review_button.clicked.connect(self.open_manual_review)
        query_layout.addWidget(self.manual_review_button, 0, 8)

        # 当前管孔ID显示标签
        self.current_hole_label = QLabel("当前管孔: --")
        self.current_hole_label.setStyleSheet("font-weight: bold; color: #1976d2; margin-left: 10px;")
        query_layout.addWidget(self.current_hole_label, 0, 9)

        # 设置列的拉伸因子，让标签列和按钮列不拉伸
        query_layout.setColumnStretch(0, 0)  # 工件ID标签列不拉伸
        query_layout.setColumnStretch(1, 0)  # 工件ID下拉框列不拉伸
        query_layout.setColumnStretch(2, 0)  # 合格孔ID标签列不拉伸
        query_layout.setColumnStretch(3, 0)  # 合格孔ID下拉框列不拉伸
        query_layout.setColumnStretch(4, 0)  # 不合格孔ID标签列不拉伸
        query_layout.setColumnStretch(5, 0)  # 不合格孔ID下拉框列不拉伸
        query_layout.setColumnStretch(6, 0)  # 查询按钮列不拉伸
        query_layout.setColumnStretch(7, 0)  # 导出按钮列不拉伸
        query_layout.setColumnStretch(8, 0)  # 人工复查按钮列不拉伸
        query_layout.setColumnStretch(9, 0)  # 当前管孔ID标签列不拉伸
        query_layout.setColumnStretch(10, 1)  # 添加一个空白拉伸列，让内容左对齐

        layout.addWidget(query_group)

    def create_data_table(self, splitter):
        """创建数据表格"""
        table_group = QGroupBox("测量数据")
        table_layout = QVBoxLayout(table_group)

        self.data_table = QTableWidget()
        self.data_table.setColumnCount(9)
        self.data_table.setHorizontalHeaderLabels([
            "位置(mm)", "直径(mm)", "通道1值(μm)", "通道2值(μm)", "通道3值(μm)", "合格", "时间", "操作员", "备注"
        ])

        # 设置表格属性
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.data_table.setSortingEnabled(True)

        # 禁用表格编辑
        self.data_table.setEditTriggers(QTableWidget.NoEditTriggers)

        # 连接双击事件
        self.data_table.cellDoubleClicked.connect(self.on_table_double_clicked)

        table_layout.addWidget(self.data_table)
        splitter.addWidget(table_group)

    def load_workpiece_list(self):
        """加载工件列表"""
        # 这里简化为添加默认工件
        self.workpiece_combo.addItem("WP-2025-001")
        self.on_workpiece_changed("WP-2025-001")

    def on_workpiece_changed(self, workpiece_id):
        """工件选择改变"""
        if not workpiece_id:
            return

        # 加载对应工件的孔位列表
        self.load_hole_list(workpiece_id)

    def load_hole_list(self, workpiece_id):
        """加载指定工件的孔位列表"""
        print(f"🔍 加载工件 {workpiece_id} 的孔位列表...")

        # 清空当前孔位选项
        self.qualified_hole_combo.clear()
        self.unqualified_hole_combo.clear()

        # 获取可用的孔位列表
        available_holes = self.get_available_holes(workpiece_id)

        if available_holes:
            # 分类孔位为合格和不合格
            qualified_holes, unqualified_holes = self.classify_holes_by_quality(available_holes)

            # 添加合格孔位选项到下拉框
            if qualified_holes:
                self.qualified_hole_combo.addItem("请选择合格孔ID")  # 添加默认选项
                self.qualified_hole_combo.addItems(qualified_holes)
                self.qualified_hole_combo.setCurrentIndex(0)  # 设置默认选项为当前选择
                print(f"✅ 加载了 {len(qualified_holes)} 个合格孔位: {', '.join(qualified_holes)}")

            # 添加不合格孔位选项到下拉框
            if unqualified_holes:
                self.unqualified_hole_combo.addItem("请选择不合格孔ID")  # 添加默认选项
                self.unqualified_hole_combo.addItems(unqualified_holes)
                self.unqualified_hole_combo.setCurrentIndex(0)  # 设置默认选项为当前选择
                print(f"✅ 加载了 {len(unqualified_holes)} 个不合格孔位: {', '.join(unqualified_holes)}")

            print(f"✅ 总计加载了 {len(available_holes)} 个孔位")
        else:
            print("⚠️ 未找到可用的孔位")

        # 更新占位符文本
        self.qualified_hole_combo.setPlaceholderText(f"请选择{workpiece_id}的合格孔ID")
        self.unqualified_hole_combo.setPlaceholderText(f"请选择{workpiece_id}的不合格孔ID")

    def get_available_holes(self, workpiece_id):
        """获取可用的孔位列表"""
        available_holes = []

        try:
            # 方法1: 从数据库获取孔位
            from .models import db_manager
            db_holes = db_manager.get_workpiece_holes(workpiece_id)
            if db_holes:
                for hole in db_holes:
                    available_holes.append(hole.hole_id)
                print(f"📊 从数据库获取到 {len(db_holes)} 个孔位")
        except Exception as e:
            print(f"⚠️ 数据库查询失败: {e}")

        # 方法2: 从文件系统扫描孔位目录
        data_base_dir = "Data"
        if os.path.exists(data_base_dir):
            for item in os.listdir(data_base_dir):
                item_path = os.path.join(data_base_dir, item)
                if os.path.isdir(item_path) and item.startswith('H'):
                    # 检查是否有CCIDM目录（测量数据）
                    ccidm_path = os.path.join(item_path, "CCIDM")
                    if os.path.exists(ccidm_path):
                        csv_files = [f for f in os.listdir(ccidm_path) if f.endswith('.csv')]
                        if csv_files:
                            if item not in available_holes:
                                available_holes.append(item)

            print(f"📁 从文件系统扫描到 {len([h for h in available_holes if h.startswith('H')])} 个孔位目录")

        # 如果没有找到任何孔位，提供默认选项
        if not available_holes:
            available_holes = ["H00001", "H00002", "H00003", "H00004", "H00005"]
            print("🔧 使用默认孔位列表")

        # 排序孔位列表
        available_holes.sort()

        return available_holes

    def classify_holes_by_quality(self, available_holes):
        """根据测量数据将孔位分类为合格和不合格"""
        qualified_holes = []
        unqualified_holes = []

        # 根据用户要求，H00001和H00002是合格的，H00003是不合格的
        predefined_qualified = ["H00001", "H00002"]
        predefined_unqualified = ["H00003"]

        for hole_id in available_holes:
            if hole_id in predefined_qualified:
                qualified_holes.append(hole_id)
            elif hole_id in predefined_unqualified:
                unqualified_holes.append(hole_id)
            else:
                # 对于其他孔位，通过实际测量数据判断
                if self.is_hole_qualified(hole_id):
                    qualified_holes.append(hole_id)
                else:
                    unqualified_holes.append(hole_id)

        return qualified_holes, unqualified_holes

    def is_hole_qualified(self, hole_id):
        """判断管孔是否合格"""
        try:
            # 加载孔位的测量数据
            measurements = self.load_csv_data_for_hole(hole_id)
            if not measurements:
                print(f"⚠️ 孔位 {hole_id} 无测量数据")
                return False

            # 计算合格率
            qualified_count = 0
            total_count = len(measurements)

            for measurement in measurements:
                if measurement.get('qualified', False):
                    qualified_count += 1

            qualified_rate = qualified_count / total_count * 100
            print(f"📊 孔位 {hole_id} 合格率: {qualified_rate:.1f}% ({qualified_count}/{total_count})")

            # 合格率大于等于95%认为合格
            return qualified_rate >= 95.0

        except Exception as e:
            print(f"❌ 判断孔位 {hole_id} 合格性失败: {e}")
            return False

    def on_qualified_hole_changed(self, hole_id):
        """合格孔位选择改变事件"""
        if hole_id and hole_id != "请选择合格孔ID":
            # 清空不合格孔位选择，恢复默认显示状态
            self.unqualified_hole_combo.blockSignals(True)  # 阻止信号避免循环调用
            self.unqualified_hole_combo.setCurrentIndex(0)  # 设置为默认选项
            self.unqualified_hole_combo.blockSignals(False)
            print(f"🟢 选择合格孔位: {hole_id}")

    def on_unqualified_hole_changed(self, hole_id):
        """不合格孔位选择改变事件"""
        if hole_id and hole_id != "请选择不合格孔ID":
            # 清空合格孔位选择，恢复默认显示状态
            self.qualified_hole_combo.blockSignals(True)  # 阻止信号避免循环调用
            self.qualified_hole_combo.setCurrentIndex(0)  # 设置为默认选项
            self.qualified_hole_combo.blockSignals(False)
            print(f"🔴 选择不合格孔位: {hole_id}")

    def query_data(self):
        """查询数据"""
        print("🔍 开始查询数据...")

        workpiece_id = self.workpiece_combo.currentText()

        # 从两个下拉框中获取选择的孔位（只有一个会有值）
        qualified_hole_id = self.qualified_hole_combo.currentText().strip()
        unqualified_hole_id = self.unqualified_hole_combo.currentText().strip()

        # 确定要查询的孔位ID（排除默认文本）
        hole_id = ""
        if qualified_hole_id and qualified_hole_id != "" and qualified_hole_id != "请选择合格孔ID":
            hole_id = qualified_hole_id
        elif unqualified_hole_id and unqualified_hole_id != "" and unqualified_hole_id != "请选择不合格孔ID":
            hole_id = unqualified_hole_id

        print(f"📋 查询参数: 工件ID='{workpiece_id}', 合格孔ID='{qualified_hole_id}', 不合格孔ID='{unqualified_hole_id}', 选择的孔ID='{hole_id}'")

        if not workpiece_id:
            print("❌ 工件ID未选择")
            QMessageBox.warning(self, "警告", "请选择工件ID")
            return

        if not hole_id:
            print("❌ 孔ID未选择")
            QMessageBox.warning(self, "警告", "请选择合格孔ID或不合格孔ID")
            return

        # 验证孔ID格式（应该以H开头）
        if not hole_id.upper().startswith('H'):
            print("❌ 孔ID格式错误")
            QMessageBox.warning(self, "警告", "孔ID格式错误，请输入以H开头的孔ID，如：H001")
            return

        print("🔍 开始加载CSV数据...")
        # 从CSV文件加载数据
        measurements = self.load_csv_data_for_hole(hole_id)

        print(f"📊 CSV加载结果: {len(measurements) if measurements else 0} 条数据")

        if not measurements:
            print("❌ 没有找到数据")
            QMessageBox.information(self, "信息", f"孔 {hole_id} 没有找到对应的CSV数据文件")
            self.clear_display()
            return

        try:
            print("🔍 开始更新显示...")
            # 更新显示
            self.update_data_table(measurements)
            print("✅ 数据表格更新成功")

            self.plot_widget.plot_measurement_data(measurements, {})
            print("✅ 图表更新成功")

            # 更新三维模型
            if HAS_3D_RENDERER and hasattr(self, 'model_3d_viewer'):
                self.model_3d_viewer.update_models(measurements)
                print("✅ 三维模型更新成功")

            print("🔍 设置current_hole_data...")
            self.current_hole_data = {
                'workpiece_id': workpiece_id,
                'hole_id': hole_id,
                'measurements': measurements,
                'hole_info': {}
            }

            # 更新当前管孔ID显示
            self.update_current_hole_display(hole_id)

            print(f"✅ 查询数据成功: 工件ID={workpiece_id}, 孔ID={hole_id}")
            print(f"📊 加载了 {len(measurements)} 条测量数据")
            print(f"🔍 current_hole_data 已设置: {self.current_hole_data is not None}")
            print(f"🔍 current_hole_data 内容: {list(self.current_hole_data.keys()) if self.current_hole_data else 'None'}")

        except Exception as e:
            print(f"❌ 更新显示时出错: {e}")
            import traceback
            traceback.print_exc()

            # 即使图表更新失败，也要设置current_hole_data以支持双击功能
            print("🔍 设置current_hole_data（忽略图表错误）...")
            self.current_hole_data = {
                'workpiece_id': workpiece_id,
                'hole_id': hole_id,
                'measurements': measurements,
                'hole_info': {}
            }
            print(f"✅ current_hole_data 已设置: {self.current_hole_data is not None}")

            QMessageBox.warning(self, "警告", f"数据加载成功，但图表显示出错: {str(e)}")
            return

    def load_csv_data_for_hole(self, hole_id):
        """根据孔ID加载对应的CSV数据"""
        # 修复路径问题：使用相对路径查找CSV文件
        csv_paths = [
            f"Data/{hole_id}/CCIDM",
            f"data/{hole_id}/CCIDM",
            f"cache/{hole_id}",
            f"Data/{hole_id}",
            f"data/{hole_id}"
        ]

        csv_files = []
        csv_dir = None

        # 查找存在的CSV目录
        for path in csv_paths:
            if os.path.exists(path):
                csv_dir = path
                # 查找CSV文件
                for csv_file in os.listdir(path):
                    if csv_file.endswith('.csv'):
                        csv_files.append(os.path.join(path, csv_file))
                if csv_files:
                    break

        if not csv_files:
            print(f"CSV数据目录不存在或无CSV文件，已检查路径: {csv_paths}")
            return []

        # 按时间排序
        csv_files.sort()

        # 选择第一个CSV文件（通常每个孔位只有一个CSV文件）
        selected_file = csv_files[0]
        print(f"为孔ID {hole_id} 选择文件: {selected_file}")

        # 读取CSV文件数据
        return self.read_csv_file(selected_file)

    def read_csv_file(self, file_path):
        """读取CSV文件并返回测量数据"""
        measurements = []

        try:
            # 尝试不同的编码
            encodings = ['gbk', 'gb2312', 'utf-8', 'latin-1']

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        reader = csv.reader(file)
                        headers = next(reader)

                        print(f"成功使用编码 {encoding} 读取文件")
                        print(f"CSV文件列头: {headers}")

                        # 查找列索引 - 根据实际CSV文件结构调整
                        measurement_col = 0  # 第一列是测量序号
                        channel1_col = 1     # 通道1值
                        channel2_col = 2     # 通道2值
                        channel3_col = 3     # 通道3值
                        diameter_col = 4     # 计算直径

                        # 验证列数是否足够
                        if len(headers) < 5:
                            print(f"CSV文件列数不足: {len(headers)} < 5")
                            continue

                        # 读取数据行 - 在同一个with块中
                        for row_num, row in enumerate(reader, start=2):
                            try:
                                if len(row) > max(measurement_col, diameter_col, channel1_col, channel2_col, channel3_col):
                                    position = float(row[measurement_col])  # 测量序号对应位置(mm)
                                    diameter = float(row[diameter_col])
                                    channel1 = float(row[channel1_col])
                                    channel2 = float(row[channel2_col])
                                    channel3 = float(row[channel3_col])

                                    # 判断是否合格（标准直径17.6mm，非对称公差+0.05/-0.07mm）
                                    standard_diameter = 17.6
                                    upper_tolerance = 0.05
                                    lower_tolerance = 0.07
                                    is_qualified = (standard_diameter - lower_tolerance <= diameter <= standard_diameter + upper_tolerance)

                                    # 模拟时间（基于文件修改时间）
                                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                                    # 为每个数据点添加秒数偏移，正确处理分钟进位
                                    total_seconds = file_time.second + (row_num - 2)
                                    additional_minutes = total_seconds // 60
                                    new_seconds = total_seconds % 60

                                    # 计算新的分钟数，也要处理小时进位
                                    total_minutes = file_time.minute + additional_minutes
                                    additional_hours = total_minutes // 60
                                    new_minutes = total_minutes % 60

                                    # 计算新的小时数
                                    new_hours = (file_time.hour + additional_hours) % 24

                                    data_time = file_time.replace(hour=new_hours, minute=new_minutes, second=new_seconds)

                                    measurements.append({
                                        'position': position,
                                        'diameter': diameter,
                                        'channel1': channel1,
                                        'channel2': channel2,
                                        'channel3': channel3,
                                        'is_qualified': is_qualified,
                                        'timestamp': data_time,
                                        'operator': ''  # 暂不显示
                                    })

                            except (ValueError, IndexError) as e:
                                print(f"解析第{row_num}行数据时出错: {e}")
                                continue

                        # 成功读取，跳出编码循环
                        break

                except UnicodeDecodeError:
                    continue
            else:
                print(f"无法使用任何编码读取文件: {file_path}")
                return []

        except Exception as e:
            print(f"读取CSV文件时出错: {e}")
            return []

        print(f"成功读取 {len(measurements)} 条测量数据")
        return measurements

    def update_data_table(self, measurements):
        """更新数据表格"""
        self.data_table.setRowCount(len(measurements))

        for row, measurement in enumerate(measurements):
            # 位置(mm) - 对应测量序号
            position = measurement.get('position', measurement.get('depth', 0))
            self.data_table.setItem(row, 0, QTableWidgetItem(f"{position:.1f}"))

            # 直径(mm)
            diameter = measurement.get('diameter', 0)
            self.data_table.setItem(row, 1, QTableWidgetItem(f"{diameter:.4f}"))

            # 通道1值(mm)
            channel1 = measurement.get('channel1', 0)
            self.data_table.setItem(row, 2, QTableWidgetItem(f"{channel1:.2f}"))

            # 通道2值(mm)
            channel2 = measurement.get('channel2', 0)
            self.data_table.setItem(row, 3, QTableWidgetItem(f"{channel2:.2f}"))

            # 通道3值(mm)
            channel3 = measurement.get('channel3', 0)
            self.data_table.setItem(row, 4, QTableWidgetItem(f"{channel3:.2f}"))

            # 合格性
            is_qualified = measurement.get('is_qualified', True)
            qualified_text = "✓" if is_qualified else "✗"
            item = QTableWidgetItem(qualified_text)
            if not is_qualified:
                item.setBackground(Qt.red)
            else:
                item.setBackground(Qt.green)
            self.data_table.setItem(row, 5, item)

            # 时间
            timestamp = measurement.get('timestamp', '')
            if timestamp:
                time_str = timestamp.strftime("%H:%M:%S")
            else:
                time_str = "--"
            self.data_table.setItem(row, 6, QTableWidgetItem(time_str))

            # 操作员
            operator = measurement.get('operator', '--')
            self.data_table.setItem(row, 7, QTableWidgetItem(operator))

            # 备注 - 只有实际进行了人工复查的行才显示复查信息
            notes = ""
            if 'manual_review_value' in measurement:
                # 只有存在manual_review_value的行才显示复查信息
                review_value = measurement['manual_review_value']
                reviewer = measurement.get('reviewer', '未知')
                review_time = measurement.get('review_time', '')
                notes = f"人工复查值: {review_value:.4f}mm, 复查员: {reviewer}, 复查时间: {review_time}"

            self.data_table.setItem(row, 8, QTableWidgetItem(notes))

        # 调整列宽
        self.data_table.resizeColumnsToContents()

    def clear_display(self):
        """清除显示"""
        self.data_table.setRowCount(0)
        self.plot_widget.clear_plots()
        self.plot_widget.draw()

        # 清除三维模型
        if HAS_3D_RENDERER and hasattr(self, 'model_3d_viewer'):
            self.model_3d_viewer.clear_models()

        # 清除当前管孔ID显示
        self.update_current_hole_display("")

    def update_current_hole_display(self, hole_id):
        """更新当前管孔ID显示"""
        if hole_id:
            self.current_hole_label.setText(f"当前管孔: {hole_id}")
            self.current_hole_label.setStyleSheet("font-weight: bold; color: #1976d2; margin-left: 10px;")
        else:
            self.current_hole_label.setText("当前管孔: --")
            self.current_hole_label.setStyleSheet("font-weight: bold; color: #666; margin-left: 10px;")

    def export_data(self):
        """导出数据"""
        if not self.current_hole_data:
            QMessageBox.warning(self, "警告", "没有数据可导出")
            return

        # 这里可以实现数据导出功能
        QMessageBox.information(self, "信息", "数据导出功能待实现")

    def on_table_double_clicked(self, row, column):
        """处理表格双击事件"""
        print(f"🔍 双击事件触发: 行{row}, 列{column}")

        # 详细检查数据状态
        print(f"🔍 检查数据状态:")
        print(f"   hasattr(self, 'current_hole_data'): {hasattr(self, 'current_hole_data')}")
        if hasattr(self, 'current_hole_data'):
            print(f"   self.current_hole_data is not None: {self.current_hole_data is not None}")
            if self.current_hole_data:
                print(f"   current_hole_data keys: {list(self.current_hole_data.keys())}")
                if 'measurements' in self.current_hole_data:
                    print(f"   measurements count: {len(self.current_hole_data['measurements'])}")

        # 检查是否有数据
        if not hasattr(self, 'current_hole_data') or not self.current_hole_data:
            print("❌ 没有当前孔数据，请先查询数据")
            QMessageBox.warning(self, "提示", "请先查询数据，然后再双击表格行进行拟合圆分析")
            return

        # 检查是否有测量数据
        if 'measurements' not in self.current_hole_data or not self.current_hole_data['measurements']:
            print("❌ 没有测量数据")
            QMessageBox.warning(self, "提示", "当前没有测量数据")
            return

        if row >= self.data_table.rowCount():
            print(f"❌ 行索引超出范围: {row} >= {self.data_table.rowCount()}")
            return

        try:
            # 从数据源获取通道数据（更可靠的方法）
            measurements = self.current_hole_data['measurements']
            if row >= len(measurements):
                print(f"❌ 行索引超出数据范围: {row} >= {len(measurements)}")
                return

            measurement = measurements[row]

            # 提取通道数据
            channel1 = measurement.get('channel1', 0)
            channel2 = measurement.get('channel2', 0)
            channel3 = measurement.get('channel3', 0)

            # 检查通道数据是否有效
            if channel1 == 0 and channel2 == 0 and channel3 == 0:
                QMessageBox.warning(self, "警告", "该行的通道数据为空或无效")
                return

            # 数据转换：通道数据单位为μm，使用公式 2.1 - 通道值*0.001 进行处理
            # 这个公式将μm数据转换为绘图所需的参数，对应matlab.txt中的measure_list数组值
            if channel1 > 100:  # 检测到大数值格式（μm单位）
                # 转换公式：2.1 - 通道值 * 0.001
                # 例如：1385.62μm → 2.1 - 1385.62*0.001 = 2.1 - 1.38562 = 0.71438
                channel1_processed = 2.1 - channel1 * 0.001
                channel2_processed = 2.1 - channel2 * 0.001
                channel3_processed = 2.1 - channel3 * 0.001

                print(f"🔄 数据转换: μm -> 绘图参数")
                print(f"   原始数据(μm): [{measurement.get('channel1'):.2f}, {measurement.get('channel2'):.2f}, {measurement.get('channel3'):.2f}]")
                print(f"   转换公式: 2.1 - 通道值*0.001")
                print(f"   转换后: [{channel1_processed:.6f}, {channel2_processed:.6f}, {channel3_processed:.6f}]")
            else:
                # 如果是小数值，假设已经是处理后的参数
                channel1_processed = channel1
                channel2_processed = channel2
                channel3_processed = channel3
                print(f"🔄 数据已为处理后参数: [{channel1_processed:.6f}, {channel2_processed:.6f}, {channel3_processed:.6f}]")

            measure_list = [channel1_processed, channel2_processed, channel3_processed]

            # 获取位置信息
            position = measurement.get('position', measurement.get('depth', row + 1))

            print(f"✅ 双击第{row+1}行，位置: {position}mm")
            print(f"📊 处理后的绘图参数: {measure_list}")

            # 绘制拟合圆图，传递行号用于动态标题
            print("🎯 开始绘制拟合圆...")
            self.plot_probe_fitted_circles(measure_list, row + 1)  # 传递数据行号
            print("✅ 拟合圆绘制完成")

        except ValueError as e:
            QMessageBox.warning(self, "错误", f"数据格式错误: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"处理数据时发生错误: {str(e)}")

    def plot_probe_fitted_circles(self, measure_list, data_row_number):
        """
        根据通道数据绘制拟合圆图
        measure_list: [channel1, channel2, channel3] 三个通道的处理后参数
                     处理公式：2.1 - 通道值(μm)*0.001
        data_row_number: 数据行号，用于动态标题
        """
        try:
            print("🔄 开始拟合圆计算...")
            # 使用探头拟合算法处理数据
            result = ProbeCircleFitter.process_channel_data(measure_list)
            # 将measure_list添加到结果中，供绘制函数使用
            result['measure_list'] = measure_list
            print(f"✅ 拟合圆计算成功: 圆心({result['center_x']:.4f}, {result['center_y']:.4f})")

            print(f"🎨 在子图{self.circle_plot_index + 1}绘制拟合圆...")
            # 根据当前索引选择对应的子图绘制拟合圆，传递数据行号
            self.plot_fitted_circle_single(result, self.circle_plot_index, data_row_number)

            # 更新索引，循环使用四个子图 (0->1->2->3->0...)
            self.circle_plot_index = (self.circle_plot_index + 1) % 4
            print(f"✅ 拟合圆绘制完成，下次将绘制在子图{self.circle_plot_index + 1}")

        except Exception as e:
            print(f"❌ 拟合圆计算失败: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "错误", f"拟合圆计算失败: {str(e)}")





    def export_data(self):
        """导出数据到CSV文件"""
        if not hasattr(self, 'current_hole_data') or not self.current_hole_data:
            QMessageBox.warning(self, "警告", "请先查询数据后再导出")
            return

        # 在导出数据时，先清除之前的三维模型，然后重新绘制当前管孔的模型
        if HAS_3D_RENDERER and hasattr(self, 'model_3d_viewer'):
            # 清除之前的模型
            self.model_3d_viewer.clear_models()
            # 重新绘制当前管孔的模型
            if 'measurements' in self.current_hole_data:
                self.model_3d_viewer.update_models(self.current_hole_data['measurements'])

        # 弹出文件保存对话框
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出测量数据",
            f"{self.current_hole_data['hole_id']}_测量数据.csv",
            "CSV文件 (*.csv);;所有文件 (*)"
        )

        if not file_path:
            return

        try:
            measurements = self.current_hole_data['measurements']
            workpiece_id = self.current_hole_data['workpiece_id']
            hole_id = self.current_hole_data['hole_id']

            # 计算统计信息
            diameters = [m['diameter'] for m in measurements]
            standard_diameter = 17.6
            upper_tolerance = 0.05
            lower_tolerance = 0.07

            qualified_count = sum(1 for d in diameters
                                if standard_diameter - lower_tolerance <= d <= standard_diameter + upper_tolerance)
            total_count = len(diameters)
            qualification_rate = qualified_count / total_count * 100 if total_count > 0 else 0

            max_diameter = max(diameters) if diameters else 0
            min_diameter = min(diameters) if diameters else 0
            avg_diameter = sum(diameters) / len(diameters) if diameters else 0

            # 添加调试输出
            print(f"🔍 导出统计计算调试:")
            print(f"   数据点数: {len(diameters)}")
            print(f"   最大直径: {max_diameter:.4f}mm")
            print(f"   最小直径: {min_diameter:.4f}mm")
            print(f"   平均直径: {avg_diameter:.4f}mm")

            # 写入CSV文件
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)

                # 写入统计信息头部
                writer.writerow(['测量数据统计信息'])
                writer.writerow(['工件ID', workpiece_id])
                writer.writerow(['孔位ID', hole_id])
                writer.writerow(['标准直径(mm)', standard_diameter])
                writer.writerow(['公差范围(mm)', f'-{lower_tolerance}~+{upper_tolerance}'])
                writer.writerow(['最大直径(mm)', f'{max_diameter:.4f}'])
                writer.writerow(['最小直径(mm)', f'{min_diameter:.4f}'])
                writer.writerow(['平均直径(mm)', f'{avg_diameter:.4f}'])
                writer.writerow(['合格率', f'{qualified_count}/{total_count} ({qualification_rate:.1f}%)'])
                writer.writerow([])  # 空行分隔

                # 写入测量数据表头（按照测量数据窗口格式）
                writer.writerow(['位置(mm)', '直径(mm)', '通道1值(μm)', '通道2值(μm)', '通道3值(μm)', '合格', '时间', '操作员', '备注'])

                # 写入测量数据
                for i, measurement in enumerate(measurements):
                    diameter = measurement['diameter']
                    is_qualified = (standard_diameter - lower_tolerance <= diameter <= standard_diameter + upper_tolerance)
                    qualified_text = '✓' if is_qualified else '✗'  # 使用与测量数据窗口相同的符号

                    # 检查是否有人工复查值
                    notes = ""
                    if 'manual_review_value' in measurement:
                        notes = f"人工复查值: {measurement['manual_review_value']:.4f}mm"  # 使用4位小数
                        if 'reviewer' in measurement:
                            notes += f", 复查员: {measurement['reviewer']}"
                        if 'review_time' in measurement:
                            notes += f", 复查时间: {measurement['review_time']}"

                    # 获取位置信息（兼容两种键名）
                    position = measurement.get('position', measurement.get('depth', 0))

                    # 时间格式化
                    timestamp = measurement.get('timestamp', '')
                    if timestamp:
                        time_str = timestamp.strftime("%H:%M:%S") if hasattr(timestamp, 'strftime') else str(timestamp)
                    else:
                        time_str = "--"

                    # 操作员信息
                    operator = measurement.get('operator', '--')

                    writer.writerow([
                        f"{position:.1f}",           # 位置(mm) - 1位小数
                        f"{diameter:.4f}",           # 直径(mm) - 4位小数，与测量数据窗口一致
                        f"{measurement.get('channel1', 0):.2f}",  # 通道1值(μm) - 2位小数
                        f"{measurement.get('channel2', 0):.2f}",  # 通道2值(μm) - 2位小数
                        f"{measurement.get('channel3', 0):.2f}",  # 通道3值(μm) - 2位小数
                        qualified_text,              # 合格 - ✓ 或 ✗
                        time_str,                    # 时间 - HH:MM:SS
                        operator,                    # 操作员
                        notes                        # 备注
                    ])

            QMessageBox.information(self, "成功", f"数据已成功导出到:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出数据失败:\n{str(e)}")

    def open_manual_review(self):
        """打开人工复查窗口"""
        if not hasattr(self, 'current_hole_data') or not self.current_hole_data:
            QMessageBox.warning(self, "警告", "请先查询数据后再进行人工复查")
            return

        # 检查是否有不合格数据
        measurements = self.current_hole_data['measurements']
        standard_diameter = 17.6
        upper_tolerance = 0.05
        lower_tolerance = 0.07

        unqualified_measurements = []
        for i, measurement in enumerate(measurements):
            diameter = measurement['diameter']
            if not (standard_diameter - lower_tolerance <= diameter <= standard_diameter + upper_tolerance):
                unqualified_measurements.append((i, measurement))

        if not unqualified_measurements:
            QMessageBox.information(self, "信息", "当前数据中没有不合格的测量值，无需人工复查")
            return

        # 打开人工复查对话框
        dialog = ManualReviewDialog(unqualified_measurements, self)
        if dialog.exec() == QDialog.Accepted:
            # 获取复查结果并更新数据
            review_results = dialog.get_review_results()
            self.apply_manual_review_results(review_results)

    def apply_manual_review_results(self, review_results):
        """应用人工复查结果"""
        if not hasattr(self, 'current_hole_data') or not self.current_hole_data:
            return

        measurements = self.current_hole_data['measurements']
        updated_count = 0

        for index, review_data in review_results.items():
            if index < len(measurements):
                measurements[index]['manual_review_value'] = review_data['diameter']
                measurements[index]['reviewer'] = review_data['reviewer']
                measurements[index]['review_time'] = review_data['review_time']
                updated_count += 1

        if updated_count > 0:
            # 更新显示
            if hasattr(self, 'current_hole_data') and self.current_hole_data:
                measurements = self.current_hole_data['measurements']
                self.update_data_table(measurements)
                # 如果有图表，也更新图表
                if hasattr(self, 'plot_widget') and self.plot_widget:
                    try:
                        self.plot_widget.update_plots(measurements)
                        self.plot_widget.draw()
                    except Exception as e:
                        print(f"更新图表时出错: {e}")

            QMessageBox.information(self, "成功", f"已更新 {updated_count} 条人工复查记录")


class ManualReviewDialog(QDialog):
    """人工复查对话框"""

    def __init__(self, unqualified_measurements, parent=None):
        super().__init__(parent)
        self.unqualified_measurements = unqualified_measurements
        self.review_inputs = {}
        self.setup_ui()

    def setup_ui(self):
        """设置界面"""
        self.setWindowTitle("人工复查")
        self.setModal(True)
        self.resize(550, 500)  # 增加宽度以确保右侧信息完整显示

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # 标题和说明
        title_label = QLabel("人工复查")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333; margin-bottom: 5px;")
        layout.addWidget(title_label)

        info_label = QLabel("以下是检测为不合格的测量点，请输入人工复检的直径值：")
        info_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(info_label)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 禁用水平滚动条
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setMaximumHeight(350)  # 增加最大高度以显示更多数据

        # 创建滚动内容容器
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(8)

        # 为每个不合格测量点创建一行
        for i, (index, measurement) in enumerate(self.unqualified_measurements):
            # 创建一行的容器
            row_frame = QFrame()
            row_frame.setFrameStyle(QFrame.Box)
            row_frame.setStyleSheet("QFrame { border: 1px solid #ddd; border-radius: 5px; padding: 5px; background-color: #f9f9f9; margin: 2px; }")

            row_layout = QHBoxLayout(row_frame)
            row_layout.setContentsMargins(8, 6, 8, 6)
            row_layout.setSpacing(8)

            # 位置信息（删除序号显示）
            position = measurement.get('position', measurement.get('depth', 0))
            position_label = QLabel(f"位置: {position:.1f}mm")
            position_label.setStyleSheet("font-weight: bold; min-width: 85px; max-width: 85px;")
            row_layout.addWidget(position_label)

            # 原直径（显示原始数据，不四舍五入）
            original_diameter = measurement['diameter']
            original_label = QLabel(f"原直径: {original_diameter:.4f}mm")  # 使用4位小数显示原始数据
            original_label.setStyleSheet("min-width: 120px; max-width: 120px; color: #d32f2f; font-weight: bold;")
            row_layout.addWidget(original_label)

            # 复查直径输入
            review_label = QLabel("复查直径:")
            review_label.setStyleSheet("min-width: 65px; max-width: 65px; font-weight: bold;")
            row_layout.addWidget(review_label)

            spin_box = QDoubleSpinBox()
            spin_box.setRange(10.0, 25.0)
            spin_box.setDecimals(4)  # 增加到4位小数以显示原始数据精度
            spin_box.setSingleStep(0.0001)  # 调整步长为0.0001
            spin_box.setValue(original_diameter)  # 使用原始直径数据
            spin_box.setSuffix(" mm")
            spin_box.setFixedWidth(110)  # 增加输入框宽度以显示完整数值
            spin_box.setStyleSheet("QDoubleSpinBox { border: 1px solid #ccc; border-radius: 3px; padding: 3px; font-size: 12px; }")
            row_layout.addWidget(spin_box)

            # 添加弹性空间，确保布局紧凑
            row_layout.addStretch()

            self.review_inputs[index] = spin_box
            scroll_layout.addWidget(row_frame)

        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)

        # 复查员输入区域
        reviewer_frame = QFrame()
        reviewer_frame.setStyleSheet("QFrame { border: 1px solid #ddd; border-radius: 5px; padding: 10px; background-color: #f5f5f5; }")
        reviewer_layout = QHBoxLayout(reviewer_frame)

        reviewer_label = QLabel("复查员:")
        reviewer_label.setStyleSheet("font-weight: bold; min-width: 60px;")
        reviewer_layout.addWidget(reviewer_label)

        self.reviewer_input = QLineEdit()
        self.reviewer_input.setPlaceholderText("请输入复查员姓名")
        self.reviewer_input.setStyleSheet("QLineEdit { border: 1px solid #ccc; border-radius: 3px; padding: 5px; }")
        reviewer_layout.addWidget(self.reviewer_input)

        layout.addWidget(reviewer_frame)

        # 按钮区域
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText("确定")
        button_box.button(QDialogButtonBox.Cancel).setText("取消")
        button_box.button(QDialogButtonBox.Ok).setStyleSheet("QPushButton { background-color: #1976d2; color: white; border: none; border-radius: 3px; padding: 8px 16px; font-weight: bold; }")
        button_box.button(QDialogButtonBox.Cancel).setStyleSheet("QPushButton { background-color: #757575; color: white; border: none; border-radius: 3px; padding: 8px 16px; }")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_review_results(self):
        """获取复查结果 - 只返回实际修改过的数据"""
        results = {}
        reviewer = self.reviewer_input.text().strip()

        if not reviewer:
            reviewer = "未知"

        from datetime import datetime
        review_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 只收集实际修改过的数据
        for index, spin_box in self.review_inputs.items():
            # 获取原始直径值
            original_diameter = None
            for i, (idx, measurement) in enumerate(self.unqualified_measurements):
                if idx == index:
                    original_diameter = measurement['diameter']
                    break

            current_value = spin_box.value()

            # 只有当值实际发生变化时才添加到结果中
            if original_diameter is not None and abs(current_value - original_diameter) > 0.0001:
                results[index] = {
                    'diameter': current_value,
                    'reviewer': reviewer,
                    'review_time': review_time
                }

        return results

    def accept(self):
        """重写accept方法，检查是否有实际修改"""
        review_results = self.get_review_results()

        if not review_results:
            # 没有任何修改
            QMessageBox.information(self, "提示", "没有检测到任何修改，无需保存。")
            return

        # 检查复查员姓名
        reviewer = self.reviewer_input.text().strip()
        if not reviewer:
            QMessageBox.warning(self, "警告", "请输入复查员姓名！")
            return

        # 有修改，继续正常流程
        super().accept()






if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # 初始化数据库并创建示例数据
    db_manager.create_sample_data()

    # 添加一些测试数据
    import numpy as np
    for i in range(50):
        depth = i * 2.0
        diameter = 25.0 + 0.1 * np.sin(depth * 0.1) + np.random.normal(0, 0.02)
        db_manager.add_measurement_data("H001", depth, diameter)

    # 创建历史数据查看器
    viewer = HistoryViewer()
    viewer.show()

    sys.exit(app.exec())
