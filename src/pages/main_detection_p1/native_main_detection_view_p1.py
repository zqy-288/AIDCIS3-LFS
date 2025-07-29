"""
原生主检测视图 - 完全还原old版本UI布局
使用现有重构后的文件和功能模块，严格按照old版本的三栏式布局实现
采用高内聚、低耦合的设计原则
"""

import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QProgressBar, QGroupBox,
    QLineEdit, QTextEdit, QFrame, QSplitter, QCompleter,
    QComboBox, QCheckBox, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer, QStringListModel
from PySide6.QtGui import QFont, QColor

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入现有的重构后功能模块
try:
    # 控制器和服务
    from src.controllers.main_window_controller import MainWindowController
    from src.controllers.services.search_service import SearchService
    from src.controllers.services.status_service import StatusService
    from src.controllers.services.file_service import FileService
    
    # UI组件
    from src.ui.components.toolbar_component import ToolbarComponent
    from src.ui.components.info_panel_component import InfoPanelComponent
    from src.ui.components.operations_panel_component import OperationsPanelComponent
    from src.ui.view_models.main_view_model import MainViewModel
    
    # 图形组件
    from src.core_business.graphics.graphics_view import OptimizedGraphicsView
    from src.core_business.graphics.dynamic_sector_view import DynamicSectorDisplayWidget
    from src.core_business.graphics.complete_panorama_widget import CompletePanoramaWidget
    
    # 数据模型
    from src.core_business.models.hole_data import HoleCollection
    from src.models.product_model import get_product_manager
    from src.modules.product_selection import ProductSelectionDialog
    
    HAS_REFACTORED_MODULES = True
except ImportError as e:
    logging.warning(f"部分重构模块导入失败: {e}")
    HAS_REFACTORED_MODULES = False


class NativeLeftInfoPanel(QWidget):
    """左侧信息面板 - 完全还原old版本 (高内聚组件)"""
    
    # 信号定义
    hole_info_updated = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 组件状态
        self.current_hole_data = None
        self.detection_stats = {}
        
        # 设置固定宽度 (old版本: 380px)
        self.setFixedWidth(380)
        
        # 初始化UI
        self.setup_ui()
        self.initialize_data()
        
    def setup_ui(self):
        """设置UI布局 - 严格按照old版本结构"""
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(5, 5, 5, 5)

        # 设置全局字体
        panel_font = QFont()
        panel_font.setPointSize(10)
        self.setFont(panel_font)

        # 组标题字体
        group_font = QFont()
        group_font.setPointSize(10)
        group_font.setBold(True)

        # 1. 检测进度组 (恢复old版本的设计)
        self.progress_group = self._create_progress_group(group_font)
        layout.addWidget(self.progress_group)

        # 2. 状态统计组
        self.stats_group = self._create_stats_group(group_font)
        layout.addWidget(self.stats_group)

        # 3. 选中孔位信息组
        self.hole_info_group = self._create_hole_info_group(group_font)
        layout.addWidget(self.hole_info_group)

        # 4. 文件信息组
        self.file_info_group = self._create_file_info_group(group_font)
        layout.addWidget(self.file_info_group)

        # 5. 全景预览组 (old版本关键组件: 360×420px)
        self.panorama_group = self._create_panorama_group(group_font)
        layout.addWidget(self.panorama_group)

        # 6. 选中扇形组
        self.sector_stats_group = self._create_sector_stats_group(group_font)
        layout.addWidget(self.sector_stats_group)

        layout.addStretch()

    def _create_progress_group(self, group_font):
        """创建检测进度组 - 恢复old版本设计"""
        group = QGroupBox("检测进度")
        group.setFont(group_font)
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumHeight(18)
        layout.addWidget(self.progress_bar)

        # 批次信息
        self.current_batch_label = QLabel("检测批次: 未开始")
        self.current_batch_label.setFont(QFont("", 9))
        layout.addWidget(self.current_batch_label)

        # 已完成和待完成数量
        count_layout = QHBoxLayout()
        count_layout.setSpacing(2)
        self.completed_count_label = QLabel("已完成: 0")
        self.pending_count_label = QLabel("待完成: 0")
        self.completed_count_label.setFont(QFont("", 9))
        self.pending_count_label.setFont(QFont("", 9))
        count_layout.addWidget(self.completed_count_label)
        count_layout.addWidget(self.pending_count_label)
        layout.addLayout(count_layout)

        # 合格率和完成率
        rate_layout = QHBoxLayout()
        rate_layout.setSpacing(2)
        self.completion_rate_label = QLabel("完成率: 0%")
        self.qualification_rate_label = QLabel("合格率: 0%")
        self.completion_rate_label.setFont(QFont("", 9))
        self.qualification_rate_label.setFont(QFont("", 9))
        rate_layout.addWidget(self.completion_rate_label)
        rate_layout.addWidget(self.qualification_rate_label)
        layout.addLayout(rate_layout)

        return group

    def _create_stats_group(self, group_font):
        """创建状态统计组"""
        group = QGroupBox("状态统计")
        group.setFont(group_font)
        layout = QGridLayout(group)
        layout.setSpacing(2)
        layout.setContentsMargins(5, 5, 5, 5)

        label_font = QFont()
        label_font.setPointSize(9)

        # 状态统计标签 (old版本样式)
        self.total_label = QLabel("总数: 0")
        self.qualified_label = QLabel("合格: 0")
        self.unqualified_label = QLabel("异常: 0")
        self.not_detected_label = QLabel("待检: 0")
        self.blind_label = QLabel("盲孔: 0")
        self.tie_rod_label = QLabel("拉杆: 0")

        for label in [self.total_label, self.qualified_label, self.unqualified_label,
                     self.not_detected_label, self.blind_label, self.tie_rod_label]:
            label.setFont(label_font)

        # 网格布局 (old版本样式: 3列2行)
        layout.addWidget(self.total_label, 0, 0)
        layout.addWidget(self.qualified_label, 0, 1)
        layout.addWidget(self.unqualified_label, 0, 2)
        layout.addWidget(self.not_detected_label, 1, 0)
        layout.addWidget(self.blind_label, 1, 1)
        layout.addWidget(self.tie_rod_label, 1, 2)

        return group

    def _create_hole_info_group(self, group_font):
        """创建孔位信息组"""
        group = QGroupBox("选中孔位信息")
        group.setFont(group_font)
        layout = QGridLayout(group)
        layout.setSpacing(2)
        layout.setContentsMargins(5, 5, 5, 5)

        label_font = QFont()
        label_font.setPointSize(9)

        # 孔位信息标签 (两行两列布局)
        # 第一行：ID 和 坐标
        layout.addWidget(QLabel("ID:"), 0, 0)
        self.selected_hole_id_label = QLabel("--")
        self.selected_hole_id_label.setFont(label_font)
        layout.addWidget(self.selected_hole_id_label, 0, 1)

        layout.addWidget(QLabel("坐标:"), 0, 2)
        self.selected_hole_pos_label = QLabel("--")
        self.selected_hole_pos_label.setFont(label_font)
        layout.addWidget(self.selected_hole_pos_label, 0, 3)

        # 第二行：状态 和 描述
        layout.addWidget(QLabel("状态:"), 1, 0)
        self.selected_hole_status_label = QLabel("--")
        self.selected_hole_status_label.setFont(label_font)
        layout.addWidget(self.selected_hole_status_label, 1, 1)

        layout.addWidget(QLabel("描述:"), 1, 2)
        self.selected_hole_desc_label = QLabel("--")
        self.selected_hole_desc_label.setFont(label_font)
        layout.addWidget(self.selected_hole_desc_label, 1, 3)

        return group

    def _create_file_info_group(self, group_font):
        """创建文件信息组"""
        group = QGroupBox("文件信息")
        group.setFont(group_font)
        layout = QGridLayout(group)
        layout.setSpacing(2)
        layout.setContentsMargins(5, 5, 5, 5)

        label_font = QFont()
        label_font.setPointSize(9)

        # DXF文件信息 (old版本样式)
        layout.addWidget(QLabel("DXF文件:"), 0, 0)
        self.dxf_file_label = QLabel("未加载")
        self.dxf_file_label.setFont(label_font)
        self.dxf_file_label.setMaximumWidth(200)
        self.dxf_file_label.setWordWrap(False)
        layout.addWidget(self.dxf_file_label, 0, 1)

        layout.addWidget(QLabel("产品型号:"), 1, 0)
        self.product_label = QLabel("--")
        self.product_label.setFont(label_font)
        layout.addWidget(self.product_label, 1, 1)

        return group

    def _create_panorama_group(self, group_font):
        """创建全景预览组 - old版本关键组件 (360×420px)"""
        group = QGroupBox("全景预览")
        group.setFont(group_font)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(5, 5, 5, 5)

        # 创建全景预览组件 (使用重构后的CompletePanoramaWidget)
        if HAS_REFACTORED_MODULES:
            try:
                self.sidebar_panorama = CompletePanoramaWidget()
                self.sidebar_panorama.setFixedSize(360, 420)  # old版本精确尺寸
                self.sidebar_panorama.setObjectName("PanoramaWidget")
                layout.addWidget(self.sidebar_panorama)
                self.logger.info("✅ 使用重构后的CompletePanoramaWidget")
            except Exception as e:
                self.logger.warning(f"CompletePanoramaWidget创建失败: {e}")
                self.sidebar_panorama = self._create_fallback_panorama()
                layout.addWidget(self.sidebar_panorama)
        else:
            self.sidebar_panorama = self._create_fallback_panorama()
            layout.addWidget(self.sidebar_panorama)

        return group

    def _create_sector_stats_group(self, group_font):
        """创建选中扇形组"""
        group = QGroupBox("选中扇形")
        group.setFont(group_font)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(5, 5, 5, 5)

        # 扇形统计信息标签 (old版本样式)
        self.sector_stats_label = QLabel("扇形统计信息")
        self.sector_stats_label.setFont(QFont("Arial", 10))
        self.sector_stats_label.setWordWrap(True)
        self.sector_stats_label.setMinimumHeight(120)
        self.sector_stats_label.setAlignment(Qt.AlignTop)
        self.sector_stats_label.setObjectName("SectorStatsLabel")
        layout.addWidget(self.sector_stats_label)

        return group

    def _create_fallback_panorama(self):
        """创建备用全景图"""
        label = QLabel("全景图组件\n加载中...")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("border: 1px solid gray; background-color: #f0f0f0;")
        label.setFixedSize(360, 420)  # 保持old版本尺寸
        return label

    def initialize_data(self):
        """初始化数据"""
        self.update_progress_display()
        self.logger.info("✅ 左侧信息面板初始化完成")

    def update_progress_display(self, data=None):
        """更新进度显示 - 使用重构后的数据源"""
        # 默认数据
        if data is None:
            data = {
                "total": 0, "qualified": 0, "unqualified": 0, 
                "not_detected": 0, "blind": 0, "tie_rod": 0,
                "progress": 0.0, "completion_rate": 0.0, "qualification_rate": 0.0,
                "completed": 0, "pending": 0
            }

        # 更新进度组
        progress = data.get('progress', 0)
        self.progress_bar.setValue(int(progress))
        
        # 更新已完成和待完成数量
        completed = data.get('completed', data.get('qualified', 0) + data.get('unqualified', 0))
        pending = data.get('pending', data.get('not_detected', 0))
        self.completed_count_label.setText(f"已完成: {completed}")
        self.pending_count_label.setText(f"待完成: {pending}")
        
        # 更新完成率和合格率
        completion_rate = data.get('completion_rate', 0)
        qualification_rate = data.get('qualification_rate', 0)
        self.completion_rate_label.setText(f"完成率: {completion_rate:.1f}%")
        self.qualification_rate_label.setText(f"合格率: {qualification_rate:.1f}%")

        # 更新统计面板
        self.total_label.setText(f"总数: {data.get('total', 0)}")
        self.qualified_label.setText(f"合格: {data.get('qualified', 0)}")
        self.unqualified_label.setText(f"异常: {data.get('unqualified', 0)}")
        self.not_detected_label.setText(f"待检: {data.get('not_detected', 0)}")
        self.blind_label.setText(f"盲孔: {data.get('blind', 0)}")
        self.tie_rod_label.setText(f"拉杆: {data.get('tie_rod', 0)}")

    def update_hole_info(self, hole_data):
        """更新孔位信息"""
        if hole_data:
            self.selected_hole_id_label.setText(hole_data.get('id', '--'))
            self.selected_hole_pos_label.setText(hole_data.get('position', '--'))
            self.selected_hole_status_label.setText(hole_data.get('status', '--'))
            self.selected_hole_desc_label.setText(hole_data.get('description', '--'))
        else:
            self.selected_hole_id_label.setText("--")
            self.selected_hole_pos_label.setText("--")
            self.selected_hole_status_label.setText("--")
            self.selected_hole_desc_label.setText("--")

    def update_file_info(self, dxf_path=None, product_name=None):
        """更新文件信息"""
        if dxf_path:
            file_name = Path(dxf_path).name
            self.dxf_file_label.setText(file_name)
        else:
            self.dxf_file_label.setText("未加载")
            
        if product_name:
            self.product_label.setText(product_name)
        else:
            self.product_label.setText("--")


class NativeCenterVisualizationPanel(QWidget):
    """中间可视化面板 - 完全还原old版本 (高内聚组件)"""
    
    # 信号定义
    hole_selected = Signal(str)
    view_mode_changed = Signal(str)
    sector_navigation_requested = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 组件状态
        self.current_view_mode = "macro"
        self.current_sector = None
        
        # 初始化UI
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """设置UI布局 - 严格按照old版本结构"""
        # 主组框 (old版本样式)
        panel = QGroupBox("管孔检测视图")
        
        # 设置组标题字体
        center_panel_font = QFont()
        center_panel_font.setPointSize(12)
        center_panel_font.setBold(True)
        panel.setFont(center_panel_font)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)

        # 1. 状态图例已移除 (按用户要求删除)

        # 2. 视图控制 (old版本的层级化显示控制)
        view_controls_frame = self._create_view_controls()
        layout.addWidget(view_controls_frame)

        # 3. 主显示区域 (old版本: DynamicSectorDisplayWidget, 800×700px)
        main_display_widget = self._create_main_display_area()
        layout.addWidget(main_display_widget)

        # 设置主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(panel)


    def _create_view_controls(self):
        """创建视图控制 - old版本的层级化显示控制"""
        control_frame = QFrame()
        control_frame.setFrameStyle(QFrame.StyledPanel)
        control_frame.setMaximumHeight(60)
        
        layout = QHBoxLayout(control_frame)
        layout.setContentsMargins(12, 8, 12, 8)
        
        # 视图模式标签
        view_label = QLabel("视图模式:")
        view_label.setFont(QFont("Arial", 11, QFont.Bold))
        layout.addWidget(view_label)
        
        # 宏观区域视图按钮 (old版本样式)
        self.macro_view_btn = QPushButton("📊 宏观区域视图")
        self.macro_view_btn.setCheckable(True)
        self.macro_view_btn.setChecked(True)
        self.macro_view_btn.setMinimumHeight(35)
        self.macro_view_btn.setMinimumWidth(140)
        self.macro_view_btn.setToolTip("显示整个管板的全貌，适合快速浏览和状态概览")
        
        # 微观孔位视图按钮
        self.micro_view_btn = QPushButton("🔍 微观孔位视图")
        self.micro_view_btn.setCheckable(True)
        self.micro_view_btn.setMinimumHeight(35)
        self.micro_view_btn.setMinimumWidth(140)
        self.micro_view_btn.setToolTip("显示孔位的详细信息，适合精确检测和分析")
        
        # 全景总览视图按钮
        self.panorama_view_btn = QPushButton("🌍 全景总览视图")
        self.panorama_view_btn.setCheckable(True)
        self.panorama_view_btn.setMinimumHeight(35)
        self.panorama_view_btn.setMinimumWidth(140)
        self.panorama_view_btn.setToolTip("显示完整的管板全景图，适合整体分析")
        
        layout.addWidget(self.macro_view_btn)
        layout.addWidget(self.micro_view_btn)
        layout.addWidget(self.panorama_view_btn)
        
        layout.addSpacing(20)
        
        # 扇形导航控制 (old版本样式)
        nav_label = QLabel("扇形导航:")
        nav_label.setFont(QFont("Arial", 11, QFont.Bold))
        layout.addWidget(nav_label)
        
        self.prev_sector_btn = QPushButton("◀ 上一扇形")
        self.prev_sector_btn.setMinimumHeight(35)
        self.prev_sector_btn.setMinimumWidth(100)
        
        self.next_sector_btn = QPushButton("下一扇形 ▶")
        self.next_sector_btn.setMinimumHeight(35)
        self.next_sector_btn.setMinimumWidth(100)
        
        layout.addWidget(self.prev_sector_btn)
        layout.addWidget(self.next_sector_btn)
        
        layout.addStretch()
        return control_frame

    def _create_main_display_area(self):
        """创建主显示区域 - 初始为空白，等待加载CAP1000 DXF"""
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(2, 2, 2, 2)
        
        # 创建空白的图形视图，准备加载CAP1000数据
        if HAS_REFACTORED_MODULES:
            try:
                self.graphics_view = OptimizedGraphicsView()
                self.graphics_view.setMinimumSize(800, 700)
                main_layout.addWidget(self.graphics_view)
                
                # 获取或创建scene
                scene = None
                if hasattr(self.graphics_view, 'scene'):
                    scene = self.graphics_view.scene
                    if scene is None:
                        # 如果scene属性存在但为None，创建新的
                        from PySide6.QtWidgets import QGraphicsScene
                        scene = QGraphicsScene()
                        self.graphics_view.setScene(scene)
                else:
                    # scene是方法
                    try:
                        scene = self.graphics_view.scene()
                    except:
                        from PySide6.QtWidgets import QGraphicsScene
                        scene = QGraphicsScene()
                        self.graphics_view.setScene(scene)
                    
                from PySide6.QtWidgets import QGraphicsTextItem
                from PySide6.QtGui import QFont
                
                info_text = QGraphicsTextItem("请选择产品型号 (CAP1000) 或加载DXF文件")
                font = QFont()
                font.setPointSize(14)
                info_text.setFont(font)
                info_text.setPos(250, 350)
                scene.addItem(info_text)
                
                self.logger.info("✅ 创建空白视图，等待CAP1000数据")
            except Exception as e:
                self.logger.warning(f"OptimizedGraphicsView创建失败: {e}")
                self.graphics_view = self._create_fallback_graphics_view()
                main_layout.addWidget(self.graphics_view)
        else:
            self.graphics_view = self._create_fallback_graphics_view()
            main_layout.addWidget(self.graphics_view)
        
        # 保留workpiece_diagram引用以兼容
        self.workpiece_diagram = None
        
        return main_widget
    
    def _on_hole_clicked(self, hole_id, status):
        """处理孔位点击事件"""
        self.logger.info(f"孔位点击: {hole_id}, 状态: {status}")
        # 发射信号给上层
        self.hole_selected.emit(hole_id)

    def _create_fallback_graphics_view(self):
        """创建备用图形视图"""
        # 最终备用方案
        from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsTextItem
        from PySide6.QtGui import QFont
        
        view = QGraphicsView()
        scene = QGraphicsScene()
        view.setScene(scene)
        view.setMinimumSize(800, 700)
        
        # 显示初始提示信息
        text_item = QGraphicsTextItem("请选择产品型号 (CAP1000) 或加载DXF文件")
        font = QFont()
        font.setPointSize(14)
        text_item.setFont(font)
        text_item.setPos(250, 350)
        scene.addItem(text_item)
        
        return view

    def setup_connections(self):
        """设置信号连接"""
        # 视图模式按钮连接
        self.macro_view_btn.clicked.connect(lambda: self._on_view_mode_changed("macro"))
        self.micro_view_btn.clicked.connect(lambda: self._on_view_mode_changed("micro"))
        self.panorama_view_btn.clicked.connect(lambda: self._on_view_mode_changed("panorama"))
        
        # 扇形导航按钮连接
        self.prev_sector_btn.clicked.connect(lambda: self.sector_navigation_requested.emit("previous"))
        self.next_sector_btn.clicked.connect(lambda: self.sector_navigation_requested.emit("next"))

    def _on_view_mode_changed(self, mode):
        """处理视图模式变化"""
        # 更新按钮状态
        self.macro_view_btn.setChecked(mode == "macro")
        self.micro_view_btn.setChecked(mode == "micro")
        self.panorama_view_btn.setChecked(mode == "panorama")
        
        self.current_view_mode = mode
        self.view_mode_changed.emit(mode)
        self.logger.info(f"🔄 视图模式切换到: {mode}")


class NativeRightOperationsPanel(QScrollArea):
    """右侧操作面板 - 完全还原old版本 (高内聚组件)"""
    
    # 信号定义
    start_detection = Signal()
    pause_detection = Signal()
    stop_detection = Signal()
    reset_detection = Signal()
    start_simulation = Signal()  # 模拟检测信号
    pause_simulation = Signal()
    stop_simulation = Signal()
    file_operation_requested = Signal(str, dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 组件状态
        self.detection_running = False
        
        # 设置滚动区域属性 (old版本样式)
        self.setWidgetResizable(True)
        self.setMaximumWidth(350)  # old版本精确宽度
        
        # 初始化UI
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """设置UI布局 - 严格按照old版本结构"""
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # 设置字体
        panel_font = QFont()
        panel_font.setPointSize(11)
        
        group_title_font = QFont()
        group_title_font.setPointSize(12)
        group_title_font.setBold(True)
        
        button_font = QFont()
        button_font.setPointSize(11)

        # 1. 检测控制组 (old版本第一组)
        detection_group = self._create_detection_control_group(group_title_font, button_font)
        layout.addWidget(detection_group)

        # 2. 模拟检测组 (恢复模拟检测功能)
        simulation_group = self._create_simulation_group(group_title_font, button_font)
        layout.addWidget(simulation_group)

        # 3. 文件操作组 (old版本第三组)
        file_group = self._create_file_operations_group(group_title_font, button_font)
        layout.addWidget(file_group)

        # 4. 视图控制组 (old版本第四组)
        view_group = self._create_view_control_group(group_title_font, button_font)
        layout.addWidget(view_group)

        # 5. 孔位操作组已删除 (按用户要求)

        # 6. 其他操作组
        other_group = self._create_other_operations_group(group_title_font, button_font)
        layout.addWidget(other_group)

        layout.addStretch()
        self.setWidget(content_widget)

    def _create_detection_control_group(self, group_font, button_font):
        """创建检测控制组 - old版本样式"""
        group = QGroupBox("检测控制")
        group.setFont(group_font)
        layout = QVBoxLayout(group)

        # 检测按钮 (old版本样式和尺寸)
        self.start_detection_btn = QPushButton("开始检测")
        self.start_detection_btn.setMinimumHeight(45)
        self.start_detection_btn.setFont(button_font)
        self.start_detection_btn.setEnabled(False)  # old版本初始状态
        self.start_detection_btn.setStyleSheet("background-color: green; color: white;")

        self.pause_detection_btn = QPushButton("暂停检测")
        self.pause_detection_btn.setMinimumHeight(45)
        self.pause_detection_btn.setFont(button_font)
        self.pause_detection_btn.setEnabled(False)
        self.pause_detection_btn.setStyleSheet("background-color: orange; color: white;")

        self.stop_detection_btn = QPushButton("停止检测")
        self.stop_detection_btn.setMinimumHeight(45)
        self.stop_detection_btn.setFont(button_font)
        self.stop_detection_btn.setEnabled(False)
        self.stop_detection_btn.setStyleSheet("background-color: red; color: white;")

        layout.addWidget(self.start_detection_btn)
        layout.addWidget(self.pause_detection_btn)
        layout.addWidget(self.stop_detection_btn)

        return group

    def _create_simulation_group(self, group_font, button_font):
        """创建模拟检测组"""
        group = QGroupBox("模拟检测")
        group.setFont(group_font)
        layout = QVBoxLayout(group)

        # 模拟检测按钮
        self.start_simulation_btn = QPushButton("开始模拟")
        self.start_simulation_btn.setMinimumHeight(40)
        self.start_simulation_btn.setFont(button_font)
        self.start_simulation_btn.setToolTip("启动模拟检测，按蛇形路径顺序渲染")

        self.pause_simulation_btn = QPushButton("暂停模拟")
        self.pause_simulation_btn.setMinimumHeight(40)
        self.pause_simulation_btn.setFont(button_font)
        self.pause_simulation_btn.setEnabled(False)

        self.stop_simulation_btn = QPushButton("停止模拟")
        self.stop_simulation_btn.setMinimumHeight(40)
        self.stop_simulation_btn.setFont(button_font)
        self.stop_simulation_btn.setEnabled(False)

        layout.addWidget(self.start_simulation_btn)
        layout.addWidget(self.pause_simulation_btn)
        layout.addWidget(self.stop_simulation_btn)

        return group

    def _create_file_operations_group(self, group_font, button_font):
        """创建文件操作组"""
        group = QGroupBox("文件操作")
        group.setFont(group_font)
        layout = QVBoxLayout(group)

        # 文件操作按钮
        self.load_dxf_btn = QPushButton("加载DXF文件")
        self.load_dxf_btn.setMinimumHeight(40)
        self.load_dxf_btn.setFont(button_font)

        self.load_product_btn = QPushButton("选择产品型号")
        self.load_product_btn.setMinimumHeight(40)
        self.load_product_btn.setFont(button_font)

        self.export_data_btn = QPushButton("导出数据")
        self.export_data_btn.setMinimumHeight(40)
        self.export_data_btn.setFont(button_font)

        layout.addWidget(self.load_dxf_btn)
        layout.addWidget(self.load_product_btn)
        layout.addWidget(self.export_data_btn)

        return group

    def _create_view_control_group(self, group_font, button_font):
        """创建视图控制组"""
        group = QGroupBox("视图控制")
        group.setFont(group_font)
        layout = QHBoxLayout(group)

        self.zoom_in_button = QPushButton("放大")
        self.zoom_out_button = QPushButton("缩小")  
        self.reset_zoom_button = QPushButton("重置")

        for btn in [self.zoom_in_button, self.zoom_out_button, self.reset_zoom_button]:
            btn.setMinimumHeight(35)
            btn.setFont(button_font)

        layout.addWidget(self.zoom_in_button)
        layout.addWidget(self.zoom_out_button)
        layout.addWidget(self.reset_zoom_button)

        return group


    def _create_other_operations_group(self, group_font, button_font):
        """创建其他操作组"""
        group = QGroupBox("其他操作")
        group.setFont(group_font)
        layout = QVBoxLayout(group)

        # 报告相关按钮
        self.generate_report_btn = QPushButton("生成报告")
        self.generate_report_btn.setMinimumHeight(40)
        self.generate_report_btn.setFont(button_font)

        self.export_report_btn = QPushButton("导出报告")
        self.export_report_btn.setMinimumHeight(40)
        self.export_report_btn.setFont(button_font)

        layout.addWidget(self.generate_report_btn)
        layout.addWidget(self.export_report_btn)

        return group

    def setup_connections(self):
        """设置信号连接"""
        # 检测控制信号
        self.start_detection_btn.clicked.connect(self.start_detection.emit)
        self.pause_detection_btn.clicked.connect(self.pause_detection.emit)
        self.stop_detection_btn.clicked.connect(self.stop_detection.emit)

        # 模拟控制信号
        self.start_simulation_btn.clicked.connect(self.start_simulation.emit)
        self.pause_simulation_btn.clicked.connect(self.pause_simulation.emit)
        self.stop_simulation_btn.clicked.connect(self.stop_simulation.emit)

        # 文件操作信号
        self.load_dxf_btn.clicked.connect(lambda: self.file_operation_requested.emit("load_dxf", {}))
        self.load_product_btn.clicked.connect(lambda: self.file_operation_requested.emit("load_product", {}))
        self.export_data_btn.clicked.connect(lambda: self.file_operation_requested.emit("export_data", {}))

        # 其他操作信号
        self.generate_report_btn.clicked.connect(lambda: self.file_operation_requested.emit("generate_report", {}))
        self.export_report_btn.clicked.connect(lambda: self.file_operation_requested.emit("export_report", {}))


    def update_detection_state(self, running=False):
        """更新检测状态"""
        self.detection_running = running
        
        # 更新按钮状态 (old版本逻辑)
        self.start_detection_btn.setEnabled(not running)
        self.pause_detection_btn.setEnabled(running)
        self.stop_detection_btn.setEnabled(running)


class NativeMainDetectionView(QWidget):
    """
    原生主检测视图 - 完全还原old版本三栏式布局
    使用现有重构后的文件和功能模块
    采用高内聚、低耦合的设计原则
    """
    
    # 页面导航信号 (old版本信号)
    navigate_to_realtime = Signal(str)
    navigate_to_history = Signal(str)
    navigate_to_report = Signal()
    
    # 状态更新信号
    status_updated = Signal(str, str)
    file_loaded = Signal(str)
    detection_progress = Signal(int)
    error_occurred = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 集成重构后的控制器和服务 (低耦合)
        self.controller = None
        self.search_service = None
        self.status_service = None
        self.file_service = None
        
        if HAS_REFACTORED_MODULES:
            try:
                self.controller = MainWindowController()
                self.search_service = SearchService()
                self.status_service = StatusService()
                self.file_service = FileService()
                self.logger.info("✅ 重构后的服务模块集成成功")
            except Exception as e:
                self.logger.warning(f"服务模块集成失败: {e}")
        
        # UI组件引用 (高内聚组件)
        self.left_panel = None
        self.center_panel = None
        self.right_panel = None
        self.toolbar = None
        
        # 数据状态
        self.current_hole_collection = None
        self.selected_hole = None
        self.detection_running = False
        
        # 设置UI
        self.setup_ui()
        self.setup_connections()
        self.initialize_components()
        
    def setup_ui(self):
        """设置UI布局 - 完全还原old版本三栏式布局"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 1. 工具栏 (old版本顶部工具栏)
        self.toolbar = self._create_native_toolbar()
        main_layout.addWidget(self.toolbar)
        
        # 2. 主内容区域 - 三栏分割器布局 (old版本核心结构)
        content_splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：信息面板 (380px固定宽度)
        self.left_panel = NativeLeftInfoPanel()
        content_splitter.addWidget(self.left_panel)
        
        # 中间：可视化面板 (主要伸缩区域)
        self.center_panel = NativeCenterVisualizationPanel()
        content_splitter.addWidget(self.center_panel)
        
        # 右侧：操作面板 (350px最大宽度)
        self.right_panel = NativeRightOperationsPanel()
        content_splitter.addWidget(self.right_panel)
        
        # 设置分割器比例 (old版本精确比例: 380, 700, 280)
        content_splitter.setSizes([380, 700, 280])
        
        # 设置拖动策略 (old版本设置)
        content_splitter.setChildrenCollapsible(False)
        content_splitter.setStretchFactor(0, 0)  # 左侧固定
        content_splitter.setStretchFactor(1, 1)  # 中间主要伸缩
        content_splitter.setStretchFactor(2, 0)  # 右侧固定
        
        # 禁用左侧分割线拖动 (old版本设置)
        content_splitter.handle(1).setEnabled(False)
        
        main_layout.addWidget(content_splitter)

    def _create_native_toolbar(self):
        """创建原生工具栏 - old版本样式"""
        if HAS_REFACTORED_MODULES:
            try:
                # 使用重构后的ToolbarComponent (低耦合集成)
                toolbar = ToolbarComponent()
                self.logger.info("✅ 使用重构后的ToolbarComponent")
                return toolbar
            except Exception as e:
                self.logger.warning(f"ToolbarComponent创建失败: {e}")
        
        # 备用工具栏实现
        toolbar = QFrame()
        toolbar.setFrameStyle(QFrame.StyledPanel)
        toolbar.setMaximumHeight(70)
        
        layout = QHBoxLayout(toolbar)
        
        # 产品选择按钮
        product_btn = QPushButton("产品型号选择")
        product_btn.setMinimumSize(140, 45)
        layout.addWidget(product_btn)
        
        layout.addSpacing(20)
        
        # 搜索区域
        layout.addWidget(QLabel("搜索:"))
        search_input = QLineEdit()
        search_input.setPlaceholderText("输入孔位ID...")
        search_input.setMinimumSize(220, 35)
        layout.addWidget(search_input)
        
        search_btn = QPushButton("搜索")
        search_btn.setMinimumSize(70, 35)
        layout.addWidget(search_btn)
        
        layout.addSpacing(20)
        
        # 视图控制
        layout.addWidget(QLabel("视图:"))
        view_combo = QComboBox()
        view_combo.addItems(["全部孔位", "待检孔位", "合格孔位", "异常孔位"])
        view_combo.setMinimumHeight(35)
        layout.addWidget(view_combo)
        
        layout.addStretch()
        return toolbar

    def setup_connections(self):
        """设置信号连接 - 高内聚组件间通信"""
        # 左侧面板信号连接
        if self.left_panel:
            self.left_panel.hole_info_updated.connect(self._on_hole_info_updated)
            # 连接全景图扇形点击信号
            if hasattr(self.left_panel, 'sidebar_panorama') and self.left_panel.sidebar_panorama:
                self.left_panel.sidebar_panorama.sector_clicked.connect(self._on_panorama_sector_clicked)
        
        # 中间面板信号连接
        if self.center_panel:
            self.center_panel.hole_selected.connect(self._on_hole_selected)
            self.center_panel.view_mode_changed.connect(self._on_view_mode_changed)
            self.center_panel.sector_navigation_requested.connect(self._on_sector_navigation)
        
        # 右侧面板信号连接
        if self.right_panel:
            self.right_panel.start_detection.connect(self._on_start_detection)
            self.right_panel.pause_detection.connect(self._on_pause_detection)
            self.right_panel.stop_detection.connect(self._on_stop_detection)
            # right_panel.simulation_start信号连接已删除 (按用户要求)
            self.right_panel.file_operation_requested.connect(self._on_file_operation)
        
        # 重构后服务信号连接 (低耦合集成)
        if self.search_service:
            self.search_service.search_completed.connect(self._on_search_completed)
        
        if self.status_service:
            self.status_service.status_updated.connect(self._on_status_updated)

    def initialize_components(self):
        """初始化组件状态"""
        self.logger.info("🚀 原生主检测视图初始化完成")
        
        # 初始化左侧面板数据
        if self.left_panel:
            self.left_panel.update_progress_display()
        
        # 初始化控制器
        if self.controller:
            try:
                self.controller.initialize()
            except Exception as e:
                self.logger.warning(f"控制器初始化失败: {e}")

    # === 事件处理方法 (高内聚逻辑) ===
    
    def _on_hole_selected(self, hole_id):
        """处理孔位选择事件"""
        self.logger.info(f"🎯 选中孔位: {hole_id}")
        
        # 更新左侧面板孔位信息
        hole_data = {
            'id': hole_id,
            'position': f"({100}, {200})",  # 示例坐标
            'status': '待检',
            'description': '正常孔位'
        }
        
        if self.left_panel:
            self.left_panel.update_hole_info(hole_data)

    def _on_view_mode_changed(self, mode):
        """处理视图模式变化"""
        self.logger.info(f"🔄 视图模式变化: {mode}")
        
        # 这里可以集成重构后的视图切换逻辑
        if self.controller and hasattr(self.controller, 'switch_view_mode'):
            try:
                self.controller.switch_view_mode(mode)
            except Exception as e:
                self.logger.warning(f"视图模式切换失败: {e}")

    def _on_sector_navigation(self, direction):
        """处理扇形导航"""
        self.logger.info(f"🧭 扇形导航: {direction}")
    
    def _on_panorama_sector_clicked(self, sector):
        """处理全景图扇形点击"""
        from src.core_business.graphics.sector_types import SectorQuadrant
        
        self.logger.info(f"🎯 全景图扇形点击: {sector.value if hasattr(sector, 'value') else sector}")
        
        # 更新选中扇形信息
        if self.left_panel:
            self.left_panel.update_selected_sector(sector)
        
        # 在中间视图显示对应扇形的孔位
        if self.current_hole_collection and self.center_panel and hasattr(self.center_panel, 'graphics_view'):
            # 过滤该扇形的孔位
            filtered_holes = self._filter_holes_by_sector(self.current_hole_collection, sector)
            
            if filtered_holes:
                # 创建新的HoleCollection只包含该扇形的孔位
                from src.core_business.models.hole_data import HoleCollection
                filtered_dict = {hole.hole_id: hole for hole in filtered_holes}
                filtered_collection = HoleCollection(filtered_dict)
                
                # 加载到中间视图
                if hasattr(self.center_panel.graphics_view, 'load_holes'):
                    self.center_panel.graphics_view.load_holes(filtered_collection)
                    self.logger.info(f"✅ 中间视图已加载扇形 {sector.value} 的 {len(filtered_holes)} 个孔位")
                    
                    # 适应视图到内容
                    scene = self._get_center_scene()
                    if scene and hasattr(self.center_panel.graphics_view, 'fitInView'):
                        self.center_panel.graphics_view.fitInView(scene.itemsBoundingRect(), Qt.KeepAspectRatio)
    
    def _filter_holes_by_sector(self, hole_collection, sector):
        """根据扇形过滤孔位"""
        try:
            from src.core_business.graphics.sector_types import SectorQuadrant
            
            if not hole_collection:
                return []
            
            # 获取孔位列表
            holes_list = []
            if hasattr(hole_collection, 'holes'):
                if hasattr(hole_collection.holes, 'values'):
                    holes_list = list(hole_collection.holes.values())
                else:
                    holes_list = list(hole_collection.holes)
            
            if not holes_list:
                return []
            
            # 计算数据中心点
            min_x = min(hole.center_x for hole in holes_list)
            max_x = max(hole.center_x for hole in holes_list)
            min_y = min(hole.center_y for hole in holes_list)
            max_y = max(hole.center_y for hole in holes_list)
            
            center_x = (min_x + max_x) / 2
            center_y = (min_y + max_y) / 2
            
            # 根据扇形过滤孔位
            filtered = []
            for hole in holes_list:
                # 使用SectorQuadrant的from_position方法判断孔位所属扇形
                hole_sector = SectorQuadrant.from_position(
                    hole.center_x, hole.center_y, center_x, center_y
                )
                if hole_sector == sector:
                    filtered.append(hole)
            
            return filtered
            
        except Exception as e:
            self.logger.error(f"过滤扇形孔位失败: {e}")
            return []
    
    def _get_center_scene(self):
        """安全获取中间视图的scene"""
        if hasattr(self.center_panel, 'graphics_view') and self.center_panel.graphics_view:
            if hasattr(self.center_panel.graphics_view, 'scene'):
                return self.center_panel.graphics_view.scene
            else:
                try:
                    return self.center_panel.graphics_view.scene()
                except:
                    return None
        return None

    def _on_start_detection(self):
        """处理开始检测"""
        self.logger.info("🚀 开始检测")
        self.detection_running = True
        
        # 更新右侧面板状态
        if self.right_panel:
            self.right_panel.update_detection_state(running=True)
        
        # 集成重构后的检测服务
        if self.controller and hasattr(self.controller, 'start_detection'):
            try:
                self.controller.start_detection()
            except Exception as e:
                self.logger.error(f"检测启动失败: {e}")

    def _on_pause_detection(self):
        """处理暂停检测"""
        self.logger.info("⏸️ 暂停检测")

    def _on_stop_detection(self):
        """处理停止检测"""
        self.logger.info("⏹️ 停止检测")
        self.detection_running = False
        
        # 更新右侧面板状态
        if self.right_panel:
            self.right_panel.update_detection_state(running=False)

    
    def load_hole_collection(self, hole_collection):
        """加载孔位数据到视图 - 支持CAP1000和其他DXF"""
        # 清空初始提示文本
        if hasattr(self.center_panel, 'graphics_view') and self.center_panel.graphics_view:
            try:
                # 获取scene - 注意scene是属性不是方法
                if hasattr(self.center_panel.graphics_view, 'scene'):
                    scene = self.center_panel.graphics_view.scene
                else:
                    scene = self.center_panel.graphics_view.scene()
                    
                if scene:
                    scene.clear()
                
                # 使用OptimizedGraphicsView的load_holes方法
                if hasattr(self.center_panel.graphics_view, 'load_holes'):
                    self.center_panel.graphics_view.load_holes(hole_collection)
                    self.logger.info(f"✅ 成功加载 {len(hole_collection.holes) if hasattr(hole_collection, 'holes') else 0} 个孔位数据")
                else:
                    # 手动绘制孔位
                    self._draw_holes_to_scene(scene, hole_collection)
                    
            except Exception as e:
                self.logger.error(f"加载孔位数据失败: {e}")
                
        # 更新左侧面板全景预览
        if self.left_panel and hasattr(self.left_panel, 'sidebar_panorama'):
            try:
                if hasattr(self.left_panel.sidebar_panorama, 'load_hole_collection'):
                    self.left_panel.sidebar_panorama.load_hole_collection(hole_collection)
                    self.logger.info("✅ 全景预览数据已更新")
                elif hasattr(self.left_panel.sidebar_panorama, 'update_hole_data'):
                    self.left_panel.sidebar_panorama.update_hole_data(hole_collection)
                    self.logger.info("✅ 全景预览数据已更新(兼容方法)")
            except Exception as e:
                self.logger.warning(f"全景预览更新失败: {e}")
        
        # 更新状态统计
        if self.left_panel:
            hole_count = len(hole_collection.holes) if hasattr(hole_collection, 'holes') else 0
            self.left_panel.update_progress_display({
                'total': hole_count,
                'qualified': 0,
                'unqualified': 0,
                'not_detected': hole_count,
                'completed': 0,
                'pending': hole_count,
                'progress': 0.0,
                'completion_rate': 0.0,
                'qualification_rate': 0.0
            })
    
    def _draw_holes_to_scene(self, scene, hole_collection):
        """手动绘制孔位到场景"""
        from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsTextItem
        from PySide6.QtCore import QRectF
        from PySide6.QtGui import QPen, QBrush, QColor
        
        try:
            # 获取孔位列表
            holes_list = []
            if hasattr(hole_collection, 'holes'):
                if hasattr(hole_collection.holes, 'values'):
                    holes_list = list(hole_collection.holes.values())
                else:
                    holes_list = list(hole_collection.holes)
                    
            # 设置画笔和画刷
            pen = QPen(QColor(0, 100, 200), 2)
            brush = QBrush(QColor(200, 220, 255, 100))
            
            # 绘制每个孔位
            for hole in holes_list:
                x = hole.center_x
                y = hole.center_y
                radius = getattr(hole, 'radius', 5.0)
                
                # 创建圆形
                circle = QGraphicsEllipseItem(QRectF(x-radius, y-radius, 2*radius, 2*radius))
                circle.setPen(pen)
                circle.setBrush(brush)
                scene.addItem(circle)
                
                # 添加孔位编号
                if hasattr(hole, 'hole_id'):
                    text = QGraphicsTextItem(str(hole.hole_id))
                    text.setPos(x - 10, y - 10)
                    scene.addItem(text)
                    
            # 调整视图
            scene.setSceneRect(scene.itemsBoundingRect())
            if hasattr(self.center_panel.graphics_view, 'fitInView'):
                self.center_panel.graphics_view.fitInView(scene.sceneRect(), Qt.KeepAspectRatio)
                
            self.logger.info(f"✅ 手动绘制了 {len(holes_list)} 个孔位")
            
        except Exception as e:
            self.logger.error(f"手动绘制孔位失败: {e}")

    def _on_file_operation(self, operation, params):
        """处理文件操作"""
        self.logger.info(f"📁 文件操作: {operation}")
        
        if operation == "load_product":
            self._show_product_selection()
        elif operation == "load_dxf":
            self._load_dxf_file()

    def _on_hole_info_updated(self, info):
        """处理孔位信息更新"""
        pass

    def _on_search_completed(self, query, results):
        """处理搜索完成"""
        pass

    def _on_status_updated(self, hole_id, status):
        """处理状态更新"""
        pass

    # === 业务逻辑方法 (集成重构后功能) ===
    
    def _show_product_selection(self):
        """显示产品选择对话框"""
        if HAS_REFACTORED_MODULES:
            try:
                dialog = ProductSelectionDialog(self)
                if dialog.exec():
                    product = dialog.selected_product
                    if product:
                        self.logger.info(f"✅ 选择产品: {product}")
                        if self.left_panel:
                            self.left_panel.update_file_info(product_name=str(product))
            except Exception as e:
                self.logger.error(f"产品选择失败: {e}")

    def _load_dxf_file(self):
        """加载DXF文件"""
        from PySide6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择DXF文件", "", "DXF Files (*.dxf)"
        )
        
        if file_path:
            self.logger.info(f"📁 加载DXF文件: {file_path}")
            if self.left_panel:
                self.left_panel.update_file_info(dxf_path=file_path)
            self.file_loaded.emit(file_path)

    # === 公共接口方法 ===
    
    def get_current_state(self):
        """获取当前状态"""
        return {
            'detection_running': self.detection_running,
            'selected_hole': self.selected_hole,
            'has_data': self.current_hole_collection is not None
        }

    def update_hole_collection(self, hole_collection):
        """更新孔位集合"""
        self.current_hole_collection = hole_collection
        self.logger.info("📊 孔位集合已更新")

    def cleanup(self):
        """清理资源"""
        if self.controller:
            try:
                self.controller.cleanup()
            except:
                pass
        
        self.logger.info("🧹 原生主检测视图资源已清理")