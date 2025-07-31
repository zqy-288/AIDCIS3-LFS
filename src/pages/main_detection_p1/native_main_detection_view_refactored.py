"""
原生主检测视图 - 重构版本
作为薄编排层，组合高内聚的独立组件
完全还原old版本UI布局，采用高内聚、低耦合的设计原则
"""

import sys
import logging
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QPushButton, QLineEdit, QComboBox, QCompleter
)
from PySide6.QtCore import Qt, Signal, QStringListModel
from PySide6.QtGui import QFont, QAction

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入独立组件
from .components import (
    LeftInfoPanel,
    CenterVisualizationPanel,
    RightOperationsPanel,
    PanoramaSectorCoordinator,
    SimulationController
)

# 导入现有的重构后功能模块
try:
    from .controllers.main_window_controller import MainWindowController
    from .controllers.services.search_service import SearchService
    from .controllers.services.status_service import StatusService
    from .controllers.services.file_service import FileService
    from src.core_business.graphics.graphics_view import OptimizedGraphicsView
    from src.core_business.graphics.complete_panorama_widget import CompletePanoramaWidget
    from src.core.shared_data_manager import SharedDataManager
    shared_data_manager = SharedDataManager()
    from .modules.product_selection import ProductSelectionDialog
    HAS_REFACTORED_MODULES = True
except ImportError as e:
    logging.warning(f"部分重构模块导入失败: {e}")
    HAS_REFACTORED_MODULES = False


class NativeMainDetectionView(QWidget):
    """
    原生主检测视图 - 重构版本
    作为薄编排层，负责组件间的协调和通信
    """
    
    # 页面导航信号
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
        
        # 初始化服务和控制器
        self._initialize_services()
        
        # 初始化组件
        self._initialize_components()
        
        # 设置UI
        self.setup_ui()
        
        # 连接信号
        self._connect_signals()
        
        # 初始化数据
        self._initialize_data()
        
    def _initialize_services(self):
        """初始化服务和控制器"""
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
                self.logger.info("✅ 服务模块初始化成功")
            except Exception as e:
                self.logger.warning(f"服务模块初始化失败: {e}")
                
    def _initialize_components(self):
        """初始化独立组件"""
        # UI组件
        self.left_panel = LeftInfoPanel()
        self.center_panel = CenterVisualizationPanel()
        self.right_panel = RightOperationsPanel()
        
        # 协调器和控制器
        self.panorama_coordinator = PanoramaSectorCoordinator()
        self.simulation_controller = SimulationController()
        
        # 工具栏组件
        self.toolbar = None
        
        self.logger.info("✅ 组件初始化成功")
        
    def setup_ui(self):
        """设置UI布局 - 完全还原old版本三栏式布局"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 1. 工具栏
        self.toolbar = self._create_native_toolbar()
        main_layout.addWidget(self.toolbar)
        
        # 2. 主内容区域 - 三栏分割器布局
        content_splitter = QSplitter(Qt.Horizontal)
        
        # 添加三个面板
        content_splitter.addWidget(self.left_panel)
        content_splitter.addWidget(self.center_panel)
        content_splitter.addWidget(self.right_panel)
        
        # 设置分割器比例
        content_splitter.setStretchFactor(0, 0)  # 左侧固定
        content_splitter.setStretchFactor(1, 1)  # 中间伸缩
        content_splitter.setStretchFactor(2, 0)  # 右侧固定
        
        # 设置初始大小
        content_splitter.setSizes([380, 800, 350])
        
        main_layout.addWidget(content_splitter)
        
        self.logger.info("✅ UI布局设置完成")
        
    def _create_native_toolbar(self):
        """创建原生工具栏"""
        toolbar_widget = QWidget()
        toolbar_widget.setMaximumHeight(45)
        
        layout = QHBoxLayout(toolbar_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 设置字体
        toolbar_font = QFont()
        toolbar_font.setPointSize(11)
        
        # 导航按钮组
        nav_widget = QWidget()
        nav_layout = QHBoxLayout(nav_widget)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        
        # 导航按钮
        self.realtime_btn = QPushButton("实时检测")
        self.history_btn = QPushButton("历史记录")
        self.report_btn = QPushButton("报告管理")
        
        for btn in [self.realtime_btn, self.history_btn, self.report_btn]:
            btn.setMinimumHeight(35)
            btn.setFont(toolbar_font)
            nav_layout.addWidget(btn)
            
        layout.addWidget(nav_widget)
        
        # 搜索组件
        search_widget = self._create_search_widget(toolbar_font)
        layout.addWidget(search_widget)
        
        layout.addStretch()
        
        # 状态和用户信息
        status_widget = self._create_status_widget(toolbar_font)
        layout.addWidget(status_widget)
        
        return toolbar_widget
        
    def _create_search_widget(self, font):
        """创建搜索组件"""
        search_widget = QWidget()
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        search_layout.addWidget(QLabel("搜索:"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入孔位ID或关键词...")
        self.search_input.setMinimumWidth(200)
        self.search_input.setFont(font)
        
        # 设置自动完成
        if self.search_service:
            completer = QCompleter()
            completer.setModel(QStringListModel())
            self.search_input.setCompleter(completer)
            
        search_layout.addWidget(self.search_input)
        
        self.search_btn = QPushButton("搜索")
        self.search_btn.setFont(font)
        search_layout.addWidget(self.search_btn)
        
        return search_widget
        
    def _create_status_widget(self, font):
        """创建状态组件"""
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        # 连接状态
        self.connection_status = QLabel("● 已连接")
        self.connection_status.setStyleSheet("color: green;")
        self.connection_status.setFont(font)
        status_layout.addWidget(self.connection_status)
        
        status_layout.addSpacing(20)
        
        # 用户信息
        self.user_label = QLabel("操作员: 管理员")
        self.user_label.setFont(font)
        status_layout.addWidget(self.user_label)
        
        return status_widget
        
    def _connect_signals(self):
        """连接信号 - 组件间的通信"""
        # 工具栏导航
        self.realtime_btn.clicked.connect(lambda: self.navigate_to_realtime.emit(""))
        self.history_btn.clicked.connect(lambda: self.navigate_to_history.emit(""))
        self.report_btn.clicked.connect(self.navigate_to_report.emit)
        
        # 搜索功能
        self.search_btn.clicked.connect(self._on_search)
        self.search_input.returnPressed.connect(self._on_search)
        
        # 右侧操作面板信号
        self.right_panel.start_detection.connect(self._on_start_detection)
        self.right_panel.pause_detection.connect(self._on_pause_detection)
        self.right_panel.stop_detection.connect(self._on_stop_detection)
        self.right_panel.start_simulation.connect(self._on_start_simulation)
        self.right_panel.pause_simulation.connect(self._on_pause_simulation)
        self.right_panel.stop_simulation.connect(self._on_stop_simulation)
        self.right_panel.file_operation_requested.connect(self._on_file_operation)
        self.right_panel.view_control_requested.connect(self._on_view_control)
        
        # 中间面板信号
        self.center_panel.hole_selected.connect(self._on_hole_selected)
        self.center_panel.view_mode_changed.connect(self._on_view_mode_changed)
        
        # 全景扇形协调器信号
        self.panorama_coordinator.sector_clicked.connect(self._on_sector_clicked)
        self.panorama_coordinator.sector_stats_updated.connect(self._on_sector_stats_updated)
        
        # 模拟控制器信号
        self.simulation_controller.simulation_progress.connect(self._on_simulation_progress)
        self.simulation_controller.hole_status_updated.connect(self._on_hole_status_updated)
        self.simulation_controller.simulation_completed.connect(self._on_simulation_completed)
        
        # SharedDataManager信号
        if shared_data_manager:
            shared_data_manager.data_changed.connect(self._on_shared_data_changed)
            
        self.logger.info("✅ 信号连接完成")
        
    def _initialize_data(self):
        """初始化数据和组件关联"""
        # 设置图形视图
        if HAS_REFACTORED_MODULES:
            try:
                graphics_view = OptimizedGraphicsView()
                self.center_panel.set_graphics_view(graphics_view)
                self.panorama_coordinator.set_graphics_view(graphics_view)
                self.simulation_controller.set_graphics_view(graphics_view)
            except Exception as e:
                self.logger.warning(f"图形视图设置失败: {e}")
                
        # 设置全景图组件
        if HAS_REFACTORED_MODULES:
            try:
                panorama_widget = CompletePanoramaWidget()
                panorama_widget.setFixedSize(360, 420)
                self.left_panel.set_panorama_widget(panorama_widget)
                self.panorama_coordinator.set_panorama_widget(panorama_widget)
                self.simulation_controller.set_panorama_widget(panorama_widget)
            except Exception as e:
                self.logger.warning(f"全景图组件设置失败: {e}")
                
        # 连接左侧面板的扇形点击信号
        self.left_panel.sector_clicked.connect(self.panorama_coordinator._on_panorama_sector_clicked)
        
        self.logger.info("✅ 数据初始化完成")
        
    # ========== 事件处理方法 ==========
    
    def _on_search(self):
        """处理搜索"""
        query = self.search_input.text()
        if query and self.search_service:
            results = self.search_service.search(query)
            self.logger.info(f"搜索 '{query}': {len(results)} 个结果")
            
    def _on_start_detection(self):
        """开始检测"""
        if self.controller:
            self.controller.start_detection()
            self.right_panel.update_detection_state(True)
            
    def _on_pause_detection(self):
        """暂停检测"""
        if self.controller:
            self.controller.pause_detection()
            
    def _on_stop_detection(self):
        """停止检测"""
        if self.controller:
            self.controller.stop_detection()
            self.right_panel.update_detection_state(False)
            
    def _on_start_simulation(self):
        """开始模拟"""
        self.simulation_controller.start_simulation()
        self.right_panel.update_simulation_state(True)
        
    def _on_pause_simulation(self):
        """暂停/恢复模拟"""
        if self.simulation_controller.is_paused:
            self.simulation_controller.resume_simulation()
        else:
            self.simulation_controller.pause_simulation()
            
    def _on_stop_simulation(self):
        """停止模拟"""
        self.simulation_controller.stop_simulation()
        self.right_panel.update_simulation_state(False)
        
    def _on_file_operation(self, operation, params):
        """处理文件操作"""
        if operation == "load_product":
            self._show_product_selection()
        elif operation == "load_dxf":
            if self.file_service:
                self.file_service.load_dxf_file()
                
    def _on_view_control(self, action):
        """处理视图控制"""
        graphics_view = self.center_panel.get_graphics_view()
        if graphics_view:
            if action == "zoom_in":
                graphics_view.scale(1.2, 1.2)
            elif action == "zoom_out":
                graphics_view.scale(0.8, 0.8)
            elif action == "reset_zoom":
                graphics_view.resetTransform()
                
    def _on_hole_selected(self, hole_id):
        """处理孔位选择"""
        self.logger.info(f"孔位选择: {hole_id}")
        # 更新左侧面板显示
        if self.controller and self.controller.current_hole_collection:
            hole = self.controller.current_hole_collection.holes.get(hole_id)
            if hole:
                hole_info = {
                    'id': hole.hole_id,
                    'position': f"({hole.center_x:.1f}, {hole.center_y:.1f})",
                    'status': hole.status.value if hole.status else '待检',
                    'description': f"半径: {hole.radius:.1f}mm"
                }
                self.left_panel.update_hole_info(hole_info)
                
    def _on_view_mode_changed(self, mode):
        """处理视图模式变化"""
        self.logger.info(f"视图模式: {mode}")
        
    def _on_sector_clicked(self, sector):
        """处理扇形点击"""
        self.logger.info(f"扇形点击: {sector.value}")
        
    def _on_sector_stats_updated(self, stats):
        """处理扇形统计更新"""
        # 更新左侧面板的扇形统计显示
        if self.panorama_coordinator.current_sector:
            stats_text = self.panorama_coordinator.get_sector_stats_text(
                self.panorama_coordinator.current_sector
            )
            self.left_panel.update_sector_stats(stats_text)
            
    def _on_simulation_progress(self, current, total):
        """处理模拟进度"""
        progress = int(current / total * 100) if total > 0 else 0
        self.detection_progress.emit(progress)
        
        # 更新左侧面板进度
        stats = {
            'progress': progress,
            'completed': current,
            'pending': total - current,
            'total': total,
            'completion_rate': progress,
            'qualification_rate': 99.5  # 模拟成功率
        }
        self.left_panel.update_progress_display(stats)
        
    def _on_hole_status_updated(self, hole_id, status):
        """处理孔位状态更新"""
        self.logger.debug(f"孔位状态更新: {hole_id} -> {status}")
        
    def _on_simulation_completed(self):
        """处理模拟完成"""
        self.logger.info("✅ 模拟检测完成")
        self.right_panel.update_simulation_state(False)
        
    def _on_shared_data_changed(self, key, value):
        """处理共享数据变化"""
        if key == "hole_collection" and value:
            # 加载孔位数据到各个组件
            self.panorama_coordinator.load_hole_collection(value)
            self.simulation_controller.load_hole_collection(value)
            
            # 更新文件信息
            if hasattr(value, 'dxf_path'):
                self.left_panel.update_file_info(
                    dxf_path=value.dxf_path,
                    product_name=getattr(value, 'product_name', None)
                )
                
            # 启用控制按钮
            self.right_panel.enable_detection_controls(True)
            self.right_panel.enable_simulation_controls(True)
            
            self.logger.info(f"✅ 加载孔位数据: {len(value.holes)} 个孔位")
            
    def _show_product_selection(self):
        """显示产品选择对话框"""
        if HAS_REFACTORED_MODULES:
            dialog = ProductSelectionDialog(self)
            if dialog.exec():
                selected_product = dialog.get_selected_product()
                if selected_product and self.controller:
                    self.controller.load_product(selected_product)