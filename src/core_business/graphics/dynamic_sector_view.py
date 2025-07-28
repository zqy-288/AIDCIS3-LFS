"""
动态扇形区域显示组件（重构版）
专注于UI展示和用户交互，数据处理委托给其他服务
"""

from typing import Dict, Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy
from PySide6.QtCore import Qt, Signal, QTimer

from src.core_business.graphics.graphics_view import OptimizedGraphicsView
from src.core_business.graphics.sector_controllers import (
    SectorViewController, UnifiedPanoramaController, StatusController, 
    ViewTransformController, UnifiedLogger
)
from src.core_business.models.hole_data import HoleCollection
from src.core_business.graphics.sector_types import SectorQuadrant
from src.core_business.graphics.panorama import CompletePanoramaWidget
from src.core_business.graphics.sector_view_factory import SectorViewFactory
from src.core_business.graphics.sector_display_config import SectorDisplayConfig
from src.core.shared_data_manager import SharedDataManager
from src.core_business.graphics.snake_path_renderer import PathStrategy, PathRenderStyle


class DynamicSectorDisplayWidget(QWidget):
    """动态扇形区域显示组件 - 精简版"""
    
    sector_changed = Signal(SectorQuadrant)  # 扇形切换信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 依赖注入
        self.logger = UnifiedLogger("DynamicSectorDisplay")
        self.data_manager = SharedDataManager()  # 修复：使用正确的单例访问
        self.view_factory = SectorViewFactory()
        self.config = SectorDisplayConfig()
        
        # 控制器初始化
        self.sector_controller = SectorViewController(self)
        self.panorama_controller = UnifiedPanoramaController(self)
        self.status_controller = StatusController(self)
        self.transform_controller = ViewTransformController(self)
        
        # 连接信号
        self._connect_signals()
        
        # 状态管理
        self.current_sector = SectorQuadrant.SECTOR_1
        self.sector_views: Dict[SectorQuadrant, OptimizedGraphicsView] = {}
        self.hole_collection: Optional[HoleCollection] = None
        
        # 蛇形路径相关
        self.snake_path_enabled = False
        self.snake_path_strategy = PathStrategy.HYBRID
        self.snake_path_style = PathRenderStyle.SIMPLE_LINE
        self.global_snake_path = []  # 全局蛇形路径
        self.sector_snake_paths = {}  # 每个扇形的局部路径
        
        # 调试模式
        self.debug_mode = False
        
        # UI初始化
        self._setup_ui()
        
        # 响应式缩放定时器
        self._resize_timer = QTimer()
        self._resize_timer.timeout.connect(self._handle_resize_timeout)
        self._resize_timer.setSingleShot(True)
        
    def _connect_signals(self):
        """连接控制器信号"""
        self.sector_controller.sector_changed.connect(self._on_sector_changed)
        self.panorama_controller.sector_clicked.connect(self._on_sector_changed)
        
    def _setup_ui(self):
        """设置用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建主视图
        self.graphics_view = OptimizedGraphicsView()
        self.graphics_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.graphics_view.max_auto_scale = self.config.viewport.auto_scale_limit
        
        # 设置transform控制器的视图
        self.transform_controller.set_graphics_view(self.graphics_view)
        
        # 创建控制面板
        control_panel = self._create_control_panel()
        
        # 添加到布局
        main_layout.addWidget(self.graphics_view)
        main_layout.addWidget(control_panel)
        
        # 创建浮动全景图
        self._create_panorama_widget()
        
    def _create_control_panel(self) -> QWidget:
        """创建控制面板"""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 添加状态控制按钮
        status_widget = self.status_controller.create_status_buttons(panel)
        layout.addWidget(status_widget)
        
        return panel
        
    def _create_panorama_widget(self):
        """创建浮动全景图 - 使用重构后的架构"""
        from src.core_business.graphics.panorama.di_container import PanoramaDIContainer
        from src.core_business.graphics.panorama.legacy_adapter import CompletePanoramaWidgetAdapter
        
        # 创建依赖注入容器
        di_container = PanoramaDIContainer()
        
        # 创建遗留适配器以保持向后兼容
        legacy_adapter = CompletePanoramaWidgetAdapter(di_container)
        
        # 直接使用适配器作为全景图组件
        self.mini_panorama = legacy_adapter
        self.mini_panorama.setParent(self)
        
        self.mini_panorama.setFixedSize(
            self.config.panorama.widget_width,
            self.config.panorama.widget_height
        )
        self.mini_panorama.move(
            self.config.panorama.position_x,
            self.config.panorama.position_y
        )
        self.mini_panorama.setWindowOpacity(self.config.panorama.opacity)
        
        # 连接全景图信号
        self.mini_panorama.sector_clicked.connect(self._on_sector_changed)
        
    def set_hole_collection(self, collection: HoleCollection):
        """
        设置孔位集合 - 简化版
        数据处理已由其他服务完成，这里只负责显示
        """
        self.logger.info("设置孔位集合")
        
        if not collection or not collection.holes:
            self.logger.warning("孔位集合为空")
            return
            
        self.hole_collection = collection
        
        # 获取已处理好的扇形分配数据
        sector_assignments = self.data_manager.get_sector_assignments()
        if not sector_assignments:
            self.logger.error("未找到扇形分配数据")
            return
            
        # 创建扇形视图
        self._create_sector_views(sector_assignments)
        
        # 更新全景图
        self.mini_panorama.load_hole_collection(collection)
        
        # 如果启用了蛇形路径，生成并更新路径
        if self.snake_path_enabled:
            # 设置主视图的孔位集合
            self.graphics_view.set_hole_collection(collection)
            # 生成全局路径
            self._generate_global_snake_path()
            # 更新各扇形的路径
            self._update_sector_snake_paths()
            
            if self.debug_mode:
                self.logger.info("🐍 [调试] 孔位集合设置后自动生成蛇形路径", "✅")
        
        # 显示第一个扇形
        self._switch_to_sector(SectorQuadrant.SECTOR_1)
        
    def _create_sector_views(self, sector_assignments: Dict[str, int]):
        """创建各扇形的视图"""
        self.logger.info("创建扇形视图")
        
        # 清理旧视图
        self.sector_views.clear()
        
        # 按扇形分组孔位
        sector_holes = self._group_holes_by_sector(sector_assignments)
        
        # 为每个扇形创建视图
        for sector in SectorQuadrant:
            holes = sector_holes.get(sector, [])
            if holes:
                view = self.view_factory.create_sector_view(sector, holes)
                self.sector_views[sector] = view
                self.logger.info(f"创建 {sector.name} 视图，孔位数: {len(holes)}")
                
    def _group_holes_by_sector(self, sector_assignments: Dict[str, int]) -> Dict[SectorQuadrant, list]:
        """按扇形分组孔位"""
        sector_holes = {
            SectorQuadrant.SECTOR_1: [],
            SectorQuadrant.SECTOR_2: [],
            SectorQuadrant.SECTOR_3: [],
            SectorQuadrant.SECTOR_4: []
        }
        
        # 映射数字到枚举
        sector_map = {
            1: SectorQuadrant.SECTOR_1,
            2: SectorQuadrant.SECTOR_2,
            3: SectorQuadrant.SECTOR_3,
            4: SectorQuadrant.SECTOR_4
        }
        
        for hole in self.hole_collection.holes:
            sector_id = sector_assignments.get(hole.hole_id)
            if sector_id and sector_id in sector_map:
                sector_enum = sector_map[sector_id]
                sector_holes[sector_enum].append(hole)
                
        return sector_holes
        
    def _switch_to_sector(self, sector: SectorQuadrant):
        """切换到指定扇形 - 委托给控制器"""
        self.logger.info(f"切换到扇形: {sector.name}")
        
        # 更新当前扇形
        self.current_sector = sector
        
        # 获取对应视图
        view = self.sector_views.get(sector)
        if not view:
            self.logger.warning(f"未找到 {sector.name} 的视图")
            return
            
        # 切换场景
        self.graphics_view.setScene(view.scene)
        
        # 应用最优缩放
        viewport_size = (
            self.graphics_view.viewport().width(),
            self.graphics_view.viewport().height()
        )
        self.view_factory.apply_optimal_scale(view, viewport_size)
        
        # 更新全景图高亮
        self.mini_panorama.set_current_sector(sector)
        
        # 发出信号
        self.sector_changed.emit(sector)
        
    def _on_sector_changed(self, sector: SectorQuadrant):
        """处理扇形切换事件"""
        self._switch_to_sector(sector)
        
    def resizeEvent(self, event):
        """处理窗口大小调整"""
        super().resizeEvent(event)
        
        if self.config.viewport.responsive_scale_enabled:
            # 使用定时器避免频繁调整
            self._resize_timer.stop()
            self._resize_timer.start(100)
            
    def _handle_resize_timeout(self):
        """处理大小调整超时"""
        if self.current_sector and self.current_sector in self.sector_views:
            view = self.sector_views[self.current_sector]
            viewport_size = (
                self.graphics_view.viewport().width(),
                self.graphics_view.viewport().height()
            )
            self.view_factory.apply_optimal_scale(view, viewport_size)
            
    def get_current_sector(self) -> SectorQuadrant:
        """获取当前扇形"""
        return self.current_sector
        
    def refresh_display(self):
        """刷新显示"""
        if self.hole_collection:
            self.set_hole_collection(self.hole_collection)
    
    # ==================== 蛇形路径功能 ====================
    
    def enable_snake_path(self, enabled: bool, debug: bool = False):
        """启用/禁用蛇形路径显示"""
        self.snake_path_enabled = enabled
        self.debug_mode = debug
        
        if debug:
            self.logger.info(f"🐍 [调试] 蛇形路径: {'启用' if enabled else '禁用'}", "🔧")
        
        if enabled and self.hole_collection:
            self._generate_global_snake_path()
            self._update_sector_snake_paths()
        else:
            self._clear_all_snake_paths()
    
    def set_snake_path_strategy(self, strategy: PathStrategy):
        """设置蛇形路径策略"""
        self.snake_path_strategy = strategy
        
        if self.debug_mode:
            self.logger.info(f"🐍 [调试] 路径策略: {strategy.value}", "🔧")
        
        if self.snake_path_enabled and self.hole_collection:
            self._generate_global_snake_path()
            self._update_sector_snake_paths()
    
    def set_snake_path_style(self, style: PathRenderStyle):
        """设置蛇形路径样式"""
        self.snake_path_style = style
        
        if self.debug_mode:
            self.logger.info(f"🐍 [调试] 路径样式: {style.value}", "🔧")
        
        # 更新所有视图的路径样式
        for view in self.sector_views.values():
            view.set_snake_path_style(style)
    
    def _generate_global_snake_path(self):
        """生成全局蛇形路径"""
        if not self.hole_collection:
            return
        
        # 确保主视图的蛇形路径渲染器已初始化
        if not self.graphics_view.hole_collection:
            self.graphics_view.hole_collection = self.hole_collection
            self.graphics_view.snake_path_renderer.set_hole_collection(self.hole_collection)
        
        # 使用主视图生成全局路径
        self.global_snake_path = self.graphics_view.snake_path_renderer.generate_snake_path(
            self.snake_path_strategy
        )
        
        if self.debug_mode:
            self.logger.info(f"🐍 [调试] 生成全局路径: {len(self.global_snake_path)}个孔位", "🔧")
            if len(self.global_snake_path) > 0:
                self.logger.info(f"    前5个: {self.global_snake_path[:5]}", "📍")
    
    def _update_sector_snake_paths(self):
        """更新每个扇形的局部蛇形路径"""
        if not self.global_snake_path:
            return
        
        # 清空之前的扇形路径
        self.sector_snake_paths.clear()
        
        # 获取扇形分配信息
        sector_assignments = self._get_sector_assignments()
        
        if self.debug_mode:
            self.logger.info(f"🐍 [调试] 扇形分配: {len(sector_assignments)}个孔位已分配", "🔧")
        
        # 为每个扇形生成局部路径
        for sector in SectorQuadrant:
            sector_holes = {hole_id for hole_id, assigned_sector in sector_assignments.items() 
                           if assigned_sector == sector}
            
            # 从全局路径中提取属于该扇形的孔位（保持顺序）
            sector_path = [hole_id for hole_id in self.global_snake_path 
                          if hole_id in sector_holes]
            
            self.sector_snake_paths[sector] = sector_path
            
            if self.debug_mode and sector_path:
                self.logger.info(f"🐍 [调试] {sector.value}: {len(sector_path)}个孔位", "📍")
        
        # 更新当前扇形的显示
        if self.current_sector in self.sector_views:
            self._update_current_sector_path()
    
    def _get_sector_assignments(self) -> Dict[str, SectorQuadrant]:
        """获取孔位的扇形分配"""
        # 从SharedDataManager获取扇形分配信息
        sector_assignments = self.data_manager.get_sector_assignments()
        
        if not sector_assignments:
            return {}
        
        # 映射数字到枚举
        sector_map = {
            1: SectorQuadrant.SECTOR_1,
            2: SectorQuadrant.SECTOR_2,
            3: SectorQuadrant.SECTOR_3,
            4: SectorQuadrant.SECTOR_4
        }
        
        # 转换为SectorQuadrant枚举
        converted_assignments = {}
        for hole_id, sector_num in sector_assignments.items():
            if sector_num in sector_map:
                converted_assignments[hole_id] = sector_map[sector_num]
        
        return converted_assignments
    
    def _update_current_sector_path(self):
        """更新当前扇形的路径显示"""
        if self.current_sector not in self.sector_views:
            return
        
        view = self.sector_views[self.current_sector]
        sector_path = self.sector_snake_paths.get(self.current_sector, [])
        
        if self.debug_mode:
            self.logger.info(f"🐍 [调试] 更新{self.current_sector.value}路径: {len(sector_path)}个孔位", "🔧")
        
        # 确保视图有孔位集合数据（用于蛇形路径渲染器）
        if not view.hole_collection and self.hole_collection:
            # 创建该扇形的子集合
            sector_holes = [h for h in self.hole_collection.holes if h.hole_id in sector_path]
            if sector_holes:
                from src.core_business.models.hole_data import HoleCollection
                sector_collection = HoleCollection()
                for hole in sector_holes:
                    sector_collection.add_hole(hole)
                view.hole_collection = sector_collection
                view.snake_path_renderer.set_hole_collection(sector_collection)
        
        if sector_path and view.hole_collection:
            # 设置路径数据
            view.snake_path_renderer.set_path_data(sector_path)
            # 渲染路径
            view.snake_path_renderer.render_paths()
            # 设置可见性
            view.set_snake_path_visible(self.snake_path_enabled)
        else:
            # 清除路径
            view.clear_snake_path()
    
    def _clear_all_snake_paths(self):
        """清除所有扇形的蛇形路径"""
        for view in self.sector_views.values():
            view.clear_snake_path()
        
        self.global_snake_path.clear()
        self.sector_snake_paths.clear()
        
        if self.debug_mode:
            self.logger.info("🐍 [调试] 清除所有路径", "🧹")
    
    def _switch_to_sector(self, sector: SectorQuadrant):
        """切换到指定扇形（重写以添加路径支持）"""
        self.current_sector = sector
        self.logger.info(f"切换到 {sector.name}")
        
        # 获取扇形视图
        view = self.sector_views.get(sector)
        if not view:
            self.logger.warning(f"未找到 {sector.name} 的视图")
            return
            
        # 切换场景
        self.graphics_view.setScene(view.scene)
        
        # 应用最优缩放
        viewport_size = (
            self.graphics_view.viewport().width(),
            self.graphics_view.viewport().height()
        )
        self.view_factory.apply_optimal_scale(view, viewport_size)
        
        # 更新蛇形路径显示
        if self.snake_path_enabled:
            self._update_current_sector_path()
        
        # 更新全景图高亮
        self.mini_panorama.set_current_sector(sector)
        
        # 发出信号
        self.sector_changed.emit(sector)
    
    def get_snake_path_debug_info(self) -> Dict:
        """获取蛇形路径调试信息"""
        debug_info = {
            'enabled': self.snake_path_enabled,
            'strategy': self.snake_path_strategy.value,
            'style': self.snake_path_style.value,
            'global_path_length': len(self.global_snake_path),
            'sector_paths': {}
        }
        
        for sector, path in self.sector_snake_paths.items():
            debug_info['sector_paths'][sector.value] = {
                'length': len(path),
                'first_5': path[:5] if path else []
            }
        
        # 获取当前扇形的统计信息
        if self.current_sector in self.sector_views:
            view = self.sector_views[self.current_sector]
            stats = view.get_snake_path_statistics()
            debug_info['current_sector_stats'] = stats
        
        return debug_info