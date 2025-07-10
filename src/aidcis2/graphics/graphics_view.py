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
            
            # 适应视图
            self.fit_in_view()
            
            self.logger.info(f"管孔加载完成，场景大小: {scene_rect}")
            
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

    def zoom_to_fit(self):
        """缩放到适合"""
        self.fit_in_view_all()

    def reset_view(self):
        """重置视图"""
        self.reset_zoom()
        self.fit_in_view_all()
    
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
            self.hole_clicked.emit(holes[0])  # 发射第一个选择的孔

    def _on_hole_hovered(self, hole_data):
        """孔被悬停处理"""
        # 这里可以添加额外的悬停处理逻辑
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
        """切换到宏观区域视图"""
        if self.current_view_mode == "macro":
            return
            
        self.current_view_mode = "macro"
        self.update_view_display()
        
        # 适应视图显示全部内容
        self.fit_in_view_all()
        
        # 发射信号
        self.view_mode_changed.emit("macro")
        self.logger.info("切换到宏观区域视图")
        
    def switch_to_micro_view(self):
        """切换到微观管孔视图"""
        if self.current_view_mode == "micro":
            return
            
        self.current_view_mode = "micro"
        self.update_view_display()
        
        # 放大到详细视图
        self.scale(1.5, 1.5)
        
        # 发射信号
        self.view_mode_changed.emit("micro")
        self.logger.info("切换到微观管孔视图")
        
    def update_view_display(self):
        """根据当前视图模式更新显示"""
        if not self.hole_items:
            return
            
        if self.current_view_mode == "macro":
            # 宏观视图：显示整体区域分布，适当调整显示密度
            for hole_id, item in self.hole_items.items():
                item.setVisible(True)
                # 可以考虑在宏观视图中隐藏一些细节信息
                if hasattr(item, 'set_detail_level'):
                    item.set_detail_level("low")
                    
        elif self.current_view_mode == "micro":
            # 微观视图：显示详细的管孔信息
            for hole_id, item in self.hole_items.items():
                item.setVisible(True)
                # 显示详细信息
                if hasattr(item, 'set_detail_level'):
                    item.set_detail_level("high")
                    
        # 刷新视图
        self.scene.update()
        self.viewport().update()
        
    def get_current_view_mode(self):
        """获取当前视图模式"""
        return self.current_view_mode


