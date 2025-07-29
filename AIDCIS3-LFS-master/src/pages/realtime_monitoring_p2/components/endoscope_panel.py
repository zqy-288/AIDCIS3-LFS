"""
内窥镜面板组件
负责显示内窥镜实时图像
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QToolButton
)
from PySide6.QtCore import Signal, Qt

# 尝试导入内窥镜视图
try:
    from src.modules.endoscope_view import EndoscopeView
    HAS_ENDOSCOPE = True
except ImportError:
    HAS_ENDOSCOPE = False


class EndoscopePanel(QWidget):
    """
    内窥镜面板组件
    封装内窥镜视图功能
    """
    
    # 信号定义
    save_snapshot_requested = Signal()
    fullscreen_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_hole_id = None
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面 - 移除重复标题，直接使用内窥镜视图"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 直接添加内窥镜视图，不添加额外的标题栏（避免重复）
        if HAS_ENDOSCOPE:
            self.endoscope_view = EndoscopeView()
            self.endoscope_view.setObjectName("EndoscopeWidget")
            self.endoscope_view.setMinimumHeight(250)  # 减少高度
            self.endoscope_view.setMinimumWidth(350)   # 减少宽度
            layout.addWidget(self.endoscope_view)
        else:
            # 创建占位符
            placeholder = QLabel("内窥镜视图不可用\n请检查模块导入")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setObjectName("EndoscopePlaceholder")
            placeholder.setMinimumHeight(300)
            placeholder.setStyleSheet("""
                QLabel#EndoscopePlaceholder {
                    background-color: #2b2b2b;
                    color: #888;
                    border: 2px dashed #555;
                    border-radius: 8px;
                    font-size: 16px;
                }
            """)
            layout.addWidget(placeholder)
            self.endoscope_view = placeholder
            
    def set_hole_id(self, hole_id: str):
        """设置当前孔位ID"""
        self.current_hole_id = hole_id
        if HAS_ENDOSCOPE and hasattr(self.endoscope_view, 'set_hole_id'):
            self.endoscope_view.set_hole_id(hole_id)
            
    def update_image(self, image_data):
        """更新图像显示"""
        if HAS_ENDOSCOPE and hasattr(self.endoscope_view, 'update_image'):
            self.endoscope_view.update_image(image_data)
            
    def clear_image(self):
        """清除图像"""
        if HAS_ENDOSCOPE and hasattr(self.endoscope_view, 'clear_image'):
            self.endoscope_view.clear_image()
            
    def display_image_by_index(self, index: int):
        """根据索引显示图像"""
        if HAS_ENDOSCOPE and hasattr(self.endoscope_view, 'display_image_by_index'):
            self.endoscope_view.display_image_by_index(index)
            
    def get_current_image(self):
        """获取当前图像"""
        if HAS_ENDOSCOPE and hasattr(self.endoscope_view, 'get_current_image'):
            return self.endoscope_view.get_current_image()
        return None
        
    def is_endoscope_available(self) -> bool:
        """检查内窥镜是否可用"""
        return HAS_ENDOSCOPE
