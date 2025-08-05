"""
统一主题管理器
基于ModernThemeManager的共享主题系统
"""

from .theme_manager import ModernThemeManager

# 统一的主题管理器接口
def get_theme_manager():
    """获取统一的主题管理器实例"""
    return ModernThemeManager

def apply_theme(app):
    """应用主题到应用程序"""
    app.setStyleSheet(ModernThemeManager.get_main_stylesheet())
    return True

def get_main_stylesheet():
    """获取主样式表"""
    return ModernThemeManager.get_main_stylesheet()

# 向后兼容的别名
UnifiedThemeManager = ModernThemeManager
get_unified_theme_manager = get_theme_manager
theme_manager = ModernThemeManager

__all__ = [
    'ModernThemeManager',
    'get_theme_manager', 
    'apply_theme',
    'get_main_stylesheet',
    'UnifiedThemeManager',
    'get_unified_theme_manager',
    'theme_manager'
]