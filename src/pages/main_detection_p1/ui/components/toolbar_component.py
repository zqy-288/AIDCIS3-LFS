"""
Toolbar component for the main window.

This module implements the toolbar widget extracted from the original
main window, providing product selection, search, view controls, and
snake path configuration.
"""

import logging
from typing import Optional
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QPushButton, QLabel, QLineEdit, 
    QComboBox, QCheckBox, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from ..view_models.main_view_model import MainViewModel


class ToolbarComponent(QFrame):
    """
    Toolbar component containing product selection, search, and view controls.
    
    This component is extracted from the original main window toolbar
    functionality and emits signals for all user interactions.
    """
    
    # Signals for user interactions
    product_selection_requested = Signal()
    search_requested = Signal(str)  # search query
    view_filter_changed = Signal(str)  # filter type
    # 蛇形路径相关信号已移除
    
    def __init__(self, parent: Optional = None):
        """
        Initialize the toolbar component.
        
        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # UI elements
        self.product_select_btn: Optional[QPushButton] = None
        self.search_input: Optional[QLineEdit] = None
        self.search_btn: Optional[QPushButton] = None
        self.view_combo: Optional[QComboBox] = None
        # 蛇形路径相关UI元素已移除
        
        self._setup_ui()
        self._connect_signals()
        self.logger.debug("Toolbar component initialized")
    
    def _setup_ui(self) -> None:
        """Setup the toolbar UI layout."""
        self.setFrameStyle(QFrame.StyledPanel)
        self.setMaximumHeight(70)
        
        layout = QHBoxLayout(self)
        
        # Setup toolbar font
        toolbar_font = QFont()
        toolbar_font.setPointSize(11)
        
        # Product selection button
        self.product_select_btn = QPushButton("产品型号选择")
        self.product_select_btn.setMinimumSize(140, 45)
        self.product_select_btn.setFont(toolbar_font)
        layout.addWidget(self.product_select_btn)
        
        layout.addSpacing(20)
        
        # Search section
        search_label = QLabel("搜索:")
        search_label.setFont(toolbar_font)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入孔位ID...")
        self.search_input.setMinimumWidth(220)
        self.search_input.setMinimumHeight(35)
        self.search_input.setFont(toolbar_font)
        
        self.search_btn = QPushButton("搜索")
        self.search_btn.setMinimumSize(70, 35)
        self.search_btn.setFont(toolbar_font)
        
        layout.addWidget(search_label)
        layout.addWidget(self.search_input)
        layout.addWidget(self.search_btn)
        
        layout.addSpacing(20)
        
        # View controls
        view_label = QLabel("视图:")
        view_label.setFont(toolbar_font)
        
        self.view_combo = QComboBox()
        self.view_combo.addItems(["全部孔位", "待检孔位", "合格孔位", "异常孔位"])
        self.view_combo.setMinimumHeight(35)
        self.view_combo.setFont(toolbar_font)
        
        layout.addWidget(view_label)
        layout.addWidget(self.view_combo)
        
        layout.addSpacing(20)
        
        # 路径显示控件已移除 - 只保留实时点状态更新功能
        
        layout.addStretch()
    
    def _connect_signals(self) -> None:
        """Connect internal signals to slots."""
        try:
            # Product selection
            if self.product_select_btn:
                self.product_select_btn.clicked.connect(
                    lambda: self.product_selection_requested.emit()
                )
            
            # Search functionality
            if self.search_btn:
                self.search_btn.clicked.connect(self._on_search_clicked)
            
            if self.search_input:
                self.search_input.returnPressed.connect(self._on_search_clicked)
            
            # View filter
            if self.view_combo:
                self.view_combo.currentTextChanged.connect(self._on_view_filter_changed)
            
            # 蛇形路径控件已移除，无需连接信号
            
            self.logger.debug("Toolbar signals connected")
            
        except Exception as e:
            self.logger.error(f"Failed to connect toolbar signals: {e}")
    
    def _on_search_clicked(self) -> None:
        """Handle search button click or Enter key press."""
        if self.search_input:
            query = self.search_input.text().strip()
            if query:
                self.search_requested.emit(query)
                self.logger.debug(f"Search requested: {query}")
    
    def _on_view_filter_changed(self, text: str) -> None:
        """Handle view filter change."""
        # Map Chinese text to filter types
        filter_map = {
            "全部孔位": "all",
            "待检孔位": "pending", 
            "合格孔位": "qualified",
            "异常孔位": "defective"
        }
        
        filter_type = filter_map.get(text, "all")
        self.view_filter_changed.emit(filter_type)
        self.logger.debug(f"View filter changed to: {filter_type}")
    
    # 蛇形路径相关方法已移除
    
    def update_from_view_model(self, view_model: MainViewModel) -> None:
        """
        Update toolbar UI from view model.
        
        Args:
            view_model: Current view model state
        """
        try:
            # Update search input
            if self.search_input and view_model.search_query != self.search_input.text():
                self.search_input.setText(view_model.search_query)
            
            # Update view filter
            if self.view_combo:
                filter_map = {
                    "all": "全部孔位",
                    "pending": "待检孔位",
                    "qualified": "合格孔位", 
                    "defective": "异常孔位"
                }
                display_text = filter_map.get(view_model.view_filter, "全部孔位")
                current_text = self.view_combo.currentText()
                if display_text != current_text:
                    self.view_combo.setCurrentText(display_text)
            
            # 蛇形路径控件已移除，无需更新
            
            # Update product selection button if needed
            if self.product_select_btn and view_model.current_product:
                self.product_select_btn.setText(f"产品: {view_model.current_product}")
            elif self.product_select_btn:
                self.product_select_btn.setText("产品型号选择")
            
            self.logger.debug("Toolbar updated from view model")
            
        except Exception as e:
            self.logger.error(f"Failed to update toolbar from view model: {e}")
    
    def set_enabled(self, enabled: bool) -> None:
        """
        Enable or disable the toolbar.
        
        Args:
            enabled: Whether toolbar should be enabled
        """
        super().setEnabled(enabled)
        
        # Also update individual controls
        if self.product_select_btn:
            self.product_select_btn.setEnabled(enabled)
        if self.search_input:
            self.search_input.setEnabled(enabled)
        if self.search_btn:
            self.search_btn.setEnabled(enabled)
        if self.view_combo:
            self.view_combo.setEnabled(enabled)
        # 蛇形路径控件已移除，无需设置状态
    
    def clear_search(self) -> None:
        """Clear the search input."""
        if self.search_input:
            self.search_input.clear()
    
    def set_search_results_count(self, count: int) -> None:
        """
        Update search input placeholder with results count.
        
        Args:
            count: Number of search results
        """
        if self.search_input:
            if count > 0:
                self.search_input.setPlaceholderText(f"找到 {count} 个结果...")
            else:
                self.search_input.setPlaceholderText("输入孔位ID...")