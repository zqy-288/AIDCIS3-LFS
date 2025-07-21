"""
合并后的主窗口模块
集成所有功能组件的完整主界面
包含：选项卡布局 + AIDCIS2检测功能 + 搜索功能 + 模拟进度 + 所有原有功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
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
from src.modules.realtime_chart import RealtimeChart
from src.modules.worker_thread import WorkerThread
from src.modules.unified_history_viewer import UnifiedHistoryViewer
from src.modules.report_output_interface import ReportOutputInterface

# 导入AIDCIS2核心组件
from src.core_business.models.hole_data import HoleData, HoleCollection, HoleStatus
from src.core_business.models.status_manager import StatusManager
from src.core_business.dxf_parser import DXFParser
from src.core_business.data_adapter import DataAdapter
from src.core_business.graphics.graphics_view import OptimizedGraphicsView

# 导入产品管理模块
from src.modules.product_selection import ProductSelectionDialog
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'models'))
from product_model import get_product_manager

# 导入扇形区域管理组件
from src.core_business.graphics.sector_manager import SectorManager
from src.core_business.graphics.sector_view import SectorOverviewWidget, SectorDetailView
from src.core_business.graphics.dynamic_sector_view import DynamicSectorDisplayWidget, CompletePanoramaWidget
from src.core_business.graphics.sector_manager_adapter import SectorManagerAdapter
from src.core_business.graphics.dynamic_sector_overview import DynamicSectorOverviewWidget, DynamicSectorDetailView

    
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
        self.data_adapter = DataAdapter()
        self.status_manager = StatusManager()
        
        # 扇形区域管理器（使用适配器支持动态扇形）
        self.sector_manager = SectorManagerAdapter()
        
        # 产品管理
        self.product_manager = get_product_manager()
        self.current_product = None
        
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
        
        # 添加主题调试快捷键（Ctrl+Shift+T）
        from PySide6.QtGui import QKeySequence, QShortcut
        theme_shortcut = QShortcut(QKeySequence("Ctrl+Shift+T"), self)
        theme_shortcut.activated.connect(self.open_theme_debugger)
        print("✅ 主题调试快捷键已设置: Ctrl+Shift+T")
        
        # 定时器用于状态更新
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status_display)
        self.update_timer.start(1000)  # 每秒更新一次
        
        self.logger.info("合并主界面初始化完成")
        
        # 默认加载东重管板DXF文件
        # 注释掉自动加载默认DXF，让用户主动选择
        # self._load_default_dxf()
        self.log_message("🚀 AIDCIS3 启动完成，请选择产品型号或加载DXF文件")
        
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
        
        # # 设置分割器比例，给中间主显示区域更多空间
        # content_splitter.setStretchFactor(0, 1.5)  # 左侧信息面板
        # content_splitter.setStretchFactor(1.5, 6)  # 中间可视化面板（大幅增加比例）
        # content_splitter.setStretchFactor(, )  # 右侧操作面板（减少比例）

        # 设置初始布局比例，但允许用户自由拖动调整
        content_splitter.setSizes([380, 700, 280])  # 调整左侧栏宽度以消除滚动条
        
        # 设置各面板的拖动策略
        content_splitter.setChildrenCollapsible(False)  # 防止面板被完全折叠
        content_splitter.setStretchFactor(0, 0)  # 左侧栏：固定优先级
        content_splitter.setStretchFactor(1, 1)  # 中间面板：主要伸缩区域
        content_splitter.setStretchFactor(2, 0)  # 右侧栏：固定优先级
        
        # 禁用左侧面板的拖动调整，固定为全景预览框大小
        content_splitter.handle(1).setEnabled(False)  # 禁用左侧分割线拖动
        
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

        # 产品选择按钮
        self.product_select_btn = QPushButton("产品型号选择")
        self.product_select_btn.setMinimumSize(140, 45)  # 增加按钮大小
        self.product_select_btn.setFont(toolbar_font)
        layout.addWidget(self.product_select_btn)

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
        
        # 扇形偏移配置框
        # 扇形偏移配置已移除

        return toolbar
    
    

    def create_left_info_panel(self) -> QWidget:
        """创建左侧信息面板"""
        # 改为普通QWidget，移除滚动功能，确保内容适配固定宽度
        panel = QWidget()
        panel.setFixedWidth(380)  # 增加宽度以容纳所有内容
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(4)  # 减少组件间距以节省空间
        layout.setContentsMargins(5, 5, 5, 5)  # 进一步减少边距

        # 设置全局字体 - 进一步减小
        from PySide6.QtGui import QFont
        panel_font = QFont()
        panel_font.setPointSize(10)  # 减小字体到10pt
        panel.setFont(panel_font)

        # 1. 检测进度组（放在最上方）
        progress_group = QGroupBox("检测进度")
        progress_group_font = QFont()
        progress_group_font.setPointSize(10)  # 减小组标题字体
        progress_group_font.setBold(True)
        progress_group.setFont(progress_group_font)
        progress_layout = QVBoxLayout(progress_group)
        progress_layout.setSpacing(4)  # 减少内部间距
        progress_layout.setContentsMargins(4, 4, 4, 4)  # 进一步减少边距

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumHeight(18)  # 减小进度条高度
        progress_layout.addWidget(self.progress_bar)

        # 新增的统计信息 - 使用网格布局，更紧凑
        stats_grid_layout = QGridLayout()
        stats_grid_layout.setSpacing(2)  # 进一步减少网格间距
        stats_grid_layout.setContentsMargins(0, 0, 0, 0)

        # 已完成和待完成统计
        self.completed_count_label = QLabel("已完成: 0")
        self.pending_count_label = QLabel("待完成: 0")

        # 设置标签字体，进一步减小
        label_font = QFont()
        label_font.setPointSize(9)  # 进一步减小字体以节省空间
        self.completed_count_label.setFont(label_font)
        self.pending_count_label.setFont(label_font)

        # 检测批次信息显示（新增）
        self.current_batch_label = QLabel("检测批次: 未开始")
        self.batch_progress_label = QLabel("批次进度: 0/0")
        self.current_batch_label.setFont(label_font)
        self.batch_progress_label.setFont(label_font)
        stats_grid_layout.addWidget(self.current_batch_label, 0, 0)
        stats_grid_layout.addWidget(self.batch_progress_label, 0, 1)
        
        stats_grid_layout.addWidget(self.completed_count_label, 1, 0)
        stats_grid_layout.addWidget(self.pending_count_label, 1, 1)

        # 检测时间和预计用时
        self.detection_time_label = QLabel("检测时间: 00:00:00")
        self.estimated_time_label = QLabel("预计用时: 00:00:00")

        self.detection_time_label.setFont(label_font)
        self.estimated_time_label.setFont(label_font)

        stats_grid_layout.addWidget(self.detection_time_label, 2, 0)
        stats_grid_layout.addWidget(self.estimated_time_label, 2, 1)

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
        file_layout.setSpacing(2)  # 减少间距
        file_layout.setContentsMargins(6, 6, 6, 6)  # 减少边距

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
        file_info_font.setPointSize(8)  # 进一步减小字体以节省空间
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
        file_layout.addWidget(file_size_desc_label, 1, 0)
        file_layout.addWidget(self.file_size_label, 1, 1)
        file_layout.addWidget(hole_count_desc_label, 2, 0)
        file_layout.addWidget(self.hole_count_label, 2, 1)

        layout.addWidget(file_group)

        # 5. 全景预览图（新增到左侧面板）
        panorama_group = QGroupBox("全景预览")
        panorama_group.setFont(progress_group_font)
        panorama_layout = QVBoxLayout(panorama_group)
        panorama_layout.setContentsMargins(5, 5, 5, 5)
        
        # 创建全景预览组件
        self.sidebar_panorama = CompletePanoramaWidget()
        self.sidebar_panorama.setFixedSize(360, 420)  # 调整容器尺寸适配面板：宽度360，高度420（增大高度）
        # 移除内联样式，使用主题管理器
        self.sidebar_panorama.setObjectName("PanoramaWidget")
        panorama_layout.addWidget(self.sidebar_panorama)
        layout.addWidget(panorama_group)

        # 6. 扇形详细信息（删除圆形扇形概览图，只保留文字统计）
        sector_stats_group = QGroupBox("选中扇形")
        sector_stats_group.setFont(progress_group_font)
        sector_stats_layout = QVBoxLayout(sector_stats_group)
        sector_stats_layout.setContentsMargins(5, 5, 5, 5)
        
        self.sector_stats_label = QLabel("扇形统计信息")
        self.sector_stats_label.setFont(QFont("Arial", 10))
        self.sector_stats_label.setWordWrap(True)
        self.sector_stats_label.setMinimumHeight(120)  # 增加最小高度
        self.sector_stats_label.setAlignment(Qt.AlignTop)
        # 移除内联样式，使用主题管理器
        self.sector_stats_label.setObjectName("SectorStatsLabel")
        sector_stats_layout.addWidget(self.sector_stats_label)
        layout.addWidget(sector_stats_group)

        layout.addStretch()

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
        layout.setContentsMargins(5, 5, 5, 5)

        # 状态图例
        legend_frame = self.create_status_legend()
        layout.addWidget(legend_frame)

        # 层级化显示控制按钮
        view_controls_frame = self.create_view_controls()
        layout.addWidget(view_controls_frame)

        # 创建主要内容区域 - 单一显示区域，无分割器
        # 主要显示区域：动态扇形区域显示（带叠放的完整全景图）
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(2, 2, 2, 2)
        
        # 创建扇形显示容器（支持叠放）
        sector_container = QWidget()
        sector_container_layout = QVBoxLayout(sector_container)
        sector_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # 动态扇形区域显示（主要显示区域）- 直接填满整个可用空间
        self.dynamic_sector_display = DynamicSectorDisplayWidget()
        self.dynamic_sector_display.setMinimumSize(800, 700)  # 增大中间框扇形显示区域的初始大小
        
        # 直接添加主视图，让它填满整个容器，不使用居中包装
        sector_container_layout.addWidget(self.dynamic_sector_display)
        
        # 移除了原有的叠放全景图，改为使用侧边栏全景图
        
        main_layout.addWidget(sector_container)
        
        # 直接添加到布局，无分割器，无下半部分
        layout.addWidget(main_widget)
        
        # 为了向后兼容，设置graphics_view引用
        self.graphics_view = self.dynamic_sector_display.graphics_view
        
        # 连接动态扇形显示的信号
        self.dynamic_sector_display.sector_changed.connect(self.on_dynamic_sector_changed)
        
        # 连接侧边栏全景图的扇形点击信号
        self.sidebar_panorama.sector_clicked.connect(self.on_panorama_sector_clicked)
        
        # 偏移控制信号连接已移除
        
        # 连接扇形管理器信号
        self.sector_manager.sector_progress_updated.connect(self.on_sector_progress_updated)
        self.sector_manager.overall_progress_updated.connect(self.on_overall_progress_updated)

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
            from src.core_business.graphics.hole_graphics_item import HoleGraphicsItem
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
            
            # 将QColor对象转换为CSS颜色字符串
            if hasattr(color, 'name'):
                # QColor对象，转换为十六进制颜色
                css_color = color.name()
            elif isinstance(color, str):
                # 已经是字符串颜色
                css_color = color if color.startswith('#') else f"#{color}"
            else:
                # 其他类型，尝试转换
                css_color = str(color)
            
            # 直接设置背景色样式
            color_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {css_color};
                    border: 1px solid #999;
                    border-radius: 2px;
                }}
            """)
            color_label.setObjectName("StatusColorLabel")

            # 状态文本
            text_label = QLabel(status_names.get(status, status.value))
            text_label.setFont(legend_font)  # 使用更大的字体

            layout.addWidget(color_label)
            layout.addWidget(text_label)
            layout.addSpacing(15)  # 增加间距

        layout.addStretch()
        return legend_frame

    def create_view_controls(self) -> QWidget:
        """创建层级化显示控制按钮"""
        control_frame = QFrame()
        control_frame.setFrameStyle(QFrame.StyledPanel)
        control_frame.setMaximumHeight(60)
        
        layout = QHBoxLayout(control_frame)
        layout.setContentsMargins(12, 8, 12, 8)
        
        # 视图模式标签
        view_label = QLabel("视图模式:")
        view_label.setFont(QFont("Arial", 11, QFont.Bold))
        layout.addWidget(view_label)
        
        # 宏观区域视图按钮
        self.macro_view_btn = QPushButton("📊 宏观区域视图")
        self.macro_view_btn.setCheckable(True)
        self.macro_view_btn.setChecked(True)  # 默认选中宏观视图
        self.macro_view_btn.setMinimumHeight(35)
        self.macro_view_btn.setMinimumWidth(140)
        self.macro_view_btn.setToolTip("显示整个管板的全貌，适合快速浏览和状态概览")
        # 移除内联样式，使用主题管理器
        self.macro_view_btn.setProperty("class", "PrimaryAction")
        self.macro_view_btn.clicked.connect(self.switch_to_macro_view)
        layout.addWidget(self.macro_view_btn)
        
        # 微观管孔视图按钮
        self.micro_view_btn = QPushButton("🔍 微观管孔视图")
        self.micro_view_btn.setCheckable(True)
        self.micro_view_btn.setMinimumHeight(35)
        self.micro_view_btn.setMinimumWidth(140)
        self.micro_view_btn.setToolTip("显示管孔的详细信息，适合精确检查和操作")
        # 移除内联样式，使用主题管理器
        self.micro_view_btn.setProperty("class", "ActionButton")
        self.micro_view_btn.clicked.connect(self.switch_to_micro_view)
        layout.addWidget(self.micro_view_btn)
        
        # 添加分隔符
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        
        # 添加当前视图状态指示器
        self.view_status_label = QLabel("当前: 宏观视图")
        self.view_status_label.setFont(QFont("Arial", 10))
        # 移除内联样式，使用主题管理器
        self.view_status_label.setObjectName("ViewStatusLabel")
        layout.addWidget(self.view_status_label)
        
        layout.addStretch()
        
        return control_frame

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

        select_product_action = QAction("选择产品型号", self)
        select_product_action.setShortcut("Ctrl+O")
        select_product_action.triggered.connect(self.select_product_model)
        file_menu.addAction(select_product_action)

        file_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 视图菜单
        view_menu = menubar.addMenu("视图")
        
        # 主题切换子菜单
        theme_menu = view_menu.addMenu("主题")
        
        dark_theme_action = QAction("深色主题（默认）", self)
        dark_theme_action.setShortcut("Ctrl+D")
        dark_theme_action.triggered.connect(self.switch_to_dark_theme)
        theme_menu.addAction(dark_theme_action)
        
        light_theme_action = QAction("浅色主题", self)
        light_theme_action.setShortcut("Ctrl+L")
        light_theme_action.triggered.connect(self.switch_to_light_theme)
        theme_menu.addAction(light_theme_action)
        
        theme_menu.addSeparator()
        
        theme_debug_action = QAction("主题调试工具", self)
        theme_debug_action.setShortcut("Ctrl+Shift+T")
        theme_debug_action.triggered.connect(self.open_theme_debugger)
        theme_menu.addAction(theme_debug_action)

        # 工具菜单
        tools_menu = menubar.addMenu("工具")

        product_management_action = QAction("产品信息维护", self)
        product_management_action.triggered.connect(self.open_product_management)
        tools_menu.addAction(product_management_action)
        
        tools_menu.addSeparator()

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
        # 如果检测正在进行或模拟正在进行，并且有开始时间，则计算经过的时间
        is_running = getattr(self, 'detection_running', False) or getattr(self, 'simulation_running_v2', False)
        
        if is_running and self.detection_start_time:
            from datetime import datetime
            current_time = datetime.now()
            elapsed = current_time - self.detection_start_time
            self.detection_elapsed_seconds = int(elapsed.total_seconds())
        elif not hasattr(self, 'detection_elapsed_seconds'):
            self.detection_elapsed_seconds = 0

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

        from src.core_business.models.hole_data import HoleStatus
        completed_count = 0
        for hole in self.hole_collection.holes.values():
            if hole.status in [HoleStatus.QUALIFIED, HoleStatus.DEFECTIVE, HoleStatus.BLIND, HoleStatus.TIE_ROD]:
                completed_count += 1
        return completed_count

    def setup_connections(self):
        """设置信号槽连接"""
        # 工具栏连接
        self.product_select_btn.clicked.connect(self.select_product_model)
        self.search_btn.clicked.connect(self.perform_search)
        self.search_input.returnPressed.connect(self.perform_search)
        self.view_combo.currentTextChanged.connect(self.filter_holes)

        # 检测控制连接
        self.start_detection_btn.clicked.connect(self.start_detection)
        self.pause_detection_btn.clicked.connect(self.pause_detection)
        self.stop_detection_btn.clicked.connect(self.stop_detection)

        # 模拟功能连接
        self.simulate_btn.clicked.connect(self._start_snake_pattern_simulation)

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
        
        # 添加测试全景图高亮的快捷键 (Ctrl+H)
        highlight_shortcut = QShortcut(QKeySequence("Ctrl+H"), self)
        highlight_shortcut.activated.connect(self.test_panorama_highlights)



    def test_panorama_highlights(self):
        """测试全景图高亮功能 (快捷键: Ctrl+H)"""
        print("\n" + "="*60)
        print("🧪 [测试] 开始全面诊断全景图系统...")
        print("="*60)
        
        # 1. 检查全景图组件
        if hasattr(self, 'sidebar_panorama') and self.sidebar_panorama:
            print(f"✅ [测试] 找到侧边栏全景图")
            print(f"   - 类型: {type(self.sidebar_panorama)}")
            print(f"   - 场景存在: {hasattr(self.sidebar_panorama.panorama_view, 'scene') and self.sidebar_panorama.panorama_view.scene is not None}")
            
            # 2. 检查数据
            if self.sidebar_panorama.hole_collection:
                print(f"✅ [测试] 全景图有数据: {len(self.sidebar_panorama.hole_collection)} 个孔位")
                
                # 3. 检查几何信息
                print(f"\n📐 [测试] 几何信息:")
                print(f"   - center_point: {self.sidebar_panorama.center_point}")
                print(f"   - panorama_radius: {self.sidebar_panorama.panorama_radius}")
                
                # 4. 手动触发创建
                print(f"\n🔧 [测试] 手动触发高亮创建...")
                self.sidebar_panorama._calculate_panorama_geometry()
                self.sidebar_panorama._create_sector_highlights()
                
                # 5. 检查高亮状态
                print(f"\n🎨 [测试] 高亮状态:")
                print(f"   - 高亮字典大小: {len(self.sidebar_panorama.sector_highlights)}")
                for sector, highlight in self.sidebar_panorama.sector_highlights.items():
                    print(f"   - {sector.value}: 场景={highlight.scene() is not None}, 可见={highlight.isVisible()}")
                
                # 6. 测试显示所有高亮
                if hasattr(self.sidebar_panorama, 'test_highlight_all_sectors'):
                    print(f"\n🌟 [测试] 显示所有扇形高亮...")
                    self.sidebar_panorama.test_highlight_all_sectors()
                
                # 7. 检查信号连接
                print(f"\n🔌 [测试] 信号连接状态:")
                print(f"   - sector_clicked 信号: {hasattr(self.sidebar_panorama, 'sector_clicked')}")
                
            else:
                print(f"❌ [测试] 全景图没有数据")
                print(f"   - hole_collection: {self.sidebar_panorama.hole_collection}")
        else:
            print(f"❌ [测试] 没有找到侧边栏全景图")
            
        # 8. 检查扇形切换机制
        print(f"\n🔄 [测试] 扇形切换机制:")
        print(f"   - dynamic_sector_display: {hasattr(self, 'dynamic_sector_display') and self.dynamic_sector_display is not None}")
        print(f"   - sector_manager: {hasattr(self, 'sector_manager') and self.sector_manager is not None}")
        
        print("\n" + "="*60)
            
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

    def _switch_to_hole_sector(self, hole):
        """切换到包含指定孔位的扇形
        
        Args:
            hole: HoleData对象
            
        Returns:
            bool: 是否成功切换到对应扇形
        """
        try:
            if not hasattr(self, 'sector_manager') or not self.sector_manager:
                self.log_message("⚠️ 扇形管理器不存在，无法切换扇形")
                return False
                
            if not hasattr(self, 'dynamic_sector_display') or not self.dynamic_sector_display:
                self.log_message("⚠️ 动态扇形显示组件不存在，无法切换扇形")
                return False
            
            # 获取孔位所属的扇形
            import math
            from src.core_business.graphics.sector_manager import SectorQuadrant
            
            # 获取扇形管理器使用的中心点
            if hasattr(self.sector_manager, 'center_point') and self.sector_manager.center_point:
                center_x = self.sector_manager.center_point.x()
                center_y = self.sector_manager.center_point.y()
            else:
                # 如果扇形管理器没有中心点，计算管板的几何中心
                bounds = self.hole_collection.get_bounds()
                center_x = (bounds[0] + bounds[2]) / 2
                center_y = (bounds[1] + bounds[3]) / 2
            
            dx = hole.center_x - center_x
            dy = hole.center_y - center_y
            
            # 计算角度
            angle_rad = math.atan2(dy, dx)
            angle_deg = math.degrees(angle_rad)
            
            # 转换为0-360度范围
            if angle_deg < 0:
                angle_deg += 360
            
            # 确定所属扇形
            if 0 <= angle_deg < 90:
                target_sector = SectorQuadrant.SECTOR_1
            elif 90 <= angle_deg < 180:
                target_sector = SectorQuadrant.SECTOR_2
            elif 180 <= angle_deg < 270:
                target_sector = SectorQuadrant.SECTOR_3
            else:
                target_sector = SectorQuadrant.SECTOR_4
            
            self.log_message(f"🎯 孔位 {hole.hole_id} 位于 {target_sector.value} (角度: {angle_deg:.1f}°)")
            
            # 获取当前显示的扇形
            current_sector = None
            if hasattr(self.dynamic_sector_display, 'current_sector'):
                current_sector = self.dynamic_sector_display.current_sector
            
            # 如果不在当前扇形，切换到目标扇形
            if current_sector != target_sector:
                self.log_message(f"🔄 从 {current_sector.value if current_sector else '未知'} 切换到 {target_sector.value}")
                self.dynamic_sector_display.switch_to_sector(target_sector)
                
                # 等待切换完成
                from PySide6.QtWidgets import QApplication
                QApplication.processEvents()
                
                # 给一点时间让视图更新
                import time
                time.sleep(0.1)
                QApplication.processEvents()
                
                # 高亮左侧全景图中对应的扇形
                self._highlight_panorama_sector(target_sector)
                
                return True
            else:
                self.log_message(f"✅ 孔位已在当前显示的 {target_sector.value} 中")
                # 即使已在当前扇形，也要高亮左侧全景图中对应的扇形
                self._highlight_panorama_sector(target_sector)
                return True
                
        except Exception as e:
            self.log_message(f"❌ 切换扇形失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _highlight_panorama_sector(self, sector):
        """高亮左侧全景图中对应的扇形
        
        Args:
            sector: SectorQuadrant对象，要高亮的扇形
        """
        try:
            if not hasattr(self, 'sidebar_panorama') or not self.sidebar_panorama:
                self.log_message("⚠️ 左侧全景图组件不存在，无法高亮扇形")
                return
            
            # 检查sidebar_panorama是否有highlight_sector方法
            if not hasattr(self.sidebar_panorama, 'highlight_sector'):
                self.log_message("⚠️ 左侧全景图组件没有highlight_sector方法")
                return
            
            # 高亮对应的扇形
            self.sidebar_panorama.highlight_sector(sector)
            self.log_message(f"✨ 左侧全景图已高亮 {sector.value}")
            
        except Exception as e:
            self.log_message(f"❌ 高亮左侧全景图扇形失败: {e}")
            import traceback
            traceback.print_exc()

    def _clear_panorama_sector_highlight(self):
        """清空左侧全景图的扇形高亮"""
        try:
            if hasattr(self, 'sidebar_panorama') and self.sidebar_panorama:
                # 如果有清空高亮的方法，调用它
                if hasattr(self.sidebar_panorama, 'clear_sector_highlight'):
                    self.sidebar_panorama.clear_sector_highlight()
                    self.log_message("✨ 已清空左侧全景图扇形高亮")
                # 如果没有专门的清空方法，尝试设置为None或重置所有高亮
                elif hasattr(self.sidebar_panorama, 'current_highlighted_sector'):
                    self.sidebar_panorama.current_highlighted_sector = None
                    # 如果有扇形高亮字典，隐藏所有高亮
                    if hasattr(self.sidebar_panorama, 'sector_highlights'):
                        for highlight in self.sidebar_panorama.sector_highlights.values():
                            if hasattr(highlight, 'hide_highlight'):
                                highlight.hide_highlight()
                    self.log_message("✨ 已清空左侧全景图扇形高亮")
        except Exception as e:
            self.log_message(f"❌ 清空左侧全景图扇形高亮失败: {e}")

    def perform_search(self):
        """执行搜索"""
        search_text = self.search_input.text().strip()
        if not search_text:
            # 清空搜索，显示所有孔位
            if hasattr(self, 'graphics_view'):
                self.graphics_view.clear_search_highlight()
            # 清空左侧全景图的扇形高亮
            self._clear_panorama_sector_highlight()
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
            self.log_message(f"搜索 '{search_text}' 找到 {len(matched_holes)} 个孔位")
            
            # 如果只有一个匹配结果，自动切换到该孔位所在的扇形
            if len(matched_holes) == 1:
                self._switch_to_hole_sector(matched_holes[0])
            # 如果有多个结果，检查是否有精确匹配
            elif len(matched_holes) > 1:
                exact_match = None
                for hole in matched_holes:
                    if hole.hole_id.upper() == search_text_upper:
                        exact_match = hole
                        break
                if exact_match:
                    self._switch_to_hole_sector(exact_match)
                else:
                    # 如果没有精确匹配，高亮第一个结果所在的扇形
                    self._switch_to_hole_sector(matched_holes[0])
            
            # 延迟高亮匹配的孔位，确保扇形切换完成
            def delayed_highlight():
                # 更新graphics_view引用到当前扇形的视图
                if hasattr(self, 'dynamic_sector_display') and self.dynamic_sector_display:
                    if hasattr(self.dynamic_sector_display, 'graphics_view'):
                        self.graphics_view = self.dynamic_sector_display.graphics_view
                        self.graphics_view.highlight_holes(matched_holes, search_highlight=True)
                        self.log_message(f"✨ 高亮显示 {len(matched_holes)} 个搜索结果")
            
            # 延迟100ms执行高亮，确保扇形切换完成
            QTimer.singleShot(100, delayed_highlight)
            
            # 更新状态统计显示
            self.update_status_display()

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

                # AI员工2号修改开始 - 2025-01-14
                # 修改目的：将孔位ID从H格式转换为C{col}R{row}格式
                # 根据数据可用性启用按钮
                has_data = self.selected_hole.hole_id in ["C001R001", "C002R001"]
                # AI员工2号修改结束
                self.goto_realtime_btn.setEnabled(has_data)
                self.goto_history_btn.setEnabled(has_data)
                self.mark_defective_btn.setEnabled(True)  # 标记异常总是可用

                # 更新按钮提示文本
                if has_data:
                    self.goto_realtime_btn.setToolTip(f"查看 {self.selected_hole.hole_id} 的实时监控数据")
                    self.goto_history_btn.setToolTip(f"查看 {self.selected_hole.hole_id} 的历史数据")
                else:
                    # AI员工2号修改 - 工具提示更新
                    self.goto_realtime_btn.setToolTip(f"{self.selected_hole.hole_id} 无实时监控数据（仅支持 C001R001, C002R001）")
                    self.goto_history_btn.setToolTip(f"{self.selected_hole.hole_id} 无历史数据（仅支持 C001R001, C002R001）")

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
                # 查找精确匹配（已在前面处理了扇形切换）
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
                    # AI员工2号修改 - 更新数据支持检查
                    has_data = exact_match.hole_id in ["C001R001", "C002R001"]
                    self.goto_realtime_btn.setEnabled(has_data)
                    self.goto_history_btn.setEnabled(has_data)
                    self.mark_defective_btn.setEnabled(True)  # 标记异常总是可用

                    # 更新按钮提示文本
                    if has_data:
                        self.goto_realtime_btn.setToolTip(f"查看 {exact_match.hole_id} 的实时监控数据")
                        self.goto_history_btn.setToolTip(f"查看 {exact_match.hole_id} 的历史数据")
                    else:
                        # AI员工2号修改 - 工具提示更新
                        self.goto_realtime_btn.setToolTip(f"{exact_match.hole_id} 无实时监控数据（仅支持 C001R001, C002R001）")
                        self.goto_history_btn.setToolTip(f"{exact_match.hole_id} 无历史数据（仅支持 C001R001, C002R001）")

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

    def select_product_model(self):
        """选择产品型号"""
        try:
            dialog = ProductSelectionDialog(self)
            dialog.product_selected.connect(self.on_product_selected)
            dialog.exec()
        except Exception as e:
            error_msg = f"打开产品选择对话框失败: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.log_message(f"❌ {error_msg}")
            QMessageBox.critical(self, "错误", error_msg)
    
    def on_product_selected(self, product):
        """处理产品选择"""
        try:
            self.current_product = product
            self.status_label.setText(f"正在加载产品型号: {product.model_name}")
            self.log_message(f"🎯 选择产品型号: {product.model_name}")
            
            # 清空当前数据
            self.hole_collection = None
            self.log_message("🗑️ 清空当前孔位数据")
            
            # 清空UI显示
            if hasattr(self, 'dynamic_sector_display') and self.dynamic_sector_display:
                # 清空显示但不调用set_hole_collection(None)
                if hasattr(self.dynamic_sector_display, 'graphics_view'):
                    self.dynamic_sector_display.graphics_view.clear()
                if hasattr(self.dynamic_sector_display, 'mini_panorama') and hasattr(self.dynamic_sector_display.mini_panorama, 'scene'):
                    self.dynamic_sector_display.mini_panorama.scene.clear()
            if hasattr(self, 'sidebar_panorama') and self.sidebar_panorama:
                self.sidebar_panorama.info_label.setText("等待数据加载...")
            
            # 配置动态扇形管理器
            if hasattr(product, 'sector_count') and product.sector_count:
                if product.sector_count != 4:  # 非默认4扇形时启用动态模式
                    self.sector_manager.set_dynamic_mode(True, product.sector_count)
                    self.log_message(f"🔧 启用动态扇形模式，扇形数量: {product.sector_count}")
                else:
                    self.sector_manager.set_dynamic_mode(False, 4)
                    self.log_message("🔧 使用标准4扇形模式")
            
            # 如果产品有关联的DXF文件，自动加载
            if hasattr(product, 'dxf_file_path') and product.dxf_file_path:
                self.log_message(f"📁 产品关联DXF文件: {product.dxf_file_path}")
                self.load_dxf_from_product(product.dxf_file_path)
            else:
                # 没有DXF文件时，创建默认的孔位数据或提示用户
                self.log_message("⚠️ 产品没有关联DXF文件")
                self.create_default_hole_data_for_product(product)
            
            # 更新界面显示产品信息
            self.update_product_info_display(product)
            
            self.status_label.setText(f"产品型号已选择: {product.model_name}")
            self.log_message(f"✅ 成功选择产品型号: {product.model_name}")
            
        except Exception as e:
            error_msg = f"处理产品选择失败: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.log_message(f"❌ {error_msg}")
            QMessageBox.critical(self, "错误", error_msg)
    
    def load_dxf_from_product(self, dxf_file_path):
        """从产品关联的DXF文件加载数据"""
        if not dxf_file_path or not Path(dxf_file_path).exists():
            self.log_message(f"警告: DXF文件不存在 - {dxf_file_path}")
            return
        
        try:
            self.log_message(f"加载产品关联的DXF文件: {dxf_file_path}")
            
            # 使用DXF解析器加载文件
            self.hole_collection = self.dxf_parser.parse_file(dxf_file_path)
            
            if not self.hole_collection or len(self.hole_collection) == 0:
                error_msg = "DXF文件中未找到符合条件的孔位"
                self.log_message(f"警告: {error_msg}")
                QMessageBox.warning(self, "警告", error_msg)
                return
            
            self.log_message(f"DXF解析成功，找到 {len(self.hole_collection)} 个孔位")
            
            # 更新UI
            self.update_file_info(dxf_file_path)
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
            
            # 自动适应视图
            if hasattr(self.graphics_view, 'fit_to_window_width'):
                QTimer.singleShot(200, self.graphics_view.fit_to_window_width)
                self.log_message("已自动适应视图宽度")
                
            # 确保选择了扇形1并更新扇形统计信息
            from src.core_business.graphics.sector_manager import SectorQuadrant
            if hasattr(self, 'dynamic_sector_display') and self.dynamic_sector_display:
                QTimer.singleShot(500, lambda: self._update_sector_stats_display(SectorQuadrant.SECTOR_1))
                self.log_message(f"📊 将默认显示扇形1的统计信息")
                
        except Exception as e:
            error_msg = f"加载DXF文件失败: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.log_message(f"❌ {error_msg}")
            QMessageBox.critical(self, "错误", error_msg)
    
    def create_default_hole_data_for_product(self, product):
        """为产品创建默认的孔位数据"""
        # 这里可以根据产品的标准直径创建一些默认的孔位
        # 或者提示用户加载DXF文件
        reply = QMessageBox.question(
            self, "需要加载DXF文件", 
            f"产品型号 '{product.model_name}' 没有关联的DXF文件。\n是否现在选择一个DXF文件？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择DXF文件", "", "DXF文件 (*.dxf);;所有文件 (*)"
            )
            
            if file_path:
                # 保存DXF文件路径到产品
                try:
                    self.product_manager.update_product(product.id, dxf_file_path=file_path)
                    self.load_dxf_from_product(file_path)
                except Exception as e:
                    self.log_message(f"保存DXF文件路径失败: {str(e)}")
            else:
                # 用户取消选择文件，确保UI保持清空状态
                self.log_message("🚫 用户取消选择DXF文件")
                self._ensure_ui_clear_state()
        else:
            # 用户选择不加载DXF文件，确保UI保持清空状态
            self.log_message("🚫 用户选择不加载DXF文件")
            self._ensure_ui_clear_state()
    
    def _ensure_ui_clear_state(self):
        """确保UI处于清空状态"""
        try:
            # 清空主视图数据
            if hasattr(self, 'dynamic_sector_display') and self.dynamic_sector_display:
                # 清空显示但不调用set_hole_collection(None)
                if hasattr(self.dynamic_sector_display, 'graphics_view'):
                    self.dynamic_sector_display.graphics_view.clear()
                if hasattr(self.dynamic_sector_display, 'mini_panorama') and hasattr(self.dynamic_sector_display.mini_panorama, 'scene'):
                    self.dynamic_sector_display.mini_panorama.scene.clear()
                self.log_message("🧹 主视图已清空")
            
            # 清空侧边栏全景图
            if hasattr(self, 'sidebar_panorama') and self.sidebar_panorama:
                self.sidebar_panorama.info_label.setText("请选择产品型号或加载DXF文件")
                # 清空全景图内容
                if hasattr(self.sidebar_panorama, 'panorama_view'):
                    self.sidebar_panorama.panorama_view.scene.clear()
                self.log_message("🧹 侧边栏全景图已清空")
            
            # 禁用检测相关按钮
            buttons_to_disable = [
                'start_detection_btn', 'simulate_btn', 'fit_view_btn',
                'zoom_in_btn', 'zoom_out_btn', 'reset_view_btn'
            ]
            for btn_name in buttons_to_disable:
                if hasattr(self, btn_name):
                    getattr(self, btn_name).setEnabled(False)
            
            self.log_message("🧹 UI清空完成")
            
        except Exception as e:
            self.log_message(f"⚠️ UI清空时发生错误: {e}")
    
    def update_product_info_display(self, product):
        """更新产品信息显示"""
        # 在日志中显示产品详细信息
        self.log_message("=" * 50)
        self.log_message(f"当前产品型号: {product.model_name}")
        if product.model_code:
            self.log_message(f"产品代码: {product.model_code}")
        self.log_message(f"标准直径: {product.standard_diameter:.3f} mm")
        self.log_message(f"公差范围: {product.tolerance_range}")
        min_dia, max_dia = product.diameter_range
        self.log_message(f"直径范围: {min_dia:.3f} - {max_dia:.3f} mm")
        if product.description:
            self.log_message(f"产品描述: {product.description}")
        self.log_message("=" * 50)
    
    def open_product_management(self):
        """打开产品信息维护界面"""
        try:
            from modules.product_management import ProductManagementDialog
            dialog = ProductManagementDialog(self)
            dialog.exec()
        except Exception as e:
            error_msg = f"打开产品信息维护界面失败: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.log_message(f"❌ {error_msg}")
            QMessageBox.critical(self, "错误", error_msg)

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
                        if hasattr(self.graphics_view, 'fit_to_window_width'):
                            QTimer.singleShot(200, self.graphics_view.fit_to_window_width)
                            self.log_message("已自动适应视图宽度")
                            
                        # 确保选择了扇形1并更新扇形统计信息
                        from src.core_business.graphics.sector_manager import SectorQuadrant
                        if hasattr(self, 'dynamic_sector_display') and self.dynamic_sector_display:
                            QTimer.singleShot(500, lambda: self._update_sector_stats_display(SectorQuadrant.SECTOR_1))
                            self.log_message(f"📊 将默认显示扇形1的统计信息")

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

            # 不再直接在主视图加载完整数据，让动态扇形显示组件管理显示内容
            # self.graphics_view.load_holes(self.hole_collection)  # 注释掉，避免覆盖扇形专注显示
            self.log_message(f"✅ 准备加载 {len(self.hole_collection)} 个孔位到扇形显示组件")
            
            # 加载到扇形管理器
            self.sector_manager.load_hole_collection(self.hole_collection)
            self.log_message(f"✅ 扇形管理器已加载孔位数据并进行区域划分")
            
            # 加载到侧边栏全景图
            if hasattr(self, 'sidebar_panorama') and self.sidebar_panorama:
                print(f"🔄 [主窗口] 正在加载侧边栏全景图...")
                print(f"   - sidebar_panorama 类型: {type(self.sidebar_panorama)}")
                print(f"   - hole_collection 数量: {len(self.hole_collection) if self.hole_collection else 0}")
                self.sidebar_panorama.load_complete_view(self.hole_collection)
                self.log_message(f"✅ 侧边栏全景图已加载孔位数据")
                print(f"✅ [主窗口] 侧边栏全景图加载完成")
            else:
                print(f"❌ [主窗口] 侧边栏全景图不存在!")
            
            # 加载到动态扇形显示组件
            if hasattr(self, 'dynamic_sector_display') and self.dynamic_sector_display:
                self.log_message(f"🔍 准备调用 set_hole_collection，dynamic_sector_display = {self.dynamic_sector_display}")
                self.dynamic_sector_display.set_hole_collection(self.hole_collection)
                # 连接浮动全景图的数据更新信号
                self.dynamic_sector_display.connect_data_signals(self)
                self.log_message(f"✅ 动态扇形显示组件已加载孔位数据")
                
                # 显示孔位ID格式示例
                if hasattr(self, 'graphics_view') and self.graphics_view.hole_items:
                    sample_ids = list(self.graphics_view.hole_items.keys())[:5]
                    self.log_message(f"📋 孔位ID格式示例: {sample_ids}")
                
                # 确保主视图显示第一个扇形（扇形专注显示）
                from src.core_business.graphics.sector_manager import SectorQuadrant
                self.dynamic_sector_display.switch_to_sector(SectorQuadrant.SECTOR_1)
                self.log_message(f"✅ 主视图切换到扇形1专注显示")
                
                # 同时在全景图中高亮第一个扇形
                if hasattr(self, 'sidebar_panorama') and self.sidebar_panorama:
                    # 确保全景图已加载数据
                    if not self.sidebar_panorama.hole_collection:
                        print(f"⚠️ [主窗口] 检测到全景图没有数据，立即加载...")
                        self.sidebar_panorama.load_complete_view(self.hole_collection)
                    
                    # 延迟设置高亮，等扇形高亮项创建完成
                    from PySide6.QtCore import QTimer
                    QTimer.singleShot(300, lambda: self.sidebar_panorama.highlight_sector(SectorQuadrant.SECTOR_1))
                    self.log_message(f"🎯 全景图将高亮扇形1")
                
                # 更新扇形统计信息显示（默认显示扇形1）
                self._update_sector_stats_display(SectorQuadrant.SECTOR_1)
                self.log_message(f"📊 已更新扇形1的统计信息")

            # 检查图形视图状态
            scene_rect = self.graphics_view.scene.sceneRect()
            self.log_message(f"场景矩形: {scene_rect.x():.2f}, {scene_rect.y():.2f}, {scene_rect.width():.2f}x{scene_rect.height():.2f}")
            
            # 启用检测控制按钮 - 这是必需的，以便用户可以开始检测
            self.start_detection_btn.setEnabled(True)
            self.simulate_btn.setEnabled(True)
            self.fit_view_btn.setEnabled(True)
            self.zoom_in_btn.setEnabled(True)
            self.zoom_out_btn.setEnabled(True)
            self.reset_view_btn.setEnabled(True)
            self.log_message("✅ 检测控制按钮已启用")
            
            # 【治标方案】条件性自动适应：只在偏移未启用时执行
            if hasattr(self, 'dynamic_sector_widget') and self.dynamic_sector_widget:
                # 检查扇形偏移是否已启用，如果启用则跳过自动适应
                if hasattr(self.dynamic_sector_widget, 'sector_offset_enabled') and self.dynamic_sector_widget.sector_offset_enabled:
                    self.log_message("⚠️ 扇形偏移已启用，跳过自动适应以保护用户设置")
                else:
                    QTimer.singleShot(500, self._auto_fit_sector_view)
                    self.log_message("🔄 正在自动适应扇形视图...")

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
        
        # 调试信息（已静默）
        # print(f"📊 [update_status_display] 状态统计: {status_counts}")
        # print(f"📊 [update_status_display] 已完成: {completed_holes}, 待完成: {pending_holes}")

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
            
        # 更新当前显示的扇形统计信息
        if hasattr(self, 'current_displayed_sector') and self.current_displayed_sector:
            self._update_sector_stats_display(self.current_displayed_sector)

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
            # 基本信息 - 使用标准的C{column}R{row}格式显示
            if hole.row is not None and hole.column is not None:
                id_text = f"C{hole.column:03d}R{hole.row:03d}"
            else:
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
            # 移除内联样式，使用ObjectName
            self.selected_hole_status_label.setObjectName("SelectedHoleStatusLabel")
            self.selected_hole_status_label.setProperty("status_type", hole.status.value if hasattr(hole.status, 'value') else str(hole.status))
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

        # AI员工2号修改开始 - 实时监控关联检查更新
        # 检查实时监控关联
        if hole_id in ["C001R001", "C002R001"]:
            self.log_message(f"  ✅ 实时监控: 支持 (工件号: {hole_id})")
            self.log_message(f"  ✅ 历史数据: 支持")
        else:
            self.log_message(f"  ⚠️ 实时监控: 仅支持 C001R001 和 C002R001")
            self.log_message(f"  ⚠️ 历史数据: 仅支持 C001R001 和 C002R001")
        # AI员工2号修改结束

        # 数据完整性评估
        data_score = 0
        if csv_found:
            data_score += 40
        if image_found:
            data_score += 40
        # AI员工2号修改 - 数据可用性检查
        if hole_id in ["C001R001", "C002R001"]:
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
        # AI员工2号修改 - 实时支持检查
        has_realtime_support = hole_id in ["C001R001", "C002R001"]
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
            # AI员工2号修改 - 数据可用性检查
            has_data = hole.hole_id in ["C001R001", "C002R001"]
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
                # AI员工2号修改 - 工具提示更新
                realtime_tooltip = f"{hole.hole_id} 无实时监控数据（仅支持 C001R001, C002R001）"
                history_tooltip = f"{hole.hole_id} 无历史数据（仅支持 C001R001, C002R001）"

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

    def switch_to_macro_view(self):
        """切换到宏观区域视图"""
        try:
            if hasattr(self, 'graphics_view'):
                self.graphics_view.switch_to_macro_view()
                
            # 更新按钮状态
            self.macro_view_btn.setChecked(True)
            self.micro_view_btn.setChecked(False)
            
            # 更新状态指示器
            self.view_status_label.setText("当前: 宏观视图")
            
            self.log_message("📊 切换到宏观区域视图 - 显示整个管板全貌")
            
        except Exception as e:
            self.log_message(f"❌ 切换宏观视图失败: {e}")

    def switch_to_micro_view(self):
        """切换到微观管孔视图"""
        try:
            if hasattr(self, 'graphics_view'):
                self.graphics_view.switch_to_micro_view()
                
            # 更新按钮状态
            self.micro_view_btn.setChecked(True)
            self.macro_view_btn.setChecked(False)
            
            # 更新状态指示器
            self.view_status_label.setText("当前: 微观视图")
            
            self.log_message("🔍 切换到微观管孔视图 - 显示管孔详细信息")
            
        except Exception as e:
            self.log_message(f"❌ 切换微观视图失败: {e}")
            

    def on_view_mode_changed(self, mode: str):
        """处理视图模式变化"""
        if mode == "macro":
            mode_text = "宏观区域视图"
            self.macro_view_btn.setChecked(True)
            self.micro_view_btn.setChecked(False)
            self.view_status_label.setText("当前: 宏观视图")
        else:
            mode_text = "微观管孔视图"
            self.micro_view_btn.setChecked(True)
            self.macro_view_btn.setChecked(False)
            self.view_status_label.setText("当前: 微观视图")
            
        self.log_message(f"视图模式已切换为: {mode_text}")
    
    def on_sector_selected(self, sector):
        """处理扇形区域选择"""
        from src.core_business.graphics.sector_manager import SectorQuadrant
        
        sector_names = {
            SectorQuadrant.SECTOR_1: "区域1 (右上)",
            SectorQuadrant.SECTOR_2: "区域2 (左上)",
            SectorQuadrant.SECTOR_3: "区域3 (左下)",
            SectorQuadrant.SECTOR_4: "区域4 (右下)"
        }
        
        self.log_message(f"🎯 选择扇形区域: {sector_names.get(sector, sector.value)}")
        
        # 在详细视图中显示该扇形的信息
        if hasattr(self, 'sector_detail_view'):
            self.sector_detail_view.show_sector_detail(sector)
            
        # 可以在图形视图中高亮该扇形区域的孔位
        if hasattr(self, 'sector_manager') and hasattr(self, 'graphics_view'):
            sector_holes = self.sector_manager.get_sector_holes(sector)
            if sector_holes:
                self.graphics_view.highlight_holes(sector_holes, search_highlight=False)
                self.log_message(f"📍 高亮显示 {len(sector_holes)} 个孔位")
    
    def on_sector_progress_updated(self, sector, progress):
        """处理区域划分进度更新"""
        from src.core_business.graphics.sector_manager import SectorQuadrant
        
        sector_names = {
            SectorQuadrant.SECTOR_1: "区域1",
            SectorQuadrant.SECTOR_2: "区域2",
            SectorQuadrant.SECTOR_3: "区域3",
            SectorQuadrant.SECTOR_4: "区域4"
        }
        
        sector_name = sector_names.get(sector, sector.value)
        self.log_message(f"📊 {sector_name} 进度更新: {progress.progress_percentage:.1f}% "
                        f"(完成: {progress.completed_holes}/{progress.total_holes})")
    
    def on_overall_progress_updated(self, overall_stats):
        """处理整体进度更新"""
        total = overall_stats.get('total_holes', 0)
        completed = overall_stats.get('completed_holes', 0)
        qualified = overall_stats.get('qualified_holes', 0)
        
        if total > 0:
            overall_progress = (completed / total) * 100
            qualification_rate = (qualified / completed * 100) if completed > 0 else 0
            
            self.log_message(f"🏆 整体进度更新: {overall_progress:.1f}% "
                           f"(合格率: {qualification_rate:.1f}%)")
            
            # 可以在这里更新界面上的整体进度显示

    def on_report_generated(self, report_type: str, file_path: str):
        """处理报告生成完成事件"""
        self.log_message(f"{report_type}报告生成完成: {file_path}")
        
        # 可以在这里添加更多处理逻辑，如发送通知、更新状态等
        if hasattr(self, 'statusBar'):
            self.statusBar().showMessage(f"{report_type}报告已生成", 3000)

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
    
    def _auto_fit_sector_view(self):
        """自动适应扇形视图"""
        try:
            if hasattr(self, 'dynamic_sector_widget') and self.dynamic_sector_widget:
                # 获取扇形视图的graphics_view
                if hasattr(self.dynamic_sector_widget, 'graphics_view'):
                    graphics_view = self.dynamic_sector_widget.graphics_view
                    
                    # 临时启用自动适应以进行初始设置
                    original_auto_fit = getattr(graphics_view, 'disable_auto_fit', False)
                    original_auto_center = getattr(graphics_view, 'disable_auto_center', False)
                    
                    graphics_view.disable_auto_fit = False
                    graphics_view.disable_auto_center = False
                    
                    # 适应视图
                    if hasattr(graphics_view, 'fit_in_view'):
                        graphics_view.fit_in_view()
                    elif hasattr(graphics_view, 'fit_to_window_width'):
                        graphics_view.fit_to_window_width()
                    
                    # 恢复原始设置（用于扇形偏移功能）
                    QTimer.singleShot(100, lambda: self._restore_sector_settings(graphics_view, original_auto_fit, original_auto_center))
                    
                    self.log_message("✅ 扇形视图已自动适应")
                    
        except Exception as e:
            self.log_message(f"⚠️ 自动适应扇形视图失败: {e}")
    
    def _restore_sector_settings(self, graphics_view, auto_fit, auto_center):
        """恢复扇形视图的原始设置"""
        graphics_view.disable_auto_fit = auto_fit
        graphics_view.disable_auto_center = auto_center

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

        # AI员工2号修改 - 注释更新
        # 按孔位ID排序，确保从C001R001开始顺序进行
        holes.sort(key=lambda h: h.hole_id)

        return holes

    # 模拟进度功能 - 已删除旧版本，使用蛇形双孔模拟

    def _start_snake_pattern_simulation(self):
        """开始蛇形双孔模拟进度"""
        if not self.hole_collection:
            QMessageBox.warning(self, "警告", "请先加载DXF文件")
            return

        # 如果已经在运行，则停止
        if hasattr(self, 'snake_simulation_running') and self.snake_simulation_running:
            self._stop_snake_simulation()
            return

        # 导入蛇形模拟类
        from src.modules.snake_pattern_simulation import SnakePatternSimulation
        
        # 创建蛇形模拟实例
        self.snake_simulator = SnakePatternSimulation(self.hole_collection)
        
        # 初始化模拟状态
        self.snake_simulation_running = True
        self.simulate_btn.setText("停止模拟")
        
        # 记录开始时间
        from datetime import datetime
        self.detection_start_time = datetime.now()
        self.detection_elapsed_seconds = 0
        
        # 显示演示序列
        demo_sequence = self.snake_simulator.get_demonstration_sequence(10)
        self.log_message("🐍 蛇形双孔模拟模式启动")
        self.log_message(f"📋 前10步预览:")
        for i, holes in enumerate(demo_sequence, 1):
            if len(holes) == 2:
                self.log_message(f"   步骤{i}: {holes[0]} + {holes[1]} (双孔)")
            else:
                self.log_message(f"   步骤{i}: {holes[0]} (单孔)")
        
        # 初始化定时器
        self.snake_timer = QTimer()
        self.snake_timer.timeout.connect(self._process_snake_simulation_step)
        
        # 设置定时器间隔为10秒（9.5秒蓝色 + 0.5秒更新）
        self.snake_timer.start(10000)  # 10秒
        
        # 立即执行第一步
        self._process_snake_simulation_step()
    
    def _stop_snake_simulation(self):
        """停止蛇形模拟"""
        if hasattr(self, 'snake_timer'):
            self.snake_timer.stop()
        
        self.snake_simulation_running = False
        self.simulate_btn.setText("使用模拟进度")
        self.log_message("⏹️ 停止蛇形双孔模拟")
        
        # 重置检测时间
        self.detection_start_time = None
        self.detection_elapsed_seconds = 0
    
    def _process_snake_simulation_step(self):
        """处理蛇形模拟的一步"""
        if not hasattr(self, 'snake_simulator') or not self.snake_simulation_running:
            return
        
        # 获取下一批要处理的孔位
        holes_to_process = self.snake_simulator.get_next_holes()
        
        if not holes_to_process:
            # 模拟完成
            self._stop_snake_simulation()
            self.log_message("✅ 蛇形双孔模拟完成")
            return
        
        # 获取进度信息
        progress_info = self.snake_simulator.get_progress_info()
        self.log_message(f"📊 进度: {progress_info['progress_percent']:.1f}% - 列{progress_info['current_col']} ({progress_info['direction']})")
        
        # 处理每个孔位
        valid_holes = []
        for hole_pos in holes_to_process:
            if self.snake_simulator.validate_hole_exists(hole_pos):
                valid_holes.append(hole_pos)
            else:
                self.log_message(f"⚠️ 孔位不存在: {hole_pos.hole_id}")
        
        if valid_holes:
            # 设置为蓝色（检测中）
            self._set_holes_processing(valid_holes)
            
            # 9.5秒后更新为最终颜色
            QTimer.singleShot(9500, lambda: self._update_holes_final_status(valid_holes))
        
        # 前进到下一个位置
        if not self.snake_simulator.advance_position():
            # 没有更多孔位了，下次定时器触发时会停止
            self.log_message("🏁 即将完成所有孔位检测")
    
    def _set_holes_processing(self, holes: List):
        """设置孔位为检测中状态（蓝色）"""
        from src.core_business.models.hole_data import HoleStatus
        
        hole_ids = [h.hole_id for h in holes]
        if len(hole_ids) == 2:
            self.log_message(f"🔵 开始检测: {hole_ids[0]} + {hole_ids[1]}")
        else:
            self.log_message(f"🔵 开始检测: {hole_ids[0]}")
        
        for hole_pos in holes:
            hole_id = hole_pos.hole_id
            if hole_id in self.hole_collection.holes:
                hole_data = self.hole_collection.holes[hole_id]
                hole_data.status = HoleStatus.PROCESSING
                
                # 更新图形显示
                if hasattr(self.graphics_view, 'hole_items') and hole_id in self.graphics_view.hole_items:
                    hole_item = self.graphics_view.hole_items[hole_id]
                    hole_item.update_status(HoleStatus.PROCESSING)
                    hole_item.update()
        
        # 强制刷新显示
        if hasattr(self, 'graphics_view'):
            self.graphics_view.viewport().update()
        
        self.update_status_display()
    
    def _update_holes_final_status(self, holes: List):
        """更新孔位到最终状态"""
        from src.core_business.models.hole_data import HoleStatus
        import random
        
        for hole_pos in holes:
            hole_id = hole_pos.hole_id
            if hole_id in self.hole_collection.holes:
                hole_data = self.hole_collection.holes[hole_id]
                
                # 生成随机结果
                rand_value = random.random()
                if rand_value < 0.995:  # 99.5%概率合格
                    final_status = HoleStatus.QUALIFIED
                    color_emoji = "🟢"
                elif rand_value < 0.9999:  # 0.49%概率异常
                    final_status = HoleStatus.DEFECTIVE
                    color_emoji = "🔴"
                else:  # 0.01%概率其他状态
                    other_statuses = [HoleStatus.BLIND, HoleStatus.TIE_ROD]
                    final_status = random.choice(other_statuses)
                    color_emoji = "🟡" if final_status == HoleStatus.BLIND else "🔵"
                
                # 更新状态
                hole_data.status = final_status
                
                # 更新图形显示
                if hasattr(self.graphics_view, 'hole_items') and hole_id in self.graphics_view.hole_items:
                    hole_item = self.graphics_view.hole_items[hole_id]
                    hole_item.update_status(final_status)
                    hole_item.update()
                
                self.log_message(f"{color_emoji} {hole_id}: 检测完成 → {final_status.value}")
        
        # 强制刷新显示
        if hasattr(self, 'graphics_view'):
            self.graphics_view.viewport().update()
        
        self.update_status_display()

    # V2模拟功能已删除，使用蛇形双孔模拟
    
    def _manual_sync_panorama_highlight(self, sector):
        """开始模拟进度 V2 - 按扇形顺序模拟"""
        if not self.hole_collection:
            QMessageBox.warning(self, "警告", "请先加载DXF文件")
            return

        if hasattr(self, 'simulation_running_v2') and self.simulation_running_v2:
            # 停止模拟
            if hasattr(self, 'simulation_timer_v2'):
                self.simulation_timer_v2.stop()
            if hasattr(self, 'batch_generation_timer'):
                self.batch_generation_timer.stop()
            if hasattr(self, 'render_timer'):
                self.render_timer.stop()
            self.simulation_running_v2 = False
            self.simulate_btn.setText("使用模拟进度")
            self.log_message("⏹️ 停止模拟进度 V2")
            
            # 重置批次显示状态
            self.current_batch_label.setText("检测批次: 已停止")
            self.batch_progress_label.setText("批次进度: 0/0")
            
            # 重置检测时间
            self.detection_start_time = None
            self.detection_elapsed_seconds = 0
            return

        # 初始化V2模拟
        self.simulation_running_v2 = True
        
        # 重置批次显示状态
        self.current_batch_label.setText("检测批次: 初始化中...")
        self.batch_progress_label.setText("批次进度: 0/0")
        self.simulation_index_v2 = 0
        
        # 重置检测时间相关变量
        self.detection_elapsed_seconds = 0
        
        # 初始化当前显示的扇形（如果还没有设置）
        if not hasattr(self, 'current_displayed_sector') or not self.current_displayed_sector:
            from src.core_business.graphics.sector_manager import SectorQuadrant
            self.current_displayed_sector = SectorQuadrant.SECTOR_1
        
        # 初始化扇形顺序模拟
        self._initialize_sector_simulation()
        
        # 确保图形视图引用正确
        if hasattr(self, 'dynamic_sector_display') and self.dynamic_sector_display:
            self.graphics_view = self.dynamic_sector_display.graphics_view
        
        # 强制加载完整数据集以确保所有孔位都有图形项
        if hasattr(self, 'graphics_view') and self.graphics_view and hasattr(self, 'hole_collection'):
            try:
                self.graphics_view.load_holes(self.hole_collection)
                self.log_message(f"✅ 模拟前完整数据集加载: {len(self.graphics_view.hole_items)} 个孔位")
                
                # 🔧 延迟确保图形项完全创建
                QTimer.singleShot(200, lambda: self._ensure_graphics_items_exist())
                self.log_message("⏳ 图形项验证将在200ms后执行")
            except Exception as e:
                self.log_message(f"❌ 模拟前数据加载失败: {e}")
        else:
            # 如果没有图形视图，延迟验证
            QTimer.singleShot(200, lambda: self._ensure_graphics_items_exist())

        # 初始化统计计数器
        self.v2_stats = {
            "合格": 0,
            "异常": 0,
            "盲孔": 0,
            "拉杆孔": 0
        }

        total_holes = len(self.holes_list_v2)
        self.log_message(f"🚀 开始模拟进度 V2 - 扇形顺序模式")
        self.log_message(f"🎯 将处理 {total_holes} 个孔位")
        self.log_message(f"⏱️ 检测频率: 100ms/孔位 (蓝色→最终颜色: 50ms)")
        self.log_message(f"🔄 模拟顺序: 扇形1 → 扇形2 → 扇形3 → 扇形4")
        self.log_message(f"📊 预期分布比例:")
        self.log_message(f"  🟢 合格: 99.5% (约 {int(total_holes * 0.995)} 个)")
        self.log_message(f"  🔴 异常: 0.49% (约 {int(total_holes * 0.0049)} 个)")
        self.log_message(f"  🟡🔵 其他: 0.01% (约 {int(total_holes * 0.0001)} 个)")

        # 开始连续模拟
        self._start_continuous_simulation()

        self.simulate_btn.setText("停止模拟")
    
    def _initialize_sector_simulation(self):
        """初始化连续模拟数据"""
        # 重置模拟索引
        self.simulation_index_v2 = 0
        self.batch_render_index = 0
        from src.core_business.graphics.sector_manager import SectorQuadrant
        
        # 确保扇形管理器存在
        if not hasattr(self, 'sector_manager') or not self.sector_manager:
            self.log_message("⚠️ 扇形管理器不存在，无法进行扇形顺序模拟")
            return
        
        # 扇形顺序
        self.sector_order = [
            SectorQuadrant.SECTOR_1,
            SectorQuadrant.SECTOR_2, 
            SectorQuadrant.SECTOR_3,
            SectorQuadrant.SECTOR_4
        ]
        
        # 按扇形组织孔位数据，但创建连续的检测序列
        self.sector_holes = {}
        self.sector_stats = {}
        self.holes_list_v2 = []  # 所有孔位的连续序列
        self.hole_to_sector_map = {}  # 孔位到扇形的映射
        
        for sector in self.sector_order:
            sector_holes = self.sector_manager.get_sector_holes(sector)
            # 使用智能螺旋排序创建连续的检测路径
            sector_holes = self._create_spiral_detection_path(sector_holes)
            
            self.sector_holes[sector] = sector_holes
            self.sector_stats[sector] = {"completed": 0, "total": len(sector_holes)}
            
            # 将扇形孔位添加到连续序列中
            for hole in sector_holes:
                self.holes_list_v2.append(hole)
                self.hole_to_sector_map[hole.hole_id] = sector
            
            self.log_message(f"📋 {sector.value}: {len(sector_holes)} 个孔位")

            # 调试：显示每个扇形的前几个孔位ID，验证排序
            if sector_holes:
                first_few = [h.hole_id for h in sector_holes[:5]]
                self.log_message(f"   🔍 {sector.value} 前5个孔位: {first_few}")
        
        # 模拟状态
        self.simulation_index_v2 = 0
        self.current_displayed_sector = None
        
        # 保持严格的扇形->行->列顺序，不进行全局优化
        # self.holes_list_v2 = self._optimize_global_detection_path(self.holes_list_v2)  # 注释掉全局优化

        self.log_message(f"🔄 V2模拟准备完成: 共 {len(self.holes_list_v2)} 个孔位，严格按扇形->行->列顺序")
        
        # 显示调整后的参数总结
        self._log_detection_parameters()
        
        # 验证路径连续性
        self._verify_detection_path_continuity(self.holes_list_v2)
    
    def _create_spiral_detection_path(self, holes):
        """创建扇形区域内严格按行->列顺序的检测路径"""
        if not holes:
            return holes

        # 严格按行->列顺序，支持蛇形扫描模式
        # 核心思路：先精确按行分组，再在每行内按列排序

        try:
            # 第一步：基于Y坐标进行精确行分组
            # 使用更小的容差确保行分组的准确性
            tolerance = 5.0  # 减小容差，提高行分组精度
            
            # 按Y坐标排序所有孔位
            y_sorted_holes = sorted(holes, key=lambda h: h.center_y)
            
            # 动态计算行间距
            if len(y_sorted_holes) > 1:
                y_gaps = []
                for i in range(1, len(y_sorted_holes)):
                    gap = abs(y_sorted_holes[i].center_y - y_sorted_holes[i-1].center_y)
                    if gap > tolerance:  # 只记录大于容差的间距
                        y_gaps.append(gap)
                
                if y_gaps:
                    # 使用最小显著间距的一半作为动态容差
                    min_gap = min(y_gaps)
                    tolerance = min(tolerance, min_gap * 0.6)
            
            # 按行分组
            rows = []
            if y_sorted_holes:
                current_row = [y_sorted_holes[0]]
                
                for hole in y_sorted_holes[1:]:
                    # 计算当前行的平均Y坐标
                    avg_y = sum(h.center_y for h in current_row) / len(current_row)
                    
                    # 判断是否应该加入当前行
                    if abs(hole.center_y - avg_y) <= tolerance:
                        current_row.append(hole)
                    else:
                        # 开始新行
                        if current_row:
                            rows.append(current_row)
                        current_row = [hole]
                
                # 添加最后一行
                if current_row:
                    rows.append(current_row)

            # 第二步：行间排序 - 严格按Y坐标从上到下
            rows.sort(key=lambda row: min(h.center_y for h in row))

            # 第三步：构建严格的行->列蛇形扫描路径
            sorted_holes = []
            for row_index, row_holes in enumerate(rows):
                # 在每行内按X坐标排序
                if row_index % 2 == 0:
                    # 偶数行：从左到右
                    row_holes.sort(key=lambda h: h.center_x)
                else:
                    # 奇数行：从右到左（蛇形路径）
                    row_holes.sort(key=lambda h: h.center_x, reverse=True)

                sorted_holes.extend(row_holes)

            self.log_message(f"📐 扇形内严格排序: {len(holes)} 个孔位 -> {len(rows)} 行，蛇形扫描模式")
            
            # 调试信息：显示前几行的排序情况
            for i, row in enumerate(rows[:3]):  # 只显示前3行
                x_coords = [f"{h.center_x:.0f}" for h in row]
                direction = "→" if i % 2 == 0 else "←"
                self.log_message(f"  第{i+1}行 {direction}: [{', '.join(x_coords)}]")
            
            return sorted_holes

        except Exception as e:
            self.log_message(f"⚠️ 行列排序失败，使用简单排序: {e}")
            # 备用方案：简单的行列排序（不使用蛇形）
            return sorted(holes, key=lambda h: (h.center_y, h.center_x))
    
    def _optimize_global_detection_path(self, all_holes):
        """全局连续无漏检优化"""
        if len(all_holes) <= 1:
            return all_holes
        
        # 全局蛇形扫描：将所有孔位统一处理，确保整体连续
        try:
            # 对所有孔位进行全局蛇形扫描（可调参数2）- 进一步降低
            global_tolerance = 6  # 进一步激进降低全局容差，从12px降到6px
            rows = self._group_holes_into_rows(all_holes, tolerance=global_tolerance)
            
            # 行与行之间从上到下排序
            rows.sort(key=lambda row: min(h.center_y for h in row))
            
            # 全局蛇形路径
            optimized_holes = []
            for i, row_holes in enumerate(rows):
                if i % 2 == 0:
                    # 偶数行：从左到右
                    row_holes.sort(key=lambda h: h.center_x)
                else:
                    # 奇数行：从右到左
                    row_holes.sort(key=lambda h: h.center_x, reverse=True)
                
                optimized_holes.extend(row_holes)
            
            self.log_message(f"🌐 全局蛇形扫描: {len(all_holes)} 个孔位 -> {len(rows)} 行，容差={global_tolerance}px，整体连续无跳跃")
            return optimized_holes
            
        except Exception as e:
            self.log_message(f"⚠️ 全局蛇形扫描失败，使用备用方案: {e}")
            # 备用方案：简单的Y坐标排序
            return sorted(all_holes, key=lambda h: (h.center_y, h.center_x))
    
    def _group_holes_into_columns(self, holes, tolerance=10):
        """将孔位按X坐标分组为列（智能自适应分组）"""
        if not holes:
            return []
        
        # 按X坐标排序
        sorted_holes = sorted(holes, key=lambda h: h.center_x)
        
        # 自适应计算最优容差
        if len(sorted_holes) > 1:
            # 计算所有相邻孔位的X间距
            x_distances = []
            for i in range(1, len(sorted_holes)):
                dist = abs(sorted_holes[i].center_x - sorted_holes[i-1].center_x)
                if dist > 0:  # 过滤重叠孔位
                    x_distances.append(dist)
            
            if x_distances:
                # 使用最小间距的1.0倍作为动态容差（可调参数4），极度激进的列分组
                min_distance = min(x_distances)
                adaptive_tolerance = min(tolerance, min_distance * 1.0)  # 从1.2进一步降低到1.0
                tolerance = max(2, adaptive_tolerance)  # 最小2像素，从4进一步降低到2
        
        columns = []
        current_column = [sorted_holes[0]]
        
        for hole in sorted_holes[1:]:
            # 检查是否应该加入当前列
            # 不仅考虑与最后一个孔位的距离，还考虑与列中所有孔位的平均X坐标
            if current_column:
                avg_x = sum(h.center_x for h in current_column) / len(current_column)
                distance_to_avg = abs(hole.center_x - avg_x)
                distance_to_last = abs(hole.center_x - current_column[-1].center_x)
                
                # 如果与平均X坐标或最后孔位的距离都在容差内，加入当前列
                if distance_to_avg <= tolerance or distance_to_last <= tolerance:
                    current_column.append(hole)
                else:
                    # 否则开始新列
                    columns.append(current_column)
                    current_column = [hole]
            else:
                current_column.append(hole)
        
        # 添加最后一列
        if current_column:
            columns.append(current_column)
        
        return columns
    
    def _group_holes_into_rows(self, holes, tolerance=15):
        """将孔位按Y坐标分组为行（蛇形扫描专用）"""
        if not holes:
            return []
        
        # 按Y坐标排序
        sorted_holes = sorted(holes, key=lambda h: h.center_y)
        
        # 自适应计算最优容差
        if len(sorted_holes) > 1:
            # 计算所有相邻孔位的Y间距
            y_distances = []
            for i in range(1, len(sorted_holes)):
                dist = abs(sorted_holes[i].center_y - sorted_holes[i-1].center_y)
                if dist > 0:  # 过滤重叠孔位
                    y_distances.append(dist)
            
            if y_distances:
                # 使用最小间距的1.2倍作为动态容差（可调参数3），极度激进的分组
                min_distance = min(y_distances)
                adaptive_tolerance = min(tolerance, min_distance * 1.2)  # 从1.5进一步降低到1.2
                tolerance = max(3, adaptive_tolerance)  # 最小3像素，从5进一步降低到3
        
        rows = []
        current_row = [sorted_holes[0]]
        
        for hole in sorted_holes[1:]:
            # 检查是否应该加入当前行
            if current_row:
                avg_y = sum(h.center_y for h in current_row) / len(current_row)
                distance_to_avg = abs(hole.center_y - avg_y)
                distance_to_last = abs(hole.center_y - current_row[-1].center_y)
                
                # 更宽松的判断条件（可调参数5）：进一步降低阈值避免漏检
                # 只要与平均Y坐标OR最后孔位的距离在容差内，就加入当前行
                relaxed_tolerance = tolerance * 1.5  # 从20%增加到50%的宽松度
                if distance_to_avg <= relaxed_tolerance or distance_to_last <= relaxed_tolerance:
                    current_row.append(hole)
                else:
                    # 否则开始新行
                    rows.append(current_row)
                    current_row = [hole]
            else:
                current_row.append(hole)
        
        # 添加最后一行
        if current_row:
            rows.append(current_row)
        
        return rows
    
    def _log_detection_parameters(self):
        """记录所有可调的检测算法参数"""
        self.log_message("🔧 检测算法可调参数总结(极度激进版):")
        self.log_message("  参数1: 扇形基础容差 = 4px (原15px, 降幅73%)")
        self.log_message("  参数2: 全局基础容差 = 6px (原20px, 降幅70%)")
        self.log_message("  参数3: 行分组倍数 = 1.2倍最小间距 (原2.0倍)")
        self.log_message("  参数4: 列分组倍数 = 1.0倍最小间距 (原1.5倍)")
        self.log_message("  参数5: 宽松判断倍数 = 1.5倍容差 (原无, 增加50%)")
        self.log_message("  参数6: 最小行容差 = 3px (原8px, 降幅62.5%)")
        self.log_message("  参数7: 最小列容差 = 2px (原5px, 降幅60%)")
        self.log_message("💡 极度激进分组策略：彻底消除规则网格漏检！")
    
    def _create_nearest_neighbor_path(self, holes):
        """使用改进的最近邻算法创建连续的检测路径"""
        if not holes:
            return []
        
        import math
        
        # 从左上角开始
        start_hole = min(holes, key=lambda h: h.center_x + h.center_y)
        ordered_path = [start_hole]
        remaining_holes = [h for h in holes if h != start_hole]
        
        current_hole = start_hole
        
        while remaining_holes:
            best_hole = None
            best_score = float('inf')
            
            for candidate in remaining_holes:
                # 计算基础距离
                distance = math.sqrt((candidate.center_x - current_hole.center_x)**2 + 
                                   (candidate.center_y - current_hole.center_y)**2)
                
                # 添加方向偏好：优先选择右侧和下方的孔位
                direction_penalty = 0
                dx = candidate.center_x - current_hole.center_x
                dy = candidate.center_y - current_hole.center_y
                
                # 如果候选孔位在左侧，增加少量惩罚
                if dx < 0:
                    direction_penalty += abs(dx) * 0.1
                
                # 如果候选孔位在上方，增加更多惩罚
                if dy < 0:
                    direction_penalty += abs(dy) * 0.2
                
                # 计算综合得分
                total_score = distance + direction_penalty
                
                if total_score < best_score:
                    best_score = total_score
                    best_hole = candidate
            
            if best_hole:
                ordered_path.append(best_hole)
                remaining_holes.remove(best_hole)
                current_hole = best_hole
            else:
                # 备用方案：选择最近的孔位
                next_hole = min(remaining_holes, key=lambda h: 
                    math.sqrt((h.center_x - current_hole.center_x)**2 + 
                             (h.center_y - current_hole.center_y)**2))
                ordered_path.append(next_hole)
                remaining_holes.remove(next_hole)
                current_hole = next_hole
        
        return ordered_path
    
    def _verify_detection_path_continuity(self, holes_path):
        """验证检测路径的连续性"""
        if len(holes_path) <= 1:
            return
        
        import math
        
        distances = []
        total_distance = 0
        
        for i in range(1, len(holes_path)):
            prev_hole = holes_path[i-1]
            curr_hole = holes_path[i]
            distance = math.sqrt((curr_hole.center_x - prev_hole.center_x)**2 + 
                               (curr_hole.center_y - prev_hole.center_y)**2)
            distances.append(distance)
            total_distance += distance
        
        if distances:
            avg_distance = total_distance / len(distances)
            max_distance = max(distances)
            
            # 统计大跳跃（超过平均距离3倍的）
            large_jumps = [d for d in distances if d > avg_distance * 3]
            
            self.log_message(f"🔍 路径连续性验证:")
            self.log_message(f"  📏 平均距离: {avg_distance:.1f}, 最大距离: {max_distance:.1f}")
            self.log_message(f"  🦘 大跳跃次数: {len(large_jumps)} ({len(large_jumps)/len(distances)*100:.1f}%)")
            
            if len(large_jumps) == 0:
                self.log_message(f"  ✅ 检测路径连续性良好，无明显跳跃")
            else:
                self.log_message(f"  ⚠️ 检测路径存在 {len(large_jumps)} 个大跳跃，可能有漏检风险")

    def _start_continuous_simulation(self):
        """开始连续模拟所有孔位"""
        if not self.holes_list_v2:
            self.log_message("❌ V2: 没有准备好的孔位数据")
            return
        
        self.log_message(f"🚀 开始连续模拟 {len(self.holes_list_v2)} 个孔位")
        
        # 重置模拟状态
        self.simulation_index_v2 = 0
        self.current_displayed_sector = None
        
        # 初始化批量数据管理器
        if not hasattr(self, 'batch_data_manager'):
            try:
                # 尝试相对导入
                import sys
                import os
                models_path = os.path.join(os.path.dirname(__file__), 'models')
                sys.path.insert(0, models_path)
                from batch_data_manager import BatchDataManager
                print(f"✅ [批量数据] 成功导入 BatchDataManager")
            except ImportError as e:
                print(f"❌ [批量数据] 导入失败: {e}")
                # 创建一个简单的替代品
                class DummyBatchDataManager:
                    def reset_simulation(self): pass
                    def generate_simulation_batch(self, *args): return None
                BatchDataManager = DummyBatchDataManager
                print(f"⚠️ [批量数据] 使用替代实现")
            
            # 生成检测批次ID
            from datetime import datetime
            inspection_batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            product_id = self.current_product.model_name if self.current_product else "DefaultProduct"
            
            self.batch_data_manager = BatchDataManager(
                product_id=product_id,
                inspection_batch_id=inspection_batch_id
            )
        
        # 重置模拟状态，确保全局计数器从0开始
        self.batch_data_manager.reset_simulation()
        
        # 创建两个定时器：批量数据生成(1000ms) + 渲染分发(100ms)
        if not hasattr(self, 'batch_generation_timer'):
            self.batch_generation_timer = QTimer()
            self.batch_generation_timer.timeout.connect(self._generate_batch_data)
            
        if not hasattr(self, 'render_timer'):
            self.render_timer = QTimer()
            self.render_timer.timeout.connect(self._render_next_hole)
        
        self.log_message("🚀 启动新的批量渲染模拟 (1000ms批量 + 100ms渲染)")
        
        # 🔧 同步启动两个定时器，确保图形视图完全准备好且数据不丢失
        # 延迟500ms同时启动批量数据生成和渲染定时器
        QTimer.singleShot(500, lambda: self.batch_generation_timer.start(1000))
        QTimer.singleShot(500, lambda: self.render_timer.start(100))
        self.log_message("⏳ 批量数据生成和渲染定时器将在500ms后同步启动，确保图形视图完全准备好")
        
    def _start_next_sector_simulation(self):
        """开始下一个扇形的模拟"""
        from src.core_business.graphics.sector_manager import SectorQuadrant
        
        if self.current_sector_index >= len(self.sector_order):
            # 所有扇形完成，结束模拟
            self._complete_all_sectors_simulation()
            return
        
        current_sector = self.sector_order[self.current_sector_index]
        sector_holes = self.sector_holes[current_sector]
        
        if not sector_holes:
            self.log_message(f"⚠️ {current_sector.value} 没有孔位，跳过")
            self.current_sector_index += 1
            self._start_next_sector_simulation()
            return
        
        self.log_message(f"🎯 开始模拟 {current_sector.value} ({len(sector_holes)} 个孔位)")
        
        # 切换到当前扇形视图（只切换一次！）
        if hasattr(self, 'dynamic_sector_display') and self.dynamic_sector_display:
            self.log_message(f"🎯 [模拟] 即将切换到扇形: {current_sector.value}")
            self.dynamic_sector_display.switch_to_sector(current_sector)
            self.log_message(f"🔄 [模拟] 已调用切换到 {current_sector.value} 视图")
            
            # 🔧 FIX: 合并多个定时器为单一操作，防止视图变换竞态条件
            # 使用单一定时器完成所有后续操作，避免扇形→圆形→扇形的显示异常
            def complete_sector_switch():
                try:
                    # 手动触发全景预览同步
                    self._manual_sync_panorama(current_sector)
                    
                    # 适应视图到当前扇形区域
                    self._fit_view_to_current_sector(current_sector)
                    
                    # 确保所有图形项都完全准备好
                    self._ensure_graphics_items_exist()
                    
                    self.log_message(f"✅ [模拟] 扇形 {current_sector.value} 切换完成")
                except Exception as e:
                    self.log_message(f"❌ [模拟] 扇形切换后续操作失败: {e}")
            
            # 使用单一定时器，确保操作的原子性
            QTimer.singleShot(300, complete_sector_switch)
        
        # 设置当前扇形的孔位列表用于模拟
        self.holes_list_v2 = sector_holes
        self.current_sector_hole_index = 0
        self.simulation_index_v2 = 0
        
        # 创建或重启定时器
        if not hasattr(self, 'simulation_timer_v2'):
            self.simulation_timer_v2 = QTimer()
            self.simulation_timer_v2.timeout.connect(self._update_simulation_v2)
        
        # 设置为100ms间隔，符合日志中的说明
        self.simulation_timer_v2.start(100)
        
    def _complete_current_sector(self):
        """完成当前扇形的模拟"""
        current_sector = self.sector_order[self.current_sector_index]
        completed_holes = self.sector_stats[current_sector]["completed"] 
        total_holes = self.sector_stats[current_sector]["total"]
        
        self.log_message(f"✅ {current_sector.value} 模拟完成!")
        self.log_message(f"📊 完成进度: {completed_holes}/{total_holes} (100%)")
        
        # 移动到下一个扇形
        self.current_sector_index += 1
        
        # 短暂停顿后开始下一个扇形
        QTimer.singleShot(500, self._start_next_sector_simulation)
        
    def _complete_all_sectors_simulation(self):
        """完成所有扇形的模拟"""
        if hasattr(self, 'simulation_timer_v2'):
            self.simulation_timer_v2.stop()
        if hasattr(self, 'batch_generation_timer'):
            self.batch_generation_timer.stop()
        if hasattr(self, 'render_timer'):
            self.render_timer.stop()
        
        self.simulation_running_v2 = False
        self.simulate_btn.setText("使用模拟进度")
        
        # 显示最终统计结果
        total = sum(self.v2_stats.values())
        self.log_message("🎉 所有扇形模拟完成!")
        self.log_message("📊 最终统计结果:")
        
        for sector in self.sector_order:
            stats = self.sector_stats[sector]
            self.log_message(f"  🔹 {sector.value}: {stats['completed']}/{stats['total']} 个孔位")

        for status, count in self.v2_stats.items():
            percentage = (count / total * 100) if total > 0 else 0
            emoji_map = {"合格": "🟢", "异常": "🔴", "盲孔": "🟡", "拉杆孔": "🔵"}
            emoji = emoji_map.get(status, "⚫")
            self.log_message(f"  {emoji} {status}: {count} 个 ({percentage:.2f}%)")

        # 显示合格率
        qualified_rate = (self.v2_stats["合格"] / total * 100) if total > 0 else 0
        self.log_message(f"🎯 总合格率: {qualified_rate:.2f}%")
    
    def _fit_view_to_current_sector(self, sector):
        """让视图适应当前扇形区域"""
        try:
            if hasattr(self, 'graphics_view') and self.graphics_view:
                # 切换到宏观视图并适应当前显示的内容
                self.graphics_view.switch_to_macro_view()
                self.graphics_view.fit_in_view()
                self.log_message(f"✅ 视图已适应到 {sector.value} 区域")
        except Exception as e:
            self.log_message(f"⚠️ 视图适应失败: {e}")
    
    def _ensure_graphics_items_exist(self):
        """确保图形项存在，如果不存在则重新创建"""
        # 首先确保graphics_view引用正确
        if hasattr(self, 'dynamic_sector_display') and self.dynamic_sector_display:
            self.graphics_view = self.dynamic_sector_display.graphics_view
        
        if not hasattr(self, 'graphics_view') or not self.graphics_view:
            self.log_message("⚠️ 图形视图不存在，跳过图形项验证")
            return
        
        # 检查当前图形项数量
        current_items_count = len(self.graphics_view.hole_items) if hasattr(self.graphics_view, 'hole_items') else 0
        expected_count = len(self.holes_list_v2) if hasattr(self, 'holes_list_v2') else 0
        
        self.log_message(f"📊 图形项数量检查: 当前={current_items_count}, 期望={expected_count}")
        
        # 如果没有图形项或数量严重不匹配，先加载完整数据
        if current_items_count == 0 or current_items_count < expected_count * 0.8:
            self.log_message(f"⚠️ 图形项严重缺失，重新加载完整数据集")
            try:
                # 先加载完整数据确保所有孔位都有图形项
                self.graphics_view.load_holes(self.hole_collection)
                self.log_message(f"✅ 完整数据集重新加载完成")
                
                # 再次检查
                new_count = len(self.graphics_view.hole_items)
                self.log_message(f"📊 重新加载后图形项数量: {new_count}")
                
            except Exception as e:
                self.log_message(f"❌ 图形项重新加载失败: {e}")
        else:
            # 检查是否有缺失的特定项目
            missing_items = []
            if hasattr(self, 'holes_list_v2'):
                for hole in self.holes_list_v2:
                    if hole.hole_id not in self.graphics_view.hole_items:
                        missing_items.append(hole.hole_id)
            
            if missing_items:
                self.log_message(f"⚠️ 发现 {len(missing_items)} 个特定图形项缺失: {missing_items[:5]}...")
                try:
                    # 重新加载完整数据集
                    self.graphics_view.load_holes(self.hole_collection)
                    self.log_message("✅ 特定图形项修复完成")
                except Exception as e:
                    self.log_message(f"❌ 特定图形项修复失败: {e}")
            else:
                self.log_message(f"✅ 所有 {expected_count} 个图形项验证通过")

    def _generate_batch_data(self):
        """生成批量数据 (1000ms周期)"""
        if not hasattr(self, 'holes_list_v2') or not self.holes_list_v2:
            return
            
        # 检查是否还有未处理的孔位
        remaining_holes = len(self.holes_list_v2) - self.simulation_index_v2
        if remaining_holes <= 0:
            self.log_message("🏁 所有孔位处理完成，停止批量生成")
            self.batch_generation_timer.stop()
            return
        
        # 获取下一批10个孔位
        batch_size = min(10, remaining_holes)
        holes_batch = self.holes_list_v2[self.simulation_index_v2:self.simulation_index_v2 + batch_size]
        
        # 确定当前扇形
        current_hole = holes_batch[0]
        current_sector = self._get_hole_sector(current_hole)
        
        # 生成批量数据
        batch = self.batch_data_manager.generate_simulation_batch(holes_batch, current_sector.value)
        
        self.log_message(f"📦 生成批量数据: {batch.batch_id}, {len(batch.holes)}个孔位, 扇形: {current_sector.value}")
        
        # 更新UI中的批次信息
        self._update_batch_display(batch)
        
        # 更新索引
        self.simulation_index_v2 += batch_size
    
    def _update_batch_display(self, batch):
        """更新UI中的批次信息显示"""
        try:
            # 更新当前批次信息
            batch_display_id = batch.batch_id.replace("batch_", "").replace("_", "-")
            self.current_batch_label.setText(f"检测批次: {batch_display_id}")
            
            # 更新批次进度
            if hasattr(self, 'batch_data_manager'):
                progress = self.batch_data_manager.get_rendering_progress()
                current_index = self.batch_data_manager.current_render_index
                total_items = len(self.batch_data_manager.render_queue)
                self.batch_progress_label.setText(f"批次进度: {current_index}/{total_items}")
                
                # 如果批次完成，显示完成状态
                if self.batch_data_manager.is_batch_complete():
                    self.current_batch_label.setText(f"检测批次: {batch_display_id} (已完成)")
                    
        except Exception as e:
            print(f"❌ [批次显示] 更新失败: {e}")
    
    def _render_next_hole(self):
        """渲染下一个孔位 (100ms周期)"""
        if not hasattr(self, 'batch_data_manager'):
            return
            
        # 🔧 检查图形视图是否准备好
        if not hasattr(self, 'graphics_view') or not self.graphics_view:
            return
            
        # 🔧 检查图形项是否存在，如果不存在则跳过此次渲染
        if not hasattr(self.graphics_view, 'hole_items') or not self.graphics_view.hole_items:
            return
            
        # 获取下一个要渲染的孔位
        render_item = self.batch_data_manager.get_next_render_item()
        if not render_item:
            # 当前批次渲染完成，等待下一批次
            return
        
        hole_id = render_item.hole_id
        
        # 智能扇形切换
        from src.core_business.graphics.sector_manager import SectorQuadrant
        try:
            current_sector = SectorQuadrant(render_item.sector)
            self._handle_sector_switching(current_sector)
        except:
            self.log_message(f"⚠️ 扇形解析失败: {render_item.sector}")
            current_sector = SectorQuadrant.SECTOR_1  # 默认扇形
        
        # 检查图形项是否存在
        # 处理ID格式不匹配问题
        original_hole_id = hole_id
        if hole_id not in self.graphics_view.hole_items:
            # 尝试使用实际存在的孔位ID
            available_items = list(self.graphics_view.hole_items.items())
            if available_items:
                # 根据模拟索引选择对应的实际孔位
                actual_index = self.simulation_hole_index % len(available_items)
                hole_id, hole_item = available_items[actual_index]
                self.log_message(f"📝 ID映射: {original_hole_id} -> {hole_id}")
            else:
                self.log_message(f"⚠️ 没有可用的图形项")
                self.simulation_hole_index += 1
                return
        
        if hole_id not in self.graphics_view.hole_items:
            # 添加调试信息
            available_ids = list(self.graphics_view.hole_items.keys())[:5]  # 只取前5个
            self.log_message(f"⚠️ 图形项不存在 {hole_id}")
            self.log_message(f"🔍 可用的前5个图形项ID: {available_ids}")
            self._reload_current_sector()
            if hole_id not in self.graphics_view.hole_items:
                self.log_message(f"❌ 图形项 {hole_id} 仍然不存在，跳过")
                return

        # 渲染孔位状态
        hole_item = self.graphics_view.hole_items[hole_id]
        color = self._get_status_color(render_item.status)
        
        # 更新批次进度显示
        if hasattr(self, 'batch_data_manager'):
            current_index = self.batch_data_manager.current_render_index
            total_items = len(self.batch_data_manager.render_queue)
            self.batch_progress_label.setText(f"批次进度: {current_index}/{total_items}")
        
        try:
            from PySide6.QtGui import QBrush
            hole_item.setBrush(QBrush(color))
            
            # 只在调试时显示详细渲染信息
            if not hasattr(self, '_render_count'):
                self._render_count = 0
            self._render_count += 1
            
            # 每10个孔位显示一次进度
            if self._render_count % 10 == 0:
                self.log_message(f"🎨 已渲染 {self._render_count} 个孔位 (最新: {hole_id}, {render_item.status})")
            
            # 同步到全景图 - 使用统一的批量更新机制
            self._synchronize_panorama_status(hole_id, render_item.status, color)
            
            # 更新在HoleCollection中的状态
            if self.hole_collection and hole_id in self.hole_collection.holes:
                from src.core_business.models.hole_data import HoleStatus
                new_status = HoleStatus(render_item.status)
                self.hole_collection.holes[hole_id].status = new_status
                self.log_message(f"✅ 更新孔位状态: {hole_id} -> {render_item.status}")
                
                # 更新sector_manager中的状态
                if self.sector_manager:
                    self.sector_manager.update_hole_status(hole_id, new_status)
            
            # 更新状态统计显示
            self.update_status_display()
            
            # 启动检测时间计时器（如果还没有启动）
            if not self.detection_start_time:
                from datetime import datetime
                self.detection_start_time = datetime.now()
                self.log_message("🕐 开始检测时间计时")
            
            # 更新选中孔位的信息显示
            if self.selected_hole and self.selected_hole.hole_id == hole_id:
                self.selected_hole.status = HoleStatus(render_item.status)
                self.update_selected_hole_info()
            
            # 更新选中扇形的统计信息
            if hasattr(self, 'current_displayed_sector') and self.current_displayed_sector == current_sector:
                self._update_sector_stats_display(current_sector)
            
        except Exception as e:
            self.log_message(f"❌ 渲染失败 {hole_id}: {e}")
    
    def _get_status_color(self, status: str):
        """根据状态获取颜色"""
        from PySide6.QtGui import QColor
        status_colors = {
            "processing": QColor(76, 175, 80),    # 绿色 - 直接显示最终结果，不显示中间状态
            "qualified": QColor(76, 175, 80),     # 绿色 - 合格
            "defective": QColor(244, 67, 54),     # 红色 - 不合格
            "pending": QColor(158, 158, 158),     # 灰色 - 待检
            "unknown": QColor(158, 158, 158)      # 灰色 - 未知
        }
        return status_colors.get(status, status_colors["unknown"])
    
    def _reload_current_sector(self):
        """重新加载当前扇形"""
        if hasattr(self, 'current_displayed_sector') and self.current_displayed_sector:
            try:
                self.dynamic_sector_display.switch_to_sector(self.current_displayed_sector)
                self.log_message(f"✅ 重新加载扇形: {self.current_displayed_sector.value}")
            except Exception as e:
                self.log_message(f"❌ 扇形重新加载失败: {e}")

    def _handle_sector_switching(self, target_sector):
        """处理扇形切换逻辑"""
        if self.current_displayed_sector != target_sector:
            try:
                self.dynamic_sector_display.switch_to_sector(target_sector)
                self.current_displayed_sector = target_sector
                self.log_message(f"🔄 智能切换到扇形: {target_sector.value}")
                
                # 手动同步全景预览
                from PySide6.QtCore import QTimer
                QTimer.singleShot(50, lambda: self._manual_sync_panorama(target_sector))
                
                # 更新扇形统计信息
                QTimer.singleShot(100, lambda: self._update_sector_stats_display(target_sector))
                
            except Exception as e:
                self.log_message(f"❌ 扇形切换失败: {e}")

    def _get_hole_sector(self, hole):
        """获取孔位所属的扇形"""
        from src.core_business.graphics.sector_manager import SectorQuadrant
        import math
        
        # 使用简单的坐标方式确定扇形，与sector_manager逻辑一致
        if not hasattr(self, 'hole_collection') or not self.hole_collection:
            # 默认返回SECTOR_1
            return SectorQuadrant.SECTOR_1
        
        try:
            # 获取数据边界
            bounds = self.hole_collection.get_bounds()
            center_x = (bounds[0] + bounds[2]) / 2
            center_y = (bounds[1] + bounds[3]) / 2
            
            # 计算相对于中心的坐标
            dx = hole.center_x - center_x
            dy = hole.center_y - center_y
            
            # 使用象限划分
            if dx >= 0 and dy >= 0:
                return SectorQuadrant.SECTOR_1  # 右上
            elif dx < 0 and dy >= 0:
                return SectorQuadrant.SECTOR_2  # 左上
            elif dx < 0 and dy < 0:
                return SectorQuadrant.SECTOR_3  # 左下
            else:
                return SectorQuadrant.SECTOR_4  # 右下
                
        except Exception as e:
            self.log_message(f"⚠️ 扇形计算失败: {e}")
            return SectorQuadrant.SECTOR_1

    def _synchronize_panorama_status(self, hole_id: str, status: str, color):
        """统一的全景图同步机制（包含侧边栏全景图和小型全景图）"""
        print(f"🔄 [调试] _synchronize_panorama_status 被调用: {hole_id} -> {status}")
        print(f"🔍 [调试] 参数类型: hole_id={type(hole_id)}, status={type(status)}, color={type(color)}")
        
        # 调试：检查主要组件状态
        print(f"📊 [调试] 组件状态检查:")
        print(f"  - hasattr(self, 'sidebar_panorama'): {hasattr(self, 'sidebar_panorama')}")
        print(f"  - self.sidebar_panorama is not None: {getattr(self, 'sidebar_panorama', None) is not None}")
        print(f"  - hasattr(self, 'dynamic_sector_display'): {hasattr(self, 'dynamic_sector_display')}")
        print(f"  - self.dynamic_sector_display is not None: {getattr(self, 'dynamic_sector_display', None) is not None}")
        
        try:
            # 将状态转换为HoleStatus
            from src.core_business.models.hole_data import HoleStatus
            
            status_mapping = {
                "processing": HoleStatus.PROCESSING,
                "qualified": HoleStatus.QUALIFIED,
                "defective": HoleStatus.DEFECTIVE,
                "pending": HoleStatus.PENDING
            }
            
            hole_status = status_mapping.get(status, HoleStatus.PENDING)
            
            # 同步到侧边栏全景图
            if hasattr(self, 'sidebar_panorama') and self.sidebar_panorama:
                self.sidebar_panorama.update_hole_status(hole_id, hole_status)
            
            # 同步到小型全景图（关键修复！）
            if hasattr(self, 'dynamic_sector_display') and self.dynamic_sector_display:
                if hasattr(self.dynamic_sector_display, 'update_mini_panorama_hole_status'):
                    self.dynamic_sector_display.update_mini_panorama_hole_status(hole_id, hole_status)
                    
                    # 添加调试日志确认调用
                    if hasattr(self, '_mini_sync_counter'):
                        self._mini_sync_counter += 1
                    else:
                        self._mini_sync_counter = 1
                    
                    # 每5次输出一次小型全景图同步信息
                    if self._mini_sync_counter % 5 == 0:
                        print(f"🔗 [同步-小型] 主视图 -> 小型全景图: 已同步 {self._mini_sync_counter} 个孔位 (最新: {hole_id} -> {status})")
                else:
                    print(f"❌ [同步-小型] dynamic_sector_display 没有 update_mini_panorama_hole_status 方法")
            else:
                print(f"❌ [同步-小型] dynamic_sector_display 不存在")
            
            # 添加调试日志（减少频率）
            if hasattr(self, '_sync_debug_counter'):
                self._sync_debug_counter += 1
            else:
                self._sync_debug_counter = 1
            
            # 只每10次输出一次调试信息
            if self._sync_debug_counter % 10 == 0:
                print(f"🔗 [同步] 主视图 -> 全景图: 已同步 {self._sync_debug_counter} 个孔位")
            
        except Exception as e:
            # 减少错误日志频率
            if not hasattr(self, '_sync_error_count'):
                self._sync_error_count = 0
            self._sync_error_count += 1
            if self._sync_error_count <= 5:  # 只显示前5个错误
                self.log_message(f"❌ 全景图同步失败 {hole_id}: {e}")
            elif self._sync_error_count == 6:
                self.log_message("❌ 全景图同步错误过多，后续错误将被静默处理")

    def _update_simulation_v2(self):
        """更新模拟进度 V2 - 连续模拟所有孔位"""
        if self.simulation_index_v2 >= len(self.holes_list_v2):
            # 所有孔位完成，结束模拟
            self.simulation_timer_v2.stop()
            if hasattr(self, 'batch_generation_timer'):
                self.batch_generation_timer.stop()
            if hasattr(self, 'render_timer'):
                self.render_timer.stop()
            self.simulation_running_v2 = False
            self.simulate_btn.setText("使用模拟进度")
            self.log_message("✅ 连续模拟 V2 完成")
            return

        # 获取当前孔位
        current_hole = self.holes_list_v2[self.simulation_index_v2]
        hole_id = current_hole.hole_id

        # 智能扇形切换：根据当前孔位确定应该显示的扇形
        if hasattr(self, 'hole_to_sector_map') and hole_id in self.hole_to_sector_map:
            current_hole_sector = self.hole_to_sector_map[hole_id]
            
            # 检查是否需要切换扇形显示
            if self.current_displayed_sector != current_hole_sector:
                self.current_displayed_sector = current_hole_sector
                
                # 切换到新扇形视图
                if hasattr(self, 'dynamic_sector_display') and self.dynamic_sector_display:
                    self.dynamic_sector_display.switch_to_sector(current_hole_sector)
                    self.log_message(f"🔄 智能切换到扇形: {current_hole_sector.value}")
                    
                    # 手动同步全景预览
                    QTimer.singleShot(50, lambda: self._manual_sync_panorama(current_hole_sector))

        # 减少日志输出频率以提升性能 - 每10个孔位输出一次，并显示路径信息
        if self.simulation_index_v2 % 10 == 0:
            current_sector_name = self.current_displayed_sector.value if self.current_displayed_sector else "未知"
            
            # 计算路径距离（如果有前一个孔位）
            distance_info = ""
            if self.simulation_index_v2 > 0:
                prev_hole = self.holes_list_v2[self.simulation_index_v2 - 1]
                import math
                distance = math.sqrt((current_hole.center_x - prev_hole.center_x)**2 + 
                                   (current_hole.center_y - prev_hole.center_y)**2)
                distance_info = f", 距离: {distance:.1f}"
            
            self.log_message(f"🔄 {current_sector_name}: 孔位 {hole_id} ({self.simulation_index_v2 + 1}/{len(self.holes_list_v2)}){distance_info}")

        # 检查图形项是否存在
        if hole_id not in self.graphics_view.hole_items:
            self.log_message(f"⚠️ V2: 图形项不存在 {hole_id}，尝试修复")
            try:
                # 确保graphics_view引用正确
                if hasattr(self, 'dynamic_sector_display') and self.dynamic_sector_display:
                    self.graphics_view = self.dynamic_sector_display.graphics_view
                
                # 尝试重新加载完整数据集（这样可以确保所有孔位都有图形项）
                self.graphics_view.load_holes(self.hole_collection)
                self.log_message(f"✅ V2: 完整数据集重新加载")
                
                # 重新检查
                if hole_id not in self.graphics_view.hole_items:
                    self.log_message(f"❌ V2: 图形项 {hole_id} 仍然不存在，跳过")
                    self.simulation_index_v2 += 1
                    return
                else:
                    self.log_message(f"✅ V2: 图形项 {hole_id} 修复成功")
            except Exception as e:
                self.log_message(f"❌ V2: 图形项修复失败 {e}，跳过 {hole_id}")
                self.simulation_index_v2 += 1
                return

        # 获取图形项并强制设置颜色
        hole_item = self.graphics_view.hole_items[hole_id]
        
        # 验证图形项有效性
        if not hole_item or not hasattr(hole_item, 'setBrush'):
            self.log_message(f"❌ V2: 图形项 {hole_id} 无效，跳过")
            self.simulation_index_v2 += 1
            return

        # 直接设置蓝色（检测中）
        try:
            from PySide6.QtGui import QColor, QPen, QBrush
            processing_color = QColor(0, 123, 255)  # 蓝色
            hole_item.setBrush(QBrush(processing_color))
            hole_item.setPen(QPen(processing_color.darker(120), 2.0))
            hole_item.update()
        except Exception as e:
            self.log_message(f"❌ V2: 设置图形项颜色失败 {hole_id}: {e}")
            self.simulation_index_v2 += 1
            return

        # self.log_message(f"🔵 V2: {hole_id} 强制设置蓝色（检测中）")

        # 确保图形更新 - 每10个孔位刷新一次以平衡性能
        if self.simulation_index_v2 % 10 == 0:
            self.graphics_view.scene.update()
            self.graphics_view.viewport().update()
            # 强制处理事件以确保UI响应
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()

        # 先设置为检测中状态
        current_hole.status = HoleStatus.PROCESSING
        
        # 更新状态显示
        self.update_status_display()
        
        # 500ms后设置最终颜色
        def set_final_color(hole_obj=current_hole, h_id=hole_id, h_item=hole_item):
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
            h_item.setBrush(QBrush(final_color))
            h_item.setPen(QPen(final_color.darker(120), 2.0))
            h_item.update()

            # 减少日志输出频率但不影响状态更新
            if self.simulation_index_v2 % 10 == 0:
                self.log_message(f"{emoji} V2: {h_id} 检测完成 → {status_text} ({final_color.name()})")

            # 更新统计计数
            self.v2_stats[status_text] += 1
            
            # 【修复】确保更新原始hole_collection中的数据，而不是复制的对象
            if hasattr(self, 'hole_collection') and self.hole_collection and h_id in self.hole_collection.holes:
                # 直接更新hole_collection中的原始数据
                original_hole = self.hole_collection.holes[h_id]
                print(f"🔍 [修复-数据更新] 更新原始数据对象 {h_id}")
                print(f"🔍 [修复-数据更新] 原始对象ID: {id(original_hole)}, 当前对象ID: {id(hole_obj)}")
                
                if status_text == "合格":
                    original_hole.status = HoleStatus.QUALIFIED
                    hole_obj.status = HoleStatus.QUALIFIED  # 同时更新当前对象保持一致性
                elif status_text == "异常":
                    original_hole.status = HoleStatus.DEFECTIVE
                    hole_obj.status = HoleStatus.DEFECTIVE
                elif status_text == "盲孔":
                    original_hole.status = HoleStatus.BLIND
                    hole_obj.status = HoleStatus.BLIND
                elif status_text == "拉杆孔":
                    original_hole.status = HoleStatus.TIE_ROD
                    hole_obj.status = HoleStatus.TIE_ROD
                
                print(f"✅ [修复-数据更新] 原始数据状态更新为: {original_hole.status.value}")
                
                # 更新扇形管理器
                if hasattr(self, 'sector_manager') and self.sector_manager:
                    self.sector_manager.update_hole_status(hole_id, original_hole.status)
                
                # 立即更新状态统计显示
                self.update_status_display()
                
                # 更新扇形进度显示
                if hasattr(self, 'hole_to_sector_map') and h_id in self.hole_to_sector_map:
                    current_sector = self.hole_to_sector_map[h_id]
                    self._update_sector_stats_display(current_sector)
                
            else:
                print(f"❌ [修复-数据更新] 无法找到原始数据对象 {h_id}")
                
                # 作为备用方案，仍然更新当前对象
                if status_text == "合格":
                    hole_obj.status = HoleStatus.QUALIFIED
                elif status_text == "异常":
                    hole_obj.status = HoleStatus.DEFECTIVE
                elif status_text == "盲孔":
                    hole_obj.status = HoleStatus.BLIND
                elif status_text == "拉杆孔":
                    hole_obj.status = HoleStatus.TIE_ROD

            # 减少刷新频率以提升性能
            h_item.update()  # 只更新单个图形项
            
            # 同步全景图状态更新 - 使用批量更新机制优化性能
            print(f"🔍 [调试-全景更新] 准备更新全景图: {h_id}, 颜色: {final_color.name()}")
            print(f"🔍 [调试-全景更新] 当前模拟状态: V1={getattr(self, 'simulation_running', False)}, V2={getattr(self, 'simulation_running_v2', False)}")
            self._update_panorama_hole_status(h_id, final_color)
            print(f"✅ [调试-全景更新] 全景图更新调用完成")

            # 移动到下一个孔位
            self.simulation_index_v2 += 1

        # 延迟设置最终颜色
        QTimer.singleShot(50, set_final_color)  # 50ms后设置最终颜色

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

    def _update_panorama_hole_status(self, hole_id: str, color):
        """同步更新侧边栏全景图中的孔位状态（使用批量更新机制）"""
        print(f"🔍 [全景更新] 开始更新孔位 {hole_id}, 颜色: {color}")
        
        if not hasattr(self, 'sidebar_panorama') or not self.sidebar_panorama:
            print(f"❌ [全景更新] sidebar_panorama 不存在或为空")
            return
        
        print(f"✅ [全景更新] sidebar_panorama 存在: {type(self.sidebar_panorama)}")
        
        try:
            # 使用新的批量更新机制，而不是立即更新
            # 将状态变化转换为HoleStatus对象
            from src.core_business.models.hole_data import HoleStatus
            from PySide6.QtGui import QColor
            
            # 根据颜色推断状态（修复颜色映射）
            if isinstance(color, QColor):
                color_name = color.name().upper()
                r, g, b = color.red(), color.green(), color.blue()
                print(f"🎨 [全景更新] 颜色: {color_name} RGB({r}, {g}, {b})")
                
                # 使用RGB值进行精确匹配，以匹配模拟中使用的确切颜色
                if (r, g, b) == (0, 255, 0) or color_name == "#00FF00":  # 纯绿色 - 合格
                    status = HoleStatus.QUALIFIED
                elif (r, g, b) == (255, 0, 0) or color_name == "#FF0000":  # 纯红色 - 异常
                    status = HoleStatus.DEFECTIVE
                elif (r, g, b) == (255, 255, 0) or color_name == "#FFFF00":  # 纯黄色 - 盲孔
                    status = HoleStatus.BLIND
                elif (r, g, b) == (0, 0, 255) or color_name == "#0000FF":  # 纯蓝色 - 拉杆孔
                    status = HoleStatus.TIE_ROD
                elif (r, g, b) == (0, 123, 255):  # 检测中使用的蓝色
                    status = HoleStatus.PROCESSING
                else:
                    # 其他Material Design颜色的兼容性
                    if color_name in ["#4CAF50"]:  # Material 绿色
                        status = HoleStatus.QUALIFIED
                    elif color_name in ["#F44336"]:  # Material 红色
                        status = HoleStatus.DEFECTIVE
                    elif color_name in ["#2196F3"]:  # Material 蓝色
                        status = HoleStatus.PROCESSING
                    elif color_name in ["#FF9800", "#FFA500"]:  # Material 橙色
                        status = HoleStatus.BLIND
                    elif color_name in ["#9C27B0", "#800080"]:  # Material 紫色
                        status = HoleStatus.TIE_ROD
                    else:
                        print(f"⚠️ [全景更新] 未知颜色，使用默认状态: {color_name} RGB({r}, {g}, {b})")
                        status = HoleStatus.PENDING
            else:
                print(f"⚠️ [全景更新] 颜色不是QColor类型: {type(color)}")
                status = HoleStatus.PENDING
            
            print(f"📋 [全景更新] 推断状态: {status.value}")
            
            # 检查全景图组件是否有update_hole_status方法
            if hasattr(self.sidebar_panorama, 'update_hole_status'):
                print(f"✅ [全景更新] 调用 sidebar_panorama.update_hole_status({hole_id}, {status.value})")
                # 使用批量更新机制
                self.sidebar_panorama.update_hole_status(hole_id, status)
                print(f"✅ [全景更新] 状态更新完成")
            else:
                print(f"❌ [全景更新] sidebar_panorama 没有 update_hole_status 方法")
            
            # 更新动态扇形视图中的小型全景图
            if hasattr(self, 'dynamic_sector_display'):
                print(f"✅ [小型全景图] dynamic_sector_display 存在: {type(self.dynamic_sector_display)}")
                
                if hasattr(self.dynamic_sector_display, 'update_mini_panorama_hole_status'):
                    print(f"✅ [小型全景图] 调用 dynamic_sector_display.update_mini_panorama_hole_status({hole_id}, {status.value})")
                    self.dynamic_sector_display.update_mini_panorama_hole_status(hole_id, status)
                    print(f"✅ [小型全景图] 状态更新调用完成")
                else:
                    print(f"❌ [小型全景图] dynamic_sector_display 没有 update_mini_panorama_hole_status 方法")
                    print(f"🔍 [小型全景图] 可用方法: {[m for m in dir(self.dynamic_sector_display) if not m.startswith('_')]}")
                    
                # 检查 mini_panorama 的存在性和状态
                if hasattr(self.dynamic_sector_display, 'mini_panorama'):
                    mini_panorama = self.dynamic_sector_display.mini_panorama
                    print(f"✅ [小型全景图] mini_panorama 存在: {type(mini_panorama)}")
                    
                    if hasattr(mini_panorama, 'hole_items'):
                        hole_items_count = len(mini_panorama.hole_items) if mini_panorama.hole_items else 0
                        print(f"📊 [小型全景图] hole_items 数量: {hole_items_count}")
                        
                        if hole_id in mini_panorama.hole_items:
                            print(f"✅ [小型全景图] 找到目标孔位 {hole_id} 在 hole_items 中")
                        else:
                            print(f"❌ [小型全景图] 目标孔位 {hole_id} 不在 hole_items 中")
                    else:
                        print(f"❌ [小型全景图] mini_panorama 没有 hole_items 属性")
                        
                    if hasattr(mini_panorama, 'scene'):
                        scene = mini_panorama.scene
                        if scene:
                            scene_items_count = len(scene.items())
                            print(f"📊 [小型全景图] 场景图形项数量: {scene_items_count}")
                        else:
                            print(f"❌ [小型全景图] scene 为 None")
                    else:
                        print(f"❌ [小型全景图] mini_panorama 没有场景或场景为空")
                else:
                    print(f"❌ [小型全景图] dynamic_sector_display 没有 mini_panorama 属性")
            else:
                print(f"❌ [小型全景图] dynamic_sector_display 不存在")
                
        except Exception as e:
            # 添加详细错误信息，便于调试
            print(f"❌ [全景更新] 更新失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_default_dxf(self):
        """加载默认的东重管板DXF文件"""
        default_dxf_path = Path(__file__).parent.parent / "assets" / "dxf" / "DXF Graph" / "东重管板.dxf"
        
        if not default_dxf_path.exists():
            self.logger.warning(f"默认DXF文件不存在: {default_dxf_path}")
            return
        
        try:
            self.logger.info(f"开始加载默认DXF文件: {default_dxf_path}")
            
            # 使用DXF解析器解析文件
            hole_collection = self.dxf_parser.parse_file(str(default_dxf_path))
            
            if hole_collection and len(hole_collection) > 0:
                # 设置孔位集合
                self.hole_collection = hole_collection
                
                # 加载到扇形管理器
                self.sector_manager.load_hole_collection(hole_collection)
                
                # 更新动态扇形显示组件
                if hasattr(self, 'dynamic_sector_display'):
                    self.dynamic_sector_display.set_hole_collection(hole_collection)
                
                # 更新侧边栏全景图
                if hasattr(self, 'sidebar_panorama'):
                    self.sidebar_panorama.load_complete_view(hole_collection)
                
                # 更新UI显示 - 这是必需的，以便启用检测按钮
                self.update_file_info(str(default_dxf_path))
                self.update_hole_display()
                self.update_status_display()
                self.update_completer_data()
                
                # 更新状态显示
                self.statusBar().showMessage(f"已加载默认DXF文件：{default_dxf_path.name}，共 {len(hole_collection)} 个孔位")
                
                # 记录加载信息
                stats = self.dxf_parser.get_parsing_stats(hole_collection)
                self.logger.info(f"DXF文件加载成功：{stats}")
                
                # 开始模拟检测进度（用于演示）- 已禁用自动启动
                # self._start_demo_simulation()
                
            else:
                self.logger.warning("DXF文件解析成功但没有找到孔位数据")
                self.statusBar().showMessage("DXF文件解析成功但没有找到孔位数据")
                
        except Exception as e:
            self.logger.error(f"加载默认DXF文件失败: {e}")
            self.statusBar().showMessage(f"加载DXF文件失败: {e}")
    
    def _start_demo_simulation(self):
        """启动演示模拟（逐步更新孔位状态以展示扇形进度）"""
        if not self.hole_collection:
            return
        
        # 获取所有孔位
        all_holes = list(self.hole_collection.holes.values())
        if not all_holes:
            return
        
        # 随机选择一些孔位进行状态演示
        import random
        demo_holes = random.sample(all_holes, min(len(all_holes) // 3, 20))  # 选择1/3的孔位进行演示
        
        # 设置演示状态
        demo_statuses = [
            HoleStatus.QUALIFIED,   # 合格
            HoleStatus.DEFECTIVE,   # 缺陷
            HoleStatus.BLIND,       # 盲孔
            HoleStatus.TIE_ROD,     # 拉杆孔
        ]
        
        # 分配随机状态
        for hole in demo_holes:
            new_status = random.choice(demo_statuses)
            hole.status = new_status
            # 更新扇形管理器
            self.sector_manager.update_hole_status(hole.hole_id, new_status)
        
        self.logger.info(f"演示模拟已启动，更新了 {len(demo_holes)} 个孔位的状态")
    
    def on_sector_selected(self, sector):
        """处理扇形选择事件"""
        self.logger.info(f"选择了扇形区域: {sector}")
        if hasattr(self, 'sector_detail_view'):
            self.sector_detail_view.show_sector_detail(sector)
        
        # 切换动态扇形显示到选中的区域
        if hasattr(self, 'dynamic_sector_display'):
            self.dynamic_sector_display.switch_to_sector(sector)
        
        # 更新扇形统计信息
        self._update_sector_stats_display(sector)
    
    def _update_sector_stats_display(self, sector):
        """更新扇形统计信息显示"""
        # DEBUG: 主窗口扇形交互调试
        print(f"🔍 [DEBUG MainWindow] _update_sector_stats_display 被调用: {sector}")
        print(f"🔍 [DEBUG MainWindow] sector_stats_label 存在: {hasattr(self, 'sector_stats_label')}")
        print(f"🔍 [DEBUG MainWindow] sector_manager 存在: {self.sector_manager is not None}")
        
        if not hasattr(self, 'sector_stats_label') or not self.sector_manager:
            print(f"⚠️ [DEBUG MainWindow] 缺少必要组件，退出统计信息更新")
            return
        
        try:
            from src.core_business.graphics.sector_manager import SectorQuadrant
            # DEBUG: 扇形统计信息详细调试
            print(f"🔍 [DEBUG MainWindow] 详细扇形统计调试:")
            print(f"  - 请求的扇形: {sector}")
            print(f"  - SectorManager类型: {type(self.sector_manager)}")
            print(f"  - SectorManager有数据: {hasattr(self.sector_manager, 'hole_collection') and self.sector_manager.hole_collection is not None}")
            
            # 检查扇形分配
            if hasattr(self.sector_manager, 'sector_assignments'):
                print(f"  - 扇形分配数量: {len(self.sector_manager.sector_assignments)}")
                sector_count = sum(1 for s in self.sector_manager.sector_assignments.values() if s == sector)
                print(f"  - {sector.value} 扇形孔位数: {sector_count}")
            
            progress = self.sector_manager.get_sector_progress(sector)
            print(f"🔍 [DEBUG MainWindow] 获取到的进度信息: {progress}")
            
            # 如果进度信息为空，尝试强制重新计算
            if not progress:
                print(f"⚠️ [DEBUG MainWindow] 进度信息为空，尝试重新计算")
                self.sector_manager._recalculate_sector_progress(sector)
                progress = self.sector_manager.get_sector_progress(sector)
                print(f"🔍 [DEBUG MainWindow] 重新计算后的进度信息: {progress}")
            sector_names = {
                SectorQuadrant.SECTOR_1: "区域1",
                SectorQuadrant.SECTOR_2: "区域2", 
                SectorQuadrant.SECTOR_3: "区域3",
                SectorQuadrant.SECTOR_4: "区域4"
            }
            
            if progress:
                # 格式化显示扇形统计信息，改为两行紧凑布局
                stats_text = f"""<div style='text-align: center;'>
<h3 style='margin: 5px 0; color: #D3D8E0;'>{sector_names.get(sector, sector.value)}</h3>
<div style='margin: 8px 0; line-height: 1.3;'>
<p style='margin: 2px 0;'><b>总孔位:</b> {progress.total_holes} | <b>已完成:</b> {progress.completed_holes}</p>
<p style='margin: 2px 0;'><b>合格:</b> {progress.qualified_holes} | <b>异常:</b> {progress.defective_holes}</p>
<p style='margin: 4px 0; color: #0066cc;'><b>完成率:</b> {progress.completion_rate:.1f}%</p>
</div>
</div>"""
            else:
                stats_text = f"""<div style='text-align: center;'>
<h3 style='margin: 5px 0; color: #D3D8E0;'>{sector_names.get(sector, sector.value)}</h3>
<p style='margin: 8px 0; color: #D3D8E0;'>暂无统计数据</p>
</div>"""
            
            self.sector_stats_label.setTextFormat(Qt.RichText)  # 启用富文本格式
            self.sector_stats_label.setText(stats_text)
            
        except Exception as e:
            self.logger.error(f"更新扇形统计信息失败: {e}")
            self.sector_stats_label.setText("统计信息加载失败")
    
    def on_dynamic_sector_changed(self, sector):
        """处理动态扇形显示切换事件"""
        try:
            self.logger.info(f"📡 [信号] 接收到扇形切换信号: {sector.value}")
            self.log_message(f"📡 [信号] 动态扇形显示切换到: {sector.value}")
            
            # 异步同步全景图高亮，避免阻塞扇形切换
            QTimer.singleShot(100, lambda: self._async_sync_panorama_highlight(sector))
            
            # 更新状态统计显示
            self.update_status_display()
            
            # 同步更新扇形详细视图
            try:
                if hasattr(self, 'sector_detail_view'):
                    self.sector_detail_view.show_sector_detail(sector)
            except Exception as e:
                self.logger.warning(f"更新扇形详细视图失败: {e}")
            
            # 同步更新扇形统计信息
            try:
                self._update_sector_stats_display(sector)
            except Exception as e:
                self.logger.warning(f"更新扇形统计信息失败: {e}")
                
        except Exception as e:
            self.logger.error(f"处理扇形切换事件失败: {e}")
    
    def _async_sync_panorama_highlight(self, sector):
        """异步同步全景预览高亮，避免阻塞扇形切换"""
        try:
            if not hasattr(self, 'sidebar_panorama') or not self.sidebar_panorama:
                return
            
            # 简化的同步逻辑，不做过多调试检查
            self.sidebar_panorama.highlight_sector(sector) 
            self.log_message(f"✅ [异步同步] 全景高亮: {sector.value}")
            
        except Exception as e:
            self.log_message(f"❌ [异步同步] 失败: {e}")
            
    def _force_sync_panorama_highlight(self, sector):
        """强制同步全景预览高亮（保留原方法用于兼容性）"""
        try:
            self.log_message(f"🔧 [强制同步] 开始: {sector.value}")
            
            if not hasattr(self, 'sidebar_panorama') or not self.sidebar_panorama:
                self.log_message(f"❌ [强制同步] 全景预览组件不存在")
                return
            
            # 减少调试检查，提高效率
            # self._debug_sector_mapping(sector)
            
            # 直接调用高亮，不做过多检查
            self.sidebar_panorama.highlight_sector(sector) 
            self.log_message(f"✅ [强制同步] 完成: {sector.value}")
            
        except Exception as e:
            self.log_message(f"❌ [强制同步] 失败: {e}")
            # 最后的救援措施：重新创建高亮项
            try:
                self.sidebar_panorama._create_sector_highlights()
                QTimer.singleShot(100, lambda: self.sidebar_panorama.highlight_sector(sector))
                self.log_message(f"🔄 [强制同步] 重建高亮项: {sector.value}")
            except Exception as e2:
                self.log_message(f"❌ [强制同步] 重建也失败: {e2}")
    
    def _debug_sector_mapping(self, sector):
        """调试扇形映射是否一致"""
        try:
            # 主视图的扇形理解
            if hasattr(self, 'dynamic_sector_display') and self.dynamic_sector_display:
                main_sector_info = self.dynamic_sector_display.get_sector_info(sector)
                if main_sector_info:
                    main_bounds = main_sector_info.get('collection', {})
                    if hasattr(main_bounds, 'get_bounds'):
                        main_bounds = main_bounds.get_bounds()
                        self.log_message(f"🎯 [调试] 主视图扇形 {sector.value} 边界: {main_bounds}")
            
            # 全景预览的扇形理解
            if hasattr(self.sidebar_panorama, 'sector_highlights') and sector in self.sidebar_panorama.sector_highlights:
                panorama_highlight = self.sidebar_panorama.sector_highlights[sector]
                if hasattr(panorama_highlight, 'sector_bounds') and panorama_highlight.sector_bounds:
                    self.log_message(f"🎨 [调试] 全景扇形 {sector.value} 边界: {panorama_highlight.sector_bounds}")
                    
        except Exception as e:
            self.log_message(f"⚠️ [调试] 扇形映射检查失败: {e}")
    
    def _manual_sync_panorama(self, sector):
        """手动同步全景预览高亮（用于模拟进度）"""
        self.log_message(f"🔧 [模拟] 手动同步全景预览: {sector.value}")
        
        if hasattr(self, 'sidebar_panorama') and self.sidebar_panorama:
            # 检查并创建高亮项
            if not hasattr(self.sidebar_panorama, 'sector_highlights') or not self.sidebar_panorama.sector_highlights:
                self.log_message(f"⚠️ [模拟] 全景高亮项不存在，重新创建")
                self.sidebar_panorama._create_sector_highlights()
                QTimer.singleShot(100, lambda: self.sidebar_panorama.highlight_sector(sector))
            else:
                self.sidebar_panorama.highlight_sector(sector)
                self.log_message(f"✅ [模拟] 全景预览已同步高亮: {sector.value}")
    
    def on_panorama_sector_clicked(self, sector):
        """处理全景图扇形点击事件"""
        # DEBUG: 主窗口扇形交互调试
        print(f"🔍 [DEBUG MainWindow] on_panorama_sector_clicked 被调用: {sector}")
        print(f"🔍 [DEBUG MainWindow] dynamic_sector_display 存在: {hasattr(self, 'dynamic_sector_display') and self.dynamic_sector_display is not None}")
        print(f"🔍 [DEBUG MainWindow] sector_manager 存在: {hasattr(self, 'sector_manager') and self.sector_manager is not None}")
        
        self.logger.info(f"全景图扇形点击: {sector}")
        
        # 切换主视图到被点击的扇形
        if hasattr(self, 'dynamic_sector_display') and self.dynamic_sector_display:
            print(f"🔍 [DEBUG MainWindow] 调用 switch_to_sector({sector})")
            self.dynamic_sector_display.switch_to_sector(sector)
            self.log_message(f"🖱️ 通过全景图点击切换到扇形: {sector.value}")
        
        # 更新扇形统计信息
        print(f"🔍 [DEBUG MainWindow] 调用 _update_sector_stats_display({sector})")
        self._update_sector_stats_display(sector)
    
    def on_sector_progress_updated(self, sector, progress):
        """处理扇形进度更新事件"""
        self.logger.debug(f"扇形 {sector} 进度更新: {progress.progress_percentage:.1f}%")
        
        # 如果有进度更新，自动切换动态显示到该扇形
        if hasattr(self, 'dynamic_sector_display') and progress.completed_holes > 0:
            self.dynamic_sector_display.update_sector_progress(sector, progress)
    
    def on_overall_progress_updated(self, overall_stats):
        """处理整体进度更新事件"""
        total = overall_stats.get('total_holes', 0)
        completed = overall_stats.get('completed_holes', 0)
        if total > 0:
            overall_rate = (completed / total) * 100
            self.logger.debug(f"整体进度更新: {overall_rate:.1f}%")
    
    def switch_to_dark_theme(self):
        """切换到深色主题（默认主题）"""
        try:
            from modules.theme_manager_unified import get_unified_theme_manager
            theme_manager = get_unified_theme_manager()
            from PySide6.QtWidgets import QApplication
            
            app = QApplication.instance()
            if app:
                theme_manager.apply_theme(app, "dark")
                print("✅ 已切换到深色主题（默认主题）")
                QMessageBox.information(self, "主题切换", "已切换到深色主题（默认主题）")
            
        except Exception as e:
            print(f"切换到深色主题失败: {e}")
            QMessageBox.warning(self, "错误", f"切换到深色主题失败:\n{str(e)}")
    
    def switch_to_light_theme(self):
        """切换到浅色主题（可选主题）"""
        try:
            from modules.theme_manager_unified import get_unified_theme_manager
            theme_manager = get_unified_theme_manager()
            from PySide6.QtWidgets import QApplication
            
            app = QApplication.instance()
            if app:
                theme_manager.apply_theme(app, "light")
                print("✅ 已切换到浅色主题")
                QMessageBox.information(self, "主题切换", "已切换到浅色主题")
            
        except Exception as e:
            print(f"切换到浅色主题失败: {e}")
            QMessageBox.warning(self, "错误", f"切换到浅色主题失败:\n{str(e)}")

    def open_theme_debugger(self):
        """打开主题调试工具"""
        try:
            from modules.theme_switcher import show_theme_switcher
            print("打开主题调试工具...")
            show_theme_switcher(self)
        except Exception as e:
            print(f"打开主题调试工具失败: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, "错误", f"无法打开主题调试工具:\n{str(e)}")


def main():
    """
    统一的应用程序启动入口
    集成了ApplicationCore架构和传统启动方式
    """
    import sys
    from PySide6.QtWidgets import QApplication
    from pathlib import Path
    
    # 检查Python版本兼容性
    try:
        from version import check_python_version, print_version_info
        check_python_version()
    except (ImportError, RuntimeError) as e:
        print(f"❌ 版本检查失败: {e}")
        # 继续运行，但给出警告
        print("⚠️ 将使用传统启动方式")
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 尝试使用ApplicationCore架构
    try:
        from core.application import get_application
        
        print("🚀 启动 AIDCIS3-LFS 管孔检测系统...")
        print("📋 功能特点:")
        print("   ✅ 插件化架构 - 企业级插件系统")
        print("   ✅ 依赖注入框架 - 模块化服务管理")
        print("   ✅ 全局错误处理 - 统一异常管理")
        print("   ✅ ApplicationCore - 应用程序生命周期管理")
        print("   ✅ 扇形进度视图 - 智能区域管理")
        print("   ✅ 完整孔位显示 - 实时状态监控")
        print("")
        
        # 打印版本信息
        try:
            print_version_info()
        except:
            print("版本信息获取失败，使用默认版本")
        
        print("\n🚀 正在启动应用程序...")
        
        # 获取应用程序实例
        app_core = get_application()
        
        # 初始化应用程序
        if not app_core.initialize():
            print("❌ 应用程序初始化失败，回退到传统启动方式")
            raise ImportError("ApplicationCore initialization failed")
        
        print("✅ 应用程序初始化成功")
        
        # 应用现代科技蓝主题到ApplicationCore - 使用主题协调器
        try:
            from modules.theme_orchestrator import initialize_theme_system
            qt_app = app_core.get_qt_application()
            if qt_app:
                orchestrator = initialize_theme_system(qt_app)
                print("✅ 现代科技蓝主题已应用到ApplicationCore (使用协调器)")
        except Exception as e:
            print(f"⚠️ ApplicationCore主题应用失败: {e}")
            # 回退到传统方式
            try:
                from modules.theme_manager_unified import get_unified_theme_manager
                theme_manager = get_unified_theme_manager()
                qt_app = app_core.get_qt_application()
                if qt_app:
                    theme_manager.apply_theme(qt_app, "dark")
                    print("✅ 回退到传统主题应用方式")
            except Exception as e2:
                print(f"⚠️ 回退主题应用也失败: {e2}")
        
        # 运行应用程序
        try:
            exit_code = app_core.run()
            print(f"应用程序已退出，退出码: {exit_code}")
            return exit_code
        except KeyboardInterrupt:
            print("\n用户中断，正在关闭应用程序...")
            app_core.shutdown()
            return 0
        except Exception as e:
            print(f"❌ 应用程序运行时错误: {e}")
            return 1
            
    except ImportError as e:
        print(f"⚠️ ApplicationCore架构不可用: {e}")
        print("🔄 回退到传统启动方式...")
        
        # 传统启动方式
        app = QApplication(sys.argv)
        
        # 设置应用程序信息
        app.setApplicationName("上位机软件")
        app.setApplicationDisplayName("管孔检测系统")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("检测系统开发团队")
        app.setOrganizationDomain("detection-system.com")
        
        # 应用现代科技蓝主题 - 使用主题协调器
        try:
            from modules.theme_orchestrator import initialize_theme_system, get_theme_orchestrator
            orchestrator = initialize_theme_system(app)
            print("✅ 现代科技蓝主题已应用 (使用协调器)")
        except Exception as e:
            print(f"⚠️ 主题协调器初始化失败: {e}")
            # 回退到传统方式
            try:
                from modules.theme_manager_unified import get_unified_theme_manager
                theme_manager = get_unified_theme_manager()
                theme_manager.apply_theme(app, "dark")
                print("✅ 回退到传统主题应用方式")
            except Exception as e2:
                print(f"⚠️ 回退主题应用也失败: {e2}")
        
        # 创建并显示主窗口
        window = MainWindow()
        
        # 使用主题协调器管理主窗口主题
        try:
            orchestrator = get_theme_orchestrator()
            orchestrator.set_main_window(window)
            orchestrator.mark_application_ready()
            print("✅ 主窗口已注册到主题协调器")
        except Exception as e:
            print(f"⚠️ 主题协调器注册失败: {e}")
            # 回退到传统方式
            try:
                from modules.theme_manager_unified import get_unified_theme_manager
                theme_manager = get_unified_theme_manager()
                theme_manager.apply_theme(app, "dark")
                theme_manager.force_dark_theme(window)
                print("✅ 回退到传统主窗口主题应用")
            except Exception as e2:
                print(f"⚠️ 回退主题应用也失败: {e2}")
        
        window.show()
        
        return app.exec()

if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)
