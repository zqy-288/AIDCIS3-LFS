"""
3.2页面 - 缺陷标注工具 (Defect Annotation Tool)
基于PySide6的专业缺陷标注工具，支持图像标注、YOLO格式输出等功能
"""

import os
import json
import glob
from pathlib import Path
from datetime import datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QLabel, QPushButton, QComboBox, QListWidget,
                               QListWidgetItem, QGroupBox, QSplitter, QLineEdit,
                               QTextEdit, QSpinBox, QDoubleSpinBox, QMessageBox,
                               QFileDialog, QGraphicsView, QGraphicsScene,
                               QGraphicsPixmapItem, QGraphicsRectItem,
                               QGraphicsPolygonItem, QGraphicsEllipseItem,
                               QTableWidget, QTableWidgetItem, QButtonGroup)
from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import (QPen, QBrush, QColor, QPixmap, QImage, QPainter,
                           QPolygonF, QPainterPath, QFont, QCursor)


class DefectAnnotation:
    """缺陷标注数据类 - 支持YOLO格式"""

    def __init__(self, defect_class, x_center, y_center, width, height, confidence=1.0):
        self.id = None
        self.defect_class = defect_class    # 缺陷类别ID (0, 1, 2, ...)
        self.x_center = x_center            # 中心点x坐标 (归一化 0-1)
        self.y_center = y_center            # 中心点y坐标 (归一化 0-1)
        self.width = width                  # 宽度 (归一化 0-1)
        self.height = height                # 高度 (归一化 0-1)
        self.confidence = confidence        # 置信度
        self.created_at = datetime.now()

    def to_yolo_format(self):
        """转换为YOLO格式字符串"""
        return f"{self.defect_class} {self.x_center:.6f} {self.y_center:.6f} {self.width:.6f} {self.height:.6f}"

    @classmethod
    def from_yolo_format(cls, yolo_line):
        """从YOLO格式字符串创建标注"""
        parts = yolo_line.strip().split()
        if len(parts) >= 5:
            defect_class = int(parts[0])
            x_center = float(parts[1])
            y_center = float(parts[2])
            width = float(parts[3])
            height = float(parts[4])
            return cls(defect_class, x_center, y_center, width, height)
        return None

    def to_pixel_coords(self, image_width, image_height):
        """转换为像素坐标"""
        x_pixel = self.x_center * image_width
        y_pixel = self.y_center * image_height
        w_pixel = self.width * image_width
        h_pixel = self.height * image_height

        # 计算左上角坐标
        x1 = x_pixel - w_pixel / 2
        y1 = y_pixel - h_pixel / 2

        return x1, y1, w_pixel, h_pixel

    @classmethod
    def from_pixel_coords(cls, defect_class, x1, y1, width, height, image_width, image_height):
        """从像素坐标创建标注"""
        # 转换为归一化坐标
        x_center = (x1 + width / 2) / image_width
        y_center = (y1 + height / 2) / image_height
        norm_width = width / image_width
        norm_height = height / image_height

        return cls(defect_class, x_center, y_center, norm_width, norm_height)


class AnnotationGraphicsView(QGraphicsView):
    """支持三种鼠标模式的标注图形视图"""

    annotation_created = Signal(DefectAnnotation)
    annotation_selected = Signal(object)  # 选中标注框

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        # 设置视图属性
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.NoDrag)  # 默认无拖拽

        # 鼠标模式: 'pan', 'annotate', 'edit'
        self.current_mode = 'pan'
        self.defect_class = 0  # 当前缺陷类别ID

        # 标注相关
        self.current_annotation_rect = None
        self.drawing = False
        self.start_pos = None
        self.annotation_items = []  # 存储所有标注框图形项

        # 图像相关
        self.image_item = None
        self.image_width = 0
        self.image_height = 0

        # 平移相关
        self.last_pan_point = None
        self.panning = False
        
    def set_image(self, image_path):
        """设置要标注的图像"""
        self.scene.clear()
        self.annotation_items = []

        if isinstance(image_path, str) and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            self.image_width = pixmap.width()
            self.image_height = pixmap.height()

            self.image_item = QGraphicsPixmapItem(pixmap)
            self.scene.addItem(self.image_item)
            self.scene.setSceneRect(self.image_item.boundingRect())
            self.fitInView(self.image_item, Qt.KeepAspectRatio)

    def set_mouse_mode(self, mode):
        """设置鼠标模式"""
        self.current_mode = mode
        if mode == 'pan':
            self.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(Qt.OpenHandCursor)
        elif mode == 'annotate':
            self.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(Qt.CrossCursor)
        elif mode == 'edit':
            self.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(Qt.ArrowCursor)

    def set_defect_class(self, defect_class):
        """设置当前缺陷类别"""
        self.defect_class = defect_class
        

        
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            scene_pos = self.mapToScene(event.pos())

            if self.current_mode == 'pan':
                self.start_pan(event.pos())
            elif self.current_mode == 'annotate':
                self.start_annotation(scene_pos)
            elif self.current_mode == 'edit':
                self.start_edit(scene_pos)

        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.current_mode == 'pan' and self.panning:
            self.update_pan(event.pos())
        elif self.current_mode == 'annotate' and self.drawing:
            scene_pos = self.mapToScene(event.pos())
            self.update_annotation(scene_pos)
        elif self.current_mode == 'edit':
            # 编辑模式的移动处理
            pass

        super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            if self.current_mode == 'pan':
                self.end_pan()
            elif self.current_mode == 'annotate' and self.drawing:
                self.finish_annotation()
            elif self.current_mode == 'edit':
                self.end_edit()

        super().mouseReleaseEvent(event)
        
    # 平移模式方法
    def start_pan(self, pos):
        """开始平移"""
        self.panning = True
        self.last_pan_point = pos
        self.setCursor(Qt.ClosedHandCursor)

    def update_pan(self, pos):
        """更新平移"""
        if self.last_pan_point:
            delta = pos - self.last_pan_point
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            self.last_pan_point = pos

    def end_pan(self):
        """结束平移"""
        self.panning = False
        self.setCursor(Qt.OpenHandCursor)

    # 标注模式方法
    def start_annotation(self, scene_pos):
        """开始标注"""
        self.drawing = True
        self.start_pos = scene_pos

        # 创建矩形标注框
        self.current_annotation_rect = QGraphicsRectItem()
        self.current_annotation_rect.setPen(QPen(QColor(255, 0, 0), 2))
        self.current_annotation_rect.setBrush(QBrush(QColor(255, 0, 0, 50)))
        self.scene.addItem(self.current_annotation_rect)
        
    def update_bbox_annotation(self, current_pos):
        """更新边界框标注"""
        if self.current_annotation:
            rect = QRectF(self.start_pos, current_pos).normalized()
            self.current_annotation.setRect(rect)
            
    def add_polygon_point(self, pos):
        """添加多边形点"""
        self.polygon_points.append(pos)
        
        # 绘制点
        point_item = QGraphicsEllipseItem(pos.x()-3, pos.y()-3, 6, 6)
        point_item.setBrush(QBrush(QColor(255, 0, 0)))
        self.scene.addItem(point_item)
        
        # 如果有多个点，绘制线段
        if len(self.polygon_points) > 1:
            prev_pos = self.polygon_points[-2]
            line_item = self.scene.addLine(prev_pos.x(), prev_pos.y(),
                                         pos.x(), pos.y(),
                                         QPen(QColor(255, 0, 0), 2))
                                         
    def finish_polygon_annotation(self):
        """完成多边形标注"""
        if len(self.polygon_points) >= 3:
            # 创建多边形
            polygon = QPolygonF(self.polygon_points)
            polygon_item = QGraphicsPolygonItem(polygon)
            polygon_item.setPen(QPen(QColor(255, 0, 0), 2))
            polygon_item.setBrush(QBrush(QColor(255, 0, 0, 50)))
            self.scene.addItem(polygon_item)
            
            # 转换坐标为列表格式
            coordinates = []
            for point in self.polygon_points:
                coordinates.extend([point.x(), point.y()])
                
            # 创建标注项
            annotation = AnnotationItem('polygon', self.defect_type, coordinates)
            self.annotation_created.emit(annotation)
            
        self.polygon_points = []
        
    def start_ellipse_annotation(self, start_pos):
        """开始椭圆标注"""
        self.drawing = True
        self.start_pos = start_pos
        
        self.current_annotation = QGraphicsEllipseItem()
        self.current_annotation.setPen(QPen(QColor(255, 0, 0), 2))
        self.current_annotation.setBrush(QBrush(QColor(255, 0, 0, 50)))
        self.scene.addItem(self.current_annotation)
        
    def update_ellipse_annotation(self, current_pos):
        """更新椭圆标注"""
        if self.current_annotation:
            rect = QRectF(self.start_pos, current_pos).normalized()
            self.current_annotation.setRect(rect)
            
    def finish_annotation(self):
        """完成标注"""
        if self.current_annotation and self.annotation_mode in ['bbox', 'ellipse']:
            rect = self.current_annotation.rect()
            coordinates = [rect.x(), rect.y(), rect.width(), rect.height()]
            
            annotation = AnnotationItem(self.annotation_mode, self.defect_type, coordinates)
            self.annotation_created.emit(annotation)
            
        self.drawing = False
        self.current_annotation = None


class AnnotationTool(QWidget):
    """缺陷标注工具 - 3.2页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_image_path = None
        self.annotations = []
        self.defect_categories = {
            'crack': '裂纹',
            'corrosion': '腐蚀',
            'pit': '点蚀',
            'scratch': '划痕',
            'deposit': '沉积物',
            'other': '其他'
        }
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("内窥镜图像缺陷审查与标注工具")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)
        
        # 工具栏
        self.create_toolbar(layout)
        
        # 主内容区域
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：图像审查视图
        self.create_image_view(splitter)
        
        # 右侧：标注管理面板
        self.create_annotation_panel(splitter)
        
        # 设置分割器比例
        splitter.setSizes([700, 300])
        layout.addWidget(splitter)
        
    def create_toolbar(self, layout):
        """创建工具栏"""
        toolbar_group = QGroupBox("标注工具")
        toolbar_layout = QHBoxLayout(toolbar_group)
        
        # 加载图像按钮
        self.load_button = QPushButton("加载图像")
        self.load_button.clicked.connect(self.load_image)
        toolbar_layout.addWidget(self.load_button)
        
        # 缺陷类型选择
        toolbar_layout.addWidget(QLabel("缺陷类型:"))
        self.defect_combo = QComboBox()
        for key, value in self.defect_categories.items():
            self.defect_combo.addItem(value, key)
        toolbar_layout.addWidget(self.defect_combo)
        
        # 标注工具按钮
        self.bbox_button = QPushButton("边界框")
        self.bbox_button.setCheckable(True)
        self.bbox_button.clicked.connect(lambda: self.set_annotation_mode('bbox'))
        toolbar_layout.addWidget(self.bbox_button)
        
        self.polygon_button = QPushButton("多边形")
        self.polygon_button.setCheckable(True)
        self.polygon_button.clicked.connect(lambda: self.set_annotation_mode('polygon'))
        toolbar_layout.addWidget(self.polygon_button)
        
        self.ellipse_button = QPushButton("椭圆")
        self.ellipse_button.setCheckable(True)
        self.ellipse_button.clicked.connect(lambda: self.set_annotation_mode('ellipse'))
        toolbar_layout.addWidget(self.ellipse_button)
        
        # 清除和保存按钮
        self.clear_button = QPushButton("清除标注")
        self.clear_button.clicked.connect(self.clear_annotations)
        toolbar_layout.addWidget(self.clear_button)
        
        self.save_button = QPushButton("保存标注")
        self.save_button.clicked.connect(self.save_annotations)
        toolbar_layout.addWidget(self.save_button)
        
        self.export_button = QPushButton("导出COCO")
        self.export_button.clicked.connect(self.export_coco)
        toolbar_layout.addWidget(self.export_button)
        
        toolbar_layout.addStretch()
        layout.addWidget(toolbar_group)
        
    def create_image_view(self, splitter):
        """创建图像审查视图"""
        image_group = QGroupBox("图像审查视图")
        image_layout = QVBoxLayout(image_group)
        
        self.annotation_view = AnnotationGraphicsView()
        self.annotation_view.annotation_created.connect(self.add_annotation)
        image_layout.addWidget(self.annotation_view)
        
        # 缩放控制（删除放大和缩小按钮，改为鼠标滚轮缩放）
        zoom_layout = QHBoxLayout()
        self.reset_zoom_button = QPushButton("重置缩放")
        self.reset_zoom_button.clicked.connect(self.reset_zoom)
        zoom_layout.addWidget(self.reset_zoom_button)

        zoom_layout.addStretch()
        image_layout.addLayout(zoom_layout)
        
        splitter.addWidget(image_group)
        
    def create_annotation_panel(self, splitter):
        """创建标注管理面板"""
        panel_group = QGroupBox("缺陷列表")
        panel_layout = QVBoxLayout(panel_group)
        
        # 标注列表
        self.annotation_list = QListWidget()
        self.annotation_list.itemDoubleClicked.connect(self.edit_annotation)
        panel_layout.addWidget(self.annotation_list)
        
        # 标注详情
        details_group = QGroupBox("标注详情")
        details_layout = QGridLayout(details_group)
        
        details_layout.addWidget(QLabel("类型:"), 0, 0)
        self.detail_type_label = QLabel("--")
        details_layout.addWidget(self.detail_type_label, 0, 1)
        
        details_layout.addWidget(QLabel("缺陷:"), 1, 0)
        self.detail_defect_label = QLabel("--")
        details_layout.addWidget(self.detail_defect_label, 1, 1)
        
        details_layout.addWidget(QLabel("置信度:"), 2, 0)
        self.confidence_spinbox = QDoubleSpinBox()
        self.confidence_spinbox.setRange(0.0, 1.0)
        self.confidence_spinbox.setSingleStep(0.1)
        self.confidence_spinbox.setValue(1.0)
        details_layout.addWidget(self.confidence_spinbox, 2, 1)
        
        panel_layout.addWidget(details_group)
        
        # 删除按钮
        self.delete_button = QPushButton("删除选中")
        self.delete_button.clicked.connect(self.delete_annotation)
        panel_layout.addWidget(self.delete_button)
        
        splitter.addWidget(panel_group)
        
    def load_image(self):
        """加载图像"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图像文件", "", 
            "图像文件 (*.png *.jpg *.jpeg *.bmp *.tiff)"
        )
        
        if file_path:
            self.current_image_path = file_path
            self.annotation_view.set_image(file_path)
            self.clear_annotations()
            
    def set_annotation_mode(self, mode):
        """设置标注模式"""
        # 重置所有按钮状态
        self.bbox_button.setChecked(False)
        self.polygon_button.setChecked(False)
        self.ellipse_button.setChecked(False)
        
        # 设置当前模式
        if mode == 'bbox':
            self.bbox_button.setChecked(True)
        elif mode == 'polygon':
            self.polygon_button.setChecked(True)
        elif mode == 'ellipse':
            self.ellipse_button.setChecked(True)
            
        # 获取当前缺陷类型
        defect_type = self.defect_combo.currentData()
        self.annotation_view.set_annotation_mode(mode, defect_type)
        
    def add_annotation(self, annotation):
        """添加标注"""
        annotation.id = len(self.annotations)
        annotation.confidence = self.confidence_spinbox.value()
        self.annotations.append(annotation)
        
        # 更新列表显示
        defect_name = self.defect_categories.get(annotation.defect_type, annotation.defect_type)
        item_text = f"{annotation.annotation_type} - {defect_name}"
        item = QListWidgetItem(item_text)
        item.setData(Qt.UserRole, annotation.id)
        self.annotation_list.addItem(item)
        
    def delete_annotation(self):
        """删除选中的标注"""
        current_item = self.annotation_list.currentItem()
        if current_item:
            annotation_id = current_item.data(Qt.UserRole)
            # 从列表中移除
            self.annotations = [a for a in self.annotations if a.id != annotation_id]
            # 从界面中移除
            self.annotation_list.takeItem(self.annotation_list.row(current_item))
            
    def clear_annotations(self):
        """清除所有标注"""
        self.annotations = []
        self.annotation_list.clear()
        
    def edit_annotation(self, item):
        """编辑标注"""
        annotation_id = item.data(Qt.UserRole)
        annotation = next((a for a in self.annotations if a.id == annotation_id), None)
        
        if annotation:
            self.detail_type_label.setText(annotation.annotation_type)
            defect_name = self.defect_categories.get(annotation.defect_type, annotation.defect_type)
            self.detail_defect_label.setText(defect_name)
            self.confidence_spinbox.setValue(annotation.confidence)
            
    def save_annotations(self):
        """保存标注数据"""
        if not self.annotations:
            QMessageBox.warning(self, "警告", "没有标注数据可保存")
            return
            
        # 这里可以实现保存到数据库的功能
        QMessageBox.information(self, "信息", f"已保存 {len(self.annotations)} 个标注")
        
    def export_coco(self):
        """导出COCO格式数据"""
        if not self.annotations:
            QMessageBox.warning(self, "警告", "没有标注数据可导出")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存COCO文件", "", "JSON文件 (*.json)"
        )
        
        if file_path:
            coco_data = self.generate_coco_format()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(coco_data, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "成功", "COCO格式数据导出成功")
            
    def generate_coco_format(self):
        """生成COCO格式数据"""
        # COCO格式基本结构
        coco_data = {
            "info": {
                "description": "内窥镜缺陷标注数据",
                "version": "1.0",
                "year": datetime.now().year,
                "contributor": "检测系统",
                "date_created": datetime.now().isoformat()
            },
            "licenses": [],
            "images": [],
            "annotations": [],
            "categories": []
        }
        
        # 添加类别
        for i, (key, value) in enumerate(self.defect_categories.items()):
            coco_data["categories"].append({
                "id": i + 1,
                "name": key,
                "supercategory": "defect"
            })
            
        # 添加图像信息
        if self.current_image_path:
            import os
            coco_data["images"].append({
                "id": 1,
                "width": 800,  # 需要从实际图像获取
                "height": 600,
                "file_name": os.path.basename(self.current_image_path),
                "license": 0,
                "flickr_url": "",
                "coco_url": "",
                "date_captured": datetime.now().isoformat()
            })
            
        # 添加标注
        for annotation in self.annotations:
            category_id = list(self.defect_categories.keys()).index(annotation.defect_type) + 1
            coco_annotation = annotation.to_coco_format(1, category_id)
            if coco_annotation:
                coco_data["annotations"].append(coco_annotation)
                
        return coco_data
        
    def reset_zoom(self):
        """重置缩放"""
        self.annotation_view.resetTransform()
        if self.annotation_view.image_item:
            self.annotation_view.fitInView(self.annotation_view.image_item, Qt.KeepAspectRatio)


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 创建标注工具
    tool = AnnotationTool()
    tool.show()
    
    sys.exit(app.exec())
