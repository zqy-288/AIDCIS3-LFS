"""
场景管理器
管理图形场景的渲染和性能优化
"""

from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtCore import QObject, QTimer, Signal, QRectF
from PySide6.QtGui import QColor, QPainter

from typing import Dict, List, Optional
import logging
import time

from src.shared.models.hole_data import HoleCollection, HoleStatus
from src.graphics.hole_item import HoleGraphicsItem


class SceneManager(QObject):
    """场景管理器"""
    
    # 信号
    rendering_started = Signal()
    rendering_finished = Signal(float)  # 渲染时间
    performance_warning = Signal(str)   # 性能警告
    
    def __init__(self, scene: QGraphicsScene, parent=None):
        """
        初始化场景管理器
        
        Args:
            scene: 图形场景
            parent: 父对象
        """
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        self.scene = scene
        
        # 性能监控
        self.render_start_time = 0
        self.frame_count = 0
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self._update_fps)
        self.fps_timer.start(1000)  # 每秒更新一次
        
        # LOD (Level of Detail) 设置
        self.lod_enabled = True
        self.lod_thresholds = {
            'high': 1.0,    # 高细节阈值
            'medium': 0.5,  # 中等细节阈值
            'low': 0.1      # 低细节阈值
        }
        
        # 视口裁剪
        self.viewport_culling = True
        self.culling_margin = 100  # 裁剪边距
        
        # 批量渲染
        self.batch_size = 1000  # 批量处理大小
        self.render_timer = QTimer()
        self.render_timer.timeout.connect(self._process_render_batch)
        self.render_timer.setSingleShot(True)
        
        # 待渲染队列
        self.pending_items: List[HoleGraphicsItem] = []
        
        # 性能统计
        self.performance_stats = {
            'total_items': 0,
            'visible_items': 0,
            'render_time': 0,
            'fps': 0,
            'memory_usage': 0
        }
    
    def add_holes_batch(self, hole_items: List[HoleGraphicsItem]):
        """
        批量添加孔到场景
        
        Args:
            hole_items: 孔图形项列表
        """
        self.logger.info(f"开始批量添加 {len(hole_items)} 个孔到场景")
        self.rendering_started.emit()
        
        start_time = time.time()
        
        # 分批处理
        for i in range(0, len(hole_items), self.batch_size):
            batch = hole_items[i:i + self.batch_size]
            self.pending_items.extend(batch)
        
        # 开始处理
        self._process_render_batch()
        
        end_time = time.time()
        render_time = end_time - start_time
        
        self.performance_stats['total_items'] = len(hole_items)
        self.performance_stats['render_time'] = render_time
        
        self.logger.info(f"批量添加完成，耗时: {render_time:.2f} 秒")
        self.rendering_finished.emit(render_time)
    
    def _process_render_batch(self):
        """处理渲染批次"""
        if not self.pending_items:
            return
        
        # 处理一个批次
        batch_size = min(self.batch_size, len(self.pending_items))
        batch = self.pending_items[:batch_size]
        self.pending_items = self.pending_items[batch_size:]
        
        # 添加到场景
        for item in batch:
            self.scene.addItem(item)
        
        # 如果还有待处理项，继续处理
        if self.pending_items:
            self.render_timer.start(10)  # 10ms后处理下一批
    
    def optimize_for_scale(self, scale_factor: float):
        """
        根据缩放级别优化渲染
        
        Args:
            scale_factor: 缩放因子
        """
        if not self.lod_enabled:
            return
        
        # 确定细节级别
        if scale_factor >= self.lod_thresholds['high']:
            detail_level = 'high'
        elif scale_factor >= self.lod_thresholds['medium']:
            detail_level = 'medium'
        else:
            detail_level = 'low'
        
        # 应用LOD设置
        self._apply_lod_settings(detail_level)
    
    def _apply_lod_settings(self, detail_level: str):
        """
        应用LOD设置
        
        Args:
            detail_level: 细节级别 ('high', 'medium', 'low')
        """
        items = self.scene.items()
        
        for item in items:
            if isinstance(item, HoleGraphicsItem):
                if detail_level == 'low':
                    # 低细节：简化渲染
                    item.setFlag(item.ItemIgnoresTransformations, True)
                elif detail_level == 'medium':
                    # 中等细节：部分优化
                    item.setFlag(item.ItemIgnoresTransformations, False)
                else:
                    # 高细节：完整渲染
                    item.setFlag(item.ItemIgnoresTransformations, False)
    
    def update_viewport_culling(self, visible_rect: QRectF):
        """
        更新视口裁剪
        
        Args:
            visible_rect: 可见矩形
        """
        if not self.viewport_culling:
            return
        
        # 扩展可见区域
        culling_rect = visible_rect.adjusted(
            -self.culling_margin, -self.culling_margin,
            self.culling_margin, self.culling_margin
        )
        
        visible_count = 0
        total_count = 0
        
        # 遍历所有项目
        for item in self.scene.items():
            if isinstance(item, HoleGraphicsItem):
                total_count += 1
                
                # 检查是否在可见区域内
                if culling_rect.intersects(item.boundingRect()):
                    item.setVisible(True)
                    visible_count += 1
                else:
                    item.setVisible(False)
        
        # 更新统计
        self.performance_stats['visible_items'] = visible_count
        self.performance_stats['total_items'] = total_count
        
        # 性能警告
        if visible_count > 5000:
            self.performance_warning.emit(
                f"可见项目过多: {visible_count}, 可能影响性能"
            )
    
    def update_hole_status_batch(self, status_updates: Dict[str, HoleStatus]):
        """
        批量更新孔状态
        
        Args:
            status_updates: 状态更新字典 {hole_id: new_status}
        """
        updated_count = 0
        
        for item in self.scene.items():
            if isinstance(item, HoleGraphicsItem):
                hole_id = item.hole_data.hole_id
                if hole_id in status_updates:
                    item.update_status(status_updates[hole_id])
                    updated_count += 1
        
        self.logger.info(f"批量更新了 {updated_count} 个孔的状态")
    
    def get_items_in_region(self, region_rect: QRectF) -> List[HoleGraphicsItem]:
        """
        获取指定区域内的孔项目
        
        Args:
            region_rect: 区域矩形
            
        Returns:
            List[HoleGraphicsItem]: 区域内的孔项目列表
        """
        items = self.scene.items(region_rect)
        hole_items = []
        
        for item in items:
            if isinstance(item, HoleGraphicsItem):
                hole_items.append(item)
        
        return hole_items
    
    def clear_scene(self):
        """清空场景"""
        self.scene.clear()
        self.pending_items.clear()
        self.performance_stats = {
            'total_items': 0,
            'visible_items': 0,
            'render_time': 0,
            'fps': 0,
            'memory_usage': 0
        }
    
    def _update_fps(self):
        """更新FPS统计"""
        self.performance_stats['fps'] = self.frame_count
        self.frame_count = 0
    
    def on_frame_rendered(self):
        """帧渲染完成回调"""
        self.frame_count += 1
    
    def get_performance_stats(self) -> Dict:
        """获取性能统计"""
        return self.performance_stats.copy()
    
    def set_lod_enabled(self, enabled: bool):
        """设置LOD启用状态"""
        self.lod_enabled = enabled
    
    def set_viewport_culling_enabled(self, enabled: bool):
        """设置视口裁剪启用状态"""
        self.viewport_culling = enabled
    
    def set_batch_size(self, size: int):
        """设置批量处理大小"""
        self.batch_size = max(100, min(size, 5000))  # 限制在合理范围内
