"""
实时图表组件 - 高保真度还原原项目设计
基于原项目RealtimeChart类，使用高内聚、低耦合的架构重新实现
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

# 导入matplotlib相关
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib

# 设置matplotlib支持中文显示
def setup_safe_chinese_font():
    """设置安全的中文字体支持"""
    try:
        matplotlib.rcParams['font.family'] = 'sans-serif'
        matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC', 'SimHei', 'DejaVu Sans']
        matplotlib.rcParams['axes.unicode_minus'] = False
        print("✅ 安全字体配置完成")
    except Exception as e:
        print(f"⚠️ 字体配置失败，使用默认: {e}")
        matplotlib.rcParams['font.family'] = 'DejaVu Sans'

# 初始化安全字体配置
setup_safe_chinese_font()

# 导入内窥镜视图
try:
    from src.modules.endoscope_view import EndoscopeView
    HAS_ENDOSCOPE = True
except ImportError as e:
    logging.error(f"无法导入内窥镜视图: {e}")
    HAS_ENDOSCOPE = False

# 导入自动化工作器
try:
    from src.modules.automation_worker import AutomationWorker
    HAS_AUTOMATION = True
except ImportError as e:
    logging.error(f"无法导入自动化工作器: {e}")
    HAS_AUTOMATION = False


class ArchiveWorker(QObject):
    """在后台线程中执行文件归档任务的工人"""
    log_message = Signal(str)  # 用于向主界面发送日志信息
    finished = Signal(str)     # 任务完成时发射信号

    def __init__(self, source_path, base_archive_path):
        super().__init__()
        self.source_path = source_path
        self.base_archive_path = base_archive_path

    def run_archive(self):
        """执行归档的核心逻辑"""
        try:
            self.log_message.emit("📦 开始后台归档任务...")
            if not os.path.exists(self.source_path):
                raise FileNotFoundError(f"源文件不存在: {self.source_path}")

            # 确定下一个文件夹名称
            next_folder_name = self._get_next_folder_name()
            self.log_message.emit(f"   - 计算下一个归档文件夹为: {next_folder_name}")

            # 创建文件夹结构
            ccidm_path = os.path.join(self.base_archive_path, next_folder_name, "CCIDM")
            bisdm_path = os.path.join(self.base_archive_path, next_folder_name, "BISDM")
            os.makedirs(ccidm_path, exist_ok=True)
            os.makedirs(bisdm_path, exist_ok=True)
            self.log_message.emit(f"   - 已创建目录: {ccidm_path}")
            self.log_message.emit(f"   - 已创建目录: {bisdm_path}")

            # 确定最终文件名并移动文件
            final_filename = f"{next_folder_name}.csv"
            destination_path = os.path.join(ccidm_path, final_filename)

            self.log_message.emit(f"   - 准备移动文件: '{os.path.basename(self.source_path)}' -> '{destination_path}'")
            import shutil
            shutil.move(self.source_path, destination_path)

            self.finished.emit(f"✅ 归档成功！文件已存至: {destination_path}")

        except Exception as e:
            error_info = f"❌ 后台归档失败: {e}\n{traceback.format_exc()}"
            self.log_message.emit(error_info)
            self.finished.emit(error_info)

    def _get_next_folder_name(self):
        """扫描基础路径，确定下一个RxxxCxxx文件夹的名称"""
        import re
        
        if not os.path.exists(self.base_archive_path):
            os.makedirs(self.base_archive_path, exist_ok=True)
            return "R001C001"

        # 扫描现有文件夹，找到最大的编号
        existing_folders = []
        for item in os.listdir(self.base_archive_path):
            item_path = os.path.join(self.base_archive_path, item)
            if os.path.isdir(item_path):
                match = re.match(r'R(\d{3})C(\d{3})', item)
                if match:
                    r_num = int(match.group(1))
                    c_num = int(match.group(2))
                    existing_folders.append((r_num, c_num))

        if not existing_folders:
            return "R001C001"

        # 找到最大的C编号
        max_r, max_c = max(existing_folders, key=lambda x: (x[0], x[1]))
        next_c = max_c + 1

        return f"R001C{next_c:03d}"


class RealtimeChart(QWidget):
    """
    实时图表组件 - 高保真度还原原项目设计
    面板A: 管孔直径数据实时折线图
    面板B: 内窥镜实时图像显示
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_hole_id = None
        self.is_data_loaded = False  # 标记是否已加载数据
        
        # 线程管理与路径配置
        self.automation_thread = None
        self.automation_worker = None
        
        # 路径配置 - 按照原项目结构
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file_dir)))
        self.acquisition_program_path = os.path.join(project_root, "src", "hardware", "Release", "LEConfocalDemo.exe")
        self.launcher_script_path = os.path.join(project_root, "src", "automation", "launcher.py")
        self.remote_launcher_path = os.path.join(project_root, "remote_launcher.py")
        
        # CSV输出文件路径
        self.csv_output_folder = os.path.join(project_root, "src", "hardware", "Release")
        self.output_csv_path = os.path.join(self.csv_output_folder, "R0_C0.csv")
        
        # 归档路径
        self.archive_base_path = os.path.join(project_root, "Data", "CAP1000")
        self.archive_thread = None
        self.archive_worker = None
        
        # 文件生成监视器
        self.csv_watcher = QFileSystemWatcher(self)
        self.csv_watcher.directoryChanged.connect(self.on_directory_changed)
        
        self.setup_ui()
        self.setup_chart()
        self.init_data_buffers()
        self.setup_waiting_state()  # 设置等待状态
        
    def setup_ui(self):
        """设置用户界面布局 - 双面板设计"""
        layout = QVBoxLayout(self)
        
        # 状态信息面板 - 完全按照原项目的水平布局
        status_group = QGroupBox("状态监控与主控制区")
        status_group.setObjectName("StatusDashboard")
        status_layout = QHBoxLayout(status_group)
        status_layout.setContentsMargins(10, 10, 10, 10)
        status_layout.setSpacing(15)

        # 按照原项目顺序：当前孔位 | 标准直径 | 最大直径 | 最小直径 | 控制按钮

        # 当前孔位显示
        self.current_hole_label = QLabel("当前孔位: 未选择")
        self.current_hole_label.setObjectName("InfoLabel")
        self.current_hole_label.setMinimumWidth(140)
        status_layout.addWidget(self.current_hole_label)

        # 标准直径显示
        self.standard_diameter_label = QLabel("标准直径: 17.73mm")
        self.standard_diameter_label.setObjectName("StaticInfoLabel")
        self.standard_diameter_label.setMinimumWidth(140)
        status_layout.addWidget(self.standard_diameter_label)

        # 最大直径显示
        self.max_diameter_label = QLabel("最大直径: -- mm")
        self.max_diameter_label.setObjectName("StatusLabel")
        self.max_diameter_label.setMinimumWidth(140)
        status_layout.addWidget(self.max_diameter_label)

        # 最小直径显示
        self.min_diameter_label = QLabel("最小直径: -- mm")
        self.min_diameter_label.setObjectName("StatusLabel")
        self.min_diameter_label.setMinimumWidth(140)
        status_layout.addWidget(self.min_diameter_label)

        # 添加弹性空间
        status_layout.addStretch(1)

        # 右侧：主控制按钮区域 - 按照原项目样式
        control_layout = QHBoxLayout()
        control_layout.setSpacing(8)

        # 创建主控制按钮 - 按照原项目的文本和颜色
        self.start_button = QPushButton("开始监测")
        self.stop_button = QPushButton("停止监测")
        self.clear_button = QPushButton("清除数据")

        # 设置按钮样式 - 按照原项目
        self.start_button.setObjectName("StartButton")
        self.stop_button.setObjectName("StopButton")
        self.clear_button.setObjectName("ClearDataButton")

        # 设置按钮大小
        button_size = (80, 30)
        self.start_button.setFixedSize(*button_size)
        self.stop_button.setFixedSize(*button_size)
        self.clear_button.setFixedSize(*button_size)

        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.clear_button)

        status_layout.addLayout(control_layout)
        layout.addWidget(status_group)
        
        # 自动化控制日志窗口
        log_group = QGroupBox("自动化控制日志")
        log_layout = QVBoxLayout(log_group)
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setMaximumHeight(150)
        log_layout.addWidget(self.log_text_edit)
        layout.addWidget(log_group)
        
        # 双面板区域 - 垂直布局（A在上，B在下）
        splitter = QSplitter(Qt.Vertical)
        
        # 面板A: 管孔直径数据
        self.create_panel_a(splitter)
        
        # 面板B: 内窥镜图像
        if HAS_ENDOSCOPE:
            self.endoscope_view = EndoscopeView()
            self.endoscope_view.setObjectName("EndoscopeWidget")
            splitter.addWidget(self.endoscope_view)
        else:
            # 创建占位符
            placeholder = QLabel("内窥镜视图不可用")
            placeholder.setAlignment(Qt.AlignCenter)
            splitter.addWidget(placeholder)
        
        layout.addWidget(splitter)
        self.main_splitter = splitter
        
        # 延迟设置分割器比例
        QTimer.singleShot(100, lambda: self.safe_adjust_splitter_sizes(splitter))

        # 初始化孔位数据映射
        self.init_hole_data_mapping()

        # 设置信号连接
        self.setup_connections()

        # 初始状态下启用开始按钮，支持直接启动采集程序
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.clear_button.setEnabled(True)

        # 设置按钮提示
        self.start_button.setToolTip("启动采集控制程序 (LEConfocalDemo.exe)")
        self.stop_button.setToolTip("停止采集控制程序")
        self.clear_button.setToolTip("清除当前数据")

        # 采集程序相关属性
        self.acquisition_process = None
        self.remote_launcher_process = None

        # 实时CSV监控相关属性
        self.csv_monitor = None
        self.is_realtime_monitoring = False
        self.last_csv_file = None
        self.csv_file_monitor_timer = None
        self.last_file_size = 0

        # CSV播放相关属性
        self.is_csv_playing = False
        self.csv_timer = None
        self.csv_data = []
        self.csv_data_index = 0
        self.csv_file_list = []
        self.current_file_index = 0

        # 标准直径和公差设置
        self.standard_diameter = 17.73
        self.target_diameter = 17.73
        self.tolerance = 0.07
        self.upper_tolerance = 0.07
        self.lower_tolerance = 0.05

    def create_panel_a(self, splitter):
        """创建面板A: 管孔直径数据 - 完全按照原项目布局"""
        panel_a_widget = QWidget()
        panel_a_widget.setObjectName("PanelAWidget")
        panel_a_layout = QHBoxLayout(panel_a_widget)
        panel_a_layout.setContentsMargins(8, 8, 8, 8)
        panel_a_layout.setSpacing(10)

        # 面板A左侧：图表区域（matplotlib）
        chart_widget = QWidget()
        chart_widget.setObjectName("ChartWidget")
        chart_layout = QVBoxLayout(chart_widget)
        chart_layout.setContentsMargins(0, 0, 0, 0)

        # 创建图表标题栏
        chart_header = QWidget()
        chart_header.setObjectName("PanelHeader")
        chart_header_layout = QHBoxLayout(chart_header)
        chart_header_layout.setContentsMargins(15, 0, 15, 0)
        chart_header_layout.setSpacing(10)

        chart_title = QLabel("管孔直径实时监测")
        chart_title.setObjectName("PanelHeaderText")

        # 添加工具按钮
        export_chart_button = QToolButton()
        export_chart_button.setObjectName("HeaderToolButton")
        export_chart_button.setText("📊")
        export_chart_button.setToolTip("导出图表为图片")

        refresh_chart_button = QToolButton()
        refresh_chart_button.setObjectName("HeaderToolButton")
        refresh_chart_button.setText("🔄")
        refresh_chart_button.setToolTip("刷新图表")

        chart_header_layout.addWidget(chart_title)
        chart_header_layout.addStretch()
        chart_header_layout.addWidget(refresh_chart_button)
        chart_header_layout.addWidget(export_chart_button)

        chart_layout.addWidget(chart_header)

        # 创建matplotlib图形
        self.figure = Figure(figsize=(24, 12), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        chart_layout.addWidget(self.canvas)

        # 连接鼠标事件
        self.canvas.mpl_connect('scroll_event', self.on_scroll)
        self.canvas.mpl_connect('button_press_event', self.on_mouse_press)

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

        panel_a_layout.addWidget(chart_widget)

        # 面板A右侧：异常数据显示区域和按钮
        right_panel = QWidget()
        right_panel.setObjectName("RightPanel")
        right_panel.setMinimumWidth(320)
        right_panel.setMaximumWidth(400)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(8)

        # 异常监控窗口
        self.create_anomaly_panel(right_layout)

        # 添加固定间距
        right_layout.addSpacing(15)

        # 添加【查看下一个样品】按钮
        self.next_sample_button = QPushButton("查看下一个样品")
        self.next_sample_button.clicked.connect(self.view_next_sample)
        self.next_sample_button.setObjectName("next_sample_button")
        self.next_sample_button.setMinimumHeight(35)
        right_layout.addWidget(self.next_sample_button)

        # 添加底部间距
        right_layout.addSpacing(10)

        panel_a_layout.addWidget(right_panel)
        splitter.addWidget(panel_a_widget)
        panel_a_layout.setSpacing(5)

        # 左侧：图表区域 - 按照原项目占据大部分空间
        chart_container = self.create_chart_container()
        panel_a_layout.addWidget(chart_container, 3)  # 占3/4空间

        # 右侧：异常监控面板 - 按照原项目样式
        self.create_anomaly_panel(panel_a_layout)  # 占1/4空间

        splitter.addWidget(panel_a_widget)

    def create_chart_container(self):
        """创建图表容器 - 按照原项目样式"""
        chart_widget = QWidget()
        chart_widget.setObjectName("ChartWidget")
        chart_layout = QVBoxLayout(chart_widget)
        chart_layout.setContentsMargins(5, 5, 5, 5)
        chart_layout.setSpacing(5)

        # 创建图表标题栏 - 按照原项目样式
        chart_header = QWidget()
        chart_header.setObjectName("PanelHeader")
        chart_header_layout = QHBoxLayout(chart_header)
        chart_header_layout.setContentsMargins(10, 5, 10, 5)
        chart_header_layout.setSpacing(10)

        chart_title = QLabel("管孔直径实时监测")
        chart_title.setObjectName("PanelHeaderText")
        chart_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")

        chart_header_layout.addWidget(chart_title)
        chart_layout.addWidget(chart_header)

        # 创建matplotlib图形 - 按照原项目大小
        self.figure = Figure(figsize=(12, 8), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        chart_layout.addWidget(self.canvas)

        # 连接鼠标事件
        self.canvas.mpl_connect('scroll_event', self.on_scroll)
        self.canvas.mpl_connect('button_press_event', self.on_mouse_press)

        # 创建子图
        self.ax = self.figure.add_subplot(111)
        self.apply_matplotlib_dark_theme()
        self.ax.set_xlabel('深度 (mm)', fontsize=12, fontweight='bold')
        self.ax.set_ylabel('直径 (mm)', fontsize=12, fontweight='bold')
        self.ax.grid(True, alpha=0.3)

        # 设置坐标轴刻度字体大小
        self.ax.tick_params(axis='both', which='major', labelsize=10)
        self.ax.tick_params(axis='both', which='minor', labelsize=8)

        # 设置初始范围 - 按照原项目
        self.ax.set_ylim(16.5, 20.5)
        self.ax.set_xlim(0, 800)

        # 初始化数据线
        self.data_line, = self.ax.plot([], [], color='#4A90E2', linewidth=2, label='直径数据')

        # 设置图形样式
        self.figure.subplots_adjust(left=0.1, bottom=0.12, right=0.95, top=0.9)
        self.ax.legend(loc='upper right', fontsize=10)

        return chart_widget

    def create_anomaly_panel(self, parent_layout):
        """创建异常数据显示面板 - 完全按照原项目布局"""
        right_panel = QWidget()
        right_panel.setObjectName("RightPanel")
        right_panel.setMinimumWidth(280)
        right_panel.setMaximumWidth(320)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(8)

        # 异常监控窗口 - 按照原项目样式
        anomaly_widget = QGroupBox("异常直径监控")
        anomaly_widget.setObjectName("anomaly_widget")
        anomaly_layout = QVBoxLayout(anomaly_widget)
        anomaly_layout.setContentsMargins(10, 15, 10, 10)
        anomaly_layout.setSpacing(8)

        # 异常统计信息 - 按照原项目的精确布局
        stats_widget = self.create_original_stats_widget()
        anomaly_layout.addWidget(stats_widget)

        # 异常数据显示区域 - 按照原项目大小
        self.anomaly_scroll = QScrollArea()
        self.anomaly_scroll.setWidgetResizable(True)
        self.anomaly_scroll.setObjectName("anomaly_scroll")
        self.anomaly_scroll.setMinimumHeight(120)
        self.anomaly_scroll.setMaximumHeight(180)

        # 异常内容容器
        self.anomaly_content_widget = QWidget()
        self.anomaly_content_layout = QVBoxLayout(self.anomaly_content_widget)
        self.anomaly_content_layout.setContentsMargins(5, 5, 5, 5)
        self.anomaly_content_layout.setSpacing(3)

        # 添加占位文本
        placeholder_label = QLabel("暂无异常数据")
        placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_label.setStyleSheet("color: #888; font-style: italic;")
        self.anomaly_content_layout.addWidget(placeholder_label)

        self.anomaly_scroll.setWidget(self.anomaly_content_widget)
        anomaly_layout.addWidget(self.anomaly_scroll)

        right_layout.addWidget(anomaly_widget)
        right_layout.addStretch(1)  # 添加弹性空间

        # 添加【查看下一个样品】按钮 - 按照原项目样式
        self.next_sample_button = QPushButton("查看下一个样品")
        self.next_sample_button.clicked.connect(self.view_next_sample)
        self.next_sample_button.setObjectName("next_sample_button")
        self.next_sample_button.setMinimumHeight(35)
        right_layout.addWidget(self.next_sample_button)

        parent_layout.addWidget(right_panel)



    def create_original_stats_widget(self):
        """创建原项目的统计信息组件 - 完全按照原项目布局"""
        from PySide6.QtWidgets import QGridLayout

        stats_widget = QWidget()
        stats_widget.setFixedHeight(60)
        stats_layout = QGridLayout(stats_widget)
        stats_layout.setContentsMargins(10, 5, 10, 5)
        stats_layout.setSpacing(8)

        # 大号数字显示异常计数 - 按照原项目样式
        self.anomaly_count_number = QLabel("0")
        self.anomaly_count_number.setObjectName("AnomalyCountLabel")
        self.anomaly_count_number.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #E74C3C;
                text-align: right;
            }
        """)

        # 异常计数说明文字
        count_text_label = QLabel("个异常点")
        count_text_label.setObjectName("AnomalyUnitLabel")
        count_text_label.setStyleSheet("font-size: 12px; color: #666;")

        # 异常率显示
        self.anomaly_rate_label = QLabel("异常率: 0.0%")
        self.anomaly_rate_label.setObjectName("AnomalyRateLabel")
        self.anomaly_rate_label.setStyleSheet("font-size: 12px; color: #666;")

        # 将控件放入网格布局 - 按照原项目的精确位置
        # 第0行，第0列：大号数字，右对齐
        stats_layout.addWidget(self.anomaly_count_number, 0, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # 第0行，第1列：单位文字，左对齐并垂直居中
        stats_layout.addWidget(count_text_label, 0, 1, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # 第0行，第2列：异常率，右对齐并垂直居中
        stats_layout.addWidget(self.anomaly_rate_label, 0, 2, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # 设置列的伸缩比例，让中间有适当的空间
        stats_layout.setColumnStretch(0, 0)  # 大号数字列不伸缩
        stats_layout.setColumnStretch(1, 1)  # 单位文字列可以伸缩，提供间距
        stats_layout.setColumnStretch(2, 0)  # 异常率列不伸缩

        return stats_widget

    def reset_csv_playback(self):
        """重置CSV播放"""
        try:
            self.stop_csv_playback()
            self.csv_data_index = 0
            self.clear_plot_data()
            self.log_message("🔄 CSV播放已重置")
        except Exception as e:
            self.log_message(f"❌ 重置CSV播放失败: {e}")

    def setup_chart(self):
        """设置图表"""
        # 图表已在create_panel_a中设置
        pass

    def init_data_buffers(self):
        """初始化数据缓冲区"""
        self.depth_data = deque(maxlen=10000)
        self.diameter_data = deque(maxlen=10000)
        self.anomaly_data = []

    def init_hole_data_mapping(self):
        """初始化孔位数据映射 - 完全按照原项目"""
        # 获取项目根目录
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file_dir)))

        # 孔位到CSV目录的映射 - 与原项目完全一致
        self.hole_to_csv_map = {
            "R001C001": os.path.join(project_root, "Data", "CAP1000", "R001C001", "CCIDM"),
            "R001C002": os.path.join(project_root, "Data", "CAP1000", "R001C002", "CCIDM"),
            "R001C003": os.path.join(project_root, "Data", "CAP1000", "R001C003", "CCIDM"),
            "R001C004": os.path.join(project_root, "Data", "CAP1000", "R001C004", "CCIDM")
        }

        # 孔位到图像目录的映射
        self.hole_to_image_map = {
            "R001C001": os.path.join(project_root, "Data", "CAP1000", "R001C001", "BISDM", "result"),
            "R001C002": os.path.join(project_root, "Data", "CAP1000", "R001C002", "BISDM", "result"),
            "R001C003": os.path.join(project_root, "Data", "CAP1000", "R001C003", "BISDM", "result"),
            "R001C004": os.path.join(project_root, "Data", "CAP1000", "R001C004", "BISDM", "result")
        }

        print("✅ 孔位数据映射初始化完成")
        for hole_id, csv_path in self.hole_to_csv_map.items():
            print(f"   {hole_id}: {csv_path}")

    def setup_waiting_state(self):
        """设置等待状态"""
        self.current_hole_label.setText("当前孔位: 未选择")
        self.max_diameter_label.setText("最大直径: -- mm")
        self.min_diameter_label.setText("最小直径: -- mm")

        # 设置按钮状态
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def setup_connections(self):
        """设置信号连接"""
        # 控制按钮连接 - 使用原项目的方法名
        self.start_button.clicked.connect(self.start_automation_task)
        self.stop_button.clicked.connect(self.stop_automation_task)
        self.clear_button.clicked.connect(self.clear_data)

    def safe_adjust_splitter_sizes(self, splitter):
        """安全地调整分割器大小"""
        try:
            total_height = splitter.height()
            if total_height > 100:  # 确保有足够的高度
                panel_a_height = int(total_height * 0.65)  # 面板A占65%
                panel_b_height = total_height - panel_a_height  # 面板B占35%
                splitter.setSizes([panel_a_height, panel_b_height])
        except Exception as e:
            print(f"调整分割器大小失败: {e}")

    def apply_matplotlib_dark_theme(self):
        """应用matplotlib深色主题"""
        try:
            self.figure.patch.set_facecolor('#2b2b2b')
            self.ax.set_facecolor('#2b2b2b')
            self.ax.xaxis.label.set_color('white')
            self.ax.yaxis.label.set_color('white')
            self.ax.tick_params(colors='white')
            for spine in self.ax.spines.values():
                spine.set_color('white')
        except Exception as e:
            print(f"应用深色主题失败: {e}")

    def on_scroll(self, event):
        """鼠标滚轮缩放事件"""
        try:
            if event.inaxes != self.ax:
                return

            # 获取当前坐标轴范围
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()

            # 计算缩放因子
            scale_factor = 1.1 if event.step > 0 else 1/1.1

            # 计算新的范围
            x_center = (xlim[0] + xlim[1]) / 2
            y_center = (ylim[0] + ylim[1]) / 2

            x_range = (xlim[1] - xlim[0]) * scale_factor / 2
            y_range = (ylim[1] - ylim[0]) * scale_factor / 2

            # 设置新的范围
            self.ax.set_xlim(x_center - x_range, x_center + x_range)
            self.ax.set_ylim(y_center - y_range, y_center + y_range)

            self.canvas.draw_idle()
        except Exception as e:
            print(f"缩放事件处理失败: {e}")

    def on_mouse_press(self, event):
        """鼠标点击事件"""
        try:
            if event.button == 3 and event.inaxes == self.ax:  # 右键点击
                # 重置视图
                self.ax.set_xlim(0, 950)
                self.ax.set_ylim(16.5, 20.5)
                self.canvas.draw_idle()
        except Exception as e:
            print(f"鼠标点击事件处理失败: {e}")

    def view_next_sample(self):
        """查看下一个样品"""
        print("🔄 切换到下一个样品")
        # 这里可以添加样品切换逻辑

    def on_directory_changed(self, path):
        """目录变化监控"""
        print(f"📁 目录变化: {path}")
        # 这里可以添加文件监控逻辑

    # === 核心自动化任务方法 ===

    def start_automation_task(self):
        """启动自动化任务 - 完全按照原项目实现"""
        try:
            self.log_message("🚀 启动自动化任务...")

            # 更新按钮状态
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)

            # 更新状态显示 - 使用日志消息代替通信状态标签
            self.log_message("● 通信状态：启动中")

            # 启动采集程序
            self.start_acquisition_program()

            # 启动文件监控
            self.start_file_monitoring()

            self.log_message("✅ 自动化任务启动完成")

        except Exception as e:
            self.log_message(f"❌ 启动自动化任务失败: {e}")
            # 恢复按钮状态
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def stop_automation_task(self):
        """停止自动化任务 - 完全按照原项目实现"""
        try:
            self.log_message("⏸️ 停止自动化任务...")

            # 停止文件监控
            self.stop_file_monitoring()

            # 停止采集程序
            self.stop_acquisition_program()

            # 更新按钮状态
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)

            # 更新状态显示 - 使用日志消息代替通信状态标签
            self.log_message("○ 通信状态：已停止")

            self.log_message("✅ 自动化任务已停止")

        except Exception as e:
            self.log_message(f"❌ 停止自动化任务失败: {e}")

    def start_acquisition_program(self):
        """启动采集程序 - LEConfocalDemo.exe"""
        try:
            if not os.path.exists(self.acquisition_program_path):
                self.log_message(f"❌ 采集程序不存在: {self.acquisition_program_path}")
                return False

            # 启动采集程序
            import subprocess
            self.acquisition_process = subprocess.Popen(
                [self.acquisition_program_path],
                cwd=os.path.dirname(self.acquisition_program_path)
            )

            self.log_message(f"✅ 采集程序已启动: PID {self.acquisition_process.pid}")
            self.log_message("● 通信状态：采集程序运行中")

            return True

        except Exception as e:
            self.log_message(f"❌ 启动采集程序失败: {e}")
            return False

    def stop_acquisition_program(self):
        """停止采集程序"""
        try:
            if self.acquisition_process and self.acquisition_process.poll() is None:
                self.acquisition_process.terminate()
                self.log_message("✅ 采集程序已停止")
            else:
                self.log_message("ℹ️ 采集程序未运行")

        except Exception as e:
            self.log_message(f"❌ 停止采集程序失败: {e}")

    def start_file_monitoring(self):
        """启动文件监控"""
        try:
            # 监控CSV输出文件夹
            if os.path.exists(self.csv_output_folder):
                self.csv_watcher.addPath(self.csv_output_folder)
                self.log_message(f"✅ 开始监控文件夹: {self.csv_output_folder}")
            else:
                self.log_message(f"⚠️ 监控文件夹不存在: {self.csv_output_folder}")

            self.is_realtime_monitoring = True

        except Exception as e:
            self.log_message(f"❌ 启动文件监控失败: {e}")

    def stop_file_monitoring(self):
        """停止文件监控"""
        try:
            # 停止监控
            paths = self.csv_watcher.directories()
            for path in paths:
                self.csv_watcher.removePath(path)

            self.is_realtime_monitoring = False
            self.log_message("✅ 文件监控已停止")

        except Exception as e:
            self.log_message(f"❌ 停止文件监控失败: {e}")

    # === 核心功能方法 ===

    def load_data_for_hole(self, hole_id):
        """为指定的孔加载并显示其对应的CSV数据和内窥镜图片 - 完全按照原项目实现"""
        try:
            self.current_hole_id = hole_id
            self.current_hole_label.setText(f"当前孔位：{hole_id}")

            if hole_id not in self.hole_to_csv_map:
                self.log_message(f"⚠️ 孔 {hole_id} 没有关联的CSV数据文件")
                return

            csv_dir = self.hole_to_csv_map[hole_id]
            self.log_message(f"🔄 为孔 {hole_id} 加载数据目录: {csv_dir}")

            # 查找目录中的CSV文件
            csv_file = None
            if os.path.exists(csv_dir):
                try:
                    files_in_dir = os.listdir(csv_dir)
                    self.log_message(f"📁 目录中的文件: {files_in_dir}")

                    for file in files_in_dir:
                        if file.endswith('.csv'):
                            csv_file = os.path.join(csv_dir, file)
                            self.log_message(f"✅ 找到CSV文件: {file}")
                            break

                    if not csv_file:
                        self.log_message(f"❌ 目录中没有CSV文件")
                        return

                except Exception as e:
                    self.log_message(f"❌ 读取目录失败: {e}")
                    return
            else:
                self.log_message(f"❌ 目录不存在: {csv_dir}")
                return

            # 加载CSV数据
            if self.load_csv_data_from_file(csv_file):
                # 加载内窥镜图像
                if hole_id in self.hole_to_image_map:
                    image_dir = self.hole_to_image_map[hole_id]
                    if HAS_ENDOSCOPE and hasattr(self, 'endoscope_view'):
                        if os.path.exists(image_dir):
                            self.endoscope_view.load_images_from_folder(image_dir)
                            self.log_message(f"✅ 已加载内窥镜图像: {image_dir}")
                        else:
                            self.log_message(f"⚠️ 图像路径不存在: {image_dir}")

                self.is_data_loaded = True
                self.log_message(f"✅ 成功从主检测界面加载孔位 {hole_id} 的数据")
            else:
                self.log_message(f"❌ 无法加载文件: {csv_file}")

        except Exception as e:
            self.log_message(f"❌ 加载孔位数据失败: {e}")
            import traceback
            self.log_message(f"详细错误: {traceback.format_exc()}")

    def load_csv_data_from_file(self, csv_file_path):
        """从文件加载CSV数据 - 完全按照原项目实现"""
        try:
            import pandas as pd

            self.log_message(f"📊 开始加载CSV文件: {os.path.basename(csv_file_path)}")

            # 读取CSV文件
            df = pd.read_csv(csv_file_path)
            self.log_message(f"✅ CSV文件读取成功，共 {len(df)} 行数据")

            # 检查必要的列
            required_columns = ['depth', 'diameter']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.log_message(f"❌ CSV文件缺少必要列: {missing_columns}")
                return False

            # 清除现有数据
            self.clear_data()

            # 存储CSV数据用于播放
            self.csv_data = []
            for _, row in df.iterrows():
                self.csv_data.append({
                    'depth': float(row['depth']),
                    'diameter': float(row['diameter'])
                })

            self.log_message(f"✅ 已加载 {len(self.csv_data)} 个数据点")

            # 立即显示所有数据
            depths = [point['depth'] for point in self.csv_data]
            diameters = [point['diameter'] for point in self.csv_data]

            # 更新数据缓冲区
            self.depth_data.extend(depths)
            self.diameter_data.extend(diameters)

            # 更新图表
            self.update_plot()

            # 更新统计信息
            if diameters:
                max_diameter = max(diameters)
                min_diameter = min(diameters)
                self.max_diameter_label.setText(f"📈 最大直径: {max_diameter:.3f} mm")
                self.min_diameter_label.setText(f"📉 最小直径: {min_diameter:.3f} mm")

            # 检测异常
            self.detect_anomalies()

            return True

        except Exception as e:
            self.log_message(f"❌ 加载CSV数据失败: {e}")
            import traceback
            self.log_message(f"详细错误: {traceback.format_exc()}")
            return False

    def load_csv_data(self, csv_file_path):
        """加载CSV数据"""
        try:
            import pandas as pd

            # 读取CSV文件
            df = pd.read_csv(csv_file_path)

            # 假设CSV文件有 'depth' 和 'diameter' 列
            if 'depth' in df.columns and 'diameter' in df.columns:
                depths = df['depth'].values
                diameters = df['diameter'].values

                # 清除现有数据
                self.depth_data.clear()
                self.diameter_data.clear()

                # 添加新数据
                for depth, diameter in zip(depths, diameters):
                    self.depth_data.append(depth)
                    self.diameter_data.append(diameter)

                # 更新图表
                self.update_plot()

                # 更新统计信息
                if len(diameters) > 0:
                    max_diameter = np.max(diameters)
                    min_diameter = np.min(diameters)
                    self.max_diameter_label.setText(f"📈 最大直径: {max_diameter:.3f} mm")
                    self.min_diameter_label.setText(f"📉 最小直径: {min_diameter:.3f} mm")

                self.log_message(f"✅ 已加载 {len(diameters)} 个数据点")

            else:
                self.log_message(f"⚠️ CSV文件格式不正确，缺少 'depth' 或 'diameter' 列")

        except Exception as e:
            self.log_message(f"❌ 加载CSV数据失败: {e}")

    def detect_anomalies(self):
        """检测异常数据 - 完全按照原项目实现"""
        try:
            if not self.csv_data:
                return

            # 清除现有异常数据
            self.anomaly_data.clear()

            # 清除异常显示
            for i in reversed(range(self.anomaly_content_layout.count())):
                child = self.anomaly_content_layout.itemAt(i).widget()
                if child:
                    child.setParent(None)

            # 检测异常
            anomaly_count = 0
            for i, point in enumerate(self.csv_data):
                diameter = point['diameter']
                depth = point['depth']

                # 检查是否超出公差范围
                upper_limit = self.target_diameter + self.upper_tolerance
                lower_limit = self.target_diameter - self.lower_tolerance

                if diameter > upper_limit or diameter < lower_limit:
                    anomaly_count += 1
                    anomaly_info = {
                        'index': i,
                        'depth': depth,
                        'diameter': diameter,
                        'deviation': diameter - self.target_diameter
                    }
                    self.anomaly_data.append(anomaly_info)

                    # 添加到异常显示
                    self.add_anomaly_to_display(anomaly_info)

            self.log_message(f"🔍 异常检测完成，发现 {anomaly_count} 个异常点")

        except Exception as e:
            self.log_message(f"❌ 异常检测失败: {e}")

    def add_anomaly_to_display(self, anomaly_info):
        """添加异常信息到显示面板"""
        try:
            from PySide6.QtWidgets import QFrame

            # 创建异常信息框
            anomaly_frame = QFrame()
            anomaly_frame.setObjectName("anomaly_frame")
            anomaly_frame.setFrameStyle(QFrame.Box)

            anomaly_layout = QVBoxLayout(anomaly_frame)
            anomaly_layout.setContentsMargins(5, 5, 5, 5)
            anomaly_layout.setSpacing(2)

            # 异常信息
            depth_label = QLabel(f"深度: {anomaly_info['depth']:.2f} mm")
            diameter_label = QLabel(f"直径: {anomaly_info['diameter']:.3f} mm")
            deviation_label = QLabel(f"偏差: {anomaly_info['deviation']:+.3f} mm")

            # 设置颜色
            if anomaly_info['deviation'] > 0:
                deviation_label.setStyleSheet("color: red; font-weight: bold;")
            else:
                deviation_label.setStyleSheet("color: blue; font-weight: bold;")

            anomaly_layout.addWidget(depth_label)
            anomaly_layout.addWidget(diameter_label)
            anomaly_layout.addWidget(deviation_label)

            # 添加到异常内容布局
            self.anomaly_content_layout.addWidget(anomaly_frame)

            # 更新异常统计
            self.update_anomaly_stats()

        except Exception as e:
            print(f"添加异常显示失败: {e}")

    def update_anomaly_stats(self):
        """更新异常统计信息 - 按照原项目样式"""
        total_points = len(self.depth_data)
        anomaly_count = len(self.anomaly_data)
        anomaly_rate = (anomaly_count / total_points * 100) if total_points > 0 else 0

        # 更新大号数字显示
        self.anomaly_count_number.setText(str(anomaly_count))

        # 更新异常率显示
        self.anomaly_rate_label.setText(f"异常率: {anomaly_rate:.1f}%")

    def update_plot(self):
        """更新图表显示"""
        try:
            if len(self.depth_data) > 0 and len(self.diameter_data) > 0:
                # 更新数据线
                self.data_line.set_data(list(self.depth_data), list(self.diameter_data))

                # 自动调整坐标轴范围
                if len(self.depth_data) > 1:
                    depth_min, depth_max = min(self.depth_data), max(self.depth_data)
                    diameter_min, diameter_max = min(self.diameter_data), max(self.diameter_data)

                    # 添加一些边距
                    depth_margin = (depth_max - depth_min) * 0.05
                    diameter_margin = (diameter_max - diameter_min) * 0.05

                    self.ax.set_xlim(depth_min - depth_margin, depth_max + depth_margin)
                    self.ax.set_ylim(diameter_min - diameter_margin, diameter_max + diameter_margin)

                # 重绘图表
                self.canvas.draw_idle()

        except Exception as e:
            print(f"更新图表失败: {e}")

    def start_csv_data_import(self, auto_play=False):
        """开始CSV数据导入 - 完全按照原项目实现"""
        try:
            # 如果是自动播放模式，数据应该已经加载了
            if auto_play:
                if not self.csv_data:
                    self.log_message("❌ 自动播放模式下没有可用的CSV数据")
                    return
            else:
                # 手动模式：如果没有数据，尝试从文件列表加载
                if not self.csv_data:
                    if not hasattr(self, 'csv_file_list') or not self.csv_file_list:
                        self.log_message("❌ 没有可用的CSV文件列表")
                        return
                    current_file = self.csv_file_list[self.current_file_index]
                    self.log_message(f"🚀 开始CSV数据导入 - 文件: {current_file}")
                    if not self.load_csv_data_from_file(current_file):
                        self.log_message("❌ CSV数据加载失败")
                        return

            # 清除现有显示数据
            self.clear_plot_data()

            # 重置播放位置
            self.csv_data_index = 0

            # 设置标准直径
            self.set_standard_diameter_for_csv()

            # 开始播放
            self.is_csv_playing = True
            self.csv_timer = QTimer()
            self.csv_timer.timeout.connect(self.play_next_csv_point)
            self.csv_timer.start(50)  # 50ms间隔

            self.log_message("▶️ 开始CSV数据播放")

        except Exception as e:
            self.log_message(f"❌ 启动CSV数据导入失败: {e}")

    def play_next_csv_point(self):
        """播放下一个CSV数据点"""
        try:
            if not self.is_csv_playing or not self.csv_data:
                return

            if self.csv_data_index >= len(self.csv_data):
                # 播放完成
                self.stop_csv_playback()
                return

            # 获取当前数据点
            point = self.csv_data[self.csv_data_index]
            depth = point['depth']
            diameter = point['diameter']

            # 添加到显示数据
            self.depth_data.append(depth)
            self.diameter_data.append(diameter)

            # 更新图表
            self.update_plot()

            # 更新深度显示
            self.depth_label.setText(f"📏 探头深度: {depth:.2f} mm")

            # 检查异常
            if abs(diameter - self.target_diameter) > self.tolerance:
                anomaly_info = {
                    'depth': depth,
                    'diameter': diameter,
                    'deviation': diameter - self.target_diameter
                }
                self.add_anomaly_to_display(anomaly_info)

            # 移动到下一个点
            self.csv_data_index += 1

        except Exception as e:
            self.log_message(f"❌ 播放CSV数据点失败: {e}")

    def stop_csv_playback(self):
        """停止CSV播放"""
        try:
            self.is_csv_playing = False
            if self.csv_timer:
                self.csv_timer.stop()
                self.csv_timer = None

            self.log_message("⏸️ CSV数据播放已停止")

        except Exception as e:
            self.log_message(f"❌ 停止CSV播放失败: {e}")

    def clear_plot_data(self):
        """清除图表显示数据（但保留加载的CSV数据）"""
        self.depth_data.clear()
        self.diameter_data.clear()
        self.data_line.set_data([], [])
        self.canvas.draw_idle()

    def set_standard_diameter_for_csv(self):
        """为CSV数据设置标准直径"""
        # 这里可以根据需要设置不同的标准直径
        self.target_diameter = self.standard_diameter
        self.log_message(f"📏 设置标准直径: {self.target_diameter} mm")

    def start_csv_data_import_old(self):
        """开始CSV数据导入"""
        try:
            # 在测试环境中，允许没有孔位选择的情况
            if not self.current_hole_id and not hasattr(self, '_test_mode'):
                QMessageBox.warning(self, "警告", "请先选择一个孔位")
                return

            self.log_message("🚀 开始数据监测...")
            self.log_message("● 通信状态：监测中")

            # 更新按钮状态
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)

            # 如果有自动化工作器，启动它
            if HAS_AUTOMATION:
                self.start_automation_worker()

        except Exception as e:
            self.log_message(f"❌ 启动监测失败: {e}")

    def stop_monitoring(self):
        """停止监测"""
        try:
            self.log_message("⏸️ 停止数据监测")
            self.log_message("○ 通信状态：待机")

            # 更新按钮状态
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)

            # 停止自动化工作器
            if self.automation_thread and self.automation_thread.isRunning():
                self.automation_worker.stop()
                self.automation_thread.quit()
                self.automation_thread.wait()

        except Exception as e:
            self.log_message(f"❌ 停止监测失败: {e}")

    def clear_data(self):
        """清除数据"""
        try:
            # 清除数据缓冲区
            self.depth_data.clear()
            self.diameter_data.clear()
            self.anomaly_data.clear()

            # 清除图表
            self.data_line.set_data([], [])
            self.ax.set_xlim(0, 950)
            self.ax.set_ylim(16.5, 20.5)
            self.canvas.draw_idle()

            # 重置显示
            self.depth_label.setText("📏 探头深度: -- mm")
            self.max_diameter_label.setText("📈 最大直径: -- mm")
            self.min_diameter_label.setText("📉 最小直径: -- mm")

            # 清除异常显示
            for i in reversed(range(self.anomaly_content_layout.count())):
                child = self.anomaly_content_layout.itemAt(i).widget()
                if child:
                    child.setParent(None)

            # 重置异常统计显示
            self.anomaly_count_number.setText("0")
            self.anomaly_rate_label.setText("异常率: 0.0%")

            self.log_message("🗑️ 数据已清除")

        except Exception as e:
            self.log_message(f"❌ 清除数据失败: {e}")

    def log_message(self, message):
        """添加日志消息"""
        try:
            self.log_text_edit.append(message)
            # 自动滚动到底部
            scrollbar = self.log_text_edit.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        except Exception as e:
            print(f"日志记录失败: {e}")

    def start_automation_worker(self):
        """启动自动化工作器 - 完全按照原项目实现"""
        try:
            if not HAS_AUTOMATION:
                self.log_message("⚠️ 自动化模块不可用")
                return

            self.log_message("🚀 启动自动化任务...")

            # 创建工作线程
            self.automation_thread = QThread()

            # 创建自动化工作器，传入必要的路径参数
            self.automation_worker = AutomationWorker(
                acquisition_path=self.acquisition_program_path,
                launcher_path=self.launcher_script_path
            )
            self.automation_worker.moveToThread(self.automation_thread)

            # 连接信号 - 按照原项目的信号接口
            self.automation_worker.progress_updated.connect(self.log_message)
            self.automation_worker.task_finished.connect(self.on_automation_task_finished)

            # 启动线程
            self.automation_thread.started.connect(self.automation_worker.run_automation)
            self.automation_thread.start()

            self.log_message("✅ 自动化任务已启动")

        except Exception as e:
            self.log_message(f"❌ 启动自动化任务失败: {e}")

    def on_automation_task_finished(self, success, message):
        """自动化任务完成回调 - 按照原项目实现"""
        try:
            if success:
                self.log_message(f"✅ 自动化任务完成: {message}")
            else:
                self.log_message(f"❌ 自动化任务失败: {message}")

            # 清理线程资源
            if self.automation_thread and self.automation_thread.isRunning():
                self.automation_thread.quit()
                self.automation_thread.wait()

        except Exception as e:
            self.log_message(f"❌ 处理自动化任务结果失败: {e}")


# 为了兼容性，创建别名
RealtimeMonitoringPage = RealtimeChart
