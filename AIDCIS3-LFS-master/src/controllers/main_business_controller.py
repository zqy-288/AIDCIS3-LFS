"""
Main business controller implementation for MVVM architecture.

This module implements the core business controller that coordinates all
services and manages business logic layer functionality.
"""

import logging
from typing import Dict, Any, Optional, List
from PySide6.QtCore import QObject, Signal

from .services.detection_service import DetectionService
from .services.file_service import FileService
from .services.search_service import SearchService
from .services.status_service import StatusService
from ..exceptions.main_exceptions import BusinessControllerError
from ..ui.view_models.enums import DetectionState, SimulationState


class MainBusinessController(QObject):
    """
    Main business controller for coordinating all services.
    
    This controller acts as the central coordinator for all business logic,
    managing service interactions and providing a unified interface for
    the UI layer.
    """
    
    # Business operation signals
    operation_completed = Signal(str, dict)  # operation_name, result
    operation_failed = Signal(str, str)  # operation_name, error_message
    state_changed = Signal(str, object)  # state_type, new_state
    
    # Data update signals
    data_updated = Signal(str, object)  # data_type, data
    statistics_updated = Signal(dict)  # statistics_data
    progress_updated = Signal(str, dict)  # operation_type, progress_data
    
    def __init__(self):
        """Initialize the main business controller."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Initialize services
        self._detection_service: Optional[DetectionService] = None
        self._file_service: Optional[FileService] = None
        self._search_service: Optional[SearchService] = None
        self._status_service: Optional[StatusService] = None
        
        # Current state
        self._current_hole_collection: Optional[Any] = None
        self._current_product: Optional[str] = None
        
        # Initialize and connect services
        self._initialize_services()
        self._connect_service_signals()
        
        self.logger.debug("Main business controller initialized")
    
    def _initialize_services(self) -> None:
        """Initialize all business services."""
        try:
            # Initialize core services
            self._file_service = FileService()
            self._search_service = SearchService()
            self._status_service = StatusService()
            
            # Initialize detection service with dependencies if available
            try:
                from src.core_business.dxf_parser import DXFParser
                from src.core_business.models.status_manager import StatusManager
                
                dxf_parser = DXFParser()
                status_manager = StatusManager()
                self._detection_service = DetectionService(dxf_parser, status_manager)
                
            except ImportError as e:
                self.logger.warning(f"Detection service dependencies not available: {e}")
                # Create minimal detection service without dependencies
                self._detection_service = None
            
            self.logger.debug("Business services initialized")
            
        except Exception as e:
            error_msg = f"Failed to initialize services: {e}"
            self.logger.error(error_msg)
            raise BusinessControllerError(error_msg)
    
    def _connect_service_signals(self) -> None:
        """Connect signals from all services."""
        try:
            # File service signals
            if self._file_service:
                self._file_service.file_loaded.connect(self._on_file_loaded)
                self._file_service.file_load_failed.connect(self._on_file_load_failed)
                self._file_service.product_loaded.connect(self._on_product_loaded)
                self._file_service.product_load_failed.connect(self._on_product_load_failed)
            
            # Search service signals
            if self._search_service:
                self._search_service.search_completed.connect(self._on_search_completed)
                self._search_service.search_failed.connect(self._on_search_failed)
                self._search_service.filter_changed.connect(self._on_filter_changed)
            
            # Status service signals
            if self._status_service:
                self._status_service.status_updated.connect(self._on_status_updated)
                self._status_service.statistics_updated.connect(self._on_statistics_updated)
            
            # Detection service signals
            if self._detection_service:
                self._detection_service.detection_state_changed.connect(self._on_detection_state_changed)
                self._detection_service.detection_progress_updated.connect(self._on_detection_progress)
                self._detection_service.detection_completed.connect(self._on_detection_completed)
                self._detection_service.hole_status_updated.connect(self._on_hole_status_updated)
                self._detection_service.simulation_state_changed.connect(self._on_simulation_state_changed)
                self._detection_service.simulation_progress_updated.connect(self._on_simulation_progress)
            
            self.logger.debug("Service signals connected")
            
        except Exception as e:
            self.logger.error(f"Failed to connect service signals: {e}")
    
    # File operations
    def load_dxf_file(self, file_path: str) -> None:
        """
        Load a DXF file.
        
        Args:
            file_path: Path to the DXF file
        """
        try:
            if not self._file_service:
                raise BusinessControllerError("File service not available")
            
            self._file_service.load_dxf_file(file_path)
            self.logger.info(f"Requested DXF file load: {file_path}")
            
        except Exception as e:
            error_msg = f"Failed to load DXF file: {e}"
            self.logger.error(error_msg)
            self.operation_failed.emit("load_dxf", error_msg)
    
    def load_product(self, product_name: str) -> None:
        """
        Load a product configuration.
        
        Args:
            product_name: Name of the product to load
        """
        try:
            if not self._file_service:
                raise BusinessControllerError("File service not available")
            
            self._file_service.load_product(product_name)
            self.logger.info(f"Requested product load: {product_name}")
            
        except Exception as e:
            error_msg = f"Failed to load product: {e}"
            self.logger.error(error_msg)
            self.operation_failed.emit("load_product", error_msg)
    
    def get_available_products(self) -> List[str]:
        """
        Get list of available products.
        
        Returns:
            List of available product names
        """
        try:
            if not self._file_service:
                return []
            
            return self._file_service.get_available_products()
            
        except Exception as e:
            self.logger.error(f"Failed to get available products: {e}")
            return []
    
    # Search operations
    def search_holes(self, query: str) -> List[str]:
        """
        Search for holes matching the query.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching hole IDs
        """
        try:
            if not self._search_service:
                return []
            
            return self._search_service.search(query)
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            self.operation_failed.emit("search", str(e))
            return []
    
    def filter_holes_by_status(self, filter_type: str) -> List[str]:
        """
        Filter holes by status.
        
        Args:
            filter_type: Type of filter to apply
            
        Returns:
            List of filtered hole IDs
        """
        try:
            if not self._search_service:
                return []
            
            return self._search_service.filter_by_status(filter_type)
            
        except Exception as e:
            self.logger.error(f"Filter failed: {e}")
            self.operation_failed.emit("filter", str(e))
            return []
    
    # Status operations
    def update_hole_status(self, hole_id: str, new_status: str) -> None:
        """
        Update the status of a specific hole.
        
        Args:
            hole_id: ID of the hole to update
            new_status: New status value
        """
        try:
            if not self._status_service:
                raise BusinessControllerError("Status service not available")
            
            self._status_service.update_hole_status(hole_id, new_status)
            
        except Exception as e:
            error_msg = f"Failed to update hole status: {e}"
            self.logger.error(error_msg)
            self.operation_failed.emit("update_status", error_msg)
    
    def get_status_summary(self) -> Dict[str, int]:
        """
        Get summary of status counts.
        
        Returns:
            Dictionary with status counts
        """
        try:
            if not self._status_service:
                return {}
            
            return self._status_service.get_status_summary()
            
        except Exception as e:
            self.logger.error(f"Failed to get status summary: {e}")
            return {}
    
    def get_completion_statistics(self) -> Dict[str, Any]:
        """
        Get completion and quality statistics.
        
        Returns:
            Dictionary with completion statistics
        """
        try:
            if not self._status_service:
                return {}
            
            return self._status_service.get_completion_statistics()
            
        except Exception as e:
            self.logger.error(f"Failed to get completion statistics: {e}")
            return {}
    
    # Detection operations
    def start_detection(self) -> None:
        """Start the detection process."""
        try:
            if not self._detection_service:
                raise BusinessControllerError("Detection service not available")
            
            if not self._current_hole_collection:
                raise BusinessControllerError("No hole collection loaded")
            
            result = self._detection_service.start_detection(self._current_hole_collection)
            if not result.get("success", False):
                error_msg = result.get("error", "Unknown error")
                self.operation_failed.emit("start_detection", error_msg)
            
        except Exception as e:
            error_msg = f"Failed to start detection: {e}"
            self.logger.error(error_msg)
            self.operation_failed.emit("start_detection", error_msg)
    
    def pause_detection(self) -> None:
        """Pause or resume the detection process."""
        try:
            if not self._detection_service:
                raise BusinessControllerError("Detection service not available")
            
            result = self._detection_service.pause_detection()
            if not result.get("success", False):
                error_msg = result.get("error", "Unknown error")
                self.operation_failed.emit("pause_detection", error_msg)
            
        except Exception as e:
            error_msg = f"Failed to pause detection: {e}"
            self.logger.error(error_msg)
            self.operation_failed.emit("pause_detection", error_msg)
    
    def stop_detection(self) -> None:
        """Stop the detection process."""
        try:
            if not self._detection_service:
                raise BusinessControllerError("Detection service not available")
            
            result = self._detection_service.stop_detection()
            if not result.get("success", False):
                error_msg = result.get("error", "Unknown error")
                self.operation_failed.emit("stop_detection", error_msg)
            
        except Exception as e:
            error_msg = f"Failed to stop detection: {e}"
            self.logger.error(error_msg)
            self.operation_failed.emit("stop_detection", error_msg)
    
    # Simulation operations
    def start_simulation(self, parameters: Dict[str, Any]) -> None:
        """
        Start simulation with given parameters.
        
        Args:
            parameters: Simulation parameters
        """
        try:
            if not self._detection_service:
                raise BusinessControllerError("Detection service not available")
            
            if not self._current_hole_collection:
                raise BusinessControllerError("No hole collection loaded")
            
            result = self._detection_service.start_simulation(self._current_hole_collection)
            if not result.get("success", False):
                error_msg = result.get("error", "Unknown error")
                self.operation_failed.emit("start_simulation", error_msg)
            
        except Exception as e:
            error_msg = f"Failed to start simulation: {e}"
            self.logger.error(error_msg)
            self.operation_failed.emit("start_simulation", error_msg)
    
    def stop_simulation(self) -> None:
        """Stop the simulation process."""
        try:
            if not self._detection_service:
                raise BusinessControllerError("Detection service not available")
            
            result = self._detection_service.stop_simulation()
            if not result.get("success", False):
                error_msg = result.get("error", "Unknown error")
                self.operation_failed.emit("stop_simulation", error_msg)
            
        except Exception as e:
            error_msg = f"Failed to stop simulation: {e}"
            self.logger.error(error_msg)
            self.operation_failed.emit("stop_simulation", error_msg)
    
    # State management
    def set_hole_collection(self, hole_collection: Any) -> None:
        """
        Set the current hole collection for all services.
        
        Args:
            hole_collection: The hole collection to set
        """
        try:
            self._current_hole_collection = hole_collection
            
            # Update services with new collection
            if self._search_service:
                self._search_service.set_hole_collection(hole_collection)
            
            if self._status_service:
                self._status_service.set_hole_collection(hole_collection)
            
            self.data_updated.emit("hole_collection", hole_collection)
            self.logger.debug("Hole collection updated in all services")
            
        except Exception as e:
            self.logger.error(f"Failed to set hole collection: {e}")
    
    def get_current_state(self) -> Dict[str, Any]:
        """
        Get current business controller state.
        
        Returns:
            Dictionary with current state information
        """
        try:
            state = {
                "has_hole_collection": self._current_hole_collection is not None,
                "current_product": self._current_product,
                "services_available": {
                    "file_service": self._file_service is not None,
                    "search_service": self._search_service is not None,
                    "status_service": self._status_service is not None,
                    "detection_service": self._detection_service is not None
                }
            }
            
            # Add service-specific state
            if self._detection_service:
                state["detection_running"] = self._detection_service.is_detection_running()
                state["simulation_running"] = self._detection_service.is_simulation_running()
            
            if self._file_service:
                state["current_file"] = self._file_service.current_file_path
            
            return state
            
        except Exception as e:
            self.logger.error(f"Failed to get current state: {e}")
            return {}
    
    # Signal handlers
    def _on_file_loaded(self, file_path: str, file_info: Dict[str, Any]) -> None:
        """Handle file loaded signal."""
        try:
            # Extract hole collection if available
            if 'hole_collection' in file_info:
                self.set_hole_collection(file_info['hole_collection'])
            
            self.operation_completed.emit("load_file", {"file_path": file_path, "file_info": file_info})
            
        except Exception as e:
            self.logger.error(f"Error handling file loaded: {e}")
    
    def _on_file_load_failed(self, error_message: str) -> None:
        """Handle file load failed signal."""
        self.operation_failed.emit("load_file", error_message)
    
    def _on_product_loaded(self, product_name: str, product_info: Dict[str, Any]) -> None:
        """Handle product loaded signal."""
        try:
            self._current_product = product_name
            self.operation_completed.emit("load_product", {"product_name": product_name, "product_info": product_info})
            
        except Exception as e:
            self.logger.error(f"Error handling product loaded: {e}")
    
    def _on_product_load_failed(self, error_message: str) -> None:
        """Handle product load failed signal."""
        self.operation_failed.emit("load_product", error_message)
    
    def _on_search_completed(self, query: str, results: List[str]) -> None:
        """Handle search completed signal."""
        self.operation_completed.emit("search", {"query": query, "results": results})
    
    def _on_search_failed(self, error_message: str) -> None:
        """Handle search failed signal."""
        self.operation_failed.emit("search", error_message)
    
    def _on_filter_changed(self, filter_type: str, results: List[str]) -> None:
        """Handle filter changed signal."""
        self.data_updated.emit("filtered_holes", {"filter_type": filter_type, "results": results})
    
    def _on_status_updated(self, hole_id: str, new_status: str) -> None:
        """Handle status updated signal."""
        self.data_updated.emit("hole_status", {"hole_id": hole_id, "status": new_status})
    
    def _on_statistics_updated(self, statistics: Dict[str, Any]) -> None:
        """Handle statistics updated signal."""
        self.statistics_updated.emit(statistics)
    
    def _on_detection_state_changed(self, state: DetectionState) -> None:
        """Handle detection state changed signal."""
        self.state_changed.emit("detection", state)
    
    def _on_detection_progress(self, progress_info: Dict[str, Any]) -> None:
        """Handle detection progress signal."""
        self.progress_updated.emit("detection", progress_info)
    
    def _on_detection_completed(self, result_info: Dict[str, Any]) -> None:
        """Handle detection completed signal."""
        self.operation_completed.emit("detection", result_info)
    
    def _on_hole_status_updated(self, hole_id: str, status: Any) -> None:
        """Handle hole status updated signal."""
        self.data_updated.emit("hole_status", {"hole_id": hole_id, "status": status})
    
    def _on_simulation_state_changed(self, state: SimulationState) -> None:
        """Handle simulation state changed signal."""
        self.state_changed.emit("simulation", state)
    
    def _on_simulation_progress(self, progress_info: Dict[str, Any]) -> None:
        """Handle simulation progress signal."""
        self.progress_updated.emit("simulation", progress_info)
    
    # Cleanup
    def cleanup(self) -> None:
        """Clean up resources when shutting down."""
        try:
            # Cleanup all services
            if self._detection_service:
                self._detection_service.cleanup()
            
            if self._file_service:
                self._file_service.cleanup()
            
            if self._search_service:
                self._search_service.cleanup()
            
            if self._status_service:
                self._status_service.cleanup()
            
            # Clear references
            self._current_hole_collection = None
            self._current_product = None
            
            self.logger.debug("Main business controller cleaned up")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup business controller: {e}")