"""
工具栏组件模块
从main_window.py中提取的独立UI组件创建函数
"""

from typing import Optional
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QPushButton, QLabel, QLineEdit, 
    QComboBox, QWidget
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt


def create_main_toolbar(
    toolbar_font_size: int = 11,
    toolbar_height: int = 70,
    button_min_size: tuple = (140, 45),
    search_input_min_size: tuple = (220, 35),
    search_btn_min_size: tuple = (70, 35)
) -> tuple[QWidget, dict]:
    """
    创建主工具栏
    
    Args:
        toolbar_font_size: 工具栏字体大小
        toolbar_height: 工具栏高度
        button_min_size: 按钮最小尺寸 (width, height)
        search_input_min_size: 搜索框最小尺寸 (width, height)
        search_btn_min_size: 搜索按钮最小尺寸 (width, height)
    
    Returns:
        tuple: (toolbar_widget, components_dict)
        - toolbar_widget: 创建的工具栏组件
        - components_dict: 包含所有子组件的字典，键为组件名称
    """
    toolbar = QFrame()
    toolbar.setFrameStyle(QFrame.StyledPanel)
    toolbar.setMaximumHeight(toolbar_height)

    layout = QHBoxLayout(toolbar)

    # 设置工具栏字体
    toolbar_font = QFont()
    toolbar_font.setPointSize(toolbar_font_size)

    # 产品选择按钮
    product_select_btn = QPushButton("产品型号选择")
    product_select_btn.setMinimumSize(*button_min_size)
    product_select_btn.setFont(toolbar_font)
    layout.addWidget(product_select_btn)

    layout.addSpacing(20)

    # 搜索框和搜索按钮
    search_label = QLabel("搜索:")
    search_label.setFont(toolbar_font)

    search_input = QLineEdit()
    search_input.setPlaceholderText("输入孔位ID...")
    search_input.setMinimumWidth(search_input_min_size[0])
    search_input.setMinimumHeight(search_input_min_size[1])
    search_input.setFont(toolbar_font)

    # 搜索按钮
    search_btn = QPushButton("搜索")
    search_btn.setMinimumSize(*search_btn_min_size)
    search_btn.setFont(toolbar_font)

    layout.addWidget(search_label)
    layout.addWidget(search_input)
    layout.addWidget(search_btn)

    layout.addSpacing(20)

    # 视图控制
    view_label = QLabel("视图:")
    view_label.setFont(toolbar_font)

    view_combo = QComboBox()
    view_combo.addItems(["全部孔位", "待检孔位", "合格孔位", "异常孔位"])
    view_combo.setMinimumHeight(search_input_min_size[1])
    view_combo.setFont(toolbar_font)

    layout.addWidget(view_label)
    layout.addWidget(view_combo)

    layout.addStretch()

    # 返回组件字典，便于外部访问
    components = {
        'product_select_btn': product_select_btn,
        'search_input': search_input,
        'search_btn': search_btn,
        'view_combo': view_combo,
        'search_label': search_label,
        'view_label': view_label
    }

    return toolbar, components


def create_status_legend(
    legend_height: int = 50,
    legend_font_size: int = 11,
    color_indicator_size: tuple = (16, 16),
    spacing: int = 15
) -> QWidget:
    """
    创建状态图例组件
    
    Args:
        legend_height: 图例高度
        legend_font_size: 图例字体大小
        color_indicator_size: 颜色指示器尺寸 (width, height)
        spacing: 图例项间距
    
    Returns:
        QWidget: 创建的状态图例组件
    """
    from src.core_business.models.hole_data import HoleStatus
    
    legend_frame = QFrame()
    legend_frame.setFrameStyle(QFrame.StyledPanel)
    legend_frame.setMaximumHeight(legend_height)

    layout = QHBoxLayout(legend_frame)
    layout.setContentsMargins(8, 8, 8, 8)

    # 从图形组件获取状态颜色
    try:
        from src.core_business.graphics.hole_graphics_item import HoleGraphicsItem
        status_colors = HoleGraphicsItem.STATUS_COLORS
    except:
        # 默认颜色映射
        status_colors = {
            HoleStatus.PENDING: "#CCCCCC",
            HoleStatus.QUALIFIED: "#4CAF50",
            HoleStatus.DEFECTIVE: "#F44336",
            HoleStatus.BLIND: "#FF9800",
            HoleStatus.TIE_ROD: "#9C27B0",
            HoleStatus.PROCESSING: "#2196F3"
        }

    status_names = {
        HoleStatus.PENDING: "待检",
        HoleStatus.QUALIFIED: "合格",
        HoleStatus.DEFECTIVE: "异常",
        HoleStatus.BLIND: "盲孔",
        HoleStatus.TIE_ROD: "拉杆孔",
        HoleStatus.PROCESSING: "检测中"
    }

    # 设置图例字体
    legend_font = QFont()
    legend_font.setPointSize(legend_font_size)

    for status, color in status_colors.items():
        # 颜色指示器
        color_label = QLabel()
        color_label.setFixedSize(*color_indicator_size)
        
        # 将QColor对象转换为CSS颜色字符串
        if hasattr(color, 'name'):
            # QColor对象，转换为十六进制颜色
            css_color = color.name()
        elif isinstance(color, str):
            # 已经是字符串颜色
            css_color = color if color.startswith('#') else f"#{color}"
        else:
            # 其他类型，尝试转换
            css_color = str(color)
        
        # 直接设置背景色样式
        color_label.setStyleSheet(f"""
            QLabel {{
                background-color: {css_color};
                border: 1px solid #999;
                border-radius: 2px;
            }}
        """)
        color_label.setObjectName("StatusColorLabel")

        # 状态文本
        text_label = QLabel(status_names.get(status, status.value))
        text_label.setFont(legend_font)

        layout.addWidget(color_label)
        layout.addWidget(text_label)
        layout.addSpacing(spacing)

    layout.addStretch()
    return legend_frame