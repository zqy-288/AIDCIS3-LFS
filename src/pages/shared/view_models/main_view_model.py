"""
MainViewModel implementation for the MVVM architecture.

This module implements the data model for UI binding, containing all state
information needed for the main window display.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum

# from ...core.interfaces.main_interfaces import IMainViewModel  # Removed due to dataclass compatibility
from src.core.exceptions.main_exceptions import DataValidationError
from src.shared.utils.validation import TypeValidator, safe_cast


class ViewMode(Enum):
    """View mode enumeration."""
    MACRO = "macro"
    MICRO = "micro"
    PANORAMA = "panorama"


class MessageLevel(Enum):
    """Message level enumeration."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


@dataclass
class MainViewModel:
    """
    Main view model containing all UI state data.
    
    This dataclass holds
    all the state information needed for UI display and binding.
    """
    
    # Window information
    window_title: str = "AIDCIS3-LFS 工业检测系统"
    
    # File information
    current_file_path: Optional[str] = None
    file_info: Dict[str, Any] = field(default_factory=dict)
    
    # Detection state
    detection_running: bool = False
    detection_progress: float = 0.0
    current_hole_id: Optional[str] = None
    
    # Display state
    current_sector: Optional[Any] = None
    view_mode: str = ViewMode.MACRO.value
    
    # Data state
    hole_collection: Optional[Any] = None
    total_holes_count: int = 0
    status_summary: Dict[str, int] = field(default_factory=lambda: {
        "pending": 0,
        "qualified": 0, 
        "defective": 0,
        "blind": 0,
        "tie_rod": 0,
        "processing": 0
    })
    
    # Search state
    search_query: str = ""
    search_results: List[str] = field(default_factory=list)
    
    # UI state
    loading: bool = False
    message: str = ""
    message_level: str = MessageLevel.INFO.value
    
    # Progress tracking
    completed_count: int = 0
    pending_count: int = 0
    detection_time_seconds: int = 0
    estimated_time_seconds: int = 0
    completion_rate: float = 0.0
    qualification_rate: float = 0.0
    
    # View controls
    view_filter: str = "all"  # all, pending, qualified, defective
    snake_path_enabled: bool = False
    snake_path_strategy: str = "hybrid"
    snake_path_debug: bool = False
    
    # Product information
    current_product: Optional[str] = None
    product_info: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> List[str]:
        """
        Validate the current view model state.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Validate detection progress
        if not (0.0 <= self.detection_progress <= 100.0):
            errors.append("Detection progress must be between 0 and 100")
        
        # Validate view mode
        valid_view_modes = [mode.value for mode in ViewMode]
        if self.view_mode not in valid_view_modes:
            errors.append(f"Invalid view mode: {self.view_mode}")
        
        # Validate message level
        valid_message_levels = [level.value for level in MessageLevel]
        if self.message_level not in valid_message_levels:
            errors.append(f"Invalid message level: {self.message_level}")
        
        # Validate rates
        if not (0.0 <= self.completion_rate <= 100.0):
            errors.append("Completion rate must be between 0 and 100")
        
        if not (0.0 <= self.qualification_rate <= 100.0):
            errors.append("Qualification rate must be between 0 and 100")
        
        # Validate counts
        if self.completed_count < 0:
            errors.append("Completed count cannot be negative")
        
        if self.pending_count < 0:
            errors.append("Pending count cannot be negative")
        
        # Validate status summary
        for status, count in self.status_summary.items():
            if count < 0:
                errors.append(f"Status count for '{status}' cannot be negative")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the view model to a dictionary.
        
        Returns:
            Dictionary representation of the view model
        """
        return {
            'current_file_path': self.current_file_path,
            'file_info': self.file_info,
            'detection_running': self.detection_running,
            'detection_progress': self.detection_progress,
            'current_hole_id': self.current_hole_id,
            'current_sector': self.current_sector,
            'view_mode': self.view_mode,
            'hole_collection': self.hole_collection,
            'status_summary': self.status_summary,
            'search_query': self.search_query,
            'search_results': self.search_results,
            'loading': self.loading,
            'message': self.message,
            'message_level': self.message_level,
            'completed_count': self.completed_count,
            'pending_count': self.pending_count,
            'detection_time_seconds': self.detection_time_seconds,
            'estimated_time_seconds': self.estimated_time_seconds,
            'completion_rate': self.completion_rate,
            'qualification_rate': self.qualification_rate,
            'view_filter': self.view_filter,
            'snake_path_enabled': self.snake_path_enabled,
            'snake_path_strategy': self.snake_path_strategy,
            'snake_path_debug': self.snake_path_debug,
            'current_product': self.current_product,
            'product_info': self.product_info
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MainViewModel':
        """
        Create a MainViewModel from a dictionary.
        
        Args:
            data: Dictionary containing view model data
            
        Returns:
            MainViewModel instance
        """
        # Filter known fields and use safe casting
        kwargs = {}
        for field_name in cls.__dataclass_fields__:
            if field_name in data:
                field_type = cls.__dataclass_fields__[field_name].type
                kwargs[field_name] = safe_cast(data[field_name], field_type)
        
        return cls(**kwargs)
    
    def copy(self) -> 'MainViewModel':
        """
        Create a deep copy of the view model.
        
        Returns:
            New MainViewModel instance with copied data
        """
        return MainViewModel.from_dict(self.to_dict())
    
    def update_detection_progress(self, progress: float, completed: int, pending: int) -> None:
        """
        Update detection progress information.
        
        Args:
            progress: Progress percentage (0-100)
            completed: Number of completed holes
            pending: Number of pending holes
        """
        self.detection_progress = max(0.0, min(100.0, progress))
        self.completed_count = max(0, completed)
        self.pending_count = max(0, pending)
        
        # Calculate completion rate
        total = completed + pending
        self.completion_rate = (completed / total * 100.0) if total > 0 else 0.0
    
    def update_status_summary(self, status_counts: Dict[str, int]) -> None:
        """
        Update status summary information.
        
        Args:
            status_counts: Dictionary of status names to counts
        """
        self.status_summary.update(status_counts)
        
        # Calculate qualification rate
        total = sum(self.status_summary.values())
        qualified = self.status_summary.get("qualified", 0)
        self.qualification_rate = (qualified / total * 100.0) if total > 0 else 0.0
    
    def update_file_info(self, file_path: str, info: Dict[str, Any]) -> None:
        """
        Update file information.
        
        Args:
            file_path: Path to the loaded file
            info: File information dictionary
        """
        self.current_file_path = file_path
        self.file_info = info.copy()
    
    def update_search_results(self, query: str, results: List[str]) -> None:
        """
        Update search results.
        
        Args:
            query: Search query string
            results: List of search result IDs
        """
        self.search_query = query
        self.search_results = results.copy()
    
    def set_message(self, message: str, level: MessageLevel = MessageLevel.INFO) -> None:
        """
        Set status message.
        
        Args:
            message: Message text
            level: Message level
        """
        self.message = message
        self.message_level = level.value
    
    def clear_message(self) -> None:
        """Clear the current status message."""
        self.message = ""
        self.message_level = MessageLevel.INFO.value
    
    def format_time(self, seconds: int) -> str:
        """
        Format time in seconds to HH:MM:SS string.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted time string
        """
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def get_detection_time_formatted(self) -> str:
        """Get formatted detection time string."""
        return self.format_time(self.detection_time_seconds)
    
    def get_estimated_time_formatted(self) -> str:
        """Get formatted estimated time string."""
        return self.format_time(self.estimated_time_seconds)