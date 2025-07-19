"""
视口控制器
管理主视图区域的显示和交互
"""

import logging
from typing import Optional, Dict, List, Any
from PySide6.QtCore import QObject, Signal, QTimer, QPointF, QRectF
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QFrame
from PySide6.QtGui import QTransform, QWheelEvent, QMouseEvent
from PySide6.QtCore import Qt

# 导入现有组件
from src.core_business.graphics.graphics_view import OptimizedGraphicsView
from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus
from src.core.dependency_injection import injectable, ServiceLifetime

# 事件类型常量
class EventTypes:
    DXF_FILE_LOADED = "dxf_file_loaded"
    HOLE_SELECTED = "hole_selected"
    VIEWPORT_CHANGED = "viewport_changed"
    ZOOM_CHANGED = "zoom_changed"


@injectable(ServiceLifetime.TRANSIENT)
class ViewportController(QObject):
    """视口控制器 - 管理主视图区域的显示和交互"""
    
    # 局部信号
    hole_clicked = Signal(str)  # 孔位ID
    hole_hovered = Signal(str)  # 孔位ID
    viewport_changed = Signal(dict)  # 视口变化信息
    zoom_changed = Signal(float)  # 缩放级别
    
    # 交互信号
    selection_changed = Signal(list)  # 选择的孔位列表
    view_mode_changed = Signal(str)  # 视图模式变化
    
    # 性能信号
    rendering_started = Signal()
    rendering_finished = Signal()
    
    def __init__(self, parent: QWidget, model, event_bus):
        super().__init__()
        self.parent = parent
        self.model = model
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        
        # 初始化图形视图
        self.graphics_view = OptimizedGraphicsView()
        
        # 视口状态
        self.current_zoom_level = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 10.0
        self.zoom_step = 0.1
        
        # 选择状态
        self.selected_holes = []
        self.hovered_hole = None
        
        # 视图模式
        self.view_mode = "normal"  # normal, highlight, filter
        
        # 性能优化
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.perform_delayed_update)
        
        # 订阅相关事件
        self.subscribe_to_events()
        
        # 设置UI
        self.setup_ui()
        
        # 设置交互
        self.setup_interactions()
        
        # 连接信号
        self.setup_signal_connections()
        
        self.logger.info("视口控制器初始化完成")
    
    def subscribe_to_events(self):
        """订阅事件总线事件"""
        try:
            # 订阅DXF文件加载事件
            self.event_bus.subscribe(EventTypes.DXF_FILE_LOADED, self.load_viewport_data)
            
            # 订阅孔位选择事件
            self.event_bus.subscribe(EventTypes.HOLE_SELECTED, self.highlight_hole)
            
            self.logger.info("事件订阅完成")
            
        except Exception as e:
            self.logger.error(f"事件订阅失败: {e}")
    
    def setup_ui(self):
        """设置视口UI"""
        try:
            # 创建主容器
            self.ui_container = QWidget()
            layout = QVBoxLayout(self.ui_container)
            
            # 工具栏
            toolbar_frame = QFrame()
            toolbar_layout = QHBoxLayout(toolbar_frame)
            
            # 缩放控制
            zoom_label = QLabel("缩放:")
            toolbar_layout.addWidget(zoom_label)
            
            # 缩放滑块
            self.zoom_slider = QSlider(Qt.Horizontal)
            self.zoom_slider.setMinimum(int(self.min_zoom * 100))
            self.zoom_slider.setMaximum(int(self.max_zoom * 100))
            self.zoom_slider.setValue(int(self.current_zoom_level * 100))
            self.zoom_slider.setFixedWidth(200)
            self.zoom_slider.valueChanged.connect(self.on_zoom_slider_changed)
            toolbar_layout.addWidget(self.zoom_slider)
            
            # 缩放值显示
            self.zoom_value_label = QLabel(f"{self.current_zoom_level:.1f}x")
            self.zoom_value_label.setMinimumWidth(50)
            toolbar_layout.addWidget(self.zoom_value_label)
            
            # 视图控制按钮
            self.fit_button = QPushButton("适应窗口")
            self.fit_button.clicked.connect(self.fit_to_window)
            toolbar_layout.addWidget(self.fit_button)
            
            self.reset_button = QPushButton("重置视图")
            self.reset_button.clicked.connect(self.reset_view)
            toolbar_layout.addWidget(self.reset_button)
            
            toolbar_layout.addStretch()
            
            # 状态信息
            self.status_info_label = QLabel("视口状态: 就绪")
            self.status_info_label.setStyleSheet("color: #007ACC; font-size: 11px;")
            toolbar_layout.addWidget(self.status_info_label)
            
            layout.addWidget(toolbar_frame)
            
            # 图形视图区域
            self.graphics_view.setParent(self.ui_container)
            layout.addWidget(self.graphics_view)
            
            # 底部信息栏
            info_frame = QFrame()
            info_layout = QHBoxLayout(info_frame)
            
            # 坐标信息
            self.coordinates_label = QLabel("坐标: (0, 0)")
            info_layout.addWidget(self.coordinates_label)
            
            info_layout.addStretch()
            
            # 统计信息
            self.stats_label = QLabel("孔位: 0 | 选中: 0")
            info_layout.addWidget(self.stats_label)
            
            layout.addWidget(info_frame)
            
            # 应用主题
            self.apply_theme()
            
        except Exception as e:
            self.logger.error(f"视口UI设置失败: {e}")
    
    def setup_interactions(self):
        """设置交互逻辑"""
        try:
            # 鼠标事件
            self.graphics_view.setMouseTracking(True)
            
            # 自定义事件过滤器
            self.graphics_view.installEventFilter(self)
            
            # 缩放设置
            self.graphics_view.setTransformationAnchor(OptimizedGraphicsView.AnchorUnderMouse)
            self.graphics_view.setResizeAnchor(OptimizedGraphicsView.AnchorUnderMouse)
            
        except Exception as e:
            self.logger.error(f"交互设置失败: {e}")
    
    def setup_signal_connections(self):
        """设置信号连接"""
        try:
            # 连接图形视图信号
            if hasattr(self.graphics_view, 'hole_clicked'):
                self.graphics_view.hole_clicked.connect(self.on_hole_clicked)
            
            if hasattr(self.graphics_view, 'hole_hovered'):
                self.graphics_view.hole_hovered.connect(self.on_hole_hovered)
            
            if hasattr(self.graphics_view, 'view_changed'):
                self.graphics_view.view_changed.connect(self.on_view_changed)
            
            # 连接内部信号
            self.hole_clicked.connect(self.on_hole_clicked_internal)
            self.viewport_changed.connect(self.on_viewport_changed_internal)
            self.zoom_changed.connect(self.on_zoom_changed_internal)
            
        except Exception as e:
            self.logger.error(f"信号连接失败: {e}")
    
    def load_viewport_data(self, event_data: Dict[str, Any]):
        """加载视口数据"""
        try:
            self.rendering_started.emit()
            
            hole_collection = event_data.get('hole_collection')
            if not hole_collection:
                self.logger.warning("未收到有效的孔位数据")
                return
            
            self.logger.info(f"加载视口数据: {len(hole_collection)} 个孔位")
            
            # 清除现有数据
            self.clear_viewport()
            
            # 加载新数据到图形视图
            self.graphics_view.load_holes(hole_collection)
            
            # 更新统计信息
            self.update_statistics(len(hole_collection), 0)
            
            # 自动适应窗口
            self.fit_to_window()
            
            # 发布视口变化事件
            self.event_bus.publish(EventTypes.VIEWPORT_CHANGED, {
                'action': 'data_loaded',
                'hole_count': len(hole_collection),
                'zoom_level': self.current_zoom_level
            })
            
            self.viewport_changed.emit({
                'action': 'data_loaded',
                'hole_count': len(hole_collection)
            })
            
            self.rendering_finished.emit()
            
        except Exception as e:
            self.logger.error(f"视口数据加载失败: {e}")
            self.rendering_finished.emit()
    
    def highlight_hole(self, event_data: Dict[str, Any]):
        """高亮显示孔位"""
        try:
            hole_id = event_data.get('hole_id')
            if not hole_id:
                return
            
            self.logger.debug(f"高亮孔位: {hole_id}")
            
            # 实现孔位高亮逻辑
            if hasattr(self.graphics_view, 'highlight_hole'):
                self.graphics_view.highlight_hole(hole_id)
            
            # 更新选择状态
            if hole_id not in self.selected_holes:
                self.selected_holes.append(hole_id)
                self.selection_changed.emit(self.selected_holes)
                
                # 更新统计信息
                total_holes = len(self.graphics_view.scene.items()) if self.graphics_view.scene else 0
                self.update_statistics(total_holes, len(self.selected_holes))
            
        except Exception as e:
            self.logger.error(f"孔位高亮失败: {e}")
    
    def on_hole_clicked(self, hole_data: HoleData):
        """处理孔位点击事件"""
        try:
            hole_id = hole_data.id if hasattr(hole_data, 'id') else str(hole_data)
            
            self.logger.debug(f"孔位被点击: {hole_id}")
            
            # 更新坐标显示
            if hasattr(hole_data, 'x') and hasattr(hole_data, 'y'):
                self.coordinates_label.setText(f"坐标: ({hole_data.x:.2f}, {hole_data.y:.2f})")
            
            # 发出信号
            self.hole_clicked.emit(hole_id)
            
            # 发布事件
            self.event_bus.publish(EventTypes.HOLE_SELECTED, {
                'hole_id': hole_id,
                'hole_data': hole_data,
                'source': 'viewport'
            })
            
        except Exception as e:
            self.logger.error(f"孔位点击处理失败: {e}")
    
    def on_hole_hovered(self, hole_data: HoleData):
        """处理孔位悬停事件"""
        try:
            hole_id = hole_data.id if hasattr(hole_data, 'id') else str(hole_data)
            
            self.hovered_hole = hole_id
            self.hole_hovered.emit(hole_id)
            
            # 更新状态显示
            self.status_info_label.setText(f"悬停: {hole_id}")
            
        except Exception as e:
            self.logger.error(f"孔位悬停处理失败: {e}")
    
    def on_view_changed(self):
        """处理视图变化事件"""
        try:
            # 获取当前变换
            transform = self.graphics_view.transform()
            current_zoom = transform.m11()  # 获取缩放因子
            
            # 更新缩放级别
            if abs(current_zoom - self.current_zoom_level) > 0.01:
                self.current_zoom_level = current_zoom
                self.zoom_changed.emit(current_zoom)
                
                # 更新UI
                self.zoom_slider.setValue(int(current_zoom * 100))
                self.zoom_value_label.setText(f"{current_zoom:.1f}x")
            
            # 延迟更新视口信息
            self.update_timer.start(100)  # 100ms延迟
            
        except Exception as e:
            self.logger.error(f"视图变化处理失败: {e}")
    
    def perform_delayed_update(self):
        """执行延迟的视口更新"""
        try:
            # 获取视口信息
            viewport_rect = self.graphics_view.mapToScene(self.graphics_view.viewport().rect()).boundingRect()
            
            # 发布视口变化事件
            self.viewport_changed.emit({
                'action': 'view_changed',
                'zoom_level': self.current_zoom_level,
                'viewport_rect': {
                    'x': viewport_rect.x(),
                    'y': viewport_rect.y(),
                    'width': viewport_rect.width(),
                    'height': viewport_rect.height()
                }
            })
            
        except Exception as e:
            self.logger.error(f"延迟更新失败: {e}")
    
    def on_zoom_slider_changed(self, value: int):
        """处理缩放滑块变化"""
        try:
            new_zoom = value / 100.0
            self.set_zoom_level(new_zoom)
            
        except Exception as e:
            self.logger.error(f"缩放滑块处理失败: {e}")
    
    def set_zoom_level(self, zoom_level: float):
        """设置缩放级别"""
        try:
            # 限制缩放范围
            zoom_level = max(self.min_zoom, min(self.max_zoom, zoom_level))
            
            # 应用缩放
            self.graphics_view.resetTransform()
            self.graphics_view.scale(zoom_level, zoom_level)
            
            # 更新状态
            self.current_zoom_level = zoom_level
            self.zoom_value_label.setText(f"{zoom_level:.1f}x")
            
            # 发出信号
            self.zoom_changed.emit(zoom_level)
            
        except Exception as e:
            self.logger.error(f"缩放设置失败: {e}")
    
    def zoom_in(self):
        """放大"""
        new_zoom = self.current_zoom_level + self.zoom_step
        self.set_zoom_level(new_zoom)
    
    def zoom_out(self):
        """缩小"""
        new_zoom = self.current_zoom_level - self.zoom_step
        self.set_zoom_level(new_zoom)
    
    def fit_to_window(self):
        """适应窗口大小"""
        try:
            if self.graphics_view.scene and self.graphics_view.scene.items():
                # 获取场景边界
                scene_rect = self.graphics_view.scene.itemsBoundingRect()
                
                # 适应视图
                self.graphics_view.fitInView(scene_rect, Qt.KeepAspectRatio)
                
                # 更新缩放信息
                transform = self.graphics_view.transform()
                self.current_zoom_level = transform.m11()
                self.zoom_slider.setValue(int(self.current_zoom_level * 100))
                self.zoom_value_label.setText(f"{self.current_zoom_level:.1f}x")
                
                self.logger.info("视图已适应窗口")
            
        except Exception as e:
            self.logger.error(f"适应窗口失败: {e}")
    
    def reset_view(self):
        """重置视图"""
        try:
            # 重置变换
            self.graphics_view.resetTransform()
            self.current_zoom_level = 1.0
            
            # 更新UI
            self.zoom_slider.setValue(100)
            self.zoom_value_label.setText("1.0x")
            
            # 清除选择
            self.selected_holes.clear()
            self.selection_changed.emit(self.selected_holes)
            
            self.logger.info("视图已重置")
            
        except Exception as e:
            self.logger.error(f"视图重置失败: {e}")
    
    def clear_viewport(self):
        """清除视口内容"""
        try:
            # 清除图形视图
            if self.graphics_view.scene:
                self.graphics_view.scene.clear()
            
            # 重置状态
            self.selected_holes.clear()
            self.hovered_hole = None
            
            # 更新UI
            self.coordinates_label.setText("坐标: (0, 0)")
            self.update_statistics(0, 0)
            
            self.logger.info("视口已清除")
            
        except Exception as e:
            self.logger.error(f"视口清除失败: {e}")
    
    def update_statistics(self, total_holes: int, selected_holes: int):
        """更新统计信息"""
        try:
            self.stats_label.setText(f"孔位: {total_holes} | 选中: {selected_holes}")
            
        except Exception as e:
            self.logger.error(f"统计信息更新失败: {e}")
    
    def on_hole_clicked_internal(self, hole_id: str):
        """内部孔位点击处理"""
        try:
            self.logger.debug(f"内部处理孔位点击: {hole_id}")
            
        except Exception as e:
            self.logger.error(f"内部孔位点击处理失败: {e}")
    
    def on_viewport_changed_internal(self, viewport_info: Dict[str, Any]):
        """内部视口变化处理"""
        try:
            action = viewport_info.get('action', 'unknown')
            self.status_info_label.setText(f"视口状态: {action}")
            
        except Exception as e:
            self.logger.error(f"内部视口变化处理失败: {e}")
    
    def on_zoom_changed_internal(self, zoom_level: float):
        """内部缩放变化处理"""
        try:
            # 发布缩放变化事件
            self.event_bus.publish(EventTypes.ZOOM_CHANGED, {
                'zoom_level': zoom_level,
                'source': 'viewport'
            })
            
        except Exception as e:
            self.logger.error(f"内部缩放变化处理失败: {e}")
    
    def apply_theme(self):
        """应用主题样式"""
        try:
            # 应用深色主题
            self.ui_container.setStyleSheet("""
                QWidget {
                    background-color: #2C313C;
                    color: #D3D8E0;
                }
                QFrame {
                    background-color: #313642;
                    border: 1px solid #404552;
                    border-radius: 4px;
                }
                QPushButton {
                    background-color: #007ACC;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #0099FF;
                }
                QPushButton:pressed {
                    background-color: #005C99;
                }
                QSlider::groove:horizontal {
                    border: 1px solid #404552;
                    height: 8px;
                    background: #313642;
                    border-radius: 4px;
                }
                QSlider::handle:horizontal {
                    background: #007ACC;
                    border: 1px solid #005C99;
                    width: 18px;
                    margin: -5px 0;
                    border-radius: 9px;
                }
                QSlider::handle:horizontal:hover {
                    background: #0099FF;
                }
                QLabel {
                    color: #D3D8E0;
                    font-size: 12px;
                }
            """)
            
            # 图形视图特殊样式
            self.graphics_view.setStyleSheet("""
                QGraphicsView {
                    border: 1px solid #404552;
                    background-color: #1E222B;
                }
            """)
            
        except Exception as e:
            self.logger.error(f"主题应用失败: {e}")
    
    def get_ui_container(self) -> QWidget:
        """获取UI容器"""
        return self.ui_container
    
    def get_graphics_view(self) -> OptimizedGraphicsView:
        """获取图形视图"""
        return self.graphics_view
    
    def get_selected_holes(self) -> List[str]:
        """获取选中的孔位"""
        return self.selected_holes.copy()
    
    def get_current_zoom_level(self) -> float:
        """获取当前缩放级别"""
        return self.current_zoom_level
    
    def eventFilter(self, obj, event):
        """事件过滤器"""
        try:
            if obj == self.graphics_view:
                if event.type() == QWheelEvent.Type:
                    # 处理鼠标滚轮缩放
                    self.handle_wheel_zoom(event)
                    return True
                elif event.type() == QMouseEvent.Type:
                    # 处理鼠标移动
                    self.handle_mouse_move(event)
            
            return super().eventFilter(obj, event)
            
        except Exception as e:
            self.logger.error(f"事件过滤失败: {e}")
            return False
    
    def handle_wheel_zoom(self, event: QWheelEvent):
        """处理滚轮缩放"""
        try:
            # 获取滚轮增量
            delta = event.angleDelta().y()
            
            # 计算缩放因子
            zoom_factor = 1.25 if delta > 0 else 0.8
            
            # 应用缩放
            new_zoom = self.current_zoom_level * zoom_factor
            self.set_zoom_level(new_zoom)
            
        except Exception as e:
            self.logger.error(f"滚轮缩放处理失败: {e}")
    
    def handle_mouse_move(self, event: QMouseEvent):
        """处理鼠标移动"""
        try:
            # 获取鼠标位置
            scene_pos = self.graphics_view.mapToScene(event.position().toPoint())
            
            # 更新坐标显示
            self.coordinates_label.setText(f"坐标: ({scene_pos.x():.2f}, {scene_pos.y():.2f})")
            
        except Exception as e:
            self.logger.error(f"鼠标移动处理失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        try:
            # 停止定时器
            if self.update_timer:
                self.update_timer.stop()
            
            # 清除视口
            self.clear_viewport()
            
            # 清理引用
            self.graphics_view = None
            self.selected_holes.clear()
            
            self.logger.info("视口控制器资源清理完成")
            
        except Exception as e:
            self.logger.error(f"资源清理失败: {e}")