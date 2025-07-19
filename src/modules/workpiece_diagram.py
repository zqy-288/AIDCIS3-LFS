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
        self.current_view_mode = "macro"  # 当前视图模式：macro(宏观) 或 micro(微观)
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
        
        # 视图控制栏
        control_frame = QFrame()
        control_frame.setFrameStyle(QFrame.StyledPanel)
        control_layout = QHBoxLayout(control_frame)
        
        # 视图模式按钮
        self.macro_btn = QPushButton("📊 宏观视图")
        self.macro_btn.setCheckable(True)
        self.macro_btn.setChecked(True)
        self.macro_btn.setToolTip("显示整个工件的全貌")
        self.macro_btn.clicked.connect(self.switch_to_macro_view)
        
        self.micro_btn = QPushButton("🔍 微观视图")
        self.micro_btn.setCheckable(True)
        self.micro_btn.setToolTip("显示检测点的详细信息")
        self.micro_btn.clicked.connect(self.switch_to_micro_view)
        
        control_layout.addWidget(self.macro_btn)
        control_layout.addWidget(self.micro_btn)
        control_layout.addStretch()
        
        layout.addWidget(control_frame)
        layout.addWidget(title_label)
        
        # 层级化显示按钮
        self.create_view_controls(layout)
        
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
        
    def create_view_controls(self, layout):
        """创建视图控制按钮"""
        control_frame = QFrame()
        control_frame.setFrameStyle(QFrame.Box)
        control_layout = QHBoxLayout(control_frame)
        
        # 视图模式标签
        view_label = QLabel("视图模式:")
        view_label.setFont(QFont("Arial", 9, QFont.Bold))
        control_layout.addWidget(view_label)
        
        # 宏观区域视图按钮
        self.macro_view_btn = QPushButton("宏观区域视图")
        self.macro_view_btn.setCheckable(True)
        self.macro_view_btn.setChecked(True)  # 默认选中
        self.macro_view_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ECC71;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #45a049;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.macro_view_btn.clicked.connect(self.switch_to_macro_view)
        control_layout.addWidget(self.macro_view_btn)
        
        # 微观管孔视图按钮
        self.micro_view_btn = QPushButton("微观管孔视图")
        self.micro_view_btn.setCheckable(True)
        self.micro_view_btn.setStyleSheet("""
            QPushButton {
                background-color: #007ACC;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #1976D2;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.micro_view_btn.clicked.connect(self.switch_to_micro_view)
        control_layout.addWidget(self.micro_view_btn)
        
        # 添加分隔符
        control_layout.addSpacing(20)
        
        # 缩放控制按钮
        zoom_in_btn = QPushButton("放大")
        zoom_in_btn.clicked.connect(self.zoom_in)
        control_layout.addWidget(zoom_in_btn)
        
        zoom_out_btn = QPushButton("缩小")
        zoom_out_btn.clicked.connect(self.zoom_out)
        control_layout.addWidget(zoom_out_btn)
        
        reset_btn = QPushButton("重置")
        reset_btn.clicked.connect(self.reset_zoom)
        control_layout.addWidget(reset_btn)
        
        control_layout.addStretch()
        layout.addWidget(control_frame)
        
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
        
    def switch_to_macro_view(self):
        """切换到宏观区域视图"""
        self.current_view_mode = "macro"
        self.macro_btn.setChecked(True)
        self.micro_btn.setChecked(False)
        
        # 更新显示模式
        self.update_view_display()
        
        # 适应视图显示全部内容
        self.graphics_view.fitInView(self.graphics_scene.sceneRect(), Qt.KeepAspectRatio)
        
    def switch_to_micro_view(self):
        """切换到微观管孔视图"""
        self.current_view_mode = "micro"
        self.micro_btn.setChecked(True)
        self.macro_btn.setChecked(False)
        
        # 更新显示模式
        self.update_view_display()
        
        # 放大到详细视图
        self.graphics_view.scale(2.0, 2.0)
        
        
    def update_view_display(self):
        """根据当前视图模式更新显示"""
        if self.current_view_mode == "macro":
            # 宏观视图：显示整体区域分布
            for hole_id, point in self.detection_points.items():
                # 显示所有检测点
                point.setVisible(True)
                # 设置较小的点大小以显示更多信息
                if hasattr(point, 'text_item'):
                    point.text_item.setVisible(True)
                # 调整点的大小适合宏观视图
                rect = point.rect()
                if rect.width() > 10:  # 如果点太大，缩小它
                    point.setRect(-6, -6, 12, 12)
                    
        elif self.current_view_mode == "micro":
            # 微观视图：显示详细的管孔信息
            for hole_id, point in self.detection_points.items():
                # 显示所有检测点
                point.setVisible(True)
                # 显示详细信息
                if hasattr(point, 'text_item'):
                    point.text_item.setVisible(True)
                # 调整点的大小适合微观视图
                rect = point.rect()
                if rect.width() < 16:  # 如果点太小，放大它
                    point.setRect(-8, -8, 16, 16)
                    
        # 刷新视图
        self.graphics_scene.update()

    def load_product_data(self, product_obj, dxf_file_path=None):
        """加载产品数据并更新工件图显示
        
        Args:
            product_obj: 产品对象，包含产品信息
            dxf_file_path: DXF文件路径（可选）
        """
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"开始加载产品数据: {product_obj.model_name if product_obj else 'Unknown'}")
            
            # 清除现有数据
            self.clear_workpiece_data()
            
            if product_obj:
                # 更新产品信息显示
                self.current_product = product_obj
                logger.info(f"产品信息: 直径={product_obj.standard_diameter}mm, 公差={product_obj.tolerance_range}")
                
                # 如果有DXF文件，解析并加载孔位数据
                if dxf_file_path and self.load_dxf_file(dxf_file_path):
                    logger.info(f"DXF文件加载成功: {dxf_file_path}")
                else:
                    # 如果没有DXF文件，生成示例工件
                    logger.info("生成示例工件数据")
                    self.create_sample_workpiece_for_product(product_obj)
                    
            else:
                # 回退到默认示例工件
                logger.info("使用默认示例工件")
                self.create_sample_workpiece()
                
            # 刷新显示
            self.update_view_display()
            logger.info("产品数据加载完成")
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"加载产品数据失败: {e}")
            # 回退到示例工件
            self.create_sample_workpiece()
    
    def load_dxf_file(self, dxf_file_path):
        """加载DXF文件并解析孔位数据
        
        Args:
            dxf_file_path: DXF文件路径
            
        Returns:
            bool: 加载是否成功
        """
        try:
            import os
            import logging
            logger = logging.getLogger(__name__)
            
            if not os.path.exists(dxf_file_path):
                logger.warning(f"DXF文件不存在: {dxf_file_path}")
                return False
                
            logger.info(f"开始解析DXF文件: {dxf_file_path}")
            
            # 尝试导入DXF解析器
            try:
                from ..core_business.dxf_parser import DXFParser
                parser = DXFParser()
                hole_collection = parser.parse_file(dxf_file_path)
                
                if hole_collection and hole_collection.holes:
                    self.load_hole_collection(hole_collection)
                    logger.info(f"成功加载 {len(hole_collection.holes)} 个孔位")
                    return True
                else:
                    logger.warning("DXF文件中未找到孔位数据")
                    return False
                    
            except ImportError as e:
                logger.warning(f"无法导入DXF解析器: {e}")
                return False
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"DXF文件加载失败: {e}")
            return False
    
    def load_hole_collection(self, hole_collection):
        """从HoleCollection加载孔位数据
        
        Args:
            hole_collection: 孔位数据集合
        """
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            # 清除现有检测点
            self.graphics_scene.clear()
            self.detection_points.clear()
            
            # 计算合适的显示区域
            min_x = min_y = float('inf')
            max_x = max_y = float('-inf')
            
            for hole in hole_collection.holes:
                min_x = min(min_x, hole.x)
                max_x = max(max_x, hole.x)
                min_y = min(min_y, hole.y)
                max_y = max(max_y, hole.y)
            
            # 添加边距
            margin = 50
            width = max_x - min_x + 2 * margin
            height = max_y - min_y + 2 * margin
            
            # 绘制工件轮廓（矩形）
            from PySide6.QtGui import QPen, QBrush, QColor
            outline_pen = QPen(QColor(100, 100, 100), 2)
            outline_brush = QBrush(QColor(240, 240, 240))
            
            workpiece_rect = self.graphics_scene.addRect(
                min_x - margin, min_y - margin, width, height,
                outline_pen, outline_brush
            )
            
            # 添加检测点
            for hole in hole_collection.holes:
                # 转换坐标系（DXF坐标可能需要调整）
                display_x = hole.x
                display_y = -hole.y  # 反转Y轴以适应显示坐标系
                
                # 创建检测点
                point = DetectionPoint(hole.hole_id, display_x, display_y, radius=8)
                
                # 根据孔位状态设置初始状态
                if hasattr(hole, 'status') and hole.status:
                    # 将HoleStatus转换为DetectionStatus
                    status_map = {
                        'not_detected': DetectionStatus.NOT_DETECTED,
                        'qualified': DetectionStatus.QUALIFIED,
                        'unqualified': DetectionStatus.UNQUALIFIED,
                        'detecting': DetectionStatus.DETECTING,
                        'real_data': DetectionStatus.REAL_DATA
                    }
                    status = status_map.get(hole.status.value, DetectionStatus.NOT_DETECTED)
                    point.set_status(status)
                
                self.graphics_scene.addItem(point)
                self.detection_points[hole.hole_id] = point
            
            # 设置场景矩形
            self.graphics_scene.setSceneRect(min_x - margin, min_y - margin, width, height)
            
            # 将视图调整到适合所有内容
            self.graphics_view.fitInView(self.graphics_scene.sceneRect(), Qt.KeepAspectRatio)
            
            logger.info(f"成功加载 {len(hole_collection.holes)} 个孔位到图形显示")
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"加载孔位集合失败: {e}")
    
    def create_sample_workpiece_for_product(self, product_obj):
        """为特定产品创建示例工件
        
        Args:
            product_obj: 产品对象
        """
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"为产品 {product_obj.model_name} 生成示例工件")
            
            # 清除现有内容
            self.graphics_scene.clear()
            self.detection_points.clear()
            
            # 根据产品信息调整工件参数
            sector_count = getattr(product_obj, 'sector_count', 4)
            hole_diameter = getattr(product_obj, 'standard_diameter', 17.730)
            
            # 生成基于产品参数的孔位布局
            from PySide6.QtGui import QPen, QBrush, QColor
            
            # 工件尺寸（基于孔径调整）
            workpiece_radius = max(200, hole_diameter * 8)  
            
            # 绘制工件轮廓（圆形管板）
            outline_pen = QPen(QColor(100, 100, 100), 3)
            outline_brush = QBrush(QColor(245, 245, 245))
            
            self.graphics_scene.addEllipse(
                -workpiece_radius, -workpiece_radius, 
                workpiece_radius * 2, workpiece_radius * 2,
                outline_pen, outline_brush
            )
            
            # 根据扇形数量生成孔位
            holes_per_ring = [8, 16, 24, 32]  # 不同环的孔数
            ring_radii = [60, 120, 180, 240]  # 不同环的半径
            
            hole_count = 0
            for ring_idx, (count, radius) in enumerate(zip(holes_per_ring, ring_radii)):
                if radius > workpiece_radius - 30:  # 确保孔不超出工件边界
                    break
                    
                for i in range(count):
                    angle = (2 * math.pi * i) / count
                    x = radius * math.cos(angle)
                    y = radius * math.sin(angle)
                    
                    hole_count += 1
                    hole_id = f"{product_obj.model_code or 'P'}{hole_count:03d}"
                    
                    # 创建检测点，尺寸基于孔径
                    point_radius = max(6, hole_diameter / 3)
                    point = DetectionPoint(hole_id, x, y, radius=point_radius)
                    
                    self.graphics_scene.addItem(point)
                    self.detection_points[hole_id] = point
            
            # 设置场景范围
            scene_size = workpiece_radius + 50
            self.graphics_scene.setSceneRect(-scene_size, -scene_size, scene_size * 2, scene_size * 2)
            
            # 调整视图
            self.graphics_view.fitInView(self.graphics_scene.sceneRect(), Qt.KeepAspectRatio)
            
            logger.info(f"为产品 {product_obj.model_name} 生成了 {hole_count} 个示例孔位")
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"生成产品示例工件失败: {e}")
            # 回退到默认示例
            self.create_sample_workpiece()
    
    def clear_workpiece_data(self):
        """清除当前工件数据"""
        self.graphics_scene.clear()
        self.detection_points.clear()
        self.highlighted_hole = None
        self.current_product = None
    
    def get_current_product(self):
        """获取当前产品对象"""
        return getattr(self, 'current_product', None)


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
