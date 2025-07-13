"""
重构后的主窗口模块
采用模块化设计，分离关注点
"""

import logging
import sys
import os
from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget,
    QMessageBox, QStatusBar, QSplitter
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QKeySequence, QShortcut

# 添加父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
sys.path.insert(0, src_dir)

# 导入UI组件
from .ui_components import (
    ToolbarWidget, InfoPanel, VisualizationPanel, 
    OperationsPanel, StatusBarWidget
)

# 导入管理器
from .managers import (
    DetectionManager, SimulationManager, ProductManager,
    HoleSearchManager
)

# 导入服务
from .services import StatusService, NavigationService

# 导入原有功能模块
from modules.realtime_chart import RealtimeChart
from modules.worker_thread import WorkerThread
from modules.history_viewer import HistoryViewer
from modules.defect_annotation_tool import DefectAnnotationTool

# 导入AIDCIS2核心组件
from aidcis2.models.hole_data import HoleData, HoleCollection
from aidcis2.models.status_manager import StatusManager
from aidcis2.dxf_parser import DXFParser
from aidcis2.data_adapter import DataAdapter
from aidcis2.graphics.graphics_view import OptimizedGraphicsView
from aidcis2.graphics.sector_manager_adapter import SectorManagerAdapter

# 导入产品管理
from models.product_model import get_product_manager

# 导入全景图同步集成
from panorama_sync_integration import integrate_panorama_sync


class MainWindow(QMainWindow):
    """
    重构后的主窗口类
    采用组件化设计，提高可维护性
    """
    
    # 导航信号
    navigate_to_realtime = Signal(str)
    navigate_to_history = Signal(str)
    status_updated = Signal(str, str)
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # 初始化核心组件
        self._init_core_components()
        
        # 初始化管理器
        self._init_managers()
        
        # 初始化服务
        self._init_services()
        
        # 设置UI
        self.setup_ui()
        
        # 连接信号
        self.setup_connections()
        
        # 初始化数据
        self._init_data()
        
        # 集成全景图数据库同步系统
        self._init_panorama_sync()
        
        # 设置调试快捷键
        self._setup_debug_shortcuts()
        
    def _init_core_components(self):
        """初始化核心组件"""
        # AIDCIS2核心组件
        self.dxf_parser = DXFParser()
        self.data_adapter = DataAdapter()
        self.status_manager = StatusManager()
        self.sector_manager = SectorManagerAdapter()
        
        # 产品管理
        self.product_model_manager = get_product_manager()
        
        # 数据
        self.hole_collection: Optional[HoleCollection] = None
        self.selected_hole: Optional[HoleData] = None
        
        # 原有功能组件
        self.worker_thread = None
        
    def _init_managers(self):
        """初始化管理器"""
        # 检测管理器
        self.detection_manager = DetectionManager(self)
        self.detection_manager.log_message.connect(self.log_message)
        self.detection_manager.status_message.connect(self.update_status_message)
        self.detection_manager.detection_step_completed.connect(self._on_detection_step_completed)
        
        # 模拟管理器
        self.simulation_manager = SimulationManager(self)
        self.simulation_manager.log_message.connect(self.log_message)
        self.simulation_manager.status_updated.connect(self.update_status_display)
        
        # 产品管理器
        self.product_manager = ProductManager(self)
        self.product_manager.set_components(self, self.product_model_manager, self.dxf_parser)
        self.product_manager.log_message.connect(self.log_message)
        self.product_manager.status_message.connect(self.update_status_message)
        self.product_manager.product_selected.connect(self._on_product_selected)
        self.product_manager.dxf_loaded.connect(self._on_dxf_loaded)
        
        # 搜索管理器
        self.search_manager = HoleSearchManager(self)
        self.search_manager.log_message.connect(self.log_message)
        self.search_manager.hole_selected.connect(self._on_hole_selected_from_search)
        
    def _init_services(self):
        """初始化服务"""
        # 状态服务
        self.status_service = StatusService(self)
        self.status_service.log_message.connect(self.log_message)
        self.status_service.status_updated.connect(self._on_status_updated)
        
        # 导航服务
        self.navigation_service = NavigationService(self)
        self.navigation_service.log_message.connect(self.log_message)
        
    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("AIDCIS3系统 - 模块化版本")
        self.setGeometry(100, 100, 1600, 900)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 工具栏
        self.toolbar = ToolbarWidget(self)
        self.toolbar.product_select_clicked.connect(self.product_manager.select_product)
        self.toolbar.search_requested.connect(self.search_manager.perform_search)
        self.toolbar.view_changed.connect(self._on_view_filter_changed)
        main_layout.addWidget(self.toolbar)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 添加主检测视图标签
        self.main_detection_view = self._create_main_detection_view()
        self.tab_widget.addTab(self.main_detection_view, "主检测视图")
        
        # 添加实时监控标签
        self.realtime_chart = RealtimeChart()
        self.tab_widget.addTab(self.realtime_chart, "实时监控")
        
        # 添加历史数据标签
        self.history_viewer = HistoryViewer()
        self.tab_widget.addTab(self.history_viewer, "历史数据")
        
        # 添加缺陷标注工具标签
        self.defect_annotation_tool = DefectAnnotationTool()
        self.tab_widget.addTab(self.defect_annotation_tool, "缺陷标注工具")
        
        # 设置菜单栏
        self.setup_menu()
        
        # 设置状态栏
        self.setup_status_bar()
        
        # 设置导航服务组件
        self.navigation_service.set_components(self.tab_widget, self)
        
    def _create_main_detection_view(self) -> QWidget:
        """创建主检测视图"""
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧信息面板
        self.info_panel = InfoPanel(self)
        splitter.addWidget(self.info_panel)
        
        # 中央可视化面板
        self.visualization_panel = VisualizationPanel(self)
        self.graphics_view = self.visualization_panel.graphics_view
        splitter.addWidget(self.visualization_panel)
        
        # 右侧操作面板
        self.operations_panel = OperationsPanel(self)
        splitter.addWidget(self.operations_panel)
        
        # 设置分割器比例
        splitter.setSizes([250, 800, 250])
        
        layout.addWidget(splitter)
        
        return container
        
    def setup_menu(self):
        """设置菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        # 产品管理
        product_action = QAction("产品管理", self)
        product_action.triggered.connect(self._open_product_management)
        file_menu.addAction(product_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图")
        
        # 缩放控制
        zoom_in_action = QAction("放大", self)
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("缩小", self)
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        fit_view_action = QAction("适应视图", self)
        fit_view_action.triggered.connect(self.fit_view)
        view_menu.addAction(fit_view_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def setup_status_bar(self):
        """设置状态栏"""
        self.status_bar = StatusBarWidget(self)
        self.setStatusBar(self.status_bar)
        
    def setup_connections(self):
        """设置信号连接"""
        # 搜索组件
        self.search_manager.set_components(
            self.toolbar.search_input,
            self.graphics_view
        )
        
        # 检测管理器
        self.detection_manager.set_ui_components(
            self.graphics_view,
            self.operations_panel.start_detection_btn,
            self.operations_panel.pause_detection_btn,
            self.operations_panel.stop_detection_btn
        )
        
        # 模拟管理器
        self.simulation_manager.set_components(
            self.hole_collection,
            self.graphics_view,
            self.operations_panel.simulate_btn,
            self.sector_manager
        )
        
        # 操作面板信号
        self.operations_panel.start_detection_clicked.connect(
            self.detection_manager.start_detection
        )
        self.operations_panel.pause_detection_clicked.connect(
            self.detection_manager.pause_detection
        )
        self.operations_panel.stop_detection_clicked.connect(
            self.detection_manager.stop_detection
        )
        self.operations_panel.simulate_clicked.connect(
            lambda: self.simulation_manager.start_simulation(version=2)
        )
        self.operations_panel.goto_realtime_clicked.connect(
            self._goto_realtime
        )
        self.operations_panel.goto_history_clicked.connect(
            self._goto_history
        )
        self.operations_panel.mark_defective_clicked.connect(
            self._mark_defective
        )
        
        # 图形视图信号
        if hasattr(self.graphics_view, 'hole_selected'):
            self.graphics_view.hole_selected.connect(self._on_hole_selected)
            
        # 导航信号
        self.navigate_to_realtime.connect(
            self.navigation_service.goto_realtime
        )
        self.navigate_to_history.connect(
            self.navigation_service.goto_history
        )
        
    def _init_data(self):
        """初始化数据"""
        # 设置默认状态
        self.update_status_message("就绪")
        
    def _init_panorama_sync(self):
        """初始化全景图数据库同步系统"""
        try:
            # 创建存根方法以避免错误
            if not hasattr(self, '_update_panorama_hole_status'):
                self._update_panorama_hole_status = lambda hole_id, color: None
            
            success = integrate_panorama_sync(self)
            if success:
                self.log_message("✅ 全景图数据库同步系统已集成")
            else:
                self.log_message("⚠️ 全景图数据库同步系统集成失败")
        except Exception as e:
            self.log_message(f"❌ 全景图同步初始化错误: {e}")
    
    def _setup_debug_shortcuts(self):
        """设置调试快捷键"""
        # Ctrl+D: 运行全景图调试
        debug_shortcut = QShortcut(QKeySequence(Qt.CTRL | Qt.Key_D), self)
        debug_shortcut.activated.connect(self._run_panorama_debug)
        
        # Ctrl+Shift+S: 强制同步所有孔位到全景图
        force_sync_shortcut = QShortcut(QKeySequence(Qt.CTRL | Qt.SHIFT | Qt.Key_S), self)
        force_sync_shortcut.activated.connect(self._force_sync_all_holes)
        
        self.log_message("🔧 调试快捷键已设置: Ctrl+D (调试), Ctrl+Shift+S (强制同步)")
    
    def _run_panorama_debug(self):
        """运行全景图调试 (Ctrl+D)"""
        self.log_message("🔍 运行全景图调试...")
        
        try:
            # 检查全景图组件
            if hasattr(self, 'panorama_widget') and self.panorama_widget:
                # 调用调试方法
                if hasattr(self.panorama_widget, 'debug_hole_items_format'):
                    self.panorama_widget.debug_hole_items_format()
                    self.log_message("✅ 全景图调试信息已输出到控制台")
                else:
                    self.log_message("⚠️ 全景图组件没有调试方法")
            else:
                self.log_message("❌ 未找到全景图组件")
                
            # 检查同步管理器状态
            if hasattr(self, 'panorama_sync_integration'):
                stats = self.panorama_sync_integration.get_sync_status()
                if stats:
                    self.log_message(f"📊 同步状态: 已同步 {stats.get('total_synced', 0)} 个更新")
                    
        except Exception as e:
            self.log_message(f"❌ 调试执行失败: {e}")
    
    def _force_sync_all_holes(self):
        """强制同步所有孔位到全景图 (Ctrl+Shift+S)"""
        self.log_message("⚡ 强制同步所有孔位...")
        
        try:
            if hasattr(self, 'panorama_sync_integration'):
                self.panorama_sync_integration.force_sync_all()
                self.log_message("✅ 强制同步完成")
            else:
                self.log_message("❌ 同步管理器未初始化")
        except Exception as e:
            self.log_message(f"❌ 强制同步失败: {e}")
        
    # 事件处理方法
    def _on_product_selected(self, product):
        """处理产品选择"""
        self.info_panel.update_product_info(product)
        
        # 配置扇形管理器
        if hasattr(product, 'sector_count') and product.sector_count:
            if product.sector_count != 4:
                self.sector_manager.set_dynamic_mode(True, product.sector_count)
            else:
                self.sector_manager.set_dynamic_mode(False, 4)
                
    def _on_dxf_loaded(self, file_path):
        """处理DXF加载"""
        # 获取孔位集合
        self.hole_collection = self.product_manager.get_hole_collection()
        
        # 更新各组件
        self.detection_manager.set_hole_collection(self.hole_collection)
        self.simulation_manager.set_components(
            self.hole_collection,
            self.graphics_view,
            self.operations_panel.simulate_btn,
            self.sector_manager
        )
        self.search_manager.set_hole_collection(self.hole_collection)
        self.status_service.set_hole_collection(self.hole_collection)
        
        # 更新UI
        self.info_panel.update_file_info(file_path)
        self.visualization_panel.set_hole_collection(self.hole_collection)
        self.operations_panel.enable_detection_controls(True)
        
        # 更新状态
        self.update_status_display()
        
    def _on_hole_selected(self, hole: HoleData):
        """处理孔位选择"""
        self.selected_hole = hole
        self.info_panel.update_hole_info(hole)
        self.operations_panel.update_for_selected_hole(hole)
        
    def _on_hole_selected_from_search(self, hole: HoleData):
        """处理搜索选择的孔位"""
        self._on_hole_selected(hole)
        # 在图形视图中高亮
        if self.graphics_view:
            self.graphics_view.highlight_holes([hole])
            
    def _on_detection_step_completed(self, hole_id: str, status: str):
        """处理检测步骤完成"""
        self.update_status_display()
        self.log_message(f"检测完成: {hole_id} - {status}")
        
    def _on_status_updated(self, stats: dict):
        """处理状态更新"""
        # 更新信息面板的统计显示
        self.info_panel.update_statistics(stats)
        
    def _on_view_filter_changed(self, filter_text: str):
        """处理视图过滤变化"""
        if self.graphics_view:
            self.graphics_view.filter_holes(filter_text)
            
    # 功能方法
    def log_message(self, message: str):
        """记录日志消息"""
        self.logger.info(message)
        if hasattr(self, 'operations_panel'):
            self.operations_panel.add_log_message(message)
            
    def update_status_message(self, message: str):
        """更新状态栏消息"""
        if hasattr(self, 'status_bar'):
            self.status_bar.set_status_message(message)
            
    def update_status_display(self):
        """更新状态显示"""
        self.status_service.update_status_display()
        
    def zoom_in(self):
        """放大视图"""
        if self.graphics_view:
            self.graphics_view.zoom_in()
            
    def zoom_out(self):
        """缩小视图"""
        if self.graphics_view:
            self.graphics_view.zoom_out()
            
    def fit_view(self):
        """适应视图"""
        if self.graphics_view:
            self.graphics_view.fit_view()
            
    def _goto_realtime(self):
        """跳转到实时监控"""
        if self.selected_hole:
            self.navigate_to_realtime.emit(self.selected_hole.hole_id)
            
    def _goto_history(self):
        """跳转到历史数据"""
        if self.selected_hole:
            self.navigate_to_history.emit(self.selected_hole.hole_id)
            
    def _mark_defective(self):
        """标记为异常"""
        if self.selected_hole:
            from aidcis2.models.hole_data import HoleStatus
            self.selected_hole.status = HoleStatus.DEFECTIVE
            if self.graphics_view:
                self.graphics_view.update_hole_status(
                    self.selected_hole.hole_id, 
                    HoleStatus.DEFECTIVE
                )
            self.update_status_display()
            self.log_message(f"已标记 {self.selected_hole.hole_id} 为异常")
            
    def _open_product_management(self):
        """打开产品管理界面"""
        # TODO: 实现产品管理界面
        QMessageBox.information(self, "提示", "产品管理功能开发中...")
        
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于 AIDCIS3",
            "AIDCIS3 内孔检测系统\n\n"
            "模块化架构版本\n"
            "版本: 3.0.0"
        )