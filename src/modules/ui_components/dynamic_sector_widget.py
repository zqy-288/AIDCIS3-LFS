"""
动态扇形显示组件
支持扇形区域划分、缩放平移、点击交互的工件显示组件
可替换现有的WorkpieceDiagram或与其集成
"""

from typing import Dict, List, Optional, Set
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QGraphicsView, QGraphicsScene, QGraphicsItem,
                               QFrame, QPushButton, QButtonGroup)
from PySide6.QtCore import Qt, Signal, QPointF, QRectF, QTimer
from PySide6.QtGui import QColor, QPainter, QPen, QBrush

from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus
from src.core_business.graphics.graphics_view import OptimizedGraphicsView
from src.core_business.graphics.dynamic_sector_view import DynamicSectorView
from src.core_business.graphics.sector_manager_adapter import SectorManagerAdapter


class DynamicSectorDisplayWidget(QWidget):
    """
    动态扇形显示组件
    集成扇形管理、图形显示和用户交互的综合组件
    """
    
    # 信号定义
    sector_changed = Signal(int)      # 当前扇形改变
    sector_clicked = Signal(int)      # 扇形被点击
    hole_clicked = Signal(str)        # 孔位被点击
    view_mode_changed = Signal(str)   # 视图模式改变：'overview'/'sector'
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 数据
        self.hole_collection: Optional[HoleCollection] = None
        self.sector_manager = SectorManagerAdapter()
        self.current_sector: Optional[int] = None
        self.view_mode = "overview"  # 'overview' 或 'sector'
        
        # UI组件
        self.graphics_view: Optional[OptimizedGraphicsView] = None
        self.graphics_scene: Optional[QGraphicsScene] = None
        self.sector_view: Optional[DynamicSectorView] = None
        self.sector_buttons: Dict[int, QPushButton] = {}
        self.button_group: Optional[QButtonGroup] = None
        
        # 初始化UI
        self.setup_ui()
        self.setup_connections()
        
        # 定时器用于延迟更新
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._perform_delayed_update)
    
    def setup_ui(self):
        """设置用户界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)
        
        # 创建控制面板
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel)
        
        # 创建图形视图
        self._create_graphics_view()
        main_layout.addWidget(self.graphics_view, 1)
        
        # 创建状态面板
        status_panel = self._create_status_panel()
        main_layout.addWidget(status_panel)
    
    def _create_control_panel(self) -> QFrame:
        """创建控制面板"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        panel.setMaximumHeight(60)
        
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        
        # 视图模式切换
        mode_label = QLabel("视图模式:")
        layout.addWidget(mode_label)
        
        self.overview_btn = QPushButton("全景视图")
        self.overview_btn.setCheckable(True)
        self.overview_btn.setChecked(True)
        self.overview_btn.clicked.connect(lambda: self._set_view_mode("overview"))
        layout.addWidget(self.overview_btn)
        
        self.sector_btn = QPushButton("扇形视图")
        self.sector_btn.setCheckable(True)
        self.sector_btn.clicked.connect(lambda: self._set_view_mode("sector"))
        layout.addWidget(self.sector_btn)
        
        # 按钮组确保单选
        self.mode_button_group = QButtonGroup()
        self.mode_button_group.addButton(self.overview_btn)
        self.mode_button_group.addButton(self.sector_btn)
        
        layout.addWidget(QLabel("|"))  # 分隔符
        
        # 扇形选择按钮
        sector_label = QLabel("扇形:")
        layout.addWidget(sector_label)
        
        self.button_group = QButtonGroup()
        for i in range(8):  # 8个扇形
            btn = QPushButton(f"S{i}")
            btn.setCheckable(True)
            btn.setFixedSize(30, 30)
            btn.clicked.connect(lambda checked, sector_id=i: self._select_sector(sector_id))
            self.sector_buttons[i] = btn
            self.button_group.addButton(btn)
            layout.addWidget(btn)
        
        layout.addStretch()
        
        # 操作按钮
        self.reset_view_btn = QPushButton("重置视图")
        self.reset_view_btn.clicked.connect(self._reset_view)
        layout.addWidget(self.reset_view_btn)
        
        return panel
    
    def _create_graphics_view(self):
        """创建图形视图"""
        # 使用优化的图形视图
        self.graphics_view = OptimizedGraphicsView()
        self.graphics_scene = QGraphicsScene()
        self.graphics_view.setScene(self.graphics_scene)
        
        # 设置视图属性
        self.graphics_view.setRenderHint(QPainter.Antialiasing, True)
        self.graphics_view.setDragMode(QGraphicsView.RubberBandDrag)
        self.graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 启用缩放和平移
        self.graphics_view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.graphics_view.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
        # 创建扇形视图
        self.sector_view = DynamicSectorView()
        
        # 连接信号
        if hasattr(self.graphics_view, 'item_clicked'):
            self.graphics_view.item_clicked.connect(self._on_item_clicked)
    
    def _create_status_panel(self) -> QFrame:
        """创建状态面板"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        panel.setMaximumHeight(40)
        
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # 统计信息
        self.stats_label = QLabel("孔位: 0 | 已检: 0 | 合格: 0")
        layout.addWidget(self.stats_label)
        
        return panel
    
    def setup_connections(self):
        """设置信号连接"""
        # 扇形管理器信号
        self.sector_manager.sector_progress_updated.connect(self._on_sector_progress_updated)
        self.sector_manager.overall_progress_updated.connect(self._on_overall_progress_updated)
        
        # 扇形视图信号
        if self.sector_view:
            if hasattr(self.sector_view, 'sector_clicked'):
                self.sector_view.sector_clicked.connect(self._on_sector_view_clicked)
            if hasattr(self.sector_view, 'hole_clicked'):
                self.sector_view.hole_clicked.connect(self.hole_clicked.emit)
    
    def load_workpiece_data(self, hole_collection: HoleCollection):
        """加载工件数据"""
        self.hole_collection = hole_collection
        
        if not hole_collection:
            self._clear_display()
            return
        
        # 更新扇形管理器
        if hasattr(self.sector_manager, 'load_hole_collection'):
            self.sector_manager.load_hole_collection(hole_collection)
        
        # 更新扇形视图
        if self.sector_view:
            self.sector_view.load_workpiece_data(hole_collection)
        
        # 重新显示内容
        self._refresh_display()
        
        # 更新统计信息
        self._update_statistics()
        
        # 更新扇形按钮状态
        self._update_sector_buttons()
    
    def _clear_display(self):
        """清空显示"""
        if self.graphics_scene:
            self.graphics_scene.clear()
        
        self.status_label.setText("无数据")
        self.stats_label.setText("孔位: 0 | 已检: 0 | 合格: 0")
    
    def _refresh_display(self):
        """刷新显示"""
        if not self.hole_collection:
            return
        
        # 清空场景
        if self.graphics_scene:
            self.graphics_scene.clear()
        
        # 根据视图模式显示不同内容
        if self.view_mode == "overview":
            self._display_overview()
        elif self.view_mode == "sector" and self.current_sector is not None:
            self._display_sector(self.current_sector)
        
        # 适应视图
        self._fit_view()
    
    def _display_overview(self):
        """显示全景视图"""
        if not self.hole_collection or not self.graphics_scene:
            return
        
        # 添加所有孔位到场景
        for hole in self.hole_collection.holes.values():
            hole_item = self._create_hole_item(hole)
            self.graphics_scene.addItem(hole_item)
        
        # 添加扇形分割线
        self._add_sector_divisions()
        
        self.status_label.setText("全景视图 - 显示所有扇形")
    
    def _display_sector(self, sector_id: int):
        """显示指定扇形视图"""
        if not self.hole_collection or not self.graphics_scene:
            return
        
        # 获取该扇形的孔位
        sector_holes = self._get_sector_holes(sector_id)
        
        # 添加孔位到场景
        for hole in sector_holes:
            hole_item = self._create_hole_item(hole)
            self.graphics_scene.addItem(hole_item)
        
        # 添加扇形高亮
        self._add_sector_highlight(sector_id)
        
        self.status_label.setText(f"扇形视图 - 扇形 {sector_id}")
    
    def _create_hole_item(self, hole: HoleData) -> QGraphicsItem:
        """创建孔位图形项"""
        from PySide6.QtWidgets import QGraphicsEllipseItem
        
        # 根据状态确定颜色
        if hole.status == HoleStatus.QUALIFIED:
            color = QColor(76, 175, 80)  # 绿色
        elif hole.status == HoleStatus.DEFECTIVE:
            color = QColor(244, 67, 54)  # 红色
        elif hole.status == HoleStatus.PROCESSING:
            color = QColor(255, 193, 7)  # 黄色
        else:
            color = QColor(128, 128, 128)  # 灰色
        
        # 创建椭圆项
        radius = 3
        item = QGraphicsEllipseItem(
            hole.x - radius, hole.y - radius,
            radius * 2, radius * 2
        )
        
        item.setBrush(QBrush(color))
        item.setPen(QPen(QColor(0, 0, 0, 100)))
        item.setToolTip(f"孔位: {hole.hole_id}\n状态: {hole.status.value}")
        
        # 设置数据以便识别
        item.setData(0, hole.hole_id)
        
        return item
    
    def _add_sector_divisions(self):
        """添加扇形分割线"""
        if not self.hole_collection or not self.graphics_scene:
            return
        
        # 计算工件边界
        holes = list(self.hole_collection.holes.values())
        if not holes:
            return
        
        min_x = min(hole.x for hole in holes)
        max_x = max(hole.x for hole in holes)
        min_y = min(hole.y for hole in holes)
        max_y = max(hole.y for hole in holes)
        
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        radius = max(max_x - min_x, max_y - min_y) / 2 * 1.2
        
        # 绘制8条分割线
        from PySide6.QtWidgets import QGraphicsLineItem
        
        for i in range(8):
            angle = i * 45  # 每45度一条线
            end_x = center_x + radius * math.cos(math.radians(angle))
            end_y = center_y + radius * math.sin(math.radians(angle))
            
            line = QGraphicsLineItem(center_x, center_y, end_x, end_y)
            line.setPen(QPen(QColor(150, 150, 150), 1, Qt.DashLine))
            line.setZValue(-1)  # 确保在孔位下方
            self.graphics_scene.addItem(line)
    
    def _add_sector_highlight(self, sector_id: int):
        """添加扇形高亮"""
        # 这里可以添加扇形高亮显示逻辑
        pass
    
    def _get_sector_holes(self, sector_id: int) -> List[HoleData]:
        """获取指定扇形的孔位"""
        if not self.hole_collection:
            return []
        
        # 这里需要根据实际的扇形划分逻辑来实现
        # 暂时返回所有孔位作为示例
        return list(self.hole_collection.holes.values())
    
    def _fit_view(self):
        """调整视图以适应内容"""
        if self.graphics_view and self.graphics_scene:
            scene_rect = self.graphics_scene.itemsBoundingRect()
            if not scene_rect.isEmpty():
                self.graphics_view.fitInView(scene_rect, Qt.KeepAspectRatio)
    
    def _set_view_mode(self, mode: str):
        """设置视图模式"""
        if self.view_mode != mode:
            self.view_mode = mode
            
            # 更新按钮状态
            if mode == "overview":
                self.overview_btn.setChecked(True)
                self.sector_btn.setChecked(False)
            else:
                self.overview_btn.setChecked(False)
                self.sector_btn.setChecked(True)
            
            # 刷新显示
            self._refresh_display()
            
            # 发出信号
            self.view_mode_changed.emit(mode)
    
    def _select_sector(self, sector_id: int):
        """选择扇形"""
        if self.current_sector != sector_id:
            old_sector = self.current_sector
            self.current_sector = sector_id
            
            # 更新按钮状态
            self._update_sector_buttons()
            
            # 如果在扇形视图模式，刷新显示
            if self.view_mode == "sector":
                self._refresh_display()
            
            # 发出信号
            self.sector_changed.emit(sector_id)
            self.sector_clicked.emit(sector_id)
    
    def _update_sector_buttons(self):
        """更新扇形按钮状态"""
        for sector_id, btn in self.sector_buttons.items():
            btn.setChecked(sector_id == self.current_sector)
            
            # 根据扇形状态更新按钮样式
            if hasattr(self.sector_manager, 'get_sector_progress'):
                progress = self.sector_manager.get_sector_progress(sector_id)
                if progress and progress.completion_rate > 0.8:
                    btn.setStyleSheet("QPushButton { background-color: #4CAF50; }")  # 绿色
                elif progress and progress.completion_rate > 0.5:
                    btn.setStyleSheet("QPushButton { background-color: #FFC107; }")  # 黄色
                else:
                    btn.setStyleSheet("")  # 默认
    
    def _update_statistics(self):
        """更新统计信息"""
        if not self.hole_collection:
            return
        
        total_holes = len(self.hole_collection.holes)
        qualified_count = sum(1 for hole in self.hole_collection.holes.values() 
                            if hole.status == HoleStatus.QUALIFIED)
        detected_count = sum(1 for hole in self.hole_collection.holes.values() 
                           if hole.status != HoleStatus.PENDING)
        
        self.stats_label.setText(
            f"孔位: {total_holes} | 已检: {detected_count} | 合格: {qualified_count}"
        )
    
    def _reset_view(self):
        """重置视图"""
        if self.graphics_view:
            self.graphics_view.resetTransform()
            self._fit_view()
    
    def _perform_delayed_update(self):
        """执行延迟更新"""
        self._update_statistics()
        self._update_sector_buttons()
        self.update()
    
    def _on_sector_progress_updated(self, sector, progress):
        """处理扇形进度更新"""
        # 延迟更新以避免频繁刷新
        self.update_timer.start(100)
    
    def _on_overall_progress_updated(self, progress_data: Dict):
        """处理整体进度更新"""
        self.update_timer.start(100)
    
    def _on_sector_view_clicked(self, sector_id: int):
        """处理扇形视图点击"""
        self._select_sector(sector_id)
    
    def _on_item_clicked(self, item):
        """处理图形项点击"""
        if item and item.data(0):
            hole_id = item.data(0)
            self.hole_clicked.emit(hole_id)
    
    # 公共接口方法
    def set_sector(self, sector_id: int):
        """设置当前扇形"""
        self._select_sector(sector_id)
    
    def get_current_sector(self) -> Optional[int]:
        """获取当前扇形"""
        return self.current_sector
    
    def zoom_in(self):
        """放大视图"""
        if self.graphics_view:
            self.graphics_view.scale(1.2, 1.2)
    
    def zoom_out(self):
        """缩小视图"""
        if self.graphics_view:
            self.graphics_view.scale(0.8, 0.8)
    
    def reset_zoom(self):
        """重置缩放"""
        self._reset_view()


# 导入math模块（如果需要）
import math