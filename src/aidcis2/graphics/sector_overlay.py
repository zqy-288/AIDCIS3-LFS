"""
扇形覆盖层 - 始终固定在视图中心的扇形显示
"""

from typing import Optional
from PySide6.QtWidgets import QWidget, QGraphicsView
from PySide6.QtCore import Qt, QPointF, QRectF, Signal
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPainterPath, QResizeEvent

from aidcis2.graphics.sector_manager import SectorQuadrant


class SectorOverlayWidget(QWidget):
    """扇形覆盖层组件 - 始终显示在父视图的中心"""
    
    sector_clicked = Signal(SectorQuadrant)
    
    def __init__(self, parent_view: QGraphicsView):
        super().__init__(parent_view)
        self.parent_view = parent_view
        self.current_highlighted_sector: Optional[SectorQuadrant] = None
        
        # 设置为透明背景
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")
        
        # 调整到父视图的大小
        self.resize(parent_view.size())
        
        # 监听父视图的大小变化
        parent_view.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """事件过滤器，监听父视图的大小变化"""
        if obj == self.parent_view and event.type() == QResizeEvent:
            self.resize(self.parent_view.size())
            self.update()
        return super().eventFilter(obj, event)
    
    def paintEvent(self, event):
        """绘制扇形覆盖层"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # 获取视图中心
        center = QPointF(self.width() / 2, self.height() / 2)
        
        # 计算半径
        radius = min(self.width(), self.height()) * 0.35
        
        # 绘制四个扇形
        for i, sector in enumerate(SectorQuadrant):
            # 计算角度
            start_angle = i * 90 * 16  # QPainter使用1/16度作为单位
            span_angle = 90 * 16
            
            # 设置颜色
            if sector == self.current_highlighted_sector:
                color = QColor(255, 193, 7, 100)  # 高亮黄色
            else:
                color = QColor(200, 200, 200, 30)  # 淡灰色
            
            # 绘制扇形
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(100, 100, 100, 100), 1))
            
            # 创建扇形路径
            path = QPainterPath()
            path.moveTo(center)
            rect = QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2)
            path.arcTo(rect, start_angle / 16, span_angle / 16)
            path.lineTo(center)
            
            painter.drawPath(path)
        
        # 绘制中心点
        painter.setBrush(QBrush(QColor(255, 0, 0)))
        painter.setPen(QPen(QColor(255, 0, 0), 2))
        painter.drawEllipse(center, 3, 3)
    
    def mousePressEvent(self, event):
        """处理鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            # 计算点击的扇形
            center = QPointF(self.width() / 2, self.height() / 2)
            dx = event.pos().x() - center.x()
            dy = event.pos().y() - center.y()
            
            import math
            angle = math.degrees(math.atan2(dy, dx))
            if angle < 0:
                angle += 360
            
            # 确定扇形
            if 0 <= angle < 90:
                sector = SectorQuadrant.SECTOR_1
            elif 90 <= angle < 180:
                sector = SectorQuadrant.SECTOR_2
            elif 180 <= angle < 270:
                sector = SectorQuadrant.SECTOR_3
            else:
                sector = SectorQuadrant.SECTOR_4
            
            self.sector_clicked.emit(sector)
            self.highlight_sector(sector)
    
    def highlight_sector(self, sector: Optional[SectorQuadrant]):
        """高亮指定的扇形"""
        self.current_highlighted_sector = sector
        self.update()
    
    def show_overlay(self):
        """显示覆盖层"""
        self.show()
        self.raise_()
    
    def hide_overlay(self):
        """隐藏覆盖层"""
        self.hide()