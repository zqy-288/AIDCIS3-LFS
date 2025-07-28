"""
扇形显示配置管理
集中管理所有配置项，避免硬编码
"""

from dataclasses import dataclass
from typing import Dict
from PySide6.QtGui import QColor


@dataclass
class DisplayColors:
    """显示颜色配置"""
    background = QColor(240, 240, 240)
    hole_default = QColor(100, 100, 255)
    hole_hover = QColor(255, 150, 150)
    hole_selected = QColor(255, 100, 100)
    sector_highlight = QColor(255, 200, 100, 80)
    grid_line = QColor(200, 200, 200)


@dataclass
class ViewportConfig:
    """视口配置"""
    min_scale: float = 0.1
    max_scale: float = 2.0
    default_scale_factor: float = 0.9
    auto_scale_limit: float = 1.5
    view_margin: int = 40
    responsive_scale_enabled: bool = True


@dataclass
class PanoramaConfig:
    """全景图配置"""
    widget_width: int = 300
    widget_height: int = 300
    position_x: int = 20
    position_y: int = 20
    opacity: float = 0.95
    min_hole_display_radius: float = 2.0


@dataclass
class AnimationConfig:
    """动画配置"""
    sector_switch_duration: int = 300  # ms
    fade_duration: int = 200
    smooth_scroll_enabled: bool = True


class SectorDisplayConfig:
    """扇形显示配置管理器"""
    
    def __init__(self):
        self.colors = DisplayColors()
        self.viewport = ViewportConfig()
        self.panorama = PanoramaConfig()
        self.animation = AnimationConfig()
        
        # 扇形名称映射
        self.sector_names: Dict[int, str] = {
            1: "第一象限",
            2: "第二象限", 
            3: "第三象限",
            4: "第四象限"
        }
        
        # 调试模式
        self.debug_mode = False
        
    def get_sector_name(self, sector_id: int) -> str:
        """获取扇形显示名称"""
        return self.sector_names.get(sector_id, f"扇形{sector_id}")
    
    def enable_debug(self):
        """启用调试模式"""
        self.debug_mode = True
        
    def disable_debug(self):
        """禁用调试模式"""
        self.debug_mode = False