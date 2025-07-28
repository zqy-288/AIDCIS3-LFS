"""
动态扇形概览视图组件
支持根据扇形数量动态调整显示
"""

import math
from typing import List, Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGridLayout, QGroupBox
from PySide6.QtCore import Qt, Signal, QRectF, QPointF, QTimer
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath

from .dynamic_sector_manager import DynamicSectorManager, DynamicSectorQuadrant, DynamicSectorProgress


class DynamicSectorOverviewWidget(QWidget):
    """动态扇形概览可视化组件"""
    
    # 信号
    sector_selected = Signal(object)  # DynamicSectorQuadrant
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sector_manager: Optional[DynamicSectorManager] = None
        self.selected_sector: Optional[DynamicSectorQuadrant] = None
        self.hover_sector: Optional[DynamicSectorQuadrant] = None
        
        # 动画相关
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_progress = 0.0
        self.animation_timer.start(50)  # 20 FPS
        
        self.setMouseTracking(True)
        self.setMinimumSize(200, 200)
    
    def set_sector_manager(self, manager: DynamicSectorManager):
        """设置扇形管理器"""
        self.sector_manager = manager
        
        # 连接信号
        manager.sector_progress_updated.connect(self.on_sector_progress_updated)
        manager.sector_count_changed.connect(self.on_sector_count_changed)
        
        self.update()
    
    def on_sector_progress_updated(self, sector: DynamicSectorQuadrant, progress: DynamicSectorProgress):
        """扇形进度更新"""
        self.update()
    
    def on_sector_count_changed(self, count: int):
        """扇形数量变化"""
        self.selected_sector = None
        self.hover_sector = None
        self.update()
    
    def update_animation(self):
        """更新动画"""
        self.animation_progress += 0.05
        if self.animation_progress > 1.0:
            self.animation_progress -= 1.0
        self.update()
    
    def paintEvent(self, event):
        """绘制扇形图"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if not self.sector_manager or not self.sector_manager.sectors:
            painter.drawText(self.rect(), Qt.AlignCenter, "未加载数据")
            return
        
        # 计算绘制区域
        margin = 20
        rect = self.rect().adjusted(margin, margin, -margin, -margin)
        center = rect.center()
        radius = min(rect.width(), rect.height()) / 2
        
        # 绘制背景圆
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.setBrush(QBrush(QColor(245, 245, 245)))
        painter.drawEllipse(center, radius, radius)
        
        # 绘制扇形
        for sector in self.sector_manager.sectors:
            self._draw_sector(painter, center, radius, sector)
        
        # 绘制中心装饰
        self._draw_center_decoration(painter, center)
        
        # 绘制统计信息
        self._draw_statistics(painter, rect)
    
    def _draw_sector(self, painter: QPainter, center: QPointF, radius: float, sector: DynamicSectorQuadrant):
        """绘制单个扇形"""
        progress = self.sector_manager.get_sector_progress(sector)
        if not progress:
            return
        
        # 计算扇形路径
        start_angle = int(sector.start_angle * 16)  # Qt使用1/16度为单位
        span_angle = int((sector.end_angle - sector.start_angle) * 16)
        
        # 创建扇形路径
        path = QPainterPath()
        path.moveTo(center)
        
        # 外圈半径（根据完成率调整）
        outer_radius = radius * (0.5 + 0.5 * progress.completion_rate / 100)
        
        # 创建扇形
        rect = QRectF(center.x() - outer_radius, center.y() - outer_radius,
                      outer_radius * 2, outer_radius * 2)
        path.arcTo(rect, start_angle / 16, span_angle / 16)
        path.lineTo(center)
        
        # 设置颜色
        color = self.sector_manager.get_sector_color(sector)
        
        # 根据状态调整透明度
        if sector == self.selected_sector:
            color.setAlpha(255)
        elif sector == self.hover_sector:
            color.setAlpha(200)
        else:
            color.setAlpha(150)
        
        # 绘制扇形
        painter.setPen(QPen(color.darker(120), 2))
        painter.setBrush(QBrush(color))
        painter.drawPath(path)
        
        # 绘制进度条效果（如果有完成的孔位）
        if progress.completed_holes > 0:
            # 创建渐变效果
            gradient_color = color.lighter(120)
            gradient_color.setAlpha(100)
            
            # 计算进度扇形
            progress_radius = outer_radius * 0.9
            progress_rect = QRectF(center.x() - progress_radius, center.y() - progress_radius,
                                 progress_radius * 2, progress_radius * 2)
            
            progress_path = QPainterPath()
            progress_path.moveTo(center)
            progress_path.arcTo(progress_rect, start_angle / 16, 
                              span_angle / 16 * progress.completion_rate / 100)
            progress_path.lineTo(center)
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(gradient_color))
            painter.drawPath(progress_path)
        
        # 绘制扇形标签
        self._draw_sector_label(painter, center, radius * 0.7, sector, progress)
    
    def _draw_sector_label(self, painter: QPainter, center: QPointF, radius: float, 
                          sector: DynamicSectorQuadrant, progress: DynamicSectorProgress):
        """绘制扇形标签"""
        # 计算标签位置（扇形中心角度）
        mid_angle = (sector.start_angle + sector.end_angle) / 2
        angle_rad = math.radians(mid_angle)
        
        label_x = center.x() + radius * math.cos(angle_rad)
        label_y = center.y() + radius * math.sin(angle_rad)
        
        # 设置字体
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        
        # 绘制扇形名称
        painter.setPen(QPen(Qt.white, 1))
        text = f"区域{sector.index + 1}"
        text_rect = QRectF(label_x - 30, label_y - 20, 60, 20)
        painter.drawText(text_rect, Qt.AlignCenter, text)
        
        # 绘制进度百分比
        font.setPointSize(8)
        font.setBold(False)
        painter.setFont(font)
        
        progress_text = f"{progress.completion_rate:.1f}%"
        progress_rect = QRectF(label_x - 30, label_y, 60, 20)
        painter.drawText(progress_rect, Qt.AlignCenter, progress_text)
    
    def _draw_center_decoration(self, painter: QPainter, center: QPointF):
        """绘制中心装饰"""
        # 绘制中心圆
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.setBrush(QBrush(Qt.white))
        painter.drawEllipse(center, 30, 30)
        
        # 绘制旋转动画效果
        painter.setPen(QPen(QColor(33, 150, 243), 3))
        painter.setBrush(Qt.NoBrush)
        
        angle = self.animation_progress * 360
        arc_rect = QRectF(center.x() - 25, center.y() - 25, 50, 50)
        painter.drawArc(arc_rect, int(angle * 16), int(90 * 16))
    
    def _draw_statistics(self, painter: QPainter, rect: QRectF):
        """绘制统计信息"""
        if not self.sector_manager:
            return
        
        # 在底部绘制整体统计
        font = QFont()
        font.setPointSize(9)
        painter.setFont(font)
        painter.setPen(QPen(QColor(60, 60, 60)))
        
        # 计算整体进度
        total_holes = sum(p.total_holes for p in self.sector_manager.sector_progresses.values())
        completed_holes = sum(p.completed_holes for p in self.sector_manager.sector_progresses.values())
        
        if total_holes > 0:
            overall_progress = completed_holes / total_holes * 100
            text = f"总进度: {overall_progress:.1f}% ({completed_holes}/{total_holes})"
            
            text_rect = QRectF(rect.left(), rect.bottom() - 20, rect.width(), 20)
            painter.drawText(text_rect, Qt.AlignCenter, text)
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton and self.hover_sector:
            self.selected_sector = self.hover_sector
            self.sector_selected.emit(self.selected_sector)
            self.update()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if not self.sector_manager:
            return
        
        # 计算鼠标位置对应的扇形
        margin = 20
        rect = self.rect().adjusted(margin, margin, -margin, -margin)
        center = rect.center()
        
        # 计算相对于中心的角度
        dx = event.pos().x() - center.x()
        dy = event.pos().y() - center.y()
        distance = math.sqrt(dx * dx + dy * dy)
        
        # 检查是否在圆内
        radius = min(rect.width(), rect.height()) / 2
        if distance > radius:
            self.hover_sector = None
        else:
            # 计算角度
            angle_rad = math.atan2(dy, dx)
            angle_deg = math.degrees(angle_rad)
            if angle_deg < 0:
                angle_deg += 360
            
            # 找到对应的扇形
            self.hover_sector = None
            for sector in self.sector_manager.sectors:
                if sector.start_angle <= angle_deg < sector.end_angle:
                    self.hover_sector = sector
                    break
        
        self.update()
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        self.hover_sector = None
        self.update()


class DynamicSectorDetailView(QWidget):
    """动态扇形详细信息视图"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sector_manager: Optional[DynamicSectorManager] = None
        self.current_sector: Optional[DynamicSectorQuadrant] = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 创建详情组
        self.detail_group = QGroupBox("扇形区域详情")
        detail_layout = QGridLayout(self.detail_group)
        
        # 扇形名称
        self.sector_name_label = QLabel("未选择扇形")
        self.sector_name_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.sector_name_label.setFont(font)
        detail_layout.addWidget(self.sector_name_label, 0, 0, 1, 2)
        
        # 统计标签
        self.labels = {}
        stats = [
            ("总孔数:", "total"),
            ("已完成:", "completed"),
            ("合格数:", "qualified"),
            ("异常数:", "defective"),
            ("完成率:", "completion_rate"),
            ("合格率:", "qualification_rate")
        ]
        
        for i, (text, key) in enumerate(stats):
            row = i // 2 + 1
            col = (i % 2) * 2
            
            label = QLabel(text)
            value_label = QLabel("-")
            value_label.setAlignment(Qt.AlignRight)
            
            detail_layout.addWidget(label, row, col)
            detail_layout.addWidget(value_label, row, col + 1)
            
            self.labels[key] = value_label
        
        layout.addWidget(self.detail_group)
        
        # 操作按钮（可选）
        self.action_button = QPushButton("查看详细数据")
        self.action_button.setEnabled(False)
        layout.addWidget(self.action_button)
        
        layout.addStretch()
    
    def set_sector_manager(self, manager: DynamicSectorManager):
        """设置扇形管理器"""
        self.sector_manager = manager
        manager.sector_progress_updated.connect(self.on_sector_progress_updated)
    
    def set_current_sector(self, sector: DynamicSectorQuadrant):
        """设置当前显示的扇形"""
        self.current_sector = sector
        self.update_display()
    
    def on_sector_progress_updated(self, sector: DynamicSectorQuadrant, progress: DynamicSectorProgress):
        """扇形进度更新"""
        if sector == self.current_sector:
            self.update_display()
    
    def update_display(self):
        """更新显示"""
        if not self.sector_manager or not self.current_sector:
            self.sector_name_label.setText("未选择扇形")
            for label in self.labels.values():
                label.setText("-")
            self.action_button.setEnabled(False)
            return
        
        progress = self.sector_manager.get_sector_progress(self.current_sector)
        if not progress:
            return
        
        # 更新扇形名称
        self.sector_name_label.setText(f"区域 {self.current_sector.index + 1}")
        
        # 设置颜色
        color = self.sector_manager.get_sector_color(self.current_sector)
        self.sector_name_label.setStyleSheet(f"color: {color.name()};")
        
        # 更新统计数据
        self.labels["total"].setText(str(progress.total_holes))
        self.labels["completed"].setText(str(progress.completed_holes))
        self.labels["qualified"].setText(str(progress.qualified_holes))
        self.labels["defective"].setText(str(progress.defective_holes))
        self.labels["completion_rate"].setText(f"{progress.completion_rate:.1f}%")
        self.labels["qualification_rate"].setText(f"{progress.qualification_rate:.1f}%")
        
        # 根据状态设置颜色
        if progress.completion_rate >= 100:
            self.labels["completion_rate"].setStyleSheet("color: green;")
        elif progress.completion_rate >= 50:
            self.labels["completion_rate"].setStyleSheet("color: orange;")
        else:
            self.labels["completion_rate"].setStyleSheet("color: red;")
        
        if progress.qualification_rate >= 95:
            self.labels["qualification_rate"].setStyleSheet("color: green;")
        elif progress.qualification_rate >= 90:
            self.labels["qualification_rate"].setStyleSheet("color: orange;")
        else:
            self.labels["qualification_rate"].setStyleSheet("color: red;")
        
        self.action_button.setEnabled(True)