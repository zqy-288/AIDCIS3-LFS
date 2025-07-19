"""
统一样式管理器
解决重复的样式定义问题，提供一致的UI样式
"""

from typing import Dict, Any, Optional
from enum import Enum


class ButtonVariant(Enum):
    """按钮变体枚举"""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    SUCCESS = "success"
    WARNING = "warning"
    DANGER = "danger"


class ButtonSize(Enum):
    """按钮尺寸枚举"""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class StyleManager:
    """统一样式管理器"""
    
    # 颜色配置
    COLORS = {
        'primary': '#2196F3',
        'primary_hover': '#1976D2',
        'primary_pressed': '#1565C0',
        'secondary': '#757575',
        'secondary_hover': '#616161',
        'success': '#4CAF50',
        'success_hover': '#45A049',
        'warning': '#FF9800',
        'warning_hover': '#F57C00',
        'danger': '#F44336',
        'danger_hover': '#D32F2F',
        'disabled': '#BDBDBD',
        'disabled_text': '#757575',
        'white': '#FFFFFF'
    }
    
    # 尺寸配置
    BUTTON_SIZES = {
        ButtonSize.SMALL: {
            'padding': '6px 10px',
            'font_size': '10px',
            'min_height': '14px',
            'min_width': '60px',
            'border_radius': '4px'
        },
        ButtonSize.MEDIUM: {
            'padding': '8px 12px',
            'font_size': '11px',
            'min_height': '16px',
            'min_width': '70px',
            'border_radius': '6px'
        },
        ButtonSize.LARGE: {
            'padding': '10px 16px',
            'font_size': '12px',
            'min_height': '20px',
            'min_width': '80px',
            'border_radius': '8px'
        }
    }
    
    @classmethod
    def get_button_style(cls, 
                        variant: ButtonVariant = ButtonVariant.PRIMARY,
                        size: ButtonSize = ButtonSize.MEDIUM,
                        custom_props: Optional[Dict[str, str]] = None) -> str:
        """
        获取按钮样式
        
        Args:
            variant: 按钮变体
            size: 按钮尺寸
            custom_props: 自定义属性
            
        Returns:
            str: CSS样式字符串
        """
        # 获取尺寸配置
        size_config = cls.BUTTON_SIZES[size]
        
        # 获取颜色配置
        base_color = cls.COLORS[variant.value]
        hover_color = cls.COLORS[f'{variant.value}_hover']
        
        # 基础样式
        style = f"""
            QPushButton {{
                background-color: {base_color};
                border: none;
                border-radius: {size_config['border_radius']};
                color: {cls.COLORS['white']};
                font-weight: 500;
                font-size: {size_config['font_size']};
                padding: {size_config['padding']};
                min-height: {size_config['min_height']};
                min-width: {size_config['min_width']};
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {hover_color};
                border: 1px solid {cls.COLORS[f'{variant.value}_pressed'] if f'{variant.value}_pressed' in cls.COLORS else hover_color};
            }}
            QPushButton:disabled {{
                background-color: {cls.COLORS['disabled']};
                color: {cls.COLORS['disabled_text']};
            }}
        """
        
        # 应用自定义属性
        if custom_props:
            custom_style = "\n".join([
                f"QPushButton {{ {prop}: {value}; }}"
                for prop, value in custom_props.items()
            ])
            style += "\n" + custom_style
            
        return style
    
    @classmethod
    def apply_button_style(cls, button, 
                          variant: ButtonVariant = ButtonVariant.PRIMARY,
                          size: ButtonSize = ButtonSize.MEDIUM,
                          custom_props: Optional[Dict[str, str]] = None):
        """
        应用按钮样式到按钮组件
        
        Args:
            button: 按钮组件
            variant: 按钮变体
            size: 按钮尺寸
            custom_props: 自定义属性
        """
        style = cls.get_button_style(variant, size, custom_props)
        button.setStyleSheet(style)
        
        # 设置属性用于CSS选择器
        button.setProperty("variant", variant.value)
        button.setProperty("size", size.value)
    
    @classmethod
    def apply_button_styles(cls, *buttons, 
                           variant: ButtonVariant = ButtonVariant.PRIMARY,
                           size: ButtonSize = ButtonSize.MEDIUM,
                           custom_props: Optional[Dict[str, str]] = None):
        """
        批量应用按钮样式
        
        Args:
            buttons: 按钮组件列表
            variant: 按钮变体
            size: 按钮尺寸
            custom_props: 自定义属性
        """
        for button in buttons:
            if button:
                cls.apply_button_style(button, variant, size, custom_props)
    
    @classmethod
    def get_panel_style(cls, title_bg: str = "#FAFAFA", 
                       border_color: str = "#D0D0D0") -> str:
        """
        获取面板样式
        
        Args:
            title_bg: 标题背景色
            border_color: 边框颜色
            
        Returns:
            str: CSS样式字符串
        """
        return f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 12px;
                border: 1px solid {border_color};
                border-radius: 10px;
                margin-top: 12px;
                padding-top: 12px;
                background-color: {title_bg};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: #555555;
                background-color: white;
                border-radius: 4px;
            }}
        """
    
    @classmethod
    def apply_panel_style(cls, panel, **kwargs):
        """
        应用面板样式
        
        Args:
            panel: 面板组件
            **kwargs: 样式参数
        """
        style = cls.get_panel_style(**kwargs)
        panel.setStyleSheet(style)


# 便捷函数
def apply_primary_button_style(button, size=ButtonSize.MEDIUM):
    """应用主要按钮样式"""
    StyleManager.apply_button_style(button, ButtonVariant.PRIMARY, size)

def apply_secondary_button_style(button, size=ButtonSize.MEDIUM):
    """应用次要按钮样式"""
    StyleManager.apply_button_style(button, ButtonVariant.SECONDARY, size)

def apply_success_button_style(button, size=ButtonSize.MEDIUM):
    """应用成功按钮样式"""
    StyleManager.apply_button_style(button, ButtonVariant.SUCCESS, size)

def apply_warning_button_style(button, size=ButtonSize.MEDIUM):
    """应用警告按钮样式"""
    StyleManager.apply_button_style(button, ButtonVariant.WARNING, size)

def apply_danger_button_style(button, size=ButtonSize.MEDIUM):
    """应用危险按钮样式"""
    StyleManager.apply_button_style(button, ButtonVariant.DANGER, size)