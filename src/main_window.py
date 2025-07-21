"""
合并后的主窗口模块
集成所有功能组件的完整主界面
包含：选项卡布局 + AIDCIS2检测功能 + 搜索功能 + 模拟进度 + 所有原有功能
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTabWidget, QMenuBar, QStatusBar, QMessageBox, QFileDialog,
    QPushButton, QLabel, QLineEdit, QComboBox, QGroupBox,
    QProgressBar, QTextEdit, QSplitter, QScrollArea, QFrame,
    QCompleter, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, Signal, QStringListModel
from PySide6.QtGui import QAction, QFont, QPalette, QColor

# 导入所有功能模块
from modules.realtime_chart import RealtimeChart
from modules.worker_thread import WorkerThread
from modules.unified_history_viewer import UnifiedHistoryViewer
from modules.report_output_interface import ReportOutputInterface

# 导入AIDCIS2核心组件
from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus
from aidcis2.models.status_manager import StatusManager
from aidcis2.dxf_parser import DXFParser
from aidcis2.data_adapter import DataAdapter
from aidcis2.graphics.graphics_view import OptimizedGraphicsView


class MainWindow(QMainWindow):
    """
    合并后的主窗口类
    整合选项卡布局 + AIDCIS2检测功能 + 搜索功能 + 所有原有功能
    """
    
    # 导航信号 - 用于内部组件通信
    navigate_to_realtime = Signal(str)  # 导航到实时监控，传递孔位ID
    navigate_to_history = Signal(str)   # 导航到历史数据，传递孔位ID
    navigate_to_report = Signal(str)    # 导航到报告输出，传递工件ID
    status_updated = Signal(str, str)   # 孔位ID, 新状态
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # 原主窗口的属性
        self.worker_thread = None
        self.status_sync_timer = None
        self.last_aidcis2_status = ""
        
        # AIDCIS2核心组件
        self.dxf_parser = DXFParser()
        self.status_manager = StatusManager()
        self.data_adapter = DataAdapter()
        
        # 数据
        self.hole_collection: Optional[HoleCollection] = None
        self.selected_hole: Optional[HoleData] = None
        
        # 检测控制
        self.detection_running = False
        self.detection_paused = False
        self.detection_holes = []
        self.detection_timer = QTimer()
        self.detection_timer.timeout.connect(self._process_detection_step)
        
        # 模拟进度控制
        self.simulation_running = False
        self.simulation_timer = QTimer()
        self.simulation_timer.timeout.connect(self._update_simulation_progress)
        self.pending_holes = []
        self.simulation_hole_index = 0

        # 检测时间相关
        self.detection_start_time = None
        self.detection_elapsed_seconds = 0
        self.detection_time_timer = QTimer()
        self.detection_time_timer.timeout.connect(self._update_detection_time)
        self.detection_time_timer.start(1000)  # 每秒更新一次
        
        # 初始化界面
        self.setup_ui()
        self.setup_menu()
        self.setup_status_bar()
        self.setup_connections()
        self.setup_search_completer()
        
        # 定时器用于状态更新
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status_display)
        self.update_timer.start(1000)  # 每秒更新一次
        
        self.logger.info("合并主界面初始化完成")
        
    def setup_ui(self):
        """设置主界面布局"""
        self.setWindowTitle("上位机软件 - 管孔检测系统")

        # 获取屏幕尺寸并设置合适的初始窗口大小
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()

        # 设置窗口大小为屏幕的80%，但不超过1400x900
        window_width = min(int(screen_geometry.width() * 0.8), 1400)
        window_height = min(int(screen_geometry.height() * 0.8), 900)

        # 居中显示
        x = (screen_geometry.width() - window_width) // 2
        y = (screen_geometry.height() - window_height) // 2

        self.setGeometry(x, y, window_width, window_height)
        self.setMinimumSize(1200, 800)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建选项卡控件
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # 主检测视图选项卡（集成AIDCIS2功能）
        self.main_detection_widget = self.create_main_detection_view()
        self.tab_widget.addTab(self.main_detection_widget, "主检测视图")

        # 添加实时监控选项卡（二级页面）
        self.realtime_tab = RealtimeChart()
        self.tab_widget.addTab(self.realtime_tab, "实时监控")

        # 添加统一历史数据选项卡（三级页面，合并3.1和3.2）
        self.history_tab = UnifiedHistoryViewer()
        self.tab_widget.addTab(self.history_tab, "历史数据")

        # 添加报告输出选项卡（四级页面）
        self.report_tab = ReportOutputInterface()
        self.tab_widget.addTab(self.report_tab, "报告输出")

        # --- 新增代码：将报告界面的状态信号连接到主窗口状态栏 ---
        self.report_tab.status_updated.connect(self.statusBar().showMessage)

        # 设置默认选项卡为主检测视图
        self.tab_widget.setCurrentIndex(0)
        
    def create_main_detection_view(self) -> QWidget:
        """创建主检测视图（集成AIDCIS2功能）"""
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # 工具栏
        toolbar = self.create_toolbar()
        main_layout.addWidget(toolbar)
        
        # 主内容区域 - 三栏布局
        content_splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：信息面板
        left_panel = self.create_left_info_panel()
        content_splitter.addWidget(left_panel)
        
        # 中间：可视化面板
        center_panel = self.create_center_visualization_panel()
        content_splitter.addWidget(center_panel)
        
        # 右侧：操作面板
        right_panel = self.create_right_operations_panel()
        content_splitter.addWidget(right_panel)
        
        # 设置分割器比例，给左侧面板更多空间
        content_splitter.setStretchFactor(0, 1)  # 左侧信息面板
        content_splitter.setStretchFactor(1, 3)  # 中间可视化面板（增加比例）
        content_splitter.setStretchFactor(2, 1)  # 右侧操作面板

        # 设置最小宽度确保面板稳定性
        content_splitter.setSizes([380, 800, 350])  # 设置初始大小
        
        main_layout.addWidget(content_splitter)
        
        return main_widget
    
    def create_toolbar(self) -> QWidget:
        """创建工具栏"""
        toolbar = QFrame()
        toolbar.setFrameStyle(QFrame.StyledPanel)
        toolbar.setMaximumHeight(70)  # 增加工具栏高度以适应更大字体

        layout = QHBoxLayout(toolbar)

        # 设置工具栏字体
        from PySide6.QtGui import QFont
        toolbar_font = QFont()
        toolbar_font.setPointSize(11)

        # 文件操作按钮
        self.load_dxf_btn = QPushButton("加载DXF文件")
        self.load_dxf_btn.setMinimumSize(140, 45)  # 增加按钮大小
        self.load_dxf_btn.setFont(toolbar_font)
        layout.addWidget(self.load_dxf_btn)

        layout.addSpacing(20)

        # 搜索框和搜索按钮
        search_label = QLabel("搜索:")
        search_label.setFont(toolbar_font)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入孔位ID...")
        self.search_input.setMinimumWidth(220)  # 增加搜索框宽度
        self.search_input.setMinimumHeight(35)  # 增加搜索框高度
        self.search_input.setFont(toolbar_font)

        # 搜索按钮
        self.search_btn = QPushButton("搜索")
        self.search_btn.setMinimumSize(70, 35)  # 设置最小尺寸而不是最大宽度
        self.search_btn.setFont(toolbar_font)

        layout.addWidget(search_label)
        layout.addWidget(self.search_input)
        layout.addWidget(self.search_btn)

        layout.addSpacing(20)

        # 视图控制
        view_label = QLabel("视图:")
        view_label.setFont(toolbar_font)

        self.view_combo = QComboBox()
        self.view_combo.addItems(["全部孔位", "待检孔位", "合格孔位", "异常孔位"])
        self.view_combo.setMinimumHeight(35)  # 增加下拉框高度
        self.view_combo.setFont(toolbar_font)

        layout.addWidget(view_label)
        layout.addWidget(self.view_combo)

        layout.addStretch()

        return toolbar

    def create_left_info_panel(self) -> QWidget:
        """创建左侧信息面板"""
        panel = QScrollArea()
        panel.setWidgetResizable(True)
        panel.setMinimumWidth(380)  # 设置最小宽度确保稳定性
        panel.setMaximumWidth(380)  # 增加宽度以适应更大字体

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(8)  # 减少组件间距以节省空间

        # 设置全局字体
        from PySide6.QtGui import QFont
        panel_font = QFont()
        panel_font.setPointSize(11)  # 设置字体大小为11pt
        content_widget.setFont(panel_font)

        # 1. 检测进度组（放在最上方）
        progress_group = QGroupBox("检测进度")
        progress_group_font = QFont()
        progress_group_font.setPointSize(11)  # 稍微减小组标题字体
        progress_group_font.setBold(True)
        progress_group.setFont(progress_group_font)
        progress_layout = QVBoxLayout(progress_group)
        progress_layout.setSpacing(6)  # 减少内部间距
        progress_layout.setContentsMargins(8, 8, 8, 8)  # 减少边距

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumHeight(22)  # 稍微减小进度条高度
        progress_layout.addWidget(self.progress_bar)

        # 新增的统计信息 - 使用网格布局，更紧凑
        stats_grid_layout = QGridLayout()
        stats_grid_layout.setSpacing(4)  # 减少网格间距
        stats_grid_layout.setContentsMargins(0, 0, 0, 0)

        # 已完成和待完成统计
        self.completed_count_label = QLabel("已完成: 0")
        self.pending_count_label = QLabel("待完成: 0")

        # 设置标签字体，稍微减小
        label_font = QFont()
        label_font.setPointSize(10)  # 减小字体以节省空间
        self.completed_count_label.setFont(label_font)
        self.pending_count_label.setFont(label_font)

        stats_grid_layout.addWidget(self.completed_count_label, 0, 0)
        stats_grid_layout.addWidget(self.pending_count_label, 0, 1)

        # 检测时间和预计用时
        self.detection_time_label = QLabel("检测时间: 00:00:00")
        self.estimated_time_label = QLabel("预计用时: 00:00:00")

        self.detection_time_label.setFont(label_font)
        self.estimated_time_label.setFont(label_font)

        stats_grid_layout.addWidget(self.detection_time_label, 1, 0)
        stats_grid_layout.addWidget(self.estimated_time_label, 1, 1)

        progress_layout.addLayout(stats_grid_layout)

        # 原有的完成率和合格率 - 使用水平布局节省空间
        rate_layout = QHBoxLayout()
        rate_layout.setSpacing(10)

        self.completion_rate_label = QLabel("完成率: 0%")
        self.qualification_rate_label = QLabel("合格率: 0%")

        self.completion_rate_label.setFont(label_font)
        self.qualification_rate_label.setFont(label_font)

        rate_layout.addWidget(self.completion_rate_label)
        rate_layout.addWidget(self.qualification_rate_label)
        rate_layout.addStretch()

        progress_layout.addLayout(rate_layout)

        layout.addWidget(progress_group)

        # 2. 状态统计组
        stats_group = QGroupBox("状态统计")
        stats_group.setFont(progress_group_font)  # 使用相同的组标题字体
        stats_layout = QGridLayout(stats_group)
        stats_layout.setSpacing(4)  # 减少间距
        stats_layout.setContentsMargins(8, 8, 8, 8)  # 减少边距

        self.pending_status_count_label = QLabel("待检: 0")
        self.qualified_count_label = QLabel("合格: 0")
        self.defective_count_label = QLabel("异常: 0")
        self.blind_count_label = QLabel("盲孔: 0")
        self.tie_rod_count_label = QLabel("拉杆孔: 0")
        self.processing_count_label = QLabel("检测中: 0")

        # 设置状态统计标签字体，使用更小的字体
        status_font = QFont()
        status_font.setPointSize(10)  # 减小字体
        status_labels = [
            self.pending_status_count_label, self.qualified_count_label,
            self.defective_count_label, self.blind_count_label,
            self.tie_rod_count_label, self.processing_count_label
        ]
        for label in status_labels:
            label.setFont(status_font)

        stats_layout.addWidget(self.pending_status_count_label, 0, 0)
        stats_layout.addWidget(self.qualified_count_label, 0, 1)
        stats_layout.addWidget(self.defective_count_label, 1, 0)
        stats_layout.addWidget(self.blind_count_label, 1, 1)
        stats_layout.addWidget(self.tie_rod_count_label, 2, 0)
        stats_layout.addWidget(self.processing_count_label, 2, 1)

        layout.addWidget(stats_group)

        # 3. 孔位信息组
        hole_info_group = QGroupBox("孔位信息")
        hole_info_group.setFont(progress_group_font)  # 使用相同的组标题字体
        hole_info_layout = QGridLayout(hole_info_group)
        hole_info_layout.setSpacing(4)  # 减少间距
        hole_info_layout.setContentsMargins(8, 8, 8, 8)  # 减少边距

        self.selected_hole_id_label = QLabel("未选择")
        self.selected_hole_position_label = QLabel("-")
        self.selected_hole_status_label = QLabel("-")
        self.selected_hole_radius_label = QLabel("-")

        # 创建描述标签并设置字体
        hole_id_desc_label = QLabel("孔位ID:")
        position_desc_label = QLabel("位置:")
        status_desc_label = QLabel("状态:")
        radius_desc_label = QLabel("半径:")

        # 设置所有孔位信息标签的字体，使用更小的字体
        hole_info_font = QFont()
        hole_info_font.setPointSize(10)  # 减小字体
        hole_info_labels = [
            hole_id_desc_label, position_desc_label, status_desc_label, radius_desc_label,
            self.selected_hole_id_label, self.selected_hole_position_label,
            self.selected_hole_status_label, self.selected_hole_radius_label
        ]
        for label in hole_info_labels:
            label.setFont(hole_info_font)

        hole_info_layout.addWidget(hole_id_desc_label, 0, 0)
        hole_info_layout.addWidget(self.selected_hole_id_label, 0, 1)
        hole_info_layout.addWidget(position_desc_label, 1, 0)
        hole_info_layout.addWidget(self.selected_hole_position_label, 1, 1)
        hole_info_layout.addWidget(status_desc_label, 2, 0)
        hole_info_layout.addWidget(self.selected_hole_status_label, 2, 1)
        hole_info_layout.addWidget(radius_desc_label, 3, 0)
        hole_info_layout.addWidget(self.selected_hole_radius_label, 3, 1)

        layout.addWidget(hole_info_group)

        # 4. 文件信息组（放在最底下）
        file_group = QGroupBox("文件信息")
        file_group.setFont(progress_group_font)  # 使用相同的组标题字体
        file_layout = QGridLayout(file_group)
        file_layout.setSpacing(4)  # 减少间距
        file_layout.setContentsMargins(8, 8, 8, 8)  # 减少边距

        self.file_name_label = QLabel("未加载文件")
        self.file_path_label = QLabel("路径: -")
        self.file_size_label = QLabel("大小: -")
        self.load_time_label = QLabel("加载时间: -")
        self.hole_count_label = QLabel("孔位数量: 0")

        # 创建描述标签并设置字体
        file_name_desc_label = QLabel("文件名:")
        file_path_desc_label = QLabel("路径:")
        file_size_desc_label = QLabel("大小:")
        load_time_desc_label = QLabel("加载时间:")
        hole_count_desc_label = QLabel("孔位数量:")

        # 设置所有文件信息标签的字体，使用更小的字体
        file_info_font = QFont()
        file_info_font.setPointSize(9)  # 进一步减小字体以节省空间
        file_info_labels = [
            file_name_desc_label, file_path_desc_label, file_size_desc_label,
            load_time_desc_label, hole_count_desc_label,
            self.file_name_label, self.file_path_label, self.file_size_label,
            self.load_time_label, self.hole_count_label
        ]
        for label in file_info_labels:
            label.setFont(file_info_font)

        file_layout.addWidget(file_name_desc_label, 0, 0)
        file_layout.addWidget(self.file_name_label, 0, 1)
        file_layout.addWidget(file_path_desc_label, 1, 0)
        file_layout.addWidget(self.file_path_label, 1, 1)
        file_layout.addWidget(file_size_desc_label, 2, 0)
        file_layout.addWidget(self.file_size_label, 2, 1)
        file_layout.addWidget(load_time_desc_label, 3, 0)
        file_layout.addWidget(self.load_time_label, 3, 1)
        file_layout.addWidget(hole_count_desc_label, 4, 0)
        file_layout.addWidget(self.hole_count_label, 4, 1)

        layout.addWidget(file_group)

        layout.addStretch()

        panel.setWidget(content_widget)
        return panel

    def create_center_visualization_panel(self) -> QWidget:
        """创建中间可视化面板"""
        panel = QGroupBox("管孔检测视图")

        # 设置中间面板组标题字体
        from PySide6.QtGui import QFont
        center_panel_font = QFont()
        center_panel_font.setPointSize(12)
        center_panel_font.setBold(True)
        panel.setFont(center_panel_font)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(2, 2, 2, 2)

        # 状态图例
        legend_frame = self.create_status_legend()
        layout.addWidget(legend_frame)

        # 创建优化的图形视图
        self.graphics_view = OptimizedGraphicsView()
        self.graphics_view.setFrameStyle(QFrame.StyledPanel)

        # 连接图形视图信号
        self.graphics_view.hole_clicked.connect(self.on_hole_selected)
        self.graphics_view.hole_hovered.connect(self.on_hole_hovered)
        self.graphics_view.view_changed.connect(self.on_view_changed)

        layout.addWidget(self.graphics_view)

        return panel

    def create_status_legend(self) -> QWidget:
        """创建状态图例"""
        legend_frame = QFrame()
        legend_frame.setFrameStyle(QFrame.StyledPanel)
        legend_frame.setMaximumHeight(50)  # 增加高度以适应更大字体

        layout = QHBoxLayout(legend_frame)
        layout.setContentsMargins(8, 8, 8, 8)  # 增加边距

        # 从图形组件获取状态颜色
        try:
            from aidcis2.graphics.hole_graphics_item import HoleGraphicsItem
            status_colors = HoleGraphicsItem.STATUS_COLORS
        except:
            # 默认颜色映射
            status_colors = {
                HoleStatus.PENDING: "#CCCCCC",
                HoleStatus.QUALIFIED: "#4CAF50",
                HoleStatus.DEFECTIVE: "#F44336",
                HoleStatus.BLIND: "#FF9800",
                HoleStatus.TIE_ROD: "#9C27B0",
                HoleStatus.PROCESSING: "#2196F3"
            }

        status_names = {
            HoleStatus.PENDING: "待检",
            HoleStatus.QUALIFIED: "合格",
            HoleStatus.DEFECTIVE: "异常",
            HoleStatus.BLIND: "盲孔",
            HoleStatus.TIE_ROD: "拉杆孔",
            HoleStatus.PROCESSING: "检测中"
        }

        # 设置图例字体
        from PySide6.QtGui import QFont
        legend_font = QFont()
        legend_font.setPointSize(11)  # 增加字体大小

        for status, color in status_colors.items():
            # 颜色指示器
            color_label = QLabel()
            color_label.setFixedSize(16, 16)  # 增加颜色指示器大小
            color_label.setStyleSheet(f"background-color: {color}; border: 1px solid #000;")

            # 状态文本
            text_label = QLabel(status_names.get(status, status.value))
            text_label.setFont(legend_font)  # 使用更大的字体

            layout.addWidget(color_label)
            layout.addWidget(text_label)
            layout.addSpacing(15)  # 增加间距

        layout.addStretch()
        return legend_frame

    def create_right_operations_panel(self) -> QWidget:
        """创建右侧操作面板"""
        panel = QScrollArea()
        panel.setWidgetResizable(True)
        panel.setMaximumWidth(350)  # 增加宽度以适应更大字体

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)

        # 设置右侧面板字体
        from PySide6.QtGui import QFont
        panel_font = QFont()
        panel_font.setPointSize(11)

        group_title_font = QFont()
        group_title_font.setPointSize(12)
        group_title_font.setBold(True)

        button_font = QFont()
        button_font.setPointSize(11)

        # 检测控制组
        detection_group = QGroupBox("检测控制")
        detection_group.setFont(group_title_font)
        detection_layout = QVBoxLayout(detection_group)

        self.start_detection_btn = QPushButton("开始检测")
        self.start_detection_btn.setMinimumHeight(45)  # 增加按钮高度
        self.start_detection_btn.setFont(button_font)
        self.start_detection_btn.setEnabled(False)

        self.pause_detection_btn = QPushButton("暂停检测")
        self.pause_detection_btn.setMinimumHeight(45)
        self.pause_detection_btn.setFont(button_font)
        self.pause_detection_btn.setEnabled(False)

        self.stop_detection_btn = QPushButton("停止检测")
        self.stop_detection_btn.setMinimumHeight(45)
        self.stop_detection_btn.setFont(button_font)
        self.stop_detection_btn.setEnabled(False)

        detection_layout.addWidget(self.start_detection_btn)
        detection_layout.addWidget(self.pause_detection_btn)
        detection_layout.addWidget(self.stop_detection_btn)

        layout.addWidget(detection_group)

        # 模拟功能组
        simulation_group = QGroupBox("模拟功能")
        simulation_group.setFont(group_title_font)
        simulation_layout = QVBoxLayout(simulation_group)

        self.simulate_btn = QPushButton("使用模拟进度")
        self.simulate_btn.setMinimumHeight(45)
        self.simulate_btn.setFont(button_font)
        self.simulate_btn.setEnabled(False)

        simulation_layout.addWidget(self.simulate_btn)

        layout.addWidget(simulation_group)

        # 视图控制组
        view_control_group = QGroupBox("视图控制")
        view_control_group.setFont(group_title_font)
        view_control_layout = QGridLayout(view_control_group)

        self.zoom_in_btn = QPushButton("放大")
        self.zoom_out_btn = QPushButton("缩小")
        self.fit_view_btn = QPushButton("适应窗口")
        self.reset_view_btn = QPushButton("重置视图")

        # 设置视图控制按钮字体和高度
        view_control_buttons = [self.zoom_in_btn, self.zoom_out_btn, self.fit_view_btn, self.reset_view_btn]
        for btn in view_control_buttons:
            btn.setFont(button_font)
            btn.setMinimumHeight(40)
            btn.setEnabled(False)

        view_control_layout.addWidget(self.zoom_in_btn, 0, 0)
        view_control_layout.addWidget(self.zoom_out_btn, 0, 1)
        view_control_layout.addWidget(self.fit_view_btn, 1, 0)
        view_control_layout.addWidget(self.reset_view_btn, 1, 1)

        layout.addWidget(view_control_group)

        # 孔位操作组
        hole_ops_group = QGroupBox("孔位操作")
        hole_ops_group.setFont(group_title_font)
        hole_ops_layout = QVBoxLayout(hole_ops_group)

        self.goto_realtime_btn = QPushButton("实时监控")
        self.goto_realtime_btn.setMinimumHeight(40)  # 增加按钮高度
        self.goto_realtime_btn.setFont(button_font)
        self.goto_realtime_btn.setEnabled(False)

        self.goto_history_btn = QPushButton("历史数据")
        self.goto_history_btn.setMinimumHeight(40)
        self.goto_history_btn.setFont(button_font)
        self.goto_history_btn.setEnabled(False)

        self.mark_defective_btn = QPushButton("标记异常")
        self.mark_defective_btn.setMinimumHeight(40)
        self.mark_defective_btn.setFont(button_font)
        self.mark_defective_btn.setEnabled(False)

        self.goto_report_btn = QPushButton("生成报告")
        self.goto_report_btn.setMinimumHeight(40)
        self.goto_report_btn.setFont(button_font)
        # 使用主题管理器的警告色样式
        self.goto_report_btn.setObjectName("WarningButton")
        self.goto_report_btn.setEnabled(True)  # 报告生成总是可用

        hole_ops_layout.addWidget(self.goto_realtime_btn)
        hole_ops_layout.addWidget(self.goto_history_btn)
        hole_ops_layout.addWidget(self.mark_defective_btn)
        hole_ops_layout.addWidget(self.goto_report_btn)

        layout.addWidget(hole_ops_group)

        # 操作日志组
        log_group = QGroupBox("操作日志")
        log_group.setFont(group_title_font)
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        self.log_text.setFont(panel_font)  # 设置日志文本字体

        log_layout.addWidget(self.log_text)

        layout.addWidget(log_group)

        layout.addStretch()

        panel.setWidget(content_widget)
        return panel

    def setup_menu(self):
        """设置菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件")

        open_action = QAction("打开DXF文件", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.load_dxf_file)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 工具菜单
        tools_menu = menubar.addMenu("工具")

        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助")

        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_status_bar(self):
        """设置状态栏"""
        status_bar = self.statusBar()

        # 状态标签
        self.status_label = QLabel("就绪")
        status_bar.addWidget(self.status_label)

        # 连接状态标签
        self.connection_label = QLabel("系统正常")
        status_bar.addPermanentWidget(self.connection_label)

        # 时间标签
        self.time_label = QLabel()
        status_bar.addPermanentWidget(self.time_label)

        # 更新时间
        timer = QTimer(self)
        timer.timeout.connect(self.update_time)
        timer.start(1000)
        self.update_time()

    def update_time(self):
        """更新时间显示"""
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(current_time)

    def _update_detection_time(self):
        """更新检测时间显示"""
        if self.detection_running and self.detection_start_time:
            from datetime import datetime
            current_time = datetime.now()
            elapsed = current_time - self.detection_start_time
            self.detection_elapsed_seconds = int(elapsed.total_seconds())

        # 格式化时间显示
        hours = self.detection_elapsed_seconds // 3600
        minutes = (self.detection_elapsed_seconds % 3600) // 60
        seconds = self.detection_elapsed_seconds % 60
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        self.detection_time_label.setText(f"检测时间: {time_str}")

        # 计算预计用时
        self._update_estimated_time()

    def _update_estimated_time(self):
        """更新预计用时"""
        if not self.hole_collection or self.detection_elapsed_seconds == 0:
            self.estimated_time_label.setText("预计用时: 00:00:00")
            return

        try:
            total_holes = len(self.hole_collection)
            completed_holes = self._get_completed_holes_count()

            if completed_holes > 0:
                # 基于已完成的孔位计算平均时间
                avg_time_per_hole = self.detection_elapsed_seconds / completed_holes
                remaining_holes = total_holes - completed_holes
                estimated_remaining_seconds = int(avg_time_per_hole * remaining_holes)

                hours = estimated_remaining_seconds // 3600
                minutes = (estimated_remaining_seconds % 3600) // 60
                seconds = estimated_remaining_seconds % 60
                time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

                self.estimated_time_label.setText(f"预计用时: {time_str}")
            else:
                self.estimated_time_label.setText("预计用时: 计算中...")
        except Exception:
            self.estimated_time_label.setText("预计用时: 00:00:00")

    def _get_completed_holes_count(self):
        """获取已完成检测的孔位数量"""
        if not self.hole_collection:
            return 0

        from aidcis2.models.hole_data import HoleStatus
        completed_count = 0
        for hole in self.hole_collection.holes.values():
            if hole.status in [HoleStatus.QUALIFIED, HoleStatus.DEFECTIVE, HoleStatus.BLIND, HoleStatus.TIE_ROD]:
                completed_count += 1
        return completed_count

    def setup_connections(self):
        """设置信号槽连接"""
        # 工具栏连接
        self.load_dxf_btn.clicked.connect(self.load_dxf_file)
        self.search_btn.clicked.connect(self.perform_search)
        self.search_input.returnPressed.connect(self.perform_search)
        self.view_combo.currentTextChanged.connect(self.filter_holes)

        # 检测控制连接
        self.start_detection_btn.clicked.connect(self.start_detection)
        self.pause_detection_btn.clicked.connect(self.pause_detection)
        self.stop_detection_btn.clicked.connect(self.stop_detection)

        # 模拟功能连接 - 使用蛇形双孔模拟
        self.simulate_btn.clicked.connect(self._start_snake_simulation)

        # 视图控制连接
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.fit_view_btn.clicked.connect(self.fit_view)
        self.reset_view_btn.clicked.connect(self.reset_view)

        # 孔位操作连接
        self.goto_realtime_btn.clicked.connect(self.goto_realtime)
        self.goto_history_btn.clicked.connect(self.goto_history)
        self.mark_defective_btn.clicked.connect(self.mark_defective)
        self.goto_report_btn.clicked.connect(self.goto_report)

        # 内部信号连接
        self.navigate_to_realtime.connect(self.navigate_to_realtime_from_main_view)
        self.navigate_to_history.connect(self.navigate_to_history_from_main_view)
        self.navigate_to_report.connect(self.navigate_to_report_from_main_view)

        # 添加测试DXF加载的快捷键 (Ctrl+T)
        from PySide6.QtGui import QShortcut, QKeySequence
        test_shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        test_shortcut.activated.connect(self.test_load_default_dxf)



    def setup_search_completer(self):
        """设置搜索自动补全器"""
        # 创建自动补全器
        self.completer = QCompleter()
        self.completer_model = QStringListModel()
        self.completer.setModel(self.completer_model)

        # 配置补全器
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setMaxVisibleItems(10)

        # 设置到搜索框
        self.search_input.setCompleter(self.completer)

        # 连接信号
        self.completer.activated.connect(self.on_completer_activated)

    def update_completer_data(self):
        """更新自动补全数据"""
        if not self.hole_collection:
            self.completer_model.setStringList([])
            return

        # 获取所有孔位ID
        hole_ids = [hole.hole_id for hole in self.hole_collection.holes.values()]
        hole_ids.sort()  # 按字母顺序排序

        # 更新补全数据
        self.completer_model.setStringList(hole_ids)
        self.logger.debug(f"更新自动补全数据: {len(hole_ids)} 个孔位")

    def on_completer_activated(self, text):
        """处理自动补全选择"""
        self.search_input.setText(text)
        self.perform_search()

    def perform_search(self):
        """执行搜索"""
        search_text = self.search_input.text().strip()
        if not search_text:
            # 清空搜索，显示所有孔位
            if hasattr(self, 'graphics_view'):
                self.graphics_view.clear_search_highlight()
            self.log_message("清空搜索")
            return

        if not self.hole_collection:
            self.log_message("没有加载孔位数据")
            return

        # 模糊搜索匹配的孔位
        search_text_upper = search_text.upper()
        matched_holes = []

        for hole in self.hole_collection.holes.values():
            if search_text_upper in hole.hole_id.upper():
                matched_holes.append(hole)

        if matched_holes:
            # 高亮匹配的孔位
            if hasattr(self, 'graphics_view'):
                self.graphics_view.highlight_holes(matched_holes, search_highlight=True)

            self.log_message(f"搜索 '{search_text}' 找到 {len(matched_holes)} 个孔位")

            # 如果只有一个结果，选中它并显示详细信息
            if len(matched_holes) == 1:
                self.selected_hole = matched_holes[0]
                self.log_message(f"🎯 设置选中孔位: {self.selected_hole.hole_id}")

                # 强制调用UI更新并验证
                self.log_message("🔄 强制调用孔位信息更新...")
                self.update_hole_info_display()

                # 验证UI更新结果
                self.log_message("🔍 验证UI更新结果:")
                self.log_message(f"  ID标签: '{self.selected_hole_id_label.text()}'")
                self.log_message(f"  位置标签: '{self.selected_hole_position_label.text()}'")
                self.log_message(f"  状态标签: '{self.selected_hole_status_label.text()}'")
                self.log_message(f"  半径标签: '{self.selected_hole_radius_label.text()}'")

                # 强制UI组件可见性和刷新
                self.selected_hole_id_label.setVisible(True)
                self.selected_hole_position_label.setVisible(True)
                self.selected_hole_status_label.setVisible(True)
                self.selected_hole_radius_label.setVisible(True)

                # 强制重绘所有标签
                self.selected_hole_id_label.repaint()
                self.selected_hole_position_label.repaint()
                self.selected_hole_status_label.repaint()
                self.selected_hole_radius_label.repaint()

                # 根据数据可用性启用按钮
                has_data = self.selected_hole.hole_id in ["H00001", "H00002"]
                self.goto_realtime_btn.setEnabled(has_data)
                self.goto_history_btn.setEnabled(has_data)
                self.mark_defective_btn.setEnabled(True)  # 标记异常总是可用

                # 更新按钮提示文本
                if has_data:
                    self.goto_realtime_btn.setToolTip(f"查看 {self.selected_hole.hole_id} 的实时监控数据")
                    self.goto_history_btn.setToolTip(f"查看 {self.selected_hole.hole_id} 的历史数据")
                else:
                    self.goto_realtime_btn.setToolTip(f"{self.selected_hole.hole_id} 无实时监控数据（仅支持 H00001, H00002）")
                    self.goto_history_btn.setToolTip(f"{self.selected_hole.hole_id} 无历史数据（仅支持 H00001, H00002）")

                self.mark_defective_btn.setToolTip(f"将 {self.selected_hole.hole_id} 标记为异常")

                # 显示详细的孔位信息和数据关联
                hole = self.selected_hole
                self.log_message(f"🔍 搜索选中孔位: {hole.hole_id}")
                self.log_message(f"  📍 位置: ({hole.center_x:.1f}, {hole.center_y:.1f})")
                self.log_message(f"  📊 状态: {hole.status.value}")
                self.log_message(f"  📏 半径: {hole.radius:.3f}mm")

                # 检查数据关联
                self._check_hole_data_availability(self.selected_hole.hole_id)

                # 强制刷新整个UI
                from PySide6.QtWidgets import QApplication
                QApplication.processEvents()
                self.log_message(f"🔄 搜索完成，UI已刷新: {self.selected_hole.hole_id}")

            # 如果有多个结果，选中第一个精确匹配的（如果有的话）
            elif len(matched_holes) > 1:
                # 查找精确匹配
                exact_match = None
                for hole in matched_holes:
                    if hole.hole_id.upper() == search_text_upper:
                        exact_match = hole
                        break

                if exact_match:
                    self.selected_hole = exact_match
                    self.log_message(f"🎯 精确匹配设置选中孔位: {self.selected_hole.hole_id}")

                    # 强制调用UI更新并验证
                    self.log_message("🔄 强制调用孔位信息更新(精确匹配)...")
                    self.update_hole_info_display()

                    # 验证UI更新结果
                    self.log_message("🔍 验证UI更新结果(精确匹配):")
                    self.log_message(f"  ID标签: '{self.selected_hole_id_label.text()}'")
                    self.log_message(f"  位置标签: '{self.selected_hole_position_label.text()}'")
                    self.log_message(f"  状态标签: '{self.selected_hole_status_label.text()}'")
                    self.log_message(f"  半径标签: '{self.selected_hole_radius_label.text()}'")

                    # 强制UI组件可见性和刷新
                    self.selected_hole_id_label.setVisible(True)
                    self.selected_hole_position_label.setVisible(True)
                    self.selected_hole_status_label.setVisible(True)
                    self.selected_hole_radius_label.setVisible(True)

                    # 强制重绘所有标签
                    self.selected_hole_id_label.repaint()
                    self.selected_hole_position_label.repaint()
                    self.selected_hole_status_label.repaint()
                    self.selected_hole_radius_label.repaint()

                    # 根据数据可用性启用按钮
                    has_data = exact_match.hole_id in ["H00001", "H00002"]
                    self.goto_realtime_btn.setEnabled(has_data)
                    self.goto_history_btn.setEnabled(has_data)
                    self.mark_defective_btn.setEnabled(True)  # 标记异常总是可用

                    # 更新按钮提示文本
                    if has_data:
                        self.goto_realtime_btn.setToolTip(f"查看 {exact_match.hole_id} 的实时监控数据")
                        self.goto_history_btn.setToolTip(f"查看 {exact_match.hole_id} 的历史数据")
                    else:
                        self.goto_realtime_btn.setToolTip(f"{exact_match.hole_id} 无实时监控数据（仅支持 H00001, H00002）")
                        self.goto_history_btn.setToolTip(f"{exact_match.hole_id} 无历史数据（仅支持 H00001, H00002）")

                    self.mark_defective_btn.setToolTip(f"将 {exact_match.hole_id} 标记为异常")

                    # 检查数据关联
                    self._check_hole_data_availability(exact_match.hole_id)

                    # 强制刷新整个UI
                    from PySide6.QtWidgets import QApplication
                    QApplication.processEvents()

                    self.log_message(f"精确匹配并选中: {exact_match.hole_id}，UI已刷新")
                else:
                    # 列出所有匹配的孔位
                    hole_ids = [hole.hole_id for hole in matched_holes]
                    self.log_message(f"匹配的孔位: {', '.join(hole_ids)}")
        else:
            self.log_message(f"搜索 '{search_text}' 没有找到匹配的孔位")

    def load_dxf_file(self):
        """加载DXF文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择DXF文件", "", "DXF文件 (*.dxf);;所有文件 (*)"
        )

        if not file_path:
            return

        try:
            self.status_label.setText("正在加载DXF文件...")
            self.log_message(f"开始加载DXF文件: {file_path}")

            # 使用DXF解析器加载文件
            self.hole_collection = self.dxf_parser.parse_file(file_path)

            if not self.hole_collection or len(self.hole_collection) == 0:
                error_msg = "DXF文件中未找到符合条件的孔位"
                self.log_message(f"警告: {error_msg}")
                QMessageBox.warning(self, "警告", error_msg)
                return

            self.log_message(f"DXF解析成功，找到 {len(self.hole_collection)} 个孔位")

            # 更新UI
            self.update_file_info(file_path)
            self.update_hole_display()
            self.update_status_display()
            self.update_completer_data()

            # 启用相关按钮
            self.start_detection_btn.setEnabled(True)
            self.simulate_btn.setEnabled(True)
            self.fit_view_btn.setEnabled(True)
            self.zoom_in_btn.setEnabled(True)
            self.zoom_out_btn.setEnabled(True)
            self.reset_view_btn.setEnabled(True)

            self.status_label.setText("DXF文件加载完成")
            self.log_message(f"✅ 成功加载 {len(self.hole_collection)} 个孔位")

            # 自动适应视图
            if hasattr(self.graphics_view, 'fit_in_view'):
                self.graphics_view.fit_in_view()
                self.log_message("已自动适应视图范围")

        except Exception as e:
            error_msg = f"加载DXF文件失败: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.log_message(f"❌ {error_msg}")
            QMessageBox.critical(self, "错误", error_msg)
            self.status_label.setText("加载失败")

    def test_load_default_dxf(self):
        """测试加载默认DXF文件 (快捷键: Ctrl+T)"""
        test_files = ["测试管板.dxf", "DXF Graph/东重管板.dxf"]

        for test_file in test_files:
            if Path(test_file).exists():
                self.log_message(f"🧪 测试加载DXF文件: {test_file}")
                try:
                    self.status_label.setText("测试加载DXF文件...")

                    # 解析DXF文件
                    self.hole_collection = self.dxf_parser.parse_file(test_file)

                    if self.hole_collection and len(self.hole_collection) > 0:
                        self.log_message(f"✅ 测试成功，找到 {len(self.hole_collection)} 个孔位")

                        # 更新UI
                        self.update_file_info(test_file)
                        self.update_hole_display()
                        self.update_status_display()
                        self.update_completer_data()

                        # 启用按钮
                        self.start_detection_btn.setEnabled(True)
                        self.simulate_btn.setEnabled(True)
                        self.fit_view_btn.setEnabled(True)
                        self.zoom_in_btn.setEnabled(True)
                        self.zoom_out_btn.setEnabled(True)
                        self.reset_view_btn.setEnabled(True)

                        self.status_label.setText("测试DXF加载完成")

                        # 自动适应视图
                        if hasattr(self.graphics_view, 'fit_in_view'):
                            self.graphics_view.fit_in_view()
                            self.log_message("已自动适应视图")

                        return
                    else:
                        self.log_message(f"⚠️ 测试文件 {test_file} 中未找到孔位")

                except Exception as e:
                    error_msg = f"测试加载失败: {str(e)}"
                    self.logger.error(error_msg, exc_info=True)
                    self.log_message(f"❌ {error_msg}")
            else:
                self.log_message(f"⚠️ 测试文件不存在: {test_file}")

        self.log_message("❌ 没有找到可用的测试DXF文件")



    def update_file_info(self, file_path: str):
        """更新文件信息显示"""
        import os
        from datetime import datetime

        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        size_str = f"{file_size / 1024:.1f} KB" if file_size < 1024*1024 else f"{file_size / (1024*1024):.1f} MB"

        self.file_name_label.setText(file_name)
        self.file_path_label.setText(file_path)
        self.file_size_label.setText(size_str)
        self.load_time_label.setText(datetime.now().strftime("%H:%M:%S"))
        self.hole_count_label.setText(f"孔位数量: {len(self.hole_collection)}")

    def update_hole_display(self):
        """更新孔位显示"""
        if not self.hole_collection:
            self.log_message("⚠️ 没有孔位数据可显示")
            return

        try:
            self.log_message(f"开始更新孔位显示，孔位数量: {len(self.hole_collection)}")

            # 显示前几个孔位的信息用于调试
            for i, hole in enumerate(self.hole_collection):
                if i < 3:  # 只显示前3个
                    self.log_message(f"  孔位 {i+1}: {hole.hole_id} 位置=({hole.center_x:.2f}, {hole.center_y:.2f}) 半径={hole.radius:.2f}")
                elif i == 3:
                    self.log_message(f"  ... 还有 {len(self.hole_collection) - 3} 个孔位")
                    break

            # 显示边界信息
            bounds = self.hole_collection.get_bounds()
            self.log_message(f"孔位边界: X=[{bounds[0]:.2f}, {bounds[2]:.2f}], Y=[{bounds[1]:.2f}, {bounds[3]:.2f}]")

            # 使用图形视图加载孔位数据
            self.graphics_view.load_holes(self.hole_collection)
            self.log_message(f"✅ 图形视图已加载 {len(self.hole_collection)} 个孔位")

            # 检查图形视图状态
            scene_rect = self.graphics_view.scene.sceneRect()
            self.log_message(f"场景矩形: {scene_rect.x():.2f}, {scene_rect.y():.2f}, {scene_rect.width():.2f}x{scene_rect.height():.2f}")

        except Exception as e:
            error_msg = f"更新孔位显示失败: {e}"
            self.logger.error(error_msg, exc_info=True)
            self.log_message(f"❌ {error_msg}")

    def update_status_display(self):
        """更新状态统计显示"""
        if not self.hole_collection:
            return

        # 统计各种状态的孔位数量
        status_counts = {
            HoleStatus.PENDING: 0,
            HoleStatus.QUALIFIED: 0,
            HoleStatus.DEFECTIVE: 0,
            HoleStatus.BLIND: 0,
            HoleStatus.TIE_ROD: 0,
            HoleStatus.PROCESSING: 0
        }

        for hole in self.hole_collection.holes.values():
            if hole.status in status_counts:
                status_counts[hole.status] += 1

        # 更新状态统计标签
        self.pending_status_count_label.setText(f"待检: {status_counts[HoleStatus.PENDING]}")
        self.qualified_count_label.setText(f"合格: {status_counts[HoleStatus.QUALIFIED]}")
        self.defective_count_label.setText(f"异常: {status_counts[HoleStatus.DEFECTIVE]}")
        self.blind_count_label.setText(f"盲孔: {status_counts[HoleStatus.BLIND]}")
        self.tie_rod_count_label.setText(f"拉杆孔: {status_counts[HoleStatus.TIE_ROD]}")
        self.processing_count_label.setText(f"检测中: {status_counts[HoleStatus.PROCESSING]}")

        # 更新进度
        try:
            total_holes = len(self.hole_collection)
        except TypeError:
            # 处理Mock对象或其他无法计算长度的情况
            total_holes = len(self.hole_collection.holes) if hasattr(self.hole_collection, 'holes') else 0

        completed_holes = status_counts[HoleStatus.QUALIFIED] + status_counts[HoleStatus.DEFECTIVE] + status_counts[HoleStatus.BLIND] + status_counts[HoleStatus.TIE_ROD]
        pending_holes = status_counts[HoleStatus.PENDING] + status_counts[HoleStatus.PROCESSING]

        # 更新检测进度组中的已完成和待完成数量
        self.completed_count_label.setText(f"已完成: {completed_holes}")
        self.pending_count_label.setText(f"待完成: {pending_holes}")

        if total_holes > 0:
            completion_rate = (completed_holes / total_holes) * 100
            self.progress_bar.setValue(int(completion_rate))
            self.completion_rate_label.setText(f"完成率: {completion_rate:.1f}%")

            if completed_holes > 0:
                qualification_rate = (status_counts[HoleStatus.QUALIFIED] / completed_holes) * 100
                self.qualification_rate_label.setText(f"合格率: {qualification_rate:.1f}%")
            else:
                self.qualification_rate_label.setText("合格率: 0%")

        # 如果检测正在进行，更新检测开始时间
        if self.detection_running and not self.detection_start_time:
            from datetime import datetime
            self.detection_start_time = datetime.now()

    def update_hole_info_display(self):
        """更新选中孔位信息显示"""
        self.log_message("🔄 开始UI更新...")

        # 验证UI组件是否存在
        ui_components = [
            ('selected_hole_id_label', self.selected_hole_id_label),
            ('selected_hole_position_label', self.selected_hole_position_label),
            ('selected_hole_status_label', self.selected_hole_status_label),
            ('selected_hole_radius_label', self.selected_hole_radius_label)
        ]

        for name, component in ui_components:
            if component is None:
                self.log_message(f"❌ UI组件不存在: {name}")
                return
            else:
                # 检查组件的可见性和父组件
                self.log_message(f"✅ {name}: 存在={component is not None}, 可见={component.isVisible()}, 启用={component.isEnabled()}")

        self.log_message("✅ 所有UI组件验证通过")

        # 检查selected_hole状态
        if self.selected_hole:
            self.log_message(f"✅ selected_hole存在: {self.selected_hole.hole_id}")
        else:
            self.log_message("❌ selected_hole为None")

        if not self.selected_hole:
            self.log_message("🔄 清空孔位信息显示")
            self.selected_hole_id_label.setText("未选择")
            self.selected_hole_position_label.setText("-")
            self.selected_hole_status_label.setText("-")
            self.selected_hole_radius_label.setText("-")

            # 强制刷新所有标签
            for _, component in ui_components:
                component.repaint()

            # 处理Qt事件队列
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()
            self.log_message("✅ 清空UI更新完成")
            return

        hole = self.selected_hole
        self.log_message(f"🔄 UI更新: 显示孔位 {hole.hole_id} 信息")
        self.log_message(f"  📊 孔位数据: ID={hole.hole_id}, X={hole.center_x}, Y={hole.center_y}, R={hole.radius}, 状态={hole.status}")

        try:
            # 基本信息 - 只设置值部分（前缀由布局中的描述标签提供）
            id_text = f"{hole.hole_id}"
            position_text = f"({hole.center_x:.1f}, {hole.center_y:.1f})"

            self.log_message(f"  📝 准备设置ID标签: '{id_text}'")
            self.log_message(f"  📝 准备设置位置标签: '{position_text}'")

            # 设置文本并验证
            self.selected_hole_id_label.setText(id_text)
            actual_id_text = self.selected_hole_id_label.text()
            self.log_message(f"  ✅ ID标签设置结果: 期望='{id_text}', 实际='{actual_id_text}'")

            self.selected_hole_position_label.setText(position_text)
            actual_position_text = self.selected_hole_position_label.text()
            self.log_message(f"  ✅ 位置标签设置结果: 期望='{position_text}', 实际='{actual_position_text}'")

            # 立即强制刷新
            self.selected_hole_id_label.repaint()
            self.selected_hole_position_label.repaint()

            # 状态信息（带颜色）
            if hole.status == HoleStatus.QUALIFIED:
                status_color = "#4CAF50"  # 绿色
            elif hole.status == HoleStatus.DEFECTIVE:
                status_color = "#F44336"  # 红色
            elif hole.status == HoleStatus.PROCESSING:
                status_color = "#2196F3"  # 蓝色
            elif hole.status == HoleStatus.BLIND:
                status_color = "#FF9800"  # 橙色
            elif hole.status == HoleStatus.TIE_ROD:
                status_color = "#9C27B0"  # 紫色
            else:
                status_color = "#CCCCCC"  # 灰色

            # 状态和半径信息 - 只设置值部分
            status_text = f"{hole.status.value}"
            radius_text = f"{hole.radius:.3f}mm"

            self.log_message(f"  📝 准备设置状态标签: '{status_text}' (颜色: {status_color})")
            self.log_message(f"  📝 准备设置半径标签: '{radius_text}'")

            # 设置状态标签并验证
            self.selected_hole_status_label.setText(status_text)
            self.selected_hole_status_label.setStyleSheet(f"color: {status_color}; font-weight: bold;")
            actual_status_text = self.selected_hole_status_label.text()
            self.log_message(f"  ✅ 状态标签设置结果: 期望='{status_text}', 实际='{actual_status_text}'")

            # 设置半径标签并验证
            self.selected_hole_radius_label.setText(radius_text)
            actual_radius_text = self.selected_hole_radius_label.text()
            self.log_message(f"  ✅ 半径标签设置结果: 期望='{radius_text}', 实际='{actual_radius_text}'")

            # 强制刷新所有UI组件
            for _, component in ui_components:
                component.repaint()

            # 确保整个父容器也刷新
            if hasattr(self, 'hole_info_widget'):
                self.hole_info_widget.repaint()

            # 多重强制UI刷新
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import QTimer

            # 1. 立即处理事件队列
            QApplication.processEvents()

            # 2. 强制刷新整个窗口
            self.update()

            # 3. 再次处理事件队列
            QApplication.processEvents()

            # 4. 使用定时器延迟刷新（确保UI完全更新）
            QTimer.singleShot(50, lambda: self._final_ui_refresh(hole.hole_id))

            self.log_message(f"✅ UI更新完成: {hole.hole_id} - 所有标签已刷新")

            # 在日志中显示更详细的信息
            self.log_message(f"📍 孔位详情: {hole.hole_id}")
            self.log_message(f"   坐标: X={hole.center_x:.1f}, Y={hole.center_y:.1f}")
            self.log_message(f"   半径: {hole.radius:.3f}mm")

            # 检查数据关联
            self._check_hole_data_availability(hole.hole_id)

        except Exception as e:
            self.log_message(f"❌ UI更新过程异常: {e}")
            import traceback
            self.log_message(f"❌ 异常详情: {traceback.format_exc()}")
            return

    def _final_ui_refresh(self, hole_id):
        """最终UI刷新确认"""
        try:
            # 最后一次强制刷新
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()

            # 验证UI更新结果
            if self.selected_hole and self.selected_hole.hole_id == hole_id:
                actual_id = self.selected_hole_id_label.text()
                actual_position = self.selected_hole_position_label.text()
                actual_status = self.selected_hole_status_label.text()
                actual_radius = self.selected_hole_radius_label.text()

                self.log_message(f"🔍 最终UI验证: {hole_id}")
                self.log_message(f"  ID标签: '{actual_id}'")
                self.log_message(f"  位置标签: '{actual_position}'")
                self.log_message(f"  状态标签: '{actual_status}'")
                self.log_message(f"  半径标签: '{actual_radius}'")

                if (hole_id in actual_id and
                    "(" in actual_position and
                    self.selected_hole.status.value in actual_status and
                    "mm" in actual_radius):
                    self.log_message(f"✅ UI同步成功: {hole_id}")
                else:
                    self.log_message(f"❌ UI同步失败: {hole_id} - 部分标签未更新")

        except Exception as e:
            self.log_message(f"❌ 最终UI刷新异常: {e}")

    def _check_hole_data_availability(self, hole_id):
        """检查孔位数据可用性"""
        self.log_message(f"🔗 检查 {hole_id} 数据关联:")

        # 检查CSV测量数据
        csv_paths = [
            f"Data/{hole_id}/CCIDM",
            f"data/{hole_id}/CCIDM",
            f"cache/{hole_id}",
            f"Data/{hole_id}",
            f"data/{hole_id}"
        ]

        csv_found = False
        csv_files = []

        for csv_path in csv_paths:
            if Path(csv_path).exists():
                # 查找CSV文件
                for csv_file in Path(csv_path).glob("*.csv"):
                    csv_files.append(str(csv_file))
                    csv_found = True

        if csv_found:
            self.log_message(f"  ✅ CSV测量数据: 找到 {len(csv_files)} 个文件")
            for csv_file in csv_files[:3]:  # 只显示前3个
                file_size = Path(csv_file).stat().st_size
                self.log_message(f"    📄 {Path(csv_file).name} ({file_size} bytes)")
            if len(csv_files) > 3:
                self.log_message(f"    ... 还有 {len(csv_files) - 3} 个文件")
        else:
            self.log_message(f"  ❌ CSV测量数据: 未找到")

        # 检查内窥镜图像
        image_paths = [
            f"cache/result/{hole_id}",
            f"cache/result2/{hole_id}",
            f"cache/result",
            f"cache/result2"
        ]

        image_found = False
        image_files = []

        for image_path in image_paths:
            if Path(image_path).exists():
                # 查找图像文件
                for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp']:
                    for img_file in Path(image_path).glob(ext):
                        if hole_id.lower() in img_file.name.lower():
                            image_files.append(str(img_file))
                            image_found = True

        # 如果没有找到特定孔位的图像，检查通用图像目录
        if not image_found:
            for image_path in ["cache/result", "cache/result2"]:
                if Path(image_path).exists():
                    all_images = list(Path(image_path).glob("*.jpg")) + list(Path(image_path).glob("*.png"))
                    if all_images:
                        image_files = [str(f) for f in all_images[:5]]  # 取前5个
                        image_found = True
                        break

        if image_found:
            self.log_message(f"  ✅ 内窥镜图像: 找到 {len(image_files)} 个文件")
            for img_file in image_files[:3]:  # 只显示前3个
                file_size = Path(img_file).stat().st_size
                self.log_message(f"    🖼️ {Path(img_file).name} ({file_size} bytes)")
        else:
            self.log_message(f"  ❌ 内窥镜图像: 未找到")

        # 检查实时监控关联
        if hole_id in ["H00001", "H00002"]:
            self.log_message(f"  ✅ 实时监控: 支持 (工件号: {hole_id})")
            self.log_message(f"  ✅ 历史数据: 支持")
        else:
            self.log_message(f"  ⚠️ 实时监控: 仅支持 H00001 和 H00002")
            self.log_message(f"  ⚠️ 历史数据: 仅支持 H00001 和 H00002")

        # 数据完整性评估
        data_score = 0
        if csv_found:
            data_score += 40
        if image_found:
            data_score += 40
        if hole_id in ["H00001", "H00002"]:
            data_score += 20

        if data_score >= 80:
            completeness = "完整"
            emoji = "🟢"
        elif data_score >= 40:
            completeness = "部分"
            emoji = "🟡"
        else:
            completeness = "缺失"
            emoji = "🔴"

        self.log_message(f"  {emoji} 数据完整性: {completeness} ({data_score}/100)")

        # 显示可用操作
        has_realtime_support = hole_id in ["H00001", "H00002"]
        self.log_message(f"  🎮 可用操作:")
        self.log_message(f"    🔄 实时监控 - {'✅ 可用' if has_realtime_support else '❌ 无数据'}")
        self.log_message(f"    📊 历史数据 - {'✅ 可用' if has_realtime_support else '❌ 无数据'}")
        self.log_message(f"    ⚠️ 标记异常 - ✅ 可用")

        return {
            'csv_files': csv_files,
            'image_files': image_files,
            'realtime_support': has_realtime_support,
            'csv_found': csv_found,
            'image_found': image_found,
            'data_score': data_score
        }

    def on_hole_selected(self, hole: HoleData):
        """孔位被选中时的处理"""
        self.log_message(f"🎯 右键选中孔位: {hole.hole_id}")

        try:
            # 设置选中孔位
            self.selected_hole = hole
            self.log_message(f"📝 设置selected_hole为: {hole.hole_id}")

            # 立即更新UI显示
            self.update_hole_info_display()

            # 根据数据可用性启用按钮
            has_data = hole.hole_id in ["H00001", "H00002"]
            self.log_message(f"🔍 数据可用性检查: {hole.hole_id} -> {has_data}")

            # 验证按钮对象存在
            buttons = [
                ('goto_realtime_btn', self.goto_realtime_btn),
                ('goto_history_btn', self.goto_history_btn),
                ('mark_defective_btn', self.mark_defective_btn)
            ]

            for name, btn in buttons:
                if btn is None:
                    self.log_message(f"❌ 按钮不存在: {name}")
                    return

            self.log_message("✅ 所有按钮对象验证通过")

            # 设置按钮状态并验证
            self.goto_realtime_btn.setEnabled(has_data)
            self.goto_history_btn.setEnabled(has_data)
            self.mark_defective_btn.setEnabled(True)  # 标记异常总是可用

            # 验证按钮状态设置结果
            realtime_enabled = self.goto_realtime_btn.isEnabled()
            history_enabled = self.goto_history_btn.isEnabled()
            mark_enabled = self.mark_defective_btn.isEnabled()

            self.log_message(f"🎮 按钮状态设置结果:")
            self.log_message(f"  实时监控: 期望={has_data}, 实际={realtime_enabled}")
            self.log_message(f"  历史数据: 期望={has_data}, 实际={history_enabled}")
            self.log_message(f"  标记异常: 期望=True, 实际={mark_enabled}")

            # 更新按钮提示文本
            if has_data:
                realtime_tooltip = f"查看 {hole.hole_id} 的实时监控数据"
                history_tooltip = f"查看 {hole.hole_id} 的历史数据"
            else:
                realtime_tooltip = f"{hole.hole_id} 无实时监控数据（仅支持 H00001, H00002）"
                history_tooltip = f"{hole.hole_id} 无历史数据（仅支持 H00001, H00002）"

            mark_tooltip = f"将 {hole.hole_id} 标记为异常"

            self.goto_realtime_btn.setToolTip(realtime_tooltip)
            self.goto_history_btn.setToolTip(history_tooltip)
            self.mark_defective_btn.setToolTip(mark_tooltip)

            # 验证工具提示设置结果
            actual_realtime_tooltip = self.goto_realtime_btn.toolTip()
            actual_history_tooltip = self.goto_history_btn.toolTip()
            actual_mark_tooltip = self.mark_defective_btn.toolTip()

            self.log_message(f"💬 工具提示设置结果:")
            self.log_message(f"  实时监控: '{actual_realtime_tooltip}'")
            self.log_message(f"  历史数据: '{actual_history_tooltip}'")
            self.log_message(f"  标记异常: '{actual_mark_tooltip}'")

            # 检查数据关联
            self._check_hole_data_availability(hole.hole_id)

            # 多重强制UI刷新
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import QTimer

            # 1. 立即处理事件队列
            QApplication.processEvents()

            # 2. 强制刷新整个窗口
            self.update()

            # 3. 再次处理事件队列
            QApplication.processEvents()

            # 4. 使用定时器延迟刷新
            QTimer.singleShot(50, lambda: self._final_ui_refresh(hole.hole_id))

            self.log_message(f"✅ 右键选择完成，UI已刷新: {hole.hole_id}")

        except Exception as e:
            self.log_message(f"❌ 右键选择处理异常: {e}")
            import traceback
            self.log_message(f"❌ 异常详情: {traceback.format_exc()}")
            return

    def on_hole_hovered(self, hole: HoleData):
        """孔位被悬停时的处理"""
        # 可以在这里显示悬停信息
        pass

    def on_view_changed(self):
        """视图改变时的处理"""
        # 可以在这里更新缩放信息等
        pass

    def log_message(self, message: str):
        """添加日志消息"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_text.append(formatted_message)

        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def filter_holes(self, filter_type: str):
        """过滤孔位显示"""
        if not self.hole_collection:
            return

        self.log_message(f"过滤视图: {filter_type}")
        # 这里可以实现过滤逻辑

    # 视图控制方法
    def zoom_in(self):
        """放大视图"""
        if hasattr(self, 'graphics_view'):
            self.graphics_view.zoom_in()

    def zoom_out(self):
        """缩小视图"""
        if hasattr(self, 'graphics_view'):
            self.graphics_view.zoom_out()

    def fit_view(self):
        """适应窗口"""
        if hasattr(self, 'graphics_view'):
            self.graphics_view.fit_in_view()

    def reset_view(self):
        """重置视图"""
        if hasattr(self, 'graphics_view'):
            self.graphics_view.reset_view()

    # 检测控制方法
    def start_detection(self):
        """开始检测"""
        if not self.hole_collection:
            QMessageBox.warning(self, "警告", "请先加载DXF文件")
            return

        if self.detection_running:
            return

        # 创建有序的孔位列表（按孔位ID顺序）
        self.detection_holes = self._create_ordered_hole_list()
        self.detection_running = True
        self.detection_paused = False

        # 初始化检测时间
        from datetime import datetime
        self.detection_start_time = datetime.now()
        self.detection_elapsed_seconds = 0

        # 更新按钮状态
        self.start_detection_btn.setEnabled(False)
        self.pause_detection_btn.setEnabled(True)
        self.stop_detection_btn.setEnabled(True)

        # 启动检测定时器
        self.detection_timer.start(1000)  # 每秒处理一个孔位

        self.log_message("开始检测")
        self.status_label.setText("检测进行中...")

    def pause_detection(self):
        """暂停/恢复检测"""
        if not self.detection_running:
            return

        if self.detection_paused:
            # 恢复检测
            self.detection_timer.start(1000)
            self.detection_paused = False
            self.pause_detection_btn.setText("暂停检测")
            self.log_message("恢复检测")
            self.status_label.setText("检测进行中...")
        else:
            # 暂停检测
            self.detection_timer.stop()
            self.detection_paused = True
            self.pause_detection_btn.setText("恢复检测")
            self.log_message("暂停检测")
            self.status_label.setText("检测已暂停")

    def stop_detection(self):
        """停止检测"""
        if not self.detection_running:
            return

        self.detection_timer.stop()
        self.detection_running = False
        self.detection_paused = False

        # 重置检测时间相关变量
        self.detection_start_time = None

        # 更新按钮状态
        self.start_detection_btn.setEnabled(True)
        self.pause_detection_btn.setEnabled(False)
        self.pause_detection_btn.setText("暂停检测")
        self.stop_detection_btn.setEnabled(False)

        self.log_message("停止检测")
        self.status_label.setText("检测已停止")

    def _process_detection_step(self):
        """处理检测步骤"""
        if not self.detection_holes or not self.detection_running:
            self.stop_detection()
            return

        # 获取下一个待检测的孔位
        current_hole = self.detection_holes.pop(0)

        # 模拟检测过程
        current_hole.status = HoleStatus.PROCESSING
        self.graphics_view.update_hole_status(current_hole.hole_id, current_hole.status)

        # 模拟检测结果（这里可以接入真实的检测算法）- 按照指定比例分配状态
        import random
        rand_value = random.random()

        if rand_value < 0.995:  # 99.5%概率合格
            current_hole.status = HoleStatus.QUALIFIED
        elif rand_value < 0.9999:  # 0.49%概率异常
            current_hole.status = HoleStatus.DEFECTIVE
        else:  # 0.01%概率其他状态
            # 随机分配其他状态
            other_statuses = [HoleStatus.BLIND, HoleStatus.TIE_ROD]
            current_hole.status = random.choice(other_statuses)

        self.graphics_view.update_hole_status(current_hole.hole_id, current_hole.status)
        self.update_status_display()

        self.log_message(f"检测完成: {current_hole.hole_id} - {current_hole.status.value}")

        # 检查是否完成所有检测
        if not self.detection_holes:
            self.stop_detection()
            self.log_message("所有孔位检测完成")
            QMessageBox.information(self, "完成", "所有孔位检测完成！")

    def _create_ordered_hole_list(self):
        """创建有序的孔位列表（按孔位ID顺序）"""
        holes = list(self.hole_collection.holes.values())

        # 按孔位ID排序，确保从H00001开始顺序进行
        holes.sort(key=lambda h: h.hole_id)

        return holes

    # 模拟进度功能
    def _start_simulation_progress(self):
        """开始模拟进度"""
        if not self.hole_collection:
            QMessageBox.warning(self, "警告", "请先加载DXF文件")
            return

        if self.simulation_running:
            # 停止模拟
            self.simulation_timer.stop()
            self.simulation_running = False
            self.simulate_btn.setText("使用模拟进度")
            self.log_message("⏹️ 停止模拟进度")
            return

        # 创建待处理孔位列表（按孔位ID顺序）
        self.pending_holes = list(self.hole_collection.holes.values())
        # 按孔位ID排序，确保从H00001开始顺序进行
        self.pending_holes.sort(key=lambda hole: hole.hole_id)
        self.simulation_hole_index = 0

        self.log_message(f"🎯 准备模拟 {len(self.pending_holes)} 个孔位")
        self.log_message(f"📋 孔位列表: {[h.hole_id for h in self.pending_holes[:5]]}{'...' if len(self.pending_holes) > 5 else ''}")

        # 检查图形视图状态
        graphics_hole_count = len(self.graphics_view.hole_items) if hasattr(self.graphics_view, 'hole_items') else 0
        self.log_message(f"🖼️ 图形视图中的孔位数量: {graphics_hole_count}")

        if graphics_hole_count == 0:
            self.log_message("⚠️ 图形视图中没有孔位，模拟可能无法显示颜色变化")

        # 启动模拟定时器
        self.simulation_timer.start(1000)  # 每1000ms更新一个孔位，便于观察
        self.simulation_running = True
        self.simulate_btn.setText("停止模拟")

        self.log_message("🚀 开始模拟进度")

    def _update_simulation_progress(self):
        """更新模拟进度"""
        if not self.pending_holes or self.simulation_hole_index >= len(self.pending_holes):
            # 模拟完成
            self.simulation_timer.stop()
            self.simulation_running = False
            self.simulate_btn.setText("使用模拟进度")
            self.log_message("✅ 模拟进度完成")
            return

        # 获取当前孔位
        current_hole = self.pending_holes[self.simulation_hole_index]

        self.log_message(f"🔄 正在处理孔位: {current_hole.hole_id} (索引: {self.simulation_hole_index}/{len(self.pending_holes)})")

        # 检查图形视图中是否有这个孔位
        if current_hole.hole_id not in self.graphics_view.hole_items:
            self.log_message(f"⚠️ 图形视图中未找到孔位: {current_hole.hole_id}")
            self.simulation_hole_index += 1
            return

        # 获取图形项
        hole_item = self.graphics_view.hole_items[current_hole.hole_id]

        # 先设置为检测中状态
        old_status = current_hole.status
        old_brush = hole_item.brush().color().name()

        # 更新为检测中状态
        current_hole.status = HoleStatus.PROCESSING
        hole_item.update_status(current_hole.status)

        processing_brush = hole_item.brush().color().name()
        self.log_message(f"🔵 {current_hole.hole_id}: {old_status.value} → {current_hole.status.value}")
        self.log_message(f"🎨 颜色变化: {old_brush} → {processing_brush}")

        # 强制刷新显示检测中状态
        hole_item.update()
        self.graphics_view.scene.update(hole_item.boundingRect())
        self.graphics_view.viewport().update()

        self.update_status_display()

        # 保存当前状态，准备延迟更新最终状态
        import random
        rand_value = random.random()

        if rand_value < 0.995:  # 99.5%概率合格
            final_status = HoleStatus.QUALIFIED
            color_emoji = "🟢"
        elif rand_value < 0.9999:  # 0.49%概率异常
            final_status = HoleStatus.DEFECTIVE
            color_emoji = "🔴"
        else:  # 0.01%概率其他状态
            # 随机分配其他状态
            other_statuses = [HoleStatus.BLIND, HoleStatus.TIE_ROD]
            final_status = random.choice(other_statuses)
            color_emoji = "🟡" if final_status == HoleStatus.BLIND else "🔵"

        # 使用定时器延迟更新最终状态，让用户看到检测中状态
        def update_final_status():
            # 更新最终状态显示
            final_old_brush = hole_item.brush().color().name()
            current_hole.status = final_status
            hole_item.update_status(final_status)
            final_new_brush = hole_item.brush().color().name()

            self.log_message(f"{color_emoji} {current_hole.hole_id}: 检测完成 → {final_status.value}")
            self.log_message(f"🎨 最终颜色变化: {final_old_brush} → {final_new_brush}")

            # 多重强制刷新
            hole_item.update()
            self.graphics_view.scene.update(hole_item.boundingRect())
            self.graphics_view.viewport().update()
            self.graphics_view.update()

            # 验证状态是否真的更新了
            actual_status = hole_item.hole_data.status
            if actual_status == final_status:
                self.log_message(f"✅ 状态更新成功: {actual_status.value}")
            else:
                self.log_message(f"❌ 状态更新失败: 期望 {final_status.value}, 实际 {actual_status.value}")

            self.update_status_display()

            # 移动到下一个孔位
            self.simulation_hole_index += 1

        # 500ms后更新最终状态
        QTimer.singleShot(500, update_final_status)

    def _start_simulation_progress_v2(self):
        """开始模拟进度 V2 - 强制颜色更新版本"""
        if not self.hole_collection:
            QMessageBox.warning(self, "警告", "请先加载DXF文件")
            return

        if hasattr(self, 'simulation_running_v2') and self.simulation_running_v2:
            # 停止模拟
            if hasattr(self, 'simulation_timer_v2'):
                self.simulation_timer_v2.stop()
            self.simulation_running_v2 = False
            self.simulate_btn.setText("使用模拟进度")
            self.log_message("⏹️ 停止模拟进度 V2")
            return

        # 初始化V2模拟
        self.simulation_running_v2 = True
        self.simulation_index_v2 = 0
        self.holes_list_v2 = list(self.hole_collection.holes.values())
        self.holes_list_v2.sort(key=lambda h: h.hole_id)

        # 初始化统计计数器
        self.v2_stats = {
            "合格": 0,
            "异常": 0,
            "盲孔": 0,
            "拉杆孔": 0
        }

        total_holes = len(self.holes_list_v2)
        self.log_message(f"🚀 开始模拟进度 V2 - 高频检测模式")
        self.log_message(f"🎯 将处理 {total_holes} 个孔位")
        self.log_message(f"⏱️ 检测频率: 1000ms/孔位 (蓝色→最终颜色: 100ms)")
        self.log_message(f"📊 预期分布比例:")
        self.log_message(f"  🟢 合格: 99.5% (约 {int(total_holes * 0.995)} 个)")
        self.log_message(f"  🔴 异常: 0.49% (约 {int(total_holes * 0.0049)} 个)")
        self.log_message(f"  🟡🔵 其他: 0.01% (约 {int(total_holes * 0.0001)} 个)")

        # 创建定时器
        if not hasattr(self, 'simulation_timer_v2'):
            self.simulation_timer_v2 = QTimer()
            self.simulation_timer_v2.timeout.connect(self._update_simulation_v2)

        self.simulation_timer_v2.start(1000)  # 1000ms一个孔位
        self.simulate_btn.setText("停止模拟")

    def _update_simulation_v2(self):
        """更新模拟进度 V2 - 强制颜色更新"""
        if self.simulation_index_v2 >= len(self.holes_list_v2):
            # 模拟完成
            self.simulation_timer_v2.stop()
            self.simulation_running_v2 = False
            self.simulate_btn.setText("使用模拟进度")

            # 显示最终统计结果
            total = sum(self.v2_stats.values())
            self.log_message("✅ 模拟进度 V2 完成")
            self.log_message("📊 最终统计结果:")

            for status, count in self.v2_stats.items():
                percentage = (count / total * 100) if total > 0 else 0
                emoji_map = {"合格": "🟢", "异常": "🔴", "盲孔": "🟡", "拉杆孔": "🔵"}
                emoji = emoji_map.get(status, "⚫")
                self.log_message(f"  {emoji} {status}: {count} 个 ({percentage:.2f}%)")

            # 显示合格率
            qualified_rate = (self.v2_stats["合格"] / total * 100) if total > 0 else 0
            self.log_message(f"🎯 总合格率: {qualified_rate:.2f}%")
            return

        # 获取当前孔位
        current_hole = self.holes_list_v2[self.simulation_index_v2]
        hole_id = current_hole.hole_id

        self.log_message(f"🔄 V2处理孔位: {hole_id} ({self.simulation_index_v2 + 1}/{len(self.holes_list_v2)})")

        # 检查图形项是否存在
        if hole_id not in self.graphics_view.hole_items:
            self.log_message(f"⚠️ V2: 图形项不存在 {hole_id}")
            self.simulation_index_v2 += 1
            return

        # 获取图形项并强制设置颜色
        hole_item = self.graphics_view.hole_items[hole_id]

        # 直接设置蓝色（检测中）
        from PySide6.QtGui import QColor, QPen, QBrush
        processing_color = QColor(0, 123, 255)  # 蓝色
        hole_item.setBrush(QBrush(processing_color))
        hole_item.setPen(QPen(processing_color.darker(120), 2.0))
        hole_item.update()

        self.log_message(f"🔵 V2: {hole_id} 强制设置蓝色（检测中）")

        # 多重强制刷新
        self.graphics_view.scene.update()
        self.graphics_view.viewport().update()
        self.graphics_view.update()

        # 500ms后设置最终颜色
        def set_final_color():
            import random
            rand = random.random()

            # 按照精确的规格要求分配状态
            if rand < 0.995:  # 99.5%概率 - 合格
                final_color = QColor(0, 255, 0)  # 绿色
                status_text = "合格"
                emoji = "🟢"
            elif rand < 0.9999:  # 0.49%概率 - 异常 (99.5% + 0.49% = 99.99%)
                final_color = QColor(255, 0, 0)  # 红色
                status_text = "异常"
                emoji = "🔴"
            else:  # 0.01%概率 - 其他状态
                # 随机选择其他状态
                other_rand = random.random()
                if other_rand < 0.5:  # 50%概率是盲孔
                    final_color = QColor(255, 255, 0)  # 黄色
                    status_text = "盲孔"
                    emoji = "🟡"
                else:  # 50%概率是拉杆孔
                    final_color = QColor(0, 0, 255)  # 蓝色
                    status_text = "拉杆孔"
                    emoji = "🔵"

            # 直接设置最终颜色
            hole_item.setBrush(QBrush(final_color))
            hole_item.setPen(QPen(final_color.darker(120), 2.0))
            hole_item.update()

            self.log_message(f"{emoji} V2: {hole_id} 检测完成 → {status_text} ({final_color.name()})")

            # 更新统计计数
            self.v2_stats[status_text] += 1

            # 多重强制刷新
            self.graphics_view.scene.update()
            self.graphics_view.viewport().update()
            self.graphics_view.update()

            # 移动到下一个孔位
            self.simulation_index_v2 += 1

        # 延迟设置最终颜色
        QTimer.singleShot(100, set_final_color)  # 100ms后设置最终颜色

    # 孔位操作方法
    def goto_realtime(self):
        """跳转到实时监控"""
        if not self.selected_hole:
            QMessageBox.warning(self, "警告", "请先选择一个孔位")
            return

        hole_id = self.selected_hole.hole_id

        # 检查数据可用性
        if hole_id not in ["H00001", "H00002"]:
            QMessageBox.warning(
                self,
                "数据不可用",
                f"孔位 {hole_id} 没有实时监控数据。\n\n仅 H00001 和 H00002 有完整的测量数据和内窥镜图像。"
            )
            self.log_message(f"❌ 实时监控: {hole_id} 无数据")
            return

        self.log_message(f"🔄 跳转到实时监控: {hole_id}")
        self.navigate_to_realtime.emit(hole_id)

    def goto_history(self):
        """跳转到历史数据"""
        if not self.selected_hole:
            QMessageBox.warning(self, "警告", "请先选择一个孔位")
            return

        hole_id = self.selected_hole.hole_id

        # 检查数据可用性
        if hole_id not in ["H00001", "H00002"]:
            QMessageBox.warning(
                self,
                "数据不可用",
                f"孔位 {hole_id} 没有历史数据。\n\n仅 H00001 和 H00002 有完整的历史测量数据。"
            )
            self.log_message(f"❌ 历史数据: {hole_id} 无数据")
            return

        self.log_message(f"📊 跳转到历史数据: {hole_id}")
        self.navigate_to_history.emit(hole_id)

    def goto_report(self):
        """跳转到报告输出"""
        # 获取当前工件ID（假设为固定值，实际应该从项目配置获取）
        workpiece_id = "H00001"  # 这里应该从当前项目或选中的工件获取

        self.log_message(f"📋 跳转到报告输出: {workpiece_id}")
        self.navigate_to_report.emit(workpiece_id)

    def mark_defective(self):
        """标记为异常"""
        if not self.selected_hole:
            QMessageBox.warning(self, "警告", "请先选择一个孔位")
            return

        hole_id = self.selected_hole.hole_id

        # 确认操作
        reply = QMessageBox.question(
            self,
            "确认标记异常",
            f"确定要将孔位 {hole_id} 标记为异常吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.selected_hole.status = HoleStatus.DEFECTIVE
            self.graphics_view.update_hole_status(hole_id, self.selected_hole.status)
            self.update_status_display()
            self.update_hole_info_display()

            self.log_message(f"⚠️ 标记异常: {hole_id}")
            QMessageBox.information(self, "操作完成", f"孔位 {hole_id} 已标记为异常")
        else:
            self.log_message(f"❌ 取消标记异常: {hole_id}")

    # 导航方法
    def navigate_to_realtime_from_main_view(self, hole_id: str):
        """从主视图导航到实时监控"""
        try:
            # 切换到实时监控选项卡
            self.tab_widget.setCurrentIndex(1)

            # 加载孔位数据到实时监控
            if hasattr(self.realtime_tab, 'load_data_for_hole'):
                self.realtime_tab.load_data_for_hole(hole_id)

            self.log_message(f"导航到实时监控: {hole_id}")
            self.status_label.setText(f"实时监控 - {hole_id}")

        except Exception as e:
            self.logger.error(f"导航到实时监控失败: {e}")
            QMessageBox.warning(self, "错误", f"导航失败: {str(e)}")

    def navigate_to_history_from_main_view(self, hole_id: str):
        """从主视图导航到历史数据"""
        try:
            # 切换到历史数据选项卡
            self.tab_widget.setCurrentIndex(2)

            # 加载孔位数据到历史查看器
            if hasattr(self.history_tab, 'load_data_for_hole'):
                self.history_tab.load_data_for_hole(hole_id)

            self.log_message(f"导航到历史数据: {hole_id}")
            self.status_label.setText(f"历史数据 - {hole_id}")

        except Exception as e:
            self.logger.error(f"导航到历史数据失败: {e}")
            QMessageBox.warning(self, "错误", f"导航失败: {str(e)}")

    def navigate_to_report_from_main_view(self, workpiece_id: str):
        """从主视图导航到报告输出"""
        try:
            # 切换到报告输出选项卡
            self.tab_widget.setCurrentIndex(3)

            # 加载工件数据到报告输出界面
            if hasattr(self.report_tab, 'load_data_for_workpiece'):
                self.report_tab.load_data_for_workpiece(workpiece_id)

            self.log_message(f"导航到报告输出: {workpiece_id}")
            self.status_label.setText(f"报告输出 - {workpiece_id}")

        except Exception as e:
            self.logger.error(f"导航到报告输出失败: {e}")
            QMessageBox.warning(self, "错误", f"导航失败: {str(e)}")

    # 菜单方法
    def show_settings(self):
        """显示设置对话框"""
        QMessageBox.information(self, "设置", "设置功能待实现")

    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于",
                         "上位机软件 - 管孔检测系统\n"
                         "版本: 1.0.0\n"
                         "负责人: Tsinghua\n\n"
                         "集成DXF文件处理、孔位检测和实时监控功能")

    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止所有定时器
        if hasattr(self, 'detection_timer'):
            self.detection_timer.stop()
        if hasattr(self, 'simulation_timer'):
            self.simulation_timer.stop()
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()

        # 停止工作线程
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait()

        self.logger.info("主窗口关闭")
        event.accept()


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    app = QApplication(sys.argv)

    # 设置应用程序信息
    app.setApplicationName("上位机软件")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Tsinghua")

    # 创建并显示主窗口
    window = MainWindow()
    window.show()

    sys.exit(app.exec())
