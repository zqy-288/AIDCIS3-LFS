"""
视图工厂
管理视图组件的创建
"""

from typing import Optional, Any
from PySide6.QtWidgets import QWidget, QLabel


class ViewFactory:
    """
    视图工厂类
    创建各种视图组件
    """
    
    def __init__(self):
        self._view_cache = {}
        
    def create_graphics_view(self, parent: Optional[QWidget] = None) -> Any:
        """创建图形视图"""
        try:
            from src.pages.main_detection_p1.graphics.core.graphics_view import OptimizedGraphicsView
            return OptimizedGraphicsView(parent)
        except ImportError:
            return self._create_placeholder_view("图形视图", parent)
            
    def create_table_view(self, parent: Optional[QWidget] = None) -> Any:
        """创建表格视图"""
        from PySide6.QtWidgets import QTableView
        return QTableView(parent)
        
    def create_tree_view(self, parent: Optional[QWidget] = None) -> Any:
        """创建树形视图"""
        from PySide6.QtWidgets import QTreeView
        return QTreeView(parent)
        
    def create_list_view(self, parent: Optional[QWidget] = None) -> Any:
        """创建列表视图"""
        from PySide6.QtWidgets import QListView
        return QListView(parent)
        
    def _create_placeholder_view(self, name: str, parent: Optional[QWidget] = None) -> QLabel:
        """创建占位视图"""
        label = QLabel(f"{name}占位", parent)
        label.setStyleSheet("border: 1px solid gray; padding: 20px; background-color: #f0f0f0;")
        label.setMinimumSize(300, 200)
        return label


# 全局视图工厂实例
_global_view_factory = None


def get_view_factory() -> ViewFactory:
    """获取全局视图工厂实例"""
    global _global_view_factory
    if _global_view_factory is None:
        _global_view_factory = ViewFactory()
    return _global_view_factory