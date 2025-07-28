"""
极简统一接口 - 直接利用现有的 UnifiedZoomController
避免重复代码，真正减少系统复杂度
"""

from typing import Dict, List, Optional
import sys
import os

# 导入现有的缩放控制器
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from unified_zoom_control import UnifiedZoomController

from src.core_business.models.hole_data import HoleStatus


class SimpleUnifiedInterface:
    """极简统一接口 - 仅整合必要功能"""
    
    def __init__(self):
        # 注册的视图和缩放控制器
        self.views: Dict[str, any] = {}
        self.zoom_controllers: Dict[str, UnifiedZoomController] = {}
    
    def register_view(self, view_id: str, view):
        """注册视图"""
        self.views[view_id] = view
        
        # 如果视图有图形功能，自动创建缩放控制器
        if hasattr(view, 'hole_items') or hasattr(view, 'graphics_view'):
            graphics_view = getattr(view, 'graphics_view', view)
            self.zoom_controllers[view_id] = UnifiedZoomController(graphics_view)
    
    def unregister_view(self, view_id: str):
        """注销视图"""
        self.views.pop(view_id, None)
        self.zoom_controllers.pop(view_id, None)
    
    # ============================================================================
    # 孔位状态管理 - 直接调用视图方法
    # ============================================================================
    
    def update_hole_status(self, hole_id: str, status: HoleStatus, 
                          target_views: Optional[List[str]] = None):
        """更新孔位状态"""
        views_to_update = target_views or list(self.views.keys())
        
        for view_id in views_to_update:
            if view_id in self.views:
                view = self.views[view_id]
                if hasattr(view, 'update_hole_status'):
                    view.update_hole_status(hole_id, status)
    
    def highlight_holes(self, hole_ids: List[str], 
                       target_views: Optional[List[str]] = None):
        """高亮孔位"""
        views_to_update = target_views or list(self.views.keys())
        
        for view_id in views_to_update:
            if view_id in self.views:
                view = self.views[view_id]
                if hasattr(view, 'highlight_holes'):
                    view.highlight_holes(hole_ids)
    
    # ============================================================================
    # 缩放管理 - 直接使用现有 UnifiedZoomController
    # ============================================================================
    
    def fit_to_items(self, view_id: str, item_ids: Optional[List[str]] = None, delay: bool = True):
        """缩放到指定项目 - 使用现有控制器的核心功能"""
        if view_id in self.zoom_controllers:
            self.zoom_controllers[view_id].fit_to_items(item_ids, delay)
    
    def zoom_in(self, view_id: str, factor: float = 1.2):
        """放大"""
        if view_id in self.views:
            view = self.views[view_id]
            graphics_view = getattr(view, 'graphics_view', view)
            if hasattr(graphics_view, 'scale'):
                graphics_view.scale(factor, factor)
    
    def zoom_out(self, view_id: str, factor: float = 0.8):
        """缩小"""
        if view_id in self.views:
            view = self.views[view_id]
            graphics_view = getattr(view, 'graphics_view', view)
            if hasattr(graphics_view, 'scale'):
                graphics_view.scale(factor, factor)
    
    def reset_zoom(self, view_id: str):
        """重置缩放"""
        if view_id in self.views:
            view = self.views[view_id]
            graphics_view = getattr(view, 'graphics_view', view)
            if hasattr(graphics_view, 'resetTransform'):
                graphics_view.resetTransform()


# 全局单例
_simple_interface = None

def get_simple_unified_interface() -> SimpleUnifiedInterface:
    """获取极简统一接口"""
    global _simple_interface
    if _simple_interface is None:
        _simple_interface = SimpleUnifiedInterface()
    return _simple_interface