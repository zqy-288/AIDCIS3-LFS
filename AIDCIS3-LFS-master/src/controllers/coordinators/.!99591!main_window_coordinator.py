"""
Main window coordinator implementation for system integration.

This module implements the main coordinator that manages component creation,
initialization, lifecycle, and signal connections between all system components.
"""

import logging
from typing import Optional, Dict, Any
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from ..main_business_controller import MainBusinessController
from ...ui.main_view_controller import MainViewController
from ...ui.view_models.main_view_model import MainViewModel
from ...ui.view_models.view_model_manager import MainViewModelManager
from ...exceptions.main_exceptions import CoordinatorError


class MainWindowCoordinator(QObject):
    """
    Main window coordinator for system integration.
    
    This coordinator manages the entire application architecture, creating
    and coordinating all components, managing their lifecycle, and setting
    up signal connections between UI, business logic, and data layers.
    """
    
    # Coordinator lifecycle signals
    initialization_completed = Signal()
    initialization_failed = Signal(str)
    shutdown_completed = Signal()
    
    # System state signals
    system_ready = Signal()
    system_error = Signal(str)
    
    def __init__(self, parent: Optional[QObject] = None):
        """
        Initialize the main window coordinator.
        
        Args:
            parent: Optional parent QObject
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # Component references
        self._main_view_controller: Optional[MainViewController] = None
        self._main_business_controller: Optional[MainBusinessController] = None
        self._view_model_manager: Optional[MainViewModelManager] = None
        self._view_model: Optional[MainViewModel] = None
        
        # State tracking
        self._initialized = False
        self._shutdown = False
        
        self.logger.debug("Main window coordinator created")
    
    def initialize(self) -> None:
        """
        Initialize all components and setup the system.
        
        This method creates all components, sets up their relationships,
        and connects signals between layers.
        """
        try:
            if self._initialized:
                self.logger.warning("Coordinator already initialized")
                return
            
            self.logger.info("Starting system initialization")
            
            # Step 1: Create core components
            self._create_core_components()
            
            # Step 2: Setup component relationships
            self._setup_component_relationships()
            
            # Step 3: Connect all signals
            self._connect_all_signals()
            
            # Step 4: Initialize components
            self._initialize_components()
            
            # Step 5: Final setup
            self._finalize_initialization()
            
            self._initialized = True
            self.logger.info("System initialization completed successfully")
            self.initialization_completed.emit()
            self.system_ready.emit()
            
        except Exception as e:
            error_msg = f"Failed to initialize coordinator: {e}"
            self.logger.error(error_msg, exc_info=True)
            self.initialization_failed.emit(error_msg)
            raise CoordinatorError(error_msg)
    
    def _create_core_components(self) -> None:
        """Create all core system components."""
        try:
            self.logger.debug("Creating core components")
            
            # Create view model and manager (data layer)
            self._view_model = MainViewModel()
            self._view_model_manager = MainViewModelManager(self._view_model)
            
            # Create business controller (business logic layer)
            self._main_business_controller = MainBusinessController()
            
            # Create main view controller (UI layer)
            self._main_view_controller = MainViewController()
            
            self.logger.debug("Core components created successfully")
            
        except Exception as e:
            raise CoordinatorError(f"Failed to create core components: {e}")
    
    def _setup_component_relationships(self) -> None:
        """Setup relationships between components."""
        try:
            self.logger.debug("Setting up component relationships")
            
            # Connect view model manager to view controller
            if self._main_view_controller and self._view_model_manager:
                self._main_view_controller.set_view_model_manager(self._view_model_manager)
            
            # Ensure view model is available to view controller
            if self._main_view_controller and self._view_model:
                self._main_view_controller.set_view_model(self._view_model)
            
            self.logger.debug("Component relationships established")
            
        except Exception as e:
            raise CoordinatorError(f"Failed to setup component relationships: {e}")
    
    def _connect_all_signals(self) -> None:
        """Connect signals between all system components."""
        try:
            self.logger.debug("Connecting system signals")
            
            # Connect business controller signals to view model updates
            self._connect_business_to_viewmodel_signals()
            
            # Connect UI controller signals to business operations
            self._connect_ui_to_business_signals()
            
            # Connect view model manager signals to UI updates
            self._connect_viewmodel_to_ui_signals()
            
            # Connect internal coordinator signals
            self._connect_coordinator_signals()
            
            self.logger.debug("All signals connected successfully")
            
        except Exception as e:
            raise CoordinatorError(f"Failed to connect signals: {e}")
    
    def _connect_business_to_viewmodel_signals(self) -> None:
        """Connect business controller signals to view model updates."""
        if not self._main_business_controller or not self._view_model_manager:
            return
        
        try:
            # Operation completion/failure signals
            self._main_business_controller.operation_completed.connect(
                self._on_business_operation_completed
            )
            self._main_business_controller.operation_failed.connect(
                self._on_business_operation_failed
            )
            
            # State change signals
            self._main_business_controller.state_changed.connect(
                self._on_business_state_changed
            )
            
            # Data update signals
            self._main_business_controller.data_updated.connect(
                self._on_business_data_updated
            )
            
            # Statistics signals
            self._main_business_controller.statistics_updated.connect(
                self._on_statistics_updated
            )
            
            # Progress signals
            self._main_business_controller.progress_updated.connect(
                self._on_progress_updated
            )
            
            self.logger.debug("Business to view model signals connected")
            
        except Exception as e:
            self.logger.error(f"Failed to connect business to view model signals: {e}")
    
    def _connect_ui_to_business_signals(self) -> None:
        """Connect UI controller signals to business operations."""
        if not self._main_view_controller or not self._main_business_controller:
            return
        
        try:
            # User action signals from UI to business operations
            self._main_view_controller.user_action.connect(
                self._on_user_action
            )
            
            # Specific operation signals from UI components
            # File operations
            if hasattr(self._main_view_controller, 'operations_panel') and self._main_view_controller.operations_panel:
                ops_panel = self._main_view_controller.operations_panel
                
                ops_panel.file_load_requested.connect(
                    self._main_business_controller.load_dxf_file
                )
                ops_panel.product_load_requested.connect(
                    lambda: self._handle_product_selection()
                )
                
                # Detection operations
                ops_panel.detection_start_requested.connect(
                    self._main_business_controller.start_detection
                )
                ops_panel.detection_pause_requested.connect(
                    self._main_business_controller.pause_detection
                )
                ops_panel.detection_stop_requested.connect(
                    self._main_business_controller.stop_detection
                )
                
                # Simulation operations
                ops_panel.simulation_start_requested.connect(
                    self._main_business_controller.start_simulation
                )
                ops_panel.simulation_stop_requested.connect(
                    self._main_business_controller.stop_simulation
                )
                
                # Report export (handled separately)
                ops_panel.report_export_requested.connect(
                    self._handle_report_export
                )
            
            # Search operations from toolbar
            if hasattr(self._main_view_controller, 'toolbar_component') and self._main_view_controller.toolbar_component:
                toolbar = self._main_view_controller.toolbar_component
                
                toolbar.search_requested.connect(
                    self._main_business_controller.search_holes
                )
                toolbar.view_filter_changed.connect(
                    self._main_business_controller.filter_holes_by_status
                )
            
            self.logger.debug("UI to business signals connected")
            
        except Exception as e:
            self.logger.error(f"Failed to connect UI to business signals: {e}")
    
    def _connect_viewmodel_to_ui_signals(self) -> None:
        """Connect view model manager signals to UI updates."""
        if not self._view_model_manager or not self._main_view_controller:
            return
        
        try:
            # View model change signals
            self._view_model_manager.view_model_changed.connect(
                self._main_view_controller.update_from_view_model
            )
            
            # Message signals
            self._view_model_manager.message_changed.connect(
                self._on_view_model_message
            )
            
            self.logger.debug("View model to UI signals connected")
            
        except Exception as e:
            self.logger.error(f"Failed to connect view model to UI signals: {e}")
    
    def _connect_coordinator_signals(self) -> None:
        """Connect internal coordinator signals."""
        try:
            # Connect system error handling
            self.system_error.connect(self._on_system_error)
            
            self.logger.debug("Coordinator signals connected")
            
        except Exception as e:
            self.logger.error(f"Failed to connect coordinator signals: {e}")
    
    def _initialize_components(self) -> None:
        """Initialize all components."""
        try:
            self.logger.debug("Initializing components")
            
            # Initialize business controller services
            if self._main_business_controller:
                # Business controller initializes itself
                pass
            
            # Initialize view model manager
            if self._view_model_manager:
                # View model manager initializes itself
                pass
            
            # Initialize UI controller
            if self._main_view_controller:
                # UI controller shows itself
                self._main_view_controller.show()
            
            self.logger.debug("Components initialized")
            
        except Exception as e:
            raise CoordinatorError(f"Failed to initialize components: {e}")
    
    def _finalize_initialization(self) -> None:
        """Perform final initialization steps."""
        try:
            self.logger.debug("Finalizing initialization")
            
            # Load default product if available
            if self._main_business_controller:
                products = self._main_business_controller.get_available_products()
                if products:
                    # Load first available product as default
                    self._main_business_controller.load_product(products[0])
            
            # Update initial UI state
            if self._view_model_manager and self._view_model:
                self._view_model_manager.emit_view_model_changed()
            
            self.logger.debug("Initialization finalized")
            
        except Exception as e:
            self.logger.warning(f"Failed to finalize initialization: {e}")
    
    # Signal handlers
    def _on_user_action(self, action: Any) -> None:
        """Handle user action from UI."""
        try:
            if not hasattr(action, 'action_type'):
                return
            
            action_type = getattr(action, 'action_type', '')
            
            # Route actions to appropriate business operations
            if action_type == 'load_file':
                file_path = getattr(action, 'file_path', '')
                if file_path and self._main_business_controller:
                    self._main_business_controller.load_dxf_file(file_path)
            
            elif action_type == 'search':
                query = getattr(action, 'query', '')
                if self._main_business_controller:
                    self._main_business_controller.search_holes(query)
            
            elif action_type == 'filter':
                filter_type = getattr(action, 'filter_type', 'all')
                if self._main_business_controller:
                    self._main_business_controller.filter_holes_by_status(filter_type)
            
            # Add more action handlers as needed
            
        except Exception as e:
            self.logger.error(f"Failed to handle user action: {e}")
    
    def _on_business_operation_completed(self, operation_name: str, result: Dict[str, Any]) -> None:
        """Handle business operation completion."""
        try:
            if not self._view_model_manager or not self._view_model:
                return
            
            # Update view model based on operation type
            if operation_name == 'load_file':
                file_path = result.get('file_path', '')
                if file_path:
                    self._view_model.current_file_path = file_path
