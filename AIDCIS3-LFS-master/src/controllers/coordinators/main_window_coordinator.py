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
                    self._view_model.current_message = f"}: {file_path}"
                    self._view_model.message_type = "success"
                
                # Update hole collection if available
                file_info = result.get('file_info', {})
                if 'hole_collection' in file_info:
                    self._view_model.hole_collection = file_info['hole_collection']
            
            elif operation_name == 'load_product':
                product_name = result.get('product_name', '')
                if product_name:
                    self._view_model.current_product = product_name
                    self._view_model.current_message = f"}: {product_name}"
                    self._view_model.message_type = "success"
            
            elif operation_name == 'search':
                query = result.get('query', '')
                results = result.get('results', [])
                self._view_model.search_query = query
                self._view_model.search_results = results
                self._view_model.current_message = f"": ~0 {len(results)} *Ӝ"
                self._view_model.message_type = "info"
            
            elif operation_name == 'detection':
                self._view_model.detection_running = False
                self._view_model.detection_progress = 100.0
                self._view_model.current_message = "K"
                self._view_model.message_type = "success"
            
            # Emit view model update
            self._view_model_manager.emit_view_model_changed()
            
        except Exception as e:
            self.logger.error(f"Failed to handle operation completion: {e}")
    
    def _on_business_operation_failed(self, operation_name: str, error_message: str) -> None:
        """Handle business operation failure."""
        try:
            if not self._view_model_manager or not self._view_model:
                return
            
            # Update view model with error information
            self._view_model.current_message = f"\1% ({operation_name}): {error_message}"
            self._view_model.message_type = "error"
            
            # Reset relevant state based on operation
            if operation_name in ['start_detection', 'pause_detection']:
                self._view_model.detection_running = False
            
            # Emit view model update
            self._view_model_manager.emit_view_model_changed()
            
        except Exception as e:
            self.logger.error(f"Failed to handle operation failure: {e}")
    
    def _on_business_state_changed(self, state_type: str, new_state: Any) -> None:
        """Handle business state changes."""
        try:
            if not self._view_model_manager or not self._view_model:
                return
            
            # Update view model state
            if state_type == 'detection':
                from ...ui.view_models.enums import DetectionState
                if new_state == DetectionState.RUNNING:
                    self._view_model.detection_running = True
                elif new_state in [DetectionState.IDLE, DetectionState.STOPPED]:
                    self._view_model.detection_running = False
            
            elif state_type == 'simulation':
                from ...ui.view_models.enums import SimulationState
                if new_state == SimulationState.RUNNING:
                    self._view_model.simulation_running = True
                else:
                    self._view_model.simulation_running = False
            
            # Emit view model update
            self._view_model_manager.emit_view_model_changed()
            
        except Exception as e:
            self.logger.error(f"Failed to handle state change: {e}")
    
    def _on_business_data_updated(self, data_type: str, data: Any) -> None:
        """Handle business data updates."""
        try:
            if not self._view_model_manager or not self._view_model:
                return
            
            # Update view model data
            if data_type == 'hole_collection':
                self._view_model.hole_collection = data
            
            elif data_type == 'hole_status':
                # Individual hole status update
                hole_data = data if isinstance(data, dict) else {}
                hole_id = hole_data.get('hole_id', '')
                if hole_id:
                    self._view_model.current_message = f"TM: {hole_id}"
                    self._view_model.message_type = "info"
            
            elif data_type == 'filtered_holes':
                filter_data = data if isinstance(data, dict) else {}
                results = filter_data.get('results', [])
                filter_type = filter_data.get('filter_type', 'all')
                self._view_model.search_results = results
                self._view_model.current_filter = filter_type
            
            # Emit view model update
            self._view_model_manager.emit_view_model_changed()
            
        except Exception as e:
            self.logger.error(f"Failed to handle data update: {e}")
    
    def _on_statistics_updated(self, statistics: Dict[str, Any]) -> None:
        """Handle statistics updates."""
        try:
            if not self._view_model_manager or not self._view_model:
                return
            
            # Update view model statistics
            completion_stats = statistics.get('completion', {})
            if completion_stats:
                self._view_model.completion_rate = completion_stats.get('completion_rate', 0.0)
                self._view_model.total_holes = completion_stats.get('total_holes', 0)
                self._view_model.completed_holes = completion_stats.get('completed_holes', 0)
                self._view_model.qualified_holes = completion_stats.get('qualified_holes', 0)
                self._view_model.defective_holes = completion_stats.get('defective_holes', 0)
            
            # Emit view model update
            self._view_model_manager.emit_view_model_changed()
            
        except Exception as e:
            self.logger.error(f"Failed to handle statistics update: {e}")
    
    def _on_progress_updated(self, operation_type: str, progress_data: Dict[str, Any]) -> None:
        """Handle progress updates."""
        try:
            if not self._view_model_manager or not self._view_model:
                return
            
            # Update view model progress
            if operation_type == 'detection':
                current = progress_data.get('current', 0)
                total = progress_data.get('total', 1)
                progress_percent = (current / total * 100.0) if total > 0 else 0.0
                
                self._view_model.detection_progress = progress_percent
                self._view_model.current_hole_index = current
                
                # Update current message
                self._view_model.current_message = f"检测进度: {current}/{total} ({progress_percent:.1f}%)"
                self._view_model.message_type = "info"
            
            # Emit view model update
            self._view_model_manager.emit_view_model_changed()
            
        except Exception as e:
            self.logger.error(f"Failed to handle progress update: {e}")
    
    def _on_view_model_message(self, message: str, message_type: str) -> None:
        """Handle view model messages."""
        try:
            # Log messages based on type
            if message_type == "error":
                self.logger.error(f"View model error: {message}")
            elif message_type == "warning":
                self.logger.warning(f"View model warning: {message}")
            else:
                self.logger.info(f"View model message: {message}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle view model message: {e}")
    
    def _on_system_error(self, error_message: str) -> None:
        """Handle system-level errors."""
        try:
            self.logger.error(f"System error: {error_message}")
            
            # Update view model with system error
            if self._view_model_manager and self._view_model:
                self._view_model.current_message = f": {error_message}"
                self._view_model.message_type = "error"
                self._view_model_manager.emit_view_model_changed()
            
        except Exception as e:
            self.logger.error(f"Failed to handle system error: {e}")
    
    # Helper methods
    def _handle_product_selection(self) -> None:
        """Handle product selection dialog."""
        try:
            if not self._main_business_controller:
                return
            
            products = self._main_business_controller.get_available_products()
            if not products:
                self.logger.warning("No products available")
                return
            
            # For now, load the first product
            # In a real implementation, this would show a selection dialog
            if products:
                self._main_business_controller.load_product(products[0])
            
        except Exception as e:
            self.logger.error(f"Failed to handle product selection: {e}")
    
    def _handle_report_export(self, parameters: Dict[str, Any]) -> None:
        """Handle report export request."""
        try:
            # Report export would be handled by a separate service
            # For now, just log the request
            export_format = parameters.get('format', 'PDF报告')
            self.logger.info(f"Report export requested: {export_format}")
            
            if self._view_model_manager and self._view_model:
                self._view_model.current_message = f"报告导出功能暂未实现 ({export_format})"
                self._view_model.message_type = "warning"
                self._view_model_manager.emit_view_model_changed()
            
        except Exception as e:
            self.logger.error(f"Failed to handle report export: {e}")
    
    # Public interface
    def get_main_view_controller(self) -> Optional[MainViewController]:
        """Get the main view controller."""
        return self._main_view_controller
    
    def get_business_controller(self) -> Optional[MainBusinessController]:
        """Get the main business controller."""
        return self._main_business_controller
    
    def get_view_model(self) -> Optional[MainViewModel]:
        """Get the view model."""
        return self._view_model
    
    def is_initialized(self) -> bool:
        """Check if the coordinator is initialized."""
        return self._initialized
    
    def shutdown(self) -> None:
        """Shutdown the coordinator and clean up resources."""
        try:
            if self._shutdown:
                return
            
            self.logger.info("Starting system shutdown")
            
            # Cleanup business controller
            if self._main_business_controller:
                self._main_business_controller.cleanup()
            
            # Cleanup view controller
            if self._main_view_controller:
                self._main_view_controller.close()
            
            # Cleanup view model manager
            if self._view_model_manager:
                # View model manager cleanup if needed
                pass
            
            # Clear references
            self._main_view_controller = None
            self._main_business_controller = None
            self._view_model_manager = None
            self._view_model = None
            
            self._shutdown = True
            self.logger.info("System shutdown completed")
            self.shutdown_completed.emit()
            
        except Exception as e:
            self.logger.error(f"Failed to shutdown coordinator: {e}")