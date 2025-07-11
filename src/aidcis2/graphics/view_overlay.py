"""
视图叠加层组件
实现微观和宏观视图区域的叠加显示
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QGraphicsView, QGraphicsScene, 
                               QGraphicsEllipseItem, QGraphicsRectItem,
                               QSizePolicy)
from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QTimer
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QPainter

from typing import Optional
import logging


class ViewOverlayWidget(QWidget):
    """视图叠加层基类"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.logger = logging.getLogger(__name__)
        self.setup_ui()
    
    def setup_ui(self):
        """设置用户界面"""
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.95);
                border: 2px solid #4CAF50;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)
        
        # 标题
        title_label = QLabel(self.title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #2E7D32;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
                border: none;
                padding: 3px;
            }
        """)
        layout.addWidget(title_label)
        
        # 内容区域
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(2, 2, 2, 2)
        self.content_layout.setSpacing(2)
        
        layout.addWidget(self.content_widget)
        
        # 设置大小策略
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    
    def add_content(self, widget: QWidget):
        """添加内容组件"""
        self.content_layout.addWidget(widget)


class MicroViewOverlay(ViewOverlayWidget):
    """微观视图叠加层 - 左上角"""
    
    hole_selected = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__("🔍 微观视图", parent)
        self.current_hole_data = None
        self.setup_micro_view()
    
    def setup_micro_view(self):
        """设置微观视图内容"""
        # 创建微观视图图形区域
        self.micro_view = QGraphicsView()
        self.micro_view.setFixedSize(150, 150)
        self.micro_view.setStyleSheet("background: transparent; border: none;")
        self.micro_view.setRenderHint(QPainter.Antialiasing)
        self.micro_view.setFrameShape(QFrame.NoFrame)
        self.micro_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.micro_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.micro_scene = QGraphicsScene()
        self.micro_view.setScene(self.micro_scene)
        
        # 添加到内容区域
        self.add_content(self.micro_view)
        
        # 创建信息显示区域
        self.info_label = QLabel("点击孔位查看详情")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("""
            QLabel {
                color: #555;
                font-size: 10px;
                background: transparent;
                border: none;
                padding: 2px;
            }
        """)
        self.info_label.setWordWrap(True)
        self.add_content(self.info_label)
        
        # 初始化视图
        self.create_placeholder_view()
    
    def create_placeholder_view(self):
        """创建占位符视图"""
        # 清空场景
        self.micro_scene.clear()
        
        # 添加占位符圆形
        placeholder = QGraphicsEllipseItem(-60, -60, 120, 120)
        placeholder.setBrush(QBrush(QColor(200, 200, 200, 100)))
        placeholder.setPen(QPen(QColor(150, 150, 150), 2, Qt.DashLine))
        self.micro_scene.addItem(placeholder)
        
        # 添加文本
        text_item = self.micro_scene.addText("微观视图", QFont("Arial", 12))
        text_item.setPos(-40, -10)
        text_item.setDefaultTextColor(QColor(100, 100, 100))
        
        # 设置场景范围
        self.micro_scene.setSceneRect(-75, -75, 150, 150)
        self.micro_view.fitInView(self.micro_scene.sceneRect(), Qt.KeepAspectRatio)
    
    def show_hole_detail(self, hole_data):
        """显示孔位详情"""
        self.current_hole_data = hole_data
        
        # 清空场景
        self.micro_scene.clear()
        
        # 创建孔位详细视图
        hole_item = QGraphicsEllipseItem(-25, -25, 50, 50)
        
        # 根据状态设置颜色
        status_colors = {
            'not_detected': QColor(128, 128, 128),
            'detecting': QColor(255, 255, 0),
            'qualified': QColor(0, 255, 0),
            'unqualified': QColor(255, 0, 0),
            'real_data': QColor(255, 165, 0)
        }
        
        color = status_colors.get(hole_data.get('status', 'not_detected'), QColor(128, 128, 128))
        hole_item.setBrush(QBrush(color))
        hole_item.setPen(QPen(QColor(0, 0, 0), 2))
        self.micro_scene.addItem(hole_item)
        
        # 添加孔位ID
        hole_id = hole_data.get('hole_id', 'N/A')
        text_item = self.micro_scene.addText(hole_id, QFont("Arial", 10, QFont.Bold))
        text_item.setPos(-len(hole_id) * 3, 30)
        text_item.setDefaultTextColor(QColor(0, 0, 0))
        
        # 添加周围的相邻孔位（模拟）
        for i, (dx, dy) in enumerate([(0, -80), (80, 0), (0, 80), (-80, 0)]):
            neighbor_item = QGraphicsEllipseItem(dx-15, dy-15, 30, 30)
            neighbor_item.setBrush(QBrush(QColor(200, 200, 200, 150)))
            neighbor_item.setPen(QPen(QColor(100, 100, 100), 1))
            self.micro_scene.addItem(neighbor_item)
        
        # 设置场景范围
        self.micro_scene.setSceneRect(-100, -100, 200, 200)
        self.micro_view.fitInView(self.micro_scene.sceneRect(), Qt.KeepAspectRatio)
        
        # 更新信息标签
        status_text = hole_data.get('status', 'not_detected')
        coord_text = f"({hole_data.get('x', 0):.1f}, {hole_data.get('y', 0):.1f})"
        self.info_label.setText(f"孔位: {hole_id}\n坐标: {coord_text}\n状态: {status_text}")


class MacroViewOverlay(ViewOverlayWidget):
    """宏观视图叠加层 - 右上角"""
    
    sector_selected = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__("📊 宏观视图", parent)
        self.setup_macro_view()
    
    def setup_macro_view(self):
        """设置宏观视图内容"""
        # 创建宏观视图图形区域
        self.macro_view = QGraphicsView()
        self.macro_view.setFixedSize(150, 150)
        self.macro_view.setStyleSheet("background: transparent; border: none;")
        self.macro_view.setRenderHint(QPainter.Antialiasing)
        self.macro_view.setFrameShape(QFrame.NoFrame)
        self.macro_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.macro_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.macro_scene = QGraphicsScene()
        self.macro_view.setScene(self.macro_scene)
        
        # 添加到内容区域
        self.add_content(self.macro_view)
        
        # 创建统计信息显示区域
        self.stats_label = QLabel("整体统计")
        self.stats_label.setAlignment(Qt.AlignCenter)
        self.stats_label.setStyleSheet("""
            QLabel {
                color: #555;
                font-size: 10px;
                background: transparent;
                border: none;
                padding: 2px;
            }
        """)
        self.stats_label.setWordWrap(True)
        self.add_content(self.stats_label)
        
        # 初始化视图
        self.create_overview_display()
    
    def create_overview_display(self):
        """创建概览显示"""
        # 清空场景
        self.macro_scene.clear()
        
        # 创建管板整体轮廓
        outline = QGraphicsRectItem(-60, -45, 120, 90)
        outline.setBrush(QBrush(QColor(240, 240, 240, 200)))
        outline.setPen(QPen(QColor(100, 100, 100), 2))
        self.macro_scene.addItem(outline)
        
        # 添加网格点表示孔位分布
        rows, cols = 6, 8
        start_x, start_y = -50, -35
        spacing_x, spacing_y = 12, 11
        
        for row in range(rows):
            for col in range(cols):
                x = start_x + col * spacing_x
                y = start_y + row * spacing_y
                
                dot = QGraphicsEllipseItem(x-1, y-1, 2, 2)
                dot.setBrush(QBrush(QColor(100, 100, 100)))
                dot.setPen(QPen(QColor(100, 100, 100), 1))
                self.macro_scene.addItem(dot)
        
        # 添加标题
        text_item = self.macro_scene.addText("管板全貌", QFont("Arial", 10))
        text_item.setPos(-30, -70)
        text_item.setDefaultTextColor(QColor(100, 100, 100))
        
        # 设置场景范围
        self.macro_scene.setSceneRect(-75, -75, 150, 150)
        self.macro_view.fitInView(self.macro_scene.sceneRect(), Qt.KeepAspectRatio)
    
    def update_statistics(self, stats_data):
        """更新统计信息"""
        total = stats_data.get('total', 0)
        completed = stats_data.get('completed', 0)
        qualified = stats_data.get('qualified', 0)
        
        progress = (completed / total * 100) if total > 0 else 0
        qualified_rate = (qualified / completed * 100) if completed > 0 else 0
        
        stats_text = f"总数: {total}\n完成: {completed}\n合格率: {qualified_rate:.1f}%\n进度: {progress:.1f}%"
        self.stats_label.setText(stats_text)
        
        # 更新图形显示中的颜色分布
        self.update_overview_colors(stats_data)
    
    def update_overview_colors(self, stats_data):
        """更新概览图中的颜色分布"""
        # 这里可以根据统计数据更新管板上的颜色分布
        # 例如用不同颜色的区域表示不同的检测状态
        pass


class ViewOverlayManager:
    """视图叠加层管理器"""
    
    def __init__(self, parent_widget: QWidget):
        self.parent_widget = parent_widget
        self.micro_overlay: Optional[MicroViewOverlay] = None
        self.macro_overlay: Optional[MacroViewOverlay] = None
        
        # 创建叠加层
        self.create_overlays()
        
        # 设置定时器用于更新位置
        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self.update_overlay_positions)
        self.position_timer.start(100)  # 每100ms更新一次位置
    
    def create_overlays(self):
        """创建叠加层组件"""
        # 创建微观视图叠加层（左上角）
        self.micro_overlay = MicroViewOverlay(self.parent_widget)
        self.micro_overlay.setFixedSize(160, 200)
        
        # 创建宏观视图叠加层（右上角）
        self.macro_overlay = MacroViewOverlay(self.parent_widget)
        self.macro_overlay.setFixedSize(160, 200)
        
        # 初始位置
        self.update_overlay_positions()
        
        # 确保在最上层显示
        self.micro_overlay.raise_()
        self.macro_overlay.raise_()
        
        # 显示叠加层
        self.micro_overlay.show()
        self.macro_overlay.show()
    
    def update_overlay_positions(self):
        """更新叠加层位置"""
        if not self.parent_widget:
            return
        
        parent_rect = self.parent_widget.rect()
        
        # 微观视图 - 左上角
        if self.micro_overlay:
            self.micro_overlay.move(10, 10)
        
        # 宏观视图 - 右上角
        if self.macro_overlay:
            self.macro_overlay.move(parent_rect.width() - 170, 10)
    
    def show_hole_detail(self, hole_data):
        """显示孔位详情"""
        if self.micro_overlay:
            self.micro_overlay.show_hole_detail(hole_data)
    
    def update_macro_statistics(self, stats_data):
        """更新宏观统计"""
        if self.macro_overlay:
            self.macro_overlay.update_statistics(stats_data)
    
    def set_visible(self, visible: bool):
        """设置叠加层可见性"""
        if self.micro_overlay:
            self.micro_overlay.setVisible(visible)
        if self.macro_overlay:
            self.macro_overlay.setVisible(visible)
    
    def cleanup(self):
        """清理资源"""
        if self.position_timer:
            self.position_timer.stop()
        
        if self.micro_overlay:
            self.micro_overlay.deleteLater()
        if self.macro_overlay:
            self.macro_overlay.deleteLater()