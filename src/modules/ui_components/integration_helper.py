"""
组件集成助手
帮助MainDetectionView集成全景预览和动态扇形组件
"""

from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import QObject, Signal

from .panorama_widget import CompletePanoramaWidget
from .dynamic_sector_widget import DynamicSectorDisplayWidget
from src.core_business.models.hole_data import HoleCollection


class ComponentIntegrationHelper(QObject):
    """
    组件集成助手
    负责协调全景预览、动态扇形显示和主界面之间的交互
    """
    
    # 信号定义
    sector_selected = Signal(int)
    hole_selected = Signal(str)
    view_mode_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 组件实例
        self.panorama_widget: Optional[CompletePanoramaWidget] = None
        self.dynamic_sector_widget: Optional[DynamicSectorDisplayWidget] = None
        
        # 数据
        self.hole_collection: Optional[HoleCollection] = None
        self.current_sector: Optional[int] = None
    
    def create_panorama_widget(self) -> CompletePanoramaWidget:
        """创建全景预览组件"""
        if self.panorama_widget is None:
            self.panorama_widget = CompletePanoramaWidget()
            
            # 连接信号
            self.panorama_widget.sector_clicked.connect(self._on_panorama_sector_clicked)
            self.panorama_widget.hole_clicked.connect(self._on_panorama_hole_clicked)
            
        return self.panorama_widget
    
    def create_dynamic_sector_widget(self) -> DynamicSectorDisplayWidget:
        """创建动态扇形显示组件"""
        if self.dynamic_sector_widget is None:
            self.dynamic_sector_widget = DynamicSectorDisplayWidget()
            
            # 连接信号
            self.dynamic_sector_widget.sector_clicked.connect(self._on_sector_widget_sector_clicked)
            self.dynamic_sector_widget.hole_clicked.connect(self._on_sector_widget_hole_clicked)
            self.dynamic_sector_widget.view_mode_changed.connect(self.view_mode_changed.emit)
            
        return self.dynamic_sector_widget
    
    def load_workpiece_data(self, hole_collection: HoleCollection):
        """加载工件数据到所有组件"""
        self.hole_collection = hole_collection
        
        # 更新全景预览
        if self.panorama_widget:
            self.panorama_widget.load_workpiece_data(hole_collection)
        
        # 更新动态扇形显示
        if self.dynamic_sector_widget:
            self.dynamic_sector_widget.load_workpiece_data(hole_collection)
    
    def set_current_sector(self, sector_id: Optional[int]):
        """设置当前扇形"""
        if self.current_sector != sector_id:
            self.current_sector = sector_id
            
            # 同步到所有组件
            if self.panorama_widget:
                self.panorama_widget.set_selected_sector(sector_id)
            
            if self.dynamic_sector_widget and sector_id is not None:
                self.dynamic_sector_widget.set_sector(sector_id)
            
            # 发出信号
            if sector_id is not None:
                self.sector_selected.emit(sector_id)
    
    def _on_panorama_sector_clicked(self, sector_id: int):
        """处理全景预览扇形点击"""
        self.set_current_sector(sector_id)
    
    def _on_panorama_hole_clicked(self, hole_id: str):
        """处理全景预览孔位点击"""
        self.hole_selected.emit(hole_id)
    
    def _on_sector_widget_sector_clicked(self, sector_id: int):
        """处理动态扇形组件扇形点击"""
        self.set_current_sector(sector_id)
    
    def _on_sector_widget_hole_clicked(self, hole_id: str):
        """处理动态扇形组件孔位点击"""
        self.hole_selected.emit(hole_id)
    
    def get_current_sector_info(self) -> Optional[dict]:
        """获取当前扇形信息"""
        if self.panorama_widget and self.current_sector is not None:
            return self.panorama_widget.get_sector_info(self.current_sector)
        return None


def replace_panorama_placeholder(main_detection_view, integration_helper: ComponentIntegrationHelper):
    """
    替换MainDetectionView中的全景预览占位符
    
    Args:
        main_detection_view: MainDetectionView实例
        integration_helper: 组件集成助手
    """
    try:
        # 检查是否有全景预览面板
        if not hasattr(main_detection_view, 'panorama_preview_panel'):
            return False
        
        # 创建新的全景预览组件
        panorama_widget = integration_helper.create_panorama_widget()
        
        # 获取当前布局
        panorama_layout = main_detection_view.panorama_preview_panel.layout()
        
        # 移除占位符
        if hasattr(main_detection_view, 'panorama_placeholder'):
            panorama_layout.removeWidget(main_detection_view.panorama_placeholder)
            main_detection_view.panorama_placeholder.deleteLater()
            delattr(main_detection_view, 'panorama_placeholder')
        
        # 添加真实组件
        panorama_layout.addWidget(panorama_widget)
        
        # 连接信号到主界面
        panorama_widget.sector_clicked.connect(
            lambda sector_id: main_detection_view.log_message(f"选择扇形: {sector_id}", "blue")
        )
        panorama_widget.hole_clicked.connect(
            lambda hole_id: main_detection_view.log_message(f"选择孔位: {hole_id}", "green")
        )
        
        return True
        
    except Exception as e:
        if hasattr(main_detection_view, 'logger'):
            main_detection_view.logger.error(f"替换全景预览占位符失败: {e}")
        return False


def update_sector_statistics_placeholder(main_detection_view, integration_helper: ComponentIntegrationHelper):
    """
    更新扇形统计占位符的内容
    
    Args:
        main_detection_view: MainDetectionView实例
        integration_helper: 组件集成助手
    """
    try:
        # 检查是否有扇形统计占位符
        if not hasattr(main_detection_view, 'sector_stats_placeholder'):
            return False
        
        # 获取当前扇形信息
        sector_info = integration_helper.get_current_sector_info()
        
        if sector_info:
            stats_text = f"""扇形 {sector_info['id']} 统计:
孔位数: {sector_info['hole_count']}
合格: {sector_info['qualified_count']}
不合格: {sector_info['defective_count']}
进度: {sector_info['progress']:.1f}%"""
        else:
            stats_text = "扇形统计信息\n请选择扇形查看详情"
        
        main_detection_view.sector_stats_placeholder.setText(stats_text)
        return True
        
    except Exception as e:
        if hasattr(main_detection_view, 'logger'):
            main_detection_view.logger.error(f"更新扇形统计失败: {e}")
        return False