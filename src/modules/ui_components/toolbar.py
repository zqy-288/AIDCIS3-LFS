"""
顶部工具栏组件
从main_window.py重构提取的独立UI组件
负责产品型号选择、搜索功能、视图过滤等功能
"""

import logging
from typing import List, Optional

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QGroupBox,
    QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont


class MainToolbar(QWidget):
    """
    主检测视图顶部工具栏组件
    包含产品型号选择、搜索功能、视图过滤等功能
    """
    
    # 定义信号
    product_selected = Signal(str)  # 产品型号选择信号
    search_requested = Signal(str)  # 搜索请求信号
    filter_changed = Signal(str)    # 过滤器变化信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        try:
            self.setup_ui()
            self.setup_connections()
            self.logger.info("工具栏组件初始化完成")
        except Exception as e:
            self.logger.error(f"工具栏组件初始化失败: {e}")
            self._setup_error_ui()
    
    def setup_ui(self):
        """设置用户界面"""
        # 主布局 - 水平布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 5, 10, 5)
        main_layout.setSpacing(15)
        
        # 设置固定高度
        self.setFixedHeight(70)
        self.setMinimumHeight(70)
        self.setMaximumHeight(70)
        
        # 设置字体
        self.setup_fonts()
        
        # 1. 产品型号选择按钮
        self.create_product_selection_section(main_layout)
        
        # 2. 分隔线
        self.add_separator(main_layout)
        
        # 3. 搜索功能区域
        self.create_search_section(main_layout)
        
        # 4. 分隔线
        self.add_separator(main_layout)
        
        # 5. 视图过滤区域
        self.create_filter_section(main_layout)
        
        # 6. 弹性空间
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        main_layout.addItem(spacer)
    
    def setup_fonts(self):
        """设置字体"""
        # 工具栏按钮字体 (11pt)
        self.button_font = QFont()
        self.button_font.setPointSize(11)
        
        # 标签字体
        self.label_font = QFont()
        self.label_font.setPointSize(10)
    
    def create_product_selection_section(self, layout):
        """创建产品型号选择区域"""
        try:
            # 产品选择按钮 (140x45px，字体11pt)
            self.product_selection_btn = QPushButton("选择产品型号")
            self.product_selection_btn.setFont(self.button_font)
            self.product_selection_btn.setFixedSize(140, 45)
            self.product_selection_btn.setProperty("class", "ActionButton")
            self.product_selection_btn.setToolTip("点击选择产品型号")
            
            layout.addWidget(self.product_selection_btn)
            
        except Exception as e:
            self.logger.error(f"创建产品选择区域失败: {e}")
            # 添加占位符
            placeholder = QLabel("产品选择\n加载失败")
            placeholder.setFixedSize(140, 45)
            placeholder.setAlignment(Qt.AlignCenter)
            layout.addWidget(placeholder)
    
    def create_search_section(self, layout):
        """创建搜索功能区域"""
        try:
            # 搜索容器
            search_container = QWidget()
            search_layout = QHBoxLayout(search_container)
            search_layout.setContentsMargins(0, 0, 0, 0)
            search_layout.setSpacing(5)
            
            # 搜索标签
            search_label = QLabel("搜索:")
            search_label.setFont(self.label_font)
            search_layout.addWidget(search_label)
            
            # 搜索框 (220px宽，35px高)
            self.search_input = QLineEdit()
            self.search_input.setFont(self.button_font)
            self.search_input.setFixedSize(220, 35)
            self.search_input.setPlaceholderText("输入孔位ID进行搜索...")
            self.search_input.setToolTip("支持模糊搜索，按回车确认")
            search_layout.addWidget(self.search_input)
            
            # 搜索按钮
            self.search_btn = QPushButton("搜索")
            self.search_btn.setFont(self.button_font)
            self.search_btn.setFixedHeight(35)
            self.search_btn.setProperty("class", "ActionButton")
            self.search_btn.setToolTip("执行搜索")
            search_layout.addWidget(self.search_btn)
            
            layout.addWidget(search_container)
            
        except Exception as e:
            self.logger.error(f"创建搜索区域失败: {e}")
            # 添加占位符
            placeholder = QLabel("搜索功能\n加载失败")
            placeholder.setFixedSize(300, 45)
            placeholder.setAlignment(Qt.AlignCenter)
            layout.addWidget(placeholder)
    
    def create_filter_section(self, layout):
        """创建视图过滤区域"""
        try:
            # 过滤容器
            filter_container = QWidget()
            filter_layout = QHBoxLayout(filter_container)
            filter_layout.setContentsMargins(0, 0, 0, 0)
            filter_layout.setSpacing(5)
            
            # 过滤标签
            filter_label = QLabel("过滤:")
            filter_label.setFont(self.label_font)
            filter_layout.addWidget(filter_label)
            
            # 视图过滤下拉框
            self.filter_combo = QComboBox()
            self.filter_combo.setFont(self.button_font)
            self.filter_combo.setFixedHeight(35)
            self.filter_combo.setMinimumWidth(120)
            
            # 添加过滤选项
            filter_options = [
                "全部孔位",
                "待检孔位", 
                "合格孔位",
                "异常孔位"
            ]
            self.filter_combo.addItems(filter_options)
            self.filter_combo.setCurrentText("全部孔位")
            self.filter_combo.setToolTip("选择要显示的孔位类型")
            
            filter_layout.addWidget(self.filter_combo)
            
            layout.addWidget(filter_container)
            
        except Exception as e:
            self.logger.error(f"创建过滤区域失败: {e}")
            # 添加占位符
            placeholder = QLabel("过滤功能\n加载失败")
            placeholder.setFixedSize(200, 45)
            placeholder.setAlignment(Qt.AlignCenter)
            layout.addWidget(placeholder)
    
    def add_separator(self, layout):
        """添加分隔线"""
        try:
            separator = QLabel("|")
            separator.setFont(self.label_font)
            separator.setAlignment(Qt.AlignCenter)
            separator.setStyleSheet("color: #cccccc; font-size: 16px;")
            layout.addWidget(separator)
        except Exception as e:
            self.logger.error(f"添加分隔线失败: {e}")
    
    def _setup_error_ui(self):
        """设置错误UI"""
        layout = QHBoxLayout(self)
        error_label = QLabel("⚠️ 工具栏加载失败")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(error_label)
        self.setFixedHeight(70)
    
    def setup_connections(self):
        """设置信号连接"""
        try:
            # 产品选择按钮信号
            if hasattr(self, 'product_selection_btn'):
                self.product_selection_btn.clicked.connect(self._on_product_selection_clicked)
            
            # 搜索相关信号
            if hasattr(self, 'search_btn'):
                self.search_btn.clicked.connect(self._on_search_clicked)
            if hasattr(self, 'search_input'):
                self.search_input.returnPressed.connect(self._on_search_clicked)
            
            # 过滤器信号
            if hasattr(self, 'filter_combo'):
                self.filter_combo.currentTextChanged.connect(self._on_filter_changed)
                
        except Exception as e:
            self.logger.error(f"设置信号连接失败: {e}")
    
    def _on_product_selection_clicked(self):
        """处理产品选择按钮点击"""
        try:
            self.logger.info("产品选择按钮被点击")
            # 发送产品选择请求信号，由主视图处理具体的对话框逻辑
            self.product_selected.emit("open_dialog")
        except Exception as e:
            self.logger.error(f"处理产品选择失败: {e}")
    
    def _on_search_clicked(self):
        """处理搜索按钮点击或回车"""
        try:
            if hasattr(self, 'search_input'):
                search_text = self.search_input.text().strip()
                if search_text:
                    self.logger.info(f"执行搜索: {search_text}")
                    self.search_requested.emit(search_text)
                else:
                    self.logger.warning("搜索文本为空")
        except Exception as e:
            self.logger.error(f"处理搜索失败: {e}")
    
    def _on_filter_changed(self, filter_text):
        """处理过滤器变化"""
        try:
            self.logger.info(f"过滤器变化: {filter_text}")
            self.filter_changed.emit(filter_text)
        except Exception as e:
            self.logger.error(f"处理过滤器变化失败: {e}")
    
    # 公共方法
    def set_product_name(self, product_name: str):
        """设置当前产品名称"""
        try:
            if hasattr(self, 'product_selection_btn'):
                display_name = product_name if len(product_name) <= 12 else f"{product_name[:9]}..."
                self.product_selection_btn.setText(display_name)
                self.product_selection_btn.setToolTip(f"当前产品: {product_name}")
        except Exception as e:
            self.logger.error(f"设置产品名称失败: {e}")
    
    def set_search_text(self, text: str):
        """设置搜索框文本"""
        try:
            if hasattr(self, 'search_input'):
                self.search_input.setText(text)
        except Exception as e:
            self.logger.error(f"设置搜索文本失败: {e}")
    
    def get_search_text(self) -> str:
        """获取搜索框文本"""
        try:
            if hasattr(self, 'search_input'):
                return self.search_input.text().strip()
            return ""
        except Exception as e:
            self.logger.error(f"获取搜索文本失败: {e}")
            return ""
    
    def set_filter_option(self, option: str):
        """设置过滤选项"""
        try:
            if hasattr(self, 'filter_combo'):
                index = self.filter_combo.findText(option)
                if index >= 0:
                    self.filter_combo.setCurrentIndex(index)
        except Exception as e:
            self.logger.error(f"设置过滤选项失败: {e}")
    
    def get_current_filter(self) -> str:
        """获取当前过滤选项"""
        try:
            if hasattr(self, 'filter_combo'):
                return self.filter_combo.currentText()
            return "全部孔位"
        except Exception as e:
            self.logger.error(f"获取当前过滤选项失败: {e}")
            return "全部孔位"
    
    def set_enabled(self, enabled: bool):
        """设置工具栏是否可用"""
        try:
            if hasattr(self, 'product_selection_btn'):
                self.product_selection_btn.setEnabled(enabled)
            if hasattr(self, 'search_btn'):
                self.search_btn.setEnabled(enabled)
            if hasattr(self, 'search_input'):
                self.search_input.setEnabled(enabled)
            if hasattr(self, 'filter_combo'):
                self.filter_combo.setEnabled(enabled)
        except Exception as e:
            self.logger.error(f"设置工具栏状态失败: {e}")
    
    def update_search_suggestions(self, suggestions: List[str]):
        """更新搜索建议"""
        try:
            if hasattr(self, 'search_input'):
                from PySide6.QtWidgets import QCompleter
                from PySide6.QtCore import QStringListModel
                
                completer = QCompleter(suggestions, self)
                completer.setCaseSensitivity(Qt.CaseInsensitive)
                completer.setFilterMode(Qt.MatchContains)
                self.search_input.setCompleter(completer)
                
                self.logger.info(f"更新搜索建议完成，共 {len(suggestions)} 项")
        except Exception as e:
            self.logger.error(f"更新搜索建议失败: {e}")