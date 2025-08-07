"""
扇形视图工厂类
负责创建和配置扇形视图，统一视图创建逻辑
"""

from typing import List, Optional, Tuple
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPen, QBrush, QColor
from PySide6.QtWidgets import QGraphicsScene, QGraphicsEllipseItem

from src.pages.main_detection_p1.graphics.core.graphics_view import OptimizedGraphicsView
from src.pages.main_detection_p1.graphics.core.hole_item import HoleGraphicsItem
from src.shared.models.hole_data import HoleData
from src.pages.main_detection_p1.graphics.core.sector_types import SectorQuadrant
from src.pages.main_detection_p1.graphics.core.sector_controllers import UnifiedLogger


class SectorViewConfig:
    """扇形视图配置"""
    # 缩放配置
    MAX_AUTO_SCALE = 1.5
    MIN_SCALE = 0.1
    MAX_SCALE = 2.0
    DEFAULT_SCALE_FACTOR = 0.9  # 留10%边距
    
    # 孔位显示配置
    MIN_HOLE_RADIUS = 1.0
    DEFAULT_HOLE_COLOR = QColor(100, 100, 255)
    HOVER_HOLE_COLOR = QColor(255, 150, 150)
    
    # 视图边距
    VIEW_MARGIN = 40


class SectorViewFactory:
    """扇形视图工厂"""
    
    def __init__(self):
        self.logger = UnifiedLogger("SectorViewFactory")
        self.config = SectorViewConfig()
    
    def create_sector_view(self, sector: SectorQuadrant, holes: List[HoleData]) -> OptimizedGraphicsView:
        """
        创建扇形视图
        
        Args:
            sector: 扇形象限
            holes: 该扇形的孔位数据
            
        Returns:
            配置好的图形视图
        """
        self.logger.info(f"创建扇形视图: {sector.name}, 孔位数: {len(holes)}")
        
        # 创建视图和场景
        view = OptimizedGraphicsView()
        scene = QGraphicsScene()
        view.setScene(scene)
        
        # 配置视图
        view.max_auto_scale = self.config.MAX_AUTO_SCALE
        view.setHorizontalScrollBarPolicy(1)  # Qt.ScrollBarAlwaysOff
        view.setVerticalScrollBarPolicy(1)
        
        # 添加孔位到场景
        self._add_holes_to_scene(scene, holes)
        
        # 设置场景边界
        if holes:
            self._set_scene_rect(scene, holes)
        
        return view
    
    def _add_holes_to_scene(self, scene: QGraphicsScene, holes: List[HoleData]) -> None:
        """添加孔位到场景"""
        for hole in holes:
            hole_item = self._create_hole_item(hole)
            scene.addItem(hole_item)
    
    def _create_hole_item(self, hole: HoleData) -> HoleGraphicsItem:
        """创建孔位图形项"""
        # 创建孔位项
        hole_item = HoleGraphicsItem(
            hole_data=hole,
            x=hole.x,
            y=hole.y,
            radius=max(hole.radius, self.config.MIN_HOLE_RADIUS)
        )
        
        # 设置样式
        hole_item.setPen(QPen(self.config.DEFAULT_HOLE_COLOR, 1))
        hole_item.setBrush(QBrush(self.config.DEFAULT_HOLE_COLOR.lighter(150)))
        
        # 设置工具提示
        tooltip = f"孔位ID: {hole.hole_id}\n位置: ({hole.x:.1f}, {hole.y:.1f})"
        hole_item.setToolTip(tooltip)
        
        return hole_item
    
    def _set_scene_rect(self, scene: QGraphicsScene, holes: List[HoleData]) -> None:
        """设置场景边界"""
        if not holes:
            return
            
        # 计算边界
        min_x = min(h.x - h.radius for h in holes)
        max_x = max(h.x + h.radius for h in holes)
        min_y = min(h.y - h.radius for h in holes)
        max_y = max(h.y + h.radius for h in holes)
        
        # 添加边距
        margin = self.config.VIEW_MARGIN
        scene_rect = QRectF(
            min_x - margin,
            min_y - margin,
            max_x - min_x + 2 * margin,
            max_y - min_y + 2 * margin
        )
        
        scene.setSceneRect(scene_rect)
        self.logger.info(f"场景边界设置: {scene_rect}")
    
    def apply_optimal_scale(self, view: OptimizedGraphicsView, viewport_size: Tuple[int, int]) -> float:
        """
        应用最优缩放
        
        Args:
            view: 图形视图
            viewport_size: 视口大小 (width, height)
            
        Returns:
            应用的缩放比例
        """
        scene = view.scene()
        if not scene:
            return 1.0
            
        scene_rect = scene.itemsBoundingRect()
        if scene_rect.isEmpty():
            return 1.0
            
        # 计算缩放比例
        width_scale = viewport_size[0] / scene_rect.width()
        height_scale = viewport_size[1] / scene_rect.height()
        
        # 使用较小的缩放比例，确保完全适配
        scale = min(width_scale, height_scale) * self.config.DEFAULT_SCALE_FACTOR
        
        # 限制缩放范围
        scale = max(self.config.MIN_SCALE, min(self.config.MAX_SCALE, scale))
        
        # 应用缩放
        view.resetTransform()
        view.scale(scale, scale)
        view.centerOn(scene_rect.center())
        
        self.logger.info(f"应用缩放: {scale:.3f}")
        return scale