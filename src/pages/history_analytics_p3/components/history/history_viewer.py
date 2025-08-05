"""
3.1页面 - 光谱共焦历史数据查看器
允许操作员查询、审查任一已检测孔的光谱共焦内径测量历史数据
"""

import numpy as np
import matplotlib
# 修复后端问题 - 使用PySide6兼容的后端
try:
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
                               QScrollArea, QFrame, QTabWidget, QToolButton, QMenu,
                               QHeaderView)
from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction
from PySide6.QtCore import QPoint
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import csv
import os
import glob
from datetime import datetime
import tempfile
import io


class ScrollableTextLabel(QLabel):
    """可滚动的文本标签 - 基于像素的丝滑滑动"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.full_text = ""
        self.placeholder_text = ""
        self.scroll_timer = QTimer()
        self.scroll_timer.timeout.connect(self.scroll_text)
        self.scroll_offset = 0  # 像素偏移量
        self.scroll_direction = 1  # 1 为向右滚动，-1 为向左滚动
        self.pause_counter = 0  # 用于在两端暂停
        self.max_scroll_offset = 0  # 最大滚动偏移量（像素）
        self.text_width = 0  # 文本总宽度
        self.visible_width = 0  # 可见区域宽度
        self.scroll_step = 1  # 每次滚动的像素数
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
        if text:
            super().setText(text)
            self.start_scrolling()
        else:
            super().setText(self.placeholder_text)
            self.stop_scrolling()
    
    def start_scrolling(self):
        """开始滚动"""
        # 计算文本宽度
        font_metrics = self.fontMetrics()
        self.text_width = font_metrics.horizontalAdvance(self.full_text)
        self.visible_width = self.width() - 10  # 减去padding
        
        # 如果文本宽度超过可见宽度，启动滚动
        if self.text_width > self.visible_width:
            self.max_scroll_offset = self.text_width - self.visible_width
            self.scroll_offset = 0
            self.scroll_direction = 1
            self.pause_counter = 0
            self.scroll_timer.start(30)  # 30ms刷新一次，更丝滑
        else:
            self.stop_scrolling()
    
    def stop_scrolling(self):
        """停止滚动"""
        self.scroll_timer.stop()
        self.scroll_offset = 0
    
    def scroll_text(self):
        """滚动文本"""
        if not self.full_text:
            return
            
        # 在两端暂停
        if self.scroll_offset <= 0 or self.scroll_offset >= self.max_scroll_offset:
            self.pause_counter += 1
            if self.pause_counter < 60:  # 暂停约2秒（60次 * 30ms）
                return
            else:
                self.pause_counter = 0
                self.scroll_direction *= -1  # 改变方向
        
        # 更新滚动偏移
        self.scroll_offset += self.scroll_direction * self.scroll_step
        
        # 边界检查
        if self.scroll_offset < 0:
            self.scroll_offset = 0
            self.scroll_direction = 1
        elif self.scroll_offset > self.max_scroll_offset:
            self.scroll_offset = self.max_scroll_offset
            self.scroll_direction = -1
        
        # 更新显示
        self.update()
    
    def paintEvent(self, event):
        """重写绘制事件以实现滚动效果"""
        if not self.full_text or self.text_width <= self.visible_width:
            super().paintEvent(event)
            return
        
        from PySide6.QtGui import QPainter
        painter = QPainter(self)
        
        # 设置字体和颜色
        painter.setFont(self.font())
        painter.setPen(self.palette().color(self.foregroundRole()))
        
        # 计算绘制位置
        rect = self.rect()
        text_rect = rect.adjusted(5, 5, -5, -5)  # padding
        draw_x = text_rect.x() - self.scroll_offset
        draw_y = text_rect.center().y() + self.fontMetrics().ascent() // 2
        
        # 绘制文本
        painter.drawText(draw_x, draw_y, self.full_text)
        painter.end()
    
    def resizeEvent(self, event):
        """窗口大小改变时重新计算滚动参数"""
        super().resizeEvent(event)
        if self.full_text:
            self.start_scrolling()


class ToleranceCanvas(FigureCanvas):
    """二维公差带包络图绘制画布"""

    def __init__(self, parent=None, width=8, height=6, dpi=100):
        self.figure = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.figure)
        self.setParent(parent)

        # 创建坐标系
        self.ax = self.figure.add_subplot(111)

        # 应用深色主题
        self.apply_dark_theme()

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

    def apply_dark_theme(self):
        """应用深色主题到图表"""
        # 设置图形背景色
        self.figure.patch.set_facecolor('#313642')
        self.ax.set_facecolor('#313642')

        # 设置坐标轴边框颜色
        self.ax.spines['bottom'].set_color('#505869')
        self.ax.spines['top'].set_color('#505869')
        self.ax.spines['left'].set_color('#505869')
        self.ax.spines['right'].set_color('#505869')

        # 设置坐标轴刻度颜色
        self.ax.tick_params(axis='x', colors='#D3D8E0')
        self.ax.tick_params(axis='y', colors='#D3D8E0')

        # 设置坐标轴标签颜色
        self.ax.xaxis.label.set_color('#D3D8E0')
        self.ax.yaxis.label.set_color('#D3D8E0')
        self.ax.title.set_color('#FFFFFF')

        # 设置网格颜色
        self.ax.grid(True, color='#505869', alpha=0.3)

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
        # 清除后重新应用深色主题
        self.apply_dark_theme()

        try:
            # 提取深度和直径数据
            depths = [m['depth'] for m in measurements if 'depth' in m]
            diameters = [m['diameter'] for m in measurements if 'diameter' in m]

            if not depths or not diameters:
                self.init_empty_plot()
                return

            # 绘制测量数据点
            self.ax.scatter(depths, diameters, c='#4CAF50', s=20, alpha=0.8, label='测量点')

            # 计算并绘制拟合曲线
            if len(depths) >= 3:  # 需要至少3个点才能拟合
                z = np.polyfit(depths, diameters, 2)  # 二次拟合
                p = np.poly1d(z)
                depth_range = np.linspace(min(depths), max(depths), 100)
                fitted_diameters = p(depth_range)
                self.ax.plot(depth_range, fitted_diameters, 'r--', alpha=0.7, label='拟合曲线')

            # 绘制公差带
            nominal_diameter = hole_info.get('nominal_diameter', 17.6)
            tolerance = hole_info.get('tolerance', 0.1)
            
            depth_range_full = np.linspace(0, max(depths) * 1.1, 100)
            upper_limit = [nominal_diameter + tolerance] * len(depth_range_full)
            lower_limit = [nominal_diameter - tolerance] * len(depth_range_full)
            
            self.ax.plot(depth_range_full, upper_limit, 'r-', alpha=0.5, label=f'上限 ({nominal_diameter + tolerance:.2f})')
            self.ax.plot(depth_range_full, lower_limit, 'r-', alpha=0.5, label=f'下限 ({nominal_diameter - tolerance:.2f})')
            self.ax.fill_between(depth_range_full, lower_limit, upper_limit, alpha=0.1, color='red')

            # 设置坐标轴范围
            depth_margin = (max(depths) - min(depths)) * 0.1
            diameter_margin = (max(diameters) - min(diameters)) * 0.1 if len(set(diameters)) > 1 else 0.1
            
            self.ax.set_xlim(min(depths) - depth_margin, max(depths) + depth_margin)
            self.ax.set_ylim(min(diameters) - diameter_margin, max(diameters) + diameter_margin)

            # 设置标签和标题
            self.ax.set_xlabel('深度 (mm)')
            self.ax.set_ylabel('直径 (mm)')
            self.ax.set_title(f'孔位 {hole_info.get("hole_id", "未知")} - 二维公差带包络图')
            self.ax.legend()
            self.ax.grid(True, alpha=0.3)

        except Exception as e:
            print(f"绘图错误: {e}")
            self.init_empty_plot()

        self.draw()


class HistoryViewer(QWidget):
    """
    3.1界面 - 光谱共焦历史数据查看器
    允许操作员查询、审查任一已检测孔的光谱共焦内径测量历史数据
    """
    
    # 信号定义
    data_loaded = Signal(str)  # 数据加载完成信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 当前加载的孔位ID
        self.current_hole_id = None
        
        # 初始化UI
        self.init_ui()
        
        # 加载默认示例数据
        self._load_default_sample_data()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("历史数据查看器")
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 创建标题区域
        self.create_header(main_layout)
        
        # 创建内容区域
        self.create_content_area(main_layout)
        
    def create_header(self, parent_layout):
        """创建标题区域"""
        header_group = QGroupBox("管孔直径历史数据")
        header_layout = QHBoxLayout(header_group)
        
        # 当前孔位标签
        self.hole_label = QLabel("当前孔位: 未选择")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.hole_label.setFont(font)
        
        # 数据状态标签
        self.status_label = QLabel("状态: 就绪")
        self.status_label.setStyleSheet("color: #2E7D32;")
        
        header_layout.addWidget(self.hole_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_label)
        
        parent_layout.addWidget(header_group)
        
    def create_content_area(self, parent_layout):
        """创建内容区域"""
        # 创建分割器
        self.splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：数据表格
        self.create_data_table(self.splitter)
        
        # 右侧：详细信息
        self.create_detail_panel(self.splitter)
        
        # 设置分割比例 - 确保左侧表格有足够空间
        # 使用比例分配，让布局更平衡
        self.splitter.setStretchFactor(0, 2)  # 左侧可拉伸，权重更高
        self.splitter.setStretchFactor(1, 1)  # 右侧也可拉伸
        
        # 设置最小宽度以保证可用性
        self.splitter.setChildrenCollapsible(False)  # 防止面板被完全折叠
        
        parent_layout.addWidget(self.splitter)
        
    def create_data_table(self, parent):
        """创建数据表格"""
        table_group = QGroupBox("历史测量数据")
        table_layout = QVBoxLayout(table_group)
        
        # 创建表格
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(5)
        self.data_table.setHorizontalHeaderLabels([
            "测量时间", "管孔直径(mm)", "深度(mm)", "质量等级", "备注"
        ])
        
        # 设置表格属性
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # 设置表格列自动调整模式
        header = self.data_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 测量时间 - 自适应内容
        header.setSectionResizeMode(1, QHeaderView.Interactive)  # 管孔直径 - 可手动调整
        header.setSectionResizeMode(2, QHeaderView.Interactive)  # 深度 - 可手动调整
        header.setSectionResizeMode(3, QHeaderView.Interactive)  # 质量等级 - 可手动调整
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # 备注 - 拉伸填充剩余空间
        
        # 设置表格最小尺寸，确保可见
        self.data_table.setMinimumSize(500, 300)
        
        # 设置初始列宽（用户仍可调整）
        self.data_table.setColumnWidth(0, 160)  # 测量时间
        self.data_table.setColumnWidth(1, 120)  # 管孔直径
        self.data_table.setColumnWidth(2, 100)  # 深度
        self.data_table.setColumnWidth(3, 100)  # 质量等级
        
        table_layout.addWidget(self.data_table)
        parent.addWidget(table_group)
        
    def create_detail_panel(self, parent):
        """创建详细信息面板"""
        detail_group = QGroupBox("详细信息")
        detail_group.setMinimumWidth(250)  # 设置最小宽度，防止过窄
        detail_layout = QVBoxLayout(detail_group)
        
        # 统计信息
        stats_group = QGroupBox("统计信息")
        stats_layout = QVBoxLayout(stats_group)
        
        self.total_count_label = QLabel("总测量次数: 0")
        self.avg_diameter_label = QLabel("平均直径: 0.00 mm")
        self.min_diameter_label = QLabel("最小直径: 0.00 mm")
        self.max_diameter_label = QLabel("最大直径: 0.00 mm")
        
        stats_layout.addWidget(self.total_count_label)
        stats_layout.addWidget(self.avg_diameter_label)
        stats_layout.addWidget(self.min_diameter_label)
        stats_layout.addWidget(self.max_diameter_label)
        stats_layout.addStretch()
        
        # 备注信息
        notes_group = QGroupBox("备注信息")
        notes_layout = QVBoxLayout(notes_group)
        
        self.notes_text = QTextEdit()
        self.notes_text.setMaximumHeight(100)
        self.notes_text.setPlaceholderText("选择测量记录查看备注...")
        self.notes_text.setReadOnly(True)
        
        notes_layout.addWidget(self.notes_text)
        
        detail_layout.addWidget(stats_group)
        detail_layout.addWidget(notes_group)
        detail_layout.addStretch()
        
        parent.addWidget(detail_group)
        
    def load_data_for_hole(self, hole_id: str):
        """为指定孔位加载数据"""
        print(f"📊 历史数据查看器: 加载孔位 {hole_id} 的数据")
        
        self.current_hole_id = hole_id
        self.hole_label.setText(f"当前孔位: {hole_id}")
        self.status_label.setText("状态: 加载中...")
        self.status_label.setStyleSheet("color: #FF9800;")
        
        # 模拟加载历史数据
        self._load_mock_data(hole_id)
        
        # 发射数据加载完成信号
        self.data_loaded.emit(hole_id)
        
    def _load_mock_data(self, hole_id: str):
        """加载模拟数据"""
        # 清空现有数据
        self.data_table.setRowCount(0)
        
        # 模拟历史数据
        mock_data = [
            ["2024-01-15 09:30:00", "12.50", "25.0", "优秀", "正常测量"],
            ["2024-01-14 14:20:00", "12.48", "24.8", "良好", "轻微偏差"],
            ["2024-01-13 11:45:00", "12.52", "25.2", "优秀", "标准范围内"],
            ["2024-01-12 16:10:00", "12.49", "24.9", "良好", "正常测量"],
            ["2024-01-11 10:25:00", "12.51", "25.1", "优秀", "质量良好"],
        ]
        
        # 填充表格数据
        self.data_table.setRowCount(len(mock_data))
        for row, data in enumerate(mock_data):
            for col, value in enumerate(data):
                item = QTableWidgetItem(str(value))
                self.data_table.setItem(row, col, item)
        
        # 更新统计信息
        diameters = [float(data[1]) for data in mock_data]
        self.total_count_label.setText(f"总测量次数: {len(mock_data)}")
        self.avg_diameter_label.setText(f"平均直径: {sum(diameters)/len(diameters):.2f} mm")
        self.min_diameter_label.setText(f"最小直径: {min(diameters):.2f} mm")
        self.max_diameter_label.setText(f"最大直径: {max(diameters):.2f} mm")
        
        # 更新状态
        self.status_label.setText("状态: 数据加载完成")
        self.status_label.setStyleSheet("color: #2E7D32;")
        
        print(f"✅ 历史数据查看器: 孔位 {hole_id} 数据加载完成 ({len(mock_data)} 条记录)")
    
    def _load_default_sample_data(self):
        """加载默认示例数据供演示"""
        # 设置初始状态
        self.hole_label.setText("当前孔位: 未选择")
        self.status_label.setText("状态: 就绪")
        self.status_label.setStyleSheet("color: #2E7D32;")
        
        # 加载示例数据展示表格功能
        sample_data = [
            ["2024-01-15 09:30:00", "12.50", "25.0", "优秀", "正常测量"],
            ["2024-01-14 14:20:00", "12.48", "24.8", "良好", "轻微偏差"],
            ["2024-01-13 11:45:00", "12.52", "25.2", "优秀", "标准范围内"],
            ["2024-01-12 16:10:00", "12.49", "24.9", "良好", "正常测量"],
            ["2024-01-11 10:25:00", "12.51", "25.1", "优秀", "质量良好"],
        ]
        
        # 填充表格数据
        self.data_table.setRowCount(len(sample_data))
        for row, data in enumerate(sample_data):
            for col, value in enumerate(data):
                item = QTableWidgetItem(str(value))
                self.data_table.setItem(row, col, item)
        
        # 更新统计信息
        diameters = [float(data[1]) for data in sample_data]
        self.total_count_label.setText(f"总测量次数: {len(sample_data)}")
        self.avg_diameter_label.setText(f"平均直径: {sum(diameters)/len(diameters):.2f} mm")
        self.min_diameter_label.setText(f"最小直径: {min(diameters):.2f} mm")
        self.max_diameter_label.setText(f"最大直径: {max(diameters):.2f} mm")
        
        print("✅ 历史数据查看器: 默认示例数据加载完成")
        
    def showEvent(self, event):
        """窗口显示时调整布局"""
        super().showEvent(event)
        # 根据实际窗口大小设置分割器比例
        if hasattr(self, 'splitter'):
            total_width = self.width()
            if total_width > 0:
                left_width = int(total_width * 0.65)  # 65% 给表格
                right_width = int(total_width * 0.35)  # 35% 给详情面板
                self.splitter.setSizes([left_width, right_width])
    
    def cleanup(self):
        """清理资源"""
        print("🧹 历史数据查看器: 清理资源")
        self.current_hole_id = None
        self.data_table.clear()