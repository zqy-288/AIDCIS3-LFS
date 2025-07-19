"""
主题管理器重定向
将所有对旧主题管理器的引用重定向到新的统一版本
解决版本冲突问题
"""

import warnings
from .theme_manager_unified import get_unified_theme_manager

# 发出弃用警告
warnings.warn(
    "theme_manager模块已被统一，请使用theme_manager_unified模块",
    DeprecationWarning,
    stacklevel=2
)

# 重定向到统一的主题管理器
theme_manager = get_unified_theme_manager()

# 为了保持向后兼容，导出所有可能被使用的接口
ModernThemeManager = type(theme_manager)
get_theme_manager = get_unified_theme_manager

# 兼容旧的类方法调用
def apply_dark_theme_2d(figure, axes):
    """2D图表深色主题应用 - 兼容旧版本"""
    colors = theme_manager.COLORS
    figure.patch.set_facecolor(colors['background_secondary'])
    axes.set_facecolor(colors['background_secondary'])
    axes.spines['bottom'].set_color(colors['border_normal'])
    axes.spines['top'].set_color(colors['border_normal'])
    axes.spines['left'].set_color(colors['border_normal'])
    axes.spines['right'].set_color(colors['border_normal'])
    axes.tick_params(axis='x', colors=colors['text_primary'])
    axes.tick_params(axis='y', colors=colors['text_primary'])
    axes.xaxis.label.set_color(colors['text_primary'])
    axes.yaxis.label.set_color(colors['text_primary'])
    axes.title.set_color(colors['text_secondary'])
    axes.grid(True, color=colors['border_normal'], linestyle='--', alpha=0.5)

def apply_dark_theme_3d(figure, axes):
    """3D图表深色主题应用 - 兼容旧版本"""
    colors = theme_manager.COLORS
    figure.patch.set_facecolor(colors['background_primary'])
    axes.set_facecolor(colors['background_primary'])
    axes.xaxis.set_pane_color((0.1, 0.1, 0.1, 0.4))
    axes.yaxis.set_pane_color((0.1, 0.1, 0.1, 0.4))
    axes.zaxis.set_pane_color((0.1, 0.1, 0.1, 0.4))
    axes.xaxis.line.set_color(colors['border_normal'])
    axes.yaxis.line.set_color(colors['border_normal'])
    axes.zaxis.line.set_color(colors['border_normal'])
    axes.tick_params(axis='x', colors=colors['text_primary'])
    axes.tick_params(axis='y', colors=colors['text_primary'])
    axes.tick_params(axis='z', colors=colors['text_primary'])
    axes.set_xlabel(axes.get_xlabel(), color=colors['text_primary'])
    axes.set_ylabel(axes.get_ylabel(), color=colors['text_primary'])
    axes.set_zlabel(axes.get_zlabel(), color=colors['text_primary'])
    axes.set_title(axes.get_title(), color=colors['text_secondary'])

# 将类方法绑定到实例
theme_manager.apply_dark_theme_2d = apply_dark_theme_2d
theme_manager.apply_dark_theme_3d = apply_dark_theme_3d