"""
全景图依赖注入容器
管理组件的创建和依赖关系
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QGraphicsScene
from .event_bus import PanoramaEventBus

if TYPE_CHECKING:
    from ..components.data_model import PanoramaDataModel
    from ..components.status_manager import PanoramaStatusManager


class PanoramaDIContainer:
    """
    全景图依赖注入容器
    负责创建和管理所有全景图相关组件
    """
    
    def __init__(self):
        """初始化容器，创建单例组件"""
        # 延迟导入以避免循环依赖
        from ..components.data_model import PanoramaDataModel
        from ..components.geometry_calculator import PanoramaGeometryCalculator
        from ..components.status_manager import PanoramaStatusManager
        
        # 创建事件总线（单例）
        self.event_bus = PanoramaEventBus()
        
        # 创建数据模型（单例）
        self.data_model = PanoramaDataModel()
        
        # 创建几何计算器（单例）
        self.geometry_calculator = PanoramaGeometryCalculator()
        
        # 创建状态管理器（单例）
        self.status_manager = PanoramaStatusManager(self.data_model)
        
        # 渲染器和处理器将在创建widget时创建
        self._renderer = None
        self._sector_handler = None
        self._snake_path_renderer = None
    
    def create_panorama_widget(self, parent=None):
        """
        创建全景图组件
        
        Args:
            parent: 父组件
            
        Returns:
            完整配置的全景图组件
        """
        # 延迟导入以避免循环依赖
        from ..components.renderer import PanoramaRenderer
        from ..components.sector_handler import SectorInteractionHandler
        from ..components.snake_path_renderer import SnakePathRenderer
        from ..components.view_controller import PanoramaViewController
        from ..components.panorama_widget import PanoramaWidget
        
        # 创建场景
        scene = QGraphicsScene()
        
        # 创建渲染器（每个widget独立）
        renderer = PanoramaRenderer()
        
        # 创建扇区交互处理器
        sector_handler = SectorInteractionHandler()
        
        # 创建蛇形路径渲染器
        snake_path_renderer = SnakePathRenderer()
        
        # 创建视图控制器
        controller = PanoramaViewController(
            data_model=self.data_model,
            geometry_calculator=self.geometry_calculator,
            status_manager=self.status_manager,
            renderer=renderer,
            sector_handler=sector_handler,
            snake_path_renderer=snake_path_renderer,
            event_bus=self.event_bus,
            scene=scene
        )
        
        # 创建UI组件
        widget = PanoramaWidget(controller, parent)
        
        return widget
    
    def get_event_bus(self) -> PanoramaEventBus:
        """获取事件总线"""
        return self.event_bus
    
    def get_data_model(self) -> 'PanoramaDataModel':
        """获取数据模型"""
        return self.data_model
    
    def get_status_manager(self) -> 'PanoramaStatusManager':
        """获取状态管理器"""
        return self.status_manager
    
    def reset(self):
        """重置容器，清理所有数据"""
        # 清理数据模型
        self.data_model.clear_data()
        
        # 清理待处理的状态更新
        self.status_manager.clear_pending_updates()
        
        # 清理事件订阅
        self.event_bus.clear_subscribers()


# 全局容器实例（可选）
_global_container = None

def get_global_container() -> PanoramaDIContainer:
    """
    获取全局容器实例
    使用单例模式确保全局只有一个容器
    """
    global _global_container
    if _global_container is None:
        _global_container = PanoramaDIContainer()
    return _global_container

def reset_global_container():
    """重置全局容器"""
    global _global_container
    if _global_container:
        _global_container.reset()
    _global_container = None