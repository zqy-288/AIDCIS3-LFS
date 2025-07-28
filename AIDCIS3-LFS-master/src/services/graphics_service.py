"""
图形服务层
封装所有图形相关的组件创建和管理
"""

from typing import Optional, Any, Dict
from PySide6.QtWidgets import QWidget


class GraphicsService:
    """
    图形服务
    管理所有图形视图组件的创建和配置
    """
    
    # 类级别的单例缓存
    _instance = None
    _graphics_view_cache = {}
    _sector_view_cache = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        # 延迟初始化的组件引用
        self._graphics_view = None
        self._panorama_widget = None
        self._sector_view = None
        self._snake_path_coordinator = None
        self._unified_adapter = None
        
    def create_graphics_view(self, parent: Optional[QWidget] = None) -> Any:
        """创建优化的图形视图"""
        from src.core_business.graphics.graphics_view import OptimizedGraphicsView
        return OptimizedGraphicsView(parent)
        
    def create_panorama_widget(self, parent: Optional[QWidget] = None) -> Any:
        """创建全景图组件"""
        from src.core_business.graphics.panorama import CompletePanoramaWidget
        return CompletePanoramaWidget(parent)
        
    def create_sector_view(self, parent: Optional[QWidget] = None, quadrant: Any = None) -> Any:
        """创建扇形区域视图（使用缓存避免重复创建）"""
        cache_key = f"{id(parent)}_{quadrant}"
        
        if cache_key in self._sector_view_cache:
            return self._sector_view_cache[cache_key]
            
        try:
            # 直接创建简单的占位组件，避免复杂的DynamicSectorDisplayWidget
            from PySide6.QtWidgets import QLabel
            label = QLabel(f"扇形视图占位{len(self._sector_view_cache)+1}", parent)
            label.setStyleSheet("border: 1px solid gray; padding: 10px; background-color: #e0e0e0;")
            label.setFixedSize(150, 150)
            
            self._sector_view_cache[cache_key] = label
            return label
        except Exception:
            # 最简单的回退
            from PySide6.QtWidgets import QLabel
            label = QLabel("扇形视图", parent)
            label.setFixedSize(150, 150)
            return label
        
    def create_snake_path_coordinator(self) -> Any:
        """创建蛇形路径协调器（单例）"""
        if self._snake_path_coordinator is None:
            from src.core_business.graphics.snake_path_coordinator import SnakePathCoordinator
            self._snake_path_coordinator = SnakePathCoordinator()
        return self._snake_path_coordinator
        
    def get_unified_adapter(self) -> Any:
        """获取统一的扇形适配器（单例）"""
        if self._unified_adapter is None:
            # 通过共享数据管理器获取，确保是同一个实例
            from src.core.shared_data_manager import SharedDataManager
            shared_manager = SharedDataManager()
            self._unified_adapter = shared_manager.unified_adapter
        return self._unified_adapter
        
    def create_path_renderer(self, strategy: str = "zigzag", style: str = "default") -> Any:
        """
        创建路径渲染器
        
        Args:
            strategy: 路径策略
            style: 渲染样式
            
        Returns:
            配置好的路径渲染器
        """
        from src.core_business.graphics.snake_path_renderer import PathStrategy, PathRenderStyle
        
        # 映射字符串到枚举
        strategy_map = {
            "zigzag": PathStrategy.ZIGZAG,
            "spiral": PathStrategy.SPIRAL,
            "optimal": PathStrategy.OPTIMAL
        }
        
        style_map = {
            "default": PathRenderStyle.DEFAULT,
            "highlighted": PathRenderStyle.HIGHLIGHTED,
            "animated": PathRenderStyle.ANIMATED
        }
        
        return {
            "strategy": strategy_map.get(strategy, PathStrategy.ZIGZAG),
            "style": style_map.get(style, PathRenderStyle.DEFAULT)
        }
        
    def configure_coordinate_system(self, config: Dict[str, Any]) -> Any:
        """配置坐标系统"""
        from src.core_business.coordinate_system import CoordinateConfig
        
        coord_config = CoordinateConfig()
        for key, value in config.items():
            if hasattr(coord_config, key):
                setattr(coord_config, key, value)
                
        return coord_config
        
    def get_sector_quadrants(self) -> Dict[str, Any]:
        """获取所有扇形象限定义"""
        from src.core_business.graphics.dynamic_sector_view import SectorQuadrant
        
        return {
            "SECTOR_1": SectorQuadrant.SECTOR_1,
            "SECTOR_2": SectorQuadrant.SECTOR_2,
            "SECTOR_3": SectorQuadrant.SECTOR_3,
            "SECTOR_4": SectorQuadrant.SECTOR_4
        }
        
    def cleanup(self):
        """清理图形资源"""
        # 清理缓存的组件
        self._graphics_view = None
        self._panorama_widget = None
        self._sector_view = None
        self._snake_path_coordinator = None
        self._unified_adapter = None
        

# 全局图形服务实例
_global_graphics_service = None


def get_graphics_service() -> GraphicsService:
    """获取全局图形服务实例"""
    global _global_graphics_service
    if _global_graphics_service is None:
        _global_graphics_service = GraphicsService()
    return _global_graphics_service