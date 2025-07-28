"""
全景图视图控制器
协调各个组件，管理全景图的生命周期
"""

from typing import Optional, Dict
from PySide6.QtCore import QObject, Signal, QPointF
from PySide6.QtWidgets import QGraphicsScene

from src.core_business.graphics.panorama.interfaces import (
    IPanoramaDataModel, IPanoramaGeometryCalculator,
    IPanoramaStatusManager, IPanoramaRenderer,
    ISectorInteractionHandler, ISnakePathRenderer
)
from src.core_business.graphics.panorama.event_bus import PanoramaEventBus, PanoramaEvent
from src.core_business.models.hole_data import HoleCollection, HoleStatus
from src.core_business.graphics.sector_types import SectorQuadrant


class PanoramaViewController(QObject):
    """
    全景图视图控制器
    负责协调各个组件的工作
    """
    
    # 对外信号
    sector_clicked = Signal(SectorQuadrant)
    status_update_completed = Signal(int)
    
    def __init__(
        self,
        data_model: IPanoramaDataModel,
        geometry_calculator: IPanoramaGeometryCalculator,
        status_manager: IPanoramaStatusManager,
        renderer: IPanoramaRenderer,
        sector_handler: ISectorInteractionHandler,
        snake_path_renderer: ISnakePathRenderer,
        event_bus: PanoramaEventBus,
        scene: QGraphicsScene
    ):
        super().__init__()
        
        # 注入依赖
        self.data_model = data_model
        self.geometry_calculator = geometry_calculator
        self.status_manager = status_manager
        self.renderer = renderer
        self.sector_handler = sector_handler
        self.snake_path_renderer = snake_path_renderer
        self.event_bus = event_bus
        self.scene = scene
        
        # 内部状态
        self.center_point: Optional[QPointF] = None
        self.panorama_radius: float = 0.0
        self.hole_items: Dict[str, any] = {}
        
        # 设置事件订阅
        self._setup_event_subscriptions()
        
        # 连接组件信号
        self._connect_signals()
    
    def _setup_event_subscriptions(self):
        """设置事件订阅"""
        # 订阅数据事件
        self.event_bus.subscribe(PanoramaEvent.DATA_LOADED, self._on_data_loaded)
        self.event_bus.subscribe(PanoramaEvent.DATA_CLEARED, self._on_data_cleared)
        self.event_bus.subscribe(PanoramaEvent.HOLE_STATUS_CHANGED, self._on_hole_status_changed)
        
        # 订阅交互事件
        self.event_bus.subscribe(PanoramaEvent.SECTOR_CLICKED, self._on_sector_clicked)
        
        # 订阅渲染事件
        self.event_bus.subscribe(PanoramaEvent.RENDER_REQUESTED, self._on_render_requested)
        self.event_bus.subscribe(PanoramaEvent.THEME_CHANGED, self._on_theme_changed)
    
    def _connect_signals(self):
        """连接组件信号"""
        if hasattr(self.data_model, 'data_loaded'):
            self.data_model.data_loaded.connect(self._handle_data_loaded)
        
        if hasattr(self.status_manager, 'batch_update_completed'):
            self.status_manager.batch_update_completed.connect(self.status_update_completed.emit)
    
    def load_hole_collection(self, hole_collection: HoleCollection):
        """
        加载孔位集合
        
        Args:
            hole_collection: 孔位集合
        """
        # 清空场景
        self.scene.clear()
        self.hole_items.clear()
        
        # 加载数据
        self.data_model.load_hole_collection(hole_collection)
    
    def _handle_data_loaded(self):
        """处理数据加载完成"""
        # 获取孔位数据
        holes = self.data_model.get_holes()
        if not holes:
            return
        
        # 计算几何信息
        self.center_point = self.geometry_calculator.calculate_center(holes)
        self.panorama_radius = self.geometry_calculator.calculate_radius(holes, self.center_point)
        
        # 计算显示参数
        hole_count = len(holes)
        density = self.geometry_calculator.calculate_data_density(hole_count, self.panorama_radius)
        data_scale = self.geometry_calculator.detect_data_scale(hole_count)
        
        # 计算孔位显示大小
        base_size = self.geometry_calculator.calculate_hole_display_size(hole_count, self.panorama_radius, density)
        scale_factor = self.geometry_calculator.get_scale_factor(data_scale)
        hole_size = base_size * scale_factor
        
        # 渲染孔位
        self.hole_items = self.renderer.render_holes(holes, self.scene, hole_size)
        
        # 渲染扇区分隔线
        self.renderer.render_sector_dividers(self.center_point, self.panorama_radius, self.scene)
        
        # 设置扇区交互
        self.sector_handler.set_geometry(self.center_point, self.panorama_radius, self.scene)
        
        # 发布几何变更事件
        self.event_bus.publish(PanoramaEvent.GEOMETRY_CHANGED, {
            'center': self.center_point,
            'radius': self.panorama_radius
        })
    
    def update_hole_status(self, hole_id: str, status: HoleStatus):
        """
        更新孔位状态
        
        Args:
            hole_id: 孔位ID
            status: 新状态
        """
        self.status_manager.queue_status_update(hole_id, status)
    
    def highlight_sector(self, sector: SectorQuadrant):
        """
        高亮扇区
        
        Args:
            sector: 扇区
        """
        self.sector_handler.highlight_sector(sector.value)
        self.event_bus.publish(PanoramaEvent.SECTOR_HIGHLIGHTED, sector)
    
    def clear_sector_highlight(self):
        """清除扇区高亮"""
        self.sector_handler.clear_highlight()
        self.event_bus.publish(PanoramaEvent.HIGHLIGHT_CLEARED)
    
    def handle_click(self, pos: QPointF):
        """
        处理点击事件
        
        Args:
            pos: 点击位置
        """
        sector_id = self.sector_handler.handle_click(pos)
        if sector_id:
            # 转换为枚举
            try:
                sector = SectorQuadrant(sector_id)
                self.sector_clicked.emit(sector)
                self.event_bus.publish(PanoramaEvent.SECTOR_CLICKED, sector)
            except ValueError:
                pass
    
    def enable_snake_path(self, enabled: bool):
        """
        启用/禁用蛇形路径
        
        Args:
            enabled: 是否启用
        """
        self.snake_path_renderer.set_enabled(enabled)
        
        if enabled:
            # 计算并渲染路径
            holes = list(self.data_model.get_holes().values())
            path = self.snake_path_renderer.calculate_path(holes, "hybrid")
            self.snake_path_renderer.render_path(path, self.scene, "simple_line")
            self.event_bus.publish(PanoramaEvent.SNAKE_PATH_ENABLED)
        else:
            self.event_bus.publish(PanoramaEvent.SNAKE_PATH_DISABLED)
    
    def apply_theme(self, theme_config: dict):
        """
        应用主题
        
        Args:
            theme_config: 主题配置
        """
        self.renderer.apply_theme(theme_config)
        self.event_bus.publish(PanoramaEvent.THEME_CHANGED, theme_config)
    
    # 事件处理方法
    def _on_data_loaded(self, event_data):
        """处理数据加载事件"""
        self._handle_data_loaded()
    
    def _on_data_cleared(self, event_data):
        """处理数据清空事件"""
        self.scene.clear()
        self.hole_items.clear()
    
    def _on_hole_status_changed(self, event_data):
        """处理孔位状态变更事件"""
        hole_id = event_data.data.get('hole_id')
        status = event_data.data.get('status')
        if hole_id and status:
            self.update_hole_status(hole_id, status)
    
    def _on_sector_clicked(self, event_data):
        """处理扇区点击事件"""
        sector = event_data.data
        if isinstance(sector, SectorQuadrant):
            self.highlight_sector(sector)
    
    def _on_render_requested(self, event_data):
        """处理渲染请求事件"""
        self._handle_data_loaded()
    
    def _on_theme_changed(self, event_data):
        """处理主题变更事件"""
        theme_config = event_data.data
        if theme_config:
            self.apply_theme(theme_config)