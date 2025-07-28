"""
检测工具栏组件
从main_window.py重构提取的独立UI组件
"""

from PySide6.QtWidgets import (
    QWidget, QFrame, QHBoxLayout, QPushButton, 
    QLabel, QLineEdit, QComboBox
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont


class DetectionToolbar(QFrame):
    """
    检测工具栏组件
    负责产品选择、搜索功能、视图过滤等工具栏功能
    """
    
    # 定义信号
    product_select_requested = Signal()
    search_requested = Signal(str)  # 搜索文本
    view_filter_changed = Signal(str)  # 视图过滤类型
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """设置UI组件"""
        self.setFrameStyle(QFrame.StyledPanel)
        self.setMaximumHeight(70)
        
        layout = QHBoxLayout(self)
        
        # 设置工具栏字体
        self.toolbar_font = QFont()
        self.toolbar_font.setPointSize(11)
        
        # 产品选择按钮
        self.product_select_btn = QPushButton("产品型号选择")
        self.product_select_btn.setMinimumSize(140, 45)
        self.product_select_btn.setFont(self.toolbar_font)
        layout.addWidget(self.product_select_btn)
        
        layout.addSpacing(20)
        
        # 搜索功能区
        self._create_search_section(layout)
        
        layout.addSpacing(20)
        
        # 视图控制区
        self._create_view_section(layout)
        
        layout.addStretch()
    
    def _create_search_section(self, layout):
        """创建搜索功能区"""
        search_label = QLabel("搜索:")
        search_label.setFont(self.toolbar_font)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入孔位ID...")
        self.search_input.setMinimumWidth(220)
        self.search_input.setMinimumHeight(35)
        self.search_input.setFont(self.toolbar_font)
        
        self.search_btn = QPushButton("搜索")
        self.search_btn.setMinimumSize(70, 35)
        self.search_btn.setFont(self.toolbar_font)
        
        layout.addWidget(search_label)
        layout.addWidget(self.search_input)
        layout.addWidget(self.search_btn)
    
    def _create_view_section(self, layout):
        """创建视图控制区"""
        view_label = QLabel("视图:")
        view_label.setFont(self.toolbar_font)
        
        self.view_combo = QComboBox()
        self.view_combo.addItems(["全部孔位", "待检孔位", "合格孔位", "异常孔位"])
        self.view_combo.setMinimumHeight(35)
        self.view_combo.setFont(self.toolbar_font)
        
        layout.addWidget(view_label)
        layout.addWidget(self.view_combo)
    
    def setup_connections(self):
        """设置信号连接"""
        self.product_select_btn.clicked.connect(self.product_select_requested.emit)
        self.search_btn.clicked.connect(self._on_search_clicked)
        self.search_input.returnPressed.connect(self._on_search_clicked)
        self.view_combo.currentTextChanged.connect(self.view_filter_changed.emit)
    
    def _on_search_clicked(self):
        """处理搜索按钮点击"""
        search_text = self.search_input.text().strip()
        if search_text:
            self.search_requested.emit(search_text)
    
    def get_search_text(self) -> str:
        """获取搜索文本"""
        return self.search_input.text().strip()
    
    def set_search_text(self, text: str):
        """设置搜索文本"""
        self.search_input.setText(text)
    
    def get_selected_view_filter(self) -> str:
        """获取当前选中的视图过滤器"""
        return self.view_combo.currentText()
    
    def set_view_filter(self, filter_type: str):
        """设置视图过滤器"""
        index = self.view_combo.findText(filter_type)
        if index >= 0:
            self.view_combo.setCurrentIndex(index)
    
    def clear_search(self):
        """清空搜索框"""
        self.search_input.clear()
        
    def set_product_button_text(self, text: str):
        """设置产品选择按钮文本"""
        self.product_select_btn.setText(text)