"""
实时图表组件模块
面板A使用matplotlib实现稳定的误差线显示，其他功能保持不变
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib
import numpy as np
import os
import sys
import traceback

# 设置matplotlib支持中文显示 - 安全版本
def setup_safe_chinese_font():
    """设置安全的中文字体支持"""
    try:
        # 使用简化的字体配置，避免复杂的字体检测
        matplotlib.rcParams['font.family'] = 'sans-serif'
        matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC', 'SimHei', 'DejaVu Sans']
        matplotlib.rcParams['axes.unicode_minus'] = False
        print("✅ 安全字体配置完成")
    except Exception as e:
        print(f"⚠️ 字体配置失败，使用默认: {e}")
        # 使用最基本的配置
        matplotlib.rcParams['font.family'] = 'DejaVu Sans'

# 初始化安全字体配置
setup_safe_chinese_font()
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QSplitter, QGroupBox, QLineEdit, QMessageBox, QComboBox, QTextEdit)
from PySide6.QtCore import Qt, Slot, QTimer, QThread, QFileSystemWatcher
from PySide6.QtGui import QPixmap, QIcon
from collections import deque
from .endoscope_view import EndoscopeView
from .camera_preview import CameraPreviewWidget
from .video_display_widget import VideoDisplayWidget
from ..workers.automation_worker import AutomationWorker

# 尝试导入qtawesome用于图标支持
try:
    import qtawesome as qta
    HAS_QTAWESOME = True
except ImportError:
    HAS_QTAWESOME = False
    print("⚠️ qtawesome未安装，将使用文本状态指示器")

# 新增导入
import re
import shutil
from PySide6.QtCore import QObject, Signal

class ArchiveWorker(QObject):
    """
    在后台线程中执行文件归档任务的工人。
    """
    log_message = Signal(str)  # 用于向主界面发送日志信息
    finished = Signal(str)     # 任务完成时发射信号，并附带最终状态信息

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

            # 1. 确定下一个文件夹名称 (如 R001C005)
            next_folder_name = self._get_next_folder_name()
            self.log_message.emit(f"   - 计算下一个归档文件夹为: {next_folder_name}")

            # 2. 创建文件夹结构 (RxxxCxxx/BISDM 和 RxxxCxxx/CCIDM)
            ccidm_path = os.path.join(self.base_archive_path, next_folder_name, "CCIDM")
            bisdm_path = os.path.join(self.base_archive_path, next_folder_name, "BISDM")
            os.makedirs(ccidm_path, exist_ok=True)
            os.makedirs(bisdm_path, exist_ok=True)
            self.log_message.emit(f"   - 已创建目录: {ccidm_path}")
            self.log_message.emit(f"   - 已创建目录: {bisdm_path}")

            # 3. 确定最终文件名并移动文件
            # 将 R0_C0.csv 重命名为与文件夹同名的CSV，如 R001C005.csv
            final_filename = f"{next_folder_name}.csv"
            destination_path = os.path.join(ccidm_path, final_filename)

            self.log_message.emit(f"   - 准备移动文件: '{os.path.basename(self.source_path)}' -> '{destination_path}'")
            shutil.move(self.source_path, destination_path)

            self.finished.emit(f"✅ 归档成功！文件已存至: {destination_path}")

        except Exception as e:
            error_info = f"❌ 后台归档失败: {e}\n{traceback.format_exc()}"
            self.log_message.emit(error_info)
            self.finished.emit(error_info)

    def _get_next_folder_name(self):
        """扫描基础路径，确定下一个RxxxCxxx文件夹的名称"""
        if not os.path.exists(self.base_archive_path):
            self.log_message.emit(f"   - 归档根目录不存在，将创建: {self.base_archive_path}")
            os.makedirs(self.base_archive_path)
            return "R001C001"

        dir_pattern = re.compile(r'^R(\d{3})C(\d{3})$')
        max_num = 0

        for item in os.listdir(self.base_archive_path):
            if os.path.isdir(os.path.join(self.base_archive_path, item)):
                match = dir_pattern.match(item)
                if match:
                    # 我们只关心C后面的数字来确定顺序
                    num = int(match.group(2))
                    if num > max_num:
                        max_num = num

        next_num = max_num + 1
        return f"R001C{next_num:03d}"

# --- 以上是新增的 ArchiveWorker 类 ---


class RealtimeChart(QWidget):
    """
    实时图表组件 - 二级页面双面板设计
    面板A: 管孔直径数据实时折线图
    面板B: 内窥镜实时图像显示
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_hole_id = None
        self.is_data_loaded = False  # 标记是否已加载数据

        # --- 新增：线程管理与路径配置 ---
        self.automation_thread = None
        self.automation_worker = None

        # 动态计算项目路径，避免硬编码
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        # 从 .../src/pages/realtime_monitoring_p2/components 向上4级到项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file_dir))))
        # 使用相对路径构建采集程序路径
        self.acquisition_program_path = os.path.join(project_root, "src", "hardware", "Release", "LEConfocalDemo.exe")
        self.remote_launcher_path = os.path.join(project_root, "src", "pages", "realtime_monitoring_p2", "utils", "remote_launcher.py")

        # --- 新增：定义最终生成的数据CSV文件路径 ---
        self.csv_output_folder = os.path.join(project_root, "src", "hardware", "Release")  # CSV输出文件夹
        
        # --- 新增：定义归档路径和相关配置 ---
        # 使用重构前的CAP1000项目目录结构
        self.csv_archive_folder = os.path.join(project_root, "Data", "CAP1000")  # CSV归档文件夹
        os.makedirs(self.csv_archive_folder, exist_ok=True)  # 确保文件夹存在
        self.project_root = project_root  # 保存project_root供其他方法使用
        self.output_csv_path = os.path.join(self.csv_output_folder, "R0_C0.csv")

        # --- 新增：定义归档路径和worker属性 ---
        self.archive_base_path = os.path.join(project_root, "Data", "CAP1000")
        self.archive_thread = None
        self.archive_worker = None
        # ------------------------------------
        # ----------------------------------------

        # --- 新增：文件生成监视器 ---
        self.csv_watcher = QFileSystemWatcher(self)
        self.csv_watcher.directoryChanged.connect(self.on_directory_changed)
        # ---------------------------
        # --------------------------------

        self.setup_ui()
        self.setup_chart()
        self.init_data_buffers()
        self.setup_waiting_state()  # 设置等待状态
        
    def setup_ui(self):
        """设置用户界面布局 - 双面板设计"""
        layout = QVBoxLayout(self)

        # 状态信息面板 - 优化为仪表盘样式，集成控制按钮
        status_group = QGroupBox("状态监控与主控制区")
        status_group.setObjectName("StatusDashboard")
        status_layout = QHBoxLayout(status_group)

        # 左侧：核心状态信息
        status_info_layout = QHBoxLayout()
        status_info_layout.setSpacing(20)

        # 当前孔位显示 - 改为文本显示，增大字体
        self.current_hole_label = QLabel("当前孔位：未选择")
        self.current_hole_label.setObjectName("InfoLabel")
        self.current_hole_label.setMinimumWidth(180)  # 从140增加到180

        # 通信状态显示 - 强化关键状态，准备添加图标
        self.comm_status_label = QLabel("通信状态: 等待连接")
        self.comm_status_label.setObjectName("CommStatusLabel")
        self.comm_status_label.setMinimumWidth(200)  # 从150增加到200

        # 标准直径显示 - 弱化静态信息
        self.standard_diameter_label = QLabel("标准直径：17.73mm")
        self.standard_diameter_label.setObjectName("StaticInfoLabel")
        self.standard_diameter_label.setMinimumWidth(180)  # 从140增加到180

        status_info_layout.addWidget(self.current_hole_label)
        status_info_layout.addWidget(self.comm_status_label)
        status_info_layout.addWidget(self.standard_diameter_label)

        status_layout.addLayout(status_info_layout)
        status_layout.addStretch(1)

        # 中间：实时数据显示 - 添加图标
        realtime_info_layout = QHBoxLayout()
        realtime_info_layout.setSpacing(15)

        self.depth_label = QLabel("📏 探头深度: -- mm")
        self.max_diameter_label = QLabel("📈 最大直径: -- mm")
        self.min_diameter_label = QLabel("📉 最小直径: -- mm")

        # 使用主题管理器的样式，设置objectName
        self.depth_label.setObjectName("StatusLabel")
        self.max_diameter_label.setObjectName("StatusLabel")
        self.min_diameter_label.setObjectName("StatusLabel")

        # 设置最小宽度，让文本窗口适当放长
        self.depth_label.setMinimumWidth(180)
        self.max_diameter_label.setMinimumWidth(180)
        self.min_diameter_label.setMinimumWidth(180)

        realtime_info_layout.addWidget(self.depth_label)
        realtime_info_layout.addWidget(self.max_diameter_label)
        realtime_info_layout.addWidget(self.min_diameter_label)

        status_layout.addLayout(realtime_info_layout)
        status_layout.addStretch(1)

        # 右侧：主控制按钮区域
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)

        # 创建主控制按钮 - 添加图标
        self.start_button = QPushButton("▶️ 开始监测")
        self.stop_button = QPushButton("⏸️ 停止监测")
        self.clear_button = QPushButton("🗑️ 清除数据")

        # 设置按钮样式
        self.start_button.setObjectName("StartButton")
        self.stop_button.setObjectName("StopButton")
        self.clear_button.setObjectName("ClearDataButton")  # 使用专门的objectName以便单独控制

        # 移除固定尺寸设置，改用QSS中的min-width来确保文字完整显示
        # button_size = (100, 35)
        # for button in [self.start_button, self.stop_button, self.clear_button]:
        #     button.setFixedSize(*button_size)

        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.clear_button)

        status_layout.addLayout(control_layout)

        layout.addWidget(status_group)

        # --- 新增：自动化控制日志窗口 ---
        log_group = QGroupBox("自动化控制日志")
        log_layout = QVBoxLayout(log_group)
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setMaximumHeight(150)
        log_layout.addWidget(self.log_text_edit)
        layout.addWidget(log_group)
        # -----------------------------------

        # 双面板区域 - 改为垂直布局（A在上，B在下）
        splitter = QSplitter(Qt.Vertical)

        # 面板A: 管孔直径数据 - 无边框设计，最大化内容区域
        panel_a_widget = QWidget()
        panel_a_widget.setObjectName("PanelAWidget")
        panel_a_layout = QHBoxLayout(panel_a_widget)  # 水平布局：图表在左，异常窗口在右
        panel_a_layout.setContentsMargins(8, 8, 8, 8)  # 减少边距
        panel_a_layout.setSpacing(10)

        # 面板A左侧：图表区域（matplotlib）
        chart_widget = QWidget()
        chart_widget.setObjectName("ChartWidget")
        chart_layout = QVBoxLayout(chart_widget)
        chart_layout.setContentsMargins(0, 0, 0, 0)  # 移除边距，最大化图表区域

        # 创建图表标题栏
        chart_header = QWidget()
        chart_header.setObjectName("PanelHeader")
        chart_header_layout = QHBoxLayout(chart_header)
        chart_header_layout.setContentsMargins(15, 0, 15, 0)  # 左右留边距
        chart_header_layout.setSpacing(10)

        chart_title = QLabel("管孔直径实时监测")
        chart_title.setObjectName("PanelHeaderText")

        # 添加工具按钮
        from PySide6.QtWidgets import QToolButton
        export_chart_button = QToolButton()
        export_chart_button.setObjectName("HeaderToolButton")
        export_chart_button.setText("📊")  # 使用emoji作为图标
        export_chart_button.setToolTip("导出图表为图片")

        refresh_chart_button = QToolButton()
        refresh_chart_button.setObjectName("HeaderToolButton")
        refresh_chart_button.setText("🔄")  # 使用emoji作为图标
        refresh_chart_button.setToolTip("刷新图表")

        chart_header_layout.addWidget(chart_title)
        chart_header_layout.addStretch()
        chart_header_layout.addWidget(refresh_chart_button)
        chart_header_layout.addWidget(export_chart_button)

        # 将标题栏添加到布局
        chart_layout.addWidget(chart_header)

        # 创建matplotlib图形，优化尺寸以最大化显示区域
        self.figure = Figure(figsize=(24, 12), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        chart_layout.addWidget(self.canvas)

        # 连接鼠标事件用于缩放和重置
        self.canvas.mpl_connect('scroll_event', self.on_scroll)
        self.canvas.mpl_connect('button_press_event', self.on_mouse_press)

        # 创建子图 - 增大字体
        self.ax = self.figure.add_subplot(111)
        self.apply_matplotlib_dark_theme()  # 应用深色主题
        self.ax.set_xlabel('深度 (mm)', fontsize=14, fontweight='bold')
        self.ax.set_ylabel('直径 (mm)', fontsize=14, fontweight='bold')
        # 移除matplotlib内部标题，使用外部标题栏
        # self.ax.set_title('管孔直径实时监测', fontsize=16, fontweight='bold', pad=15)
        self.ax.grid(True, alpha=0.3)

        # 设置坐标轴刻度字体大小
        self.ax.tick_params(axis='both', which='major', labelsize=12)
        self.ax.tick_params(axis='both', which='minor', labelsize=10)

        # 设置初始范围
        self.ax.set_ylim(16.5, 20.5)
        self.ax.set_xlim(0, 950)

        # 初始化数据线 - 使用主题蓝色
        self.data_line, = self.ax.plot([], [], color='#4A90E2', linewidth=3, label='直径数据')

        # 设置图形样式，确保所有标签都能完整显示
        self.figure.subplots_adjust(left=0.12, bottom=0.15, right=0.95, top=0.85)

        # 设置图例位置，确保不被遮挡 - 增大字体
        self.ax.legend(loc='upper right', bbox_to_anchor=(0.95, 0.95), fontsize=12)

        # 在图表下方添加面板A专用控制按钮（移除标准直径输入）
        self.create_panel_a_controls(chart_layout)

        panel_a_layout.addWidget(chart_widget)

        # 面板A右侧：异常数据显示区域和按钮
        right_panel = QWidget()
        right_panel.setObjectName("RightPanel")
        right_panel.setMinimumWidth(320)  # 设置最小宽度而不是固定宽度
        right_panel.setMaximumWidth(400)  # 设置最大宽度，允许适度调整
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)  # 设置边距
        right_layout.setSpacing(8)  # 设置组件间距

        # 异常监控窗口 - 使用stretch factor占据大部分空间
        self.create_anomaly_panel(right_layout)

        # 添加固定间距，确保按钮不会紧贴异常面板
        right_layout.addSpacing(15)

        # 添加【查看下一个样品】按钮 - 使用主题样式
        self.next_sample_button = QPushButton("查看下一个样品")
        self.next_sample_button.clicked.connect(self.view_next_sample)
        self.next_sample_button.setObjectName("next_sample_button")
        from PySide6.QtWidgets import QSizePolicy
        self.next_sample_button.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )
        right_layout.addWidget(self.next_sample_button)

        # 添加底部间距，确保按钮不会贴底
        right_layout.addSpacing(10)

        panel_a_layout.addWidget(right_panel)
        splitter.addWidget(panel_a_widget)

        # 面板B: 内窥镜监测区域 - 改为左右分割布局（按照重构前设计）
        panel_b_widget = QWidget()
        panel_b_widget.setObjectName("PanelBWidget")
        panel_b_layout = QHBoxLayout(panel_b_widget)
        panel_b_layout.setContentsMargins(8, 8, 8, 8)
        panel_b_layout.setSpacing(10)
        
        # 创建水平分割器（左右布局）
        endoscope_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：内窥镜展开图（处理结果）
        endoscope_container = QWidget()
        endoscope_layout = QVBoxLayout(endoscope_container)
        endoscope_layout.setContentsMargins(5, 5, 5, 5)
        
        # 内窥镜标题
        endo_header = QWidget()
        endo_header.setObjectName("PanelHeader")
        endo_header_layout = QHBoxLayout(endo_header)
        endo_header_layout.setContentsMargins(15, 0, 15, 0)
        
        endo_title = QLabel("内窥镜实时图像 - 内表面展开图")
        endo_title.setObjectName("PanelHeaderText")
        endo_header_layout.addWidget(endo_title)
        endo_header_layout.addStretch()
        
        endoscope_layout.addWidget(endo_header)
        
        # 内窥镜视图
        self.endoscope_view = EndoscopeView()
        self.endoscope_view.setObjectName("EndoscopeWidget")
        endoscope_layout.addWidget(self.endoscope_view)
        
        endoscope_splitter.addWidget(endoscope_container)
        
        # 右侧：原始视频流
        video_container = QWidget()
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(5, 5, 5, 5)
        
        # 视频标题
        video_header = QWidget()
        video_header.setObjectName("PanelHeader")
        video_header_layout = QHBoxLayout(video_header)
        video_header_layout.setContentsMargins(15, 0, 15, 0)
        
        video_title = QLabel("原始视频流 - 摄像头实时画面")
        video_title.setObjectName("PanelHeaderText")
        video_header_layout.addWidget(video_title)
        video_header_layout.addStretch()
        
        video_layout.addWidget(video_header)
        
        # 视频显示组件
        self.video_display = VideoDisplayWidget()
        self.video_display.setObjectName("VideoDisplayWidget")
        video_layout.addWidget(self.video_display)
        
        endoscope_splitter.addWidget(video_container)
        
        # 设置左右比例 (60:40) - 按照重构前比例
        endoscope_splitter.setSizes([600, 400])
        
        panel_b_layout.addWidget(endoscope_splitter)
        splitter.addWidget(panel_b_widget)
        
        # 同时创建摄像头预览控制器
        self.camera_preview = CameraPreviewWidget()
        self.camera_preview.setObjectName("CameraPreviewWidget")

        # 设置分割器比例，使用相对比例而不是固定像素
        # 面板A占65%，面板B占35%
        layout.addWidget(splitter)

        # 保存分割器引用，用于后续调整
        self.main_splitter = splitter

        # 延迟设置分割器比例，确保窗口已完全初始化
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self.safe_adjust_splitter_sizes(splitter))

        # 初始化孔位数据映射
        self.init_hole_data_mapping()

        # --- 修改：按钮连接 ---
        # 清理旧的连接
        try:
            self.start_button.clicked.disconnect()
        except RuntimeError:
            pass  # 如果没有连接，会抛出异常，忽略即可

        self.start_button.clicked.connect(self.start_automation_task)  # 连接到新的总启动函数
        self.stop_button.clicked.connect(self.stop_automation_task)   # 连接到新的总停止函数
        self.clear_button.clicked.connect(self.clear_data)
        # -------------------

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
        self.remote_launcher_process = None  # 运动台控制程序进程
        # 路径配置已在__init__中完成，无需重复设置

        # 实时CSV监控相关属性
        self.csv_monitor = None
        self.is_realtime_monitoring = False
        self.last_csv_file = None
        self.csv_file_monitor_timer = None
        
        # 初始化摄像头预览功能
        self.init_camera_preview()
        self.last_file_size = 0  # 用于检测文件增量更新


        # 加载实时监控配置
        try:
            from config.realtime_config import realtime_config
            self.realtime_config = realtime_config
            # 使用项目内的CSV输出文件夹
            self.csv_watch_folder = self.csv_output_folder
        except ImportError:
            # 如果配置文件不存在，使用项目内的默认配置
            self.csv_watch_folder = self.csv_output_folder
            self.realtime_config = None

    def create_panel_a_controls(self, parent_layout):
        """创建面板A专用控制按钮"""
        # 不再创建面板A的启动、停止按钮和状态标签
        # 这些控制功能已被移除
        pass

    def update_comm_status(self, status, message):
        """更新通信状态显示，支持图标"""
        if HAS_QTAWESOME:
            if status == "connected":
                icon = qta.icon('fa5s.check-circle', color='#2ECC71')
                self.comm_status_label.setText(f"  {message}")
            elif status == "error":
                icon = qta.icon('fa5s.exclamation-circle', color='#E74C3C')
                self.comm_status_label.setText(f"  {message}")
            elif status == "warning":
                icon = qta.icon('fa5s.exclamation-triangle', color='#E67E22')
                self.comm_status_label.setText(f"  {message}")
            else:
                icon = qta.icon('fa5s.circle', color='#AAAAAA')
                self.comm_status_label.setText(f"  {message}")

            # 设置图标（如果支持的话）
            try:
                pixmap = icon.pixmap(16, 16)
                self.comm_status_label.setPixmap(pixmap)
            except:
                # 如果设置图标失败，只显示文本
                pass
        else:
            # 不支持图标时，使用文本指示器
            if status == "connected":
                self.comm_status_label.setText(f"✓ {message}")
            elif status == "error":
                self.comm_status_label.setText(f"✗ {message}")
            elif status == "warning":
                self.comm_status_label.setText(f"⚠ {message}")
            else:
                self.comm_status_label.setText(f"○ {message}")

    def init_hole_data_mapping(self):
        """初始化孔位数据映射"""
        import os

        # 获取当前工作目录
        base_dir = os.getcwd()

        # 使用绝对路径确保路径解析正确，更新为CAP1000子目录
        self.hole_to_csv_map = {
            "R001C001": os.path.join(base_dir, "Data/CAP1000/R001C001/CCIDM"),
            "R001C002": os.path.join(base_dir, "Data/CAP1000/R001C002/CCIDM"),
            "R001C003": os.path.join(base_dir, "Data/CAP1000/R001C003/CCIDM"),
            "R001C004": os.path.join(base_dir, "Data/CAP1000/R001C004/CCIDM")
        }

        self.hole_to_image_map = {
            "R001C001": os.path.join(base_dir, "Data/CAP1000/R001C001/BISDM/result"),
            "R001C002": os.path.join(base_dir, "Data/CAP1000/R001C002/BISDM/result"),
            "R001C003": os.path.join(base_dir, "Data/CAP1000/R001C003/BISDM/result"),
            "R001C004": os.path.join(base_dir, "Data/CAP1000/R001C004/BISDM/result"),
            "R0_C0": os.path.join(base_dir, "Data/CAP1000/R001C001/BISDM/result")  # 测量模式使用R001C001的图片作为示例
        }

        # 打印路径信息用于调试
        print("🔧 孔位数据映射初始化:")
        for hole_id, csv_path in self.hole_to_csv_map.items():
            image_path = self.hole_to_image_map[hole_id]
            print(f"  {hole_id}:")
            print(f"    📄 CSV: {csv_path}")
            print(f"    🖼️ 图像: {image_path}")
            print(f"    📂 CSV目录存在: {os.path.exists(csv_path)}")
            print(f"    📂 图像目录存在: {os.path.exists(image_path)}")

            # 检查CSV目录中的文件
            if os.path.exists(csv_path):
                csv_files = [f for f in os.listdir(csv_path) if f.endswith('.csv')]
                print(f"    📄 找到CSV文件: {csv_files}")
            else:
                print(f"    ❌ CSV目录不存在: {csv_path}")

    def set_current_hole_display(self, hole_id):
        """设置当前孔位显示"""
        if hole_id:
            self.current_hole_label.setText(f"当前孔位：{hole_id}")
            self.current_hole_id = hole_id
            print(f"🔄 设置当前孔位显示: {hole_id}")
            # 如果有对应的数据文件，自动加载
            if hole_id in ["R001C001", "R001C002", "R001C003", "R001C004"]:
                self.load_data_for_hole(hole_id)
        else:
            self.current_hole_label.setText("当前孔位：未选择")
            self.current_hole_id = None

    def setup_waiting_state(self):
        """设置等待状态 - 等待从主检测界面跳转"""
        # 显示等待提示
        self.current_hole_label.setText("当前孔位：未选择")
        self.depth_label.setText("📏 探头深度: -- mm")
        self.update_comm_status("waiting", "等待选择孔位")
        self.max_diameter_label.setText("📈 最大直径: -- mm")
        self.min_diameter_label.setText("📉 最小直径: -- mm")

        # 在图表中显示等待提示
        self.show_waiting_message()

        print("⏳ 实时监控界面等待状态 - 请从主检测界面选择孔位后跳转")

    def show_waiting_message(self):
        """在图表区域显示等待状态（无提示文字）"""
        try:
            # 清除现有数据
            self.ax.clear()

            # 移除matplotlib内部标题，使用外部标题栏
            # self.ax.set_title("管孔直径实时监测", fontsize=16, fontweight='bold', pad=20)

            # 设置基本的坐标轴
            self.ax.set_xlabel("深度 (mm)", fontsize=12)
            self.ax.set_ylabel("直径 (mm)", fontsize=12)
            self.ax.grid(True, alpha=0.3)

            # 设置默认的坐标轴范围
            self.ax.set_xlim(0, 100)
            self.ax.set_ylim(16, 20)

            # 刷新画布
            self.canvas.draw()

        except Exception as e:
            print(f"⚠️ 显示等待状态失败: {e}")

    def enable_controls_after_data_load(self):
        """数据加载后启用控制按钮"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.clear_button.setEnabled(True)

        # 更新按钮提示
        self.start_button.setToolTip("开始播放测量数据")
        self.stop_button.setToolTip("停止播放测量数据")
        self.clear_button.setToolTip("清除当前数据")

        print("✅ 控制按钮已启用")

    def setup_chart_for_data(self):
        """为数据显示设置图表"""
        try:
            # 清除现有内容
            self.ax.clear()

            # 移除matplotlib内部标题，使用外部标题栏
            # self.ax.set_title("管孔直径实时监测", fontsize=16, fontweight='bold', pad=20)

            # 设置坐标轴标签
            self.ax.set_xlabel("深度 (mm)", fontsize=12)
            self.ax.set_ylabel("直径 (mm)", fontsize=12)

            # 设置网格
            self.ax.grid(True, alpha=0.3)

            # 初始化数据线 - 使用主题蓝色
            self.data_line, = self.ax.plot([], [], color='#4A90E2', linewidth=2, label='测量数据')

            # 重新绘制误差线（如果标准直径已设置）
            if hasattr(self, 'standard_diameter') and self.standard_diameter is not None:
                self.draw_error_lines_and_adjust_y_axis()
                print("✅ 误差线已重新绘制")
            else:
                # 设置图例（无误差线时）
                self.ax.legend(loc='upper right')

            # 刷新画布
            self.canvas.draw()

            print("✅ 图表已准备好显示数据")

        except Exception as e:
            print(f"⚠️ 设置图表失败: {e}")





    def start_endoscope_image_switching(self):
        """启动内窥镜图像切换功能"""
        print("🖼️ 启动面板B图像切换功能")

        # 检查是否有图像数据
        if not hasattr(self, 'current_images') or not self.current_images:
            print("⚠️ 没有可用的内窥镜图像数据")
            return

        # 标记图像切换功能已启用
        self.endoscope_switching_enabled = True

        # 如果CSV数据正在播放，图像会自动根据进度切换
        # 如果没有播放，显示第一张图像
        if not hasattr(self, 'is_csv_playing') or not self.is_csv_playing:
            if self.current_images:
                self.display_endoscope_image(0)
                print("📸 显示第一张内窥镜图像")

        print(f"✅ 图像切换功能已启用，共 {len(self.current_images)} 张图像")

    def stop_endoscope_image_switching(self):
        """停止内窥镜图像切换功能"""
        print("⏹️ 停止面板B图像切换功能")

        # 标记图像切换功能已禁用
        self.endoscope_switching_enabled = False

        print("✅ 图像切换功能已停止")

    def create_anomaly_panel(self, parent_layout):
        """创建异常数据显示面板 - 使用主题样式"""
        anomaly_widget = QGroupBox("异常直径监控")
        anomaly_widget.setObjectName("anomaly_widget")
        anomaly_widget.setMinimumWidth(310)  # 设置最小宽度
        anomaly_widget.setMaximumWidth(390)  # 设置最大宽度，允许适度调整
        anomaly_layout = QVBoxLayout(anomaly_widget)
        anomaly_layout.setContentsMargins(8, 8, 8, 8)
        anomaly_layout.setSpacing(5)  # 设置组件间距

        # # 标题 - 使用主题样式
        # title_label = QLabel("超出公差的测量点")
        # title_label.setObjectName("AnomalyTitle")
        # title_label.setFixedHeight(25)  # 增加标题高度
        # anomaly_layout.addWidget(title_label)

        # 滚动区域用于显示异常数据
        from PySide6.QtWidgets import QScrollArea
        self.anomaly_scroll = QScrollArea()
        self.anomaly_scroll.setWidgetResizable(True)
        self.anomaly_scroll.setObjectName("anomaly_scroll")

        self.anomaly_content = QWidget()
        self.anomaly_content.setObjectName("anomaly_content")
        self.anomaly_content_layout = QVBoxLayout(self.anomaly_content)
        self.anomaly_content_layout.setContentsMargins(5, 5, 5, 5)
        self.anomaly_scroll.setWidget(self.anomaly_content)

        # 滚动区域占据可用空间，但为统计信息预留足够空间
        anomaly_layout.addWidget(self.anomaly_scroll, 1)

        # 统计信息 - 使用栅格布局精确控制异常计数显示
        stats_widget = QWidget()
        stats_widget.setFixedHeight(50)  # 适当调整高度
        stats_widget.setObjectName("AnomalyStatsWidget")

        # 使用QGridLayout实现精确的控件对齐
        from PySide6.QtWidgets import QGridLayout
        stats_layout = QGridLayout(stats_widget)
        stats_layout.setContentsMargins(10, 5, 10, 5)
        stats_layout.setSpacing(5)

        # 大号数字显示异常计数
        self.anomaly_count_number = QLabel("0")
        self.anomaly_count_number.setObjectName("AnomalyCountLabel")

        # 异常计数说明文字
        count_text_label = QLabel("个异常点")
        count_text_label.setObjectName("AnomalyUnitLabel")

        # 异常率显示
        self.anomaly_rate_label = QLabel("异常率: 0.0%")
        self.anomaly_rate_label.setObjectName("AnomalyRateLabel")


        # 将控件放入网格布局
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

        # 添加统计区域，不使用stretch factor，保持固定位置
        anomaly_layout.addWidget(stats_widget, 0)

        # 让异常面板占据可用空间，但为按钮预留空间
        parent_layout.addWidget(anomaly_widget, 1)  # 使用stretch factor

    def apply_matplotlib_dark_theme(self):
        """为内置的Matplotlib图表应用深色主题"""
        fig = self.figure
        ax = self.ax

        # 设置图形和坐标轴背景色
        fig.set_facecolor('#313642')
        ax.set_facecolor('#313642')

        # 设置坐标轴边框颜色
        ax.spines['bottom'].set_color('#505869')
        ax.spines['top'].set_color('#505869')
        ax.spines['left'].set_color('#505869')
        ax.spines['right'].set_color('#505869')

        # 设置刻度颜色
        ax.tick_params(axis='x', colors='#D3D8E0')
        ax.tick_params(axis='y', colors='#D3D8E0')

        # 设置标签颜色
        ax.xaxis.label.set_color('#D3D8E0')
        ax.yaxis.label.set_color('#D3D8E0')
        ax.title.set_color('#FFFFFF')

        # 设置网格颜色
        ax.grid(color='#404552', linestyle='--', linewidth=0.7)





    def set_standard_diameter(self, diameter):
        """设置标准直径并绘制公差线"""
        self.standard_diameter = diameter

        # 误差范围：+0.05/-0.07mm
        self.upper_tolerance = 0.07
        self.lower_tolerance = 0.05

        # 更新目标直径（用于异常检测）
        self.target_diameter = diameter
        self.tolerance = max(self.upper_tolerance, self.lower_tolerance)  # 使用最大误差进行异常检测

        # 绘制误差线并调整Y轴范围
        self.draw_error_lines_and_adjust_y_axis()

    def draw_error_lines_and_adjust_y_axis(self):
        """绘制误差线并调整Y轴范围（matplotlib版本）"""
        if not hasattr(self, 'standard_diameter') or self.standard_diameter is None:
            return

        # 移除现有的误差线
        self.remove_error_lines_and_reset_y_axis()

        # 计算误差线位置
        max_error_line_y = self.standard_diameter + self.upper_tolerance  # +0.05mm
        min_error_line_y = self.standard_diameter - self.lower_tolerance  # -0.07mm

        # 计算Y轴显示范围：标准直径 ± 0.15mm
        y_margin = 0.15
        y_min = self.standard_diameter - y_margin
        y_max = self.standard_diameter + y_margin

        # 设置Y轴范围
        self.ax.set_ylim(y_min, y_max)

        # 使用matplotlib绘制误差线
        try:
            # 绘制上误差线（使用柔和的橙色）
            self.max_error_line = self.ax.axhline(
                y=max_error_line_y,
                color='#E67E22',
                linestyle='--',
                linewidth=1.5,
                alpha=0.8,
                label=f'上限 {max_error_line_y:.2f}mm'
            )

            # 绘制下误差线（使用柔和的橙色）
            self.min_error_line = self.ax.axhline(
                y=min_error_line_y,
                color='#E67E22',
                linestyle='--',
                linewidth=1.5,
                alpha=0.8,
                label=f'下限 {min_error_line_y:.2f}mm'
            )

            # 更新图例，设置位置确保不被遮挡，并应用深色主题
            legend = self.ax.legend(loc='upper right', bbox_to_anchor=(0.98, 0.98), fontsize=12)
            legend.get_frame().set_facecolor('#3A404E')
            legend.get_frame().set_edgecolor('#505869')
            for text in legend.get_texts():
                text.set_color('#D3D8E0')

            # 更新图表并强制刷新布局
            self.figure.canvas.draw_idle()

            print(f"matplotlib误差线绘制成功:")
            print(f"  上误差线: y = {max_error_line_y:.3f}mm")
            print(f"  下误差线: y = {min_error_line_y:.3f}mm")
            print(f"  Y轴范围: {y_min:.2f} ~ {y_max:.2f}mm")

        except Exception as e:
            print(f"matplotlib误差线绘制失败: {e}")

    def remove_error_lines_and_reset_y_axis(self):
        """移除误差线并重置Y轴范围（matplotlib版本）"""
        # 移除最大直径误差线
        if hasattr(self, 'max_error_line') and self.max_error_line:
            try:
                self.max_error_line.remove()
            except:
                pass
            self.max_error_line = None

        # 移除最小直径误差线
        if hasattr(self, 'min_error_line') and self.min_error_line:
            try:
                self.min_error_line.remove()
            except:
                pass
            self.min_error_line = None

        # 重置图例（只有在data_line存在时）
        if hasattr(self, 'data_line') and self.data_line:
            try:
                self.ax.legend([self.data_line], ['测量数据'], loc='upper right', bbox_to_anchor=(0.95, 0.95), fontsize=10)
            except:
                # 如果data_line不可用，创建空图例
                self.ax.legend(loc='upper right', bbox_to_anchor=(0.95, 0.95), fontsize=10)

        # 恢复默认Y轴范围
        self.ax.set_ylim(16.5, 20.5)

        # 更新图表并强制刷新布局
        self.figure.canvas.draw_idle()

        print("移除误差线，恢复默认Y轴范围: 16.5 - 20.5mm")

    # 删除移除公差线方法

    def safe_adjust_splitter_sizes(self, splitter):
        """安全地调整分割器大小比例，检查对象有效性"""
        try:
            # 检查对象是否仍然有效
            if hasattr(self, 'height') and callable(self.height):
                self.adjust_splitter_sizes(splitter)
        except RuntimeError as e:
            # 对象已被删除，忽略错误
            print(f"对象已删除，跳过分割器调整: {e}")
        except Exception as e:
            # 其他错误也忽略
            print(f"分割器调整失败: {e}")

    def adjust_splitter_sizes(self, splitter):
        """调整分割器大小比例"""
        total_height = self.height()
        if total_height > 0:
            # 面板A占65%，面板B占35%
            panel_a_height = int(total_height * 0.65)
            panel_b_height = int(total_height * 0.35)
            splitter.setSizes([panel_a_height, panel_b_height])

            # 同时调整异常面板的高度
            self.adjust_anomaly_panel_height(panel_a_height)

    def adjust_anomaly_panel_height(self, panel_a_height):
        """动态调整异常面板高度，确保按钮不遮挡统计信息"""
        if hasattr(self, 'anomaly_scroll') and hasattr(self, 'next_sample_button'):
            # 计算可用高度：面板A高度 - 状态面板高度 - 按钮高度 - 间距
            available_height = panel_a_height - 80  # 减去状态面板和其他组件的高度
            button_height = 35  # 按钮高度
            spacing = 30  # 间距
            stats_height = 50  # 统计信息高度
            title_height = 25  # 标题高度

            # 计算滚动区域的最大高度
            max_scroll_height = available_height - button_height - spacing - stats_height - title_height

            # 设置最小高度，确保基本可用性
            min_scroll_height = 150
            scroll_height = max(min_scroll_height, max_scroll_height)

            # 应用高度限制
            if scroll_height > 0:
                self.anomaly_scroll.setMaximumHeight(int(scroll_height))
                self.anomaly_scroll.setMinimumHeight(min(min_scroll_height, int(scroll_height)))

    def resizeEvent(self, event):
        """窗口大小变化事件处理"""
        super().resizeEvent(event)
        # 延迟调整布局，确保窗口大小变化完成
        if hasattr(self, 'main_splitter'):
            QTimer.singleShot(50, lambda: self.adjust_splitter_sizes(self.main_splitter))

    def setup_chart(self):
        """设置图表属性和样式（matplotlib版本）"""
        # 固定标准直径为17.73mm
        self.standard_diameter = 17.73
        self.target_diameter = 17.73  # 目标直径，用于Y轴范围设置
        self.tolerance = 0.5  # 默认公差，用于异常检测
        self.upper_tolerance = 0.07  # 上公差 +0.07mm
        self.lower_tolerance = 0.05  # 下公差 -0.05mm

        # 初始化误差线
        self.max_error_line = None  # 最大直径误差线
        self.min_error_line = None  # 最小直径误差线

        # 数据缓冲队列系统 - 保证所有数据都绘制但控制速度
        from collections import deque
        self.data_queue = deque()  # 待绘制的数据队列
        self.is_drawing = False  # 是否正在绘制

        # 绘制速度控制定时器
        self.draw_timer = QTimer()
        self.draw_timer.timeout.connect(self.draw_next_data_point)
        self.draw_interval = 20  # 每150ms绘制一个数据点（可调整：50=快，300=慢）

        # 图表更新定时器（用于刷新显示）
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_plot)
        self.update_timer.start(50)  # 保持50ms刷新频率，确保界面流畅

        # 初始化缩放参数
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 10.0

        # 自动设置标准直径并绘制误差线
        self.set_standard_diameter(17.73)
        print(f"✅ 自动设置标准直径为: {self.standard_diameter}mm")

    def update_plot(self):
        """更新matplotlib图表显示 - 优化性能版本"""
        try:
            # 快速检查必要属性和数据有效性
            if not (hasattr(self, 'depth_data') and hasattr(self, 'diameter_data') and 
                    hasattr(self, 'data_line') and hasattr(self, 'ax') and hasattr(self, 'canvas')):
                return
            
            data_len = len(self.depth_data)
            if data_len == 0 or data_len != len(self.diameter_data):
                return

            # 显示所有数据，不限制显示点数
            self.data_line.set_data(self.depth_data, self.diameter_data)

            # 计算X轴范围
            if data_len > 1:
                x_min = self.depth_data[0]
                x_max = self.depth_data[-1]
            else:
                x_min = x_max = self.depth_data[0] if data_len == 1 else 0

            # 调整坐标轴范围
            if data_len > 0:
                x_range = x_max - x_min
                margin = max(x_range * 0.1, 50) if x_range > 0 else 50
                x_min_display = max(0, x_min - margin)
                self.ax.set_xlim(x_min_display, x_max + margin)

            # 重绘画布
            self.canvas.draw_idle()

        except Exception as e:
            # 输出错误信息用于调试，但不中断程序
            if not hasattr(self, '_plot_error_count'):
                self._plot_error_count = 0
            self._plot_error_count += 1

            # 只输出前5个错误，避免日志过多
            if self._plot_error_count <= 5:
                print(f"⚠️ 图表更新错误 #{self._plot_error_count}: {e}")
                import traceback
                print(f"详细错误: {traceback.format_exc()}")

    def cleanup(self):
        """清理资源，停止定时器"""
        try:
            if hasattr(self, 'update_timer') and self.update_timer:
                self.update_timer.stop()
            if hasattr(self, 'draw_timer') and self.draw_timer:
                self.draw_timer.stop()
            if hasattr(self, 'csv_timer') and self.csv_timer:
                self.csv_timer.stop()
            # 清空数据队列
            if hasattr(self, 'data_queue'):
                remaining = len(self.data_queue)
                if remaining > 0:
                    print(f"⚠️ 清理时队列中还有{remaining}个未绘制的数据点")
                self.data_queue.clear()
        except Exception:
            pass

    def closeEvent(self, event):
        """窗口关闭事件"""
        self.cleanup()
        super().closeEvent(event)

    def on_scroll(self, event):
        """处理鼠标滚轮缩放事件"""
        if event.inaxes != self.ax:
            return

        # 获取当前坐标轴范围
        x_min, x_max = self.ax.get_xlim()
        y_min, y_max = self.ax.get_ylim()

        # 获取鼠标位置
        x_mouse = event.xdata
        y_mouse = event.ydata

        if x_mouse is None or y_mouse is None:
            return

        # 设置缩放因子
        if event.button == 'up':
            # 向上滚动，放大
            scale_factor = 0.9
        elif event.button == 'down':
            # 向下滚动，缩小
            scale_factor = 1.1
        else:
            return

        # 计算新的坐标范围，以鼠标位置为中心缩放
        x_range = x_max - x_min
        y_range = y_max - y_min

        new_x_range = x_range * scale_factor
        new_y_range = y_range * scale_factor

        # 计算新的坐标范围
        new_x_min = x_mouse - (x_mouse - x_min) * scale_factor
        new_x_max = x_mouse + (x_max - x_mouse) * scale_factor
        new_y_min = y_mouse - (y_mouse - y_min) * scale_factor
        new_y_max = y_mouse + (y_max - y_mouse) * scale_factor

        # 限制缩放范围，避免过度缩放
        if new_x_range < 10:  # X轴最小范围10mm
            return
        if new_x_range > 2000:  # X轴最大范围2000mm
            return
        if new_y_range < 0.1:  # Y轴最小范围0.1mm
            return
        if new_y_range > 10:  # Y轴最大范围10mm
            return

        # 应用新的坐标范围
        self.ax.set_xlim(new_x_min, new_x_max)
        self.ax.set_ylim(new_y_min, new_y_max)

        # 重绘图表
        self.canvas.draw_idle()

        print(f"缩放: X轴[{new_x_min:.1f}, {new_x_max:.1f}], Y轴[{new_y_min:.3f}, {new_y_max:.3f}]")

    def on_mouse_press(self, event):
        """处理鼠标点击事件"""
        if event.inaxes != self.ax:
            return

        # 双击重置缩放
        if event.dblclick:
            self.reset_zoom()

    def reset_zoom(self):
        """重置缩放到默认视图"""
        if hasattr(self, 'standard_diameter') and self.standard_diameter:
            # 如果设置了标准直径，使用聚焦视图
            y_margin = 0.15
            y_min = self.standard_diameter - y_margin
            y_max = self.standard_diameter + y_margin
            self.ax.set_ylim(y_min, y_max)
        else:
            # 否则使用默认范围
            self.ax.set_ylim(16.5, 20.5)

        # X轴范围根据数据自动调整
        if len(self.depth_data) > 0:
            x_min = min(self.depth_data)
            x_max = max(self.depth_data)
            x_range = x_max - x_min

            if x_range > 0:
                margin = max(x_range * 0.1, 50)
                # 确保X轴最小值不小于0（深度不能为负）
                x_min_display = max(0, x_min - margin)
                self.ax.set_xlim(x_min_display, x_max + margin)
            else:
                self.ax.set_xlim(0, 950)
        else:
            self.ax.set_xlim(0, 950)

        # 重绘图表
        self.canvas.draw_idle()
        print("缩放已重置到默认视图")

    def reset_to_standard_view(self):
        """还原到标准直径设置后的坐标轴显示范围"""
        if hasattr(self, 'standard_diameter') and self.standard_diameter:
            # 还原到标准直径的聚焦视图
            y_margin = 0.15
            y_min = self.standard_diameter - y_margin
            y_max = self.standard_diameter + y_margin
            self.ax.set_ylim(y_min, y_max)

            # X轴范围根据当前数据自动调整
            if len(self.depth_data) > 0:
                x_min = min(self.depth_data)
                x_max = max(self.depth_data)
                x_range = x_max - x_min

                if x_range > 0:
                    margin = max(x_range * 0.1, 50)
                    # 确保X轴最小值不小于0（深度不能为负）
                    x_min_display = max(0, x_min - margin)
                    self.ax.set_xlim(x_min_display, x_max + margin)
                else:
                    self.ax.set_xlim(0, 950)
            else:
                self.ax.set_xlim(0, 950)

            # 重绘图表
            self.canvas.draw_idle()
            print(f"视图已还原到标准直径 {self.standard_diameter}mm 的显示范围")
        else:
            # 如果没有设置标准直径，还原到默认视图
            self.ax.set_ylim(16.5, 20.5)
            self.ax.set_xlim(0, 950)
            self.canvas.draw_idle()
            print("视图已还原到默认显示范围")
        
    def init_data_buffers(self):
        """初始化数据缓冲区"""
        # 注意：孔位数据映射现在在init_hole_data_mapping()中初始化
        # 这里只初始化基本的数据缓冲区

        # 内窥镜图片相关变量
        self.current_images = []  # 当前孔位的图片列表
        self.current_image_index = 0  # 当前显示的图片索引
        self.image_switch_points = []  # 图片切换的数据点位置
        self.endoscope_switching_enabled = False  # 图像切换功能是否启用
        self.current_hole_id = None  # 当前选中的孔位ID
        self.endoscope_image_timer = None  # 独立的内窥镜图像切换定时器
        self.endoscope_timer_interval = 7500  # 图像切换间隔（毫秒）- 已优化为0.3秒
        # 移除最大点数限制，允许显示所有数据
        self.depth_data = deque()  # 无限制的数据容器
        self.diameter_data = deque()  # 无限制的数据容器

        # 样品管理
        self.current_sample_index = 0
        self.sample_data_history = {}  # 存储多个样品的数据

        # 异常数据管理
        self.anomaly_data = []  # 存储异常数据点

        # 最大最小直径跟踪
        self.max_diameter = None  # 当前样品的最大直径
        self.min_diameter = None  # 当前样品的最小直径

        # CSV数据导入相关
        self.csv_data = []  # 存储CSV数据
        self.csv_data_index = 0  # 当前播放位置
        self.csv_timer = None  # CSV数据播放定时器
        self.is_csv_playing = False  # CSV数据播放状态

        # 多文件管理（向后兼容，但主要使用新的孔位映射）
        self.csv_file_list = []
        self.current_file_index = 0  # 当前文件索引
        self.csv_base_path = "Data/R001C001/CCIDM"  # 使用相对路径
    
    def init_camera_preview(self):
        """初始化摄像头预览功能"""
        try:
            # 连接摄像头预览信号到视频显示组件
            def connect_camera_signals():
                if hasattr(self.camera_preview, 'camera_thread') and self.camera_preview.camera_thread:
                    # 连接摄像头帧信号到视频显示组件
                    self.camera_preview.camera_thread.frameReady.connect(self.video_display.update_frame)
                    print("✅ 摄像头预览信号已连接到视频显示组件")
                else:
                    # 如果摄像头线程还没创建，延迟连接
                    QTimer.singleShot(1000, connect_camera_signals)
            
            # 监听摄像头预览状态变化
            if hasattr(self.camera_preview, 'preview_button'):
                # 连接预览按钮点击事件
                self.camera_preview.preview_button.clicked.connect(connect_camera_signals)
            
            # 自动启动摄像头预览（可选）
            # 注释掉自动启动，让用户手动控制
            # QTimer.singleShot(2000, lambda: self.camera_preview.start_preview())
            
            print("✅ 摄像头预览功能初始化完成")
            
        except Exception as e:
            print(f"⚠️ 摄像头预览初始化失败: {e}")
        
    @Slot(float, float)
    def update_data(self, depth, diameter):
        """
        更新图表数据的槽函数
        由工作线程的信号触发
        """
        # 添加新数据点
        self.depth_data.append(depth)
        self.diameter_data.append(diameter)

        # 检测异常数据
        self.check_anomaly(depth, diameter)

        # 保存当前样品数据
        self.save_current_sample_data(depth, diameter)

        # 更新最大最小直径
        self.update_diameter_extremes(diameter)

        # 更新图表（matplotlib版本在update_plot中处理）
        # matplotlib的数据更新由定时器驱动的update_plot方法处理

    @Slot(float, float)
    def on_realtime_data_received(self, depth, diameter):
        """
        接收实时数据的槽函数 - 使用队列缓冲系统
        由automation_worker的realtime_data_received信号触发
        """
        # 第一次接收到数据时的提示
        if not hasattr(self, '_first_data_received'):
            self._first_data_received = True
            self.log_text_edit.append(f"🎉 **开始接收实时数据!** 使用队列缓冲绘制...")
            self.log_text_edit.append(f"📊 绘制间隔: 每{self.draw_interval}ms绘制一个数据点")

        # 将数据加入队列，而不是立即绘制
        self.data_queue.append((depth, diameter))

        # 立即更新探头深度显示（不需要等待绘制）
        self.depth_label.setText(f"📏 探头深度: {depth:.1f} mm")

        # 如果绘制定时器还没启动，启动它
        if not self.draw_timer.isActive():
            self.draw_timer.start(self.draw_interval)
            self.is_drawing = True
            self.log_text_edit.append(f"🚀 **开始队列绘制** - 绘制速度: 每{self.draw_interval}ms一个点")

        # 统计信息
        if not hasattr(self, '_received_count'):
            self._received_count = 0
        self._received_count += 1

        # 前5个数据点输出接收确认
        if self._received_count <= 5:
            sequence = int(depth / 0.1) if depth > 0 else 0
            self.log_text_edit.append(f"🔍 接收第{self._received_count}个数据: 序号{sequence}, 深度{depth:.1f}mm, 直径{diameter:.4f}mm")

        # 每50个接收的数据输出队列状态
        if self._received_count % 50 == 0:
            queue_size = len(self.data_queue)
            drawn_count = len(self.depth_data)
            self.log_text_edit.append(f"📊 队列状态: 已接收{self._received_count}, 队列中{queue_size}, 已绘制{drawn_count}")

    def draw_next_data_point(self):
        """
        从队列中取出下一个数据点进行绘制
        """
        if self.data_queue:
            # 从队列中取出一个数据点
            depth, diameter = self.data_queue.popleft()

            # 绘制这个数据点
            self.update_data(depth, diameter)

            # 更新探头深度显示（确保显示最新绘制的深度）
            self.depth_label.setText(f"📏 探头深度: {depth:.1f} mm")

            # 每10个绘制的数据点输出一次进度
            drawn_count = len(self.depth_data)
            if drawn_count % 10 == 0:
                sequence = int(depth / 0.1) if depth > 0 else 0
                queue_size = len(self.data_queue)
                self.log_text_edit.append(f"🎨 绘制进度: 序号{sequence}, 深度{depth:.1f}mm, 已绘制{drawn_count}点, 队列剩余{queue_size}")
        else:
            # 队列为空，暂停绘制定时器
            self.draw_timer.stop()
            self.is_drawing = False

    def set_draw_speed(self, interval_ms):
        """
        设置绘制速度
        Args:
            interval_ms: 绘制间隔（毫秒）
                50 = 很快（每秒20个点）
                100 = 快速（每秒10个点）
                150 = 适中（每秒6.7个点）- 默认
                200 = 较慢（每秒5个点）
                300 = 慢速（每秒3.3个点）
                500 = 很慢（每秒2个点）
        """
        self.draw_interval = interval_ms
        if self.draw_timer.isActive():
            # 如果定时器正在运行，重新启动以应用新间隔
            self.draw_timer.stop()
            self.draw_timer.start(self.draw_interval)
        self.log_text_edit.append(f"⚙️ 绘制速度已调整: 每{interval_ms}ms绘制一个数据点")

    def update_diameter_extremes(self, diameter):
        """更新最大最小直径"""
        # 更新最大直径
        if self.max_diameter is None or diameter > self.max_diameter:
            self.max_diameter = diameter

        # 更新最小直径
        if self.min_diameter is None or diameter < self.min_diameter:
            self.min_diameter = diameter

        # 更新状态栏显示
        self.update_diameter_display()

    def update_diameter_display(self):
        """更新直径显示"""
        if self.max_diameter is not None:
            self.max_diameter_label.setText(f"📈 最大直径: {self.max_diameter:.3f} mm")
        else:
            self.max_diameter_label.setText("📈 最大直径: --")

        if self.min_diameter is not None:
            self.min_diameter_label.setText(f"📉 最小直径: {self.min_diameter:.3f} mm")
        else:
            self.min_diameter_label.setText("📉 最小直径: --")

    @Slot(str, float, str)
    def update_status(self, hole_id, probe_depth, comm_status):
        """
        更新状态信息的槽函数
        """
        # 更新当前孔位显示
        if hole_id and hole_id != "未知样品" and hole_id != "当前样品":
            self.current_hole_label.setText(f"当前孔位：{hole_id}")
            self.current_hole_id = hole_id

        self.depth_label.setText(f"📏 探头深度: {probe_depth:.1f} mm")

        # 使用新的通信状态更新方法
        if comm_status == "连接正常":
            self.update_comm_status("connected", comm_status)
        else:
            self.update_comm_status("error", comm_status)
    
    def clear_data(self):
        """清除所有数据"""
        self.depth_data.clear()
        self.diameter_data.clear()
        self.data_line.set_data([], [])
        self.canvas.draw()

        # 清除异常数据
        self.anomaly_data.clear()
        self.update_anomaly_display()

        # 清除内窥镜图像
        self.endoscope_view.clear_image()

        # 重置状态显示
        self.depth_label.setText("📏 探头深度: -- mm")
        self.update_comm_status("disconnected", "未连接")

        # 注意：不重置孔位显示，保持当前选中的孔位
        # 只有在完全重置时才清除孔位信息

        # 重置最大最小直径
        self.max_diameter = None
        self.min_diameter = None
        self.update_diameter_display()

    def reset_to_waiting_state(self):
        """完全重置到等待状态"""
        # 清除数据
        self.clear_data()

        # 重置孔位显示
        self.current_hole_label.setText("当前孔位：未选择")
        self.current_hole_id = None
        self.is_data_loaded = False

        # 保持开始按钮启用状态，支持直接启动采集程序
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.clear_button.setEnabled(True)

        # 更新按钮提示
        self.start_button.setToolTip("启动采集控制程序 (LEConfocalDemo.exe)")

        # 显示等待状态
        self.setup_waiting_state()

    def set_current_hole(self, hole_id):
        """设置当前检测的孔ID"""
        self.current_hole_id = hole_id
        self.current_hole_label.setText(f"当前孔位：{hole_id}")
        self.endoscope_view.set_hole_id(hole_id)
        print(f"✅ 设置当前检测孔位: {hole_id}")

    def start_measurement_for_hole(self, hole_id):
        """为指定孔开始测量"""
        self.set_current_hole(hole_id)
        self.clear_data()

        # 开始内窥镜图像采集
        self.endoscope_view.start_acquisition()

    def stop_measurement(self):
        """停止测量"""
        # 停止内窥镜图像采集
        self.endoscope_view.stop_acquisition()

    def check_anomaly(self, depth, diameter):
        """检测异常数据点"""
        # 只有在设置了标准直径时才进行异常检测
        if hasattr(self, 'standard_diameter') and self.standard_diameter is not None:
            # 检查是否超出上下公差范围
            upper_limit = self.standard_diameter + self.upper_tolerance
            lower_limit = self.standard_diameter - self.lower_tolerance

            if diameter > upper_limit or diameter < lower_limit:
                # 计算偏差（相对于最近的公差边界）
                if diameter > upper_limit:
                    deviation = diameter - upper_limit
                else:
                    deviation = lower_limit - diameter

                # 添加到异常数据列表
                anomaly_info = {
                    'depth': depth,
                    'diameter': diameter,
                    'deviation': deviation,
                    'standard_diameter': self.standard_diameter,
                    'upper_limit': upper_limit,
                    'lower_limit': lower_limit,
                    'sample_id': self.current_hole_id or f"Sample_{self.current_sample_index}"
                }
                self.anomaly_data.append(anomaly_info)

                # 更新异常显示
                self.update_anomaly_display()

    def update_anomaly_display(self):
        """更新异常数据显示"""
        # 清除现有显示
        for i in reversed(range(self.anomaly_content_layout.count())):
            child = self.anomaly_content_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        # 显示最近的异常数据（最多显示10个）
        recent_anomalies = self.anomaly_data[-10:] if len(self.anomaly_data) > 10 else self.anomaly_data

        for anomaly in recent_anomalies:
            anomaly_widget = QWidget()
            anomaly_layout = QHBoxLayout(anomaly_widget)
            anomaly_layout.setContentsMargins(5, 2, 5, 2)

            # 深度和直径信息
            info_label = QLabel(f"深度: {anomaly['depth']:.1f}mm\n直径: {anomaly['diameter']:.3f}mm")
            info_label.setStyleSheet("font-size: 10px; color: red;")
            anomaly_layout.addWidget(info_label)

            # 偏差信息
            deviation_label = QLabel(f"偏差: {anomaly['deviation']:.3f}mm")
            deviation_label.setStyleSheet("font-size: 10px; font-weight: bold; color: red;")
            anomaly_layout.addWidget(deviation_label)

            self.anomaly_content_layout.addWidget(anomaly_widget)

        # 更新统计信息
        total_points = len(self.depth_data)
        anomaly_count = len(self.anomaly_data)
        anomaly_rate = (anomaly_count / total_points * 100) if total_points > 0 else 0

        # 更新大号异常计数显示
        self.anomaly_count_number.setText(str(anomaly_count))
        self.anomaly_rate_label.setText(f"异常率: {anomaly_rate:.1f}%")

    def save_current_sample_data(self, depth, diameter):
        """保存当前样品数据"""
        sample_key = self.current_hole_id or f"Sample_{self.current_sample_index}"
        if sample_key not in self.sample_data_history:
            self.sample_data_history[sample_key] = {
                'depths': [],
                'diameters': [],
                'anomalies': []
            }

        self.sample_data_history[sample_key]['depths'].append(depth)
        self.sample_data_history[sample_key]['diameters'].append(diameter)

        # 如果是异常点，也保存到样品的异常列表中
        deviation = abs(diameter - self.target_diameter)
        if deviation > self.tolerance:
            self.sample_data_history[sample_key]['anomalies'].append({
                'depth': depth,
                'diameter': diameter,
                'deviation': deviation
            })

    def view_next_sample(self):
        """查看下一个样品 - 基于孔位ID切换（R001C001 → R001C002 → R001C003...）"""
        # 停止当前播放
        if self.is_csv_playing:
            self.stop_csv_data_import()

        # 定义孔位切换顺序
        hole_sequence = ["R001C001", "R001C002"]

        # 获取当前孔位ID
        current_hole = self.current_hole_id

        # 确定下一个孔位
        next_hole = None
        if current_hole in hole_sequence:
            current_index = hole_sequence.index(current_hole)
            next_index = (current_index + 1) % len(hole_sequence)  # 循环切换
            next_hole = hole_sequence[next_index]
        else:
            # 如果当前孔位不在序列中，默认切换到第一个
            next_hole = hole_sequence[0]

        print(f"🔄 切换样品: {current_hole} → {next_hole}")

        # 检查下一个孔位是否有数据
        if next_hole not in self.hole_to_csv_map:
            print(f"❌ 孔位 {next_hole} 没有关联的数据文件")
            QMessageBox.information(self, "信息", f"孔位 {next_hole} 没有可用的数据文件")
            return

        # 加载下一个孔位的数据
        try:
            self.load_data_for_hole(next_hole)

            # 更新主窗口状态栏显示
            self.update_main_window_status(next_hole)

            print(f"✅ 成功切换到孔位: {next_hole}")
        except Exception as e:
            print(f"❌ 切换到孔位 {next_hole} 失败: {e}")
            QMessageBox.warning(self, "错误", f"切换到孔位 {next_hole} 失败:\n{str(e)}")

    def update_main_window_status(self, hole_id):
        """更新主窗口状态栏显示"""
        try:
            # 查找主窗口
            main_window = None
            parent = self.parent()
            while parent:
                if hasattr(parent, 'status_label'):
                    main_window = parent
                    break
                parent = parent.parent()

            # 更新状态栏
            if main_window and hasattr(main_window, 'status_label'):
                main_window.status_label.setText(f"实时监控 - {hole_id}")
                print(f"✅ 更新主窗口状态栏: 实时监控 - {hole_id}")
            else:
                print("⚠️ 未找到主窗口状态栏，无法更新")

        except Exception as e:
            print(f"⚠️ 更新主窗口状态栏失败: {e}")

    def load_sample_data(self, sample_key):
        """加载指定样品的数据"""
        if sample_key not in self.sample_data_history:
            return

        sample_data = self.sample_data_history[sample_key]

        # 清除当前显示
        self.depth_data.clear()
        self.diameter_data.clear()
        self.anomaly_data.clear()

        # 加载历史数据
        for depth, diameter in zip(sample_data['depths'], sample_data['diameters']):
            self.depth_data.append(depth)
            self.diameter_data.append(diameter)

        # 加载异常数据
        self.anomaly_data = sample_data['anomalies'].copy()

        # 更新显示
        if len(self.depth_data) > 0:
            self.data_curve.setData(
                x=list(self.depth_data),
                y=list(self.diameter_data)
            )

        self.update_anomaly_display()
        self.current_hole_id = sample_key

    def set_tolerance_limits(self, target, tolerance):
        """设置公差限制 - 已废弃，删除目标线引用"""
        self.target_diameter = target
        self.tolerance = tolerance

        # 删除所有公差线和目标线相关代码
        # 调整Y轴范围
        margin = tolerance * 3
        self.plot_widget.setYRange(target - margin, target + margin)
        
    def get_current_statistics(self):
        """获取当前数据的统计信息"""
        if len(self.diameter_data) == 0:
            return None
            
        diameters = list(self.diameter_data)
        return {
            'count': len(diameters),
            'mean': np.mean(diameters),
            'std': np.std(diameters),
            'min': np.min(diameters),
            'max': np.max(diameters),
            'in_tolerance': sum(
                1 for d in diameters 
                if abs(d - self.target_diameter) <= self.tolerance
            ),
            'out_of_tolerance': sum(
                1 for d in diameters 
                if abs(d - self.target_diameter) > self.tolerance
            )
        }

    def load_data_for_hole(self, hole_id):
        """为指定的孔加载并显示其对应的CSV数据和内窥镜图片"""
        import os

        if hole_id not in self.hole_to_csv_map:
            QMessageBox.information(self, "信息", f"孔 {hole_id} 没有关联的CSV数据文件。")
            return

        csv_dir = self.hole_to_csv_map[hole_id]
        print(f"🔄 为孔 {hole_id} 加载数据目录: {csv_dir}")
        print(f"🔍 检查目录是否存在: {os.path.exists(csv_dir)}")

        # 查找目录中的CSV文件
        csv_file = None
        if os.path.exists(csv_dir):
            try:
                files_in_dir = os.listdir(csv_dir)
                print(f"📁 目录中的文件: {files_in_dir}")

                for file in files_in_dir:
                    if file.endswith('.csv'):
                        csv_file = os.path.join(csv_dir, file)
                        print(f"✅ 找到CSV文件: {file}")
                        break

                if not csv_file:
                    print(f"❌ 目录中没有CSV文件")
            except Exception as e:
                print(f"❌ 读取目录失败: {e}")
        else:
            print(f"❌ 目录不存在: {csv_dir}")

        if not csv_file:
            QMessageBox.warning(self, "错误", f"在目录 {csv_dir} 中未找到CSV文件\n请检查路径是否正确")
            return

        print(f"📄 准备加载CSV文件: {csv_file}")

        # 停止当前可能正在播放的任何数据
        if hasattr(self, 'is_csv_playing') and self.is_csv_playing:
            self.stop_csv_data_import()

        # 清除旧数据
        self.clear_data()

        # 加载新的CSV文件
        if self.load_csv_data(file_path=csv_file):
            self.set_current_hole(hole_id)

            # 设置当前孔位ID，用于状态显示
            self.current_hole_id = hole_id
            self.is_data_loaded = True  # 标记数据已加载

            # 加载对应的内窥镜图片
            self.load_endoscope_images_for_hole(hole_id)

            # 设置图表用于数据显示
            self.setup_chart_for_data()

            # 启用控制按钮
            self.enable_controls_after_data_load()

            # 自动开始播放
            self.start_csv_data_import(auto_play=True)

            print(f"✅ 成功从主检测界面加载孔位 {hole_id} 的数据")
        else:
            QMessageBox.warning(self, "错误", f"无法加载文件: \n{csv_file}")

    def start_csv_data_import(self, auto_play=False):
        """开始CSV数据导入"""
        # 如果是自动播放模式，数据应该已经加载了
        if auto_play:
            if not self.csv_data:
                print("❌ 自动播放模式下没有可用的CSV数据")
                return
        else:
            # 手动模式：如果没有数据，尝试从文件列表加载
            if not self.csv_data:
                if not hasattr(self, 'csv_file_list') or not self.csv_file_list:
                    print("❌ 没有可用的CSV文件列表")
                    return
                current_file = self.csv_file_list[self.current_file_index]
                print(f"🚀 开始CSV数据导入 - 文件: {current_file}")
                if not self.load_csv_data():
                    print("❌ CSV数据加载失败")
                    return

        # 清除现有数据
        self.clear_data()

        # 重置播放位置
        self.csv_data_index = 0

        # 设置标准直径
        self.set_standard_diameter_for_csv()

        # 开始播放 - 降低频率提高稳定性
        self.is_csv_playing = True
        self.csv_timer = QTimer()
        self.csv_timer.timeout.connect(self.update_csv_data_point)
        self.csv_timer.start(10)  # 每10ms更新一个数据点，提高绘图流畅度

        # 更新按钮状态
        self.start_button.setText("测量中...")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        # 启动独立的内窥镜图像切换
        self.start_endoscope_auto_switching()

        print(f"📊 开始播放CSV数据，共{len(self.csv_data)}个数据点")

    def stop_csv_data_import(self):
        """停止CSV数据导入"""
        print("⏸️ 停止CSV数据导入")

        if self.csv_timer:
            self.csv_timer.stop()
            self.csv_timer = None

        self.is_csv_playing = False
        
        # 停止内窥镜图像自动切换
        self.stop_endoscope_auto_switching()

        # 更新按钮状态
        self.start_button.setText("开始测量")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        # 显示当前进度
        if self.csv_data:
            progress = (self.csv_data_index / len(self.csv_data)) * 100
            print(f"📊 数据导入已暂停，进度: {progress:.1f}%")

    def load_csv_data(self, file_path=None):
        """加载CSV数据文件"""
        import csv
        import os

        # 如果未提供路径，则使用文件列表中的当前文件
        if file_path is None:
            if self.current_file_index >= len(self.csv_file_list):
                print(f"❌ 文件索引超出范围: {self.current_file_index}")
                return False
            filename = self.csv_file_list[self.current_file_index]
            file_path = os.path.join(self.csv_base_path, filename)

        try:
            if not os.path.exists(file_path):
                print(f"❌ 文件不存在: {file_path}")
                return False

            print(f"📁 加载CSV文件: {file_path}")

            # 尝试不同的编码
            encodings = ['gbk', 'gb2312', 'utf-8', 'latin-1']

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        reader = csv.reader(file)
                        headers = next(reader)

                        # 找到目标列
                        measurement_col = None
                        diameter_col = None

                        for i, header in enumerate(headers):
                            if '测量序号' in header:
                                measurement_col = i
                            elif '计算直径' in header:
                                diameter_col = i

                        if measurement_col is None or diameter_col is None:
                            print(f"⚠️ 未找到必要的列: 测量序号={measurement_col}, 计算直径={diameter_col}")
                            # 尝试使用默认列索引
                            measurement_col = 0
                            diameter_col = 4  # 根据之前的分析，计算直径在第5列（索引4）

                        # 读取数据
                        self.csv_data = []
                        for row in reader:
                            if len(row) > max(measurement_col, diameter_col):
                                try:
                                    measurement_num = int(row[measurement_col])
                                    diameter_value = float(row[diameter_col])

                                    # 模拟深度数据（基于测量序号）
                                    depth_value = measurement_num * 1.0  # 每个测量点1.0mm深度

                                    self.csv_data.append({
                                        'measurement': measurement_num,
                                        'depth': depth_value,
                                        'diameter': diameter_value
                                    })
                                except (ValueError, IndexError):
                                    continue

                        print(f"✅ 成功加载 {len(self.csv_data)} 个数据点 (编码: {encoding})")
                        return True

                except UnicodeDecodeError:
                    continue

            print(f"❌ 无法使用任何编码读取文件: {file_path}")
            return False

        except Exception as e:
            print(f"❌ 加载CSV文件失败: {e}")
            return False

    def load_csv_data_by_index(self, file_index):
        """按索引加载CSV数据文件"""
        import csv
        import os

        if file_index >= len(self.csv_file_list):
            print(f"❌ 文件索引超出范围: {file_index}")
            return False

        filename = self.csv_file_list[file_index]
        file_path = os.path.join(self.csv_base_path, filename)

        try:
            if not os.path.exists(file_path):
                print(f"❌ 文件不存在: {file_path}")
                return False

            print(f"📁 加载CSV文件: {file_path}")

            with open(file_path, 'r', encoding='gbk') as file:
                reader = csv.reader(file)
                headers = next(reader)

                # 找到目标列
                measurement_col = None
                diameter_col = None

                for i, header in enumerate(headers):
                    if '测量序号' in header:
                        measurement_col = i
                    if '计算直径' in header:
                        diameter_col = i

                if measurement_col is None or diameter_col is None:
                    print(f"❌ 找不到必需的列")
                    return False

                # 读取数据
                self.csv_data = []
                for row in reader:
                    try:
                        if len(row) > max(measurement_col, diameter_col):
                            measurement_num = int(row[measurement_col])
                            diameter = float(row[diameter_col])
                            # 每个测量点对应1.0mm深度
                            depth = measurement_num * 1.0
                            self.csv_data.append((depth, diameter))
                    except (ValueError, IndexError):
                        continue

                if len(self.csv_data) == 0:
                    print("❌ 没有有效数据")
                    return False

                # 计算统计信息
                depths = [d[0] for d in self.csv_data]
                diameters = [d[1] for d in self.csv_data]

                min_depth = min(depths)
                max_depth = max(depths)
                min_diameter = min(diameters)
                max_diameter = max(diameters)
                avg_diameter = sum(diameters) / len(diameters)

                print(f"✅ CSV数据加载成功:")
                print(f"   数据点数量: {len(self.csv_data)}")
                print(f"   深度范围: {min_depth:.0f} - {max_depth:.0f} mm")
                print(f"   直径范围: {min_diameter:.3f} - {max_diameter:.3f} mm")
                print(f"   平均直径: {avg_diameter:.3f} mm")

                self.csv_avg_diameter = avg_diameter
                return True

        except Exception as e:
            print(f"❌ CSV加载错误: {e}")
            return False

    def set_standard_diameter_for_csv(self):
        """为CSV数据设置标准直径"""
        # 标准直径已固定为17.73mm，无需额外设置
        print(f"🎯 使用固定标准直径: {self.standard_diameter} mm")

    def update_csv_data_point(self):
        """更新CSV数据点"""
        if self.csv_data_index >= len(self.csv_data):
            # 播放完成
            print("✅ CSV数据播放完成")
            self.stop_csv_data_import()

            # 显示最终统计
            final_max = self.max_diameter if self.max_diameter else 0
            final_min = self.min_diameter if self.min_diameter else 0

            print(f"📊 最终统计:")
            print(f"   最大圆直径: {final_max:.3f} mm")
            print(f"   最小圆直径: {final_min:.3f} mm")
            print(f"   直径范围: {final_max - final_min:.3f} mm")

            return

        # 获取当前数据点 - 支持两种数据格式
        data_point = self.csv_data[self.csv_data_index]
        if isinstance(data_point, dict):
            # 新格式：字典
            depth = data_point['depth']
            diameter = data_point['diameter']
        else:
            # 旧格式：元组
            depth, diameter = data_point

        # 更新图表
        self.update_data(depth, diameter)

        # 确定样品名称 - 兼容新旧两种模式
        if hasattr(self, 'current_hole_id') and self.current_hole_id:
            # 新模式：使用当前选中的孔位ID
            sample_name = self.current_hole_id
        elif hasattr(self, 'csv_file_list') and self.csv_file_list and hasattr(self, 'current_file_index'):
            # 旧模式：使用文件列表索引
            try:
                current_file = self.csv_file_list[self.current_file_index]
                sample_name = f"H0{self.current_file_index + 1}"
            except (IndexError, AttributeError):
                sample_name = "未知样品"
        else:
            # 默认模式
            sample_name = "当前样品"

        self.update_status(sample_name, depth, "测量中")

        # 输出进度（每100个数据点输出一次）
        if self.csv_data_index % 100 == 0:
            progress = ((self.csv_data_index + 1) / len(self.csv_data)) * 100
            current_max = self.max_diameter if self.max_diameter else 0
            current_min = self.min_diameter if self.min_diameter else 0
            print(f"📊 测量进度: {progress:.1f}% - 深度: {depth:.0f}mm, 直径: {diameter:.3f}mm | "
                  f"最大: {current_max:.3f}mm, 最小: {current_min:.3f}mm")

        self.csv_data_index += 1

        # 检查是否需要切换内窥镜图片 - 已禁用，使用独立定时器切换
        # self.update_endoscope_image_by_progress()

    def load_endoscope_images_for_hole(self, hole_id):
        """为指定孔位加载内窥镜图片"""
        import os
        import glob

        if hole_id not in self.hole_to_image_map:
            print(f"⚠️ 孔位 {hole_id} 没有关联的内窥镜图片目录")
            self.current_images = []
            return

        images_dir = self.hole_to_image_map[hole_id]
        if not os.path.exists(images_dir):
            print(f"⚠️ 图片目录不存在: {images_dir}")
            self.current_images = []
            return

        # 获取所有PNG图片文件
        image_files = glob.glob(os.path.join(images_dir, "*.png"))

        if not image_files:
            print(f"⚠️ 目录中没有找到PNG图片: {images_dir}")
            self.current_images = []
            return

        # 按文件名排序（确保按数值从小到大）
        def extract_number(filename):
            """从文件名中提取数值用于排序"""
            import re
            basename = os.path.basename(filename)
            # 提取文件名中的数字部分，如 "1-1.2.png" -> 1.2, "2-3.0.png" -> 3.0
            match = re.search(r'-(\d+\.?\d*)', basename)
            if match:
                return float(match.group(1))
            return 0

        image_files.sort(key=extract_number)
        self.current_images = image_files
        self.current_image_index = 0

        print(f"✅ 为孔位 {hole_id} 加载了 {len(image_files)} 张内窥镜图片:")
        for i, img in enumerate(image_files):
            print(f"   {i+1}. {os.path.basename(img)}")

        # 计算图片切换点
        self.calculate_image_switch_points()

        # 显示第一张图片
        if self.current_images:
            print("📸 自动显示第一张内窥镜图像")
            self.display_endoscope_image(0)
        else:
            print("❌ 没有图像可显示")

    def calculate_image_switch_points(self):
        """计算图片切换的数据点位置"""
        if not self.current_images or not self.csv_data:
            self.image_switch_points = []
            return

        total_data_points = len(self.csv_data)
        num_images = len(self.current_images)

        # 将数据点均匀分配给每张图片
        points_per_image = total_data_points / num_images

        self.image_switch_points = []
        for i in range(num_images):
            switch_point = int(i * points_per_image)
            self.image_switch_points.append(switch_point)

        print(f"📊 图片切换点计算完成:")
        print(f"   总数据点: {total_data_points}, 图片数量: {num_images}")
        print(f"   每张图片约 {points_per_image:.1f} 个数据点")
        print(f"   切换点: {self.image_switch_points}")

    def update_endoscope_image_by_progress(self):
        """根据CSV播放进度更新内窥镜图片"""
        # 只要有图像数据就允许切换，不需要等待"启动算法"
        if not self.current_images or not self.image_switch_points:
            return

        current_progress = self.csv_data_index

        # 确定当前应该显示哪张图片
        target_image_index = 0
        for i, switch_point in enumerate(self.image_switch_points):
            if current_progress >= switch_point:
                target_image_index = i
            else:
                break

        # 如果需要切换图片
        if target_image_index != self.current_image_index:
            self.current_image_index = target_image_index
            self.display_endoscope_image(target_image_index)

            progress_percent = (current_progress / len(self.csv_data)) * 100
            print(f"🖼️ 切换内窥镜图片: 第{target_image_index + 1}张 "
                  f"(进度: {progress_percent:.1f}%, 数据点: {current_progress})")

    def display_endoscope_image(self, image_index):
        """显示指定索引的内窥镜图片"""
        import os

        print(f"🔍 调试: 尝试显示图像索引 {image_index}")
        print(f"🔍 调试: 当前图像列表长度 {len(self.current_images) if self.current_images else 0}")

        if not self.current_images:
            print("❌ 调试: 图像列表为空")
            return

        if image_index >= len(self.current_images):
            print(f"❌ 调试: 索引超出范围 {image_index}/{len(self.current_images)}")
            return

        image_path = self.current_images[image_index]
        print(f"🔍 调试: 图像路径 {image_path}")
        print(f"🔍 调试: 文件存在 {os.path.exists(image_path)}")

        try:
            # 使用内窥镜视图组件显示图片
            self.endoscope_view.update_image(image_path)
            print(f"✅ 显示内窥镜图片: {os.path.basename(image_path)}")

        except Exception as e:
            print(f"❌ 显示内窥镜图片失败: {e}")
            import traceback
            print(f"🔍 详细错误信息: {traceback.format_exc()}")

    # 旧的启动函数已删除，使用新的自动化流程

    # 旧的运动台启动函数已删除，使用新的自动化流程

    # 旧的采集程序启动函数已删除，使用新的自动化流程

    # 旧的扩展监控函数已删除，使用新的自动化流程

    def stop_measurement_process(self):
        """停止测量过程 - 停止采集程序和运动台控制程序"""
        import subprocess

        print("🛑 开始停止测量过程...")

        # 停止延迟启动定时器
        if hasattr(self, 'acquisition_start_timer') and self.acquisition_start_timer:
            self.acquisition_start_timer.stop()
            self.acquisition_start_timer = None
            print("🛑 停止采集程序延迟启动定时器")

        # 停止扩展监控定时器
        if hasattr(self, 'extended_monitor_timer') and self.extended_monitor_timer:
            self.extended_monitor_timer.stop()
            print("🛑 停止扩展监控定时器")

        # 停止采集程序
        if self.acquisition_process and self.acquisition_process.poll() is None:
            try:
                print(f"⏹️ 停止采集程序，进程ID: {self.acquisition_process.pid}")

                # 终止外部程序
                self.acquisition_process.terminate()

                # 等待程序结束（最多等待5秒）
                try:
                    self.acquisition_process.wait(timeout=5)
                    print("✅ 采集程序已正常结束")
                except subprocess.TimeoutExpired:
                    # 如果5秒内没有结束，强制杀死
                    print("⚠️ 采集程序未在5秒内结束，强制终止")
                    self.acquisition_process.kill()
                    self.acquisition_process.wait()
                    print("✅ 采集程序已强制终止")

                self.acquisition_process = None

            except Exception as e:
                print(f"❌ 停止采集程序失败: {e}")

        # 停止运动台控制程序（注意：remote_launcher.py通常执行完就退出了）
        if hasattr(self, 'remote_launcher_process') and self.remote_launcher_process and self.remote_launcher_process.poll() is None:
            try:
                print(f"⏹️ 停止运动台控制程序，进程ID: {self.remote_launcher_process.pid}")

                # 终止运动台控制程序
                self.remote_launcher_process.terminate()

                # 等待程序结束（最多等待3秒）
                try:
                    self.remote_launcher_process.wait(timeout=3)
                    print("✅ 运动台控制程序已正常结束")
                except subprocess.TimeoutExpired:
                    print("⚠️ 运动台控制程序未在3秒内结束，强制终止")
                    self.remote_launcher_process.kill()
                    self.remote_launcher_process.wait()
                    print("✅ 运动台控制程序已强制终止")

                self.remote_launcher_process = None

            except Exception as e:
                print(f"❌ 停止运动台控制程序失败: {e}")
        else:
            print("📋 运动台控制程序已经结束（这是正常的，因为remote_launcher.py执行完就退出）")

        # 如果没有外部程序在运行，停止CSV播放
        if not self.acquisition_process:
            self.stop_csv_data_import()

        # 更新按钮状态
        self.start_button.setText("▶️ 开始监测")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        # 更新状态显示
        self.update_comm_status("disconnected", "所有程序已停止")

        # 停止进程监控
        self.stop_process_monitor()

        # 停止实时CSV监控
        self.stop_realtime_csv_monitoring()



        print("✅ 测量过程停止完成")

    def start_process_monitor(self):
        """启动进程监控定时器"""
        if not hasattr(self, 'process_monitor_timer'):
            from PySide6.QtCore import QTimer
            self.process_monitor_timer = QTimer()
            self.process_monitor_timer.timeout.connect(self.check_process_status)

        self.process_monitor_timer.start(2000)  # 每2秒检查一次
        print("🔍 进程监控已启动")

    def stop_process_monitor(self):
        """停止进程监控定时器"""
        if hasattr(self, 'process_monitor_timer') and self.process_monitor_timer.isActive():
            self.process_monitor_timer.stop()
            print("⏹️ 进程监控已停止")

    def check_process_status(self):
        """检查外部程序进程状态"""
        if self.acquisition_process:
            poll_result = self.acquisition_process.poll()
            if poll_result is not None:
                # 程序已结束
                print(f"📋 外部采集程序已结束，退出码: {poll_result}")

                # 自动恢复按钮状态
                self.start_button.setText("▶️ 开始监测")
                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(False)

                # 更新状态显示
                if poll_result == 0:
                    self.update_comm_status("disconnected", "采集程序正常结束")
                else:
                    self.update_comm_status("error", f"采集程序异常结束 (退出码: {poll_result})")

                self.acquisition_process = None
                self.stop_process_monitor()

    def start_realtime_csv_monitoring(self):
        """启动实时CSV文件监控"""
        import os
        try:
            # 尝试导入watchdog库
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler

            class CSVFileHandler(FileSystemEventHandler):
                def __init__(self, chart_instance):
                    self.chart = chart_instance

                def on_created(self, event):
                    """文件创建事件"""
                    if not event.is_directory and event.src_path.endswith('.csv'):
                        print(f"🆕 检测到新CSV文件: {event.src_path}")
                        self.chart.process_new_csv_file(event.src_path)

                def on_modified(self, event):
                    """文件修改事件"""
                    if not event.is_directory and event.src_path.endswith('.csv'):
                        print(f"📝 检测到CSV文件更新: {event.src_path}")
                        self.chart.process_updated_csv_file(event.src_path)

            # 创建监控器
            self.csv_monitor = Observer()
            event_handler = CSVFileHandler(self)

            # 监控指定文件夹
            if os.path.exists(self.csv_watch_folder):
                self.csv_monitor.schedule(event_handler, self.csv_watch_folder, recursive=True)
                self.csv_monitor.start()
                self.is_realtime_monitoring = True
                print(f"✅ 开始监控CSV文件夹: {self.csv_watch_folder}")
                return True
            else:
                print(f"❌ 监控文件夹不存在: {self.csv_watch_folder}")
                return False

        except ImportError:
            print("⚠️ watchdog库未安装，使用定时器轮询方案")
            return self.start_polling_csv_monitoring()
        except Exception as e:
            print(f"❌ 启动文件监控失败: {e}")
            return self.start_polling_csv_monitoring()

    def start_polling_csv_monitoring(self):
        """启动定时器轮询CSV文件监控（备选方案）"""
        import os
        if not os.path.exists(self.csv_watch_folder):
            print(f"❌ 监控文件夹不存在: {self.csv_watch_folder}")
            return False

        # 创建定时器，每1秒检查一次
        self.csv_file_monitor_timer = QTimer()
        self.csv_file_monitor_timer.timeout.connect(self.check_for_new_csv_files)
        self.csv_file_monitor_timer.start(1000)  # 1秒间隔

        self.is_realtime_monitoring = True
        print(f"✅ 开始轮询监控CSV文件夹: {self.csv_watch_folder}")
        return True

    def check_for_new_csv_files(self):
        """检查新的CSV文件（轮询方式）"""
        import os
        try:
            # 查找最新的CSV文件
            csv_files = []
            for root, dirs, files in os.walk(self.csv_watch_folder):
                for file in files:
                    if file.endswith('.csv'):
                        file_path = os.path.join(root, file)
                        csv_files.append((file_path, os.path.getmtime(file_path)))

            if csv_files:
                # 按修改时间排序，获取最新文件
                csv_files.sort(key=lambda x: x[1], reverse=True)
                latest_file = csv_files[0][0]

                # 检查是否是新文件
                if latest_file != self.last_csv_file:
                    print(f"🆕 发现新CSV文件: {latest_file}")
                    self.last_csv_file = latest_file
                    self.process_new_csv_file(latest_file)

        except Exception as e:
            print(f"❌ 检查CSV文件失败: {e}")

    def closeEvent(self, event):
        """窗口关闭事件 - 确保清理外部程序"""
        self.stop_measurement_process()
        self.stop_realtime_csv_monitoring()
        try:
            super().closeEvent(event)
        except AttributeError:
            # 如果父类没有closeEvent方法，直接接受事件
            event.accept()

    def process_new_csv_file(self, file_path):
        """处理新的CSV文件"""
        print(f"📄 开始处理新CSV文件: {file_path}")

        # 等待文件写入完成（避免读取不完整的文件）
        import time
        time.sleep(0.5)

        # 清除当前数据
        self.clear_data()



        # 加载新CSV文件
        if self.load_realtime_csv_data(file_path):
            # 开始实时播放
            self.start_realtime_csv_playback()
        else:
            print(f"❌ 加载CSV文件失败: {file_path}")

    def process_updated_csv_file(self, file_path):
        """处理更新的CSV文件（增量数据）"""
        if file_path == self.last_csv_file:
            print(f"📝 处理CSV文件更新: {file_path}")
            # 读取新增的数据行
            self.load_incremental_csv_data(file_path)

    def load_realtime_csv_data(self, file_path):
        """加载实时CSV数据"""
        import csv

        try:
            self.csv_data = []
            encodings = ['gbk', 'gb2312', 'utf-8', 'latin-1']

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        reader = csv.reader(file)

                        # 跳过标题行（如果有）
                        first_row = next(reader, None)
                        if first_row and not self.is_numeric_row(first_row):
                            print(f"📋 跳过标题行: {first_row}")
                        else:
                            # 第一行就是数据，重新处理
                            if first_row and self.is_numeric_row(first_row):
                                depth, diameter = self.extract_depth_diameter(first_row)
                                if depth is not None and diameter is not None:
                                    self.csv_data.append((depth, diameter))

                        # 读取数据行
                        for row in reader:
                            if len(row) >= 2 and self.is_numeric_row(row):
                                try:
                                    depth, diameter = self.extract_depth_diameter(row)
                                    if depth is not None and diameter is not None:
                                        self.csv_data.append((depth, diameter))
                                except ValueError:
                                    continue

                    print(f"✅ 成功加载实时CSV数据: {len(self.csv_data)} 个数据点")

                    # 显示数据统计
                    if self.csv_data:
                        depths = [d[0] for d in self.csv_data]
                        diameters = [d[1] for d in self.csv_data]
                        print(f"📊 深度范围: {min(depths):.1f} - {max(depths):.1f}")
                        print(f"📊 直径范围: {min(diameters):.3f} - {max(diameters):.3f} mm")
                        print(f"📊 平均直径: {sum(diameters)/len(diameters):.3f} mm")

                    return True

                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    print(f"❌ 加载CSV失败 (编码: {encoding}): {e}")
                    continue

            return False

        except Exception as e:
            print(f"❌ 加载实时CSV数据失败: {e}")
            return False

    def extract_depth_diameter(self, row):
        """从CSV行中提取深度和直径数据"""
        try:
            # 检查不同的CSV格式
            if len(row) >= 5:
                # R0_C0.csv格式: 测量序号,通道1值,通道2值,通道3值,管孔直径
                sequence = float(row[0])  # 测量序号作为深度
                diameter = float(row[4])  # 管孔直径(mm)

                # 将序号转换为深度（假设每个测量点间隔0.1mm）
                depth = sequence * 0.1

                return depth, diameter

            elif len(row) >= 2:
                # 标准格式: 深度,直径
                depth = float(row[0])
                diameter = float(row[1])
                return depth, diameter
            else:
                return None, None

        except (ValueError, IndexError):
            return None, None

    def is_numeric_row(self, row):
        """检查行是否为数值数据"""
        if len(row) < 2:
            return False
        try:
            float(row[0])
            float(row[1])
            return True
        except ValueError:
            return False

    def start_realtime_csv_playback(self):
        """开始实时CSV数据播放"""
        if not self.csv_data:
            print("❌ 没有CSV数据可播放")
            return

        # 重置播放位置
        self.csv_data_index = 0

        # 设置标准直径
        self.set_standard_diameter_for_csv()

        # 开始播放
        self.is_csv_playing = True
        if self.csv_timer:
            self.csv_timer.stop()

        self.csv_timer = QTimer()
        self.csv_timer.timeout.connect(self.update_csv_data_point)
        self.csv_timer.start(10)  # 10ms间隔，更流畅的播放速度

        # 更新按钮状态
        self.start_button.setText("实时采集中...")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        # 启动独立的内窥镜图像切换
        self.start_endoscope_auto_switching()

        print(f"🎬 开始实时播放CSV数据，共 {len(self.csv_data)} 个数据点")

    def stop_realtime_csv_monitoring(self):
        """停止实时CSV监控"""
        if self.csv_monitor:
            try:
                self.csv_monitor.stop()
                self.csv_monitor.join()
                self.csv_monitor = None
                print("⏹️ 文件监控已停止")
            except Exception as e:
                print(f"❌ 停止文件监控失败: {e}")

        if self.csv_file_monitor_timer:
            self.csv_file_monitor_timer.stop()
            self.csv_file_monitor_timer = None
            print("⏹️ 轮询监控已停止")

        self.is_realtime_monitoring = False

    def start_endoscope_auto_switching(self):
        """启动独立的内窥镜图像自动切换"""
        print("🖼️ 启动独立的内窥镜图像自动切换")
        
        # 检查是否有图像数据
        if not self.current_images:
            # 尝试加载当前孔位的图像
            if self.current_hole_id:
                self.load_endoscope_images_for_hole(self.current_hole_id)
            else:
                # 如果没有当前孔位，尝试加载默认孔位的图像
                default_hole = "R0_C0"  # 可以根据需要修改默认孔位
                self.load_endoscope_images_for_hole(default_hole)
        
        if not self.current_images:
            print("⚠️ 没有可用的内窥镜图像")
            return
        
        # 停止旧的定时器（如果存在）
        if self.endoscope_image_timer:
            self.endoscope_image_timer.stop()
        
        # 创建新的定时器
        self.endoscope_image_timer = QTimer()
        self.endoscope_image_timer.timeout.connect(self.switch_endoscope_image)
        self.endoscope_image_timer.start(self.endoscope_timer_interval)
        
        # 显示第一张图像
        self.current_image_index = 0
        self.display_endoscope_image(0)
        
        print(f"✅ 内窥镜图像自动切换已启动，间隔 {self.endoscope_timer_interval}ms")
    
    def stop_endoscope_auto_switching(self):
        """停止独立的内窥镜图像自动切换"""
        if self.endoscope_image_timer:
            self.endoscope_image_timer.stop()
            self.endoscope_image_timer = None
            print("⏹️ 内窥镜图像自动切换已停止")
    
    def switch_endoscope_image(self):
        """切换到下一张内窥镜图像"""
        if not self.current_images:
            return
        
        # 循环切换到下一张图像
        self.current_image_index = (self.current_image_index + 1) % len(self.current_images)
        self.display_endoscope_image(self.current_image_index)
        
        print(f"🔄 切换到内窥镜图像 {self.current_image_index + 1}/{len(self.current_images)}")











    # --- 新增：一套完整的自动化控制函数 ---
    @Slot()
    def start_automation_task(self):
        """【开始监测】按钮的槽函数，创建并启动后台工作线程。"""
        if self.automation_thread and self.automation_thread.isRunning():
            QMessageBox.warning(self, "提示", "自动化流程已在运行中，请先停止。")
            return

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.start_button.setText("监测中...")
        self.log_text_edit.clear()
        self.clear_data()  # 开始前清空图表

        # 准备图表用于实时绘制
        self.setup_chart_for_data()

        # --- 修改：启动CSV文件监控（仅用于归档，不用于绘制） ---
        if os.path.exists(self.csv_output_folder):
            self.csv_watcher.addPath(self.csv_output_folder)
            self.log_text_edit.append(f"🟢 **CSV归档监控已启动**: 监控文件夹 {self.csv_output_folder}")
            self.log_text_edit.append(f"📊 **实时绘制模式**: 等待LEConfocalDemo程序输出数据...")
        else:
            self.log_text_edit.append(f"🔴 **错误**: 监控文件夹不存在: {self.csv_output_folder}")
        # ------------------------------------

        self.automation_thread = QThread()
        self.automation_worker = AutomationWorker(
            acquisition_path=self.acquisition_program_path,
            launcher_path=self.remote_launcher_path
        )
        self.automation_worker.moveToThread(self.automation_thread)

        # 连接信号与槽
        self.automation_thread.started.connect(self.automation_worker.run_automation)
        self.automation_worker.task_finished.connect(self.on_automation_finished)
        self.automation_worker.progress_updated.connect(self.update_log_view)
        # 新增：连接实时数据信号
        self.automation_worker.realtime_data_received.connect(self.on_realtime_data_received)

        self.automation_thread.finished.connect(self.automation_thread.deleteLater)

        self.automation_thread.start()

    @Slot(str)
    def on_directory_changed(self, path):
        """当被监控的目录发生变化时，此函数被调用 - 仅用于归档处理"""
        try:
            # 检查我们期待的那个CSV文件是否已经存在
            if os.path.exists(self.output_csv_path):
                self.log_text_edit.append(f"✅ **检测到CSV文件生成!** 开始归档处理...")

                # 关键：立刻停止监控，防止因为文件内容写入等后续变化导致重复触发
                self.csv_watcher.removePath(path)

                # 直接启动归档处理，不再触发绘制
                QTimer.singleShot(200, self.start_archive_only)

        except Exception as e:
            self.log_text_edit.append(f"🔴 **监控回调函数出错**: {e}")

    def start_archive_only(self):
        """仅启动归档处理，不进行数据绘制"""
        try:
            # 启动后台归档线程
            self.log_text_edit.append("📦 开始后台归档任务...")
            self.archive_thread = QThread()
            self.archive_worker = ArchiveWorker(
                source_path=self.output_csv_path,
                base_archive_path=self.archive_base_path
            )
            self.archive_worker.moveToThread(self.archive_thread)

            # 连接信号
            self.archive_thread.started.connect(self.archive_worker.run_archive)
            self.archive_worker.log_message.connect(self.update_log_view)
            self.archive_worker.finished.connect(self.on_archive_finished)

            self.archive_thread.start()

        except Exception as e:
            self.log_text_edit.append(f"❌ 启动归档失败: {e}")

    def _get_latest_hole_id(self):
        """获取最新的孔位ID（基于已存在的文件夹）"""
        try:
            import re
            
            if not os.path.exists(self.archive_base_path):
                return None
            
            dir_pattern = re.compile(r'^R(\d{3})C(\d{3})$')
            max_num = 0
            latest_hole = None
            
            for item in os.listdir(self.archive_base_path):
                if os.path.isdir(os.path.join(self.archive_base_path, item)):
                    match = dir_pattern.match(item)
                    if match:
                        num = int(match.group(2))
                        if num > max_num:
                            max_num = num
                            latest_hole = item
            
            return latest_hole
        except Exception as e:
            print(f"❌ 获取最新孔位ID失败: {e}")
            return None
    
    def start_playback_from_new_file(self):
        """从新生成的文件加载并开始回放，同时启动后台归档"""
        if self.load_realtime_csv_data(self.output_csv_path):
            self.setup_chart_for_data()
            
            # 在测量模式下，设置孔位并加载内窥镜图片
            # 优先使用R0_C0（测量模式专用）
            measurement_hole = "R0_C0"
            if measurement_hole in self.hole_to_image_map:
                self.set_current_hole(measurement_hole)
                self.load_endoscope_images_for_hole(measurement_hole)
                self.log_text_edit.append(f"📸 已加载测量模式的内窥镜图像")
            else:
                # 如果R0_C0不存在，尝试使用最新的孔位文件夹
                latest_hole = self._get_latest_hole_id()
                if latest_hole and latest_hole in self.hole_to_image_map:
                    self.set_current_hole(latest_hole)
                    self.load_endoscope_images_for_hole(latest_hole)
                    self.log_text_edit.append(f"📸 已加载孔位 {latest_hole} 的内窥镜图像")
                else:
                    # 如果没有找到，使用第一个可用的孔位
                    if self.hole_to_image_map:
                        first_hole = list(self.hole_to_image_map.keys())[0]
                        self.set_current_hole(first_hole)
                        self.load_endoscope_images_for_hole(first_hole)
                        self.log_text_edit.append(f"📸 使用默认孔位 {first_hole} 的内窥镜图像")
            
            self.start_csv_data_import(auto_play=True)

            # --- 新增：启动后台归档线程 ---
            self.log_text_edit.append("---") # 分隔符
            self.archive_thread = QThread()
            self.archive_worker = ArchiveWorker(
                source_path=self.output_csv_path,
                base_archive_path=self.archive_base_path
            )
            self.archive_worker.moveToThread(self.archive_thread)

            # 连接信号
            self.archive_thread.started.connect(self.archive_worker.run_archive)
            self.archive_worker.log_message.connect(self.update_log_view)
            self.archive_worker.finished.connect(self.on_archive_finished)

            self.archive_thread.start()
            # -----------------------------

        else:
            error_msg = f"错误：加载或解析新生成的数据文件失败: {self.output_csv_path}"
            self.log_text_edit.append(f"❌ {error_msg}")
            QMessageBox.critical(self, "加载失败", error_msg)

    @Slot()
    def stop_automation_task(self):
        """【停止监测】按钮的槽函数，请求后台线程停止。"""
        # --- 新增：停止文件监控 ---
        if self.csv_watcher.directories():
            self.csv_watcher.removePaths(self.csv_watcher.directories())
        # ---------------------------
        self.log_text_edit.append("--- 用户请求停止 ---")
        if self.automation_worker:
            self.automation_worker.stop()  # 调用worker的停止方法
        
        # 3. --- 新增：检查并停止曲线绘制 ---
        if self.is_csv_playing:
            self.stop_csv_data_import()
        # ------------------------------------
        
        # 停止内窥镜图像自动切换
        self.stop_endoscope_auto_switching()

        # 按钮状态将在 on_automation_finished 中恢复

    @Slot(str)
    def update_log_view(self, message):
        """接收后台日志并显示在日志窗口中。"""
        self.log_text_edit.append(message)
        self.log_text_edit.verticalScrollBar().setValue(self.log_text_edit.verticalScrollBar().maximum())  # 自动滚到最下方

    @Slot(str)
    def on_archive_finished(self, final_message):
        """后台归档任务完成后的处理"""
        self.update_log_view(final_message) # 在日志窗口显示最终结果
        self.update_log_view("---")

        # 清理线程
        if self.archive_thread:
            self.archive_thread.quit()
            self.archive_thread.wait(1000) # 等待1秒确保线程退出
            self.archive_thread = None
            self.archive_worker = None

    @Slot(bool, str)
    def on_automation_finished(self, success, message):
        """自动化流程结束后，恢复UI状态。"""
        self.log_text_edit.append(f"\n--- 后台流程完全结束 ---\n{message}")

        # --- 新增：确保文件监控已停止 ---
        if self.csv_watcher.directories():
            self.csv_watcher.removePaths(self.csv_watcher.directories())
        # ---------------------------

        # 注意：此时UI可能已经在播放曲线了，所以这里主要是恢复按钮和清理线程
        # 如果播放还未结束，我们甚至可以不操作按钮，让它在播放结束后再恢复
        if not hasattr(self, 'is_csv_playing') or not self.is_csv_playing:
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.start_button.setText("▶️ 开始监测")

        if not success:
            # 如果自动化流程本身失败了，还是弹出错误提示
            QMessageBox.warning(self, "任务中断", message)
            # 恢复按钮状态
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.start_button.setText("▶️ 开始监测")

        # 清理线程
        if self.automation_thread:
            self.automation_thread.quit()
            self.automation_thread.wait(2000)
            self.automation_thread = None
            self.automation_worker = None

    # display_final_result 函数已删除，因为不再需要


if __name__ == "__main__":
    """测试代码"""
    import sys
    from PySide6.QtWidgets import QApplication
    from worker_thread import WorkerThread
    
    app = QApplication(sys.argv)
    
    # 创建图表组件
    chart = RealtimeChart()
    chart.show()
    
    # 创建数据源
    worker = WorkerThread()
    worker.data_updated.connect(chart.update_data)
    worker.status_updated.connect(chart.update_status)
    
    # 注意：按钮已经连接到CSV数据导入功能
    # 如果需要使用worker线程，请注释掉CSV功能的按钮连接
    # chart.start_button.clicked.connect(lambda: worker.start_measurement("TEST_001"))
    # chart.stop_button.clicked.connect(worker.stop_measurement)
    
    sys.exit(app.exec())
