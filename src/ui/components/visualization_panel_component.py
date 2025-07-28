"""
Visualization panel component for the main window.

This module implements the center visualization panel widget extracted from
the original main window, providing the main graphics view for hole detection
and visualization.
"""

import logging
from typing import Optional, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFrame,
    QPushButton, QLabel
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from ..view_models.main_view_model import MainViewModel


class StatusLegendWidget(QFrame):
    """Status legend widget showing color codes for different hole statuses."""
    
    def __init__(self, parent: Optional = None):
        """Initialize the status legend widget."""
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the status legend UI."""
        self.setFrameStyle(QFrame.Box)
        self.setMaximumHeight(50)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Status legend label
        legend_label = QLabel("状态图例:")
        legend_font = QFont()
        legend_font.setPointSize(10)
        legend_font.setBold(True)
        legend_label.setFont(legend_font)
        layout.addWidget(legend_label)
        
        # Status items
        status_items = [
            ("待检", "#E0E0E0"),
            ("合格", "#90EE90"),
            ("异常", "#FFB6C1"),
            ("盲孔", "#DDA0DD"),
            ("拉杆孔", "#87CEEB"),
            ("检测中", "#FFD700")
        ]
        
        for status_text, color in status_items:
            status_widget = self._create_status_item(status_text, color)
            layout.addWidget(status_widget)
        
        layout.addStretch()
    
    def _create_status_item(self, text: str, color: str) -> QWidget:
        """Create a single status legend item."""
        item_widget = QWidget()
        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(0, 0, 0, 0)
        item_layout.setSpacing(3)
        
        # Color indicator
        color_label = QLabel()
        color_label.setFixedSize(12, 12)
        color_label.setStyleSheet(f"background-color: {color}; border: 1px solid #888;")
        
        # Text label
        text_label = QLabel(text)
        text_font = QFont()
        text_font.setPointSize(9)
        text_label.setFont(text_font)
        
        item_layout.addWidget(color_label)
        item_layout.addWidget(text_label)
        
        return item_widget


class ViewControlsWidget(QFrame):
    """View controls widget for switching between different display modes."""
    
    # Signals
    view_mode_changed = Signal(str)  # view mode
    sector_navigation_requested = Signal(str)  # direction
    
    def __init__(self, parent: Optional = None):
        """Initialize the view controls widget."""
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # Control buttons
        self.macro_view_btn: Optional[QPushButton] = None
        self.micro_view_btn: Optional[QPushButton] = None
        self.panorama_view_btn: Optional[QPushButton] = None
        self.prev_sector_btn: Optional[QPushButton] = None
        self.next_sector_btn: Optional[QPushButton] = None
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self) -> None:
        """Setup the view controls UI."""
        self.setFrameStyle(QFrame.Box)
        self.setMaximumHeight(60)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # View mode controls
        view_label = QLabel("视图模式:")
        view_font = QFont()
        view_font.setPointSize(10)
        view_font.setBold(True)
        view_label.setFont(view_font)
        layout.addWidget(view_label)
        
        button_font = QFont()
        button_font.setPointSize(10)
        
        self.macro_view_btn = QPushButton("宏观视图")
        self.macro_view_btn.setFont(button_font)
        self.macro_view_btn.setCheckable(True)
        self.macro_view_btn.setChecked(True)
        layout.addWidget(self.macro_view_btn)
        
        self.micro_view_btn = QPushButton("微观视图")
        self.micro_view_btn.setFont(button_font)
        self.micro_view_btn.setCheckable(True)
        layout.addWidget(self.micro_view_btn)
        
        self.panorama_view_btn = QPushButton("全景视图")
        self.panorama_view_btn.setFont(button_font)
        self.panorama_view_btn.setCheckable(True)
        layout.addWidget(self.panorama_view_btn)
        
        layout.addSpacing(20)
        
        # Sector navigation
        nav_label = QLabel("扇形导航:")
        nav_label.setFont(view_font)
        layout.addWidget(nav_label)
        
        self.prev_sector_btn = QPushButton("◀ 上一扇形")
        self.prev_sector_btn.setFont(button_font)
        layout.addWidget(self.prev_sector_btn)
        
        self.next_sector_btn = QPushButton("下一扇形 ▶")
        self.next_sector_btn.setFont(button_font)
        layout.addWidget(self.next_sector_btn)
        
        layout.addStretch()
    
    def _connect_signals(self) -> None:
        """Connect internal signals."""
        if self.macro_view_btn:
            self.macro_view_btn.clicked.connect(lambda: self._on_view_mode_clicked("macro"))
        if self.micro_view_btn:
            self.micro_view_btn.clicked.connect(lambda: self._on_view_mode_clicked("micro"))
        if self.panorama_view_btn:
            self.panorama_view_btn.clicked.connect(lambda: self._on_view_mode_clicked("panorama"))
        
        if self.prev_sector_btn:
            self.prev_sector_btn.clicked.connect(lambda: self.sector_navigation_requested.emit("previous"))
        if self.next_sector_btn:
            self.next_sector_btn.clicked.connect(lambda: self.sector_navigation_requested.emit("next"))
    
    def _on_view_mode_clicked(self, mode: str) -> None:
        """Handle view mode button clicks."""
        # Update button states
        self.macro_view_btn.setChecked(mode == "macro")
        self.micro_view_btn.setChecked(mode == "micro")
        self.panorama_view_btn.setChecked(mode == "panorama")
        
        self.view_mode_changed.emit(mode)
        self.logger.debug(f"View mode changed to: {mode}")
    
    def update_view_mode(self, mode: str) -> None:
        """Update view mode buttons from external state."""
        self.macro_view_btn.setChecked(mode == "macro")
        self.micro_view_btn.setChecked(mode == "micro")
        self.panorama_view_btn.setChecked(mode == "panorama")


class MainVisualizationWidget(QWidget):
    """Main visualization widget placeholder for graphics view."""
    
    # Signals for user interactions
    hole_selected = Signal(str)  # hole_id
    sector_changed = Signal(object)  # sector object
    zoom_requested = Signal(float)  # zoom factor
    pan_requested = Signal(float, float)  # dx, dy
    
    def __init__(self, parent: Optional = None):
        """Initialize the main visualization widget."""
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._current_view_model: Optional[MainViewModel] = None
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the visualization widget UI."""
        self.setMinimumSize(800, 700)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        
        # Placeholder for actual graphics view
        # In the real implementation, this would be replaced with:
        # - DynamicSectorDisplayRefactored
        # - OptimizedGraphicsView
        # - Or other visualization components
        
        placeholder_label = QLabel("图形视图区域\n(将集成现有的DynamicSectorDisplay组件)")
        placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #888;
                background-color: #f0f0f0;
                color: #666;
                font-size: 14px;
            }
        """)
        
        layout.addWidget(placeholder_label)
        
        self.logger.debug("Main visualization widget initialized")
    
    def update_from_view_model(self, view_model: MainViewModel) -> None:
        """
        Update visualization from view model.
        
        Args:
            view_model: Current view model state
        """
        try:
            self._current_view_model = view_model
            
            # In real implementation, this would update:
            # - Hole display based on view_model.hole_collection
            # - Selected hole highlighting based on view_model.current_hole_id
            # - View filter based on view_model.view_filter
            # - Snake path display based on view_model.snake_path_enabled
            # - Sector display based on view_model.current_sector
            
            self.logger.debug("Visualization updated from view model")
            
        except Exception as e:
            self.logger.error(f"Failed to update visualization from view model: {e}")
    
    def set_hole_collection(self, hole_collection: Any) -> None:
        """
        Set the hole collection for display.
        
        Args:
            hole_collection: Hole collection to display
        """
        # This would integrate with the actual graphics view
        # For now, just emit a signal indicating data changed
        if hole_collection:
            self.logger.info("Hole collection updated in visualization")
    
    def select_hole(self, hole_id: str) -> None:
        """
        Select a hole in the visualization.
        
        Args:
            hole_id: ID of hole to select
        """
        # This would highlight the hole in the graphics view
        self.hole_selected.emit(hole_id)
        self.logger.debug(f"Hole selected in visualization: {hole_id}")
    
    def clear_selection(self) -> None:
        """Clear hole selection."""
        self.hole_selected.emit("")
        self.logger.debug("Hole selection cleared")


class VisualizationPanelComponent(QGroupBox):
    """
    Main visualization panel component for the center area.
    
    This component provides the main graphics display area with controls
    and status legend.
    """
    
    # Signals for user interactions
    hole_selected = Signal(str)  # hole_id
    sector_changed = Signal(object)  # sector object
    view_mode_changed = Signal(str)  # view mode
    
    def __init__(self, parent: Optional = None):
        """
        Initialize the visualization panel component.
        
        Args:
            parent: Optional parent widget
        """
        super().__init__("管孔检测视图", parent)
        self.logger = logging.getLogger(__name__)
        
        # Components
        self.status_legend: Optional[StatusLegendWidget] = None
        self.view_controls: Optional[ViewControlsWidget] = None
        self.main_visualization: Optional[MainVisualizationWidget] = None
        
        self._setup_ui()
        self._connect_signals()
        self.logger.debug("Visualization panel component initialized")
    
    def _setup_ui(self) -> None:
        """Setup the visualization panel UI."""
        # Set panel title font
        center_panel_font = QFont()
        center_panel_font.setPointSize(12)
        center_panel_font.setBold(True)
        self.setFont(center_panel_font)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Status legend
        self.status_legend = StatusLegendWidget()
        layout.addWidget(self.status_legend)
        
        # View controls
        self.view_controls = ViewControlsWidget()
        layout.addWidget(self.view_controls)
        
        # Main visualization area
        self.main_visualization = MainVisualizationWidget()
        layout.addWidget(self.main_visualization)
    
    def _connect_signals(self) -> None:
        """Connect component signals."""
        try:
            # View controls signals
            if self.view_controls:
                self.view_controls.view_mode_changed.connect(self.view_mode_changed.emit)
                self.view_controls.sector_navigation_requested.connect(
                    self._on_sector_navigation_requested
                )
            
            # Main visualization signals
            if self.main_visualization:
                self.main_visualization.hole_selected.connect(self.hole_selected.emit)
                self.main_visualization.sector_changed.connect(self.sector_changed.emit)
            
            self.logger.debug("Visualization panel signals connected")
            
        except Exception as e:
            self.logger.error(f"Failed to connect visualization panel signals: {e}")
    
    def _on_sector_navigation_requested(self, direction: str) -> None:
        """Handle sector navigation requests."""
        # This would calculate the next/previous sector based on current state
        # For now, emit a generic sector change
        self.sector_changed.emit({"navigation": direction})
        self.logger.debug(f"Sector navigation requested: {direction}")
    
    def update_from_view_model(self, view_model: MainViewModel) -> None:
        """
        Update visualization panel from view model.
        
        Args:
            view_model: Current view model state
        """
        try:
            # Update view controls
            if self.view_controls:
                self.view_controls.update_view_mode(view_model.view_mode)
            
            # Update main visualization
            if self.main_visualization:
                self.main_visualization.update_from_view_model(view_model)
            
            self.logger.debug("Visualization panel updated from view model")
            
        except Exception as e:
            self.logger.error(f"Failed to update visualization panel from view model: {e}")
    
    def set_hole_collection(self, hole_collection: Any) -> None:
        """
        Set hole collection for visualization.
        
        Args:
            hole_collection: Hole collection to display
        """
        if self.main_visualization:
            self.main_visualization.set_hole_collection(hole_collection)
    
    def select_hole(self, hole_id: str) -> None:
        """
        Select a hole in the visualization.
        
        Args:
            hole_id: ID of hole to select
        """
        if self.main_visualization:
            self.main_visualization.select_hole(hole_id)
    
    def clear_selection(self) -> None:
        """Clear hole selection."""
        if self.main_visualization:
            self.main_visualization.clear_selection()
    
    def set_view_mode(self, mode: str) -> None:
        """
        Set the view mode.
        
        Args:
            mode: View mode ("macro", "micro", "panorama")
        """
        if self.view_controls:
            self.view_controls.update_view_mode(mode)
    
    def get_visualization_widget(self) -> Optional[MainVisualizationWidget]:
        """
        Get the main visualization widget for direct access.
        
        Returns:
            Main visualization widget or None
        """
        return self.main_visualization