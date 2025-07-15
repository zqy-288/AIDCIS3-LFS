"""
扇形进度可视化组件
实现扇形区域的图形显示和进度指示
"""

import math
from typing import Dict, Optional
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QGraphicsView, QGraphicsScene, 
                               QGraphicsEllipseItem, QGraphicsTextItem,
                               QGraphicsPathItem, QSizePolicy)
from PySide6.QtCore import Qt, QRectF, QPointF, Signal
from PySide6.QtGui import (QPen, QBrush, QColor, QFont, QPainter, QPainterPath,
                          QRadialGradient, QConicalGradient)

# AI员工3号修改开始
from aidcis2.graphics.sector_manager import SectorManager, SectorQuadrant, SectorProgress
import re  # 用于孔位ID格式验证和转换
# AI员工3号修改结束


class SectorGraphicsItem(QGraphicsPathItem):
    """扇形图形项"""
    
    def __init__(self, sector: SectorQuadrant, center: QPointF, radius: float, parent=None):
        super().__init__(parent)
        self.sector = sector
        self.center = center
        self.radius = radius
        self.progress = 0.0
        self.sector_color = QColor(255, 182, 193)  # 默认淡粉色
        
        # 设置扇形角度范围
        self.start_angle = self._get_start_angle()
        self.span_angle = 90  # 每个扇形90度
        
        self.setFlag(QGraphicsPathItem.ItemIsSelectable, True)
        self.setCursor(Qt.PointingHandCursor)
        
        self._create_sector_path()
        self._update_appearance()
        
        # 添加文本标签
        self.text_item = QGraphicsTextItem(self._get_sector_name())
        self.text_item.setParentItem(self)
        self._position_text_label()
    
    def _get_start_angle(self) -> float:
        """获取扇形起始角度
        
        调整角度以匹配实际的管板坐标系统：
        - 区域1：右上角 (0°-90°)
        - 区域2：左上角 (90°-180°) 
        - 区域3：左下角 (180°-270°)
        - 区域4：右下角 (270°-360°)
        
        Qt坐标系中，0度从正右方开始，顺时针增加
        """
        angle_map = {
            SectorQuadrant.SECTOR_1: 0,     # 右上角：从正右方开始 (0°-90°)
            SectorQuadrant.SECTOR_2: 90,    # 左上角：从正上方开始 (90°-180°)
            SectorQuadrant.SECTOR_3: 180,   # 左下角：从正左方开始 (180°-270°)
            SectorQuadrant.SECTOR_4: 270    # 右下角：从正下方开始 (270°-360°)
        }
        return angle_map[self.sector]
    
    def _get_sector_name(self) -> str:
        """获取扇形区域名称"""
        name_map = {
            SectorQuadrant.SECTOR_1: "区域1",
            SectorQuadrant.SECTOR_2: "区域2", 
            SectorQuadrant.SECTOR_3: "区域3",
            SectorQuadrant.SECTOR_4: "区域4"
        }
        return name_map[self.sector]
    
    def _create_sector_path(self):
        """创建扇形路径"""
        path = QPainterPath()
        
        # 移动到中心点
        path.moveTo(self.center)
        
        # 创建扇形路径
        rect = QRectF(
            self.center.x() - self.radius,
            self.center.y() - self.radius,
            self.radius * 2,
            self.radius * 2
        )
        
        # 添加扇形弧线
        path.arcTo(rect, self.start_angle, self.span_angle)
        
        # 连接回中心点
        path.lineTo(self.center)
        
        self.setPath(path)
    
    def _update_appearance(self):
        """更新外观"""
        # 基础颜色
        base_color = self.sector_color
        
        # 根据进度调整透明度和亮度
        alpha = max(50, min(255, int(50 + self.progress * 2.05)))  # 50-255
        progress_color = QColor(base_color)
        progress_color.setAlpha(alpha)
        
        # 设置画刷和画笔
        self.setBrush(QBrush(progress_color))
        
        pen_color = base_color.darker(150)
        self.setPen(QPen(pen_color, 0.5))  # 进一步缩小边框宽度
    
    def _position_text_label(self):
        """定位文本标签"""
        # 计算标签位置（扇形中心）
        angle_rad = math.radians(self.start_angle + self.span_angle / 2)
        label_radius = self.radius * 0.5  # 调整标签位置，让文字更靠近中心

        x = self.center.x() + label_radius * math.cos(angle_rad)
        y = self.center.y() + label_radius * math.sin(angle_rad)

        # 调整文本位置以居中
        font = QFont("Arial", 4, QFont.Bold)  # 调整为4大小，保证可读性
        self.text_item.setFont(font)

        text_rect = self.text_item.boundingRect()
        self.text_item.setPos(
            x - text_rect.width() / 2,
            y - text_rect.height() / 2
        )

        # 设置文本颜色
        self.text_item.setDefaultTextColor(QColor(255, 255, 255))
        
        # 确保文字在最顶层
        self.text_item.setZValue(1000)
    
    def update_progress(self, progress: SectorProgress):
        """更新进度显示"""
        self.progress = progress.progress_percentage
        self.sector_color = progress.status_color
        
        # 更新外观
        self._update_appearance()
        
        # 更新文本内容
        progress_text = f"{self._get_sector_name()}\n{self.progress:.1f}%"
        self.text_item.setPlainText(progress_text)
        
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            # 发送扇形选择信号
            scene = self.scene()
            if hasattr(scene, 'parent_widget'):
                scene.parent_widget.sector_selected.emit(self.sector)
        super().mousePressEvent(event)


class SectorOverviewWidget(QWidget):
    """扇形概览组件（主要显示区域）"""
    
    sector_selected = Signal(SectorQuadrant)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sector_manager: Optional[SectorManager] = None
        self.sector_items: Dict[SectorQuadrant, SectorGraphicsItem] = {}
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置用户界面"""
        # 移除固定大小限制，让父组件控制大小
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(245, 245, 245, 0.95);
                border: 2px solid #ddd;
                border-radius: 12px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 标题
        title_label = QLabel("区域划分进度")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 14px;
                font-weight: bold;
                background: transparent;
                border: none;
                padding: 4px;
            }
        """)
        layout.addWidget(title_label)
        
        # 图形视图
        self.graphics_view = QGraphicsView()
        self.graphics_view.setStyleSheet("background: transparent; border: none;")
        self.graphics_view.setRenderHint(QPainter.Antialiasing)
        self.graphics_view.setFrameShape(QFrame.NoFrame)
        self.graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.graphics_scene = QGraphicsScene()
        self.graphics_scene.parent_widget = self  # 用于信号传递
        self.graphics_view.setScene(self.graphics_scene)
        
        layout.addWidget(self.graphics_view)
        
        # 整体统计信息
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.8);
                border: 1px solid #ccc;
                border-radius: 6px;
                padding: 5px;
            }
        """)
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setContentsMargins(5, 5, 5, 5)
        
        self.overall_progress_label = QLabel("整体进度: 0%")
        self.overall_qualified_label = QLabel("整体合格率: 0%")
        
        for label in [self.overall_progress_label, self.overall_qualified_label]:
            label.setFont(QFont("Arial", 11, QFont.Bold))
            # 使用主题管理器的颜色
            try:
                from modules.theme_manager import theme_manager
                colors = theme_manager.COLORS
                label.setStyleSheet(f"background: transparent; border: none; color: {colors['text_disabled']};")
            except ImportError:
                label.setStyleSheet("background: transparent; border: none; color: #555;")
            stats_layout.addWidget(label)
        
        layout.addWidget(stats_frame)
        
        # 创建扇形图形项
        self._create_sector_items()
    
    def _create_sector_items(self):
        """创建扇形图形项"""
        center = QPointF(0, 0)
        radius = 6  # 再次减小半径使扇形更紧凑，适应容器大小

        for sector in SectorQuadrant:
            item = SectorGraphicsItem(sector, center, radius)
            self.sector_items[sector] = item
            self.graphics_scene.addItem(item)

        # 获取所有项的实际边界
        items_rect = self.graphics_scene.itemsBoundingRect()
        
        # 设置场景范围 - 基于实际项边界并添加适当边距
        margin = 3  # 减小边距以更紧凑的显示
        scene_rect = items_rect.adjusted(-margin, -margin, margin, margin)
        self.graphics_scene.setSceneRect(scene_rect)
        
        # 设置视图的最小大小以确保能完整显示
        min_size = max(scene_rect.width(), scene_rect.height()) + 3
        self.graphics_view.setMinimumSize(int(min_size), int(min_size))
        
        # 适应视图 - 使用稍微缩小的比例以确保完整显示
        self.graphics_view.fitInView(scene_rect, Qt.KeepAspectRatio)
        self.graphics_view.scale(0.6, 0.6)  # 进一步缩小以确保完整显示所有饼图
    
    def set_sector_manager(self, sector_manager: SectorManager):
        """设置扇形管理器"""
        self.sector_manager = sector_manager
        
        # 连接信号
        if sector_manager:
            sector_manager.sector_progress_updated.connect(self.update_sector_progress)
            sector_manager.overall_progress_updated.connect(self.update_overall_display)
    
    def update_sector_progress(self, sector: SectorQuadrant, progress: SectorProgress):
        """更新扇形进度显示"""
        if sector in self.sector_items:
            self.sector_items[sector].update_progress(progress)
    
    def update_overall_display(self, overall_stats: dict):
        """更新整体显示"""
        total = overall_stats.get('total_holes', 0)
        completed = overall_stats.get('completed_holes', 0)
        qualified = overall_stats.get('qualified_holes', 0)
        
        if total > 0:
            overall_progress = (completed / total) * 100
            self.overall_progress_label.setText(f"整体进度: {overall_progress:.1f}%")
            
            if completed > 0:
                qualification_rate = (qualified / completed) * 100
                self.overall_qualified_label.setText(f"整体合格率: {qualification_rate:.1f}%")
            else:
                self.overall_qualified_label.setText("整体合格率: 0%")
        else:
            self.overall_progress_label.setText("整体进度: 0%")
            self.overall_qualified_label.setText("整体合格率: 0%")
    
    def resizeEvent(self, event):
        """处理大小变化事件"""
        super().resizeEvent(event)
        # 重新适应视图
        if hasattr(self, 'graphics_view') and hasattr(self, 'graphics_scene'):
            # 保持扇形图居中并完整显示
            scene_rect = self.graphics_scene.sceneRect()
            self.graphics_view.resetTransform()  # 重置变换
            self.graphics_view.fitInView(scene_rect, Qt.KeepAspectRatio)
            self.graphics_view.scale(0.6, 0.6)  # 保持一致的缩放比例


class SectorDetailView(QWidget):
    """扇形详细视图（主预览区）"""
    
    # AI员工3号修改开始 - 孔位ID格式验证和转换支持
    @staticmethod
    def validate_new_hole_id_format(hole_id: str) -> bool:
        """验证孔位ID是否符合新格式 C{col:03d}R{row:03d}"""
        pattern = r'^C\d{3}R\d{3}$'
        return bool(re.match(pattern, hole_id))
    
    @staticmethod
    def format_hole_id_for_display(hole_id: str) -> str:
        """格式化孔位ID用于显示，优先显示新格式"""
        # 如果已经是新格式，直接返回
        if SectorDetailView.validate_new_hole_id_format(hole_id):
            return hole_id
        
        # 其他格式保持原样，但添加标识
        if re.match(r'^H\d+$', hole_id):
            return f"{hole_id}(旧)"
        
        return hole_id
    # AI员工3号修改结束
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sector_manager: Optional[SectorManager] = None
        self.current_sector: Optional[SectorQuadrant] = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        
        # 标题栏 - 紧凑版
        title_frame = QFrame()
        title_frame.setFrameStyle(QFrame.StyledPanel)
        title_frame.setMaximumHeight(25)
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(2, 2, 2, 2)
        
        self.sector_title_label = QLabel("区域详情")
        self.sector_title_label.setFont(QFont("Arial", 9, QFont.Bold))
        title_layout.addWidget(self.sector_title_label)
        
        self.progress_label = QLabel("进度: 0%")
        self.progress_label.setFont(QFont("Arial", 8))
        title_layout.addWidget(self.progress_label)
        
        title_layout.addStretch()
        layout.addWidget(title_frame)
        
        # 统计信息面板 - 紧凑版
        stats_frame = QFrame()
        stats_frame.setFrameStyle(QFrame.StyledPanel)
        stats_frame.setMaximumHeight(50)
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setContentsMargins(2, 2, 2, 2)
        stats_layout.setSpacing(2)
        
        # 创建统计标签 - 使用更小字体
        self.total_label = QLabel("总数: 0")
        self.completed_label = QLabel("完成: 0") 
        self.qualified_label = QLabel("合格: 0")
        self.defective_label = QLabel("异常: 0")
        
        for label in [self.total_label, self.completed_label, self.qualified_label, self.defective_label]:
            label.setFont(QFont("Arial", 8))
            label.setStyleSheet("padding: 2px; margin: 1px;")
            stats_layout.addWidget(label)
        
        layout.addWidget(stats_frame)
        
        # 简化信息显示 - 增加高度以显示完整内容
        self.hole_list_widget = QLabel("点击扇形区域查看详情")
        self.hole_list_widget.setAlignment(Qt.AlignCenter)
        self.hole_list_widget.setFont(QFont("Arial", 9))  # 稍微增大字体
        # 使用主题管理器的颜色
        try:
            from modules.theme_manager import theme_manager
            colors = theme_manager.COLORS
            self.hole_list_widget.setStyleSheet(f"border: 1px solid {colors['border_normal']}; padding: 8px; color: {colors['text_disabled']};")
        except ImportError:
            self.hole_list_widget.setStyleSheet("border: 1px solid #ccc; padding: 8px; color: #666;")
        self.hole_list_widget.setMaximumHeight(60)  # 增加高度以显示更多内容
        self.hole_list_widget.setWordWrap(True)  # 允许文字换行
        layout.addWidget(self.hole_list_widget)
    
    def set_sector_manager(self, sector_manager: SectorManager):
        """设置扇形管理器"""
        self.sector_manager = sector_manager
        
        # 连接信号
        if sector_manager:
            sector_manager.sector_progress_updated.connect(self.update_sector_display)
    
    def show_sector_detail(self, sector: SectorQuadrant):
        """显示指定扇形的详细信息"""
        self.current_sector = sector
        
        if self.sector_manager:
            progress = self.sector_manager.get_sector_progress(sector)
            if progress:
                self.update_sector_display(sector, progress)
                
                # 获取该扇形的孔位列表
                holes = self.sector_manager.get_sector_holes(sector)
                self._display_hole_list(holes)
    
    def update_sector_display(self, sector: SectorQuadrant, progress: SectorProgress):
        """更新扇形显示"""
        if sector != self.current_sector:
            return
        
        # 更新标题和进度
        sector_names = {
            SectorQuadrant.SECTOR_1: "区域1 (右上)",
            SectorQuadrant.SECTOR_2: "区域2 (左上)",
            SectorQuadrant.SECTOR_3: "区域3 (左下)",
            SectorQuadrant.SECTOR_4: "区域4 (右下)"
        }
        
        self.sector_title_label.setText(sector_names[sector])
        self.progress_label.setText(f"进度: {progress.progress_percentage:.1f}%")
        
        # 更新统计信息
        self.total_label.setText(f"总数: {progress.total_holes}")
        self.completed_label.setText(f"完成: {progress.completed_holes}")
        self.qualified_label.setText(f"合格: {progress.qualified_holes}")
        self.defective_label.setText(f"异常: {progress.defective_holes}")
        
        # 根据进度设置颜色
        color = progress.status_color.name()
        self.progress_label.setStyleSheet(f"color: {color}; font-weight: bold;")
    
    def _display_hole_list(self, holes):
        """显示孔位列表"""
        if not holes:
            self.hole_list_widget.setText("该区域暂无孔位")
            return
        
        # AI员工3号修改开始 - 支持新格式孔位ID显示
        # 创建简化的孔位信息文本，适应有限的显示空间
        hole_info_lines = []
        hole_info_lines.append(f"区域包含 {len(holes)} 个孔位")
        
        # 统计格式类型
        new_format_count = 0
        old_format_count = 0
        
        # 按状态分组显示，只显示重要统计信息
        status_groups = {}
        for hole in holes:
            status = hole.status.value
            if status not in status_groups:
                status_groups[status] = []
            
            # 格式化孔位ID用于显示
            formatted_id = self.format_hole_id_for_display(hole.hole_id)
            status_groups[status].append(formatted_id)
            
            # 统计格式类型
            if self.validate_new_hole_id_format(hole.hole_id):
                new_format_count += 1
            else:
                old_format_count += 1
        
        # 显示格式统计
        format_info = []
        if new_format_count > 0:
            format_info.append(f"新格式: {new_format_count}")
        if old_format_count > 0:
            format_info.append(f"旧格式: {old_format_count}")
        
        if format_info:
            hole_info_lines.append(f"格式分布: {', '.join(format_info)}")
        
        # 只显示状态统计，不显示具体孔位ID以节省空间
        for status, hole_ids in status_groups.items():
            hole_info_lines.append(f"{status}: {len(hole_ids)} 个")
        
        self.hole_list_widget.setText("\n".join(hole_info_lines))
        self.hole_list_widget.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        # AI员工3号修改结束