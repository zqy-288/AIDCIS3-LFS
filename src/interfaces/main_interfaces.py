"""
Core interfaces for MainWindow refactoring following MVVM pattern.

This module defines the interfaces that all main components must implement
to ensure proper separation of concerns and testability.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget, QMainWindow


@dataclass
class UserAction:
    """Represents a user action with parameters."""
    action_type: str
    parameters: Dict[str, Any]
    source_component: Optional[str] = None


class IMainViewController(ABC):
    """
    Interface for the main view controller (UI layer).
    
    Responsibilities:
    - Manage UI layout and components
    - Handle user interactions
    - Update UI based on view model changes
    - Emit user action signals
    
    This interface ensures the UI layer is completely decoupled from business logic.
    """
    
    @abstractmethod
    def setup_ui(self) -> None:
        """Initialize and setup the complete UI layout."""
        pass
    
    @abstractmethod
    def create_toolbar(self) -> QWidget:
        """
        Create and return the main toolbar widget.
        
        Returns:
            QWidget: The configured toolbar widget
        """
        pass
    
    @abstractmethod
    def create_left_info_panel(self) -> QWidget:
        """
        Create and return the left information panel.
        
        Returns:
            QWidget: The configured left panel widget
        """
        pass
    
    @abstractmethod
    def create_center_visualization_panel(self) -> QWidget:
        """
        Create and return the center visualization panel.
        
        Returns:
            QWidget: The configured center panel widget
        """
        pass
    
    @abstractmethod
    def create_right_operations_panel(self) -> QWidget:
        """
        Create and return the right operations panel.
        
        Returns:
            QWidget: The configured right panel widget
        """
        pass
    
    @abstractmethod
    def update_display(self, view_model: 'IMainViewModel') -> None:
        """
        Update the UI display based on view model changes.
        
        Args:
            view_model: The updated view model containing new state
        """
        pass
    
    @abstractmethod
    def show_message(self, message: str, level: str) -> None:
        """
        Display a message to the user.
        
        Args:
            message: The message text to display
            level: Message level ('info', 'warning', 'error')
        """
        pass
    
    @abstractmethod
    def set_loading_state(self, loading: bool) -> None:
        """
        Set the loading state of the UI.
        
        Args:
            loading: True to show loading state, False to hide
        """
        pass
    
    @abstractmethod
    def show(self) -> None:
        """Show the main window."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close the main window."""
        pass


class IMainBusinessController(ABC):
    """
    Interface for the main business controller (business logic layer).
    
    Responsibilities:
    - Handle user actions and coordinate business logic
    - Manage business services and data operations
    - Emit view model updates and status messages
    - Coordinate between different business services
    
    This interface ensures business logic is decoupled from UI concerns.
    """
    
    @abstractmethod
    def handle_user_action(self, action: UserAction) -> None:
        """
        Handle a user action received from the UI layer.
        
        Args:
            action: The user action to process
        """
        pass
    
    @abstractmethod
    def start_detection(self, parameters: Dict[str, Any]) -> None:
        """
        Start the detection/inspection process.
        
        Args:
            parameters: Detection parameters and configuration
        """
        pass
    
    @abstractmethod
    def load_dxf_file(self, file_path: str) -> None:
        """
        Load a DXF file and process it.
        
        Args:
            file_path: Path to the DXF file to load
        """
        pass
    
    @abstractmethod
    def select_hole(self, hole_id: str) -> None:
        """
        Select a specific hole for detailed view.
        
        Args:
            hole_id: Unique identifier of the hole to select
        """
        pass
    
    @abstractmethod
    def switch_sector(self, sector: Any) -> None:
        """
        Switch to a different sector view.
        
        Args:
            sector: The sector to switch to
        """
        pass
    
    @abstractmethod
    def perform_search(self, query: str) -> None:
        """
        Perform a search operation.
        
        Args:
            query: The search query string
        """
        pass
    
    @abstractmethod
    def export_report(self, parameters: Dict[str, Any]) -> None:
        """
        Export a report with given parameters.
        
        Args:
            parameters: Export parameters and configuration
        """
        pass
    
    @abstractmethod
    def initialize_services(self) -> None:
        """Initialize all required business services."""
        pass
    
    @abstractmethod
    def cleanup_resources(self) -> None:
        """Clean up resources when shutting down."""
        pass


class IMainViewModel(ABC):
    """
    Interface for the main view model (data binding layer).
    
    Responsibilities:
    - Hold all UI state data
    - Provide data change notifications
    - Maintain consistency of UI state
    - Support data validation and transformation
    
    This interface defines the contract for UI data binding.
    """
    
    @property
    @abstractmethod
    def current_file_path(self) -> Optional[str]:
        """Get the currently loaded file path."""
        pass
    
    @property
    @abstractmethod
    def file_info(self) -> Dict[str, Any]:
        """Get information about the current file."""
        pass
    
    @property
    @abstractmethod
    def detection_running(self) -> bool:
        """Get whether detection is currently running."""
        pass
    
    @property
    @abstractmethod
    def detection_progress(self) -> float:
        """Get the current detection progress (0.0 to 1.0)."""
        pass
    
    @property
    @abstractmethod
    def current_hole_id(self) -> Optional[str]:
        """Get the currently selected hole ID."""
        pass
    
    @property
    @abstractmethod
    def current_sector(self) -> Optional[Any]:
        """Get the currently selected sector."""
        pass
    
    @property
    @abstractmethod
    def view_mode(self) -> str:
        """Get the current view mode ('macro', 'micro', etc.)."""
        pass
    
    @property
    @abstractmethod
    def hole_collection(self) -> Optional[Any]:
        """Get the current hole collection."""
        pass
    
    @property
    @abstractmethod
    def status_summary(self) -> Dict[str, int]:
        """Get the current status summary."""
        pass
    
    @property
    @abstractmethod
    def search_query(self) -> str:
        """Get the current search query."""
        pass
    
    @property
    @abstractmethod
    def search_results(self) -> List[str]:
        """Get the current search results."""
        pass
    
    @property
    @abstractmethod
    def loading(self) -> bool:
        """Get whether the UI is in loading state."""
        pass
    
    @property
    @abstractmethod
    def message(self) -> str:
        """Get the current status message."""
        pass
    
    @property
    @abstractmethod
    def message_level(self) -> str:
        """Get the current message level."""
        pass
    
    @abstractmethod
    def validate(self) -> List[str]:
        """
        Validate the current view model state.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the view model to a dictionary.
        
        Returns:
            Dictionary representation of the view model
        """
        pass


class IMainWindowCoordinator(ABC):
    """
    Interface for the main window coordinator.
    
    Responsibilities:
    - Coordinate communication between UI and business layers
    - Manage component lifecycle
    - Handle cross-component concerns
    - Provide unified interface for the main window
    
    This interface defines the coordination contract between components.
    """
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize all components and setup connections."""
        pass
    
    @abstractmethod
    def show_main_window(self) -> None:
        """Show the main window."""
        pass
    
    @abstractmethod
    def close_main_window(self) -> None:
        """Close the main window and cleanup resources."""
        pass
    
    @abstractmethod
    def get_view_controller(self) -> IMainViewController:
        """
        Get the view controller instance.
        
        Returns:
            The main view controller instance
        """
        pass
    
    @abstractmethod
    def get_business_controller(self) -> IMainBusinessController:
        """
        Get the business controller instance.
        
        Returns:
            The main business controller instance
        """
        pass
    
    @abstractmethod
    def get_view_model(self) -> IMainViewModel:
        """
        Get the current view model.
        
        Returns:
            The current view model instance
        """
        pass
    
    @abstractmethod
    def handle_component_error(self, component: str, error: Exception) -> None:
        """
        Handle errors from components.
        
        Args:
            component: Name of the component that had an error
            error: The exception that occurred
        """
        pass
    
    @abstractmethod
    def register_component_event_handlers(self) -> None:
        """Register event handlers between components."""
        pass
    
    @abstractmethod
    def validate_component_states(self) -> List[str]:
        """
        Validate the state of all components.
        
        Returns:
            List of validation errors (empty if all valid)
        """
        pass