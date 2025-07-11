"""
自定义图形视图
高性能的管孔显示视图
"""

from PySide6.QtWidgets import (QGraphicsView, QGraphicsScene, QApplication,
                               QGraphicsItem, QWidget)
from PySide6.QtCore import Qt, QRectF, QTimer, Signal, QPointF
from PySide6.QtGui import QPainter, QWheelEvent, QMouseEvent, QTransform, QResizeEvent

from typing import List, Optional, Dict
import logging

from aidcis2.models.hole_data import HoleCollection, HoleData, HoleStatus
from aidcis2.graphics.hole_item import HoleGraphicsItem, HoleItemFactory
from aidcis2.graphics.navigation import NavigationMixin
from aidcis2.graphics.interaction import InteractionMixin
from aidcis2.graphics.view_overlay import ViewOverlayManager


class OptimizedGraphicsView(InteractionMixin, NavigationMixin, QGraphicsView):
    """优化的图形视图"""
    
    # 信号
    hole_clicked = Signal(HoleData)
    hole_hovered = Signal(HoleData)
    view_changed = Signal()
    view_mode_changed = Signal(str)  # 视图模式改变信号
    
    def __init__(self, parent=None):
        """初始化视图"""
        QGraphicsView.__init__(self, parent)
        NavigationMixin.__init__(self)
        InteractionMixin.__init__(self)

        self.logger = logging.getLogger(__name__)
        
        # 创建场景
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # 视图模式管理
        self.current_view_mode = "macro"  # macro(宏观) 或 micro(微观)
        
        # 性能优化设置
        self.setRenderHint(QPainter.Antialiasing, False)  # 禁用抗锯齿提升性能
        self.setRenderHint(QPainter.SmoothPixmapTransform, False)  # 禁用平滑变换
        self.setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)  # 最小更新模式
        self.setOptimizationFlag(QGraphicsView.DontSavePainterState, True)
        self.setOptimizationFlag(QGraphicsView.DontAdjustForAntialiasing, True)

        # 缓存模式 - 禁用缓存以提升大量对象的性能
        self.setCacheMode(QGraphicsView.CacheNone)
        
        # 拖拽模式 - 改为无拖拽模式，手动实现平移
        self.setDragMode(QGraphicsView.NoDrag)
        
        # 变换锚点
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
        # 数据存储
        self.hole_items: Dict[str, HoleGraphicsItem] = {}
        self.hole_collection: Optional[HoleCollection] = None

        # 选中的孔集合
        self.selected_holes: set = set()
        
        # 性能监控
        self.render_timer = QTimer()
        self.render_timer.timeout.connect(self._on_render_timer)
        self.render_timer.setSingleShot(True)
        
        # 当前悬停的项
        self.current_hover_item: Optional[HoleGraphicsItem] = None
        
        # 设置导航功能
        self.setup_navigation()

        # 设置交互功能
        self.setup_interaction()

        # 连接导航信号
        self.zoom_changed.connect(self._on_navigation_changed)
        self.pan_changed.connect(self._on_navigation_changed)

        # 连接交互信号
        self.hole_selected.connect(self._on_holes_selected)
        self.hole_hovered.connect(self._on_hole_hovered)

        # 启用鼠标跟踪
        self.setMouseTracking(True)
        
        # 创建视图叠加层管理器
        self.overlay_manager = ViewOverlayManager(self)
        
        # 连接叠加层信号
        if self.overlay_manager.micro_overlay:
            self.overlay_manager.micro_overlay.hole_selected.connect(self._on_overlay_hole_selected)
        if self.overlay_manager.macro_overlay:
            self.overlay_manager.macro_overlay.sector_selected.connect(self._on_overlay_sector_selected)
    
    def load_holes(self, hole_collection: HoleCollection):
        """
        加载管孔数据
        
        Args:
            hole_collection: 孔集合
        """
        try:
            self.logger.info(f"开始加载 {len(hole_collection)} 个管孔")
            
            # 清空现有数据
            self.clear_holes()
            
            # 保存数据引用
            self.hole_collection = hole_collection
            
            # 批量创建图形项
            items = HoleItemFactory.create_batch_items(hole_collection)

            # 禁用场景索引以提升批量添加性能
            self.scene.setItemIndexMethod(QGraphicsScene.NoIndex)

            # 批量添加到场景
            for item in items:
                self.scene.addItem(item)
                self.hole_items[item.hole_data.hole_id] = item

            # 重新启用场景索引
            self.scene.setItemIndexMethod(QGraphicsScene.BspTreeIndex)
            
            # 设置场景矩形
            bounds = hole_collection.get_bounds()
            margin = 100  # 添加边距
            scene_rect = QRectF(
                bounds[0] - margin, bounds[1] - margin,
                bounds[2] - bounds[0] + 2 * margin,
                bounds[3] - bounds[1] + 2 * margin
            )
            self.scene.setSceneRect(scene_rect)
            
            self.logger.info(f"管孔加载完成，场景大小: {scene_rect}")
            
            # 延迟执行默认适配到窗口宽度
            QTimer.singleShot(100, self.fit_to_window_width)
            
            # 更新叠加层统计
            QTimer.singleShot(200, self._update_overlay_statistics)
            
        except Exception as e:
            self.logger.error(f"加载管孔时出错: {e}")
            raise
    
    def clear_holes(self):
        """清空所有管孔"""
        self.scene.clear()
        self.hole_items.clear()
        self.current_hover_item = None
        self.hole_collection = None
    
    def fit_in_view(self):
        """适应视图显示所有内容"""
        self.fit_in_view_all()

    def fit_to_window_width(self):
        """适配到窗口宽度 - 默认显示模式"""
        if not self.hole_collection:
            return
            
        # 获取场景边界
        scene_rect = self.scene.sceneRect()
        view_rect = self.viewport().rect()
        
        if scene_rect.isEmpty() or view_rect.isEmpty():
            return
        
        # 防止除零错误
        if scene_rect.width() <= 0 or scene_rect.height() <= 0:
            self.logger.warning("场景尺寸无效，无法适配窗口宽度")
            return
            
        # 计算宽度适配的缩放比例
        width_scale = view_rect.width() / scene_rect.width()
        height_scale = view_rect.height() / scene_rect.height()
        
        # 使用较小的缩放比例以确保完全适配，但优先考虑宽度
        scale = min(width_scale, height_scale * 0.9)  # 留10%的高度边距
        
        # 防止无效缩放
        if scale <= 0:
            self.logger.warning("计算的缩放比例无效")
            return
        
        # 重置变换
        self.resetTransform()
        
        # 应用缩放
        self.scale(scale, scale)
        
        # 居中显示
        self.centerOn(scene_rect.center())
        
        self.logger.info(f"适配到窗口宽度完成，缩放比例: {scale:.3f}")

    def zoom_to_fit(self):
        """缩放到适合"""
        self.fit_to_window_width()

    def reset_view(self):
        """重置视图"""
        self.reset_zoom()
        self.fit_to_window_width()
    
    def get_hole_at_position(self, scene_pos: QPointF) -> Optional[HoleGraphicsItem]:
        """获取指定位置的孔"""
        items = self.scene.items(scene_pos)
        for item in items:
            if isinstance(item, HoleGraphicsItem):
                return item
        return None
    
    def update_hole_status(self, hole_id: str, status: HoleStatus):
        """更新孔状态"""
        if hole_id in self.hole_items:
            self.hole_items[hole_id].update_status(status)
            # 强制刷新图形项
            self.hole_items[hole_id].update()
            # 强制刷新视图
            self.viewport().update()
    
    def batch_update_status(self, status_updates: Dict[str, HoleStatus]):
        """批量更新状态"""
        HoleItemFactory.update_items_status(
            list(self.hole_items.values()), 
            status_updates
        )
        
        # 更新叠加层宏观统计
        self._update_overlay_statistics()
    
    def _update_overlay_statistics(self):
        """更新叠加层统计信息"""
        if not self.overlay_manager or not self.overlay_manager.macro_overlay:
            return
            
        # 计算统计数据
        total_holes = len(self.hole_items)
        if total_holes == 0:
            return
            
        status_counts = {}
        for item in self.hole_items.values():
            status = item.hole_data.status
            status_key = status.value if hasattr(status, 'value') else str(status)
            status_counts[status_key] = status_counts.get(status_key, 0) + 1
        
        completed = status_counts.get('qualified', 0) + status_counts.get('unqualified', 0)
        qualified = status_counts.get('qualified', 0)
        
        stats_data = {
            'total': total_holes,
            'completed': completed,
            'qualified': qualified,
            'not_detected': status_counts.get('not_detected', 0),
            'detecting': status_counts.get('detecting', 0),
            'unqualified': status_counts.get('unqualified', 0),
            'real_data': status_counts.get('real_data', 0)
        }
        
        self.overlay_manager.update_macro_statistics(stats_data)
    
    def highlight_holes(self, holes, search_highlight: bool = False):
        """高亮指定的孔位"""
        # 如果传入的是HoleData对象列表，转换为hole_id列表
        if holes and hasattr(holes[0], 'hole_id'):
            hole_ids = [hole.hole_id for hole in holes]
        else:
            hole_ids = holes

        # 如果是搜索高亮，先重置所有孔位的搜索高亮状态
        if search_highlight:
            for item_id, item in self.hole_items.items():
                if hasattr(item, 'set_search_highlighted'):
                    item.set_search_highlighted(False)

        # 高亮指定的孔位
        highlighted_count = 0
        for hole_id in hole_ids:
            if hole_id in self.hole_items:
                if search_highlight:
                    # 搜索高亮
                    if hasattr(self.hole_items[hole_id], 'set_search_highlighted'):
                        self.hole_items[hole_id].set_search_highlighted(True)
                        highlighted_count += 1
                else:
                    # 普通高亮
                    if hasattr(self.hole_items[hole_id], 'set_highlighted'):
                        self.hole_items[hole_id].set_highlighted(True)
                        highlighted_count += 1

        # 更新视图
        self.scene.update()

        highlight_type = "搜索高亮" if search_highlight else "高亮"
        self.logger.info(f"{highlight_type}显示了 {highlighted_count} 个孔位")

    def clear_search_highlight(self):
        """清除所有搜索高亮"""
        cleared_count = 0
        for item_id, item in self.hole_items.items():
            if hasattr(item, 'set_search_highlighted'):
                item.set_search_highlighted(False)
                cleared_count += 1

        # 更新视图
        self.scene.update()
        self.logger.info(f"清除了 {cleared_count} 个孔位的搜索高亮")

    def clear_all_highlights(self):
        """清除所有高亮（包括普通高亮和搜索高亮）"""
        cleared_count = 0
        for item_id, item in self.hole_items.items():
            if hasattr(item, 'set_highlighted'):
                item.set_highlighted(False)
                cleared_count += 1
            if hasattr(item, 'set_search_highlighted'):
                item.set_search_highlighted(False)

        # 更新视图
        self.scene.update()
        self.logger.info(f"清除了 {cleared_count} 个孔位的所有高亮")
    
    def select_holes(self, hole_ids: List[str]):
        """选择指定的孔"""
        # 使用InteractionMixin的方法
        self.select_holes_by_id(hole_ids)



    def get_visible_holes(self) -> List[HoleGraphicsItem]:
        """获取当前可见的孔"""
        visible_rect = self.mapToScene(self.viewport().rect()).boundingRect()
        visible_items = []
        
        for item in self.hole_items.values():
            if visible_rect.intersects(item.boundingRect()):
                visible_items.append(item)
        
        return visible_items
    
    # wheelEvent 现在由 NavigationMixin 处理
    
    # 鼠标事件现在由 InteractionMixin 处理
    
    def _on_render_timer(self):
        """渲染计时器回调"""
        # 可以在这里添加性能监控逻辑
        pass

    def _on_navigation_changed(self, *args):
        """导航改变处理"""
        self.view_changed.emit()

    def _on_holes_selected(self, holes: list):
        """孔被选择处理"""
        # 发射原有的hole_clicked信号以保持兼容性
        if holes:
            selected_hole = holes[0]
            self.hole_clicked.emit(selected_hole)  # 发射第一个选择的孔
            
            # 更新叠加层微观视图
            if self.overlay_manager and self.overlay_manager.micro_overlay:
                hole_data = {
                    'hole_id': selected_hole.hole_id,
                    'x': selected_hole.x,
                    'y': selected_hole.y,
                    'status': selected_hole.status.value if hasattr(selected_hole.status, 'value') else str(selected_hole.status)
                }
                self.overlay_manager.show_hole_detail(hole_data)

    def _on_hole_hovered(self, hole_data):
        """孔被悬停处理"""
        # 这里可以添加额外的悬停处理逻辑
        pass
    
    def _on_overlay_hole_selected(self, hole_id: str):
        """叠加层孔位选择处理"""
        if hole_id in self.hole_items:
            hole_item = self.hole_items[hole_id]
            self.hole_clicked.emit(hole_item.hole_data)
            self.centerOn(hole_item.pos())
    
    def _on_overlay_sector_selected(self, sector_id: str):
        """叠加层扇形区域选择处理"""
        # 这里可以添加扇形区域选择的处理逻辑
        pass





    def batch_update_status(self, status_updates: dict):
        """批量更新孔状态"""
        for hole_id, new_status in status_updates.items():
            self.update_hole_status(hole_id, new_status)
    
    def get_performance_info(self) -> Dict:
        """获取性能信息"""
        return {
            'total_items': len(self.hole_items),
            'visible_items': len(self.get_visible_holes()),
            'scene_rect': self.scene.sceneRect(),
            'view_rect': self.viewport().rect(),
            'transform': self.transform(),
            'scale': self.transform().m11()
        }

    def resizeEvent(self, event: QResizeEvent):
        """处理窗口大小变化事件"""
        super().resizeEvent(event)

        # 更新状态图例位置（如果存在）
        self._update_status_legend_position()
        
        # 窗口大小变化时，重新适配到窗口宽度
        if self.hole_collection:
            QTimer.singleShot(50, self.fit_to_window_width)

    def _update_status_legend_position(self):
        """更新状态图例位置到左上角"""
        # 如果有状态图例引用，直接更新位置
        if hasattr(self, 'status_legend') and self.status_legend:
            self.status_legend.move(10, 10)
            self.status_legend.raise_()  # 确保在最上层
        else:
            # 查找状态图例子组件
            for child in self.children():
                if 'StatusLegendWidget' in str(type(child)):
                    # 设置位置到左上角，留出一些边距
                    child.move(10, 10)
                    child.raise_()  # 确保在最上层
                    break
    
    def switch_to_macro_view(self):
        """切换到宏观区域视图
        
        宏观视图特点：
        - 显示整个管板的全貌
        - 突出区域分布和整体状态
        - 适合快速浏览和状态概览
        - 确保管板竖向摆放
        """
        if self.current_view_mode == "macro":
            return
            
        self.current_view_mode = "macro"
        self.logger.info("切换到宏观区域视图")
        
        # 更新显示模式
        self.update_view_display()
        
        # 确保管板竖向摆放
        self.ensure_vertical_orientation()
        
        # 适应视图显示全部内容，并留有适当边距
        self.fit_in_view_with_margin()
        
        # 设置适合宏观视图的缩放比例
        self.set_macro_view_scale()
        
        # 发射信号
        self.view_mode_changed.emit("macro")
        
    def switch_to_micro_view(self):
        """切换到微观管孔视图
        
        微观视图特点：
        - 显示管孔的详细信息
        - 突出单个或少量管孔的细节
        - 适合精确检查和操作
        - 保持管板竖向摆放
        """
        if self.current_view_mode == "micro":
            return
            
        self.current_view_mode = "micro"
        self.logger.info("切换到微观管孔视图")
        
        # 更新显示模式
        self.update_view_display()
        
        # 确保管板竖向摆放
        self.ensure_vertical_orientation()
        
        # 如果有选中的管孔，聚焦到选中区域
        if self.selected_holes:
            self.focus_on_selected_holes()
        else:
            # 否则放大到合适的微观视图比例
            self.set_micro_view_scale()
        
        # 发射信号
        self.view_mode_changed.emit("micro")
        
    def update_view_display(self):
        """根据当前视图模式更新显示"""
        if not self.hole_items:
            return
            
        if self.current_view_mode == "macro":
            # 宏观视图：突出整体分布和状态概览
            for hole_id, item in self.hole_items.items():
                item.setVisible(True)
                # 调整显示细节级别
                if hasattr(item, 'set_detail_level'):
                    item.set_detail_level("overview")
                # 调整孔位显示大小以适合宏观视图
                if hasattr(item, 'set_macro_display'):
                    item.set_macro_display(True)
                    
        elif self.current_view_mode == "micro":
            # 微观视图：显示详细的管孔信息
            for hole_id, item in self.hole_items.items():
                item.setVisible(True)
                # 显示全部详细信息
                if hasattr(item, 'set_detail_level'):
                    item.set_detail_level("detailed")
                # 调整孔位显示大小以适合微观视图
                if hasattr(item, 'set_macro_display'):
                    item.set_macro_display(False)
                    
        # 刷新视图
        self.scene.update()
        self.viewport().update()
        
    def ensure_vertical_orientation(self):
        """确保管板竖向摆放
        
        统一所有界面中管板二维图的摆放方向为竖向，满足甲方方向统一要求
        """
        if not self.hole_collection:
            return
            
        # 获取管板边界
        bounds = self.hole_collection.get_bounds()
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        center_x = (bounds[0] + bounds[2]) / 2
        center_y = (bounds[1] + bounds[3]) / 2
        
        # 防止无效尺寸
        if width <= 0 or height <= 0:
            self.logger.warning(f"管板尺寸无效: {width}x{height}")
            return
        
        self.logger.info(f"应用管板方向统一化: 尺寸({width:.1f}x{height:.1f}), 中心({center_x:.1f}, {center_y:.1f})")
        
        # 重置变换矩阵，确保统一的基准方向
        self.resetTransform()
        
        # 检查当前是否为横向摆放（宽度大于高度）
        if width > height:
            # 管板需要旋转90度变为竖向
            self.logger.info("检测到横向管板，应用竖向转换")
            
            # 应用90度旋转变换，使管板竖向显示
            transform = QTransform()
            transform.translate(center_x, center_y)
            transform.rotate(90)
            transform.translate(-center_x, -center_y)
            self.setTransform(transform)
        else:
            # 管板已是竖向，确保标准方向
            self.logger.info("管板已为竖向摆放，确保标准方向")
        
        # 居中显示
        self.centerOn(center_x, center_y)
        
        self.logger.info("✅ 管板方向统一化完成：确保竖向摆放")
    
    def set_macro_view_scale(self):
        """设置适合宏观视图的缩放比例"""
        # 适应整个管板显示，保持适当边距
        self.fit_in_view_with_margin(margin_factor=0.1)
        
        # 限制最大缩放比例，避免过度放大
        current_scale = self.transform().m11()
        max_scale = 2.0
        if current_scale > max_scale:
            self.scale(max_scale / current_scale, max_scale / current_scale)
        
        self.logger.info(f"宏观视图缩放设置完成，当前缩放比例: {self.transform().m11():.3f}")
            
    def fit_in_view_with_margin(self, margin_ratio=0.1):
        """适应视图并留有边距"""
        if not self.hole_collection:
            return
            
        # 获取场景边界
        scene_rect = self.scene.sceneRect()
        
        # 防止无效场景尺寸
        if scene_rect.isEmpty() or scene_rect.width() <= 0 or scene_rect.height() <= 0:
            self.logger.warning("场景尺寸无效，无法适应视图")
            return
        
        # 添加边距
        margin_x = scene_rect.width() * margin_ratio
        margin_y = scene_rect.height() * margin_ratio
        
        view_rect = QRectF(
            scene_rect.x() - margin_x,
            scene_rect.y() - margin_y,
            scene_rect.width() + 2 * margin_x,
            scene_rect.height() + 2 * margin_y
        )
        
        self.fitInView(view_rect, Qt.KeepAspectRatio)
        
    def set_macro_view_scale(self):
        """设置宏观视图的适当缩放比例"""
        # 确保整个管板可见，但不要太小
        current_scale = self.transform().m11()
        
        # 宏观视图的最小缩放比例
        min_macro_scale = 0.3
        max_macro_scale = 1.0
        
        if current_scale < min_macro_scale:
            scale_factor = min_macro_scale / current_scale
            self.scale(scale_factor, scale_factor)
        elif current_scale > max_macro_scale:
            scale_factor = max_macro_scale / current_scale
            self.scale(scale_factor, scale_factor)
            
    def set_micro_view_scale(self):
        """设置微观视图的适当缩放比例"""
        # 微观视图需要更大的缩放比例以显示细节
        current_scale = self.transform().m11()
        
        # 微观视图的缩放范围
        min_micro_scale = 1.2
        max_micro_scale = 4.0
        
        if current_scale < min_micro_scale:
            scale_factor = min_micro_scale / current_scale
            self.scale(scale_factor, scale_factor)
        elif current_scale > max_micro_scale:
            scale_factor = max_micro_scale / current_scale
            self.scale(scale_factor, scale_factor)
            
    def focus_on_selected_holes(self):
        """聚焦到选中的管孔区域"""
        if not self.selected_holes or not self.hole_items:
            return
            
        # 计算选中孔位的边界
        selected_items = [self.hole_items[hole_id] for hole_id in self.selected_holes 
                         if hole_id in self.hole_items]
        
        if not selected_items:
            return
            
        # 计算边界矩形
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        for item in selected_items:
            item_rect = item.boundingRect()
            pos = item.pos()
            
            min_x = min(min_x, pos.x() + item_rect.left())
            min_y = min(min_y, pos.y() + item_rect.top())
            max_x = max(max_x, pos.x() + item_rect.right())
            max_y = max(max_y, pos.y() + item_rect.bottom())
        
        # 添加边距
        margin = 50
        focus_rect = QRectF(
            min_x - margin, min_y - margin,
            max_x - min_x + 2 * margin,
            max_y - min_y + 2 * margin
        )
        
        # 聚焦到该区域
        self.fitInView(focus_rect, Qt.KeepAspectRatio)
        
        # 确保缩放比例适合微观视图
        self.set_micro_view_scale()
        
    def get_current_view_mode(self):
        """获取当前视图模式"""
        return self.current_view_mode


