"""
全景图模块
提供高内聚低耦合的全景图组件实现

使用方式:
    from .core import PanoramaDIContainer
    
    container = PanoramaDIContainer()
    panorama_widget = container.create_panorama_widget()
"""

# 主要组件导入
from .components.panorama_widget import PanoramaWidget
from .core.di_container import PanoramaDIContainer, get_global_container, reset_global_container

# 事件系统
from .core.event_bus import PanoramaEventBus, PanoramaEvent, EventData

# 数据层组件
from .components.data_model import PanoramaDataModel
from .components.geometry_calculator import PanoramaGeometryCalculator
from .components.status_manager import PanoramaStatusManager

# 渲染层组件
from .components.renderer import PanoramaRenderer
from .components.sector_handler import SectorInteractionHandler
from .components.snake_path_renderer import SnakePathRenderer

# 控制器
from .components.view_controller import PanoramaViewController

# 向后兼容适配器
from .adapters.legacy_adapter import CompletePanoramaWidgetAdapter, CompletePanoramaWidget, create_legacy_panorama_widget

# 接口定义
from .core.interfaces import (
    IPanoramaDataModel,
    IPanoramaGeometryCalculator,
    IPanoramaStatusManager,
    IPanoramaRenderer,
    ISectorInteractionHandler,
    ISnakePathRenderer
)

# 公开API
__all__ = [
    # === 主要使用的组件 ===
    'PanoramaWidget',           # 全景图UI组件
    'PanoramaDIContainer',      # 依赖注入容器
    
    # === 容器管理 ===
    'get_global_container',     # 获取全局容器
    'reset_global_container',   # 重置全局容器
    
    # === 事件系统 ===
    'PanoramaEventBus',         # 事件总线
    'PanoramaEvent',            # 事件类型枚举
    'EventData',                # 事件数据包装器
    
    # === 核心组件（高级用法） ===
    'PanoramaDataModel',        # 数据模型
    'PanoramaGeometryCalculator', # 几何计算器
    'PanoramaStatusManager',    # 状态管理器
    'PanoramaRenderer',         # 渲染器
    'SectorInteractionHandler', # 扇区交互处理器
    'SnakePathRenderer',        # 蛇形路径渲染器
    'PanoramaViewController',   # 视图控制器
    
    # === 向后兼容（迁移期间使用） ===
    'CompletePanoramaWidget',      # 旧接口适配器
    'CompletePanoramaWidgetAdapter', # 适配器类
    'create_legacy_panorama_widget', # 工厂函数
    
    # === 接口定义（扩展用） ===
    'IPanoramaDataModel',
    'IPanoramaGeometryCalculator', 
    'IPanoramaStatusManager',
    'IPanoramaRenderer',
    'ISectorInteractionHandler',
    'ISnakePathRenderer',
]

# 版本信息
__version__ = '1.0.0'
__author__ = 'AIDCIS3-LFS Team'