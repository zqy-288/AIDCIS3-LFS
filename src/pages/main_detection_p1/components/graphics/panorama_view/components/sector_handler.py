"""
扇区交互处理器实现
负责扇区点击检测和高亮管理
"""

import math
from typing import Optional, Dict
from PySide6.QtCore import QPointF, QObject, QTimer
from PySide6.QtWidgets import QGraphicsScene

from ..core.interfaces import ISectorInteractionHandler
from src.core_business.graphics.sector_types import SectorQuadrant
# 延迟导入避免循环依赖


class SectorInteractionHandler(QObject):
    """扇区交互处理器实现"""
    
    def __init__(self):
        super().__init__()
        
        # 几何信息
        self.center: Optional[QPointF] = None
        self.radius: float = 0.0
        
        # 高亮管理
        self.sector_highlights: Dict[str, any] = {}  # 使用any避免循环导入
        self.current_highlighted_sector: Optional[str] = None
        self.scene: Optional[QGraphicsScene] = None
        
        # 高亮定时器（防抖）
        self.highlight_timer = QTimer()
        self.highlight_timer.timeout.connect(self._execute_highlight)
        self.highlight_timer.setSingleShot(True)
        self.highlight_delay = 50  # 50ms延迟
        
        # 待处理的高亮操作
        self.pending_highlight_sector: Optional[str] = None
    
    def set_geometry(self, center: QPointF, radius: float, scene: QGraphicsScene = None):
        """
        设置几何信息
        
        Args:
            center: 中心点
            radius: 半径
            scene: 图形场景
        """
        self.center = center
        self.radius = radius
        if scene:
            self.scene = scene
            self._create_sector_highlights()
    
    def handle_click(self, pos: QPointF) -> Optional[str]:
        """
        处理点击事件
        
        Args:
            pos: 点击位置
            
        Returns:
            被点击的扇区标识，如果没有点击在扇区内则返回None
        """
        if not self.center or self.radius <= 0:
            return None
        
        # 计算点击位置相对于中心的向量
        dx = pos.x() - self.center.x()
        dy = pos.y() - self.center.y()
        
        # 检查是否在圆形区域内
        distance = math.sqrt(dx * dx + dy * dy)
        if distance > self.radius:
            return None
        
        # 计算角度（从正X轴开始，逆时针为正）
        angle = math.atan2(-dy, dx)  # 注意Y轴翻转
        
        # 转换为0-360度
        angle_degrees = math.degrees(angle)
        if angle_degrees < 0:
            angle_degrees += 360
        
        # 确定扇区
        sector = self._angle_to_sector(angle_degrees)
        return sector
    
    def _angle_to_sector(self, angle_degrees: float) -> str:
        """
        将角度转换为扇区
        
        Args:
            angle_degrees: 角度（0-360度）
            
        Returns:
            扇区标识
        """
        # 扇区划分：
        # 第一象限: 315-45度（右上）
        # 第二象限: 45-135度（左上）
        # 第三象限: 135-225度（左下）
        # 第四象限: 225-315度（右下）
        
        if (angle_degrees >= 315 and angle_degrees < 360) or (angle_degrees >= 0 and angle_degrees < 45):
            return SectorQuadrant.SECTOR_1.value
        elif angle_degrees >= 45 and angle_degrees < 135:
            return SectorQuadrant.SECTOR_2.value
        elif angle_degrees >= 135 and angle_degrees < 225:
            return SectorQuadrant.SECTOR_3.value
        else:  # 225-315度
            return SectorQuadrant.SECTOR_4.value
    
    def highlight_sector(self, sector: str) -> None:
        """
        高亮扇区（使用防抖）
        
        Args:
            sector: 扇区标识
        """
        self.pending_highlight_sector = sector
        
        # 启动防抖定时器
        if not self.highlight_timer.isActive():
            self.highlight_timer.start(self.highlight_delay)
    
    def clear_highlight(self) -> None:
        """清除高亮"""
        self.pending_highlight_sector = None
        self.highlight_timer.stop()
        self._clear_all_highlights()
    
    def _execute_highlight(self):
        """执行高亮操作"""
        if not self.pending_highlight_sector:
            return
        
        # 清除旧高亮
        self._clear_all_highlights()
        
        # 设置新高亮
        sector = self.pending_highlight_sector
        if sector in self.sector_highlights:
            highlight_item = self.sector_highlights[sector]
            highlight_item.highlight(True)
            self.current_highlighted_sector = sector
        
        self.pending_highlight_sector = None
    
    def _clear_all_highlights(self):
        """清除所有高亮"""
        for highlight_item in self.sector_highlights.values():
            highlight_item.highlight(False)
        self.current_highlighted_sector = None
    
    def _create_sector_highlights(self):
        """创建扇区高亮项"""
        if self.center is None or self.radius <= 0 or self.scene is None:
            return
        
        # 清除旧的高亮项
        for highlight in self.sector_highlights.values():
            if highlight.scene():
                self.scene.removeItem(highlight)
        self.sector_highlights.clear()
        
        # 创建新的高亮项
        for sector in SectorQuadrant:
            try:
                # 动态导入避免循环依赖
                from src.pages.main_detection_p1.components.graphics.sector_highlight_item import SectorHighlightItem
                highlight = SectorHighlightItem(
                    sector=sector,
                    center=self.center,
                    radius=self.radius
                )
                self.scene.addItem(highlight)
                self.sector_highlights[sector.value] = highlight
            except Exception as e:
                print(f"创建扇区 {sector.value} 高亮失败: {e}")
    
    def get_current_highlighted_sector(self) -> Optional[str]:
        """获取当前高亮的扇区"""
        return self.current_highlighted_sector