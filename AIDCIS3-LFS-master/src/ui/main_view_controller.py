"""
MainViewController implementation for the MVVM architecture.

This module implements the main UI controller that handles all UI display
and user interaction logic, completely decoupled from business logic.
"""

import logging
from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QSplitter, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication

from ..interfaces.main_interfaces import UserAction
from ..exceptions.main_exceptions import ViewControllerError
from .view_models.main_view_model import MainViewModel, MessageLevel
from .components.toolbar_component import ToolbarComponent
from .components.info_panel_component import InfoPanelComponent  
from .components.visualization_panel_component import VisualizationPanelComponent
from .components.operations_panel_component import OperationsPanelComponent


class MainViewController(QMainWindow):
    """
    Main view controller implementing the UI layer of MVVM pattern.
    
    This class handles all UI display and user interaction, emitting signals
    for user actions without containing any business logic.
    """
    
    # User action signal - emitted for all user interactions
    user_action = Signal(object)  # UserAction object
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the main view controller.
        
        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # UI components
        self.toolbar_component: Optional[ToolbarComponent] = None
        self.info_panel_component: Optional[InfoPanelComponent] = None
        self.visualization_panel_component: Optional[VisualizationPanelComponent] = None
        self.operations_panel_component: Optional[OperationsPanelComponent] = None
        
        # Tab widget for secondary views
        self.tab_widget: Optional[QTabWidget] = None
        
        # Current view model for display updates
        self._current_view_model: Optional[MainViewModel] = None
        
        # Setup the UI
        self.setup_ui()
        self.logger.info("MainViewController initialized")
    
    def setup_ui(self) -> None:
        """Initialize and setup the complete UI layout."""
        try:
            self._setup_window_properties()
            self._create_main_layout()
            self.logger.debug("UI setup completed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to setup UI: {e}")
            raise ViewControllerError(f"Failed to setup UI: {e}")
    
    def _setup_window_properties(self) -> None:
        """Setup main window properties."""
        self.setWindowTitle("上位机软件 - 管孔检测系统")
        
        # Get screen size and set appropriate window size
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        
        # Set window size to 80% of screen, but not exceeding 1400x900
        window_width = min(int(screen_geometry.width() * 0.8), 1400)
        window_height = min(int(screen_geometry.height() * 0.8), 900)
        
        # Center the window
        x = (screen_geometry.width() - window_width) // 2
        y = (screen_geometry.height() - window_height) // 2
        
        self.setGeometry(x, y, window_width, window_height)
        self.setMinimumSize(1200, 800)
    
    def _create_main_layout(self) -> None:
        """Create the main layout structure."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create main detection view tab
        main_detection_widget = self._create_main_detection_view()
        self.tab_widget.addTab(main_detection_widget, "主检测视图")
        
        # Set default tab
        self.tab_widget.setCurrentIndex(0)
    
    def _create_main_detection_view(self) -> QWidget:
        """Create the main detection view widget."""
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # Create and add toolbar
        toolbar = self.create_toolbar()
        main_layout.addWidget(toolbar)
        
        # Create three-panel layout
        content_splitter = QSplitter(Qt.Horizontal)
        
        # Left panel
        left_panel = self.create_left_info_panel()
        content_splitter.addWidget(left_panel)
        
        # Center panel  
        center_panel = self.create_center_visualization_panel()
        content_splitter.addWidget(center_panel)
        
        # Right panel
        right_panel = self.create_right_operations_panel()
        content_splitter.addWidget(right_panel)
        
        # Set splitter properties and ratios
        content_splitter.setSizes([400, 860, 280])
        content_splitter.setChildrenCollapsible(False)
        content_splitter.setStretchFactor(0, 0)  # Fixed left panel
        content_splitter.setStretchFactor(1, 1)  # Stretchable center
        content_splitter.setStretchFactor(2, 0)  # Fixed right panel
        
        # Disable left panel resizing
        content_splitter.handle(1).setEnabled(False)
        
        main_layout.addWidget(content_splitter)
        
        return main_widget
    
    def create_toolbar(self) -> QWidget:
        """
        Create and return the main toolbar widget.
        
        Returns:
            QWidget: The configured toolbar widget
        """
        try:
            self.toolbar_component = ToolbarComponent()
            
            # Connect toolbar signals to user action emission
            self.toolbar_component.product_selection_requested.connect(
                lambda: self._emit_user_action("product_selection", {})
            )
            self.toolbar_component.search_requested.connect(
                lambda query: self._emit_user_action("search", {"query": query})
            )
            self.toolbar_component.view_filter_changed.connect(
                lambda filter_type: self._emit_user_action("view_filter_changed", {"filter": filter_type})
            )
            self.toolbar_component.snake_path_toggled.connect(
                lambda enabled: self._emit_user_action("snake_path_toggled", {"enabled": enabled})
            )
            self.toolbar_component.snake_path_strategy_changed.connect(
                lambda strategy: self._emit_user_action("snake_path_strategy_changed", {"strategy": strategy})
            )
            self.toolbar_component.snake_path_debug_toggled.connect(
                lambda debug: self._emit_user_action("snake_path_debug_toggled", {"debug": debug})
            )
            
            self.logger.debug("Toolbar component created and connected")
            return self.toolbar_component
            
        except Exception as e:
            self.logger.error(f"Failed to create toolbar: {e}")
            raise ViewControllerError(f"Failed to create toolbar: {e}", "ToolbarComponent")
    
    def create_left_info_panel(self) -> QWidget:
        """
        Create and return the left information panel.
        
        Returns:
            QWidget: The configured left panel widget
        """
        try:
            self.info_panel_component = InfoPanelComponent()
            
            # Connect info panel signals (if any)
            # Info panel is mostly display-only, but could have interactive elements
            
            self.logger.debug("Info panel component created")
            return self.info_panel_component
            
        except Exception as e:
            self.logger.error(f"Failed to create left info panel: {e}")
            raise ViewControllerError(f"Failed to create left info panel: {e}", "InfoPanelComponent")
    
    def create_center_visualization_panel(self) -> QWidget:
        """
        Create and return the center visualization panel.
        
        Returns:
            QWidget: The configured center panel widget
        """
        try:
            self.visualization_panel_component = VisualizationPanelComponent()
            
            # Connect visualization panel signals
            self.visualization_panel_component.hole_selected.connect(
                lambda hole_id: self._emit_user_action("hole_selected", {"hole_id": hole_id})
            )
            self.visualization_panel_component.sector_changed.connect(
                lambda sector: self._emit_user_action("sector_changed", {"sector": sector})
            )
            self.visualization_panel_component.view_mode_changed.connect(
                lambda mode: self._emit_user_action("view_mode_changed", {"mode": mode})
            )
            
            self.logger.debug("Visualization panel component created and connected")
            return self.visualization_panel_component
            
        except Exception as e:
            self.logger.error(f"Failed to create center visualization panel: {e}")
            raise ViewControllerError(f"Failed to create center visualization panel: {e}", "VisualizationPanelComponent")
    
    def create_right_operations_panel(self) -> QWidget:
        """
        Create and return the right operations panel.
        
        Returns:
            QWidget: The configured right panel widget
        """
        try:
            self.operations_panel_component = OperationsPanelComponent()
            
            # Connect operations panel signals
            self.operations_panel_component.detection_start_requested.connect(
                lambda: self._emit_user_action("detection_start", {})
            )
            self.operations_panel_component.detection_pause_requested.connect(
                lambda: self._emit_user_action("detection_pause", {})
            )
            self.operations_panel_component.detection_stop_requested.connect(
                lambda: self._emit_user_action("detection_stop", {})
            )
            self.operations_panel_component.simulation_start_requested.connect(
                lambda params: self._emit_user_action("simulation_start", params)
            )
            self.operations_panel_component.simulation_stop_requested.connect(
                lambda: self._emit_user_action("simulation_stop", {})
            )
            self.operations_panel_component.file_load_requested.connect(
                lambda file_path: self._emit_user_action("file_load", {"file_path": file_path})
            )
            self.operations_panel_component.report_export_requested.connect(
                lambda params: self._emit_user_action("report_export", params)
            )
            
            self.logger.debug("Operations panel component created and connected")
            return self.operations_panel_component
            
        except Exception as e:
            self.logger.error(f"Failed to create right operations panel: {e}")
            raise ViewControllerError(f"Failed to create right operations panel: {e}", "OperationsPanelComponent")
    
    def update_display(self, view_model: MainViewModel) -> None:
        """
        Update the UI display based on view model changes.
        
        Args:
            view_model: The updated view model containing new state
        """
        try:
            if not isinstance(view_model, MainViewModel):
                raise ViewControllerError("Invalid view model type")
            
            self._current_view_model = view_model
            
            # Update all components with new view model
            if self.toolbar_component:
                self.toolbar_component.update_from_view_model(view_model)
            
            if self.info_panel_component:
                self.info_panel_component.update_from_view_model(view_model)
            
            if self.visualization_panel_component:
                self.visualization_panel_component.update_from_view_model(view_model)
            
            if self.operations_panel_component:
                self.operations_panel_component.update_from_view_model(view_model)
            
            # Update window title if file is loaded
            if view_model.current_file_path:
                file_name = view_model.current_file_path.split('/')[-1]
                self.setWindowTitle(f"上位机软件 - 管孔检测系统 - {file_name}")
            else:
                self.setWindowTitle("上位机软件 - 管孔检测系统")
            
            self.logger.debug("Display updated from view model")
            
        except Exception as e:
            self.logger.error(f"Failed to update display: {e}")
            raise ViewControllerError(f"Failed to update display: {e}")
    
    def show_message(self, message: str, level: str) -> None:
        """
        Display a message to the user.
        
        Args:
            message: The message text to display
            level: Message level ('info', 'warning', 'error', 'success')
        """
        try:
            # Update status bar
            if self.statusBar():
                self.statusBar().showMessage(message, 5000)  # Show for 5 seconds
            
            # Show message box for important messages
            if level in [MessageLevel.ERROR.value, MessageLevel.WARNING.value]:
                if level == MessageLevel.ERROR.value:
                    QMessageBox.critical(self, "错误", message)
                elif level == MessageLevel.WARNING.value:
                    QMessageBox.warning(self, "警告", message)
            
            self.logger.info(f"Message displayed: [{level}] {message}")
            
        except Exception as e:
            self.logger.error(f"Failed to show message: {e}")
            raise ViewControllerError(f"Failed to show message: {e}")
    
    def set_loading_state(self, loading: bool) -> None:
        """
        Set the loading state of the UI.
        
        Args:
            loading: True to show loading state, False to hide
        """
        try:
            # Enable/disable UI components based on loading state
            if self.toolbar_component:
                self.toolbar_component.setEnabled(not loading)
            
            if self.operations_panel_component:
                self.operations_panel_component.set_loading_state(loading)
            
            # Update cursor
            if loading:
                self.setCursor(Qt.WaitCursor)
            else:
                self.unsetCursor()
            
            self.logger.debug(f"Loading state set to: {loading}")
            
        except Exception as e:
            self.logger.error(f"Failed to set loading state: {e}")
            raise ViewControllerError(f"Failed to set loading state: {e}")
    
    def show(self) -> None:
        """Show the main window."""
        try:
            super().show()
            self.logger.info("Main window shown")
            
        except Exception as e:
            self.logger.error(f"Failed to show window: {e}")
            raise ViewControllerError(f"Failed to show window: {e}")
    
    def close(self) -> None:
        """Close the main window."""
        try:
            super().close()
            self.logger.info("Main window closed")
            
        except Exception as e:
            self.logger.error(f"Failed to close window: {e}")
            raise ViewControllerError(f"Failed to close window: {e}")
    
    def _emit_user_action(self, action_type: str, parameters: Dict[str, Any]) -> None:
        """
        Emit a user action signal.
        
        Args:
            action_type: Type of action performed
            parameters: Action parameters
        """
        try:
            action = UserAction(
                action_type=action_type,
                parameters=parameters,
                source_component=self.__class__.__name__
            )
            self.user_action.emit(action)
            self.logger.debug(f"User action emitted: {action_type}")
            
        except Exception as e:
            self.logger.error(f"Failed to emit user action: {e}")
            raise ViewControllerError(f"Failed to emit user action: {e}")
    
    def add_secondary_tab(self, widget: QWidget, title: str) -> None:
        """
        Add a secondary tab to the tab widget.
        
        Args:
            widget: Widget to add as tab
            title: Tab title
        """
        try:
            if self.tab_widget:
                self.tab_widget.addTab(widget, title)
                self.logger.debug(f"Secondary tab added: {title}")
            
        except Exception as e:
            self.logger.error(f"Failed to add secondary tab: {e}")
            raise ViewControllerError(f"Failed to add secondary tab: {e}")
    
    def switch_to_tab(self, index: int) -> None:
        """
        Switch to a specific tab.
        
        Args:
            index: Tab index to switch to
        """
        try:
            if self.tab_widget and 0 <= index < self.tab_widget.count():
                self.tab_widget.setCurrentIndex(index)
                self.logger.debug(f"Switched to tab index: {index}")
            
        except Exception as e:
            self.logger.error(f"Failed to switch tab: {e}")
            raise ViewControllerError(f"Failed to switch tab: {e}")
    
    def get_current_view_model(self) -> Optional[MainViewModel]:
        """
        Get the current view model.
        
        Returns:
            Current view model or None if not set
        """
        return self._current_view_model
    
    def closeEvent(self, event) -> None:
        """Handle window close event."""
        try:
            # Emit close action for business layer to handle
            self._emit_user_action("window_close", {})
            super().closeEvent(event)
            
        except Exception as e:
            self.logger.error(f"Error during close event: {e}")
            event.accept()  # Accept close anyway to prevent hang