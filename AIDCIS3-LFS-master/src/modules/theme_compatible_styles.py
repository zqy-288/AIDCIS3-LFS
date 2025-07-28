"""
主题兼容样式定义
提供预定义的主题兼容样式，避免硬编码
"""

from src.modules.theme_manager_unified import get_unified_theme_manager

def get_theme_compatible_styles():
    """获取主题兼容的样式定义"""
    theme_manager = get_unified_theme_manager()
    colors = theme_manager.COLORS
    
    return {
        'success_button': f"""
            QPushButton {{
                background-color: {colors['success']};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {colors['success']}DD;
            }}
            QPushButton:pressed {{
                background-color: {colors['success']}BB;
            }}
        """,
        
        'error_button': f"""
            QPushButton {{
                background-color: {colors['error']};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {colors['error']}DD;
            }}
            QPushButton:pressed {{
                background-color: {colors['error']}BB;
            }}
        """,
        
        'primary_button': f"""
            QPushButton {{
                background-color: {colors['accent_primary']};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {colors['accent_hover']};
            }}
            QPushButton:pressed {{
                background-color: {colors['accent_pressed']};
            }}
        """,
        
        'secondary_panel': f"""
            QGroupBox {{
                background-color: {colors['background_secondary']};
                border: 1px solid {colors['border_normal']};
                border-radius: 8px;
                margin-top: 10px;
                padding: 10px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                color: {colors['text_secondary']};
                font-size: 16px;
                font-weight: bold;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
            }}
        """,
        
        'input_field': f"""
            QLineEdit, QTextEdit {{
                background-color: {colors['background_secondary']};
                border: 1px solid {colors['border_normal']};
                border-radius: 4px;
                padding: 6px;
                color: {colors['text_primary']};
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border: 1px solid {colors['border_focus']};
            }}
        """,
        
        'table_style': f"""
            QTableWidget {{
                background-color: {colors['background_secondary']};
                gridline-color: {colors['border_normal']};
                border: 1px solid {colors['border_normal']};
                selection-background-color: {colors['selection']};
                selection-color: white;
                color: {colors['text_primary']};
            }}
            QHeaderView::section {{
                background-color: {colors['background_tertiary']};
                color: {colors['text_primary']};
                padding: 6px;
                border: none;
                font-weight: bold;
                border-right: 1px solid {colors['border_normal']};
                border-bottom: 1px solid {colors['border_normal']};
            }}
        """
    }

def apply_button_style(button, style_name):
    """应用按钮样式"""
    styles = get_theme_compatible_styles()
    if style_name in styles:
        button.setStyleSheet(styles[style_name])
    else:
        # 回退到ObjectName方式
        button.setObjectName(style_name)

def apply_widget_style(widget, style_name):
    """应用组件样式"""
    styles = get_theme_compatible_styles()
    if style_name in styles:
        widget.setStyleSheet(styles[style_name])
    else:
        # 回退到ObjectName方式
        widget.setObjectName(style_name)
