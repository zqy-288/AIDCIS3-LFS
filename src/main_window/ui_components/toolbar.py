"""工具栏组件"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QFrame, QPushButton, 
    QLabel, QLineEdit, QComboBox
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont


class ToolbarWidget(QFrame):
    """
    工具栏组件
    包含产品选择、搜索和视图控制
    """
    
    # 信号定义
    product_select_clicked = Signal()
    search_requested = Signal(str)
    view_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        self.setFrameStyle(QFrame.StyledPanel)
        self.setMaximumHeight(70)
        
        layout = QHBoxLayout(self)
        
        # 设置工具栏字体
        toolbar_font = QFont()
        toolbar_font.setPointSize(11)
        
        # 产品选择按钮
        self.product_select_btn = QPushButton("产品型号选择")
        self.product_select_btn.setMinimumSize(140, 45)
        self.product_select_btn.setFont(toolbar_font)
        self.product_select_btn.clicked.connect(self.product_select_clicked.emit)
        layout.addWidget(self.product_select_btn)
        
        layout.addSpacing(20)
        
        # 搜索框和搜索按钮
        search_label = QLabel("搜索:")
        search_label.setFont(toolbar_font)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入孔位ID...")
        self.search_input.setMinimumWidth(220)
        self.search_input.setMinimumHeight(35)
        self.search_input.setFont(toolbar_font)
        self.search_input.returnPressed.connect(self._on_search)
        
        # 搜索按钮
        self.search_btn = QPushButton("搜索")
        self.search_btn.setMinimumSize(70, 35)
        self.search_btn.setFont(toolbar_font)
        self.search_btn.clicked.connect(self._on_search)
        
        layout.addWidget(search_label)
        layout.addWidget(self.search_input)
        layout.addWidget(self.search_btn)
        
        layout.addSpacing(20)
        
        # 视图控制
        view_label = QLabel("视图:")
        view_label.setFont(toolbar_font)
        
        self.view_combo = QComboBox()
        self.view_combo.addItems(["全部孔位", "待检孔位", "合格孔位", "异常孔位"])
        self.view_combo.setMinimumHeight(35)
        self.view_combo.setFont(toolbar_font)
        self.view_combo.currentTextChanged.connect(self.view_changed.emit)
        
        layout.addWidget(view_label)
        layout.addWidget(self.view_combo)
        
        layout.addStretch()
        
    def _on_search(self):
        """处理搜索请求"""
        search_text = self.search_input.text().strip()
        if search_text:
            self.search_requested.emit(search_text)
            
    def set_search_completer(self, completer):
        """设置搜索框的自动完成器"""
        self.search_input.setCompleter(completer)
        
    def clear_search(self):
        """清空搜索框"""
        self.search_input.clear()
        
    def get_current_view(self) -> str:
        """获取当前视图选择"""
        return self.view_combo.currentText()