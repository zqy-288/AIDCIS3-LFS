"""
扇形显示控制器模块
将DynamicSectorDisplayWidget拆分为多个专职控制器
"""

import logging
from typing import Dict, List, Optional, Any
from enum import Enum
from PySide6.QtCore import QObject, Signal, QTimer, QPointF
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout
from PySide6.QtGui import QTransform

from src.shared.models.hole_data import HoleData, HoleCollection
from src.pages.main_detection_p1.graphics.core.sector_types import SectorQuadrant


class UnifiedLogger:
    """统一日志系统"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # 如果还没有处理器，添加控制台处理器
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def info(self, message: str, prefix: str = ""):
        """信息日志"""
        self.logger.info(f"{prefix} {message}".strip())
    
    def warning(self, message: str, prefix: str = "⚠️"):
        """警告日志"""
        self.logger.warning(f"{prefix} {message}".strip())
    
    def error(self, message: str, prefix: str = "❌"):
        """错误日志"""
        self.logger.error(f"{prefix} {message}".strip())
    
    def debug(self, message: str, prefix: str = "🔍"):
        """调试日志"""
        self.logger.debug(f"{prefix} {message}".strip())


class SectorViewController(QObject):
    """扇形切换控制器"""
    
    sector_changed = Signal(SectorQuadrant)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = UnifiedLogger("SectorViewController")
        self.current_sector = SectorQuadrant.SECTOR_1
        self.external_sector_manager = None
        self.graphics_view = None
        
    def set_sector_manager(self, sector_manager):
        """设置扇形管理器"""
        self.external_sector_manager = sector_manager
        self.logger.info("扇形管理器已设置")
    
    def set_graphics_view(self, graphics_view):
        """设置图形视图"""
        self.graphics_view = graphics_view
        self.logger.info("图形视图已设置")
    
    def switch_to_sector(self, sector: SectorQuadrant):
        """切换到指定扇形区域"""
        if not self.external_sector_manager:
            self.logger.error("没有外部扇形管理器，必须通过SharedDataManager处理数据")
            return
            
        if not self.graphics_view:
            self.logger.error("没有设置图形视图")
            return
        
        self.logger.info(f"切换到扇形: {sector.value}")
        self.current_sector = sector
        
        # 获取扇形孔位数据
        sector_holes = self.external_sector_manager.get_sector_holes(sector)
        if not sector_holes:
            self.logger.warning(f"扇形 {sector.value} 没有孔位数据")
            return
            
        # 显示/隐藏孔位
        sector_hole_ids = set(hole.hole_id for hole in sector_holes)
        total_shown = 0
        total_hidden = 0
        
        for hole_id, hole_item in self.graphics_view.hole_items.items():
            if hole_id in sector_hole_ids:
                hole_item.setVisible(True)
                total_shown += 1
            else:
                hole_item.setVisible(False)
                total_hidden += 1
        
        self.logger.info(f"扇形切换完成: 显示 {total_shown} 个孔位, 隐藏 {total_hidden} 个孔位")
        self.sector_changed.emit(sector)


class UnifiedPanoramaController(QObject):
    """统一全景图控制器"""
    
    sector_clicked = Signal(SectorQuadrant)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = UnifiedLogger("UnifiedPanoramaController")
        self.hole_collection: Optional[HoleCollection] = None
        self.panorama_view = None
        self.panorama_scene = None
        self.hole_items: Dict[str, Any] = {}
        self.sector_highlights: Dict[SectorQuadrant, Any] = {}
        
        # 浮动全景图支持
        self.floating_panorama_widget = None
        self.mini_panorama_items: Dict[str, Any] = {}
        
        # 批量更新机制
        self.pending_status_updates: Dict[str, Any] = {}
        self.batch_update_timer = QTimer()
        self.batch_update_timer.timeout.connect(self._apply_batch_updates)
        self.batch_update_timer.setSingleShot(True)
        self.batch_update_interval = 200  # 200ms
    
    def set_panorama_view(self, view, scene):
        """设置全景图视图和场景"""
        self.panorama_view = view
        self.panorama_scene = scene
        self.logger.info("全景图视图已设置")
    
    def load_hole_collection(self, hole_collection: HoleCollection):
        """加载孔位集合到全景图"""
        self.hole_collection = hole_collection
        self.logger.info(f"加载孔位集合: {len(hole_collection.holes)} 个孔位")
        
        if not self.panorama_scene:
            self.logger.error("全景图场景未设置")
            return
            
        self._create_hole_items()
        self._create_sector_highlights()
        self._setup_panorama_transform()
    
    def _create_hole_items(self):
        """创建孔位图形项"""
        self.hole_items.clear()
        if not self.hole_collection or not self.panorama_scene:
            return
            
        from PySide6.QtWidgets import QGraphicsEllipseItem
        from PySide6.QtGui import QPen, QBrush, QColor
        from PySide6.QtCore import Qt
        
        for hole_id, hole in self.hole_collection.holes.items():
            # 创建圆形孔位项
            hole_item = QGraphicsEllipseItem(
                hole.center_x - hole.radius,
                hole.center_y - hole.radius,
                hole.radius * 2,
                hole.radius * 2
            )
            
            # 设置样式
            pen = QPen(QColor(100, 100, 100), 0.5)
            brush = QBrush(QColor(200, 200, 200, 100))
            hole_item.setPen(pen)
            hole_item.setBrush(brush)
            
            self.hole_items[hole_id] = hole_item
            self.panorama_scene.addItem(hole_item)
        
        self.logger.info(f"创建了 {len(self.hole_items)} 个孔位图形项")
    
    def _create_sector_highlights(self):
        """创建扇形高亮"""
        # 这里可以创建扇形高亮覆盖层
        pass
    
    def _setup_panorama_transform(self):
        """设置全景图变换"""
        if not self.hole_collection or not self.panorama_view:
            return
            
        # 计算适合的缩放和居中
        bounds = self.hole_collection.get_bounds()
        margin = 50
        
        from PySide6.QtCore import QRectF
        scene_rect = QRectF(
            bounds[0] - margin, bounds[1] - margin,
            bounds[2] - bounds[0] + 2 * margin,
            bounds[3] - bounds[1] + 2 * margin
        )
        
        self.panorama_scene.setSceneRect(scene_rect)
        self.panorama_view.fitInView(scene_rect, 1)  # Qt.KeepAspectRatio = 1
        
        self.logger.info("全景图变换设置完成")
    
    def update_hole_status(self, hole_id: str, status: Any):
        """更新孔位状态（批量处理）"""
        self.pending_status_updates[hole_id] = status
        self.batch_update_timer.start(self.batch_update_interval)
    
    def _apply_batch_updates(self):
        """应用批量状态更新"""
        if not self.pending_status_updates:
            return
            
        updated_count = 0
        for hole_id, status in self.pending_status_updates.items():
            if hole_id in self.hole_items:
                self._apply_single_status_update(hole_id, status)
                updated_count += 1
        
        self.logger.info(f"批量更新完成: {updated_count} 个孔位")
        self.pending_status_updates.clear()
    
    def _apply_single_status_update(self, hole_id: str, status: Any):
        """应用单个状态更新"""
        hole_item = self.hole_items.get(hole_id)
        if not hole_item:
            return
            
        # 根据状态设置颜色
        from PySide6.QtGui import QBrush, QColor
        color_map = {
            'qualified': QColor(76, 175, 80),    # 绿色
            'defective': QColor(244, 67, 54),    # 红色  
            'pending': QColor(200, 200, 200),    # 灰色
        }
        
        status_name = getattr(status, 'value', str(status))
        color = color_map.get(status_name, QColor(200, 200, 200))
        hole_item.setBrush(QBrush(color))
    
    def highlight_sector(self, sector: SectorQuadrant):
        """高亮指定扇形"""
        self.logger.info(f"高亮扇形: {sector.value}")
        # 实现扇形高亮逻辑
    
    def detect_clicked_sector(self, scene_pos: QPointF) -> Optional[SectorQuadrant]:
        """检测点击的扇形区域"""
        if not self.hole_collection:
            return None
            
        # 计算几何中心
        bounds = self.hole_collection.get_bounds()
        center_x = (bounds[0] + bounds[2]) / 2
        center_y = (bounds[1] + bounds[3]) / 2
        
        # 计算相对位置
        dx = scene_pos.x() - center_x
        dy = scene_pos.y() - center_y
        
        # 根据象限确定扇形
        if dx >= 0 and dy < 0:
            return SectorQuadrant.SECTOR_1  # 右上
        elif dx < 0 and dy < 0:
            return SectorQuadrant.SECTOR_2  # 左上
        elif dx < 0 and dy >= 0:
            return SectorQuadrant.SECTOR_3  # 左下
        else:
            return SectorQuadrant.SECTOR_4  # 右下
    
    def create_floating_panorama(self, parent_widget) -> QWidget:
        """创建浮动全景图窗口"""
        from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
        from PySide6.QtCore import Qt
        
        # 创建浮动容器
        floating_container = QWidget(parent_widget)
        floating_container.setFixedSize(220, 240)
        floating_container.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.85);
                border: none;
                border-radius: 8px;
            }
        """)
        
        floating_container.setWindowFlags(Qt.Widget)
        floating_container.setAttribute(Qt.WA_TranslucentBackground, False)
        floating_container.raise_()
        
        # 布局
        layout = QVBoxLayout(floating_container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)
        
        # 标题
        title_label = QLabel("全局预览视图")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #D3D8E0;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
                border: none;
                padding: 3px;
            }
        """)
        layout.addWidget(title_label)
        
        # 创建迷你全景图组件
        from src.pages.main_detection_p1.components.graphics.complete_panorama_widget import CompletePanoramaWidget
        mini_panorama = CompletePanoramaWidget()
        mini_panorama.setFixedSize(200, 150)
        
        # 连接信号
        mini_panorama.sector_clicked.connect(self.sector_clicked.emit)
        
        layout.addWidget(mini_panorama)
        self.floating_panorama_widget = mini_panorama
        
        # 定位
        floating_container.move(10, 10)
        floating_container.show()
        
        self.logger.info("浮动全景图创建完成")
        return floating_container
    
    def update_floating_panorama_status(self, hole_id: str, status: Any):
        """更新浮动全景图中的孔位状态"""
        if not self.floating_panorama_widget:
            self.logger.warning("浮动全景图组件不存在")
            return
            
        # 通过CompletePanoramaWidget更新状态
        if hasattr(self.floating_panorama_widget, 'update_hole_status'):
            self.floating_panorama_widget.update_hole_status(hole_id, status)
            self.logger.info(f"更新浮动全景图孔位状态: {hole_id} -> {status}")
    
    def setup_floating_panorama_data(self, hole_collection: HoleCollection):
        """为浮动全景图加载数据"""
        if not self.floating_panorama_widget:
            self.logger.warning("浮动全景图组件不存在")
            return
            
        # 通过CompletePanoramaWidget加载数据
        if hasattr(self.floating_panorama_widget, 'load_complete_view'):
            self.floating_panorama_widget.load_complete_view(hole_collection)
            self.logger.info(f"浮动全景图数据加载完成: {len(hole_collection)} 个孔位")


class StatusController(QObject):
    """状态控制器"""
    
    status_filter_changed = Signal(str, bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = UnifiedLogger("StatusController")
        self.status_buttons: Dict[str, QPushButton] = {}
        self.active_filters: Dict[str, bool] = {}
    
    def create_status_buttons(self, parent_widget) -> QWidget:
        """创建状态控制按钮"""
        button_widget = QWidget()
        layout = QHBoxLayout(button_widget)
        
        status_types = [
            ('pending', '待检'),
            ('qualified', '合格'),
            ('defective', '异常'),
            ('all', '全部')
        ]
        
        for status_key, status_text in status_types:
            button = QPushButton(status_text)
            button.setCheckable(True)
            if status_key == 'all':
                button.setChecked(True)
                
            button.clicked.connect(
                lambda checked, key=status_key: self._on_status_button_clicked(key, checked)
            )
            
            self.status_buttons[status_key] = button
            layout.addWidget(button)
        
        self.logger.info("状态控制按钮创建完成")
        return button_widget
    
    def _on_status_button_clicked(self, status_key: str, checked: bool):
        """状态按钮点击处理"""
        self.active_filters[status_key] = checked
        self.logger.info(f"状态过滤器 {status_key}: {'开启' if checked else '关闭'}")
        self.status_filter_changed.emit(status_key, checked)


class ViewTransformController(QObject):
    """视图变换控制器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = UnifiedLogger("ViewTransformController")
        self.graphics_view = None
        self.current_transform = QTransform()
    
    def set_graphics_view(self, graphics_view):
        """设置图形视图"""
        self.graphics_view = graphics_view
        self.logger.info("图形视图已设置")
    
    def apply_fill_view_strategy(self):
        """应用填充视图策略"""
        if not self.graphics_view:
            self.logger.warning("图形视图未设置")
            return
            
        # 获取可见项的边界
        visible_items = [item for item in self.graphics_view.scene().items() 
                        if item.isVisible()]
        
        if not visible_items:
            self.logger.warning("没有可见的图形项")
            return
            
        # 计算边界并适应视图
        scene_rect = self.graphics_view.scene().itemsBoundingRect()
        self.graphics_view.fitInView(scene_rect, 1)  # Qt.KeepAspectRatio = 1
        
        self.logger.info("填充视图策略应用完成")
    
    def apply_responsive_scaling(self, scale: float):
        """应用响应式缩放"""
        if not self.graphics_view:
            return
            
        transform = QTransform()
        transform.scale(scale, scale)
        self.graphics_view.setTransform(transform)
        self.current_transform = transform
        
        self.logger.info(f"响应式缩放应用完成: {scale}")
    
    def reset_transform(self):
        """重置变换"""
        if self.graphics_view:
            self.graphics_view.resetTransform()
            self.current_transform = QTransform()
            self.logger.info("视图变换已重置")