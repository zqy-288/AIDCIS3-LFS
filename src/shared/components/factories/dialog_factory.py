"""
对话框工厂
管理对话框组件的创建
"""

from typing import Optional, Any
from PySide6.QtWidgets import QWidget, QDialog, QVBoxLayout, QLabel, QPushButton


class DialogFactory:
    """
    对话框工厂类
    创建各种对话框组件
    """
    
    def __init__(self):
        self._dialog_cache = {}
        
    def create_product_selection_dialog(self, parent: Optional[QWidget] = None) -> Any:
        """创建产品选择对话框"""
        try:
            from src.modules.product_selection import ProductSelectionDialog
            return ProductSelectionDialog(parent)
        except ImportError:
            # 创建简单的占位对话框
            return self._create_placeholder_dialog("产品选择", parent)
            
    def create_file_dialog(self, parent: Optional[QWidget] = None) -> Any:
        """创建文件选择对话框"""
        from PySide6.QtWidgets import QFileDialog
        return QFileDialog(parent)
        
    def create_settings_dialog(self, parent: Optional[QWidget] = None) -> Any:
        """创建设置对话框"""
        return self._create_placeholder_dialog("设置", parent)
        
    def create_about_dialog(self, parent: Optional[QWidget] = None) -> Any:
        """创建关于对话框"""
        return self._create_placeholder_dialog("关于", parent)
        
    def _create_placeholder_dialog(self, title: str, parent: Optional[QWidget] = None) -> QDialog:
        """创建占位对话框"""
        dialog = QDialog(parent)
        dialog.setWindowTitle(title)
        dialog.setModal(True)
        
        layout = QVBoxLayout(dialog)
        
        label = QLabel(f"{title}对话框占位")
        label.setStyleSheet("padding: 20px; border: 1px solid gray;")
        layout.addWidget(label)
        
        button = QPushButton("确定")
        button.clicked.connect(dialog.accept)
        layout.addWidget(button)
        
        dialog.setLayout(layout)
        return dialog


# 全局对话框工厂实例
_global_dialog_factory = None


def get_dialog_factory() -> DialogFactory:
    """获取全局对话框工厂实例"""
    global _global_dialog_factory
    if _global_dialog_factory is None:
        _global_dialog_factory = DialogFactory()
    return _global_dialog_factory