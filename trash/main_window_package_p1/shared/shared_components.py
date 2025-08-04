"""
共享组件管理器
"""

from PySide6.QtCore import QObject


class SharedComponents(QObject):
    """共享组件管理器"""
    
    def __init__(self):
        super().__init__()
        self.components = {}
        
    def register_component(self, name: str, component):
        """注册共享组件"""
        self.components[name] = component
        
    def get_component(self, name: str):
        """获取共享组件"""
        return self.components.get(name)
        
    def cleanup(self):
        """清理资源"""
        self.components.clear()