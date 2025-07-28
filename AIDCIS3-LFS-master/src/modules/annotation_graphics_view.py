"""
自定义图形视图模块
实现支持三种鼠标模式的AnnotationGraphicsView：平移、标注、编辑
"""

import os
from enum import Enum
from typing import List, Optional, Tuple
import tempfile
from datetime import datetime
from PySide6.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
                               QGraphicsRectItem, QGraphicsItem)
from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import (QPen, QBrush, QColor, QPixmap, QCursor, QPainter,
                           QMouseEvent, QWheelEvent, QFont, QFontMetrics)

from .defect_annotation_model import DefectAnnotation


class MouseMode(Enum):
    """鼠标操作模式"""
    PAN = "pan"           # 平移模式
    ANNOTATE = "annotate" # 标注模式
    EDIT = "edit"         # 编辑模式


class AnnotationRectItem(QGraphicsRectItem):
    """可编辑的标注矩形项"""

    def __init__(self, annotation: DefectAnnotation, image_width: int, image_height: int,
                 annotation_id: int = 1, category_manager=None):
        super().__init__()

        self.annotation = annotation
        self.image_width = image_width
        self.image_height = image_height
        self.annotation_id = annotation_id  # 标注编号
        self.category_manager = category_manager  # 缺陷类别管理器

        # 设置外观
        self._setup_appearance()

        # 设置为可选择和可移动
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)

        # 更新矩形位置和大小
        self._update_rect_from_annotation()
        
    def _setup_appearance(self):
        """设置标注框外观"""
        # 根据缺陷类别设置颜色
        if self.category_manager:
            color_str = self.category_manager.get_category_color(self.annotation.defect_class)
        else:
            # 默认颜色
            colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF"]
            color_str = colors[self.annotation.defect_class % len(colors)]

        color = QColor(color_str)

        # 设置边框
        pen = QPen(color, 2)
        pen.setStyle(Qt.SolidLine)
        self.setPen(pen)

        # 设置填充
        brush_color = QColor(color)
        brush_color.setAlpha(50)  # 半透明
        brush = QBrush(brush_color)
        self.setBrush(brush)

    def paint(self, painter: QPainter, option, widget=None):
        """重写paint方法，绘制矩形和文字标签"""
        # 先绘制原始矩形
        super().paint(painter, option, widget)

        # 获取矩形区域
        rect = self.rect()

        # 设置字体
        font = QFont("Arial", 12, QFont.Bold)
        painter.setFont(font)

        # 获取缺陷类别名称
        if self.category_manager:
            category_name = self.category_manager.get_category_name(self.annotation.defect_class)
        else:
            category_name = f"类别{self.annotation.defect_class}"

        # 绘制左上角的标号（白色字体）
        painter.setPen(QPen(QColor(255, 255, 255), 2))  # 白色
        id_text = str(self.annotation_id)

        # 计算文字位置（左上角，稍微偏移）
        id_x = rect.x() + 5
        id_y = rect.y() + 15
        painter.drawText(QPointF(id_x, id_y), id_text)

        # 绘制右上角的缺陷类型
        painter.setPen(QPen(QColor(255, 255, 255), 2))  # 白色

        # 计算文字宽度，用于右对齐
        font_metrics = QFontMetrics(font)
        text_width = font_metrics.horizontalAdvance(category_name)

        # 计算文字位置（右上角，稍微偏移）
        category_x = rect.x() + rect.width() - text_width - 5
        category_y = rect.y() + 15
        painter.drawText(QPointF(category_x, category_y), category_name)

    def _update_rect_from_annotation(self):
        """根据标注数据更新矩形位置和大小"""
        x1, y1, w, h = self.annotation.to_pixel_coords(self.image_width, self.image_height)
        self.setRect(x1, y1, w, h)
        
    def update_annotation_from_rect(self):
        """根据当前矩形位置更新标注数据"""
        rect = self.rect()
        self.annotation = DefectAnnotation.from_pixel_coords(
            defect_class=self.annotation.defect_class,
            x1=rect.x(),
            y1=rect.y(),
            width=rect.width(),
            height=rect.height(),
            image_width=self.image_width,
            image_height=self.image_height
        )
        
    def get_annotation(self) -> DefectAnnotation:
        """获取标注数据"""
        return self.annotation
        
    def set_selected_appearance(self, selected: bool):
        """设置选中状态的外观"""
        if selected:
            pen = self.pen()
            pen.setWidth(3)
            pen.setStyle(Qt.DashLine)
            self.setPen(pen)
        else:
            self._setup_appearance()


class AnnotationGraphicsView(QGraphicsView):
    """支持三种鼠标模式的标注图形视图"""
    
    # 信号定义
    annotation_created = Signal(DefectAnnotation)  # 创建新标注
    annotation_selected = Signal(DefectAnnotation)  # 选中标注
    annotation_modified = Signal(DefectAnnotation)  # 修改标注
    annotation_deleted = Signal(DefectAnnotation)   # 删除标注
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 创建场景
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # 设置视图属性
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 鼠标模式和状态
        self.current_mode = MouseMode.PAN
        self.current_defect_class = 0
        
        # 图像相关
        self.image_item: Optional[QGraphicsPixmapItem] = None
        self.image_width = 0
        self.image_height = 0
        
        # 标注相关
        self.annotation_items: List[AnnotationRectItem] = []
        self.selected_annotation: Optional[AnnotationRectItem] = None
        self.annotation_counter = 0  # 标注计数器
        self.category_manager = None  # 缺陷类别管理器

        # 绘制状态
        self.drawing = False
        self.draw_start_pos: Optional[QPointF] = None
        self.current_draw_rect: Optional[QGraphicsRectItem] = None
        
        # 平移状态
        self.panning = False
        self.last_pan_point: Optional[QPointF] = None
        
        # 缩放限制
        self.min_zoom = 0.1
        self.max_zoom = 10.0
        
    def set_mouse_mode(self, mode: MouseMode):
        """设置鼠标模式"""
        self.current_mode = mode
        
        # 清除当前绘制状态
        self._clear_drawing_state()
        
        # 设置光标
        if mode == MouseMode.PAN:
            self.setCursor(Qt.OpenHandCursor)
        elif mode == MouseMode.ANNOTATE:
            self.setCursor(Qt.CrossCursor)
        elif mode == MouseMode.EDIT:
            self.setCursor(Qt.ArrowCursor)
            
    def set_defect_class(self, defect_class: int):
        """设置当前缺陷类别"""
        self.current_defect_class = defect_class

    def set_category_manager(self, category_manager):
        """设置缺陷类别管理器"""
        self.category_manager = category_manager

    def load_image(self, image_path: str) -> bool:
        """加载图像"""
        try:
            if not os.path.exists(image_path):
                print(f"图像文件不存在: {image_path}")
                return False
                
            # 清除现有内容
            self.clear_scene()
            
            # 加载图像
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                print(f"无法加载图像: {image_path}")
                return False
                
            self.image_width = pixmap.width()
            self.image_height = pixmap.height()
            
            # 添加到场景
            self.image_item = QGraphicsPixmapItem(pixmap)
            self.scene.addItem(self.image_item)
            
            # 设置场景矩形
            self.scene.setSceneRect(self.image_item.boundingRect())
            
            # 适应视图
            self.fit_in_view()
            
            return True
            
        except Exception as e:
            print(f"加载图像时出错: {e}")
            return False
            
    def clear_scene(self):
        """清除场景内容"""
        self.scene.clear()
        self.annotation_items.clear()
        self.selected_annotation = None
        self.image_item = None
        self.image_width = 0
        self.image_height = 0
        self._clear_drawing_state()
        
    def fit_in_view(self):
        """适应视图大小"""
        if self.image_item:
            self.fitInView(self.image_item, Qt.KeepAspectRatio)
            
    def zoom_in(self):
        """放大 - 使用统一接口但保留缩放限制"""
        current_scale = self.transform().m11()
        if current_scale < self.max_zoom:
            self.scale(1.2, 1.2)
            
    def zoom_out(self):
        """缩小 - 使用统一接口但保留缩放限制"""
        current_scale = self.transform().m11()
        if current_scale > self.min_zoom:
            self.scale(0.8, 0.8)
            
    def add_annotation(self, annotation: DefectAnnotation):
        """添加标注"""
        if not self.image_item:
            return

        # 增加标注计数器
        self.annotation_counter += 1

        annotation_item = AnnotationRectItem(
            annotation,
            self.image_width,
            self.image_height,
            self.annotation_counter,  # 标注编号
            self.category_manager     # 类别管理器
        )
        self.scene.addItem(annotation_item)
        self.annotation_items.append(annotation_item)
        
    def remove_annotation(self, annotation_item: AnnotationRectItem):
        """移除标注"""
        if annotation_item in self.annotation_items:
            self.scene.removeItem(annotation_item)
            self.annotation_items.remove(annotation_item)
    
    def save_screenshot(self, file_path=None):
        """保存缺陷标注图的截图"""
        if file_path is None:
            # 生成临时文件路径
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, f"defect_annotation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        
        try:
            # 获取场景矩形
            scene_rect = self.scene.sceneRect()
            
            # 创建pixmap保存场景内容
            pixmap = QPixmap(int(scene_rect.width()), int(scene_rect.height()))
            pixmap.fill(Qt.white)  # 白色背景
            
            # 渲染场景到pixmap
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            self.scene.render(painter, pixmap.rect(), scene_rect)
            painter.end()
            
            # 保存到文件
            pixmap.save(file_path, "PNG")
            print(f"✅ 缺陷标注图截图已保存: {file_path}")
            return file_path
        except Exception as e:
            print(f"❌ 保存缺陷标注图截图失败: {e}")
            return None
            
    def get_annotations(self) -> List[DefectAnnotation]:
        """获取所有标注"""
        annotations = []
        for item in self.annotation_items:
            # 确保标注数据是最新的
            item.update_annotation_from_rect()
            annotations.append(item.get_annotation())
        return annotations
        
    def clear_annotations(self):
        """清除所有标注"""
        for item in self.annotation_items.copy():
            self.remove_annotation(item)
        # 重置标注计数器
        self.annotation_counter = 0
            
    def _clear_drawing_state(self):
        """清除绘制状态"""
        if self.current_draw_rect:
            self.scene.removeItem(self.current_draw_rect)
            self.current_draw_rect = None
        self.drawing = False
        self.draw_start_pos = None
        
    def _start_pan(self, pos: QPointF):
        """开始平移"""
        self.panning = True
        self.last_pan_point = pos
        self.setCursor(Qt.ClosedHandCursor)
        
    def _update_pan(self, pos: QPointF):
        """更新平移"""
        if self.panning and self.last_pan_point:
            delta = pos - self.last_pan_point
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - int(delta.x())
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - int(delta.y())
            )
            self.last_pan_point = pos
            
    def _end_pan(self):
        """结束平移"""
        self.panning = False
        self.setCursor(Qt.OpenHandCursor)
        
    def _start_annotation(self, scene_pos: QPointF):
        """开始标注"""
        if not self.image_item:
            return
            
        self.drawing = True
        self.draw_start_pos = scene_pos
        
        # 创建临时绘制矩形
        self.current_draw_rect = QGraphicsRectItem()
        pen = QPen(QColor(255, 0, 0), 2)
        pen.setStyle(Qt.DashLine)
        self.current_draw_rect.setPen(pen)
        self.scene.addItem(self.current_draw_rect)
        
    def _update_annotation(self, scene_pos: QPointF):
        """更新标注绘制"""
        if self.drawing and self.draw_start_pos and self.current_draw_rect:
            # 计算矩形
            x1 = min(self.draw_start_pos.x(), scene_pos.x())
            y1 = min(self.draw_start_pos.y(), scene_pos.y())
            x2 = max(self.draw_start_pos.x(), scene_pos.x())
            y2 = max(self.draw_start_pos.y(), scene_pos.y())
            
            # 限制在图像范围内
            if self.image_item:
                image_rect = self.image_item.boundingRect()
                x1 = max(image_rect.left(), min(image_rect.right(), x1))
                y1 = max(image_rect.top(), min(image_rect.bottom(), y1))
                x2 = max(image_rect.left(), min(image_rect.right(), x2))
                y2 = max(image_rect.top(), min(image_rect.bottom(), y2))
            
            self.current_draw_rect.setRect(x1, y1, x2 - x1, y2 - y1)
            
    def _finish_annotation(self):
        """完成标注"""
        if (self.drawing and self.current_draw_rect and 
            self.current_draw_rect.rect().width() > 5 and 
            self.current_draw_rect.rect().height() > 5):
            
            # 创建标注数据
            rect = self.current_draw_rect.rect()
            annotation = DefectAnnotation.from_pixel_coords(
                defect_class=self.current_defect_class,
                x1=rect.x(),
                y1=rect.y(),
                width=rect.width(),
                height=rect.height(),
                image_width=self.image_width,
                image_height=self.image_height
            )
            
            # 添加标注
            self.add_annotation(annotation)
            
            # 发送创建信号
            self.annotation_created.emit(annotation)
            
        # 清除绘制状态
        self._clear_drawing_state()
        
    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            scene_pos = self.mapToScene(event.pos())

            if self.current_mode == MouseMode.PAN:
                self._start_pan(event.pos())
            elif self.current_mode == MouseMode.ANNOTATE:
                self._start_annotation(scene_pos)
            elif self.current_mode == MouseMode.EDIT:
                self._handle_edit_press(scene_pos)

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动事件"""
        if self.current_mode == MouseMode.PAN and self.panning:
            self._update_pan(event.pos())
        elif self.current_mode == MouseMode.ANNOTATE and self.drawing:
            scene_pos = self.mapToScene(event.pos())
            self._update_annotation(scene_pos)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            if self.current_mode == MouseMode.PAN:
                self._end_pan()
            elif self.current_mode == MouseMode.ANNOTATE and self.drawing:
                self._finish_annotation()

        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        """键盘按下事件"""
        if event.key() == Qt.Key_Delete and self.selected_annotation:
            # 删除选中的标注
            self.remove_annotation(self.selected_annotation)
        else:
            super().keyPressEvent(event)

    def _handle_edit_press(self, scene_pos: QPointF):
        """处理编辑模式的鼠标按下"""
        # 查找点击位置的标注项
        item = self.scene.itemAt(scene_pos, self.transform())

        if isinstance(item, AnnotationRectItem):
            # 选中标注
            self._select_annotation(item)
        else:
            # 取消选择
            self._select_annotation(None)

    def _select_annotation(self, annotation_item: Optional[AnnotationRectItem]):
        """选择标注"""
        # 取消之前的选择
        if self.selected_annotation:
            self.selected_annotation.set_selected_appearance(False)

        # 设置新选择
        self.selected_annotation = annotation_item

        if self.selected_annotation:
            self.selected_annotation.set_selected_appearance(True)
            self.annotation_selected.emit(self.selected_annotation.get_annotation())

    def wheelEvent(self, event: QWheelEvent):
        """鼠标滚轮事件 - 实现缩放功能"""
        if not self.image_item:
            return

        # 获取滚轮滚动方向
        delta = event.angleDelta().y()

        # 计算缩放因子
        zoom_factor = 1.2 if delta > 0 else 0.8

        # 获取当前缩放级别
        current_scale = self.transform().m11()
        new_scale = current_scale * zoom_factor

        # 限制缩放范围
        if new_scale < self.min_zoom or new_scale > self.max_zoom:
            return

        # 获取鼠标在场景中的位置
        scene_pos = self.mapToScene(event.position().toPoint())

        # 执行缩放
        self.scale(zoom_factor, zoom_factor)

        # 调整视图位置，使鼠标位置保持不变
        view_pos = self.mapFromScene(scene_pos)
        new_scene_pos = self.mapToScene(view_pos)
        delta_pos = scene_pos - new_scene_pos
        self.translate(delta_pos.x(), delta_pos.y())
