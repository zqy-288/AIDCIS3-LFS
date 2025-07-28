"""
视图模型管理器
"""

from PySide6.QtCore import QObject, Signal


class ViewModelManager(QObject):
    """视图模型管理器"""
    
    state_changed = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self.view_model = {}
        
    def get_view_model(self):
        """获取视图模型"""
        return self.view_model
        
    def update_state(self, key: str, value):
        """更新状态"""
        self.view_model[key] = value
        self.state_changed.emit(self.view_model)