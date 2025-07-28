"""
全景图UI组件
纯UI层，不包含业务逻辑
"""

from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt, Signal, QEvent, QPointF, QObject
from PySide6.QtGui import QMouseEvent

from src.core_business.graphics.graphics_view import OptimizedGraphicsView
from src.core_business.graphics.panorama.view_controller import PanoramaViewController
from src.core_business.graphics.sector_types import SectorQuadrant


class PanoramaWidget(QWidget):
    """
    全景图UI组件
    只负责UI展示和事件转发，不包含任何业务逻辑
    """
    
    # 转发控制器的信号
    sector_clicked = Signal(SectorQuadrant)
    status_update_completed = Signal(int)
    
    def __init__(self, controller: PanoramaViewController, parent=None):
        super().__init__(parent)
        
        # 注入控制器
        self.controller = controller
        
        # 设置窗口属性
        self.setWindowTitle("全景图")
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        # 创建UI
        self._setup_ui()
        
        # 连接控制器信号
        self._connect_controller_signals()
    
    def _setup_ui(self):
        """设置UI界面"""
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 创建图形视图
        self.graphics_view = OptimizedGraphicsView()
        self.graphics_view.setMinimumSize(600, 600)
        
        # 设置场景
        self.scene = QGraphicsScene()
        self.graphics_view.setScene(self.scene)
        
        # 将场景传递给控制器
        self.controller.scene = self.scene
        
        # 安装事件过滤器
        self.graphics_view.viewport().installEventFilter(self)
        
        # 添加到布局
        layout.addWidget(self.graphics_view)
    
    def _connect_controller_signals(self):
        """连接控制器信号"""
        self.controller.sector_clicked.connect(self.sector_clicked.emit)
        self.controller.status_update_completed.connect(self.status_update_completed.emit)
    
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """
        事件过滤器
        捕获鼠标点击事件并转发给控制器
        """
        if watched == self.graphics_view.viewport() and event.type() == QEvent.MouseButtonPress:
            mouse_event = event
            if mouse_event.button() == Qt.LeftButton:
                # 转换坐标到场景坐标
                scene_pos = self.graphics_view.mapToScene(mouse_event.pos())
                # 转发给控制器处理
                self.controller.handle_click(scene_pos)
                return True
        
        return super().eventFilter(watched, event)
    
    def setFixedSize(self, w: int, h: int):
        """
        设置固定大小
        重写以同时调整图形视图大小
        """
        super().setFixedSize(w, h)
        # 调整图形视图大小，考虑边距
        margins = self.layout().contentsMargins()
        view_width = w - margins.left() - margins.right()
        view_height = h - margins.top() - margins.bottom()
        self.graphics_view.setFixedSize(view_width, view_height)
    
    def resizeEvent(self, event):
        """
        窗口大小改变事件
        确保视图适应窗口
        """
        super().resizeEvent(event)
        # 可以在这里添加自适应逻辑
    
    # 公共接口方法，转发给控制器
    
    def load_hole_collection(self, hole_collection):
        """加载孔位集合"""
        self.controller.load_hole_collection(hole_collection)
    
    def update_hole_status(self, hole_id: str, status):
        """更新孔位状态"""
        self.controller.update_hole_status(hole_id, status)
    
    def highlight_sector(self, sector: SectorQuadrant):
        """高亮扇区"""
        self.controller.highlight_sector(sector)
    
    def clear_sector_highlight(self):
        """清除扇区高亮"""
        self.controller.clear_sector_highlight()
    
    def enable_snake_path(self, enabled: bool):
        """启用/禁用蛇形路径"""
        self.controller.enable_snake_path(enabled)
    
    def apply_theme(self, theme_config: dict):
        """应用主题"""
        self.controller.apply_theme(theme_config)
        
        # 应用到自身
        if 'widget_style' in theme_config:
            self.setStyleSheet(theme_config['widget_style'])