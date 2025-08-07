"""
P3.1级界面 - 直接从重构前代码迁移的历史数据查看器
基于重构前的 /mnt/d/上位机历史版本/AIDCIS3-LFS-0803/AIDCIS3-LFS/src/modules/history_viewer.py

三列布局：
1. 左侧：光谱共焦历史数据查看器（数据筛选和操作）
2. 中间：测量数据表格
3. 右侧：二维公差带图表和三维模型渲染（标签页）

保持高内聚低耦合原则，直接迁移重构前的完整功能
"""

import numpy as np
import matplotlib
try:
    matplotlib.use('Qt5Agg')
except ImportError:
    try:
        matplotlib.use('TkAgg')
    except ImportError:
        matplotlib.use('Agg')

import matplotlib.pyplot as plt
import os
import platform

try:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
except ImportError:
    try:
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigureCanvas
    except ImportError:
        from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

from matplotlib.figure import Figure
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QLabel, QPushButton, QLineEdit, QComboBox,
                               QGroupBox, QTableWidget, QTableWidgetItem,
                               QSplitter, QTextEdit, QMessageBox, QFileDialog,
                               QDialog, QFormLayout, QDoubleSpinBox, QDialogButtonBox,
                               QScrollArea, QFrame, QTabWidget, QToolButton, QMenu)
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QFont, QAction
import csv
import glob
from datetime import datetime
import tempfile
import io

# 配置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class ScrollableTextLabel(QLabel):
    """可滚动的文本标签 - 直接从重构前代码迁移"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.full_text = ""
        self.placeholder_text = ""
        self.scroll_timer = QTimer()
        self.scroll_timer.timeout.connect(self.scroll_text)
        self.scroll_offset = 0
        self.scroll_direction = 1
        self.pause_counter = 0
        self.max_scroll_offset = 0
        self.text_width = 0
        self.visible_width = 0
        self.scroll_step = 1
        self.setStyleSheet("""
            QLabel {
                border: 1px solid #505869;
                padding: 5px;
                background-color: #2a2d35;
                color: #D3D8E0;
                text-align: left;
            }
        """)
        
    def setPlaceholderText(self, text):
        """设置占位符文本"""
        self.placeholder_text = text
        if not self.full_text:
            super().setText(text)
            
    def setText(self, text):
        """设置文本并启动滚动"""
        self.full_text = text
        if not text:
            super().setText(self.placeholder_text)
            self.scroll_timer.stop()
            return
            
        super().setText(text)
        self.check_text_overflow()
        
    def check_text_overflow(self):
        """检查文本是否溢出并决定是否启动滚动"""
        if not self.full_text:
            return
            
        font_metrics = self.fontMetrics()
        self.text_width = font_metrics.horizontalAdvance(self.full_text)
        self.visible_width = self.width() - 12  # 减去padding
        
        if self.text_width > self.visible_width:
            self.max_scroll_offset = self.text_width - self.visible_width
            self.start_scrolling()
        else:
            self.scroll_timer.stop()
            
    def start_scrolling(self):
        """开始滚动"""
        if not self.scroll_timer.isActive():
            self.scroll_offset = 0
            self.scroll_direction = 1
            self.pause_counter = 0
            self.scroll_timer.start(50)
            
    def scroll_text(self):
        """滚动文本"""
        if not self.full_text:
            return
            
        # 在两端暂停
        if self.scroll_offset <= 0 or self.scroll_offset >= self.max_scroll_offset:
            if self.pause_counter < 30:  # 暂停1.5秒
                self.pause_counter += 1
                return
            else:
                self.scroll_direction *= -1
                self.pause_counter = 0
                
        self.scroll_offset += self.scroll_direction * self.scroll_step
        self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll_offset))
        
        # 更新显示的文本
        font_metrics = self.fontMetrics()
        char_width = font_metrics.averageCharWidth()
        start_char = max(0, int(self.scroll_offset / char_width))
        visible_chars = int(self.visible_width / char_width)
        
        if start_char < len(self.full_text):
            visible_text = self.full_text[start_char:start_char + visible_chars + 1]
            super().setText(visible_text)
            
    def resizeEvent(self, event):
        """窗口大小改变时重新检查滚动"""
        super().resizeEvent(event)
        if self.full_text:
            self.check_text_overflow()
            
    def clear(self):
        """清除文本"""
        self.full_text = ""
        self.scroll_timer.stop()
        super().setText(self.placeholder_text)


class HistoryDataPlot(QWidget):
    """历史数据图表组件 - 直接从重构前代码迁移"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.measurements = []
        self.setup_ui()
        
    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建matplotlib图形
        self.figure = Figure(figsize=(12, 8), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # 设置深色主题
        self.figure.patch.set_facecolor('#313642')
        
        # 初始化空图表
        self.ax = self.figure.add_subplot(111)
        self.setup_chart_style()
        self.show_empty_chart()
        
    def setup_chart_style(self):
        """设置图表样式"""
        self.ax.set_facecolor('#313642')
        for spine in self.ax.spines.values():
            spine.set_color('#505869')
        self.ax.tick_params(axis='x', colors='#D3D8E0')
        self.ax.tick_params(axis='y', colors='#D3D8E0')
        self.ax.xaxis.label.set_color('#D3D8E0')
        self.ax.yaxis.label.set_color('#D3D8E0')
        self.ax.title.set_color('#FFFFFF')
        self.ax.grid(True, color='#505869', alpha=0.3)
        
    def show_empty_chart(self):
        """显示空图表"""
        self.ax.clear()
        self.setup_chart_style()
        self.ax.set_xlabel('深度 (mm)', fontsize=12)
        self.ax.set_ylabel('直径 (mm)', fontsize=12)
        self.ax.set_title('二维公差带包络图', fontsize=14, fontweight='bold')
        self.ax.text(0.5, 0.5, '请选择孔位加载数据', 
                    transform=self.ax.transAxes, ha='center', va='center',
                    fontsize=14, color='#888888')
        self.canvas.draw()
        
    def plot_data(self, measurements, hole_id=""):
        """绘制数据"""
        if not measurements:
            self.show_empty_chart()
            return
            
        self.measurements = measurements
        self.ax.clear()
        self.setup_chart_style()
        
        # 提取数据
        depths = []
        diameters = []
        for m in measurements:
            depth = m.get('position', m.get('depth', 0))
            diameter = m.get('diameter', 0)
            depths.append(float(depth))
            diameters.append(float(diameter))
            
        if not depths or not diameters:
            self.show_empty_chart()
            return
            
        depths = np.array(depths)
        diameters = np.array(diameters)
        
        # 设置坐标轴范围
        depth_margin = (max(depths) - min(depths)) * 0.05 if len(depths) > 1 else 50
        diameter_margin = (max(diameters) - min(diameters)) * 0.1 if len(diameters) > 1 else 0.05
        
        x_min = max(0, min(depths) - depth_margin)
        x_max = max(depths) + depth_margin
        y_min = min(diameters) - diameter_margin
        y_max = max(diameters) + diameter_margin
        
        self.ax.set_xlim(x_min, x_max)
        self.ax.set_ylim(y_min, y_max)
        
        # 绘制公差线 - 基于重构前的实际参数
        standard_diameter = 17.73  # mm
        upper_tolerance = 0.07     # +0.07mm
        lower_tolerance = 0.05     # -0.05mm
        
        depth_range = [x_min, x_max]
        
        # 上公差线
        upper_line = np.full(2, standard_diameter + upper_tolerance)
        self.ax.plot(depth_range, upper_line, 'r--', linewidth=2, alpha=0.8,
                    label=f'上公差线 ({standard_diameter + upper_tolerance:.3f}mm)')
        
        # 下公差线
        lower_line = np.full(2, standard_diameter - lower_tolerance)
        self.ax.plot(depth_range, lower_line, 'r--', linewidth=2, alpha=0.8,
                    label=f'下公差线 ({standard_diameter - lower_tolerance:.3f}mm)')
        
        # 标准直径线
        standard_line = np.full(2, standard_diameter)
        self.ax.plot(depth_range, standard_line, 'g-', linewidth=1.5, alpha=0.7,
                    label=f'标准直径 ({standard_diameter:.2f}mm)')
        
        # 填充公差带区域
        self.ax.fill_between(depth_range, 
                            standard_diameter - lower_tolerance,
                            standard_diameter + upper_tolerance,
                            alpha=0.1, color='green', label='合格区域')
        
        # 绘制测量数据
        self.ax.plot(depths, diameters, 'b-', linewidth=2, 
                    marker='o', markersize=4, markerfacecolor='#4A90E2',
                    markeredgecolor='white', markeredgewidth=0.5,
                    label='测量数据', alpha=0.8)
        
        # 标记超出公差的点
        for i, (depth, diameter) in enumerate(zip(depths, diameters)):
            if (diameter > standard_diameter + upper_tolerance or 
                diameter < standard_diameter - lower_tolerance):
                self.ax.plot(depth, diameter, 'ro', markersize=8, alpha=0.9, 
                           markeredgecolor='white', markeredgewidth=1)
        
        # 设置标签和标题
        self.ax.set_xlabel('深度 (mm)', fontsize=12)
        self.ax.set_ylabel('直径 (mm)', fontsize=12)
        
        title = '二维公差带包络图'
        if hole_id:
            title += f' - {hole_id}'
        self.ax.set_title(title, fontsize=14, fontweight='bold')
        
        # 创建图例
        legend = self.ax.legend(loc='upper right', fontsize=10)
        legend.get_frame().set_facecolor('#3a3d45')
        legend.get_frame().set_edgecolor('#505869')
        for text in legend.get_texts():
            text.set_color('#D3D8E0')
            
        # 添加统计信息
        self.add_statistics(diameters, standard_diameter, upper_tolerance, lower_tolerance)
        
        self.canvas.draw()
        
    def add_statistics(self, diameters, standard_diameter, upper_tolerance, lower_tolerance):
        """添加统计信息"""
        if len(diameters) == 0:
            return
            
        # 计算统计量
        mean_diameter = np.mean(diameters)
        std_diameter = np.std(diameters)
        min_diameter = np.min(diameters)
        max_diameter = np.max(diameters)
        
        # 计算合格率
        in_tolerance = np.sum((diameters >= standard_diameter - lower_tolerance) & 
                             (diameters <= standard_diameter + upper_tolerance))
        pass_rate = (in_tolerance / len(diameters)) * 100
        
        # 创建统计文本
        stats_text = (
            f'数据统计:\n'
            f'数据点数: {len(diameters)}\n'
            f'平均直径: {mean_diameter:.3f}mm\n'
            f'标准偏差: {std_diameter:.3f}mm\n'
            f'最小值: {min_diameter:.3f}mm\n'
            f'最大值: {max_diameter:.3f}mm\n'
            f'合格率: {pass_rate:.1f}%'
        )
        
        # 添加文本框
        props = dict(boxstyle='round', facecolor='#3a3d45', alpha=0.9, edgecolor='#505869')
        self.ax.text(0.02, 0.98, stats_text, transform=self.ax.transAxes,
                    fontsize=9, verticalalignment='top', bbox=props,
                    color='#D3D8E0')


class Hole3DViewer(QWidget):
    """三维孔洞查看器 - 占位符组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 占位符标签
        placeholder_label = QLabel("三维模型渲染区域")
        placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_label.setStyleSheet("""
            QLabel {
                color: #888888; 
                font-size: 18px;
                background-color: #2a2d35;
                border: 2px dashed #505869;
                padding: 60px;
                border-radius: 10px;
            }
        """)
        
        info_label = QLabel("将在后续版本中实现管孔三维模型的可视化渲染")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: #666666; font-size: 12px; margin-top: 20px;")
        
        layout.addWidget(placeholder_label)
        layout.addWidget(info_label)
        layout.addStretch()


class MigratedHistoryViewer(QWidget):
    """直接从重构前代码迁移的历史数据查看器 - 保持三列布局和完整功能"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_hole_data = None
        self.measurements = []
        self.setup_ui()
        self.load_workpiece_list()
        
    def setup_ui(self):
        """设置用户界面 - 三列布局"""
        # 主水平布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 创建侧边栏
        self.create_sidebar(layout)
        
        # 创建主内容区（表格和图表）
        splitter = QSplitter(Qt.Horizontal)
        self.create_data_table(splitter)
        self.create_visualization_tabs(splitter)
        splitter.setSizes([400, 600])  # 调整表格和图表比例
        
        layout.addWidget(splitter, 1)
        
    def create_sidebar(self, main_layout):
        """创建左侧的筛选与操作侧边栏 - 直接从重构前迁移"""
        self.sidebar_widget = QWidget()
        self.sidebar_widget.setObjectName("Sidebar")
        self.sidebar_widget.setMinimumWidth(200)
        self.sidebar_widget.setMaximumWidth(250)
        
        sidebar_layout = QVBoxLayout(self.sidebar_widget)
        sidebar_layout.setContentsMargins(15, 15, 15, 15)
        sidebar_layout.setSpacing(25)
        
        # 标题
        title_label = QLabel("光谱共焦历史数据查看器")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #D3D8E0;
                padding: 10px;
                background-color: #3a3d45;
                border: 1px solid #505869;
                border-radius: 5px;
            }
        """)
        sidebar_layout.addWidget(title_label)
        
        # 数据筛选部分
        filter_group = QGroupBox("数据筛选")
        filter_group.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
                color: #D3D8E0;
                border: 1px solid #505869;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #313642;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        filter_layout = QGridLayout(filter_group)
        filter_layout.setContentsMargins(10, 15, 10, 15)
        filter_layout.setSpacing(15)
        
        # 工件ID
        workpiece_label = QLabel("工件ID:")
        workpiece_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.wp_display = ScrollableTextLabel()
        self.wp_button = QToolButton()
        self.wp_button.setText("▼")
        self.wp_button.setMinimumWidth(30)
        self.wp_button.setStyleSheet("""
            QToolButton {
                border: 1px solid #505869;
                background-color: #2a2d35;
                color: #D3D8E0;
                padding: 4px;
            }
            QToolButton:hover {
                background-color: #3a3d45;
            }
        """)
        self.wp_button.clicked.connect(self.show_workpiece_menu)
        
        wp_combo_layout = QHBoxLayout()
        wp_combo_layout.setSpacing(0)
        wp_combo_layout.setContentsMargins(0, 0, 0, 0)
        wp_combo_layout.addWidget(self.wp_display)
        wp_combo_layout.addWidget(self.wp_button)
        
        # 合格孔ID
        qualified_label = QLabel("合格孔ID:")
        qualified_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.ql_display = ScrollableTextLabel()
        self.ql_display.setPlaceholderText("请选择合格孔ID")
        self.ql_button = QToolButton()
        self.ql_button.setText("▼")
        self.ql_button.setMinimumWidth(30)
        self.ql_button.setStyleSheet(self.wp_button.styleSheet())
        self.ql_button.clicked.connect(self.show_qualified_hole_menu)
        
        ql_combo_layout = QHBoxLayout()
        ql_combo_layout.setSpacing(0)
        ql_combo_layout.setContentsMargins(0, 0, 0, 0)
        ql_combo_layout.addWidget(self.ql_display)
        ql_combo_layout.addWidget(self.ql_button)
        
        # 不合格孔ID
        unqualified_label = QLabel("不合格孔ID:")
        unqualified_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.uql_display = ScrollableTextLabel()
        self.uql_display.setPlaceholderText("请选择不合格孔ID")
        self.uql_button = QToolButton()
        self.uql_button.setText("▼")
        self.uql_button.setMinimumWidth(30)
        self.uql_button.setStyleSheet(self.wp_button.styleSheet())
        self.uql_button.clicked.connect(self.show_unqualified_hole_menu)
        
        uql_combo_layout = QHBoxLayout()
        uql_combo_layout.setSpacing(0)
        uql_combo_layout.setContentsMargins(0, 0, 0, 0)
        uql_combo_layout.addWidget(self.uql_display)
        uql_combo_layout.addWidget(self.uql_button)
        
        # 添加到网格布局
        filter_layout.addWidget(workpiece_label, 0, 0)
        filter_layout.addLayout(wp_combo_layout, 0, 1)
        filter_layout.addWidget(qualified_label, 1, 0)
        filter_layout.addLayout(ql_combo_layout, 1, 1)
        filter_layout.addWidget(unqualified_label, 2, 0)
        filter_layout.addLayout(uql_combo_layout, 2, 1)
        
        sidebar_layout.addWidget(filter_group)
        
        # 操作命令部分
        self.create_operation_buttons(sidebar_layout)
        
        # 当前状态部分
        self.create_status_display(sidebar_layout)
        
        sidebar_layout.addStretch()
        main_layout.addWidget(self.sidebar_widget)
        
        # 创建隐藏的ComboBox用于数据管理
        self.workpiece_combo = QComboBox()
        self.qualified_hole_combo = QComboBox()
        self.unqualified_hole_combo = QComboBox()
        
    def create_operation_buttons(self, parent_layout):
        """创建操作按钮"""
        ops_group = QGroupBox("操作命令")
        ops_group.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
                color: #D3D8E0;
                border: 1px solid #505869;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #313642;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        ops_layout = QVBoxLayout(ops_group)
        ops_layout.setSpacing(10)
        ops_layout.setContentsMargins(15, 20, 15, 15)
        
        button_style = """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                min-height: 16px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #888;
            }
        """
        
        # 查询数据按钮
        self.query_button = QPushButton("查询数据")
        self.query_button.setStyleSheet(button_style)
        self.query_button.clicked.connect(self.query_hole_data)
        ops_layout.addWidget(self.query_button)
        
        # 导出数据按钮
        self.export_button = QPushButton("导出数据")
        self.export_button.setStyleSheet(button_style)
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self.export_data)
        ops_layout.addWidget(self.export_button)
        
        # 人工复查按钮
        self.review_button = QPushButton("人工复查")
        self.review_button.setStyleSheet(button_style)
        self.review_button.setEnabled(False)
        self.review_button.clicked.connect(self.manual_review)
        ops_layout.addWidget(self.review_button)
        
        parent_layout.addWidget(ops_group)
        
    def create_status_display(self, parent_layout):
        """创建状态显示"""
        status_group = QGroupBox("当前状态")
        status_group.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
                color: #D3D8E0;
                border: 1px solid #505869;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #313642;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        status_layout = QVBoxLayout(status_group)
        status_layout.setContentsMargins(15, 20, 15, 15)
        
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setPlainText("请选择孔位加载数据")
        self.status_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1d23;
                border: 1px solid #505869;
                color: #D3D8E0;
                font-size: 10px;
                padding: 8px;
                border-radius: 3px;
            }
        """)
        self.status_text.setReadOnly(True)
        
        status_layout.addWidget(self.status_text)
        parent_layout.addWidget(status_group)
        
    def create_data_table(self, splitter):
        """创建数据表格 - 直接从重构前迁移"""
        table_group = QGroupBox("测量数据")
        table_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
                font-weight: bold;
                color: #D3D8E0;
                border: 1px solid #505869;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #313642;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        table_layout = QVBoxLayout(table_group)
        table_layout.setContentsMargins(10, 10, 10, 10)
        
        self.data_table = QTableWidget()
        self.data_table.verticalHeader().setVisible(False)
        self.data_table.setColumnCount(10)
        self.data_table.setHorizontalHeaderLabels([
            "序号", "位置(mm)", "直径(mm)", "通道1值(μm)", "通道2值(μm)", "通道3值(μm)", "合格", "时间", "操作员", "备注"
        ])
        
        # 设置表格样式
        self.data_table.setStyleSheet("""
            QTableWidget {
                background-color: #2a2d35;
                border: 1px solid #505869;
                selection-background-color: #4A90E2;
                selection-color: white;
                gridline-color: #505869;
                color: #D3D8E0;
            }
            QHeaderView::section {
                background-color: #3a3d45;
                color: #D3D8E0;
                padding: 8px;
                border: 1px solid #505869;
                font-weight: bold;
                font-size: 10px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #505869;
            }
        """)
        
        # 设置表格属性
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.data_table.setSortingEnabled(True)
        self.data_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # 设置行高
        self.data_table.verticalHeader().setDefaultSectionSize(25)
        self.data_table.setMinimumHeight(300)
        
        table_layout.addWidget(self.data_table)
        splitter.addWidget(table_group)
        
    def create_visualization_tabs(self, parent):
        """创建可视化标签页 - 直接从重构前迁移"""
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #505869;
                background-color: #313642;
            }
            QTabBar::tab {
                background-color: #3a3d45;
                color: #D3D8E0;
                padding: 8px 16px;
                margin-right: 2px;
                border: 1px solid #505869;
                border-bottom: none;
                font-size: 11px;
            }
            QTabBar::tab:selected {
                background-color: #4A90E2;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #505869;
            }
        """)
        
        # 二维图表标签页
        self.plot_widget = HistoryDataPlot()
        tab_widget.addTab(self.plot_widget, "二维公差带图表")
        
        # 三维模型标签页
        self.model_3d_viewer = Hole3DViewer()
        tab_widget.addTab(self.model_3d_viewer, "三维模型渲染")
        
        parent.addWidget(tab_widget)
        
    # === 数据加载和处理方法 ===
    
    def load_workpiece_list(self):
        """加载工件列表"""
        self.workpiece_combo.addItem("CAP1000")
        self.wp_display.setText("CAP1000")
        self.on_workpiece_changed("CAP1000")
        
    def on_workpiece_changed(self, workpiece_id):
        """工件选择改变"""
        if workpiece_id:
            self.load_hole_list(workpiece_id)
            
    def load_hole_list(self, workpiece_id):
        """加载孔位列表"""
        print(f"🔍 加载工件 {workpiece_id} 的孔位列表...")
        
        # 清空现有选项
        self.qualified_hole_combo.clear()
        self.unqualified_hole_combo.clear()
        self.ql_display.clear()
        self.uql_display.clear()
        
        # 从实际数据源加载孔位（空实现，应由具体业务逻辑填充）
            
        print("✅ 孔位加载完成")
        
    # === 菜单显示方法 ===
    
    def show_workpiece_menu(self):
        """显示工件选择菜单"""
        menu = QMenu(self)
        for i in range(self.workpiece_combo.count()):
            text = self.workpiece_combo.itemText(i)
            action = menu.addAction(text)
            action.triggered.connect(lambda checked, t=text: self.select_workpiece(t))
        menu.exec(self.wp_button.mapToGlobal(self.wp_button.rect().bottomLeft()))
        
    def show_qualified_hole_menu(self):
        """显示合格孔位选择菜单"""
        menu = QMenu(self)
        for i in range(self.qualified_hole_combo.count()):
            text = self.qualified_hole_combo.itemText(i)
            action = menu.addAction(text)
            action.triggered.connect(lambda checked, t=text: self.select_qualified_hole(t))
        menu.exec(self.ql_button.mapToGlobal(self.ql_button.rect().bottomLeft()))
        
    def show_unqualified_hole_menu(self):
        """显示不合格孔位选择菜单"""
        menu = QMenu(self)
        # 这里可以添加不合格孔位（如果有的话）
        if self.unqualified_hole_combo.count() == 0:
            action = menu.addAction("暂无不合格孔位")
            action.setEnabled(False)
        else:
            for i in range(self.unqualified_hole_combo.count()):
                text = self.unqualified_hole_combo.itemText(i)
                action = menu.addAction(text)
                action.triggered.connect(lambda checked, t=text: self.select_unqualified_hole(t))
        menu.exec(self.uql_button.mapToGlobal(self.uql_button.rect().bottomLeft()))
        
    # === 选择处理方法 ===
    
    def select_workpiece(self, workpiece_id):
        """选择工件"""
        self.wp_display.setText(workpiece_id)
        self.workpiece_combo.setCurrentText(workpiece_id)
        self.on_workpiece_changed(workpiece_id)
        
    def select_qualified_hole(self, hole_id):
        """选择合格孔位"""
        self.ql_display.setText(hole_id)
        self.qualified_hole_combo.setCurrentText(hole_id)
        # 清空不合格孔位选择
        self.uql_display.clear()
        
    def select_unqualified_hole(self, hole_id):
        """选择不合格孔位"""
        self.uql_display.setText(hole_id)
        self.unqualified_hole_combo.setCurrentText(hole_id)
        # 清空合格孔位选择
        self.ql_display.clear()
        
    # === 核心功能方法 ===
    
    def query_hole_data(self):
        """查询孔位数据"""
        # 获取选择的孔位
        qualified_hole = self.ql_display.text() if self.ql_display.text() != self.ql_display.placeholder_text else ""
        unqualified_hole = self.uql_display.text() if self.uql_display.text() != self.uql_display.placeholder_text else ""
        
        selected_hole = qualified_hole or unqualified_hole
        
        if not selected_hole:
            QMessageBox.warning(self, "警告", "请选择合格孔ID或不合格孔ID")
            return
            
        print(f"🔍 查询孔位数据: {selected_hole}")
        
        # 从实际数据源加载数据
        self.load_hole_measurement_data(selected_hole)
        
    def load_hole_measurement_data(self, hole_id):
        """加载孔位测量数据"""
        # 加载真实测量数据（空实现，应由实际数据加载逻辑填充）
        measurements = []
        
        # 这里应该从实际的数据源（如CSV文件、数据库等）加载数据
        # measurements = data_loader.load_measurements_for_hole(hole_id)
        
        if measurements:
            self.measurements = measurements
            self.current_hole_data = {'hole_id': hole_id, 'measurements': measurements}
            
            # 更新表格显示
            self.update_data_table()
            
            # 更新图表显示
            self.plot_widget.plot_data(measurements, hole_id)
            
            # 启用操作按钮
            self.export_button.setEnabled(True)
            self.review_button.setEnabled(True)
            
            # 更新状态显示
            qualified_count = sum(1 for m in measurements if m['is_qualified'])
            pass_rate = (qualified_count / len(measurements)) * 100
            
            status_text = f"已加载孔位: {hole_id}\n"
            status_text += f"数据点数: {len(measurements)}\n"
            status_text += f"合格点数: {qualified_count}\n"
            status_text += f"合格率: {pass_rate:.1f}%"
            
            self.status_text.setPlainText(status_text)
            
            print(f"✅ 成功加载 {len(measurements)} 条测量数据")
        
    def update_data_table(self):
        """更新数据表格显示"""
        if not self.measurements:
            return
            
        self.data_table.setRowCount(len(self.measurements))
        
        for row, measurement in enumerate(self.measurements):
            # 序号
            self.data_table.setItem(row, 0, QTableWidgetItem(str(measurement.get('sequence', row + 1))))
            
            # 位置
            position = measurement.get('position', measurement.get('depth', 0))
            self.data_table.setItem(row, 1, QTableWidgetItem(f"{position:.1f}"))
            
            # 直径
            diameter = measurement.get('diameter', 0)
            item = QTableWidgetItem(f"{diameter:.4f}")
            # 根据合格性设置颜色
            if not measurement.get('is_qualified', True):
                item.setBackground(Qt.red.color())
                item.setForeground(Qt.white.color())
            self.data_table.setItem(row, 2, item)
            
            # 通道值
            self.data_table.setItem(row, 3, QTableWidgetItem(f"{measurement.get('channel1', 0):.1f}"))
            self.data_table.setItem(row, 4, QTableWidgetItem(f"{measurement.get('channel2', 0):.1f}"))
            self.data_table.setItem(row, 5, QTableWidgetItem(f"{measurement.get('channel3', 0):.1f}"))
            
            # 合格状态
            qualified_text = "合格" if measurement.get('is_qualified', True) else "不合格"
            self.data_table.setItem(row, 6, QTableWidgetItem(qualified_text))
            
            # 时间
            self.data_table.setItem(row, 7, QTableWidgetItem(measurement.get('timestamp', '')))
            
            # 操作员
            self.data_table.setItem(row, 8, QTableWidgetItem(measurement.get('operator', '')))
            
            # 备注
            self.data_table.setItem(row, 9, QTableWidgetItem(measurement.get('notes', '')))
            
        # 调整列宽
        self.data_table.resizeColumnsToContents()
        
    def export_data(self):
        """导出数据"""
        if not self.measurements:
            QMessageBox.warning(self, "警告", "没有数据可以导出")
            return
            
        # 获取保存路径
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出数据", f"hole_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV文件 (*.csv);;所有文件 (*)")
            
        if not file_path:
            return
            
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                
                # 写入表头
                headers = ["序号", "位置(mm)", "直径(mm)", "通道1值(μm)", "通道2值(μm)", "通道3值(μm)", "合格", "时间", "操作员", "备注"]
                writer.writerow(headers)
                
                # 写入数据
                for measurement in self.measurements:
                    row = [
                        measurement.get('sequence', ''),
                        f"{measurement.get('position', 0):.1f}",
                        f"{measurement.get('diameter', 0):.4f}",
                        f"{measurement.get('channel1', 0):.1f}",
                        f"{measurement.get('channel2', 0):.1f}",
                        f"{measurement.get('channel3', 0):.1f}",
                        "合格" if measurement.get('is_qualified', True) else "不合格",
                        measurement.get('timestamp', ''),
                        measurement.get('operator', ''),
                        measurement.get('notes', '')
                    ]
                    writer.writerow(row)
                    
            QMessageBox.information(self, "导出成功", f"数据已导出到:\n{file_path}")
            print(f"✅ 数据导出成功: {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出数据时发生错误:\n{str(e)}")
            print(f"❌ 数据导出失败: {e}")
            
    def manual_review(self):
        """人工复查"""
        if not self.measurements:
            QMessageBox.warning(self, "警告", "没有数据可以复查")
            return
            
        # 获取不合格的测量点
        unqualified_measurements = []
        for i, measurement in enumerate(self.measurements):
            if not measurement.get('is_qualified', True):
                unqualified_measurements.append((i, measurement))
                
        if not unqualified_measurements:
            QMessageBox.information(self, "信息", "所有测量点都是合格的，无需人工复查")
            return
            
        QMessageBox.information(self, "人工复查", 
                               f"发现 {len(unqualified_measurements)} 个不合格测量点\n"
                               "人工复查功能将在后续版本中实现")


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # 应用深色主题
    app.setStyleSheet("""
        QWidget {
            background-color: #313642;
            color: #D3D8E0;
            font-family: 'Microsoft YaHei', 'SimHei', Arial;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #505869;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
    """)
    
    viewer = MigratedHistoryViewer()
    viewer.show()
    
    sys.exit(app.exec())