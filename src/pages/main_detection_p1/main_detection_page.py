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
    from src.controllers.main_window_controller import MainWindowController
    from src.ui.factories import get_ui_factory
    from src.services import get_graphics_service
except ImportError as e:
    logging.warning(f"无法导入控制器/服务: {e}, 使用模拟实现")
    MainWindowController = None
    get_ui_factory = None
    get_graphics_service = None


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
        
        # 控制器和服务（单例模式避免重复创建）
        if not hasattr(MainDetectionPage, '_shared_controller'):
            MainDetectionPage._shared_controller = MainWindowController() if MainWindowController else None
        if not hasattr(MainDetectionPage, '_shared_ui_factory'):
            MainDetectionPage._shared_ui_factory = get_ui_factory() if get_ui_factory else None
        if not hasattr(MainDetectionPage, '_shared_graphics_service'):
            MainDetectionPage._shared_graphics_service = get_graphics_service() if get_graphics_service else None
            
        self.controller = MainDetectionPage._shared_controller
        self.ui_factory = MainDetectionPage._shared_ui_factory  
        self.graphics_service = MainDetectionPage._shared_graphics_service
        
        # UI组件 - 通过原生视图访问
        self.graphics_view = None
        self.panorama_widget = None
        
        # 视图联动相关
        self.current_hole_data = []
        self.current_selected_region = None
        self.panorama_regions = []  # 全景图区域划分
        
        self.setup_ui()
        self.setup_connections()
        
        if self.controller:
            self.controller.initialize()
        
    def setup_ui(self):
        """设置UI布局 - 使用原生三栏式布局还原old版本"""
        # 导入并使用原生主检测视图 - 不使用任何回退机制
        from src.modules.native_main_detection_view import NativeMainDetectionView
        
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 创建原生主检测视图
        self.native_view = NativeMainDetectionView()
        layout.addWidget(self.native_view)
        
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
        self.native_view.detection_progress.connect(self.detection_progress)
        self.native_view.error_occurred.connect(self.error_occurred)
        
        # 连接工具栏信号到具体功能
        toolbar = self.native_view.toolbar
        toolbar.product_selection_requested.connect(self._on_select_product)
        toolbar.search_requested.connect(self._on_search_hole)
        
        # 连接右侧面板的文件操作信号
        right_panel = self.native_view.right_panel
        right_panel.file_operation_requested.connect(self._on_file_operation)
        right_panel.start_detection.connect(self._on_start_detection)
        right_panel.pause_detection.connect(self._on_pause_detection)
        right_panel.stop_detection.connect(self._on_stop_detection)
        right_panel.simulation_start.connect(self._on_start_simulation)
        
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
        
        self.logger.info("✅ 原生视图信号连接成功")
        
    def _on_load_dxf(self):
        """加载DXF文件"""
        if self.controller:
            self.controller.load_dxf_file()
            # 确保数据传递到图形视图
            self._update_graphics_view()
        else:
            print("加载DXF - 控制器未初始化")
            
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
        if self.controller:
            # 显示产品选择对话框
            if self.ui_factory:
                try:
                    dialog = self.ui_factory.create_product_selection_dialog(self)
                    if dialog.exec():
                        product_name = dialog.selected_product
                        self.controller.select_product(product_name)
                except Exception as e:
                    self.logger.error(f"产品选择失败: {e}")
                    # 备用方案
                    from PySide6.QtWidgets import QInputDialog
                    product_name, ok = QInputDialog.getText(self, "选择产品", "请输入产品名称:")
                    if ok and product_name:
                        self.controller.select_product(product_name)
            else:
                # 简单的备用方案
                from PySide6.QtWidgets import QInputDialog
                product_name, ok = QInputDialog.getText(self, "选择产品", "请输入产品名称:")
                if ok and product_name:
                    self.controller.select_product(product_name)
        else:
            print("选择产品 - 控制器未初始化")
            
    def _on_start_detection(self):
        """开始检测"""
        if self.controller:
            self.controller.start_detection()
        else:
            print("开始检测 - 控制器未初始化")
            
    def _on_pause_detection(self):
        """暂停检测"""
        if self.controller:
            self.controller.pause_detection()
        else:
            print("暂停检测 - 控制器未初始化")
            
    def _on_stop_detection(self):
        """停止检测"""
        if self.controller:
            self.controller.stop_detection()
        else:
            print("停止检测 - 控制器未初始化")
            
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
            if not self.controller or not hasattr(self.controller, 'hole_collection') or not self.controller.hole_collection:
                self.logger.warning("⚠️ 无法获取孔位数据")
                return
                
            hole_data = self.controller.hole_collection
            self.current_hole_data = hole_data
            
            # 获取孔位数量信息
            if hasattr(hole_data, 'holes'):
                hole_count = len(hole_data.holes) if hasattr(hole_data.holes, '__len__') else '未知'
            else:
                hole_count = '未知'
            
            self.logger.info(f"📊 开始显示 {hole_count} 个孔位")
            
            # 更新主图形视图（左侧）
            if self.graphics_view and hasattr(self.graphics_view, 'load_holes'):
                # 使用OptimizedGraphicsView的load_holes方法
                self.graphics_view.load_holes(hole_data)
                self.logger.info("✅ 主视图已加载孔位数据")
            elif hasattr(self.graphics_view, 'scene'):
                # 备用方案：手动绘制
                try:
                    scene = self.graphics_view.scene()
                except TypeError:
                    scene = self.graphics_view.scene
                    
                if scene:
                    scene.clear()
                    self._draw_holes_to_scene(scene, hole_data)
                    
            # 更新全景图
            if hasattr(self.panorama_widget, 'update_holes_display'):
                self.panorama_widget.update_holes_display(hole_data)
                    
            self.logger.info("✅ 图形视图更新完成")
                
        except Exception as e:
            self.logger.error(f"❌ 更新图形视图失败: {e}")
            
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
            from src.core_business.graphics.sector_types import SectorQuadrant
            
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
                from src.core_business.models.hole_data import HoleCollection
                
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
            from src.core_business.graphics.sector_types import SectorQuadrant
            
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
            self.logger.info(f"🔍 搜索孔位: {query}")
            
            # 使用控制器的搜索功能
            if self.controller and hasattr(self.controller, 'search_hole'):
                results = self.controller.search_hole(query)
                self.logger.info(f"搜索到 {len(results)} 个结果")
            else:
                self.logger.warning("控制器搜索功能不可用")
                
        except Exception as e:
            self.logger.error(f"搜索孔位失败: {e}")
            self.error_occurred.emit(f"搜索失败: {e}")
    
    def _on_file_operation(self, operation, params):
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
    
    def _on_start_simulation(self, params):
        """开始模拟"""
        try:
            self.logger.info(f"🧪 开始模拟: {params}")
            
            speed = params.get('speed', '正常')
            quality_rate = params.get('quality_rate', '90%')
            
            if self.controller and hasattr(self.controller, 'start_simulation'):
                success = self.controller.start_simulation(speed, quality_rate)
                if success:
                    self.status_updated.emit(f"模拟已开始 - 速度:{speed}, 合格率:{quality_rate}")
                else:
                    self.error_occurred.emit("模拟启动失败")
            else:
                self.status_updated.emit(f"模拟功能 - 速度:{speed}, 合格率:{quality_rate} (待实现)")
                
        except Exception as e:
            self.logger.error(f"开始模拟失败: {e}")
            self.error_occurred.emit(f"模拟启动失败: {e}")
    
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
                self.native_view.update_detection_progress(current, total)
    
    def _on_error_from_controller(self, error_msg: str):
        """处理来自控制器的错误信号（适配器）"""
        self.error_occurred.emit(error_msg)
        self.logger.error(f"控制器错误: {error_msg}")
    
    def _update_statistics(self):
        """更新统计信息"""
        try:
            if self.controller:
                stats = self.controller.get_statistics()
                self.logger.info(f"统计信息更新: {stats}")
        except Exception as e:
            self.logger.error(f"更新统计信息失败: {e}")