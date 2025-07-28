#!/usr/bin/env python3
"""
统一的缩放控制方案
"""

from typing import Optional, List
from PySide6.QtCore import QRectF, QTimer, Qt
from PySide6.QtWidgets import QGraphicsView

class UnifiedZoomController:
    """统一的缩放控制器"""
    
    def __init__(self, graphics_view: QGraphicsView):
        self.graphics_view = graphics_view
        self.zoom_delay_ms = 50  # 统一的延迟时间
        self.margin_factor = 1.1  # 统一的边距系数
        self.max_auto_scale = 1.5  # 最大自动缩放比例
        
    def fit_to_items(self, item_ids: Optional[List[str]] = None, delay: bool = True):
        """
        统一的缩放函数
        
        Args:
            item_ids: 要显示的项目ID列表，None表示显示所有
            delay: 是否延迟执行
        """
        if delay:
            QTimer.singleShot(self.zoom_delay_ms, 
                            lambda: self._do_fit_to_items(item_ids))
        else:
            self._do_fit_to_items(item_ids)
    
    def _do_fit_to_items(self, item_ids: Optional[List[str]] = None):
        """执行实际的缩放"""
        # 获取要显示的边界
        bounds = self._calculate_bounds(item_ids)
        if not bounds:
            return
            
        # 添加边距
        expanded_bounds = self._expand_bounds(bounds, self.margin_factor)
        
        # 检查缩放限制
        if self._check_scale_limit(expanded_bounds):
            # 执行缩放
            self.graphics_view.fitInView(expanded_bounds, Qt.KeepAspectRatio)
    
    def _calculate_bounds(self, item_ids: Optional[List[str]] = None) -> Optional[QRectF]:
        """计算项目边界"""
        if not hasattr(self.graphics_view, 'hole_items'):
            return None
            
        # 确定要计算的项目
        if item_ids is None:
            # 计算所有可见项
            items = [item for item in self.graphics_view.hole_items.values() 
                    if item.isVisible()]
        else:
            # 计算指定项目
            items = [self.graphics_view.hole_items.get(item_id) 
                    for item_id in item_ids 
                    if item_id in self.graphics_view.hole_items]
            items = [item for item in items if item]  # 过滤None
        
        if not items:
            return None
            
        # 计算边界
        bounds = items[0].sceneBoundingRect()
        for item in items[1:]:
            bounds = bounds.united(item.sceneBoundingRect())
            
        return bounds
    
    def _expand_bounds(self, bounds: QRectF, factor: float) -> QRectF:
        """扩展边界"""
        margin_x = bounds.width() * (factor - 1) / 2
        margin_y = bounds.height() * (factor - 1) / 2
        
        return QRectF(
            bounds.x() - margin_x,
            bounds.y() - margin_y,
            bounds.width() * factor,
            bounds.height() * factor
        )
    
    def _check_scale_limit(self, bounds: QRectF) -> bool:
        """检查缩放是否会超过限制"""
        view_rect = self.graphics_view.viewport().rect()
        
        # 计算需要的缩放比例
        scale_x = view_rect.width() / bounds.width()
        scale_y = view_rect.height() / bounds.height()
        required_scale = min(scale_x, scale_y)
        
        # 检查是否超过最大缩放
        return required_scale <= self.max_auto_scale


# 修改后的 DynamicSectorDisplayRefactored 使用示例
class ImprovedDynamicSectorDisplay:
    """改进的动态扇形显示（示例）"""
    
    def __init__(self):
        # ... 其他初始化代码 ...
        
        # 创建统一的缩放控制器
        self.zoom_controller = UnifiedZoomController(self.graphics_view)
        
        # 禁用graphics_view的自动缩放
        self.graphics_view.disable_auto_fit = True
        
    def _process_hole_collection(self, hole_collection):
        """处理孔位集合 - 不执行缩放"""
        # 加载数据
        self.graphics_view.load_holes(hole_collection)
        
        # 分发数据...
        
        # 隐藏所有孔位
        if hasattr(self.graphics_view, 'hole_items'):
            for hole_item in self.graphics_view.hole_items.values():
                hole_item.setVisible(False)
        
        # 切换到第一个扇形（会触发缩放）
        QTimer.singleShot(200, lambda: self.switch_to_sector(SectorQuadrant.SECTOR_1))
    
    def switch_to_sector(self, sector):
        """切换扇形 - 使用统一缩放"""
        # ... 设置可见性代码 ...
        
        # 获取当前扇形的孔位ID
        sector_hole_ids = self.sector_distributor.get_sector_data(sector).hole_ids
        
        # 使用统一的缩放控制
        self.zoom_controller.fit_to_items(list(sector_hole_ids))
        
        # ... 其他代码 ...


# 更简单的方案：直接修改现有代码
def create_unified_zoom_method():
    """
    为 DynamicSectorDisplayRefactored 创建统一的缩放方法
    """
    code = '''
    def _unified_zoom_to_items(self, item_ids: Optional[List[str]] = None, delay_ms: int = 50):
        """
        统一的缩放方法
        
        Args:
            item_ids: 要缩放到的项目ID列表，None表示所有可见项
            delay_ms: 延迟执行的毫秒数
        """
        def do_zoom():
            # 计算边界
            if item_ids is None:
                # 使用可见项
                bounds = self._calculate_visible_bounds()
            else:
                # 使用指定项
                bounds = self._calculate_items_bounds(item_ids)
                
            if bounds:
                # 添加10%边距
                margin_factor = 1.1
                expanded_bounds = QRectF(
                    bounds.x() - bounds.width() * (margin_factor - 1) / 2,
                    bounds.y() - bounds.height() * (margin_factor - 1) / 2,
                    bounds.width() * margin_factor,
                    bounds.height() * margin_factor
                )
                
                # 执行缩放
                self.graphics_view.fitInView(expanded_bounds, Qt.KeepAspectRatio)
        
        if delay_ms > 0:
            QTimer.singleShot(delay_ms, do_zoom)
        else:
            do_zoom()
    
    def _calculate_items_bounds(self, item_ids: List[str]) -> Optional[QRectF]:
        """计算指定项目的边界"""
        if not hasattr(self.graphics_view, 'hole_items'):
            return None
            
        items = []
        for item_id in item_ids:
            if item_id in self.graphics_view.hole_items:
                items.append(self.graphics_view.hole_items[item_id])
                
        if not items:
            return None
            
        bounds = items[0].sceneBoundingRect()
        for item in items[1:]:
            bounds = bounds.united(item.sceneBoundingRect())
            
        return bounds
    '''
    return code


print("""
统一缩放控制方案的优势：

1. **避免重复缩放**
   - 数据加载时不缩放
   - 只在切换扇形时执行一次缩放

2. **参数统一管理**
   - 延迟时间：50ms
   - 边距系数：1.1
   - 最大缩放：1.5

3. **使用方式**
   - 加载数据：不调用缩放
   - 切换扇形：self._unified_zoom_to_items(sector_hole_ids)
   - 显示全部：self._unified_zoom_to_items(None)

4. **性能优化**
   - 减少了一次不必要的缩放计算
   - 统一的延迟避免频繁更新
""")