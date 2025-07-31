"""
P1页面模块组件
包含产品选择、主题管理等功能
"""

from .product_selection import ProductSelectionDialog
from .theme_manager import ModernThemeManager

__all__ = [
    'ProductSelectionDialog',
    'ModernThemeManager'
]