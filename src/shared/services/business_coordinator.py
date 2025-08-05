"""
Business Coordinator for MVVM architecture.

This module implements the business coordinator that manages service interactions
and provides Qt signal-based communication for UI components.
"""

import logging
from typing import Dict, Any, Optional, List
from PySide6.QtCore import QObject, Signal

from .business_service import get_business_service
from .detection_service import DetectionService
from .search_service import SearchService
from .status_service import StatusService
from ...core.exceptions.main_exceptions import BusinessControllerError
from ..view_models.enums import DetectionState, SimulationState


class BusinessCoordinator(QObject):
    """
    Business coordinator for Qt signal-based service coordination.
    
    This coordinator acts as a Qt signal bridge between the business services
    and UI components, without duplicating business logic.
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
        """Initialize the business coordinator."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Use the unified business service (no duplication)
        self.business_service = get_business_service()
        
        # Initialize Qt-based services that need signal support
        self._detection_service: Optional[DetectionService] = None
        self._search_service: Optional[SearchService] = None
        self._status_service: Optional[StatusService] = None
        
        # Initialize Qt services and connect signals
        self._initialize_qt_services()
        self._connect_service_signals()
        
        self.logger.debug("Business coordinator initialized")
    
    def _initialize_qt_services(self) -> None:
        """Initialize Qt-based services that need signal support."""
        try:
            # Initialize services that require Qt signals
            self._search_service = SearchService()
            self._status_service = StatusService()
            
            # Initialize detection service with dependencies
            try:
                from src.shared.services.status_manager import StatusManager
                status_manager = StatusManager()
                self._detection_service = DetectionService()
                
            except ImportError as e:
                self.logger.warning(f"Detection service dependencies not available: {e}")
                self._detection_service = None
            
            self.logger.debug("Qt services initialized")
            
        except Exception as e:
            error_msg = f"Failed to initialize Qt services: {e}"
            self.logger.error(error_msg)
            raise BusinessControllerError(error_msg)
    
    def _connect_service_signals(self) -> None:
        """Connect signals from Qt-based services."""
        try:
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
    
    # Coordinate business operations (delegate to business_service)
    def load_dxf_file(self, file_path: str) -> None:
        """
        Load a DXF file (coordinate with business service).
        
        Args:
            file_path: Path to the DXF file
        """
        try:
            # Delegate to business service
            hole_collection = self.business_service.parse_dxf_file(file_path)
            
            if hole_collection:
                # Apply hole numbering
                hole_collection = self.business_service.apply_hole_numbering(hole_collection)
                # Set to shared data manager
                self.business_service.set_hole_collection(hole_collection)
                
                # Emit success signal
                result = {
                    'file_path': file_path,
                    'hole_collection': hole_collection,
                    'hole_count': len(hole_collection.holes) if hole_collection else 0
                }
                self.operation_completed.emit("load_file", result)
                self.data_updated.emit("hole_collection", hole_collection)
                
                self.logger.info(f"Successfully coordinated DXF file load: {file_path}")
            else:
                error_msg = f"Failed to parse DXF file: {file_path}"
                self.operation_failed.emit("load_file", error_msg)
            
        except Exception as e:
            error_msg = f"Failed to coordinate DXF file load: {e}"
            self.logger.error(error_msg)
            self.operation_failed.emit("load_file", error_msg)
    
    def load_product(self, product_name: str) -> None:
        """
        Load a product configuration (coordinate with business service).
        
        Args:
            product_name: Name of the product to load
        """
        try:
            # Delegate to business service
            if self.business_service.select_product(product_name):
                result = {
                    'product_name': product_name,
                    'product_object': self.business_service.current_product
                }
                self.operation_completed.emit("load_product", result)
                self.logger.info(f"Successfully coordinated product load: {product_name}")
            else:
                error_msg = f"Failed to select product: {product_name}"
                self.operation_failed.emit("load_product", error_msg)
            
        except Exception as e:
            error_msg = f"Failed to coordinate product load: {e}"
            self.logger.error(error_msg)
            self.operation_failed.emit("load_product", error_msg)
    
    def get_available_products(self) -> List[str]:
        """
        Get list of available products (delegate to business service).
        
        Returns:
            List of available product names
        """
        try:
            return self.business_service.get_product_list()
        except Exception as e:
            self.logger.error(f"Failed to get available products: {e}")
            return []
    
    # Search operations (coordinate with Qt search service)
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
    
    # Status operations (coordinate with both services)
    def update_hole_status(self, hole_id: str, new_status: str) -> None:
        """
        Update the status of a specific hole.
        
        Args:
            hole_id: ID of the hole to update
            new_status: New status value
        """
        try:
            # Update via business service
            if self.business_service.update_hole_status(hole_id, new_status):
                # Also notify Qt status service
                if self._status_service:
                    self._status_service.update_hole_status(hole_id, new_status)
                
                # Emit data update signal
                self.data_updated.emit("hole_status", {"hole_id": hole_id, "status": new_status})
            else:
                error_msg = f"Failed to update hole status: {hole_id}"
                self.operation_failed.emit("update_status", error_msg)
            
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
            if self._status_service:
                return self._status_service.get_status_summary()
            return {}
            
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
            if self._status_service:
                return self._status_service.get_completion_statistics()
            return {}
            
        except Exception as e:
            self.logger.error(f"Failed to get completion statistics: {e}")
            return {}
    
    # Detection operations (coordinate with Qt detection service)
    def start_detection(self) -> None:
        """Start the detection process."""
        try:
            if not self._detection_service:
                raise BusinessControllerError("Detection service not available")
            
            # Get current hole collection from business service
            hole_collection = self.business_service.get_hole_collection()
            if not hole_collection:
                raise BusinessControllerError("No hole collection loaded")
            
            result = self._detection_service.start_detection(hole_collection)
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
    
    # Simulation operations (coordinate with Qt detection service)
    def start_simulation(self, parameters: Dict[str, Any]) -> None:
        """
        Start simulation with given parameters.
        
        Args:
            parameters: Simulation parameters
        """
        try:
            if not self._detection_service:
                raise BusinessControllerError("Detection service not available")
            
            # Get current hole collection from business service
            hole_collection = self.business_service.get_hole_collection()
            if not hole_collection:
                raise BusinessControllerError("No hole collection loaded")
            
            result = self._detection_service.start_simulation(hole_collection)
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
    
    # State management (coordinate with business service)
    def get_current_state(self) -> Dict[str, Any]:
        """
        Get current business coordinator state.
        
        Returns:
            Dictionary with current state information
        """
        try:
            # Get state from business service
            hole_collection = self.business_service.get_hole_collection()
            current_product = self.business_service.current_product
            
            state = {
                "has_hole_collection": hole_collection is not None,
                "current_product": current_product.model_name if current_product else None,
                "services_available": {
                    "search_service": self._search_service is not None,
                    "status_service": self._status_service is not None,
                    "detection_service": self._detection_service is not None
                }
            }
            
            # Add service-specific state
            if self._detection_service:
                state["detection_running"] = self._detection_service.is_detection_running()
                state["simulation_running"] = self._detection_service.is_simulation_running()
            
            return state
            
        except Exception as e:
            self.logger.error(f"Failed to get current state: {e}")
            return {}
    
    # Signal handlers
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
            # Cleanup Qt services
            if self._detection_service:
                self._detection_service.cleanup()
            
            if self._search_service:
                self._search_service.cleanup()
            
            if self._status_service:
                self._status_service.cleanup()
            
            # Cleanup business service
            self.business_service.cleanup()
            
            self.logger.debug("Business coordinator cleaned up")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup business coordinator: {e}")


# Global business coordinator instance
_global_business_coordinator = None


def get_business_coordinator() -> BusinessCoordinator:
    """Get global business coordinator instance."""
    global _global_business_coordinator
    if _global_business_coordinator is None:
        _global_business_coordinator = BusinessCoordinator()
    return _global_business_coordinator