"""
布局工厂
解决重复的布局配置问题，提供标准化的布局创建
"""

from typing import Tuple, Optional, Dict, Any
from PySide6.QtWidgets import (
    QFormLayout, QVBoxLayout, QHBoxLayout, QGridLayout,
    QWidget, QGroupBox, QScrollArea
)
from PySide6.QtCore import Qt


class LayoutFactory:
    """布局工厂类"""
    
    # 标准配置常量
    STANDARD_FORM_CONFIG = {
        'field_growth_policy': QFormLayout.ExpandingFieldsGrow,
        'label_alignment': Qt.AlignRight | Qt.AlignVCenter,
        'form_alignment': Qt.AlignLeft | Qt.AlignTop,
        'horizontal_spacing': 10,
        'vertical_spacing': 8,
        'margins': (15, 15, 15, 15)
    }
    
    COMPACT_FORM_CONFIG = {
        'field_growth_policy': QFormLayout.ExpandingFieldsGrow,
        'label_alignment': Qt.AlignRight | Qt.AlignVCenter,
        'form_alignment': Qt.AlignLeft | Qt.AlignTop,
        'horizontal_spacing': 8,
        'vertical_spacing': 6,
        'margins': (10, 10, 10, 10)
    }
    
    STANDARD_PANEL_CONFIG = {
        'margins': (10, 8, 10, 8),
        'spacing': 12
    }
    
    COMPACT_PANEL_CONFIG = {
        'margins': (8, 6, 8, 6),
        'spacing': 8
    }
    
    @classmethod
    def create_standard_form_layout(cls, 
                                   config: Optional[Dict[str, Any]] = None) -> QFormLayout:
        """
        创建标准表单布局
        
        Args:
            config: 自定义配置，会覆盖默认配置
            
        Returns:
            QFormLayout: 配置好的表单布局
        """
        layout = QFormLayout()
        
        # 应用配置
        final_config = cls.STANDARD_FORM_CONFIG.copy()
        if config:
            final_config.update(config)
        
        layout.setFieldGrowthPolicy(final_config['field_growth_policy'])
        layout.setLabelAlignment(final_config['label_alignment'])
        layout.setFormAlignment(final_config['form_alignment'])
        layout.setHorizontalSpacing(final_config['horizontal_spacing'])
        layout.setVerticalSpacing(final_config['vertical_spacing'])
        layout.setContentsMargins(*final_config['margins'])
        
        return layout
    
    @classmethod
    def create_compact_form_layout(cls,
                                  config: Optional[Dict[str, Any]] = None) -> QFormLayout:
        """
        创建紧凑表单布局
        
        Args:
            config: 自定义配置
            
        Returns:
            QFormLayout: 配置好的紧凑表单布局
        """
        layout = QFormLayout()
        
        final_config = cls.COMPACT_FORM_CONFIG.copy()
        if config:
            final_config.update(config)
        
        layout.setFieldGrowthPolicy(final_config['field_growth_policy'])
        layout.setLabelAlignment(final_config['label_alignment'])
        layout.setFormAlignment(final_config['form_alignment'])
        layout.setHorizontalSpacing(final_config['horizontal_spacing'])
        layout.setVerticalSpacing(final_config['vertical_spacing'])
        layout.setContentsMargins(*final_config['margins'])
        
        return layout
    
    @classmethod
    def create_panel_layout(cls, 
                           compact: bool = False,
                           config: Optional[Dict[str, Any]] = None) -> QVBoxLayout:
        """
        创建面板布局
        
        Args:
            compact: 是否使用紧凑模式
            config: 自定义配置
            
        Returns:
            QVBoxLayout: 配置好的面板布局
        """
        layout = QVBoxLayout()
        
        base_config = cls.COMPACT_PANEL_CONFIG if compact else cls.STANDARD_PANEL_CONFIG
        final_config = base_config.copy()
        if config:
            final_config.update(config)
        
        layout.setContentsMargins(*final_config['margins'])
        layout.setSpacing(final_config['spacing'])
        
        return layout
    
    @classmethod
    def create_scrollable_panel(cls, 
                               title: str,
                               compact: bool = False,
                               fixed_width: Optional[int] = None) -> Tuple[QScrollArea, QWidget, QVBoxLayout]:
        """
        创建可滚动面板
        
        Args:
            title: 面板标题
            compact: 是否使用紧凑模式
            fixed_width: 固定宽度
            
        Returns:
            Tuple[QScrollArea, QWidget, QVBoxLayout]: 滚动区域、内容面板、布局
        """
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        if fixed_width:
            scroll_area.setFixedWidth(fixed_width)
        
        # 创建内容面板
        content_panel = QWidget()
        layout = cls.create_panel_layout(compact)
        content_panel.setLayout(layout)
        
        # 设置滚动区域的内容
        scroll_area.setWidget(content_panel)
        
        return scroll_area, content_panel, layout
    
    @classmethod
    def create_info_panel(cls, 
                         title: str,
                         compact: bool = False) -> Tuple[QGroupBox, QFormLayout]:
        """
        创建信息面板（使用表单布局）
        
        Args:
            title: 面板标题
            compact: 是否使用紧凑模式
            
        Returns:
            Tuple[QGroupBox, QFormLayout]: 面板组件、表单布局
        """
        panel = QGroupBox(title)
        
        if compact:
            layout = cls.create_compact_form_layout()
        else:
            layout = cls.create_standard_form_layout()
        
        panel.setLayout(layout)
        
        return panel, layout
    
    @classmethod
    def create_control_panel(cls,
                            title: str,
                            rows: int = 2,
                            cols: int = 2,
                            spacing: int = 8) -> Tuple[QGroupBox, QGridLayout]:
        """
        创建控制面板（使用网格布局）
        
        Args:
            title: 面板标题
            rows: 网格行数
            cols: 网格列数
            spacing: 间距
            
        Returns:
            Tuple[QGroupBox, QGridLayout]: 面板组件、网格布局
        """
        panel = QGroupBox(title)
        layout = QGridLayout()
        layout.setSpacing(spacing)
        layout.setContentsMargins(15, 15, 15, 15)
        
        panel.setLayout(layout)
        
        return panel, layout
    
    @classmethod
    def create_three_column_layout(cls,
                                  left_width: int = 360,
                                  right_width: int = 320,
                                  spacing: int = 12,
                                  margins: Tuple[int, int, int, int] = (8, 8, 8, 8)) -> Tuple[QHBoxLayout, QWidget, QWidget, QWidget]:
        """
        创建三栏布局
        
        Args:
            left_width: 左栏宽度
            right_width: 右栏宽度
            spacing: 栏间距
            margins: 边距
            
        Returns:
            Tuple[QHBoxLayout, QWidget, QWidget, QWidget]: 布局、左栏、中栏、右栏
        """
        layout = QHBoxLayout()
        layout.setContentsMargins(*margins)
        layout.setSpacing(spacing)
        
        # 创建三栏
        left_panel = QWidget()
        middle_panel = QWidget()
        right_panel = QWidget()
        
        # 设置固定宽度
        left_panel.setFixedWidth(left_width)
        right_panel.setFixedWidth(right_width)
        
        # 添加到布局
        layout.addWidget(left_panel)
        layout.addWidget(middle_panel, 1)  # 中栏占据更多空间
        layout.addWidget(right_panel)
        
        return layout, left_panel, middle_panel, right_panel


# 便捷函数
def create_standard_form_panel(title: str) -> Tuple[QGroupBox, QFormLayout]:
    """创建标准表单面板"""
    return LayoutFactory.create_info_panel(title, compact=False)

def create_compact_form_panel(title: str) -> Tuple[QGroupBox, QFormLayout]:
    """创建紧凑表单面板"""
    return LayoutFactory.create_info_panel(title, compact=True)

def create_button_grid_panel(title: str, rows: int = 2, cols: int = 2) -> Tuple[QGroupBox, QGridLayout]:
    """创建按钮网格面板"""
    return LayoutFactory.create_control_panel(title, rows, cols)