"""
全景预览组件
360x420px固定大小的工件全景视图，支持扇形区域显示和交互
"""

import math
from typing import Dict, List, Optional, Tuple
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal, QPointF, QRectF
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath, QPolygonF

from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus
from src.core_business.graphics.sector_manager_adapter import SectorManagerAdapter


class CompletePanoramaWidget(QWidget):
    """
    完整全景预览组件 - 360x420px
    显示工件全貌和扇形区域划分，支持点击交互
    """
    
    # 信号定义
    sector_clicked = Signal(int)  # 扇形ID (0-7)
    hole_clicked = Signal(str)    # 孔位ID
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(360, 420)
        self.setToolTip("工件全景预览 - 点击扇形区域进行切换")
        
        # 数据
        self.hole_collection: Optional[HoleCollection] = None
        self.sector_manager = SectorManagerAdapter()
        self.selected_sector: Optional[int] = None
        
        # 扇形配置
        self.sector_count = 8  # 8个扇形
        self.sectors_data: Dict[int, Dict] = {}
        
        # 绘制参数
        self.center = QPointF(180, 210)  # 组件中心点
        self.radius = 150  # 主绘制半径
        self.hole_radius = 2  # 孔位绘制半径
        
        # 颜色配置
        self.colors = {
            'background': QColor(245, 245, 245),
            'border': QColor(150, 150, 150),
            'sector_normal': QColor(200, 200, 200, 100),
            'sector_selected': QColor(33, 150, 243, 150),  # 蓝色
            'sector_border': QColor(100, 100, 100),
            'hole_not_detected': QColor(128, 128, 128),
            'hole_qualified': QColor(76, 175, 80),
            'hole_defective': QColor(244, 67, 54),
            'hole_processing': QColor(255, 193, 7),
            'workpiece_outline': QColor(80, 80, 80)
        }
        
        # 连接信号
        self.sector_manager.sector_progress_updated.connect(self._on_sector_progress_updated)
        self.sector_manager.overall_progress_updated.connect(self._on_overall_progress_updated)
        
        # 初始化扇形数据
        self._initialize_sectors()
    
    def _initialize_sectors(self):
        """初始化扇形数据"""
        angle_per_sector = 360.0 / self.sector_count
        
        for i in range(self.sector_count):
            start_angle = i * angle_per_sector
            self.sectors_data[i] = {
                'id': i,
                'start_angle': start_angle,
                'span_angle': angle_per_sector,
                'progress': 0.0,
                'hole_count': 0,
                'qualified_count': 0,
                'defective_count': 0,
                'processing_count': 0,
                'bounds': None  # 将在加载数据时计算
            }
    
    def load_workpiece_data(self, hole_collection: HoleCollection):
        """加载工件数据"""
        self.hole_collection = hole_collection
        
        if not hole_collection or not hole_collection.holes:
            return
        
        # 计算工件边界
        self._calculate_workpiece_bounds()
        
        # 分配孔位到扇形
        self._assign_holes_to_sectors()
        
        # 更新扇形统计
        self._update_sector_statistics()
        
        # 重绘
        self.update()
    
    def _calculate_workpiece_bounds(self):
        """计算工件边界"""
        if not self.hole_collection or not self.hole_collection.holes:
            return
        
        holes = list(self.hole_collection.holes.values())
        if not holes:
            return
        
        # 计算边界
        min_x = min(hole.x for hole in holes)
        max_x = max(hole.x for hole in holes)
        min_y = min(hole.y for hole in holes)
        max_y = max(hole.y for hole in holes)
        
        # 添加边距
        margin = 20
        self.workpiece_bounds = QRectF(
            min_x - margin, min_y - margin,
            (max_x - min_x) + 2 * margin,
            (max_y - min_y) + 2 * margin
        )
    
    def _assign_holes_to_sectors(self):
        """将孔位分配到扇形区域"""
        if not self.hole_collection:
            return
        
        # 重置扇形统计
        for sector_data in self.sectors_data.values():
            sector_data['holes'] = []
            sector_data['hole_count'] = 0
        
        center_x = self.workpiece_bounds.center().x()
        center_y = self.workpiece_bounds.center().y()
        
        for hole in self.hole_collection.holes.values():
            # 计算孔位相对于工件中心的角度
            dx = hole.x - center_x
            dy = hole.y - center_y
            angle = math.degrees(math.atan2(-dy, dx))  # 注意Y轴方向
            
            # 规范化角度到 [0, 360)
            if angle < 0:
                angle += 360
            
            # 确定属于哪个扇形
            sector_id = int(angle / (360.0 / self.sector_count))
            sector_id = min(sector_id, self.sector_count - 1)  # 确保不超出范围
            
            # 添加到扇形
            if 'holes' not in self.sectors_data[sector_id]:
                self.sectors_data[sector_id]['holes'] = []
            self.sectors_data[sector_id]['holes'].append(hole)
            self.sectors_data[sector_id]['hole_count'] += 1
    
    def _update_sector_statistics(self):
        """更新扇形统计信息"""
        for sector_id, sector_data in self.sectors_data.items():
            holes = sector_data.get('holes', [])
            
            qualified_count = sum(1 for hole in holes if hole.status == HoleStatus.QUALIFIED)
            defective_count = sum(1 for hole in holes if hole.status == HoleStatus.DEFECTIVE)
            processing_count = sum(1 for hole in holes if hole.status == HoleStatus.PROCESSING)
            
            sector_data.update({
                'qualified_count': qualified_count,
                'defective_count': defective_count,
                'processing_count': processing_count,
                'progress': qualified_count / len(holes) * 100 if holes else 0
            })
    
    def set_selected_sector(self, sector_id: Optional[int]):
        """设置选中的扇形"""
        if self.selected_sector != sector_id:
            self.selected_sector = sector_id
            self.update()
    
    def get_sector_at_position(self, pos: QPointF) -> Optional[int]:
        """获取指定位置的扇形ID"""
        # 计算相对于中心的位置
        dx = pos.x() - self.center.x()
        dy = pos.y() - self.center.y()
        distance = math.sqrt(dx*dx + dy*dy)
        
        # 检查是否在有效半径内
        if distance > self.radius:
            return None
        
        # 计算角度
        angle = math.degrees(math.atan2(-dy, dx))
        if angle < 0:
            angle += 360
        
        # 确定扇形ID
        sector_id = int(angle / (360.0 / self.sector_count))
        return min(sector_id, self.sector_count - 1)
    
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # 填充背景
        painter.fillRect(self.rect(), self.colors['background'])
        
        # 绘制工件轮廓
        self._draw_workpiece_outline(painter)
        
        # 绘制扇形区域
        self._draw_sectors(painter)
        
        # 绘制孔位
        self._draw_holes(painter)
        
        # 绘制边框
        painter.setPen(QPen(self.colors['border'], 2))
        painter.drawRect(self.rect().adjusted(1, 1, -1, -1))
    
    def _draw_workpiece_outline(self, painter: QPainter):
        """绘制工件轮廓"""
        if not hasattr(self, 'workpiece_bounds'):
            return
        
        # 计算缩放比例以适应组件大小
        available_size = min(self.width() - 40, self.height() - 40)
        workpiece_size = max(self.workpiece_bounds.width(), self.workpiece_bounds.height())
        scale = available_size / workpiece_size if workpiece_size > 0 else 1
        
        # 计算绘制矩形
        scaled_width = self.workpiece_bounds.width() * scale
        scaled_height = self.workpiece_bounds.height() * scale
        draw_rect = QRectF(
            self.center.x() - scaled_width / 2,
            self.center.y() - scaled_height / 2,
            scaled_width,
            scaled_height
        )
        
        # 绘制轮廓
        painter.setPen(QPen(self.colors['workpiece_outline'], 2))
        painter.setBrush(QBrush(QColor(255, 255, 255, 50)))
        painter.drawRect(draw_rect)
    
    def _draw_sectors(self, painter: QPainter):
        """绘制扇形区域"""
        for sector_id, sector_data in self.sectors_data.items():
            start_angle = sector_data['start_angle']
            span_angle = sector_data['span_angle']
            
            # 创建扇形路径
            path = QPainterPath()
            path.moveTo(self.center)
            path.arcTo(
                self.center.x() - self.radius,
                self.center.y() - self.radius,
                self.radius * 2,
                self.radius * 2,
                start_angle,
                span_angle
            )
            path.closeSubpath()
            
            # 选择颜色
            if sector_id == self.selected_sector:
                fill_color = self.colors['sector_selected']
                border_color = QColor(33, 150, 243)  # 深蓝色
                border_width = 3
            else:
                # 根据进度着色
                progress = sector_data.get('progress', 0)
                if progress > 80:
                    fill_color = QColor(76, 175, 80, 100)  # 绿色
                elif progress > 50:
                    fill_color = QColor(255, 193, 7, 100)  # 黄色
                else:
                    fill_color = self.colors['sector_normal']
                border_color = self.colors['sector_border']
                border_width = 1
            
            # 绘制扇形
            painter.setBrush(QBrush(fill_color))
            painter.setPen(QPen(border_color, border_width))
            painter.drawPath(path)
            
            # 绘制扇形标签
            self._draw_sector_label(painter, sector_id, sector_data)
    
    def _draw_sector_label(self, painter: QPainter, sector_id: int, sector_data: Dict):
        """绘制扇形标签"""
        start_angle = sector_data['start_angle']
        span_angle = sector_data['span_angle']
        middle_angle = start_angle + span_angle / 2
        
        # 计算标签位置（距离中心2/3半径处）
        label_radius = self.radius * 0.6
        label_x = self.center.x() + label_radius * math.cos(math.radians(middle_angle))
        label_y = self.center.y() - label_radius * math.sin(math.radians(middle_angle))
        
        # 设置字体
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        
        # 绘制扇形ID
        painter.setPen(QPen(QColor(50, 50, 50)))
        text = str(sector_id)
        painter.drawText(int(label_x - 10), int(label_y + 5), text)
        
        # 绘制进度信息（如果有数据）
        if sector_data.get('hole_count', 0) > 0:
            font.setPointSize(8)
            painter.setFont(font)
            progress_text = f"{sector_data['progress']:.0f}%"
            painter.drawText(int(label_x - 15), int(label_y + 20), progress_text)
    
    def _draw_holes(self, painter: QPainter):
        """绘制孔位"""
        if not self.hole_collection or not hasattr(self, 'workpiece_bounds'):
            return
        
        # 计算缩放比例
        available_size = min(self.width() - 40, self.height() - 40)
        workpiece_size = max(self.workpiece_bounds.width(), self.workpiece_bounds.height())
        scale = available_size / workpiece_size if workpiece_size > 0 else 1
        
        # 计算偏移量以居中显示
        offset_x = self.center.x() - self.workpiece_bounds.center().x() * scale
        offset_y = self.center.y() - self.workpiece_bounds.center().y() * scale
        
        for hole in self.hole_collection.holes.values():
            # 计算绘制位置
            draw_x = hole.x * scale + offset_x
            draw_y = hole.y * scale + offset_y
            
            # 根据状态选择颜色
            if hole.status == HoleStatus.QUALIFIED:
                color = self.colors['hole_qualified']
            elif hole.status == HoleStatus.DEFECTIVE:
                color = self.colors['hole_defective']
            elif hole.status == HoleStatus.PROCESSING:
                color = self.colors['hole_processing']
            else:
                color = self.colors['hole_not_detected']
            
            # 绘制孔位
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(0, 0, 0, 100), 0.5))
            painter.drawEllipse(
                QPointF(draw_x, draw_y),
                self.hole_radius,
                self.hole_radius
            )
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            sector_id = self.get_sector_at_position(event.position())
            if sector_id is not None:
                self.set_selected_sector(sector_id)
                self.sector_clicked.emit(sector_id)
        
        super().mousePressEvent(event)
    
    def _on_sector_progress_updated(self, sector, progress):
        """处理扇形进度更新"""
        # 更新本地数据并重绘
        self._update_sector_statistics()
        self.update()
    
    def _on_overall_progress_updated(self, progress_data: Dict):
        """处理整体进度更新"""
        # 重绘组件
        self.update()
    
    def get_sector_info(self, sector_id: int) -> Optional[Dict]:
        """获取扇形信息"""
        return self.sectors_data.get(sector_id)
    
    def get_selected_sector_info(self) -> Optional[Dict]:
        """获取当前选中扇形的信息"""
        if self.selected_sector is not None:
            return self.get_sector_info(self.selected_sector)
        return None