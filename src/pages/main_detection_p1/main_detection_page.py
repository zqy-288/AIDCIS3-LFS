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
        
        # UI组件
        self.load_dxf_btn = None
        self.select_product_btn = None
        self.start_detection_btn = None
        self.pause_detection_btn = None
        self.stop_detection_btn = None
        self.detection_progress = None
        self.graphics_view = None
        self.panorama_widget = None
        self.sector_views = {}
        
        # 视图联动相关
        self.current_hole_data = []
        self.current_selected_region = None
        self.panorama_regions = []  # 全景图区域划分
        
        self.setup_ui()
        self.setup_connections()
        
        if self.controller:
            self.controller.initialize()
        
    def setup_ui(self):
        """设置UI布局 - 还原重构前的AIDCIS2界面"""
        layout = QVBoxLayout(self)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        
        # 文件操作按钮
        self.load_dxf_btn = QPushButton("加载DXF")
        self.select_product_btn = QPushButton("选择产品")
        toolbar_layout.addWidget(self.load_dxf_btn)
        toolbar_layout.addWidget(self.select_product_btn)
        
        toolbar_layout.addStretch()
        
        # 检测控制按钮
        self.start_detection_btn = QPushButton("开始检测")
        self.pause_detection_btn = QPushButton("暂停")
        self.stop_detection_btn = QPushButton("停止")
        
        toolbar_layout.addWidget(self.start_detection_btn)
        toolbar_layout.addWidget(self.pause_detection_btn)
        toolbar_layout.addWidget(self.stop_detection_btn)
        
        layout.addLayout(toolbar_layout)
        
        # 主内容区域
        content_layout = QHBoxLayout()
        
        # 左侧：图形视图
        left_panel = QVBoxLayout()
        
        # 创建优化的图形视图
        try:
            from src.core_business.graphics.graphics_view import OptimizedGraphicsView
            self.graphics_view = OptimizedGraphicsView()
            self.logger.info("使用OptimizedGraphicsView")
        except ImportError:
            self.logger.warning("无法导入OptimizedGraphicsView，使用备用视图")
            self.graphics_view = self._create_fallback_graphics_view()
            
        self.graphics_view.setMinimumSize(600, 400)
        left_panel.addWidget(self.graphics_view)
        
        # 进度条
        self.detection_progress = QProgressBar()
        left_panel.addWidget(self.detection_progress)
        
        content_layout.addLayout(left_panel, 2)
        
        # 右侧：全景图和扇形视图
        right_panel = QVBoxLayout()
        
        # 全景图
        panorama_group = QGroupBox("全景图")
        panorama_layout = QVBoxLayout(panorama_group)
        
        # 创建完整的全景图组件
        try:
            from src.core_business.graphics.panorama import CompletePanoramaWidgetAdapter
            self.panorama_widget = CompletePanoramaWidgetAdapter()
            self.logger.info("使用新架构的CompletePanoramaWidgetAdapter显示所有孔位")
            
            # 连接全景图的扇形点击信号
            self.panorama_widget.sector_clicked.connect(self._on_panorama_sector_clicked)
        except ImportError:
            self.logger.warning("无法导入CompletePanoramaWidget，使用交互式备用方案")
            self.panorama_widget = self._create_interactive_panorama()
            
        # 为全景图设置合适的大小
        self.panorama_widget.setFixedSize(400, 400)
        panorama_layout.addWidget(self.panorama_widget)
        
        right_panel.addWidget(panorama_group)
        
        # 扇形视图
        sectors_group = QGroupBox("扇形视图")
        sectors_layout = QHBoxLayout(sectors_group)
        
        # 创建扇形视图
        try:
            from src.core_business.graphics.graphics_view import OptimizedGraphicsView
            from src.core_business.graphics.sector_types import SectorQuadrant
            
            # 创建4个独立的优化图形视图作为扇形视图
            sector_names = ["左上", "右上", "左下", "右下"]
            for i, (sector, name) in enumerate(zip([SectorQuadrant.SECTOR_1, SectorQuadrant.SECTOR_2, 
                                                    SectorQuadrant.SECTOR_3, SectorQuadrant.SECTOR_4], 
                                                   sector_names)):
                # 创建框架
                from PySide6.QtCore import Qt
                
                frame = QFrame()
                frame.setFrameStyle(QFrame.Box)
                frame_layout = QVBoxLayout(frame)
                frame_layout.setContentsMargins(2, 2, 2, 2)
                frame_layout.setSpacing(2)
                
                # 创建标签
                label = QLabel(name)
                label.setAlignment(Qt.AlignCenter)
                label.setMaximumHeight(20)
                frame_layout.addWidget(label)
                
                # 创建视图
                sector_view = OptimizedGraphicsView()
                sector_view.setMaximumHeight(120)
                frame_layout.addWidget(sector_view)
                
                # 保存视图引用
                self.sector_views[f"sector_{i+1}"] = sector_view
                
                # 设置框架大小
                frame.setFixedSize(150, 150)
                sectors_layout.addWidget(frame)
                
            self.logger.info("使用OptimizedGraphicsView创建扇形视图")
        except ImportError as e:
            self.logger.warning(f"无法创建扇形视图: {e}，使用备用方案")
            self._create_fallback_sectors(sectors_layout)
            
        right_panel.addWidget(sectors_group)
        
        content_layout.addLayout(right_panel, 1)
        
        layout.addLayout(content_layout)
        
    def _create_fallback_graphics_view(self):
        """创建回退图形视图"""
        from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsTextItem
        
        view = QGraphicsView()
        scene = QGraphicsScene()
        view.setScene(scene)
        
        # 添加占位文本
        text_item = QGraphicsTextItem("图形视图区域\n(等待加载DXF文件)")
        scene.addItem(text_item)
        
        return view
        
    def _create_fallback_panorama(self):
        """创建回退全景图"""
        from PySide6.QtWidgets import QLabel
        from PySide6.QtCore import Qt
        
        label = QLabel("全景图区域")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("border: 1px solid gray; background-color: #f0f0f0;")
        
        return label
        
    def _create_interactive_panorama(self):
        """创建交互式全景图"""
        from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
        from PySide6.QtCore import Qt, QRectF
        from PySide6.QtGui import QColor
        
        class InteractivePanoramaView(QGraphicsView):
            def __init__(self, parent_page):
                super().__init__()
                self.parent_page = parent_page
                self.scene = QGraphicsScene()
                self.setScene(self.scene)
                self.setRenderHint(QPainter.RenderHint.Antialiasing)
                self.setStyleSheet("border: 1px solid gray;")
                
                # 区域划分（4个象限）
                self.regions = [
                    {"name": "左上", "rect": QRectF(0, 0, 175, 175), "color": QColor(255, 200, 200, 100)},
                    {"name": "右上", "rect": QRectF(175, 0, 175, 175), "color": QColor(200, 255, 200, 100)},
                    {"name": "左下", "rect": QRectF(0, 175, 175, 175), "color": QColor(200, 200, 255, 100)},
                    {"name": "右下", "rect": QRectF(175, 175, 175, 175), "color": QColor(255, 255, 200, 100)}
                ]
                self.current_highlight = None
                self._setup_regions()
                
            def _setup_regions(self):
                """初始化区域"""
                from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem
                from PySide6.QtGui import QPen, QBrush
                
                for i, region in enumerate(self.regions):
                    # 创建区域矩形
                    rect_item = QGraphicsRectItem(region["rect"])
                    rect_item.setPen(QPen(QColor(100, 100, 100)))
                    rect_item.setBrush(QBrush(QColor(240, 240, 240, 50)))
                    rect_item.setData(0, i)  # 存储区域索引
                    self.scene.addItem(rect_item)
                    
                    # 添加区域标签
                    text_item = QGraphicsTextItem(region["name"])
                    text_item.setPos(region["rect"].center().x() - 20, region["rect"].center().y() - 10)
                    self.scene.addItem(text_item)
                    
                # 设置场景大小
                self.scene.setSceneRect(0, 0, 350, 350)
                
            def mousePressEvent(self, event):
                """鼠标点击事件"""
                scene_pos = self.mapToScene(event.pos())
                
                for i, region in enumerate(self.regions):
                    if region["rect"].contains(scene_pos):
                        self._highlight_region(i)
                        self.parent_page._on_panorama_region_selected(i, region)
                        break
                        
                super().mousePressEvent(event)
                
            def _highlight_region(self, region_index):
                """高亮显示选中区域"""
                from PySide6.QtWidgets import QGraphicsRectItem
                from PySide6.QtGui import QPen, QBrush
                
                # 清除之前的高亮
                if self.current_highlight:
                    self.scene.removeItem(self.current_highlight)
                    
                # 创建新的高亮
                region = self.regions[region_index]
                highlight_item = QGraphicsRectItem(region["rect"])
                highlight_item.setPen(QPen(QColor(255, 0, 0), 3))
                highlight_item.setBrush(QBrush(region["color"]))
                self.scene.addItem(highlight_item)
                self.current_highlight = highlight_item
                
            def update_holes_display(self, hole_data):
                """更新孔位显示"""
                if not hole_data:
                    return
                    
                from PySide6.QtWidgets import QGraphicsEllipseItem
                from PySide6.QtGui import QPen, QBrush
                from PySide6.QtCore import QRectF
                
                # 处理不同类型的hole_data
                if hasattr(hole_data, 'holes'):
                    holes_list = hole_data.holes if hasattr(hole_data.holes, '__iter__') else list(hole_data.holes.values())
                elif hasattr(hole_data, '__iter__'):
                    holes_list = list(hole_data)
                else:
                    return
                    
                if not holes_list:
                    return
                
                # 清除旧的孔位显示
                for item in self.scene.items():
                    if hasattr(item, 'hole_data'):
                        self.scene.removeItem(item)
                        
                # 计算缩放比例
                min_x = min(hole.center_x for hole in holes_list)
                max_x = max(hole.center_x for hole in holes_list)
                min_y = min(hole.center_y for hole in holes_list)
                max_y = max(hole.center_y for hole in holes_list)
                
                scale_x = 300 / (max_x - min_x) if max_x != min_x else 1
                scale_y = 300 / (max_y - min_y) if max_y != min_y else 1
                scale = min(scale_x, scale_y) * 0.8
                
                # 绘制孔位
                for hole in holes_list[::50]:  # 每50个孔位显示一个，减少密度
                    x = (hole.center_x - min_x) * scale + 25
                    y = (hole.center_y - min_y) * scale + 25
                    
                    circle = QGraphicsEllipseItem(QRectF(x-1, y-1, 2, 2))
                    circle.setPen(QPen(QColor(0, 100, 200)))
                    circle.setBrush(QBrush(QColor(0, 100, 200)))
                    circle.hole_data = hole  # 标记为孔位数据
                    self.scene.addItem(circle)
        
        from PySide6.QtGui import QPainter
        return InteractivePanoramaView(self)
        
    def _create_fallback_sectors(self, layout):
        """创建回退扇形视图"""
        from PySide6.QtWidgets import QLabel
        from PySide6.QtCore import Qt
        
        for i in range(4):
            label = QLabel(f"扇形{i+1}")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("border: 1px solid gray; background-color: #f0f0f0;")
            label.setFixedSize(150, 150)
            layout.addWidget(label)
        
    def setup_connections(self):
        """设置信号连接"""
        # 按钮事件
        if self.load_dxf_btn:
            self.load_dxf_btn.clicked.connect(self._on_load_dxf)
        if self.select_product_btn:
            self.select_product_btn.clicked.connect(self._on_select_product)
        if self.start_detection_btn:
            self.start_detection_btn.clicked.connect(self._on_start_detection)
        if self.pause_detection_btn:
            self.pause_detection_btn.clicked.connect(self._on_pause_detection)
        if self.stop_detection_btn:
            self.stop_detection_btn.clicked.connect(self._on_stop_detection)
            
        # 控制器信号
        if self.controller:
            self.controller.file_loaded.connect(self._on_file_loaded)
            self.controller.status_updated.connect(self.status_updated)
            self.controller.detection_progress.connect(self._on_detection_progress)
            self.controller.error_occurred.connect(self.error_occurred)
        
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
            self.controller.select_product()
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
        if self.detection_progress:
            self.detection_progress.setValue(progress)
            
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
                    
            # 更新全景图（右上）
            try:
                self.logger.info(f"全景图组件类型: {type(self.panorama_widget)}")
                self.logger.info(f"全景图组件方法: {[m for m in dir(self.panorama_widget) if 'load' in m or 'update' in m]}")
                
                if hasattr(self.panorama_widget, 'load_complete_view'):
                    # 使用CompletePanoramaWidget的load_complete_view方法
                    self.logger.info("调用load_complete_view方法...")
                    self.panorama_widget.load_complete_view(hole_data)
                    self.logger.info("✅ 全景图已调用load_complete_view")
                elif hasattr(self.panorama_widget, 'load_hole_collection'):
                    # 备用方法名
                    self.logger.info("调用load_hole_collection方法...")
                    self.panorama_widget.load_hole_collection(hole_data)
                elif hasattr(self.panorama_widget, 'update_holes_display'):
                    # 交互式全景图的方法
                    self.logger.info("调用update_holes_display方法...")
                    self.panorama_widget.update_holes_display(hole_data)
                else:
                    self.logger.warning("全景图组件没有合适的加载方法")
            except Exception as e:
                self.logger.error(f"更新全景图失败: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
                
            # 初始化时更新所有扇形视图
            self._update_all_sector_views(hole_data)
                    
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
            
    def _on_panorama_sector_clicked(self, sector):
        """处理CompletePanoramaWidget的扇形点击事件"""
        try:
            from src.core_business.graphics.sector_types import SectorQuadrant
            
            self.logger.info(f"全景图扇形点击: {sector.value}")
            
            # 更新当前选择的扇形
            self.current_selected_sector = sector
            
            # 如果有孔位数据，根据扇形过滤
            if self.current_hole_data:
                # 获取该扇形的孔位数据
                filtered_holes = self._filter_holes_by_sector(self.current_hole_data, sector)
                
                # 更新左侧主视图显示选中扇形的放大图
                self._display_sector_detail(filtered_holes, sector)
                
                # 更新对应的扇形视图（如果存在）
                self._update_sector_views(sector, filtered_holes)
                
        except Exception as e:
            self.logger.error(f"处理全景图扇形点击失败: {e}")
            
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