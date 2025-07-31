"""
遗留代码适配器
为了向后兼容，提供与原 CompletePanoramaWidget 相同的接口
"""

from typing import Optional
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget

from ..core.di_container import PanoramaDIContainer
from ..components.panorama_widget import PanoramaWidget
from src.core_business.graphics.sector_types import SectorQuadrant
from src.core_business.models.hole_data import HoleCollection, HoleStatus


class CompletePanoramaWidgetAdapter(QWidget):
    """
    CompletePanoramaWidget 适配器
    
    提供与原组件相同的接口，内部使用新的组件架构
    这样可以实现无缝迁移，不需要修改现有调用代码
    """
    
    # 保持原有信号接口
    sector_clicked = Signal(SectorQuadrant)
    status_update_completed = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 创建新的组件
        self._container = PanoramaDIContainer()
        self._panorama_widget = self._container.create_panorama_widget(self)
        
        # 设置布局
        from PySide6.QtWidgets import QVBoxLayout, QLabel
        from PySide6.QtCore import Qt
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加信息标签（保持向后兼容）
        self.info_label = QLabel("全景图准备就绪")
        self.info_label.setAlignment(Qt.AlignCenter)
        font = self.info_label.font()
        font.setPointSize(12)
        self.info_label.setFont(font)
        self.info_label.setStyleSheet("""
            QLabel {
                padding: 8px;
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.info_label)
        
        layout.addWidget(self._panorama_widget)
        
        # 转发信号
        self._panorama_widget.sector_clicked.connect(self.sector_clicked.emit)
        self._panorama_widget.status_update_completed.connect(self.status_update_completed.emit)
        
        # 保持原有属性名（可选，用于代码检查）
        self.hole_collection: Optional[HoleCollection] = None
        self.center_point = None
        self.panorama_radius = 0.0
        self.sector_highlights = {}
        self.current_highlighted_sector = None
        
        # 暴露panorama_view以保持向后兼容
        # 注意：这需要PanoramaWidget有graphics_view属性
        if hasattr(self._panorama_widget, 'graphics_view'):
            self.panorama_view = self._panorama_widget.graphics_view
            # 同时暴露graphics_view属性
            self.graphics_view = self._panorama_widget.graphics_view
        else:
            # 创建一个占位视图
            from PySide6.QtWidgets import QGraphicsView
            from PySide6.QtWidgets import QGraphicsScene
            self.panorama_view = QGraphicsView()
            self.panorama_view.scene = QGraphicsScene()
            self.graphics_view = self.panorama_view
    
    # === 原有接口方法 ===
    
    def load_hole_collection(self, hole_collection: HoleCollection):
        """加载孔位集合（保持原接口）"""
        self.hole_collection = hole_collection
        if hole_collection and hole_collection.holes:
            hole_count = len(hole_collection.holes)
            self.info_label.setText(f"全景图已加载: {hole_count} 个孔位")
        else:
            self.info_label.setText("暂无数据")
        self._panorama_widget.load_hole_collection(hole_collection)
        
        # 加载后自动适配视图
        if hasattr(self._panorama_widget, 'graphics_view'):
            # 延迟执行以确保场景更新完成
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, self._fit_panorama_view)
            
    def load_complete_view(self, hole_collection: HoleCollection, scale_manager=None):
        """加载完整的全景图（兼容原接口）"""
        self.load_hole_collection(hole_collection)
    
    def _fit_panorama_view(self):
        """适配全景图视图"""
        if not hasattr(self._panorama_widget, 'graphics_view'):
            return
            
        view = self._panorama_widget.graphics_view
        scene = view.scene
        
        if not scene:
            return
            
        # 获取场景边界
        scene_rect = scene.sceneRect()
        if scene_rect.isEmpty():
            return
            
        # 临时修改缩放限制
        original_min_zoom = getattr(view, 'min_zoom', 0.01)
        view.min_zoom = 0.001  # 允许更小的缩放
        
        # 添加边距
        margin = 50  # 增加边距
        adjusted_rect = scene_rect.adjusted(-margin, -margin, margin, margin)
        
        # 重置变换
        view.resetTransform()
        
        # 适配到视图
        view.fitInView(adjusted_rect, Qt.KeepAspectRatio)
        
        # 检查当前缩放
        current_scale = view.transform().m11()
        print(f"适配后缩放: {current_scale}")
        
        # 根据数据量调整缩放
        if hasattr(self, 'hole_collection') and self.hole_collection:
            hole_count = len(self.hole_collection)
            if hole_count > 20000:  # 超大数据集
                target_scale = 0.01
            elif hole_count > 10000:
                target_scale = 0.02
            elif hole_count > 5000:
                target_scale = 0.03
            elif hole_count > 1000:
                target_scale = 0.05
            else:
                target_scale = 0.1
                
            if current_scale > target_scale:
                additional_scale = target_scale / current_scale
                view.scale(additional_scale, additional_scale)
                print(f"数据量: {hole_count}, 目标缩放: {target_scale}, 最终: {view.transform().m11()}")
        
        # 恢复原始限制（延迟恢复，避免影响后续操作）
        from PySide6.QtCore import QTimer
        QTimer.singleShot(1000, lambda: setattr(view, 'min_zoom', original_min_zoom))
    
    def update_hole_status(self, hole_id: str, status: HoleStatus, color_override=None):
        """更新孔位状态（保持原接口）"""
        self._panorama_widget.update_hole_status(hole_id, status, color_override)
    
    def highlight_sector(self, sector: SectorQuadrant):
        """高亮扇区（保持原接口）"""
        self._panorama_widget.highlight_sector(sector)
    
    def clear_sector_highlight(self):
        """清除扇区高亮（保持原接口）"""
        self._panorama_widget.clear_sector_highlight()
        
    def clear_highlight(self):
        """清除高亮（clear_sector_highlight的别名）"""
        self.clear_sector_highlight()
    
    def enable_snake_path(self, enabled: bool):
        """启用蛇形路径（保持原接口）"""
        self._panorama_widget.enable_snake_path(enabled)
    
    def apply_theme(self, theme_config: dict):
        """应用主题（保持原接口）"""
        self._panorama_widget.apply_theme(theme_config)
    
    
    # === 扩展方法（利用新架构优势） ===
    
    def get_event_bus(self):
        """获取事件总线（新功能）"""
        return self._container.get_event_bus()
    
    def set_current_sector(self, sector: SectorQuadrant):
        """设置当前扇区（保持原接口）"""
        # 调用 highlight_sector 而不是不存在的 set_current_sector
        self._panorama_widget.highlight_sector(sector)
        self.current_highlighted_sector = sector
    
    # === 测试和调试方法（向后兼容） ===
    
    def _calculate_panorama_geometry(self):
        """计算全景图几何（调试用）"""
        if hasattr(self._panorama_widget, '_calculate_geometry'):
            self._panorama_widget._calculate_geometry()
    
    def _create_sector_highlights(self):
        """创建扇形高亮（调试用）"""
        if hasattr(self._panorama_widget, '_create_highlights'):
            self._panorama_widget._create_highlights()
    
    def test_highlight_all_sectors(self):
        """测试高亮所有扇形（调试用）"""
        if hasattr(self._panorama_widget, 'test_highlight_all'):
            self._panorama_widget.test_highlight_all()
    
    def get_data_model(self):
        """获取数据模型（新功能）"""
        return self._container.get_data_model()
    
    def get_status_manager(self):
        """获取状态管理器（新功能）"""
        return self._container.get_status_manager()
    
    # === 向后兼容的方法（可能被调用但已废弃） ===
    
    def _setup_ui(self):
        """原有UI设置方法（空实现，向后兼容）"""
        pass
    
    def _apply_theme(self):
        """原有主题应用方法（空实现，向后兼容）"""
        pass
    
    def _calculate_geometry(self):
        """原有几何计算方法（空实现，向后兼容）"""
        pass


# 为了完全向后兼容，可以创建别名
CompletePanoramaWidget = CompletePanoramaWidgetAdapter


def create_legacy_panorama_widget(parent=None) -> CompletePanoramaWidgetAdapter:
    """
    创建遗留风格的全景图组件
    
    这个函数提供了一个简单的工厂方法，用于创建适配器
    
    Args:
        parent: 父组件
        
    Returns:
        适配器实例
    """
    return CompletePanoramaWidgetAdapter(parent)


# 迁移辅助函数
def migrate_to_new_architecture(old_panorama_widget) -> PanoramaWidget:
    """
    迁移辅助函数
    
    帮助将旧的全景图组件迁移到新架构
    
    Args:
        old_panorama_widget: 旧的全景图组件
        
    Returns:
        新的全景图组件
    """
    if isinstance(old_panorama_widget, CompletePanoramaWidgetAdapter):
        return old_panorama_widget._panorama_widget
    
    # 如果是真正的旧组件，创建新组件并迁移数据
    container = PanoramaDIContainer()
    new_widget = container.create_panorama_widget()
    
    # 迁移数据（如果有的话）
    if hasattr(old_panorama_widget, 'hole_collection') and old_panorama_widget.hole_collection:
        new_widget.load_hole_collection(old_panorama_widget.hole_collection)
    
    return new_widget