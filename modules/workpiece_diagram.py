"""
工件示意图组件
实现可缩放平移的工件二维示意图，支持检测点可视化和状态管理
"""

import math
from enum import Enum
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QGraphicsView, QGraphicsScene, 
                               QGraphicsEllipseItem, QGraphicsTextItem,
                               QGraphicsRectItem, QFrame)
from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QPainter


class DetectionStatus(Enum):
    """检测状态枚举"""
    NOT_DETECTED = "not_detected"      # 未检测 - 灰色
    DETECTING = "detecting"            # 正在检测 - 黄色
    QUALIFIED = "qualified"            # 合格 - 绿色
    UNQUALIFIED = "unqualified"        # 不合格 - 红色
    REAL_DATA = "real_data"            # 真实数据 - 橙色


class DetectionPoint(QGraphicsEllipseItem):
    """检测点图形项"""
    
    def __init__(self, hole_id, x, y, radius=8):
        super().__init__(-radius, -radius, radius*2, radius*2)
        self.hole_id = hole_id
        self.status = DetectionStatus.NOT_DETECTED
        self.setPos(x, y)
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable, True)
        self.setCursor(Qt.PointingHandCursor)
        self.original_pen = QPen(QColor(0, 0, 0), 1)
        self.highlight_pen = QPen(QColor(0, 120, 215), 3) # 蓝色高亮
        self.update_appearance()
        
        # 添加文本标签
        self.text_item = QGraphicsTextItem(hole_id)
        self.text_item.setParentItem(self)
        self.text_item.setPos(-len(hole_id)*3, radius + 2)
        font = QFont("Arial", 8)
        self.text_item.setFont(font)
        
    def update_appearance(self):
        """根据状态更新外观"""
        colors = {
            DetectionStatus.NOT_DETECTED: QColor(128, 128, 128),    # 灰色
            DetectionStatus.DETECTING: QColor(255, 255, 0),         # 黄色
            DetectionStatus.QUALIFIED: QColor(0, 255, 0),           # 绿色
            DetectionStatus.UNQUALIFIED: QColor(255, 0, 0),         # 红色
            DetectionStatus.REAL_DATA: QColor(255, 165, 0),       # 橙色
        }
        
        color = colors[self.status]
        self.setBrush(QBrush(color))
        self.setPen(self.original_pen)
        
    def set_highlight(self, highlighted):
        """设置或取消高亮"""
        self.setPen(self.highlight_pen if highlighted else self.original_pen)
        
    def set_status(self, status):
        """设置检测状态"""
        self.status = status
        self.update_appearance()
        
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            # 发送点击信号给父组件
            scene = self.scene()
            if hasattr(scene, 'parent_widget'):
                scene.parent_widget.hole_clicked.emit(self.hole_id, self.status)
        super().mousePressEvent(event)


class WorkpieceDiagram(QWidget):
    """工件示意图组件"""
    
    # 信号定义
    hole_clicked = Signal(str, DetectionStatus)  # 孔被点击时发射
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.detection_points = {}  # 存储所有检测点
        self.highlighted_hole = None
        self.setup_ui()
        self.create_sample_workpiece()
        
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("工件检测示意图")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 5px;")
        layout.addWidget(title_label)
        
        # 图形视图
        self.graphics_view = QGraphicsView()
        self.graphics_scene = QGraphicsScene()
        self.graphics_scene.parent_widget = self  # 用于信号传递
        self.graphics_view.setScene(self.graphics_scene)
        
        # 设置视图属性
        self.graphics_view.setRenderHint(QPainter.Antialiasing)
        self.graphics_view.setDragMode(QGraphicsView.ScrollHandDrag) # 启用鼠标拖动平移
        self.graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        layout.addWidget(self.graphics_view)
        
        # 状态说明
        self.create_status_legend(layout)
        
    def create_status_legend(self, layout):
        """创建状态说明"""
        legend_frame = QFrame()
        legend_frame.setFrameStyle(QFrame.Box)
        legend_layout = QHBoxLayout(legend_frame)
        
        legend_layout.addWidget(QLabel("状态说明:"))
        
        # 状态图例
        statuses = [
            (DetectionStatus.NOT_DETECTED, "未检测", QColor(128, 128, 128)),
            (DetectionStatus.DETECTING, "正在检测", QColor(255, 255, 0)),
            (DetectionStatus.QUALIFIED, "合格", QColor(0, 255, 0)),
            (DetectionStatus.UNQUALIFIED, "不合格", QColor(255, 0, 0)),
            (DetectionStatus.REAL_DATA, "真实数据", QColor(255, 165, 0)),
        ]
        
        for status, text, color in statuses:
            # 创建颜色指示器
            color_label = QLabel()
            color_label.setFixedSize(16, 16)
            color_label.setStyleSheet(f"background-color: {color.name()}; border: 1px solid black;")
            
            text_label = QLabel(text)
            
            legend_layout.addWidget(color_label)
            legend_layout.addWidget(text_label)
            legend_layout.addSpacing(10)
        
        legend_layout.addStretch()
        layout.addWidget(legend_frame)
        
    def create_sample_workpiece(self):
        """创建示例工件（管板）"""
        # 清除现有内容
        self.graphics_scene.clear()
        self.detection_points.clear()
        
        # 绘制工件外框
        workpiece_rect = QRectF(-200, -150, 400, 300)
        rect_item = QGraphicsRectItem(workpiece_rect)
        rect_item.setPen(QPen(QColor(0, 0, 0), 2))
        rect_item.setBrush(QBrush(QColor(240, 240, 240)))
        self.graphics_scene.addItem(rect_item)
        
        # 添加工件标题
        title_item = QGraphicsTextItem("管板工件")
        title_item.setPos(-30, -180)
        font = QFont("Arial", 12, QFont.Bold)
        title_item.setFont(font)
        self.graphics_scene.addItem(title_item)
        
        # 创建检测点网格 (8x6 = 48个孔)
        rows = 6
        cols = 8
        start_x = -140
        start_y = -100
        spacing_x = 40
        spacing_y = 35
        
        hole_count = 1
        for row in range(rows):
            for col in range(cols):
                x = start_x + col * spacing_x
                y = start_y + row * spacing_y
                hole_id = f"H{hole_count:03d}"
                
                # 创建检测点
                point = DetectionPoint(hole_id, x, y)
                self.graphics_scene.addItem(point)
                self.detection_points[hole_id] = point
                
                hole_count += 1
        
        # 设置场景范围
        self.graphics_scene.setSceneRect(-250, -200, 500, 400)

        # 特殊标记H001和H002为真实数据
        self.set_hole_status("H001", DetectionStatus.REAL_DATA)
        self.set_hole_status("H002", DetectionStatus.REAL_DATA)
        
        # 适应视图
        self.graphics_view.fitInView(self.graphics_scene.sceneRect(), Qt.KeepAspectRatio)
        
    def set_hole_status(self, hole_id, status):
        """设置指定孔的状态"""
        if hole_id in self.detection_points:
            self.detection_points[hole_id].set_status(status)
            
    def get_hole_status(self, hole_id):
        """获取指定孔的状态"""
        if hole_id in self.detection_points:
            return self.detection_points[hole_id].status
        return None
        
    def get_all_holes(self):
        """获取所有孔的ID列表"""
        return list(self.detection_points.keys())
        
    def get_holes_by_status(self, status):
        """获取指定状态的所有孔"""
        return [hole_id for hole_id, point in self.detection_points.items() 
                if point.status == status]
                
    def reset_all_holes(self):
        """重置所有孔的状态为未检测"""
        for point in self.detection_points.values():
            point.set_status(DetectionStatus.NOT_DETECTED)
            
    def get_detection_progress(self):
        """获取检测进度统计"""
        total = len(self.detection_points)
        if total == 0:
            return {"total": 0, "completed": 0, "progress": 0.0}
            
        completed = len(self.get_holes_by_status(DetectionStatus.QUALIFIED)) + \
                   len(self.get_holes_by_status(DetectionStatus.UNQUALIFIED))
        
        progress = completed / total * 100
        
        return {
            "total": total,
            "completed": completed,
            "not_detected": len(self.get_holes_by_status(DetectionStatus.NOT_DETECTED)),
            "detecting": len(self.get_holes_by_status(DetectionStatus.DETECTING)),
            "qualified": len(self.get_holes_by_status(DetectionStatus.QUALIFIED)),
            "unqualified": len(self.get_holes_by_status(DetectionStatus.UNQUALIFIED)),
            "real_data": len(self.get_holes_by_status(DetectionStatus.REAL_DATA)),
            "progress": progress
        }

    def highlight_hole(self, hole_id):
        """高亮指定的孔"""
        if self.highlighted_hole:
            self.highlighted_hole.set_highlight(False)

        point = self.detection_points.get(hole_id)
        if point:
            point.set_highlight(True)
            self.highlighted_hole = point

    def center_on_hole(self, hole_id):
        """将视图中心移动到指定的孔上"""
        point = self.detection_points.get(hole_id)
        if point:
            self.graphics_view.centerOn(point.pos())
        
    def zoom_in(self):
        """放大视图"""
        self.graphics_view.scale(1.2, 1.2)
        
    def zoom_out(self):
        """缩小视图"""
        self.graphics_view.scale(0.8, 0.8)
        
    def reset_zoom(self):
        """重置缩放"""
        self.graphics_view.resetTransform()
        self.graphics_view.fitInView(self.graphics_scene.sceneRect(), Qt.KeepAspectRatio)


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    def on_hole_clicked(hole_id, status):
        print(f"点击了孔 {hole_id}, 当前状态: {status}")
    
    # 创建工件示意图
    diagram = WorkpieceDiagram()
    diagram.hole_clicked.connect(on_hole_clicked)
    diagram.show()
    
    # 模拟一些状态变化
    diagram.set_hole_status("H001", DetectionStatus.QUALIFIED)
    diagram.set_hole_status("H002", DetectionStatus.DETECTING)
    diagram.set_hole_status("H003", DetectionStatus.UNQUALIFIED)
    
    sys.exit(app.exec())
