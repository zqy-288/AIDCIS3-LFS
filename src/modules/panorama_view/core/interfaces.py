"""
全景图组件接口定义
定义所有全景图相关组件的抽象接口
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from PySide6.QtCore import QPointF
from src.shared.models.hole_data import HoleData, HoleStatus


class IPanoramaDataModel(ABC):
    """全景图数据模型接口"""
    
    @abstractmethod
    def get_holes(self) -> Dict[str, HoleData]:
        """获取所有孔位数据"""
        pass
    
    @abstractmethod
    def get_hole(self, hole_id: str) -> Optional[HoleData]:
        """获取指定孔位"""
        pass
    
    @abstractmethod
    def update_hole_status(self, hole_id: str, status: HoleStatus) -> bool:
        """更新孔位状态"""
        pass
    
    @abstractmethod
    def load_hole_collection(self, hole_collection) -> None:
        """加载孔位集合"""
        pass


class IPanoramaGeometryCalculator(ABC):
    """几何计算接口"""
    
    @abstractmethod
    def calculate_center(self, holes: Dict[str, HoleData]) -> QPointF:
        """计算中心点"""
        pass
    
    @abstractmethod
    def calculate_radius(self, holes: Dict[str, HoleData], center: QPointF) -> float:
        """计算半径"""
        pass
    
    @abstractmethod
    def calculate_hole_display_size(self, hole_count: int, radius: float, density: float) -> float:
        """计算孔位显示大小"""
        pass
    
    @abstractmethod
    def get_scale_factor(self, data_scale: str) -> float:
        """获取缩放因子"""
        pass


class IPanoramaStatusManager(ABC):
    """状态管理接口"""
    
    @abstractmethod
    def queue_status_update(self, hole_id: str, status: HoleStatus) -> None:
        """队列化状态更新"""
        pass
    
    @abstractmethod
    def flush_updates(self) -> int:
        """刷新所有待处理更新，返回更新数量"""
        pass
    
    @abstractmethod
    def set_batch_interval(self, interval_ms: int) -> None:
        """设置批量更新间隔"""
        pass


class IPanoramaRenderer(ABC):
    """渲染器接口"""
    
    @abstractmethod
    def render_holes(self, holes: Dict[str, HoleData], scene, hole_size: float) -> Dict[str, any]:
        """渲染孔位，返回孔位图形项字典"""
        pass
    
    @abstractmethod
    def render_sector_dividers(self, center: QPointF, radius: float, scene) -> None:
        """渲染扇区分隔线"""
        pass
    
    @abstractmethod
    def apply_theme(self, theme_config: dict) -> None:
        """应用主题配置"""
        pass


class ISectorInteractionHandler(ABC):
    """扇区交互处理器接口"""
    
    @abstractmethod
    def handle_click(self, pos: QPointF) -> Optional[str]:
        """处理点击事件，返回扇区标识"""
        pass
    
    @abstractmethod
    def highlight_sector(self, sector: str) -> None:
        """高亮扇区"""
        pass
    
    @abstractmethod
    def clear_highlight(self) -> None:
        """清除高亮"""
        pass


class ISnakePathRenderer(ABC):
    """蛇形路径渲染器接口"""
    
    @abstractmethod
    def calculate_path(self, holes: List[HoleData], strategy: str) -> List[Tuple[float, float]]:
        """计算蛇形路径"""
        pass
    
    @abstractmethod
    def render_path(self, path: List[Tuple[float, float]], scene, style: str) -> None:
        """渲染路径"""
        pass
    
    @abstractmethod
    def set_enabled(self, enabled: bool) -> None:
        """设置是否启用"""
        pass