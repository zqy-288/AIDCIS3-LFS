"""
基于工件图的全景预览组件
实现可缩放平移的工件二维示意图，支持检测点可视化和状态管理
用于替代复杂的matplotlib全景组件
"""

import math
import logging
from enum import Enum
from typing import Optional, Dict, List
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QGraphicsView, QGraphicsScene, 
                               QGraphicsEllipseItem, QGraphicsTextItem,
                               QGraphicsRectItem, QFrame, QGraphicsLineItem,
                               QGraphicsPathItem)
from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QPainter, QPainterPath

from src.shared.models.hole_data import HoleCollection, HoleStatus
from src.pages.main_detection_p1.graphics.core.sector_types import SectorQuadrant


class SectorHighlight(QGraphicsPathItem):
    """扇形高亮图形项 - 负责绘制扇形高亮区域"""
    
    def __init__(self, center: QPointF, radius: float, sector: SectorQuadrant):
        super().__init__()
        self.center = center
        self.radius = radius
        self.sector = sector
        self.is_highlighted = False
        self._create_sector_path()
        self._setup_appearance()
        
    def _create_sector_path(self):
        """创建扇形路径"""
        path = QPainterPath()
        
        # 根据扇形类型计算起始和结束角度
        start_angle, span_angle = self._get_sector_angles()
        
        # 移动到中心点
        path.moveTo(self.center)
        
        # 创建扇形弧线
        rect = QRectF(self.center.x() - self.radius, self.center.y() - self.radius,
                     self.radius * 2, self.radius * 2)
        path.arcTo(rect, start_angle, span_angle)
        
        # 闭合路径回到中心
        path.lineTo(self.center)
        
        self.setPath(path)
        
    def _get_sector_angles(self):
        """根据扇形类型获取角度范围"""
        # 与 SectorQuadrant.from_angle 保持一致的角度映射
        # 0度=3点钟方向，角度按逆时针增加，但在Qt坐标系Y轴向下
        angle_map = {
            SectorQuadrant.SECTOR_1: (0, 90),      # 0-90度
            SectorQuadrant.SECTOR_2: (90, 90),     # 90-180度  
            SectorQuadrant.SECTOR_3: (180, 90),    # 180-270度
            SectorQuadrant.SECTOR_4: (270, 90),    # 270-360度
        }
        return angle_map.get(self.sector, (0, 90))
        
    def _setup_appearance(self):
        """设置外观"""
        # 初始状态：半透明淡黄色
        normal_color = QColor(255, 255, 150, 30)  # 很淡的黄色
        highlight_color = QColor(255, 255, 150, 100)  # 更明显的黄色
        
        self.normal_brush = QBrush(normal_color)
        self.highlight_brush = QBrush(highlight_color)
        self.highlight_pen = QPen(QColor(255, 255, 150), 2)
        self.normal_pen = QPen(QColor(255, 255, 150, 50), 1)
        
        # 设置初始外观
        self.setBrush(self.normal_brush)
        self.setPen(self.normal_pen)
        self.setVisible(False)  # 默认隐藏
        
    def set_highlighted(self, highlighted: bool):
        """设置高亮状态"""
        self.is_highlighted = highlighted
        if highlighted:
            self.setBrush(self.highlight_brush)
            self.setPen(self.highlight_pen)
            self.setVisible(True)
        else:
            self.setBrush(self.normal_brush)
            self.setPen(self.normal_pen)
            self.setVisible(False)
            
    def update_geometry(self, center: QPointF, radius: float):
        """更新几何信息"""
        if self.center != center or self.radius != radius:
            self.center = center
            self.radius = radius
            self._create_sector_path()


class DetectionPoint(QGraphicsEllipseItem):
    """检测点图形项"""
    
    def __init__(self, hole_id, x, y, radius=6):
        super().__init__(-radius, -radius, radius*2, radius*2)
        self.hole_id = hole_id
        self.status = HoleStatus.PENDING
        self.setPos(x, y)
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable, True)
        self.setCursor(Qt.PointingHandCursor)
        self.original_pen = QPen(QColor(50, 50, 50), 0.5)  # 深灰色边框
        self.highlight_pen = QPen(QColor(255, 255, 150), 3) # 淡黄色高亮
        self.update_appearance()
        
    def update_appearance(self):
        """根据状态更新外观"""
        colors = {
            HoleStatus.PENDING: QColor(200, 200, 200),      # 亮灰色 - 更容易看见
            HoleStatus.PROCESSING: QColor(255, 255, 0),     # 黄色
            HoleStatus.QUALIFIED: QColor(0, 255, 0),        # 绿色
            HoleStatus.DEFECTIVE: QColor(255, 0, 0),        # 红色 - 异常
            HoleStatus.BLIND: QColor(100, 100, 100),        # 中灰色 - 盲孔
            HoleStatus.TIE_ROD: QColor(255, 165, 0),        # 橙色 - 拉杆孔
        }
        
        color = colors.get(self.status, QColor(128, 128, 128))
        self.setBrush(QBrush(color))
        self.setPen(self.original_pen)
        
    def set_highlight(self, highlighted):
        """设置或取消高亮"""
        if highlighted:
            # 淡黄色高亮，增加发光效果
            self.setPen(self.highlight_pen)
            # 添加半透明发光效果
            glow_brush = QBrush(QColor(255, 255, 150, 80))  # 半透明黄色
            self.setBrush(glow_brush)
        else:
            self.setPen(self.original_pen)
            self.update_appearance()  # 恢复原始颜色
        
    def set_status(self, status):
        """设置检测状态"""
        try:
            # 如果status是字符串，尝试转换为枚举
            if isinstance(status, str):
                status_map = {
                    'pending': HoleStatus.PENDING,
                    'qualified': HoleStatus.QUALIFIED,
                    'defective': HoleStatus.DEFECTIVE,
                    'unqualified': HoleStatus.DEFECTIVE,  # 兼容旧数据
                    'blind': HoleStatus.BLIND,
                    'tie_rod': HoleStatus.TIE_ROD,
                    'processing': HoleStatus.PROCESSING,
                }
                self.status = status_map.get(status.lower(), HoleStatus.PENDING)
            else:
                self.status = status
            self.update_appearance()
        except Exception as e:
            # 如果转换失败，使用默认状态
            print(f"Warning: Failed to set status {status}: {e}")
            self.status = HoleStatus.PENDING
            self.update_appearance()
        
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            # 发送点击信号给父组件
            scene = self.scene()
            if hasattr(scene, 'parent_widget'):
                scene.parent_widget.hole_clicked.emit(self.hole_id, self.status)
        super().mousePressEvent(event)


class WorkpiecePanoramaWidget(QWidget):
    """基于工件图的全景预览组件"""
    
    # 信号定义
    hole_clicked = Signal(str, object)  # 孔被点击时发射
    sector_clicked = Signal(SectorQuadrant)  # 扇形点击信号，与原CompletePanoramaWidget兼容
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.detection_points = {}  # 存储所有检测点
        self.highlighted_hole = None
        self.hole_collection = None
        
        # 扇形相关属性
        self.center_point = None  # 全景图中心点
        self.panorama_radius = 0.0  # 全景图半径
        self.sector_lines = []  # 扇形分割线
        self.sector_highlights = {}  # 存储扇形高亮项 {SectorQuadrant: SectorHighlight}
        self.current_highlighted_sector = None  # 当前高亮的扇形
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        
        # 图形视图
        self.graphics_view = QGraphicsView()
        self.graphics_scene = QGraphicsScene()
        self.graphics_scene.parent_widget = self  # 用于信号传递
        self.graphics_view.setScene(self.graphics_scene)
        
        # 设置视图属性
        self.graphics_view.setRenderHint(QPainter.Antialiasing)
        self.graphics_view.setDragMode(QGraphicsView.ScrollHandDrag) # 启用鼠标拖动平移
        self.graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 连接鼠标点击事件
        self.graphics_view.mousePressEvent = self._on_graphics_view_clicked
        
        # 添加鼠标滚轮事件处理
        self.graphics_view.wheelEvent = self._on_wheel_event
        
        # 设置背景色
        self.graphics_view.setStyleSheet("""
            QGraphicsView {
                background-color: #2a2a2a;
                border: 1px solid #555;
                border-radius: 5px;
            }
        """)
        
        layout.addWidget(self.graphics_view)
        
    def _on_graphics_view_clicked(self, event):
        """处理图形视图的鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            # 获取点击在场景中的坐标
            scene_pos = self.graphics_view.mapToScene(event.pos())
            
            # 检查是否点击在扇形区域
            sector = self._get_sector_from_position(scene_pos)
            if sector:
                self.sector_clicked.emit(sector)
                self.logger.info(f"扇形点击: {sector.display_name}")
                
                # 直接高亮选中的扇形
                self.highlight_sector(sector)
        
        # 调用原始的鼠标点击处理（用于拖拽等）
        QGraphicsView.mousePressEvent(self.graphics_view, event)
    
    def _get_sector_from_position(self, pos: QPointF) -> Optional[SectorQuadrant]:
        """根据点击位置确定扇形"""
        if not self.center_point or self.panorama_radius == 0:
            return None
            
        # 计算点击位置相对于中心的向量
        dx = pos.x() - self.center_point.x()
        dy = pos.y() - self.center_point.y()
        
        # 计算距离，如果太远则不在全景图内
        distance = math.sqrt(dx*dx + dy*dy)
        if distance > self.panorama_radius:
            return None
            
        # 计算角度 (Qt坐标系中Y轴向下)
        angle = math.degrees(math.atan2(-dy, dx))  # 注意Y轴翻转
        if angle < 0:
            angle += 360
            
        # 根据角度确定扇形
        return SectorQuadrant.from_angle(angle)
    
    def _on_wheel_event(self, event):
        """处理鼠标滚轮事件进行缩放"""
        # 获取滚轮角度
        angle = event.angleDelta().y()
        
        # 计算缩放因子
        scale_factor = 1.15 if angle > 0 else 0.85
        
        # 获取当前的缩放级别
        current_transform = self.graphics_view.transform()
        current_scale = current_transform.m11()
        
        # 限制缩放范围
        new_scale = current_scale * scale_factor
        if new_scale < 0.1 or new_scale > 10:
            return
        
        # 以鼠标位置为中心进行缩放
        self.graphics_view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.graphics_view.scale(scale_factor, scale_factor)
        
        # 接受事件，防止传递
        event.accept()
    
    def _draw_sector_lines(self):
        """绘制扇形分割线"""
        if not self.center_point or self.panorama_radius == 0:
            return
            
        # 清除旧的分割线 - 安全检查避免访问已删除的Qt对象
        for line in self.sector_lines[:]:  # 创建副本避免在迭代时修改列表
            try:
                if line.scene():
                    self.graphics_scene.removeItem(line)
            except RuntimeError:
                # Qt对象已被删除，忽略此错误
                pass
        self.sector_lines.clear()
        
        # 创建新的分割线
        pen = QPen(QColor(100, 100, 100), 1)  # 灰色分割线
        center_x = self.center_point.x()
        center_y = self.center_point.y()
        radius = self.panorama_radius
        
        # 绘制四条分割线 (每90度一条)
        for angle in [0, 90, 180, 270]:
            radians = math.radians(angle)
            end_x = center_x + radius * math.cos(radians)
            end_y = center_y - radius * math.sin(radians)  # Y轴翻转
            
            line = QGraphicsLineItem(center_x, center_y, end_x, end_y)
            line.setPen(pen)
            self.graphics_scene.addItem(line)
            self.sector_lines.append(line)
        
    def _create_sector_highlights(self):
        """创建扇形高亮项"""
        if not self.center_point or self.panorama_radius == 0:
            return
            
        # 清除旧的高亮项
        for sector, highlight in self.sector_highlights.items():
            try:
                if highlight.scene():
                    self.graphics_scene.removeItem(highlight)
            except RuntimeError:
                # Qt对象已被删除，忽略此错误
                pass
        self.sector_highlights.clear()
        
        # 计算合适的高亮半径 - 基于实际孔位分布范围
        highlight_radius = self.panorama_radius * 0.95  # 缩小到95%，覆盖大部分孔位区域
        
        # 为每个扇形创建高亮项
        for sector in SectorQuadrant:
            highlight = SectorHighlight(self.center_point, highlight_radius, sector)
            self.graphics_scene.addItem(highlight)
            self.sector_highlights[sector] = highlight
            
    def _update_sector_highlights(self):
        """更新扇形高亮几何信息"""
        if not self.center_point or self.panorama_radius == 0:
            return
            
        # 使用与创建时相同的半径计算
        highlight_radius = self.panorama_radius * 0.95
        for sector, highlight in self.sector_highlights.items():
            highlight.update_geometry(self.center_point, highlight_radius)
        
    def load_hole_collection(self, hole_collection: HoleCollection):
        """
        从HoleCollection加载孔位数据
        
        Args:
            hole_collection: 包含孔位数据的集合
        """
        if not hole_collection:
            self.logger.warning("收到空的hole_collection")
            self.show_empty_state()
            return
        
        # 检查是否与当前数据相同，避免重复加载
        hole_count = len(hole_collection) if hole_collection else 0
        if (hasattr(self, 'hole_collection') and self.hole_collection and 
            len(self.hole_collection) == hole_count and hole_count > 0):
            # 进一步检查数据指纹是否相同
            current_holes = list(self.hole_collection.holes.keys())[:5]  # 检查前5个ID
            new_holes = list(hole_collection.holes.keys())[:5]
            if current_holes == new_holes:
                self.logger.info(f"🔍 [全景预览] 数据未变化，跳过重复加载：{hole_count} 个孔位")
                return
            
        # 清除现有内容
        self.graphics_scene.clear()
        self.detection_points.clear()
        self.sector_lines.clear()  # 清除分割线引用，防止访问已删除的Qt对象
        self.hole_collection = hole_collection
        
        # 记录日志
        self.logger.info(f"开始加载 {hole_count} 个孔位到全景预览")
        
        if hole_count == 0:
            self.logger.warning("hole_collection中没有孔位数据")
            self.show_empty_state()
            return
        
        # 计算边界以确定缩放
        min_x = float('inf')
        max_x = float('-inf')
        min_y = float('inf')
        max_y = float('-inf')
        
        # 遍历孔位计算边界
        for hole_id, hole in hole_collection.holes.items():
            x = hole.center_x
            y = hole.center_y
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)
        
        # 计算中心点和缩放因子
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        width = max_x - min_x
        height = max_y - min_y
        
        # 设置全景图中心和半径（用于扇形计算）
        self.center_point = QPointF(center_x, center_y)
        self.panorama_radius = max(width, height) / 2 * 1.1  # 稍大一些确保覆盖所有孔位
        
        # 设置场景大小（添加边距）
        margin = max(width, height) * 0.1
        scene_rect = QRectF(min_x - margin, min_y - margin, 
                           width + 2*margin, height + 2*margin)
        self.graphics_scene.setSceneRect(scene_rect)
        
        # 调试信息
        self.logger.info(f"孔位分布范围: X=[{min_x:.2f}, {max_x:.2f}], Y=[{min_y:.2f}, {max_y:.2f}]")
        self.logger.info(f"场景大小: {scene_rect.width():.2f} x {scene_rect.height():.2f}")
        self.logger.info(f"孔位总数: {hole_count}, 密度: {hole_count/(width*height) if width*height > 0 else 0:.6f} 个/单位面积")
        
        # 创建检测点
        created_count = 0
        for hole_id, hole in hole_collection.holes.items():
            try:
                x = hole.center_x
                y = hole.center_y
                
                # 创建检测点（调整大小以适应全景预览）
                # 动态计算点的大小，根据孔位密度自动调整
                total_area = width * height
                hole_density = hole_count / total_area if total_area > 0 else 0
                # 基础半径 + 根据密度调整（密度越大，点越小）
                base_radius = min(width, height) / 200  # 基础大小
                density_factor = max(0.3, 1 - hole_density * 1000)  # 密度调整因子
                point_radius = max(2, base_radius * density_factor)  # 最小半径为2
                point = DetectionPoint(hole_id, x, y, point_radius)
                created_count += 1
                
                if created_count % 5000 == 0:  # 每5000个点记录一次进度
                    self.logger.info(f"已创建 {created_count} 个检测点...")
                
                # 设置初始状态
                if hasattr(hole, 'status'):
                    try:
                        # 确保状态是HoleStatus枚举类型
                        if isinstance(hole.status, str):
                            # 如果是字符串，尝试转换为枚举
                            status_map = {
                                'pending': HoleStatus.PENDING,
                                'qualified': HoleStatus.QUALIFIED,
                                'defective': HoleStatus.DEFECTIVE,
                                'unqualified': HoleStatus.DEFECTIVE,  # 兼容旧数据
                                'blind': HoleStatus.BLIND,
                                'tie_rod': HoleStatus.TIE_ROD,
                                'processing': HoleStatus.PROCESSING,
                            }
                            status = status_map.get(hole.status.lower(), HoleStatus.PENDING)
                            point.set_status(status)
                        else:
                            point.set_status(hole.status)
                    except Exception as e:
                        self.logger.warning(f"设置孔位 {hole_id} 状态失败 (状态值: {hole.status}, 类型: {type(hole.status)}): {e}, 使用默认状态")
                        point.set_status(HoleStatus.PENDING)
                
                self.graphics_scene.addItem(point)
                self.detection_points[hole_id] = point
                
            except Exception as e:
                self.logger.error(f"创建检测点 {hole_id} 失败: {e}")
                continue
        
        # 适应视图 - 确保孔位可见
        self.graphics_view.fitInView(scene_rect, Qt.KeepAspectRatio)
        
        # 根据孔位数量设置合适的初始缩放级别
        if hole_count > 10000:  # 大量孔位，需要看全局
            # 保持fitInView的缩放，稍微放大一点以便查看
            current_transform = self.graphics_view.transform()
            scale_factor = min(current_transform.m11(), current_transform.m22())
            self.graphics_view.scale(1.2, 1.2)  # 稍微放大20%
        elif hole_count > 1000:  # 中等数量
            self.graphics_view.resetTransform()
            self.graphics_view.scale(0.8, 0.8)
        else:  # 少量孔位，可以放大查看
            self.graphics_view.resetTransform()
            self.graphics_view.scale(1.5, 1.5)
        
        # 绘制扇形分割线
        self._draw_sector_lines()
        
        # 创建扇形高亮项
        self._create_sector_highlights()
        
        # 如果之前有选中的扇形，重新激活高亮
        if self.current_highlighted_sector:
            self.highlight_sector(self.current_highlighted_sector)
        
        self.logger.info(f"成功加载 {len(self.detection_points)} 个检测点到全景预览")
        self.logger.info(f"全景图中心: ({self.center_point.x():.2f}, {self.center_point.y():.2f}), 半径: {self.panorama_radius:.2f}")
        
    def show_empty_state(self):
        """显示空状态"""
        self.graphics_scene.clear()
        self.detection_points.clear()
        self.sector_lines.clear()  # 清除分割线引用，防止访问已删除的Qt对象
        
        # 添加空状态文本
        empty_text = QGraphicsTextItem("请选择产品文件以查看全景图")
        empty_text.setDefaultTextColor(QColor(128, 128, 128))
        font = QFont("Arial", 12)
        empty_text.setFont(font)
        
        # 居中显示
        text_rect = empty_text.boundingRect()
        empty_text.setPos(-text_rect.width()/2, -text_rect.height()/2)
        
        self.graphics_scene.addItem(empty_text)
        self.graphics_scene.setSceneRect(-200, -50, 400, 100)
        
    def show_test_pattern(self):
        """显示测试图案来验证显示是否正常"""
        self.graphics_scene.clear()
        self.detection_points.clear()
        self.sector_lines.clear()  # 清除分割线引用，防止访问已删除的Qt对象
        
        # 添加一些测试圆形
        colors = [QColor(255, 0, 0), QColor(0, 255, 0), QColor(0, 0, 255), QColor(255, 255, 0)]
        for i in range(4):
            x = (i - 1.5) * 50
            y = 0
            test_point = DetectionPoint(f"test_{i}", x, y, 10)
            test_point.setBrush(QBrush(colors[i]))
            self.graphics_scene.addItem(test_point)
            
        # 设置场景范围
        self.graphics_scene.setSceneRect(-150, -50, 300, 100)
        self.graphics_view.fitInView(self.graphics_scene.sceneRect(), Qt.KeepAspectRatio)
        
        self.logger.info("显示测试图案：4个彩色圆点")
        
    def load_complete_view(self, hole_collection: HoleCollection):
        """兼容方法，直接调用load_hole_collection"""
        self.load_hole_collection(hole_collection)
        
    def update_hole_status(self, hole_id: str, status: HoleStatus, color_override=None):
        """更新孔位状态"""
        if hole_id in self.detection_points:
            if color_override is not None:
                # 支持颜色覆盖（用于检测中的蓝色状态）
                self.detection_points[hole_id].setBrush(QBrush(color_override))
            else:
                # 正常状态更新
                self.detection_points[hole_id].set_status(status)
            
    def get_hole_status(self, hole_id):
        """获取指定孔的状态"""
        if hole_id in self.detection_points:
            return self.detection_points[hole_id].status
        return None
        
    def get_all_holes(self):
        """获取所有孔的ID列表"""
        return list(self.detection_points.keys())
        
    def highlight_hole(self, hole_id: str, highlight: bool = True):
        """高亮指定孔位"""
        if hole_id in self.detection_points:
            self.detection_points[hole_id].set_highlight(highlight)
            if highlight:
                self.highlighted_hole = hole_id
            elif self.highlighted_hole == hole_id:
                self.highlighted_hole = None
                
    def clear_all_highlights(self):
        """清除所有高亮"""
        for point in self.detection_points.values():
            point.set_highlight(False)
        self.highlighted_hole = None
        
    def fit_to_view(self):
        """适应视图大小"""
        if self.graphics_scene.items():
            self.graphics_view.fitInView(self.graphics_scene.sceneRect(), Qt.KeepAspectRatio)
            
    def highlight_sector(self, sector: SectorQuadrant):
        """高亮指定扇形（兼容原CompletePanoramaWidget接口）"""
        if sector is None:
            return
            
        self.logger.info(f"高亮扇形: {sector.display_name}")
        self.logger.info(f"当前扇形高亮项数量: {len(self.sector_highlights)}")
        
        # 清除当前高亮
        if self.current_highlighted_sector and self.current_highlighted_sector in self.sector_highlights:
            self.sector_highlights[self.current_highlighted_sector].set_highlighted(False)
            self.logger.info(f"已清除之前的高亮: {self.current_highlighted_sector.display_name}")
        
        # 设置新的高亮
        if sector in self.sector_highlights:
            self.sector_highlights[sector].set_highlighted(True)
            self.current_highlighted_sector = sector
            self.logger.info(f"已设置新高亮: {sector.display_name}")
        else:
            # 如果高亮项不存在，尝试重新创建
            self.logger.warning(f"扇形高亮项不存在，尝试重新创建")
            self._create_sector_highlights()
            if sector in self.sector_highlights:
                self.sector_highlights[sector].set_highlighted(True)
                self.current_highlighted_sector = sector
                self.logger.info(f"重新创建后设置高亮: {sector.display_name}")
            else:
                self.logger.error(f"无法创建扇形高亮项: {sector.display_name}")
        
    def clear_sector_highlight(self):
        """清除扇形高亮（兼容原CompletePanoramaWidget接口）"""
        self.logger.info("清除扇形高亮")
        
        # 清除当前高亮
        if self.current_highlighted_sector and self.current_highlighted_sector in self.sector_highlights:
            self.sector_highlights[self.current_highlighted_sector].set_highlighted(False)
            self.current_highlighted_sector = None
            
    def test_sector_highlights(self):
        """测试扇形高亮功能"""
        if not self.sector_highlights:
            self.logger.warning("扇形高亮项未创建，测试终止")
            return
            
        self.logger.info("开始测试扇形高亮功能...")
        
        # 测试每个扇形高亮
        for sector in SectorQuadrant:
            self.logger.info(f"测试高亮扇形: {sector.display_name}")
            self.highlight_sector(sector)
            
        self.logger.info("扇形高亮测试完成")
        
    def force_highlight_first_sector(self):
        """强制高亮第一个扇形，用于测试"""
        if not self.sector_highlights:
            self._create_sector_highlights()
            
        first_sector = SectorQuadrant.SECTOR_1
        self.logger.info(f"强制高亮第一个扇形: {first_sector.display_name}")
        self.highlight_sector(first_sector)