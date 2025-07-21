"""
视图导航功能
实现鼠标滚轮缩放、拖拽平移、缩放中心跟随鼠标位置等导航功能
"""

from PySide6.QtWidgets import QGraphicsView
from PySide6.QtCore import Qt, QPointF, Signal, QTimer
from PySide6.QtGui import QWheelEvent, QMouseEvent, QKeyEvent, QCursor

import math
from typing import Optional


class NavigationMixin:
    """导航功能混入类"""
    
    # 信号
    zoom_changed = Signal(float)  # 缩放改变
    pan_changed = Signal(QPointF)  # 平移改变
    navigation_reset = Signal()  # 导航重置
    
    def __init__(self):
        """初始化导航功能"""
        # 导航参数
        self.zoom_factor_in = 1.25
        self.zoom_factor_out = 0.8
        self.min_zoom = 0.01
        self.max_zoom = 100.0
        
        # 平移参数
        self.pan_speed = 1.0
        self.is_panning = False
        self.last_pan_point = QPointF()
        
        # 缩放参数
        self.zoom_anchor_under_mouse = True
        self.smooth_zoom = True
        self.zoom_animation_duration = 100  # 毫秒
        
        # 键盘导航
        self.keyboard_pan_step = 50
        self.keyboard_zoom_step = 0.1
        
        # 状态跟踪
        self.current_zoom = 1.0
        self.zoom_center = QPointF()
        
        # 平滑缩放定时器
        self.zoom_timer = QTimer()
        self.zoom_timer.timeout.connect(self._smooth_zoom_step)
        self.zoom_timer.setSingleShot(True)
        
        # 目标缩放值（用于平滑缩放）
        self.target_zoom = 1.0
        self.zoom_steps = 0
        self.max_zoom_steps = 5
    
    def setup_navigation(self):
        """设置导航功能"""
        # 启用鼠标跟踪
        self.setMouseTracking(True)
        
        # 设置拖拽模式
        self.setDragMode(QGraphicsView.NoDrag)
        
        # 设置变换锚点
        self.setTransformationAnchor(QGraphicsView.NoAnchor)
        self.setResizeAnchor(QGraphicsView.NoAnchor)
        
        # 启用键盘焦点
        self.setFocusPolicy(Qt.StrongFocus)
    
    # 鼠标滚轮缩放功能已禁用（Mac兼容性）
    
    # 鼠标事件现在由 InteractionMixin 处理
    
    def keyPressEvent(self, event: QKeyEvent):
        """键盘按下事件"""
        key = event.key()
        modifiers = event.modifiers()
        
        # 缩放快捷键
        if key == Qt.Key_Plus or key == Qt.Key_Equal:
            if modifiers & Qt.ControlModifier:
                self.zoom_in()
                event.accept()
                return
        elif key == Qt.Key_Minus:
            if modifiers & Qt.ControlModifier:
                self.zoom_out()
                event.accept()
                return
        elif key == Qt.Key_0:
            if modifiers & Qt.ControlModifier:
                self.reset_zoom()
                event.accept()
                return
        
        # 平移快捷键
        elif key == Qt.Key_Left:
            self.pan_left()
            event.accept()
            return
        elif key == Qt.Key_Right:
            self.pan_right()
            event.accept()
            return
        elif key == Qt.Key_Up:
            self.pan_up()
            event.accept()
            return
        elif key == Qt.Key_Down:
            self.pan_down()
            event.accept()
            return
        
        # 适应视图
        elif key == Qt.Key_F:
            self.fit_in_view_all()
            event.accept()
            return
        
        # 传递给父类处理
        super().keyPressEvent(event)
    
    def start_pan(self, mouse_pos):
        """开始平移"""
        self.is_panning = True
        self.last_pan_point = mouse_pos
        self.setCursor(QCursor(Qt.ClosedHandCursor))
    
    def update_pan(self, mouse_pos):
        """更新平移"""
        if not self.is_panning:
            return
        
        # 计算移动距离
        delta = mouse_pos - self.last_pan_point
        self.last_pan_point = mouse_pos
        
        # 执行平移
        self.pan_by_pixels(delta.x(), delta.y())
    
    def end_pan(self):
        """结束平移"""
        self.is_panning = False
        self.setCursor(QCursor(Qt.ArrowCursor))
    
    def pan_by_pixels(self, dx: float, dy: float):
        """按像素平移"""
        # 转换为场景坐标增量
        scene_delta = self.mapToScene(int(dx), int(dy)) - self.mapToScene(0, 0)

        # 更新视图中心（拖拽平移使用减法，使方向正确）
        current_center = self.mapToScene(self.viewport().rect().center())
        new_center = current_center - scene_delta  # 拖拽平移：鼠标右移，视图左移
        self.centerOn(new_center)

        # 发射信号
        self.pan_changed.emit(new_center)
    
    def zoom_at_point(self, scene_pos: QPointF, zoom_factor: float):
        """在指定点缩放"""
        # 获取当前变换
        current_transform = self.transform()
        current_scale = current_transform.m11()
        
        # 计算新的缩放值
        new_scale = current_scale * zoom_factor
        
        # 限制缩放范围
        if new_scale < self.min_zoom:
            zoom_factor = self.min_zoom / current_scale
            new_scale = self.min_zoom
        elif new_scale > self.max_zoom:
            zoom_factor = self.max_zoom / current_scale
            new_scale = self.max_zoom
        
        # 如果缩放值没有变化，直接返回
        if abs(zoom_factor - 1.0) < 0.001:
            return
        
        # 执行缩放
        if self.zoom_anchor_under_mouse:
            # 以鼠标位置为中心缩放
            self.scale(zoom_factor, zoom_factor)
            
            # 调整视图位置，使鼠标位置保持不变
            view_pos = self.mapFromScene(scene_pos)
            new_scene_pos = self.mapToScene(view_pos)
            delta = scene_pos - new_scene_pos
            self.translate(delta.x(), delta.y())
        else:
            # 以视图中心缩放
            self.scale(zoom_factor, zoom_factor)
        
        # 更新当前缩放值
        self.current_zoom = new_scale
        
        # 发射信号
        self.zoom_changed.emit(new_scale)
    
    def zoom_in(self, factor: Optional[float] = None):
        """放大"""
        if factor is None:
            factor = self.zoom_factor_in
        
        center = self.mapToScene(self.viewport().rect().center())
        self.zoom_at_point(center, factor)
    
    def zoom_out(self, factor: Optional[float] = None):
        """缩小"""
        if factor is None:
            factor = self.zoom_factor_out
        
        center = self.mapToScene(self.viewport().rect().center())
        self.zoom_at_point(center, factor)
    
    def reset_zoom(self):
        """重置缩放"""
        current_scale = self.transform().m11()
        reset_factor = 1.0 / current_scale
        
        center = self.mapToScene(self.viewport().rect().center())
        self.zoom_at_point(center, reset_factor)
    
    def set_zoom(self, zoom_level: float):
        """设置缩放级别"""
        current_scale = self.transform().m11()
        zoom_factor = zoom_level / current_scale
        
        center = self.mapToScene(self.viewport().rect().center())
        self.zoom_at_point(center, zoom_factor)
    
    def get_zoom(self) -> float:
        """获取当前缩放级别"""
        return self.transform().m11()
    
    def fit_in_view_all(self):
        """适应视图显示所有内容"""
        # 尝试获取场景，兼容不同的实现方式
        scene = getattr(self, 'scene', None)
        if callable(scene):
            scene = scene()

        if scene and scene.items():
            items_rect = scene.itemsBoundingRect()
            if not items_rect.isEmpty():
                self.fitInView(items_rect, Qt.KeepAspectRatio)
                self.current_zoom = self.transform().m11()
                self.zoom_changed.emit(self.current_zoom)
    
    def pan_left(self):
        """向左平移"""
        self.pan_by_pixels(self.keyboard_pan_step, 0)  # 修正方向

    def pan_right(self):
        """向右平移"""
        self.pan_by_pixels(-self.keyboard_pan_step, 0)  # 修正方向

    def pan_up(self):
        """向上平移"""
        self.pan_by_pixels(0, self.keyboard_pan_step)  # 修正方向

    def pan_down(self):
        """向下平移"""
        self.pan_by_pixels(0, -self.keyboard_pan_step)  # 修正方向
    
    def center_on_point(self, scene_pos: QPointF):
        """将视图中心设置到指定点"""
        self.centerOn(scene_pos)
        self.pan_changed.emit(scene_pos)
    
    def _smooth_zoom_step(self):
        """平滑缩放步骤"""
        if self.zoom_steps <= 0:
            return
        
        # 计算当前步骤的缩放因子
        step_factor = (self.target_zoom / self.current_zoom) ** (1.0 / self.zoom_steps)
        
        # 执行缩放
        center = self.mapToScene(self.viewport().rect().center())
        self.zoom_at_point(center, step_factor)
        
        # 减少剩余步骤
        self.zoom_steps -= 1
        
        # 如果还有步骤，继续
        if self.zoom_steps > 0:
            self.zoom_timer.start(self.zoom_animation_duration // self.max_zoom_steps)
    
    def smooth_zoom_to(self, target_zoom: float):
        """平滑缩放到目标级别"""
        if not self.smooth_zoom:
            self.set_zoom(target_zoom)
            return
        
        self.target_zoom = target_zoom
        self.zoom_steps = self.max_zoom_steps
        self._smooth_zoom_step()
    
    def get_view_bounds(self) -> tuple:
        """获取当前视图边界"""
        view_rect = self.viewport().rect()
        scene_rect = self.mapToScene(view_rect).boundingRect()
        
        return (
            scene_rect.left(),
            scene_rect.top(),
            scene_rect.right(),
            scene_rect.bottom()
        )
    
    def is_point_visible(self, scene_pos: QPointF) -> bool:
        """检查点是否在当前视图中可见"""
        view_rect = self.viewport().rect()
        scene_rect = self.mapToScene(view_rect).boundingRect()
        return scene_rect.contains(scene_pos)
    
    def get_navigation_info(self) -> dict:
        """获取导航信息"""
        return {
            'zoom': self.get_zoom(),
            'center': self.mapToScene(self.viewport().rect().center()),
            'bounds': self.get_view_bounds(),
            'is_panning': self.is_panning
        }
