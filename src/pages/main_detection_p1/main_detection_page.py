"""
主检测视图页面 - P1级别
还原重构前的AIDCIS2检测界面布局
"""

import sys
import logging
from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QProgressBar, QGroupBox, QGraphicsView, QFrame, QLabel
)
from PySide6.QtCore import Signal

# 添加模块路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入原有的控制器和服务
try:
    # 使用 P1 本地版本的控制器
    from .controllers.main_window_controller import MainWindowController
    from src.shared.components.factories import get_ui_factory
    from src.shared.services import get_graphics_service
    from src.pages.main_detection_p1.components.simulation_controller import SimulationController
except ImportError as e:
    logging.warning(f"无法导入控制器/服务: {e}, 使用模拟实现")
    MainWindowController = None
    get_ui_factory = None
    get_graphics_service = None
    SimulationController = None


class MainDetectionPage(QWidget):
    """主检测视图页面 - P1级别 (还原重构前UI)"""
    
    # 信号
    navigate_to_realtime = Signal(str)
    navigate_to_history = Signal(str)
    file_loaded = Signal(str)
    status_updated = Signal(str)
    detection_progress = Signal(int)
    error_occurred = Signal(str)
    
    def __init__(self, shared_components=None, view_model=None, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        # 设置日志级别减少重复信息
        logging.getLogger('SnakePathRenderer').setLevel(logging.WARNING)
        logging.getLogger('ViewTransformController').setLevel(logging.WARNING)
        logging.getLogger('CompletePanorama').setLevel(logging.WARNING)
        logging.getLogger('src.pages.main_detection_p1.components.panorama_sector_coordinator').setLevel(logging.WARNING)
        logging.getLogger('src.pages.main_detection_p1.native_main_detection_view_p1').setLevel(logging.WARNING)
        logging.getLogger('src.pages.main_detection_p1.components.graphics.graphics_view').setLevel(logging.WARNING)
        logging.getLogger('src.pages.main_detection_p1.graphics.core.graphics_view').setLevel(logging.WARNING)
        
        # 控制器和服务将从native_view获取，避免重复创建
        self.controller = None  # 将在setup_ui后从native_view获取
        self.simulation_controller = None  # 将从native_view获取
        
        # UI工厂需要初始化以支持对话框创建
        try:
            from src.shared.components.factories.ui_component_factory import get_ui_factory
            self.ui_factory = get_ui_factory()
            print("✅ [MainPage] UI工厂初始化成功")
        except Exception as e:
            print(f"❌ [MainPage] UI工厂初始化失败: {e}")
            self.ui_factory = None
        
        self.graphics_service = None
        
        # UI组件 - 通过原生视图访问
        self.graphics_view = None
        self.panorama_widget = None
        
        # 视图联动相关
        self.current_hole_data = []
        self.current_selected_region = None
        self.panorama_regions = []  # 全景图区域划分
        
        self.setup_ui()
        
        # 先初始化控制器，确保信号存在
        if self.controller:
            self.controller.initialize()
        
        # 然后设置连接
        self.setup_connections()
        self._setup_simulation_controller()
        
        # 最后检查已有数据
        if self.controller:
            # 检查是否已有孔位数据 (处理自动加载的CAP1000情况)
            self._check_and_load_existing_data()
        
    def setup_ui(self):
        """设置UI布局 - 使用原生三栏式布局还原old版本"""
        # 导入并使用P1页面的原生主检测视图
        from .native_main_detection_view_p1 import NativeMainDetectionView
        
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 创建原生主检测视图
        self.native_view = NativeMainDetectionView()
        layout.addWidget(self.native_view)
        
        # 获取native_view的控制器和服务，避免重复创建
        self.controller = self.native_view.controller
        self.simulation_controller = getattr(self.native_view, 'simulation_controller', None)
        
        # 设置引用以便于访问
        self.graphics_view = getattr(self.native_view.center_panel, 'graphics_view', None)
        self.panorama_widget = getattr(self.native_view.left_panel, 'sidebar_panorama', None)
        
        self.logger.info("✅ 使用原生三栏式布局")
    
        
    def setup_connections(self):
        """设置信号连接 - 只使用原生视图，无回退机制"""
        # 连接原生视图的主要信号到P1页面的信号
        self.native_view.navigate_to_realtime.connect(self.navigate_to_realtime)
        self.native_view.navigate_to_history.connect(self.navigate_to_history)
        self.native_view.file_loaded.connect(self.file_loaded)
        self.native_view.status_updated.connect(self.status_updated)
        # 注释掉，避免重复连接detection_progress信号，使用控制器的信号
        # self.native_view.detection_progress.connect(self.detection_progress)
        self.native_view.error_occurred.connect(self.error_occurred)
        
        # 连接工具栏信号到具体功能 - 检查toolbar类型
        toolbar = self.native_view.toolbar
        if toolbar and hasattr(toolbar, 'product_selection_requested'):
            toolbar.product_selection_requested.connect(self._on_select_product)
        if toolbar and hasattr(toolbar, 'search_requested'):
            toolbar.search_requested.connect(self._on_search_hole)
            self.logger.info("✅ 搜索信号已连接到页面处理方法")
        else:
            self.logger.warning("⚠️ 工具栏不支持搜索功能或工具栏未创建")
        
        # 连接右侧面板的文件操作信号
        right_panel = self.native_view.right_panel
        right_panel.file_operation_requested.connect(self._on_file_operation)
        right_panel.start_detection.connect(self._on_start_detection)
        right_panel.pause_detection.connect(self._on_pause_detection)
        right_panel.stop_detection.connect(self._on_stop_detection)
        
        # 不再需要断开信号，因为我们会在 _on_start_simulation 中处理批次创建
        # native_view 的信号仍然连接，但我们会覆盖处理逻辑
        
        # 只连接开始模拟的信号（用于批次创建）
        # 暂停和停止让 native_view 处理，避免冲突
        right_panel.start_simulation.connect(self._on_start_simulation)
        
        # 连接中间面板的视图控制信号
        center_panel = self.native_view.center_panel
        center_panel.hole_selected.connect(self._on_hole_selected)
        center_panel.view_mode_changed.connect(self._on_view_mode_changed)
        
        # 控制器信号连接
        if self.controller:
            self.controller.file_loaded.connect(self._on_file_loaded)
            # 控制器的status_updated信号有2个参数(hole_id, status)，需要适配
            self.controller.status_updated.connect(self._on_status_updated_from_controller)
            # 控制器的detection_progress信号有2个参数(current, total)
            self.controller.detection_progress.connect(self._on_detection_progress_from_controller)
            self.controller.error_occurred.connect(self._on_error_from_controller)
            # 连接批次创建信号
            if hasattr(self.controller, 'batch_created'):
                self.controller.batch_created.connect(self._on_batch_created)
                self.logger.debug("✅ [MainPage] 批次创建信号已连接")
            else:
                self.logger.debug("❌ [MainPage] 控制器没有 batch_created 信号")
        
        self.logger.info("✅ 原生视图信号连接成功")
        
    def _on_load_dxf(self):
        """加载DXF文件"""
        if self.controller:
            self.controller.load_dxf_file()
            # 确保数据传递到图形视图
            self._update_graphics_view()
        else:
            self.logger.debug("加载DXF - 控制器未初始化")
            
    def _add_test_graphics(self):
        """添加测试图形确保显示正常"""
        try:
            if hasattr(self.graphics_view, 'scene'):
                try:
                    scene = self.graphics_view.scene()
                except TypeError:
                    scene = self.graphics_view.scene
                    
                if scene:
                    from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsTextItem
                    from PySide6.QtCore import QRectF
                    from PySide6.QtGui import QPen, QBrush, QColor
                    
                    # 添加测试圆形
                    test_circle = QGraphicsEllipseItem(QRectF(0, 0, 100, 100))
                    test_circle.setPen(QPen(QColor(255, 0, 0), 3))
                    test_circle.setBrush(QBrush(QColor(255, 0, 0, 100)))
                    scene.addItem(test_circle)
                    
                    # 添加测试文本
                    test_text = QGraphicsTextItem("测试显示")
                    test_text.setPos(50, 120)
                    scene.addItem(test_text)
                    
                    # 确保视图可见
                    scene.setSceneRect(0, 0, 200, 200)
                    self.graphics_view.fitInView(scene.sceneRect())
                    
                    self.logger.info("测试图形已添加")
                    
        except Exception as e:
            self.logger.error(f"添加测试图形失败: {e}")
            
    def _on_select_product(self):
        """选择产品"""
        print("🔧 [MainPage] _on_select_product 被调用")
        print(f"🔧 [MainPage] 控制器状态: {self.controller}")
        print(f"🔧 [MainPage] UI工厂状态: {self.ui_factory}")
        
        if self.controller:
            print("🔧 [MainPage] 控制器存在，继续执行...")
            # 显示产品选择对话框
            if self.ui_factory:
                print("🔧 [MainPage] UI工厂存在，尝试创建对话框...")
                try:
                    print("🔧 [MainPage] 正在创建产品选择对话框...")
                    dialog = self.ui_factory.create_product_selection_dialog(self)
                    print(f"🔧 [MainPage] 对话框创建结果: {dialog}")
                    if dialog and dialog.exec():
                        selected_product = dialog.selected_product
                        print(f"🔧 [MainPage] 用户选择的产品: {selected_product}")
                        # 确保传递的是产品名称字符串，而不是ProductModel对象
                        if hasattr(selected_product, 'model_name'):
                            product_name = selected_product.model_name
                        else:
                            product_name = str(selected_product)
                        print(f"🔧 [MainPage] 将选择产品: {product_name}")
                        self.controller.select_product(product_name)
                    else:
                        print("🔧 [MainPage] 用户取消了产品选择或对话框为空")
                except Exception as e:
                    print(f"❌ [MainPage] 产品选择失败: {e}")
                    import traceback
                    traceback.print_exc()
                    self.logger.error(f"产品选择失败: {e}")
                    # 备用方案：直接创建产品选择对话框
                    self._show_fallback_product_selection()
            else:
                print("🔧 [MainPage] UI工厂不存在，使用备用方案")
                # 备用方案：直接创建产品选择对话框
                self._show_fallback_product_selection()
        else:
            print("❌ [MainPage] 控制器不存在")
            
    def _show_fallback_product_selection(self):
        """备用产品选择方案"""
        try:
            print("🔧 [MainPage] 使用备用产品选择方案")
            from src.pages.main_detection_p1.modules.product_selection import ProductSelectionDialog
            dialog = ProductSelectionDialog(self)
            if dialog.exec():
                selected_product = dialog.selected_product
                if hasattr(selected_product, 'model_name'):
                    product_name = selected_product.model_name
                else:
                    product_name = str(selected_product)
                print(f"✅ [MainPage] 备用方案选择产品: {product_name}")
                self.controller.select_product(product_name)
            else:
                print("🔧 [MainPage] 备用方案：用户取消了产品选择")
        except Exception as e:
            print(f"❌ [MainPage] 备用产品选择也失败: {e}")
            # 最后的备用方案
            from PySide6.QtWidgets import QInputDialog
            product_name, ok = QInputDialog.getText(self, "选择产品", "请输入产品名称:")
            if ok and product_name:
                self.controller.select_product(product_name)
            
    def _on_start_detection(self):
        """开始检测"""
        if self.controller:
            self.controller.start_detection()
        else:
            self.logger.debug("开始检测 - 控制器未初始化")
            
    def _on_pause_detection(self):
        """暂停检测"""
        if self.controller:
            self.controller.pause_detection()
        else:
            self.logger.debug("暂停检测 - 控制器未初始化")
            
    def _on_stop_detection(self):
        """停止检测"""
        if self.controller:
            self.controller.stop_detection()
        else:
            self.logger.debug("停止检测 - 控制器未初始化")
            
    def _on_detection_progress(self, progress):
        """更新检测进度"""
        # 通过原生视图更新进度显示
        if hasattr(self.native_view, 'update_detection_progress'):
            self.native_view.update_detection_progress(progress)
            
    def _on_file_loaded(self, file_path):
        """文件加载完成处理"""
        self.logger.info(f"DXF文件加载完成: {file_path}")
        # 转发信号
        self.file_loaded.emit(file_path)
        # 更新图形视图
        self._update_graphics_view()
            
    def _update_graphics_view(self):
        """更新图形视图显示DXF数据"""
        try:
            self.logger.info(f"🚀 [DEBUG] _update_graphics_view被调用")
            self.logger.info(f"🚀 [DEBUG] controller: {self.controller is not None}")
            if self.controller:
                self.logger.info(f"🚀 [DEBUG] controller.hole_collection存在: {hasattr(self.controller, 'hole_collection')}")
                if hasattr(self.controller, 'hole_collection'):
                    self.logger.info(f"🚀 [DEBUG] hole_collection不为空: {self.controller.hole_collection is not None}")
            
            # 尝试从多个源获取孔位数据
            hole_data = None
            
            # 1. 首先尝试从控制器获取
            if self.controller and hasattr(self.controller, 'hole_collection') and self.controller.hole_collection:
                hole_data = self.controller.hole_collection
                self.logger.info("🚀 [DEBUG] 从控制器获取到孔位数据")
            # 2. 尝试从业务服务获取
            elif self.controller and hasattr(self.controller, 'business_service'):
                business_service = self.controller.business_service
                if business_service and hasattr(business_service, 'get_hole_collection'):
                    hole_data = business_service.get_hole_collection()
                    if hole_data:
                        self.logger.info("🚀 [DEBUG] 从业务服务获取到孔位数据")
            
            if not hole_data:
                self.logger.warning("⚠️ 从所有源都无法获取孔位数据")
                return
            self.current_hole_data = hole_data
            
            # 获取孔位数量信息
            if hasattr(hole_data, 'holes'):
                hole_count = len(hole_data.holes) if hasattr(hole_data.holes, '__len__') else '未知'
            else:
                hole_count = '未知'
            
            self.logger.info(f"📊 开始显示 {hole_count} 个孔位")
            
            # 使用native_view的load_hole_collection方法
            if hasattr(self, 'native_view') and hasattr(self.native_view, 'load_hole_collection'):
                self.native_view.load_hole_collection(hole_data)
                self.logger.info("✅ 已通过native_view加载孔位数据")
            else:
                self.logger.warning("⚠️ native_view不支持load_hole_collection方法")
                    
            self.logger.info("✅ 图形视图更新完成")
                
        except Exception as e:
            self.logger.error(f"❌ 更新图形视图失败: {e}")
    
    def _check_and_load_existing_data(self):
        """检查并加载已存在的孔位数据 (处理自动加载情况)"""
        try:
            # 添加短暂延迟，等待控制器完全初始化（减少延迟提升响应速度）
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, self._load_existing_data_delayed)
        except Exception as e:
            self.logger.error(f"检查已存在数据失败: {e}")
    
    def _load_existing_data_delayed(self):
        """延迟加载已存在的数据"""
        try:
            if self.controller and hasattr(self.controller, 'hole_collection') and self.controller.hole_collection:
                self.logger.info("🔍 发现已存在的孔位数据，开始加载...")
                self._update_graphics_view()
            else:
                self.logger.info("📝 当前无孔位数据，等待用户加载DXF文件")
        except Exception as e:
            self.logger.error(f"延迟加载数据失败: {e}")
            
    def _on_panorama_region_selected(self, region_index, region_info):
        """处理全景图区域选择"""
        try:
            self.current_selected_region = region_index
            region_name = region_info["name"]
            
            self.logger.info(f"选择全景图区域: {region_name} (索引: {region_index})")
            
            # 根据区域过滤孔位数据
            if self.current_hole_data:
                filtered_holes = self._filter_holes_by_region(self.current_hole_data, region_index)
                
                # 更新左侧主视图显示选中区域的放大图
                self._display_region_detail(filtered_holes, region_name)
                
        except Exception as e:
            self.logger.error(f"处理全景图区域选择失败: {e}")
            
            
    def _filter_holes_by_region(self, hole_data, region_index):
        """根据区域索引过滤孔位数据"""
        if not hole_data:
            return []
            
        # 处理不同类型的hole_data
        if hasattr(hole_data, 'holes'):
            holes_list = hole_data.holes if hasattr(hole_data.holes, '__iter__') else list(hole_data.holes.values())
        elif hasattr(hole_data, '__iter__'):
            holes_list = list(hole_data)
        else:
            return []
            
        if not holes_list:
            return []
            
        # 计算数据边界
        min_x = min(hole.center_x for hole in holes_list)
        max_x = max(hole.center_x for hole in holes_list)
        min_y = min(hole.center_y for hole in holes_list)
        max_y = max(hole.center_y for hole in holes_list)
        
        mid_x = (min_x + max_x) / 2
        mid_y = (min_y + max_y) / 2
        
        # 根据区域索引过滤
        filtered = []
        for hole in holes_list:
            if region_index == 0:  # 左上
                if hole.center_x <= mid_x and hole.center_y >= mid_y:
                    filtered.append(hole)
            elif region_index == 1:  # 右上
                if hole.center_x >= mid_x and hole.center_y >= mid_y:
                    filtered.append(hole)
            elif region_index == 2:  # 左下
                if hole.center_x <= mid_x and hole.center_y <= mid_y:
                    filtered.append(hole)
            elif region_index == 3:  # 右下
                if hole.center_x >= mid_x and hole.center_y <= mid_y:
                    filtered.append(hole)
                    
        return filtered
        
    def _display_region_detail(self, hole_data, region_name):
        """在左侧主视图显示区域详细视图"""
        try:
            if hasattr(self.graphics_view, 'scene'):
                try:
                    scene = self.graphics_view.scene()
                except TypeError:
                    scene = self.graphics_view.scene
                if scene:
                    scene.clear()
                    
                    # 添加区域标题
                    from PySide6.QtWidgets import QGraphicsTextItem
                    from PySide6.QtGui import QFont
                    
                    title_item = QGraphicsTextItem(f"区域详细视图: {region_name}")
                    title_font = QFont()
                    title_font.setPointSize(14)
                    title_font.setBold(True)
                    title_item.setFont(title_font)
                    title_item.setPos(10, 10)
                    scene.addItem(title_item)
                    
                    # 绘制该区域的孔位（放大显示）
                    if hole_data:
                        self._draw_holes_to_scene(scene, hole_data, scale_factor=2.0)
                        
                        # 更新状态信息
                        status_text = f"显示区域: {region_name}, 孔位数量: {len(hole_data)}"
                        self.logger.info(status_text)
                        
        except Exception as e:
            self.logger.error(f"显示区域详细视图失败: {e}")
            
    def _draw_holes_to_scene(self, scene, hole_data, scale_factor=1.0):
        """手动绘制孔位到场景"""
        from PySide6.QtWidgets import QGraphicsEllipseItem
        from PySide6.QtCore import QRectF
        from PySide6.QtGui import QPen, QBrush, QColor
        
        try:
            pen = QPen(QColor(0, 100, 200))
            brush = QBrush(QColor(200, 220, 255, 100))
            
            # 处理不同类型的hole_data
            if hasattr(hole_data, 'holes'):
                holes_dict = hole_data.holes
                if hasattr(holes_dict, 'values'):
                    holes_list = list(holes_dict.values())
                elif hasattr(holes_dict, '__iter__'):
                    holes_list = list(holes_dict)
                else:
                    return
            elif hasattr(hole_data, '__iter__'):
                holes_list = list(hole_data)
            else:
                return
                
            if not holes_list:
                return
                
            # 限制显示数量提高性能
            display_count = min(len(holes_list), int(100 / scale_factor))
            
            items_added = 0
            for hole in holes_list[:display_count]:
                try:
                    x, y = hole.center_x * scale_factor, hole.center_y * scale_factor
                    radius = getattr(hole, 'radius', 5.0) * scale_factor
                    
                    # 创建圆形项
                    circle = QGraphicsEllipseItem(QRectF(x-radius, y-radius, 2*radius, 2*radius))
                    circle.setPen(pen)
                    circle.setBrush(brush)
                    scene.addItem(circle)
                    items_added += 1
                        
                except Exception:
                    continue
                    
            # 调整视图以适应内容
            bounding_rect = scene.itemsBoundingRect()
            if not bounding_rect.isEmpty():
                scene.setSceneRect(bounding_rect)
                self.graphics_view.fitInView(bounding_rect)
                
            self.logger.info(f"🎨 已绘制 {items_added} 个孔位")
            
        except Exception as e:
            self.logger.error(f"❌ 绘制失败: {e}")
            
    def _filter_holes_by_sector(self, hole_data, sector):
        """根据扇形过滤孔位数据"""
        try:
            from src.pages.main_detection_p1.graphics.core.sector_types import SectorQuadrant
            
            if not hole_data:
                return []
                
            # 处理不同类型的hole_data
            if hasattr(hole_data, 'holes'):
                holes_dict = hole_data.holes
                if hasattr(holes_dict, 'values'):
                    holes_list = list(holes_dict.values())
                elif hasattr(holes_dict, '__iter__'):
                    holes_list = list(holes_dict)
                else:
                    return []
            elif hasattr(hole_data, '__iter__'):
                holes_list = list(hole_data)
            else:
                return []
                
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
            
    def _display_sector_detail(self, hole_data, sector):
        """在左侧主视图显示扇形详细视图"""
        try:
            if self.graphics_view and hasattr(self.graphics_view, 'load_holes'):
                # 将列表转换为HoleCollection
                from src.shared.models.hole_data import HoleCollection
                
                if isinstance(hole_data, list):
                    # 创建字典，使用hole_id作为键
                    holes_dict = {hole.hole_id: hole for hole in hole_data}
                    hole_collection = HoleCollection(holes_dict)
                elif isinstance(hole_data, HoleCollection):
                    hole_collection = hole_data
                else:
                    # 尝试转换其他类型
                    holes_dict = {}
                    for hole in hole_data:
                        if hasattr(hole, 'hole_id'):
                            holes_dict[hole.hole_id] = hole
                    hole_collection = HoleCollection(holes_dict)
                
                # 使用OptimizedGraphicsView加载过滤后的孔位
                self.graphics_view.load_holes(hole_collection)
                self.logger.info(f"主视图已加载扇形 {sector.value} 的 {len(hole_collection)} 个孔位")
            else:
                # 备用方案
                self._display_region_detail(hole_data, f"扇形 {sector.value}")
                
        except Exception as e:
            self.logger.error(f"显示扇形详细视图失败: {e}")
            
    def _update_all_sector_views(self, hole_data):
        """初始化时更新所有扇形视图"""
        try:
            from src.pages.main_detection_p1.graphics.core.sector_types import SectorQuadrant
            
            self.logger.info("开始更新所有扇形视图...")
            
            # 更新每个扇形
            for sector in [SectorQuadrant.SECTOR_1, SectorQuadrant.SECTOR_2, 
                          SectorQuadrant.SECTOR_3, SectorQuadrant.SECTOR_4]:
                # 过滤该扇形的数据
                sector_holes = self._filter_holes_by_sector(hole_data, sector)
                # 更新对应的视图
                self._update_sector_views(sector, sector_holes)
                
        except Exception as e:
            self.logger.error(f"更新所有扇形视图失败: {e}")
    
    def _update_sector_views(self, sector, hole_data):
        """更新扇形视图显示"""
        try:
            # 获取对应的扇形视图组件
            sector_map = {
                "SECTOR_1": "sector_1",
                "SECTOR_2": "sector_2", 
                "SECTOR_3": "sector_3",
                "SECTOR_4": "sector_4"
            }
            
            sector_key = sector_map.get(sector.value)
            if sector_key and sector_key in self.sector_views:
                sector_view = self.sector_views[sector_key]
                
                # 如果是OptimizedGraphicsView，使用load_holes加载数据
                if hasattr(sector_view, 'load_holes'):
                    sector_view.load_holes(hole_data)
                    self.logger.info(f"扇形视图 {sector.value} 已更新，显示 {len(hole_data) if hole_data else 0} 个孔位")
                elif hasattr(sector_view, 'scene'):
                    # 备用方案：手动绘制
                    try:
                        scene = sector_view.scene()
                    except TypeError:
                        scene = sector_view.scene
                    if scene:
                        scene.clear()
                        self._draw_holes_to_scene(scene, hole_data, scale_factor=0.5)  # 缩小比例以适应小视图
                    
        except Exception as e:
            self.logger.error(f"更新扇形视图失败: {e}")
            
    def load_dxf(self):
        """加载DXF文件 - 外部调用接口"""
        self._on_load_dxf()
    
    # === 新增的原生视图事件处理方法 ===
    
    def _on_search_hole(self, query):
        """处理搜索孔位"""
        try:
            self.logger.info(f"🔍 页面接收到搜索请求: {query}")
            
            # 检查是否需要更新搜索数据
            if self.controller and hasattr(self.controller, 'business_coordinator'):
                coordinator = self.controller.business_coordinator
                if coordinator and hasattr(coordinator, 'update_search_data'):
                    coordinator.update_search_data()
                    self.logger.info("🔄 已更新搜索数据")
            
            # 使用控制器的搜索功能
            if self.controller and hasattr(self.controller, 'search_hole'):
                results = self.controller.search_hole(query)
                self.logger.info(f"✅ 页面搜索完成: {len(results)} 个结果")
                
                # 如果找到结果，自动切换到第一个匹配孔位所在的扇形
                if results and hasattr(self.native_view, 'switch_to_hole_sector'):
                    first_hole_id = results[0]
                    self.native_view.switch_to_hole_sector(first_hole_id)
                elif len(results) == 0:
                    self.logger.warning(f"⚠️ 没有找到匹配 '{query}' 的孔位")
                    
            else:
                self.logger.warning("⚠️ 控制器搜索功能不可用")
                
        except Exception as e:
            self.logger.error(f"❌ 搜索孔位失败: {e}")
            self.error_occurred.emit(f"搜索失败: {e}")
    
    def _on_file_operation(self, operation, params=None):
        """处理文件操作"""
        try:
            self.logger.info(f"📁 文件操作: {operation}")
            
            if operation == "load_dxf":
                self._on_load_dxf()
            elif operation == "load_product":
                self._on_select_product()
            elif operation == "export_data":
                self._on_export_data()
            elif operation == "generate_report":
                self._on_generate_report()
            elif operation == "export_report":
                self._on_export_report()
            else:
                self.logger.warning(f"未知的文件操作: {operation}")
                
        except Exception as e:
            self.logger.error(f"文件操作失败: {e}")
            self.error_occurred.emit(f"文件操作失败: {e}")
    
    def _on_export_data(self):
        """导出数据"""
        try:
            self.logger.info("📤 导出数据")
            
            if self.controller and hasattr(self.controller, 'export_data'):
                success = self.controller.export_data()
                if success:
                    self.status_updated.emit("数据导出成功")
                else:
                    self.error_occurred.emit("数据导出失败")
            else:
                # 备用实现
                from PySide6.QtWidgets import QFileDialog, QMessageBox
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "导出数据", "", "Excel Files (*.xlsx);;CSV Files (*.csv)"
                )
                if file_path:
                    QMessageBox.information(self, "提示", f"数据将导出到: {file_path}")
                    self.status_updated.emit("数据导出功能待实现")
                    
        except Exception as e:
            self.logger.error(f"导出数据失败: {e}")
            self.error_occurred.emit(f"导出数据失败: {e}")
    
    def _on_generate_report(self):
        """生成报告"""
        try:
            self.logger.info("📋 生成报告")
            
            if self.controller and hasattr(self.controller, 'generate_report'):
                success = self.controller.generate_report()
                if success:
                    self.status_updated.emit("报告生成成功")
                else:
                    self.error_occurred.emit("报告生成失败")
            else:
                self.status_updated.emit("报告生成功能待实现")
                
        except Exception as e:
            self.logger.error(f"生成报告失败: {e}")
            self.error_occurred.emit(f"生成报告失败: {e}")
    
    def _on_export_report(self):
        """导出报告"""
        try:
            self.logger.info("📄 导出报告")
            
            if self.controller and hasattr(self.controller, 'export_report'):
                success = self.controller.export_report()
                if success:
                    self.status_updated.emit("报告导出成功")
                else:
                    self.error_occurred.emit("报告导出失败")
            else:
                # 备用实现
                from PySide6.QtWidgets import QFileDialog, QMessageBox
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "导出报告", "", "PDF Files (*.pdf);;Word Files (*.docx)"
                )
                if file_path:
                    QMessageBox.information(self, "提示", f"报告将导出到: {file_path}")
                    self.status_updated.emit("报告导出功能待实现")
                    
        except Exception as e:
            self.logger.error(f"导出报告失败: {e}")
            self.error_occurred.emit(f"导出报告失败: {e}")
    
    def _on_start_simulation(self):
        """开始模拟检测 - 使用 SimulationController"""
        try:
            self.logger.info("🐍 开始模拟检测 - 使用 SimulationController")
            
            # 确保有孔位数据
            if self.controller and self.controller.hole_collection:
                # 检查是否有未完成的批次
                if hasattr(self.controller, 'current_batch_id') and self.controller.current_batch_id:
                    # 检查批次状态
                    batch_info = self.controller.batch_service.get_batch_info(self.controller.current_batch_id)
                    if batch_info and batch_info.get('status') == 'PAUSED':
                        # 继续之前的批次
                        self.logger.debug(f"📥 [MainPage] 继续批次: {self.controller.current_batch_id}")
                        self.logger.info(f"继续批次: {self.controller.current_batch_id}")
                    else:
                        # 创建新批次
                        self._create_new_batch()
                else:
                    # 创建新批次
                    self._create_new_batch()
                
                # 使用 SimulationController
                self._use_simulation_controller()
            else:
                self.error_occurred.emit("请先加载DXF文件或选择产品")
                    
        except Exception as e:
            self.logger.error(f"开始模拟检测失败: {e}")
            self.error_occurred.emit(f"模拟检测失败: {e}")
    
    def _create_new_batch(self):
        """创建新的检测批次"""
        if self.controller.current_product_id:
            try:
                # 获取产品名称
                if hasattr(self.controller.current_product, 'model_name'):
                    product_name = self.controller.current_product.model_name
                elif isinstance(self.controller.current_product, dict):
                    product_name = self.controller.current_product.get('model_name', 'Unknown')
                elif isinstance(self.controller.current_product, str):
                    product_name = self.controller.current_product
                else:
                    product_name = "Unknown"
                
                batch = self.controller.batch_service.create_batch(
                    product_id=self.controller.current_product_id,
                    product_name=product_name,
                    is_mock=True
                )
                self.controller.current_batch_id = batch.batch_id
                self.logger.info(f"Created batch: {batch.batch_id}")
                
                # 发出批次创建信号
                self.logger.debug(f"📤 [MainPage] 发射批次创建信号: {batch.batch_id}")
                self.controller.batch_created.emit(batch.batch_id)
                self.logger.debug(f"✅ [MainPage] 批次信号已发射")
                
                # 直接更新批次标签（作为备份方案）
                if hasattr(self.native_view, 'left_panel') and hasattr(self.native_view.left_panel, 'current_batch_label'):
                    self.native_view.left_panel.current_batch_label.setText(f"检测批次: {batch.batch_id}")
                    self.logger.debug(f"📝 [MainPage] 直接更新批次标签: {batch.batch_id}")
            except Exception as e:
                self.logger.warning(f"创建批次失败: {e}")
    
    def _use_simulation_controller(self):
        """使用 SimulationController 进行模拟检测"""
        try:
            if self.simulation_controller:
                if self.controller and self.controller.hole_collection:
                    # 检查是否已经在运行，避免双重启动
                    if hasattr(self.simulation_controller, 'is_running') and self.simulation_controller.is_running:
                        self.logger.warning("SimulationController 已在运行，避免重复启动")
                        return
                    
                    # 加载孔位数据到模拟控制器
                    self.simulation_controller.load_hole_collection(self.controller.hole_collection)
                    # 启动模拟（使用10秒定时器）
                    self.simulation_controller.start_simulation()
                    # 更新UI状态
                    self._update_simulation_ui_state(True)
                    self.logger.info("✅ 成功启动模拟检测（SimulationController）")
                else:
                    self.error_occurred.emit("请先加载DXF文件或选择产品")
            else:
                self.status_updated.emit("模拟检测功能正在实现中")
        except Exception as e:
            self.logger.error(f"SimulationController 启动失败: {e}")
            self.error_occurred.emit(f"模拟检测失败: {e}")
    
    def _on_pause_simulation(self):
        """暂停/恢复模拟检测"""
        try:
            if self.simulation_controller:
                if self.simulation_controller.is_paused:
                    # 恢复模拟
                    self.logger.info("▶️ 恢复模拟检测")
                    self.simulation_controller.resume_simulation()
                    self.status_updated.emit("模拟检测已恢复")
                    # 更新按钮文本
                    if hasattr(self.native_view.right_panel, 'pause_simulation_btn'):
                        self.native_view.right_panel.pause_simulation_btn.setText("暂停模拟")
                else:
                    # 暂停模拟
                    self.logger.info("⏸️ 暂停模拟检测")
                    self.simulation_controller.pause_simulation()
                    self.status_updated.emit("模拟检测已暂停")
                    # 更新按钮文本
                    if hasattr(self.native_view.right_panel, 'pause_simulation_btn'):
                        self.native_view.right_panel.pause_simulation_btn.setText("恢复模拟")
                    
        except Exception as e:
            self.logger.error(f"暂停/恢复模拟检测失败: {e}")
            
    def _on_stop_simulation(self):
        """停止模拟检测"""
        try:
            self.logger.info("⏹️ 停止模拟检测")
            
            # 停止SimulationController
            if self.simulation_controller and hasattr(self.simulation_controller, 'is_running') and self.simulation_controller.is_running:
                self.simulation_controller.stop_simulation()
                self._update_simulation_ui_state(False)
                self.logger.info("🛑 SimulationController已停止")
                
            # 重置按钮文本
            if hasattr(self.native_view.right_panel, 'pause_simulation_btn'):
                self.native_view.right_panel.pause_simulation_btn.setText("暂停模拟")
                    
            self.status_updated.emit("模拟检测已停止")
                    
        except Exception as e:
            self.logger.error(f"停止模拟检测失败: {e}")
    
    def _on_hole_selected(self, hole_id):
        """处理孔位选择"""
        try:
            self.logger.info(f"🎯 选中孔位: {hole_id}")
            
            # 更新原生视图的左侧面板显示
            if hasattr(self, 'native_view') and self.native_view.left_panel:
                hole_data = {
                    'id': hole_id,
                    'position': f"({100}, {200})",  # 这里可以从实际数据获取
                    'status': '待检',
                    'description': '选中的孔位'
                }
                self.native_view.left_panel.update_hole_info(hole_data)
            
            # 发射状态更新信号
            self.status_updated.emit(f"已选中孔位: {hole_id}")
                
        except Exception as e:
            self.logger.error(f"处理孔位选择失败: {e}")
    
    def _on_view_mode_changed(self, mode):
        """处理视图模式变化"""
        try:
            self.logger.info(f"🔄 视图模式变化: {mode}")
            
            mode_names = {
                'macro': '宏观视图',
                'micro': '微观视图', 
                'panorama': '全景视图'
            }
            
            mode_name = mode_names.get(mode, mode)
            
            # 使用控制器切换视图模式
            if self.controller and hasattr(self.controller, 'switch_view_mode'):
                success = self.controller.switch_view_mode(mode)
                if success:
                    self.status_updated.emit(f"已切换到{mode_name}")
                else:
                    self.error_occurred.emit(f"切换到{mode_name}失败")
            else:
                self.status_updated.emit(f"视图模式: {mode_name}")
                
        except Exception as e:
            self.logger.error(f"处理视图模式变化失败: {e}")
    
    def _on_status_updated_from_controller(self, hole_id: str, status: str):
        """处理来自控制器的状态更新信号（适配器）"""
        # 转发给内部的status_updated信号
        self.status_updated.emit(f"孔位 {hole_id} 状态更新为 {status}")
        # 更新统计信息等
        self._update_statistics()
    
    def _on_detection_progress_from_controller(self, current: int, total: int):
        """处理来自控制器的检测进度信号（适配器）"""
        if total > 0:
            progress = int((current / total) * 100)
            self._on_detection_progress(progress)
            # 通过原生视图更新进度显示
            if hasattr(self.native_view, 'update_detection_progress'):
                self.native_view.update_detection_progress((current, total))
    
    def _on_error_from_controller(self, error_msg: str):
        """处理来自控制器的错误信号（适配器）"""
        self.error_occurred.emit(error_msg)
        self.logger.error(f"控制器错误: {error_msg}")
    
    def _on_batch_created(self, batch_id: str):
        """处理批次创建信号"""
        try:
            self.logger.debug(f"📥 [MainPage] 接收到批次创建信号: {batch_id}")
            self.logger.info(f"批次创建信号接收: {batch_id}")
            
            # 更新左侧面板的批次信息
            if hasattr(self.native_view, 'left_panel'):
                left_panel = self.native_view.left_panel
                
                # 尝试多种可能的批次更新方法
                if hasattr(left_panel, 'update_batch_info'):
                    left_panel.update_batch_info(batch_id)
                    self.logger.info(f"✅ 通过update_batch_info更新批次: {batch_id}")
                
                # 直接更新批次标签
                if hasattr(left_panel, 'current_batch_label'):
                    left_panel.current_batch_label.setText(f"检测批次: {batch_id}")
                    self.logger.info(f"✅ 直接更新left_panel批次标签: {batch_id}")
            
            # 检查native_view级别的批次标签
            if hasattr(self.native_view, 'current_batch_label'):
                self.native_view.current_batch_label.setText(f"检测批次: {batch_id}")
                self.logger.info(f"✅ 更新native_view批次标签: {batch_id}")
            
            # 尝试查找所有可能的批次显示组件
            def update_batch_labels(widget, batch_id):
                """递归查找并更新所有批次标签"""
                if hasattr(widget, 'setText') and hasattr(widget, 'text'):
                    current_text = widget.text()
                    if "检测批次" in current_text:
                        widget.setText(f"检测批次: {batch_id}")
                        self.logger.info(f"✅ 找到并更新批次标签: {batch_id}")
                
                # 递归检查子组件
                if hasattr(widget, 'children'):
                    for child in widget.children():
                        if hasattr(child, 'metaObject'):  # 确保是Qt对象
                            update_batch_labels(child, batch_id)
            
            # 递归更新所有可能的批次标签
            update_batch_labels(self.native_view, batch_id)
                
        except Exception as e:
            self.logger.error(f"更新批次信息失败: {e}")
            import traceback
            self.logger.error(f"错误详情: {traceback.format_exc()}")
    
    def _update_statistics(self):
        """更新统计信息"""
        try:
            if self.controller:
                stats = self.controller.get_statistics()
                self.logger.info(f"统计信息更新: {stats}")
        except Exception as e:
            self.logger.error(f"更新统计信息失败: {e}")
            
    def _setup_simulation_controller(self):
        """设置模拟控制器"""
        # 使用 native_view 的 simulation_controller
        if hasattr(self.native_view, 'simulation_controller'):
            self.simulation_controller = self.native_view.simulation_controller
            
            # native_view 已经设置好了所有组件，这里只需要连接额外的信号
            # 避免重复连接，只连接 MainDetectionPage 特有的处理
            # 注意：simulation_progress 已经在 native_view 中连接了，这里不再重复连接
            
            self.logger.info("✅ 使用 NativeMainDetectionView 的 SimulationController")
        else:
            self.logger.warning("⚠️ NativeMainDetectionView 没有 simulation_controller")
            
    def _update_simulation_ui_state(self, running):
        """更新模拟UI状态"""
        if hasattr(self.native_view, 'right_panel'):
            panel = self.native_view.right_panel
            if hasattr(panel, 'start_simulation_btn'):
                panel.start_simulation_btn.setEnabled(not running)
            if hasattr(panel, 'pause_simulation_btn'):
                panel.pause_simulation_btn.setEnabled(running)
            if hasattr(panel, 'stop_simulation_btn'):
                panel.stop_simulation_btn.setEnabled(running)
                
    def _on_simulation_progress(self, current, total):
        """处理模拟进度"""
        progress = int(current / total * 100) if total > 0 else 0
        self.detection_progress.emit(progress)
        # 移除重复的日志输出，native_view 已经输出了
        # self.logger.info(f"模拟进度: {current}/{total} ({progress}%)")
        
    def _on_hole_status_updated(self, hole_id, status):
        """处理孔位状态更新 - 增强版本"""
        self.status_updated.emit(f"孔位 {hole_id} 状态更新")
        
        # 更新左侧面板信息
        if hasattr(self, 'native_view') and self.native_view and hasattr(self.native_view, 'left_panel'):
            try:
                # 获取孔位数据
                if self.controller and hasattr(self.controller, 'hole_collection'):
                    hole_collection = self.controller.hole_collection
                    if hole_collection and hole_id in hole_collection.holes:
                        hole_data = hole_collection.holes[hole_id]
                        # 构建信息字典
                        hole_info = {
                            'id': hole_id,
                            'position': f'({hole_data.center_x:.1f}, {hole_data.center_y:.1f})',
                            'status': status.value if hasattr(status, 'value') else str(status),
                            'description': f'半径: {hole_data.radius:.2f}'
                        }
                        # 更新左侧面板
                        self.native_view.left_panel.update_hole_info(hole_info)
            except Exception as e:
                self.logger.debug(f"更新左侧面板信息失败: {e}")
        
    def _on_simulation_completed(self):
        """处理模拟完成"""
        self._update_simulation_ui_state(False)
        self.status_updated.emit("模拟检测完成")
        self.logger.info("✅ 模拟检测完成")