"""
全景图专用图形视图
禁用拖拽功能，专注于扇形点击
"""

from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt, QEvent, Signal
from PySide6.QtGui import QPainter, QMouseEvent

from src.core_business.graphics.graphics_view import OptimizedGraphicsView


class PanoramaGraphicsView(OptimizedGraphicsView):
    """
    全景图专用图形视图
    继承自OptimizedGraphicsView，但禁用了拖拽功能
    """
    
    # 信号
    left_clicked = Signal(object)  # 发送场景坐标
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 禁用拖拽相关功能
        self.setDragMode(QGraphicsView.NoDrag)
        self.panning_enabled = False  # 禁用平移
        self.is_panning = False
        
        # 保持其他优化设置
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)
        self.setOptimizationFlag(QGraphicsView.DontSavePainterState, True)
        
        # 启用鼠标跟踪以支持悬停
        self.setMouseTracking(True)
        
    def mousePressEvent(self, event: QMouseEvent):
        """重写鼠标按下事件，取消拖拽行为"""
        if event.button() == Qt.LeftButton:
            # 转换为场景坐标
            scene_pos = self.mapToScene(event.pos())
            # 发送点击信号
            self.left_clicked.emit(scene_pos)
            event.accept()
        else:
            # 其他按钮保持原有行为
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """重写鼠标移动事件，取消拖拽行为"""
        # 不进行拖拽，只处理悬停
        if hasattr(self, '_handle_hover'):
            self._handle_hover(event.pos())
        # 不调用父类的mouseMoveEvent以避免拖拽
        event.accept()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """重写鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            # 左键释放，无需特殊处理
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    def wheelEvent(self, event):
        """保持缩放功能"""
        # 保持父类的缩放功能
        super().wheelEvent(event)