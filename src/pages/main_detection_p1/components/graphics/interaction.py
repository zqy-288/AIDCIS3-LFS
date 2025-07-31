"""
交互式选择与悬停功能
实现孔位悬停高亮、信息提示框、点击选择功能
"""

from PySide6.QtWidgets import (QGraphicsView, QToolTip, QRubberBand, 
                               QApplication, QWidget)
from PySide6.QtCore import Qt, QTimer, QRect, QPoint, Signal, QPointF
from PySide6.QtGui import QMouseEvent, QKeyEvent, QPainter, QColor, QCursor

import time
from typing import List, Optional, Set
import logging

from src.core_business.models.hole_data import HoleData, HoleStatus
from .hole_item import HoleGraphicsItem


class InteractionMixin:
    """交互功能混入类"""
    
    # 信号
    hole_selected = Signal(list)  # 孔被选择（孔数据列表）
    hole_hovered = Signal(HoleData)  # 孔被悬停
    selection_changed = Signal(list)  # 选择改变
    hover_timeout = Signal()  # 悬停超时
    
    def __init__(self):
        """初始化交互功能"""
        # 悬停参数
        self.hover_delay = 50  # 悬停延迟（毫秒）
        self.hover_enabled = True
        self.current_hover_item: Optional[HoleGraphicsItem] = None
        self.hover_timer = QTimer()
        self.hover_timer.setSingleShot(True)
        self.hover_timer.timeout.connect(self._on_hover_timeout)
        
        # 选择参数
        self.selection_enabled = True
        self.multi_selection_enabled = True
        self.rubber_band_enabled = True
        self.selected_items: Set[HoleGraphicsItem] = set()
        
        # 提示框参数 - 禁用以避免与HoleGraphicsItem的自定义工具提示冲突
        self.tooltip_enabled = False
        self.tooltip_delay = 500  # 提示框延迟（毫秒）
        self.tooltip_timer = QTimer()
        self.tooltip_timer.setSingleShot(True)
        self.tooltip_timer.timeout.connect(self._show_tooltip)
        self.tooltip_position = QPoint()
        self.tooltip_item: Optional[HoleGraphicsItem] = None
        
        # 框选参数
        self.rubber_band: Optional[QRubberBand] = None
        self.rubber_band_origin = QPoint()
        self.is_rubber_banding = False
        
        # 性能监控
        self.interaction_start_time = 0
        self.max_response_time = 0.1  # 100ms响应时间要求
        
        # 日志
        self.logger = logging.getLogger(__name__)
    
    def setup_interaction(self):
        """设置交互功能"""
        # 启用鼠标跟踪
        self.setMouseTracking(True)
        
        # 设置焦点策略
        self.setFocusPolicy(Qt.StrongFocus)
        
        # 创建橡皮筋选择器
        if self.rubber_band_enabled:
            self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动事件"""
        self.interaction_start_time = time.time()

        if self.is_panning:
            # 执行拖拽平移
            self.update_pan(event.position())
            event.accept()
        elif self.is_rubber_banding:
            # 更新橡皮筋选择
            self._update_rubber_band(event.position().toPoint())
        else:
            # 处理悬停
            self._handle_hover(event.position().toPoint())
            # 调用父类方法
            super().mouseMoveEvent(event)

        # 检查响应时间
        response_time = time.time() - self.interaction_start_time
        if response_time > self.max_response_time:
            self.logger.warning(f"交互响应时间过长: {response_time:.3f}s")
    
    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            # 左键：开始拖拽平移
            self.start_pan(event.position())
            event.accept()
        elif event.button() == Qt.RightButton:
            # 右键：孔位选择
            scene_pos = self.mapToScene(event.position().toPoint())
            hole_item = self._get_hole_at_position(scene_pos)

            if hole_item:
                # 右键点击了孔
                self._handle_hole_click(hole_item, event.modifiers())
            else:
                # 右键点击了空白区域，清除选择
                if not (event.modifiers() & Qt.ControlModifier):
                    self._clear_selection()
            event.accept()
        else:
            # 调用父类方法
            super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            # 结束拖拽平移
            if self.is_panning:
                self.end_pan()
            event.accept()
        elif event.button() == Qt.RightButton:
            # 右键释放，无特殊处理
            event.accept()
        else:
            # 调用父类方法
            super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """鼠标双击事件 - 备选孔位选择方式"""
        if event.button() == Qt.LeftButton:
            # 左键双击：孔位选择（备选方式）
            scene_pos = self.mapToScene(event.position().toPoint())
            hole_item = self._get_hole_at_position(scene_pos)

            if hole_item:
                # 双击了孔
                self._handle_hole_click(hole_item, event.modifiers())
                event.accept()
                return

        # 调用父类方法
        super().mouseDoubleClickEvent(event)

    def leaveEvent(self, event):
        """鼠标离开事件"""
        # 清除悬停状态
        self._clear_hover()
        
        # 不再强制隐藏工具提示，让自定义工具提示自行管理
        # QToolTip.hideText()  # 注释掉以避免隐藏PersistentTooltip
        self.tooltip_timer.stop()
        
        # 调用父类方法
        super().leaveEvent(event)
    
    def keyPressEvent(self, event: QKeyEvent):
        """键盘按下事件"""
        if event.key() == Qt.Key_Escape:
            # ESC键清除选择
            self._clear_selection()
        elif event.key() == Qt.Key_A and event.modifiers() & Qt.ControlModifier:
            # Ctrl+A全选
            self._select_all()
        elif event.key() == Qt.Key_Delete:
            # Delete键删除选择（可选功能）
            self._delete_selected()
        
        # 调用父类方法
        super().keyPressEvent(event)
    
    def _handle_hover(self, mouse_pos: QPoint):
        """处理悬停"""
        if not self.hover_enabled:
            return
        
        # 获取鼠标位置的孔
        scene_pos = self.mapToScene(mouse_pos)
        hole_item = self._get_hole_at_position(scene_pos)
        
        if hole_item != self.current_hover_item:
            # 悬停项改变
            self._clear_hover()
            
            if hole_item:
                self.current_hover_item = hole_item
                
                # 启动悬停定时器
                self.hover_timer.start(self.hover_delay)
                
                # 启动提示框定时器
                if self.tooltip_enabled:
                    self.tooltip_position = mouse_pos
                    self.tooltip_item = hole_item
                    self.tooltip_timer.start(self.tooltip_delay)
    
    def _on_hover_timeout(self):
        """悬停超时处理"""
        if self.current_hover_item:
            # 设置高亮
            self.current_hover_item.set_highlighted(True)
            
            # 发射悬停信号
            self.hole_hovered.emit(self.current_hover_item.hole_data)
            
            # 发射超时信号
            self.hover_timeout.emit()
    
    def _show_tooltip(self):
        """显示提示框"""
        if self.tooltip_item and self.tooltip_enabled:
            tooltip_text = self._create_tooltip_text(self.tooltip_item.hole_data)
            
            # 转换为全局坐标
            global_pos = self.mapToGlobal(self.tooltip_position)
            
            # 显示提示框
            QToolTip.showText(global_pos, tooltip_text, self)
    
    def _create_tooltip_text(self, hole_data: HoleData) -> str:
        """创建提示框文本"""
        return (
            f"孔ID: {hole_data.hole_id}\n"
            f"坐标: ({hole_data.center_x:.3f}, {hole_data.center_y:.3f})\n"
            f"半径: {hole_data.radius:.3f}\n"
            f"状态: {hole_data.status.value}\n"
            f"图层: {hole_data.layer}"
        )
    
    def _clear_hover(self):
        """清除悬停状态"""
        if self.current_hover_item:
            self.current_hover_item.set_highlighted(False)
            self.current_hover_item = None
        
        # 停止定时器
        self.hover_timer.stop()
        self.tooltip_timer.stop()
    
    def _handle_hole_click(self, hole_item: HoleGraphicsItem, modifiers):
        """处理孔点击"""
        if modifiers & Qt.ControlModifier:
            # Ctrl+点击：切换选择状态
            if hole_item in self.selected_items:
                self._deselect_item(hole_item)
            else:
                self._select_item(hole_item, append=True)
        else:
            # 普通点击：单选
            self._select_item(hole_item, append=False)
    
    def _select_item(self, hole_item: HoleGraphicsItem, append: bool = False):
        """选择项目"""
        if not append:
            # 清除之前的选择
            self._clear_selection()
        
        # 添加到选择集合
        self.selected_items.add(hole_item)
        hole_item.set_selected_state(True)
        
        # 发射信号
        self._emit_selection_signals()
    
    def _deselect_item(self, hole_item: HoleGraphicsItem):
        """取消选择项目"""
        if hole_item in self.selected_items:
            self.selected_items.remove(hole_item)
            hole_item.set_selected_state(False)
            
            # 发射信号
            self._emit_selection_signals()
    
    def _clear_selection(self):
        """清除所有选择"""
        for item in self.selected_items:
            item.set_selected_state(False)
        
        self.selected_items.clear()
        
        # 发射信号
        self._emit_selection_signals()
    
    def _select_all(self):
        """全选"""
        if hasattr(self, 'hole_items'):
            self._clear_selection()
            
            for item in self.hole_items.values():
                self.selected_items.add(item)
                item.set_selected_state(True)
            
            # 发射信号
            self._emit_selection_signals()
    
    def _delete_selected(self):
        """删除选择的项目（可选功能）"""
        # 这里可以实现删除逻辑
        # 目前只是清除选择
        self._clear_selection()
    

    
    def _select_items_in_rect(self, rect: QRect):
        """选择矩形内的项目"""
        if not hasattr(self, 'hole_items'):
            return
        
        # 转换为场景坐标
        scene_rect = self.mapToScene(rect).boundingRect()
        
        # 清除之前的选择
        self._clear_selection()
        
        # 查找矩形内的孔
        for item in self.hole_items.values():
            item_rect = item.boundingRect()
            item_center = item_rect.center()
            
            if scene_rect.contains(item_center):
                self.selected_items.add(item)
                item.set_selected_state(True)
        
        # 发射信号
        self._emit_selection_signals()
    
    def _get_hole_at_position(self, scene_pos: QPointF) -> Optional[HoleGraphicsItem]:
        """获取指定位置的孔"""
        if hasattr(self, 'scene'):
            scene = self.scene
            if callable(scene):
                scene = scene()
            
            if scene:
                items = scene.items(scene_pos)
                for item in items:
                    if isinstance(item, HoleGraphicsItem):
                        return item
        
        return None
    
    def _emit_selection_signals(self):
        """发射选择相关信号"""
        selected_holes = [item.hole_data for item in self.selected_items]
        
        self.hole_selected.emit(selected_holes)
        self.selection_changed.emit(selected_holes)
    
    def get_selected_holes(self) -> List[HoleData]:
        """获取选择的孔数据"""
        return [item.hole_data for item in self.selected_items]
    
    def select_holes_by_id(self, hole_ids: List[str]):
        """根据ID选择孔"""
        if not hasattr(self, 'hole_items'):
            return
        
        self._clear_selection()
        
        for hole_id in hole_ids:
            if hole_id in self.hole_items:
                item = self.hole_items[hole_id]
                self.selected_items.add(item)
                item.set_selected_state(True)
        
        # 发射信号
        self._emit_selection_signals()
    
    def get_interaction_stats(self) -> dict:
        """获取交互统计信息"""
        return {
            'selected_count': len(self.selected_items),
            'hover_enabled': self.hover_enabled,
            'selection_enabled': self.selection_enabled,
            'tooltip_enabled': self.tooltip_enabled,
            'current_hover': self.current_hover_item.hole_data.hole_id if self.current_hover_item else None,
            'max_response_time': self.max_response_time
        }
