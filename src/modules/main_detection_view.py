"""
一级页面 - 主检测视图
提供整个检测任务的宏观状态概览，采用三栏式布局：信息、预览、操作。
"""

import os
from datetime import datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
                               QLabel, QPushButton, QProgressBar, QGroupBox,
                               QLineEdit, QTextEdit, QFrame, QSplitter, QCompleter, QSizePolicy, QScrollArea)
from PySide6.QtCore import Qt, Signal, QTimer, QStringListModel
from PySide6.QtGui import QFont

from .workpiece_diagram import WorkpieceDiagram, DetectionStatus
from .ui_components.toolbar import MainToolbar
from .ui_components.integration_helper import ComponentIntegrationHelper, replace_panorama_placeholder
from .ui_components.style_manager import StyleManager, ButtonVariant, ButtonSize
from .ui_components.layout_factory import LayoutFactory, create_standard_form_panel, create_button_grid_panel
from .time_tracker import get_time_tracker
from .simulation_system import SimulationSystem, SimulationControlWidget, SimulationState
from .navigation_manager import get_navigation_manager, get_quick_navigation_helper
from .performance_optimizer import get_performance_optimizer, OptimizationConfig, RenderingStrategy, MemoryStrategy
from .file_operations import FileOperationsManager, FileOperationsWidget


class MainDetectionView(QWidget):
    """主检测视图 - 一级页面"""
    
    navigate_to_realtime = Signal(str)
    navigate_to_history = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # [DIAGNOSTIC LOG] 记录MainDetectionView初始化开始
        import logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("🔍 [DIAGNOSTIC] MainDetectionView.__init__ 开始")
        
        self.current_hole_id = None
        
        # 集成时间跟踪器
        self.time_tracker = get_time_tracker()
        
        # 组件集成助手
        self.integration_helper = ComponentIntegrationHelper(self)
        
        # 集成模拟系统
        self.simulation_system = SimulationSystem(self)
        
        # 集成导航管理器
        self.navigation_manager = get_navigation_manager()
        self.quick_nav_helper = get_quick_navigation_helper()
        
        # 集成性能优化器 - 使用保守配置减少警告
        perf_config = OptimizationConfig(
            rendering_strategy=RenderingStrategy.VIEWPORT_ONLY,
            memory_strategy=MemoryStrategy.CONSERVATIVE,
            max_visible_items=300,  # 减少可见项目
            max_memory_mb=500.0,
            enable_async_rendering=False,  # 暂时禁用异步渲染避免线程问题
            enable_performance_monitoring=True,
            log_performance_warnings=False,  # 禁用性能警告
            update_interval_ms=500,  # 降低更新频率
            gc_threshold_mb=450.0  # 提高垃圾回收阈值
        )
        self.performance_optimizer = get_performance_optimizer(perf_config)
        
        # 集成文件操作管理器
        self.file_operations_manager = FileOperationsManager(self)
        
        # [DIAGNOSTIC LOG] 记录各个初始化步骤
        self.logger.info("🔍 [DIAGNOSTIC] 开始setup_ui()")
        self.setup_ui()
        
        self.logger.info("🔍 [DIAGNOSTIC] 开始setup_connections()")
        self.setup_connections()
        
        self.logger.info("🔍 [DIAGNOSTIC] 开始initialize_data()")
        self.initialize_data()
        
        self.logger.info("🔍 [DIAGNOSTIC] MainDetectionView.__init__ 完成")
    
    def _apply_panel_style(self, panel: QGroupBox):
        """为面板应用统一的样式 - 使用StyleManager"""
        StyleManager.apply_panel_style(panel)
    
    def _apply_button_styles(self, *buttons, variant=ButtonVariant.PRIMARY, size=ButtonSize.LARGE):
        """为按钮应用统一的样式 - 使用StyleManager"""
        StyleManager.apply_button_styles(*buttons, variant=variant, size=size)
        
    def setup_ui(self):
        """设置用户界面 - 顶部工具栏 + 三栏式布局"""
        # 主垂直布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. 在setup_ui()开始处集成工具栏
        try:
            self.toolbar = MainToolbar(self)
            main_layout.addWidget(self.toolbar)
        except Exception as e:
            self.logger.error(f"工具栏创建失败: {e}")
            # 创建错误占位符
            error_toolbar = QLabel("⚠️ 工具栏加载失败")
            error_toolbar.setFixedHeight(70)
            error_toolbar.setAlignment(Qt.AlignCenter)
            error_toolbar.setStyleSheet("background-color: #ffeeee; color: red; font-weight: bold;")
            main_layout.addWidget(error_toolbar)
            self.toolbar = None
        
        # 2. 三栏式内容布局 - 使用LayoutFactory
        content_layout, left_panel, middle_panel, right_panel = LayoutFactory.create_three_column_layout(
            left_width=360,
            right_width=320,
            spacing=12,
            margins=(8, 8, 8, 8)
        )
        
        # 创建各栏内容
        self._setup_left_panel(left_panel)
        self._setup_middle_panel(middle_panel)
        self._setup_right_panel(right_panel)
        
        # 创建内容组件并添加到主布局
        content_widget = QWidget()
        content_widget.setLayout(content_layout)
        main_layout.addWidget(content_widget, 1)
        
        # 集成性能优化器到图形视图
        if hasattr(self, 'workpiece_diagram') and self.workpiece_diagram.graphics_view:
            self.performance_optimizer.set_graphics_view(self.workpiece_diagram.graphics_view)

    def _setup_left_panel(self, panel):
        """设置左侧信息面板 - 添加滚动功能确保所有内容可见"""
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 创建内容面板
        content_panel = QWidget()
        layout = QVBoxLayout(content_panel)
        layout.setContentsMargins(10, 8, 10, 8)  # 减少边距以节省空间
        layout.setSpacing(12)  # 减少间距从20到12，确保内容适应

        # 1. 文件信息（增强版）- 使用LayoutFactory
        self.file_info_panel, file_layout = create_standard_form_panel("文件信息")
        self._apply_panel_style(self.file_info_panel)
        
        # DXF文件信息
        self.dxf_file_label = QLabel("未加载")
        self.dxf_file_label.setTextFormat(Qt.PlainText)
        self.dxf_file_label.setWordWrap(False)
        self.dxf_file_label.setMaximumWidth(220)
        self.dxf_file_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        file_layout.addRow("DXF文件:", self.dxf_file_label)
        
        # 文件大小
        self.file_size_label = QLabel("--")
        file_layout.addRow("文件大小:", self.file_size_label)
        
        # 加载时间
        self.load_time_label = QLabel("--")
        file_layout.addRow("加载时间:", self.load_time_label)
        
        layout.addWidget(self.file_info_panel)

        # 2. 状态统计 - 使用LayoutFactory
        self.stats_panel, stats_layout = create_standard_form_panel("状态统计")
        self._apply_panel_style(self.stats_panel)
        
        self.total_label = QLabel("0")
        self.total_label.setStyleSheet("font-weight: bold; color: #333;")
        stats_layout.addRow("总孔数:", self.total_label)
        
        self.qualified_label = QLabel("0")
        self.qualified_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        stats_layout.addRow("合格:", self.qualified_label)
        
        self.unqualified_label = QLabel("0")
        self.unqualified_label.setStyleSheet("font-weight: bold; color: #F44336;")
        stats_layout.addRow("不合格:", self.unqualified_label)
        
        self.not_detected_label = QLabel("0")
        self.not_detected_label.setStyleSheet("font-weight: bold; color: #FF9800;")
        stats_layout.addRow("待检:", self.not_detected_label)
        layout.addWidget(self.stats_panel)

        # 3. 检测进度（增强版）
        self.progress_panel = QGroupBox("检测进度")
        self._apply_panel_style(self.progress_panel)
        progress_layout = QVBoxLayout(self.progress_panel)
        progress_layout.setContentsMargins(15, 15, 15, 15)  # 增加内边距
        
        # 进度条行
        progress_bar_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        progress_bar_layout.addWidget(self.progress_bar)
        self.progress_label = QLabel("0%")
        progress_bar_layout.addWidget(self.progress_label)
        progress_layout.addLayout(progress_bar_layout)
        
        # 新增：完成率和合格率
        rates_layout = QGridLayout()
        rates_layout.addWidget(QLabel("完成率:"), 0, 0)
        self.completion_rate_label = QLabel("0%")
        rates_layout.addWidget(self.completion_rate_label, 0, 1)
        rates_layout.addWidget(QLabel("合格率:"), 0, 2)
        self.qualification_rate_label = QLabel("0%")
        rates_layout.addWidget(self.qualification_rate_label, 0, 3)
        progress_layout.addLayout(rates_layout)
        
        layout.addWidget(self.progress_panel)

        # 4. 孔位信息 - 使用LayoutFactory
        self.hole_info_panel, hole_info_layout = create_standard_form_panel("孔位信息")
        self._apply_panel_style(self.hole_info_panel)
        
        self.selected_hole_id_label = QLabel("--")
        self.selected_hole_id_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        hole_info_layout.addRow("选中ID:", self.selected_hole_id_label)
        
        self.selected_hole_pos_label = QLabel("--")
        hole_info_layout.addRow("坐标:", self.selected_hole_pos_label)
        
        self.selected_hole_status_label = QLabel("--")
        hole_info_layout.addRow("状态:", self.selected_hole_status_label)
        layout.addWidget(self.hole_info_panel)

        # 5. 性能监控面板 - 使用LayoutFactory
        self.performance_panel, perf_layout = create_standard_form_panel("性能监控")
        self._apply_panel_style(self.performance_panel)
        
        self.fps_label = QLabel("--")
        self.fps_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        perf_layout.addRow("帧率:", self.fps_label)
        
        self.memory_label = QLabel("--")
        self.memory_label.setStyleSheet("font-weight: bold; color: #FF9800;")
        perf_layout.addRow("内存:", self.memory_label)
        
        self.render_time_label = QLabel("--")
        self.render_time_label.setStyleSheet("font-weight: bold; color: #9C27B0;")
        perf_layout.addRow("渲染:", self.render_time_label)
        
        self.cache_hit_label = QLabel("--")
        self.cache_hit_label.setStyleSheet("font-weight: bold; color: #607D8B;")
        perf_layout.addRow("缓存:", self.cache_hit_label)
        layout.addWidget(self.performance_panel)
        
        # 6. 时间跟踪 - 使用LayoutFactory
        self.time_tracking_panel, time_layout = create_standard_form_panel("时间跟踪")
        self._apply_panel_style(self.time_tracking_panel)
        
        self.detection_time_label = QLabel("00:00:00")
        self.detection_time_label.setStyleSheet("font-weight: bold; color: #795548;")
        time_layout.addRow("检测时间:", self.detection_time_label)
        
        self.estimated_time_label = QLabel("--")
        time_layout.addRow("预计用时:", self.estimated_time_label)
        layout.addWidget(self.time_tracking_panel)
        
        # 7. 全景预览位置（360x420px的QWidget占位符）
        self.panorama_preview_panel = QGroupBox("全景预览")
        self._apply_panel_style(self.panorama_preview_panel)
        panorama_layout = QVBoxLayout(self.panorama_preview_panel)
        panorama_layout.setContentsMargins(10, 10, 10, 10)  # 减少内边距以适应固定大小的组件
        self.panorama_placeholder = QWidget()
        self.panorama_placeholder.setFixedSize(360, 420)
        self.panorama_placeholder.setStyleSheet(
            "background-color: #f0f0f0; "
            "border: 2px dashed #ccc; "
            "border-radius: 5px;"
        )
        # 添加占位文本
        panorama_placeholder_layout = QVBoxLayout(self.panorama_placeholder)
        panorama_text = QLabel("全景预览组件\n开发中...\n360x420px")
        panorama_text.setAlignment(Qt.AlignCenter)
        panorama_text.setStyleSheet("color: #888; font-style: italic; border: none;")
        panorama_placeholder_layout.addWidget(panorama_text)
        panorama_layout.addWidget(self.panorama_placeholder)
        layout.addWidget(self.panorama_preview_panel)
        
        # 8. 扇形统计位置（QLabel占位符，最小高度120px）
        self.sector_stats_panel = QGroupBox("扇形统计")
        self._apply_panel_style(self.sector_stats_panel)
        sector_layout = QVBoxLayout(self.sector_stats_panel)
        sector_layout.setContentsMargins(15, 15, 15, 15)
        self.sector_stats_placeholder = QLabel("扇形统计信息\n开发中...")
        self.sector_stats_placeholder.setAlignment(Qt.AlignCenter)
        self.sector_stats_placeholder.setMinimumHeight(120)
        self.sector_stats_placeholder.setStyleSheet(
            "background-color: #f8f8f8; "
            "border: 1px solid #ddd; "
            "border-radius: 3px; "
            "color: #888; "
            "font-style: italic;"
        )
        sector_layout.addWidget(self.sector_stats_placeholder)
        layout.addWidget(self.sector_stats_panel)

        layout.addStretch()
        
        # 将内容面板设置到滚动区域
        scroll_area.setWidget(content_panel)
        
        # 将滚动区域添加到传入的panel中
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.addWidget(scroll_area)

    def _setup_middle_panel(self, panel):
        """设置中间DXF预览面板"""
        layout = QVBoxLayout(panel)
        # 修复问题2.3: 增加底部边距，确保状态说明栏不紧贴底部
        layout.setContentsMargins(5, 0, 5, 10)  # 增加底部边距从0到10
        layout.setSpacing(5)  # 减少组件间距，解决问题2.1

        # 1. 状态图例 (从WorkpieceDiagram中提取)
        self.legend_frame = self._create_status_legend_widget()
        layout.addWidget(self.legend_frame)
        
        # 2. 新增：层级化视图控制框架（QFrame，60px高）
        self.view_control_frame = self._create_view_control_framework()
        layout.addWidget(self.view_control_frame)

        # 修复问题2.1: 减少视图控制栏与工件图之间的间距
        # 不添加stretch，直接添加工件图容器
        
        # 3. 工件图容器 - 修复问题2.2: 标题与内容对齐
        workpiece_container = self._create_workpiece_container()
        layout.addWidget(workpiece_container, 1)  # 占据剩余空间
    
    def _create_workpiece_container(self):
        """创建工件图容器，解决标题与内容对齐问题"""
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(8)  # 标题与图表间的紧凑间距
        
        # 修复问题2.2: 工件标题左对齐，与下方内容保持一致
        workpiece_title = QLabel("管板工件")
        workpiece_title.setAlignment(Qt.AlignLeft)  # 改为左对齐
        workpiece_title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #333;
                margin-left: 0px;
                padding-left: 0px;
            }
        """)
        container_layout.addWidget(workpiece_title)
        
        # 3. DXF预览（保留现有WorkpieceDiagram的位置）
        self.workpiece_diagram = WorkpieceDiagram()
        container_layout.addWidget(self.workpiece_diagram, 1)
        
        return container

    def _setup_right_panel(self, panel):
        """创建右侧操作面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 12, 10, 8)  # 增加边距使布局更舒适
        layout.setSpacing(25)  # 大幅增加间距到25px，减少拥挤感，确保生命安全操作空间

        # 1. 检测操作
        self.control_panel = ControlPanel()
        self._apply_panel_style(self.control_panel)
        layout.addWidget(self.control_panel)

        # 2. 新增：模拟功能组（集成实际模拟控制组件）
        try:
            self.simulation_control_widget = SimulationControlWidget(self)
            layout.addWidget(self.simulation_control_widget)
        except Exception as e:
            self.logger.error(f"模拟控制组件创建失败: {e}")
            # 回退到占位符
            self.simulation_panel = QGroupBox("模拟功能")
            simulation_layout = QVBoxLayout(self.simulation_panel)
            simulation_placeholder = QLabel("模拟系统功能\n加载失败")
            simulation_placeholder.setAlignment(Qt.AlignCenter)
            simulation_placeholder.setStyleSheet("color: #888; font-style: italic;")
            simulation_layout.addWidget(simulation_placeholder)
            layout.addWidget(self.simulation_panel)
            self.simulation_control_widget = None
        
        # 3. 新增：导航功能组（实时监控、历史数据按钮）
        self.navigation_panel = QGroupBox("导航功能")
        self._apply_panel_style(self.navigation_panel)
        navigation_layout = QGridLayout(self.navigation_panel)
        navigation_layout.setSpacing(8)
        navigation_layout.setContentsMargins(15, 15, 15, 15)
        
        self.goto_realtime_btn = QPushButton("🔍 实时监控")
        self.goto_realtime_btn.setFixedSize(150, 40)  # 统一按钮尺寸
        self.goto_realtime_btn.setToolTip("跳转到实时监控页面")
        self.goto_history_btn = QPushButton("📊 历史数据")
        self.goto_history_btn.setFixedSize(150, 40)  # 统一按钮尺寸
        self.goto_history_btn.setToolTip("跳转到历史数据页面")
        
        # 应用统一按钮样式
        self._apply_button_styles(self.goto_realtime_btn, self.goto_history_btn)
        
        navigation_layout.addWidget(self.goto_realtime_btn, 0, 0)
        navigation_layout.addWidget(self.goto_history_btn, 0, 1)
        layout.addWidget(self.navigation_panel)
        
        # 4. 新增：文件操作组（加载DXF、导出数据按钮）
        self.file_ops_panel = QGroupBox("文件操作")
        self._apply_panel_style(self.file_ops_panel)
        file_ops_layout = QGridLayout(self.file_ops_panel)
        file_ops_layout.setSpacing(8)
        file_ops_layout.setContentsMargins(15, 15, 15, 15)
        
        self.load_dxf_btn = QPushButton("📁 加载DXF")
        self.load_dxf_btn.setFixedSize(150, 40)  # 统一按钮尺寸
        self.load_dxf_btn.setToolTip("加载新的DXF文件")
        self.load_dxf_btn.setProperty("class", "secondary")
        
        self.export_data_btn = QPushButton("💾 导出数据")
        self.export_data_btn.setFixedSize(150, 40)  # 统一按钮尺寸
        self.export_data_btn.setToolTip("导出检测数据")
        self.export_data_btn.setProperty("class", "success")
        
        # 应用统一按钮样式
        self._apply_button_styles(self.load_dxf_btn, self.export_data_btn)
        
        file_ops_layout.addWidget(self.load_dxf_btn, 0, 0)
        file_ops_layout.addWidget(self.export_data_btn, 0, 1)
        layout.addWidget(self.file_ops_panel)

        # 5. 视图控制组已删除 - 减少与中间面板功能重复，避免操作混乱，确保生命安全

        # 6. 操作日志
        log_panel = QGroupBox("操作日志")
        self._apply_panel_style(log_panel)
        log_layout = QVBoxLayout(log_panel)
        log_layout.setContentsMargins(15, 15, 15, 15)
        
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setMinimumHeight(120)
        # 应用日志文本框的深色主题样式
        self.log_text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #2B2B2B;
                color: #FFFFFF;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                selection-background-color: #3C3C3C;
            }
            QScrollBar:vertical {
                background-color: #2B2B2B;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #555555;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #666666;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        log_layout.addWidget(self.log_text_edit)
        layout.addWidget(log_panel)

        layout.addStretch()

    def _create_status_legend_widget(self):
        """创建独立的状态图例小部件"""
        legend_frame = QFrame()
        legend_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        legend_layout = QHBoxLayout(legend_frame)
        legend_layout.setContentsMargins(5, 5, 5, 5)
        
        # 🎨 FIX 3: 补充管板孔位的图例颜色显示 - 与workpiece_diagram.py中的实际颜色完全一致
        statuses = [
            ("未检测", "#808080"),     # 灰色 - QColor(128, 128, 128)
            ("正在检测", "#FFFF00"),   # 黄色 - QColor(255, 255, 0)  
            ("合格", "#00FF00"),       # 绿色 - QColor(0, 255, 0)
            ("不合格", "#FF0000"),     # 红色 - QColor(255, 0, 0)
            ("真实数据", "#FFA500")    # 橙色 - QColor(255, 165, 0)
        ]
        
        for text, color in statuses:
            color_label = QLabel()
            color_label.setFixedSize(16, 16)
            
            # 将颜色转换为CSS颜色字符串
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
            legend_layout.addWidget(color_label)
            legend_layout.addWidget(QLabel(text))
            legend_layout.addSpacing(10)
        
        legend_layout.addStretch()
        return legend_frame
    
    def _create_view_control_framework(self):
        """创建层级化视图控制框架"""
        control_frame = QFrame()
        control_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        # 减少高度以缩小与工件图的间距
        control_frame.setFixedHeight(55)  # 增加到55以适应新按钮样式
        control_frame.setStyleSheet(
            "QFrame {"
            "    background-color: #FDFDFD;"
            "    border: 2px solid #E0E0E0;"
            "    border-radius: 8px;"
            "}"
        )
        
        control_layout = QHBoxLayout(control_frame)
        # 减少内边距以使控件更紧凑
        control_layout.setContentsMargins(8, 3, 8, 3)  # 从(10,5,10,5)减少到(8,3,8,3)
        control_layout.setSpacing(12)  # 从15减少到12
        
        # 设置基础字体
        label_font = QFont()
        label_font.setPointSize(10)
        
        # 1. 宏观/微观视图切换按钮（使用emoji图标）
        view_toggle_group = QWidget()
        view_toggle_layout = QHBoxLayout(view_toggle_group)
        view_toggle_layout.setContentsMargins(0, 0, 0, 0)
        view_toggle_layout.setSpacing(5)
        
        view_label = QLabel("视图:")
        view_label.setFont(label_font)
        view_toggle_layout.addWidget(view_label)
        
        self.macro_view_btn = QPushButton("🌍 宏观")
        self.macro_view_btn.setCheckable(True)
        self.macro_view_btn.setChecked(True)
        # 减少按钮高度以适应新的框架高度
        self.macro_view_btn.setFixedHeight(30)  # 从35减少到30
        self.macro_view_btn.setToolTip("切换到宏观视图")
        
        self.micro_view_btn = QPushButton("🔍 微观")
        self.micro_view_btn.setCheckable(True)
        # 减少按钮高度以适应新的框架高度
        self.micro_view_btn.setFixedHeight(30)  # 从35减少到30
        self.micro_view_btn.setToolTip("切换到微观视图")
        
        view_toggle_layout.addWidget(self.macro_view_btn)
        view_toggle_layout.addWidget(self.micro_view_btn)
        control_layout.addWidget(view_toggle_group)
        
        # 分隔线
        separator1 = QLabel("|")
        separator1.setStyleSheet("color: #ccc; font-size: 14px;")
        control_layout.addWidget(separator1)
        
        # 2. 方向统一按钮
        direction_group = QWidget()
        direction_layout = QHBoxLayout(direction_group)
        direction_layout.setContentsMargins(0, 0, 0, 0)
        direction_layout.setSpacing(5)
        
        direction_label = QLabel("方向:")
        direction_label.setFont(label_font)
        direction_layout.addWidget(direction_label)
        
        self.unify_direction_btn = QPushButton("↕️ 统一竖向")
        # 减少按钮高度以适应新的框架高度
        self.unify_direction_btn.setFixedHeight(30)  # 从35减少到30
        self.unify_direction_btn.setToolTip("统一所有孔位的方向为竖向")
        direction_layout.addWidget(self.unify_direction_btn)
        control_layout.addWidget(direction_group)
        
        # 分隔线
        separator2 = QLabel("|")
        separator2.setStyleSheet("color: #ccc; font-size: 14px;")
        control_layout.addWidget(separator2)
        
        # 3. 视图状态指示器标签
        status_group = QWidget()
        status_layout = QHBoxLayout(status_group)
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        status_label = QLabel("状态:")
        status_label.setFont(label_font)
        status_layout.addWidget(status_label)
        
        self.view_status_indicator = QLabel("宏观视图 - 就绪")
        self.view_status_indicator.setStyleSheet(
            "color: #2e7d32; "
            "font-weight: bold; "
            "padding: 5px 10px; "
            "background-color: #e8f5e8; "
            "border: 1px solid #4caf50; "
            "border-radius: 3px;"
        )
        status_layout.addWidget(self.view_status_indicator)
        control_layout.addWidget(status_group)
        
        # 弹性空间
        control_layout.addStretch()
        
        return control_frame

    def setup_connections(self):
        """设置所有信号和槽的连接"""
        # 工具栏信号连接（使用信号槽机制连接工具栏事件）
        if hasattr(self, 'toolbar') and self.toolbar:
            try:
                self.toolbar.product_selected.connect(self._on_toolbar_product_selected)
                self.toolbar.search_requested.connect(self._on_toolbar_search_requested) 
                self.toolbar.filter_changed.connect(self._on_toolbar_filter_changed)
            except Exception as e:
                self.logger.error(f"工具栏信号连接失败: {e}")
        
        # 预览图点击
        self.workpiece_diagram.hole_clicked.connect(self.on_hole_clicked)
        
        # 检测操作按钮
        self.control_panel.start_detection.connect(self.on_start_detection)
        self.control_panel.pause_detection.connect(self.on_pause_detection)
        self.control_panel.stop_detection.connect(self.on_stop_detection)
        self.control_panel.reset_detection.connect(self.on_reset_detection)
        
        # 视图控制按钮信号连接已删除 - 相关按钮已从右侧面板移除
        
        # 新增：层级化视图控制信号
        if hasattr(self, 'macro_view_btn'):
            self.macro_view_btn.clicked.connect(self._on_macro_view_clicked)
        if hasattr(self, 'micro_view_btn'):
            self.micro_view_btn.clicked.connect(self._on_micro_view_clicked)
        if hasattr(self, 'unify_direction_btn'):
            self.unify_direction_btn.clicked.connect(self._on_unify_direction_clicked)
        
        # 新增：导航功能信号
        if hasattr(self, 'goto_realtime_btn'):
            self.goto_realtime_btn.clicked.connect(self._on_goto_realtime_clicked)
        if hasattr(self, 'goto_history_btn'):
            self.goto_history_btn.clicked.connect(self._on_goto_history_clicked)
        
        # 新增：文件操作信号
        if hasattr(self, 'load_dxf_btn'):
            self.load_dxf_btn.clicked.connect(self._on_load_dxf_clicked)
        
        # 时间跟踪器信号连接
        self.time_tracker.time_updated.connect(self._on_time_updated)
        self.time_tracker.progress_updated.connect(self._on_progress_updated)
        if hasattr(self, 'export_data_btn'):
            self.export_data_btn.clicked.connect(self._on_export_data_clicked)
        
        # 模拟系统信号连接
        self.simulation_system.hole_detected.connect(self._on_simulation_hole_detected)
        self.simulation_system.progress_updated.connect(self._on_simulation_progress_updated)
        self.simulation_system.batch_completed.connect(self._on_simulation_batch_completed)
        self.simulation_system.simulation_started.connect(self._on_simulation_started)
        self.simulation_system.simulation_stopped.connect(self._on_simulation_stopped)
        self.simulation_system.error_occurred.connect(self._on_simulation_error)
        
        # 模拟控制组件信号连接
        if hasattr(self, 'simulation_control_widget') and self.simulation_control_widget:
            self.simulation_control_widget.start_requested.connect(self._on_simulation_start_requested)
            self.simulation_control_widget.pause_requested.connect(self.simulation_system.pause_simulation)
            self.simulation_control_widget.resume_requested.connect(self.simulation_system.resume_simulation)
            self.simulation_control_widget.stop_requested.connect(self.simulation_system.stop_simulation)
            self.simulation_control_widget.config_changed.connect(self._on_simulation_config_changed)
        
        # 导航管理器信号连接
        self.navigation_manager.navigation_requested.connect(self._on_navigation_requested)
        self.navigation_manager.navigation_completed.connect(self._on_navigation_completed)
        self.navigation_manager.navigation_failed.connect(self._on_navigation_failed)
        
        # 性能优化器信号连接
        self.performance_optimizer.metrics_updated.connect(self._on_performance_metrics_updated)
        self.performance_optimizer.optimization_applied.connect(self._on_optimization_applied)
        self.performance_optimizer.warning_issued.connect(self._on_performance_warning)
        
        # 文件操作管理器信号连接
        self.file_operations_manager.operation_started.connect(self._on_file_operation_started)
        self.file_operations_manager.operation_progress.connect(self._on_file_operation_progress)
        self.file_operations_manager.operation_completed.connect(self._on_file_operation_completed)
        self.file_operations_manager.operation_error.connect(self._on_file_operation_error)
        self.file_operations_manager.files_dropped.connect(self._on_files_dropped)
        
        # 集成全景预览组件
        try:
            self.logger.info("🔍 [DIAGNOSTIC] 开始集成全景预览组件")
            integration_success = replace_panorama_placeholder(self, self.integration_helper)
            if integration_success:
                self.logger.info("✅ [DIAGNOSTIC] 全景预览组件集成成功")
                # 连接集成助手信号
                self.integration_helper.sector_selected.connect(self._on_panorama_sector_selected)
                self.integration_helper.hole_selected.connect(self._on_panorama_hole_selected)
            else:
                self.logger.warning("⚠️ [DIAGNOSTIC] 全景预览组件集成失败")
        except Exception as e:
            self.logger.error(f"❌ [DIAGNOSTIC] 全景预览组件集成异常: {e}")
        
        # 定时器更新进度
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_progress_display)
        self.update_timer.start(1000)
        
        # 文件操作按钮连接
        if hasattr(self, 'load_dxf_btn'):
            self.load_dxf_btn.clicked.connect(self._on_load_dxf_clicked)
        if hasattr(self, 'export_data_btn'):
            self.export_data_btn.clicked.connect(self._on_export_data_clicked)

    def initialize_data(self):
        """初始化数据和UI状态"""
        self.log_message("系统初始化完成。")
        self.update_progress_display()
        
        # 初始化工具栏搜索建议
        self.update_toolbar_search_suggestions()

    def on_hole_clicked(self, hole_id, status):
        """处理孔点击事件，更新信息面板"""
        self.log_message(f"选中孔位: {hole_id}, 状态: {status.value}")
        self.update_hole_info_panel(hole_id)
        self.workpiece_diagram.highlight_hole(hole_id)

    # 搜索功能已移动到顶部工具栏，相关方法将在工具栏集成时处理

    def update_hole_info_panel(self, hole_id):
        """更新左侧的孔位信息面板"""
        point = self.workpiece_diagram.detection_points.get(hole_id)
        if point:
            self.selected_hole_id_label.setText(hole_id)
            self.selected_hole_pos_label.setText(f"({point.x():.2f}, {point.y():.2f})")
            self.selected_hole_status_label.setText(point.status.value)
            self.current_hole_id = hole_id

    def update_progress_display(self):
        """更新进度和统计信息 - 修复数据同步问题（生命安全相关）"""
        data = self.workpiece_diagram.get_detection_progress()
        
        # 更新统计面板
        self.total_label.setText(str(data.get("total", 0)))
        self.qualified_label.setText(str(data.get("qualified", 0)))
        self.unqualified_label.setText(str(data.get("unqualified", 0)))
        self.not_detected_label.setText(str(data.get("not_detected", 0) + data.get("real_data", 0)))

        # 更新进度条
        progress = data.get("progress", 0.0)
        self.progress_bar.setValue(int(progress))
        self.progress_label.setText(f"{progress:.1f}%")
        
        # 🚨 CRITICAL FIX 6: 修复进度信息数据同步问题（生命安全相关）
        # 同步更新完成率和合格率，确保与实际工件状态保持一致
        total_count = data.get("total", 0)
        completed_count = data.get("completed", 0)
        qualified_count = data.get("qualified", 0)
        
        # 计算真实的完成率和合格率
        if total_count > 0:
            completion_rate = (completed_count / total_count) * 100
            qualification_rate = (qualified_count / total_count) * 100 if total_count > 0 else 0.0
        else:
            completion_rate = 0.0
            qualification_rate = 0.0
        
        # 立即更新显示
        self.update_rates_display(completion_rate, qualification_rate)
        
        # 同步时间跟踪器数据以确保一致性
        if hasattr(self, 'time_tracker') and self.time_tracker:
            self.time_tracker.update_progress(completed_count, total_count)
            
        # 记录关键数据同步日志（仅在有实际数据时）
        if total_count > 0:
            self.logger.info(f"🔄 [数据同步] 总计:{total_count}, 完成:{completed_count}, 合格:{qualified_count}, 完成率:{completion_rate:.1f}%, 合格率:{qualification_rate:.1f}%")

    def log_message(self, message, color="black"):
        """向操作日志面板添加一条带时间戳的消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text_edit.append(f'<font color="{color}">[{timestamp}] {message}</font>')

    # --- 保留旧的控制逻辑 ---
    def on_start_detection(self):
        self.log_message("开始检测流程...", "blue")
        # ... (原有的逻辑)

    def on_pause_detection(self):
        self.log_message("检测暂停。", "orange")
        # ... (原有的逻辑)

    def on_stop_detection(self):
        self.log_message("检测停止。", "red")
        # ... (原有的逻辑)

    def on_reset_detection(self):
        self.workpiece_diagram.reset_all_holes()
        self.log_message("检测已重置。", "purple")
        # ... (原有的逻辑)
    
    # 新增：层级化视图控制方法
    def _on_macro_view_clicked(self):
        """处理宏观视图按钮点击"""
        try:
            if hasattr(self, 'macro_view_btn') and hasattr(self, 'micro_view_btn'):
                self.macro_view_btn.setChecked(True)
                self.micro_view_btn.setChecked(False)
            if hasattr(self, 'view_status_indicator'):
                self.view_status_indicator.setText("宏观视图 - 就绪")
                self.view_status_indicator.setStyleSheet(
                    "color: #2e7d32; "
                    "font-weight: bold; "
                    "padding: 5px 10px; "
                    "background-color: #e8f5e8; "
                    "border: 1px solid #4caf50; "
                    "border-radius: 3px;"
                )
            self.log_message("切换到宏观视图", "blue")
            # TODO: 实际的视图切换逻辑
        except Exception as e:
            self.logger.error(f"处理宏观视图切换失败: {e}")
    
    def _on_micro_view_clicked(self):
        """处理微观视图按钮点击"""
        try:
            if hasattr(self, 'macro_view_btn') and hasattr(self, 'micro_view_btn'):
                self.micro_view_btn.setChecked(True)
                self.macro_view_btn.setChecked(False)
            if hasattr(self, 'view_status_indicator'):
                self.view_status_indicator.setText("微观视图 - 就绪")
                self.view_status_indicator.setStyleSheet(
                    "color: #1976d2; "
                    "font-weight: bold; "
                    "padding: 5px 10px; "
                    "background-color: #e3f2fd; "
                    "border: 1px solid #2196f3; "
                    "border-radius: 3px;"
                )
            self.log_message("切换到微观视图", "blue")
            # TODO: 实际的视图切换逻辑
        except Exception as e:
            self.logger.error(f"处理微观视图切换失败: {e}")
    
    def _on_unify_direction_clicked(self):
        """处理方向统一按钮点击"""
        try:
            self.log_message("统一所有孔位方向为竖向", "green")
            # TODO: 实际的方向统一逻辑
        except Exception as e:
            self.logger.error(f"处理方向统一失败: {e}")
    
    # 新增：扩展视图控制方法
    def _on_fit_window_clicked(self):
        """处理适应窗口按钮点击"""
        try:
            # TODO: 实现适应窗口逻辑
            self.log_message("视图适应窗口", "blue")
        except Exception as e:
            self.logger.error(f"适应窗口失败: {e}")
    
    def _on_center_view_clicked(self):
        """处理居中显示按钮点击"""
        try:
            # TODO: 实现居中显示逻辑
            self.log_message("视图居中显示", "blue")
        except Exception as e:
            self.logger.error(f"居中显示失败: {e}")
    
    def _on_fullscreen_clicked(self):
        """处理全屏模式按钮点击"""
        try:
            # TODO: 实现全屏模式逻辑
            self.log_message("切换全屏模式", "blue")
        except Exception as e:
            self.logger.error(f"全屏模式切换失败: {e}")
    
    # 新增：导航功能方法
    def _on_goto_realtime_clicked(self):
        """处理跳转到实时监控按钮点击"""
        try:
            # 使用导航管理器进行跳转
            hole_id = self.current_hole_id
            success = self.quick_nav_helper.quick_jump_to_hole_realtime(hole_id) if hole_id else self.navigation_manager.navigate_to_realtime()
            
            if success:
                self.log_message(f"跳转到实时监控 - 孔位: {hole_id or '全部'}", "blue")
            else:
                self.log_message("跳转到实时监控失败", "orange")
                
        except Exception as e:
            self.logger.error(f"跳转到实时监控失败: {e}")
    
    def _on_goto_history_clicked(self):
        """处理跳转到历史数据按钮点击"""
        try:
            # 使用导航管理器进行跳转
            hole_id = self.current_hole_id
            success = self.quick_nav_helper.quick_jump_to_hole_history(hole_id) if hole_id else self.navigation_manager.navigate_to_history()
            
            if success:
                self.log_message(f"跳转到历史数据 - 孔位: {hole_id or '全部'}", "blue")
            else:
                self.log_message("跳转到历史数据失败", "orange")
                
        except Exception as e:
            self.logger.error(f"跳转到历史数据失败: {e}")
    
    # 新增：文件操作方法
    def _on_load_dxf_clicked(self):
        """处理加载DXF文件按钮点击"""
        try:
            # TODO: 实现DXF文件加载对话框
            self.log_message("打开DXF文件选择对话框", "blue")
        except Exception as e:
            self.logger.error(f"加载DXF文件失败: {e}")
    
    def _on_export_data_clicked(self):
        """处理导出数据按钮点击"""
        try:
            # TODO: 实现数据导出逻辑
            self.log_message("导出检测数据", "blue")
        except Exception as e:
            self.logger.error(f"导出数据失败: {e}")
    
    # 新增：工具栏信号处理方法
    def _on_toolbar_product_selected(self, action):
        """处理工具栏产品选择信号"""
        try:
            if action == "open_dialog":
                self.logger.info("打开产品选择对话框")
                self._open_product_selection_dialog()
            else:
                # 兼容旧的直接产品名称传递
                self.log_message(f"产品选择: {action}", "blue")
                self._on_product_selected(action)
        except Exception as e:
            self.logger.error(f"处理产品选择失败: {e}")
    
    def _open_product_selection_dialog(self):
        """打开产品选择对话框"""
        try:
            # 尝试导入产品选择对话框
            try:
                from .product_selection import ProductSelectionDialog
                dialog = ProductSelectionDialog(self)
                
                if dialog.exec():
                    selected_product = dialog.get_selected_product()
                    if selected_product:
                        self._on_product_selected(selected_product.model_name, selected_product)
                        self.logger.info(f"用户选择产品: {selected_product.model_name}")
                    else:
                        self.logger.warning("用户取消了产品选择")
                        
            except ImportError:
                # 如果没有产品选择模块，使用简单的对话框
                from PySide6.QtWidgets import QInputDialog
                
                # 获取可用产品列表（模拟数据）
                available_products = [
                    "默认产品",
                    "产品型号A", 
                    "产品型号B",
                    "产品型号C",
                    "自定义产品"
                ]
                
                product, ok = QInputDialog.getItem(
                    self, 
                    "选择产品型号", 
                    "请选择要检测的产品型号:",
                    available_products,
                    0,
                    False
                )
                
                if ok and product:
                    self._on_product_selected(product, None)
                    self.logger.info(f"用户选择产品: {product}")
                else:
                    self.logger.warning("用户取消了产品选择")
                    
        except Exception as e:
            self.logger.error(f"打开产品选择对话框失败: {e}")
            # 回退：直接设置默认产品
            self._on_product_selected("默认产品", None)
    
    def _on_product_selected(self, product_name, product_obj=None):
        """处理产品选择完成"""
        try:
            self.logger.info(f"设置当前产品: {product_name}")
            
            # 更新工具栏显示
            if hasattr(self, 'toolbar') and self.toolbar:
                self.toolbar.set_product_name(product_name)
            
            # 记录操作日志
            self.log_message(f"已选择产品: {product_name}", "green")
            
            # 触发产品配置加载
            self._load_product_configuration(product_name, product_obj)
            
        except Exception as e:
            self.logger.error(f"处理产品选择完成失败: {e}")
    
    def _load_product_configuration(self, product_name, product_obj=None):
        """加载产品配置"""
        try:
            self.logger.info(f"开始加载产品配置: {product_name}")
            
            # 保存产品对象到实例变量，以便回调使用
            self.current_loading_product = product_obj
            self.current_loading_product_name = product_name
            
            if product_obj:
                # 如果有完整的产品对象，加载详细配置
                self.log_message(f"加载产品详细配置: {product_name}", "blue")
                self.log_message(f"标准直径: {product_obj.standard_diameter:.3f}mm", "blue")
                self.log_message(f"公差范围: {product_obj.tolerance_range}", "blue")
                
                # 检查DXF文件
                dxf_file_path = getattr(product_obj, 'dxf_file_path', None)
                if dxf_file_path and os.path.exists(dxf_file_path):
                    self.log_message(f"找到关联DXF文件: {dxf_file_path}", "blue")
                    self.current_dxf_file_path = dxf_file_path
                else:
                    self.log_message("未找到关联DXF文件", "orange")
                    self.current_dxf_file_path = None
            else:
                # 简单模式，仅显示产品名称
                self.log_message(f"正在加载 {product_name} 的配置文件...", "blue")
                self.current_dxf_file_path = None
            
            # 使用QTimer模拟异步加载过程
            from PySide6.QtCore import QTimer
            timer = QTimer()
            timer.singleShot(1000, lambda: self._on_product_config_loaded(product_name))
            
        except Exception as e:
            self.logger.error(f"加载产品配置失败: {e}")
            self.log_message(f"加载 {product_name} 配置失败: {e}", "red")
    
    def _on_product_config_loaded(self, product_name):
        """产品配置加载完成回调"""
        try:
            self.log_message(f"产品 {product_name} 配置加载完成", "green")
            self.logger.info(f"产品配置加载完成: {product_name}")
            
            # 获取保存的产品对象和DXF文件路径
            product_obj = getattr(self, 'current_loading_product', None)
            dxf_file_path = getattr(self, 'current_dxf_file_path', None)
            
            # 1. 更新工件图显示
            if hasattr(self, 'workpiece_diagram') and self.workpiece_diagram:
                self.logger.info("开始更新工件图显示")
                self.log_message("正在更新工件图显示...", "blue")
                
                # 调用工件图的产品数据加载方法
                self.workpiece_diagram.load_product_data(product_obj, dxf_file_path)
                self.log_message("工件图显示更新完成", "green")
            else:
                self.logger.warning("未找到工件图组件")
                self.log_message("警告: 未找到工件图组件", "orange")
            
            # 2. 更新文件信息显示
            if product_obj:
                # 更新产品相关的文件信息
                file_info = f"产品: {product_obj.model_name}"
                if dxf_file_path:
                    file_size = self._get_file_size(dxf_file_path)
                    self.update_file_info(dxf_file_path, file_size, "配置完成")
                else:
                    self.update_file_info(file_info, "N/A", "配置完成")
            
            # 3. 更新统计信息
            if hasattr(self, 'workpiece_diagram') and self.workpiece_diagram:
                # 获取当前孔位统计
                all_holes = self.workpiece_diagram.get_all_holes()
                total_count = len(all_holes)
                
                # 更新统计显示
                if hasattr(self, 'total_label'):
                    self.total_label.setText(str(total_count))
                if hasattr(self, 'not_detected_label'):
                    self.not_detected_label.setText(str(total_count))  # 初始都是未检测
                if hasattr(self, 'qualified_label'):
                    self.qualified_label.setText("0")
                if hasattr(self, 'unqualified_label'):
                    self.unqualified_label.setText("0")
                
                self.log_message(f"统计信息已更新: 总计 {total_count} 个孔位", "blue")
            
            # 4. 更新进度显示
            self.update_rates_display(0.0, 0.0)  # 重置进度
            
            # 5. 更新搜索建议
            self.update_toolbar_search_suggestions()
            
            # 6. 清理临时变量
            self.current_loading_product = None
            self.current_loading_product_name = None
            self.current_dxf_file_path = None
            
            self.logger.info("产品配置加载和UI更新全部完成")
            self.log_message(f"✅ 产品 {product_name} 加载完成并已更新显示", "green")
            
        except Exception as e:
            self.logger.error(f"产品配置加载完成处理失败: {e}")
            self.log_message(f"配置加载完成处理失败: {e}", "red")
    
    def _get_file_size(self, file_path):
        """获取文件大小的友好显示格式"""
        try:
            if os.path.exists(file_path):
                size_bytes = os.path.getsize(file_path)
                if size_bytes < 1024:
                    return f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    return f"{size_bytes / 1024:.1f} KB"
                else:
                    return f"{size_bytes / (1024 * 1024):.1f} MB"
            else:
                return "N/A"
        except Exception:
            return "N/A"
    
    def _on_toolbar_search_requested(self, search_text):
        """处理工具栏搜索请求信号"""
        try:
            hole_id = search_text.strip().upper()
            if hole_id in self.workpiece_diagram.get_all_holes():
                self.log_message(f"通过搜索定位到孔: {hole_id}")
                self.update_hole_info_panel(hole_id)
                self.workpiece_diagram.highlight_hole(hole_id)
                self.workpiece_diagram.center_on_hole(hole_id)
            else:
                self.log_message(f"警告: 未找到孔位 '{hole_id}'", "orange")
        except Exception as e:
            self.logger.error(f"处理搜索请求失败: {e}")
    
    def _on_toolbar_filter_changed(self, filter_option):
        """处理工具栏过滤器变化信号"""
        try:
            self.log_message(f"过滤器变化: {filter_option}", "blue")
            # TODO: 实现过滤逻辑
        except Exception as e:
            self.logger.error(f"处理过滤器变化失败: {e}")
    
    # 新增：工具栏辅助方法
    def update_toolbar_search_suggestions(self):
        """更新工具栏搜索建议"""
        try:
            if hasattr(self, 'toolbar') and self.toolbar:
                all_holes = self.workpiece_diagram.get_all_holes()
                self.toolbar.update_search_suggestions(all_holes)
        except Exception as e:
            self.logger.error(f"更新搜索建议失败: {e}")
    
    def set_toolbar_product(self, product_name):
        """设置工具栏显示的产品名称"""
        try:
            if hasattr(self, 'toolbar') and self.toolbar:
                self.toolbar.set_product_name(product_name)
        except Exception as e:
            self.logger.error(f"设置工具栏产品名称失败: {e}")
    
    def _elide_text(self, text: str, max_width: int = 200) -> str:
        """
        【辅助方法】手动实现文本省略功能
        由于QLabel没有setTextElideMode方法，我们手动处理文本省略
        """
        if len(text) <= 30:  # 如果文本较短，直接返回
            return text
        
        # 简单的中间省略实现
        if len(text) > 30:
            return text[:12] + "..." + text[-12:]
        return text
    
    def update_dxf_file_display(self, file_path: str):
        """
        【新增方法】更新DXF文件显示，支持文本省略
        """
        if file_path:
            from pathlib import Path
            file_name = Path(file_path).name
            elided_name = self._elide_text(file_name)
            self.dxf_file_label.setText(elided_name)
            self.dxf_file_label.setToolTip(file_path)  # 完整路径作为工具提示
        else:
            self.dxf_file_label.setText("未加载")
            self.dxf_file_label.setToolTip("")
    
    def update_file_info(self, file_path: str, file_size: str = "", load_time: str = ""):
        """更新文件信息显示"""
        try:
            self.update_dxf_file_display(file_path)
            if hasattr(self, 'file_size_label'):
                self.file_size_label.setText(file_size or "--")
            if hasattr(self, 'load_time_label'):
                self.load_time_label.setText(load_time or "--")
        except Exception as e:
            self.logger.error(f"更新文件信息失败: {e}")
    
    def update_rates_display(self, completion_rate: float = 0.0, qualification_rate: float = 0.0):
        """更新完成率和合格率显示"""
        try:
            if hasattr(self, 'completion_rate_label'):
                self.completion_rate_label.setText(f"{completion_rate:.1f}%")
            if hasattr(self, 'qualification_rate_label'):
                self.qualification_rate_label.setText(f"{qualification_rate:.1f}%")
        except Exception as e:
            self.logger.error(f"更新率值显示失败: {e}")
    
    def update_time_display(self, detection_time: str = "00:00:00", estimated_time: str = "--"):
        """更新时间显示"""
        try:
            if hasattr(self, 'detection_time_label'):
                self.detection_time_label.setText(detection_time)
            if hasattr(self, 'estimated_time_label'):
                self.estimated_time_label.setText(estimated_time)
        except Exception as e:
            self.logger.error(f"更新时间显示失败: {e}")
    
    # ===== 性能优化器相关方法 =====
    
    def _on_performance_metrics_updated(self, metrics: dict):
        """处理性能指标更新"""
        try:
            # 更新性能监控面板
            if hasattr(self, 'fps_label'):
                fps = metrics.get('frame_rate', 0)
                self.fps_label.setText(f"{fps:.1f} FPS")
            
            if hasattr(self, 'memory_label'):
                memory = metrics.get('memory_usage_mb', 0)
                self.memory_label.setText(f"{memory:.0f}MB")
            
            if hasattr(self, 'render_time_label'):
                render_time = metrics.get('render_time_ms', 0)
                self.render_time_label.setText(f"{render_time:.1f}ms")
            
            if hasattr(self, 'cache_hit_label'):
                cache_hit = metrics.get('cache_hit_rate', 0) * 100
                self.cache_hit_label.setText(f"{cache_hit:.0f}%")
                
        except Exception as e:
            self.logger.error(f"更新性能指标失败: {e}")
    
    def _on_optimization_applied(self, description: str):
        """处理优化应用事件"""
        self.log_message(f"🚀 {description}", "green")
    
    def _on_performance_warning(self, warning: str):
        """处理性能警告"""
        self.log_message(f"⚠️ {warning}", "orange")
    
    # ===== 文件操作相关方法 =====
    
    def _on_load_dxf_clicked(self):
        """处理加载DXF按钮点击"""
        try:
            from PySide6.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getOpenFileNames(
                self, "选择DXF文件", "",
                "DXF文件 (*.dxf *.dwg);;所有文件 (*)"
            )
            
            if file_path:
                self.file_operations_manager.import_dxf_files(file_path)
                self.log_message(f"开始加载DXF文件: {len(file_path)} 个文件", "blue")
                
        except Exception as e:
            self.logger.error(f"加载DXF文件失败: {e}")
            self.log_message(f"加载DXF文件失败: {e}", "red")
    
    def _on_export_data_clicked(self):
        """处理导出数据按钮点击"""
        try:
            from .file_operations import ExportConfig, FileFormat, ExportType
            from PySide6.QtWidgets import QFileDialog
            
            # 选择导出路径
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出检测数据", "",
                "JSON文件 (*.json);;CSV文件 (*.csv);;Excel文件 (*.xlsx)"
            )
            
            if file_path:
                # 准备导出配置
                file_format = FileFormat.JSON
                if file_path.endswith('.csv'):
                    file_format = FileFormat.CSV
                elif file_path.endswith('.xlsx'):
                    file_format = FileFormat.XLSX
                
                export_config = ExportConfig(
                    export_type=ExportType.DETECTION_RESULTS,
                    file_format=file_format,
                    output_path=file_path
                )
                
                # 获取检测数据
                detection_data = self.workpiece_diagram.get_detection_progress()
                
                # 开始导出
                operation_id = self.file_operations_manager.export_detection_data(detection_data, export_config)
                self.log_message(f"开始导出数据: {operation_id}", "blue")
                
        except Exception as e:
            self.logger.error(f"导出数据失败: {e}")
            self.log_message(f"导出数据失败: {e}", "red")
    
    def _on_file_operation_started(self, operation_id: str):
        """处理文件操作开始"""
        self.log_message(f"📁 文件操作开始: {operation_id}", "blue")
    
    def _on_file_operation_progress(self, operation_id: str, progress: float):
        """处理文件操作进度"""
        self.log_message(f"🔄 文件操作进度: {operation_id} - {progress:.1f}%", "blue")
    
    def _on_file_operation_completed(self, operation_id: str, success: bool, result: str):
        """处理文件操作完成"""
        if success:
            self.log_message(f"✅ 文件操作完成: {result}", "green")
        else:
            self.log_message(f"❌ 文件操作失败: {result}", "red")
    
    def _on_file_operation_error(self, operation_id: str, error_msg: str):
        """处理文件操作错误"""
        self.log_message(f"❌ 文件操作错误: {operation_id} - {error_msg}", "red")
    
    def _on_files_dropped(self, file_paths: list):
        """处理文件拖放事件"""
        self.log_message(f"📁 接收到 {len(file_paths)} 个文件", "blue")
        for file_path in file_paths:
            self.log_message(f"  - {file_path}", "gray")
    
    def _on_time_updated(self, time_stats):
        """时间跟踪器更新信号处理 - 修复时间跟踪显示问题（生命安全相关）"""
        try:
            # 🚨 CRITICAL FIX 7: 修复时间跟踪显示问题（生命安全相关）
            # 确保时间跟踪器数据与实际工件状态同步
            
            # 获取实际工件进度数据
            workpiece_data = self.workpiece_diagram.get_detection_progress()
            total_holes = workpiece_data.get("total", 0)
            completed_holes = workpiece_data.get("completed", 0)
            qualified_holes = workpiece_data.get("qualified", 0)
            
            # 强制同步时间跟踪器与实际数据
            if total_holes > 0:
                self.time_tracker.force_sync_progress(completed_holes, total_holes)
            
            # 更新时间显示
            elapsed_time = self.time_tracker.get_formatted_elapsed_time()
            remaining_time = self.time_tracker.get_formatted_remaining_time()
            self.update_time_display(elapsed_time, remaining_time)
            
            # 获取同步后的数据，确保一致性
            summary = self.time_tracker.get_time_summary()
            completion_rate = summary['progress_percentage']
            qualification_rate = (qualified_holes / total_holes * 100) if total_holes > 0 else 0.0
            
            # 更新显示
            self.update_rates_display(completion_rate, qualification_rate)
            
            # 记录关键时间跟踪同步日志（仅在有进度时）
            if completion_rate > 0:
                self.logger.info(f"⏱️ [时间同步] 完成:{completed_holes}/{total_holes}, 进度:{completion_rate:.1f}%, 合格率:{qualification_rate:.1f}%, 预计剩余:{remaining_time}")
                
        except Exception as e:
            self.logger.error(f"处理时间更新失败: {e}")
            # 在错误情况下，依然尝试显示基本信息以保证安全
            if hasattr(self, 'time_tracker'):
                try:
                    elapsed = self.time_tracker.get_formatted_elapsed_time()
                    self.update_time_display(elapsed, "--")
                except:
                    self.update_time_display("00:00:00", "--")
    
    def _on_progress_updated(self, progress_percentage, remaining_time_seconds):
        """进度更新信号处理"""
        try:
            # 更新进度条
            if hasattr(self, 'progress_bar'):
                self.progress_bar.setValue(int(progress_percentage))
            
            # 可以在这里添加更多UI更新逻辑
            
        except Exception as e:
            self.logger.error(f"处理进度更新失败: {e}")
    
    def start_detection_with_tracking(self, total_holes: int):
        """启动带时间跟踪的检测"""
        try:
            # 重置并启动时间跟踪器
            self.time_tracker.reset()
            self.time_tracker.start_detection(total_holes)
            
            # 调用原有的开始检测逻辑
            self.on_start_detection()
            
            self.logger.info(f"🚀 开始检测任务，共 {total_holes} 个孔位")
            
        except Exception as e:
            self.logger.error(f"启动检测跟踪失败: {e}")
    
    def complete_hole_with_tracking(self, hole_id: str):
        """完成孔位检测并更新跟踪"""
        try:
            self.time_tracker.complete_hole_detection(hole_id)
            
        except Exception as e:
            self.logger.error(f"完成孔位跟踪失败: {e}")
    
    def update_detection_progress(self, completed_count: int, total_count: int = None, qualified_count: int = 0):
        """更新检测进度（供外部调用）"""
        try:
            # 更新时间跟踪器
            self.time_tracker.update_progress(completed_count, total_count)
            
            # 计算合格率
            qualification_rate = 0.0
            if completed_count > 0:
                qualification_rate = (qualified_count / completed_count) * 100
            
            # 更新显示
            summary = self.time_tracker.get_time_summary()
            self.update_rates_display(summary['progress_percentage'], qualification_rate)
            
        except Exception as e:
            self.logger.error(f"更新检测进度失败: {e}")
    
    def _on_panorama_sector_selected(self, sector_id: int):
        """处理全景预览扇形选择"""
        try:
            self.logger.info(f"🎯 [全景预览] 用户选择扇形: {sector_id}")
            
            # 更新当前选择的扇形
            self.current_hole_id = None  # 清除孔位选择
            
            # 在工件图中高亮对应扇形
            if hasattr(self, 'workpiece_diagram'):
                self.workpiece_diagram.highlight_sector(sector_id)
            
            # 更新扇形统计显示
            if hasattr(self.integration_helper, 'update_sector_statistics_placeholder'):
                from .ui_components.integration_helper import update_sector_statistics_placeholder
                update_sector_statistics_placeholder(self, self.integration_helper)
            
            # 记录消息
            self.log_message(f"已选择扇形 {sector_id}", "blue")
            
        except Exception as e:
            self.logger.error(f"处理全景预览扇形选择失败: {e}")
    
    def _on_panorama_hole_selected(self, hole_id: str):
        """处理全景预览孔位选择"""
        try:
            self.logger.info(f"🎯 [全景预览] 用户选择孔位: {hole_id}")
            
            # 更新当前选择的孔位
            self.current_hole_id = hole_id
            
            # 在工件图中高亮对应孔位
            if hasattr(self, 'workpiece_diagram'):
                self.workpiece_diagram.highlight_hole(hole_id)
            
            # 更新孔位信息面板
            self.update_hole_info_panel(hole_id)
            
            # 记录消息
            self.log_message(f"已选择孔位 {hole_id}", "green")
            
        except Exception as e:
            self.logger.error(f"处理全景预览孔位选择失败: {e}")
    
    # 新增：模拟系统信号处理方法
    def _on_simulation_hole_detected(self, hole_id: str, result: str):
        """处理模拟检测孔位完成"""
        try:
            # 更新工件图显示
            if hasattr(self, 'workpiece_diagram'):
                # 根据结果更新孔位状态
                if result == "qualified":
                    # 更新为合格状态
                    pass
                elif result == "unqualified":
                    # 更新为不合格状态
                    pass
                elif result == "error":
                    # 更新为错误状态
                    pass
            
            # 记录到日志
            self.log_message(f"模拟检测: {hole_id} -> {result}", "purple")
            
            # 如果当前选中的是这个孔位，更新信息面板
            if self.current_hole_id == hole_id:
                self.update_hole_info_panel(hole_id)
                
        except Exception as e:
            self.logger.error(f"处理模拟孔位检测失败: {e}")
    
    def _on_simulation_progress_updated(self, progress: float):
        """处理模拟进度更新"""
        try:
            # 更新进度条显示
            if hasattr(self, 'progress_bar'):
                self.progress_bar.setValue(int(progress))
            if hasattr(self, 'progress_label'):
                self.progress_label.setText(f"{progress:.1f}%")
                
        except Exception as e:
            self.logger.error(f"处理模拟进度更新失败: {e}")
    
    def _on_simulation_batch_completed(self, batch_number: int):
        """处理模拟批次完成"""
        try:
            self.log_message(f"模拟批次 {batch_number} 完成", "green")
            
        except Exception as e:
            self.logger.error(f"处理模拟批次完成失败: {e}")
    
    def _on_simulation_started(self):
        """处理模拟开始"""
        try:
            self.log_message("模拟检测已开始", "blue")
            
            # 更新模拟控制组件状态
            if hasattr(self, 'simulation_control_widget') and self.simulation_control_widget:
                self.simulation_control_widget.update_simulation_state(SimulationState.RUNNING)
                
        except Exception as e:
            self.logger.error(f"处理模拟开始失败: {e}")
    
    def _on_simulation_stopped(self):
        """处理模拟停止"""
        try:
            self.log_message("模拟检测已停止", "orange")
            
            # 更新模拟控制组件状态
            if hasattr(self, 'simulation_control_widget') and self.simulation_control_widget:
                state = self.simulation_system.get_simulation_state()
                self.simulation_control_widget.update_simulation_state(state)
                
        except Exception as e:
            self.logger.error(f"处理模拟停止失败: {e}")
    
    def _on_simulation_error(self, error_msg: str):
        """处理模拟错误"""
        try:
            self.log_message(f"模拟错误: {error_msg}", "red")
            
        except Exception as e:
            self.logger.error(f"处理模拟错误失败: {e}")
    
    def _on_simulation_start_requested(self, config_dict: dict):
        """处理模拟开始请求"""
        try:
            # 更新模拟系统配置
            self.simulation_system.update_config(**config_dict)
            
            # 获取当前所有孔位ID
            all_holes = self.workpiece_diagram.get_all_holes()
            if not all_holes:
                # 生成示例孔位ID用于测试
                all_holes = [f"H{i:03d}" for i in range(1, 51)]  # 生成50个示例孔位
            
            # 开始模拟
            success = self.simulation_system.start_simulation(all_holes)
            if not success:
                self.log_message("启动模拟失败", "red")
                
        except Exception as e:
            self.logger.error(f"处理模拟开始请求失败: {e}")
    
    def _on_simulation_config_changed(self, config_dict: dict):
        """处理模拟配置变化"""
        try:
            # 更新模拟系统配置
            self.simulation_system.update_config(**config_dict)
            
        except Exception as e:
            self.logger.error(f"处理模拟配置变化失败: {e}")
    
    # 新增：导航管理器信号处理方法
    def _on_navigation_requested(self, target: str, parameters: dict):
        """处理导航请求"""
        try:
            self.log_message(f"导航请求: {target}", "blue")
            
            # 发出原有的导航信号以保持兼容性
            if target == "realtime_preview":
                hole_id = parameters.get("hole_id", "")
                self.navigate_to_realtime.emit(hole_id)
            elif target == "history_view":
                hole_id = parameters.get("hole_id", "")
                self.navigate_to_history.emit(hole_id)
            
            # 标记导航完成
            self.navigation_manager.on_navigation_completed(target)
            
        except Exception as e:
            self.logger.error(f"处理导航请求失败: {e}")
    
    def _on_navigation_completed(self, target: str):
        """处理导航完成"""
        try:
            self.log_message(f"导航完成: {target}", "green")
            
        except Exception as e:
            self.logger.error(f"处理导航完成失败: {e}")
    
    def _on_navigation_failed(self, target: str, error: str):
        """处理导航失败"""
        try:
            self.log_message(f"导航失败: {target} - {error}", "red")
            
        except Exception as e:
            self.logger.error(f"处理导航失败失败: {e}")


class ControlPanel(QGroupBox):
    """(基本无变化) 控制面板组件"""
    start_detection = Signal()
    pause_detection = Signal()
    stop_detection = Signal()
    reset_detection = Signal()
    
    def __init__(self, title="检测操作", parent=None):
        super().__init__(title, parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QGridLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(15, 15, 15, 15)
        
        self.start_button = QPushButton("开始检测")
        self.pause_button = QPushButton("暂停检测")
        self.stop_button = QPushButton("停止检测")
        self.reset_button = QPushButton("重置")
        
        # 设置统一尺寸
        for btn in [self.start_button, self.pause_button, self.stop_button, self.reset_button]:
            btn.setFixedSize(140, 45)
        
        # 设置按钮类型属性
        self.start_button.setProperty("class", "success")
        self.pause_button.setProperty("class", "warning")
        self.stop_button.setProperty("class", "danger")
        self.reset_button.setProperty("class", "secondary")
        
        # 应用统一按钮样式
        self._apply_control_button_styles()
        
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        
        layout.addWidget(self.start_button, 0, 0)
        layout.addWidget(self.pause_button, 0, 1)
        layout.addWidget(self.stop_button, 1, 0)
        layout.addWidget(self.reset_button, 1, 1)
        
        self.start_button.clicked.connect(self.start_detection.emit)
        self.pause_button.clicked.connect(self.pause_detection.emit)
        self.stop_button.clicked.connect(self.stop_detection.emit)
        self.reset_button.clicked.connect(self.reset_detection.emit)
    
    def _apply_control_button_styles(self):
        """为控制面板按钮应用统一样式 - 使用StyleManager"""
        # 使用StyleManager为不同类型的按钮应用相应样式
        StyleManager.apply_button_style(self.start_button, ButtonVariant.SUCCESS, ButtonSize.MEDIUM)
        StyleManager.apply_button_style(self.pause_button, ButtonVariant.WARNING, ButtonSize.MEDIUM)
        StyleManager.apply_button_style(self.stop_button, ButtonVariant.DANGER, ButtonSize.MEDIUM)
        StyleManager.apply_button_style(self.reset_button, ButtonVariant.SECONDARY, ButtonSize.MEDIUM)