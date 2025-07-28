"""
MainViewModelManager implementation for the MVVM architecture.

This module manages the lifecycle and change notifications for the MainViewModel,
providing a centralized way to update and distribute view model changes.
"""

import logging
from typing import Optional, Dict, Any, List
from PySide6.QtCore import QObject, Signal

from .main_view_model import MainViewModel, MessageLevel
from ...exceptions.main_exceptions import ViewModelError
from ...utils.mvvm_utils import SignalThrottler


class MainViewModelManager(QObject):
    """
    Manages the MainViewModel lifecycle and change notifications.
    
    This class provides a centralized way to manage view model updates
    and emit change notifications to interested components.
    """
    
    # Signals for view model changes
    view_model_changed = Signal(object)  # Emitted when view model changes
    message_changed = Signal(str, str)   # Emitted when message changes (message, level)
    loading_changed = Signal(bool)       # Emitted when loading state changes
    progress_changed = Signal(float)     # Emitted when detection progress changes
    
    def __init__(self, initial_view_model: Optional[MainViewModel] = None):
        """
        Initialize the view model manager.
        
        Args:
            initial_view_model: Optional initial view model, creates new if None
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Initialize view model
        self._view_model = initial_view_model or MainViewModel()
        
        # Setup signal throttling to prevent excessive UI updates
        self._throttler = SignalThrottler(delay_ms=50)  # 50ms throttle
        self._throttler.throttled_signal.connect(self._emit_view_model_changed)
        
        # Track previous values for change detection
        self._previous_message = self._view_model.message
        self._previous_message_level = self._view_model.message_level
        self._previous_loading = self._view_model.loading
        self._previous_progress = self._view_model.detection_progress
    
    @property
    def view_model(self) -> MainViewModel:
        """
        Get the current view model.
        
        Returns:
            Current MainViewModel instance
        """
        return self._view_model
    
    def set_view_model(self, view_model: MainViewModel) -> None:
        """
        Set a new view model and emit change notification.
        
        Args:
            view_model: New view model to set
            
        Raises:
            ViewModelError: If view model validation fails
        """
        try:
            # Validate the new view model
            validation_errors = view_model.validate()
            if validation_errors:
                raise ViewModelError(
                    f"View model validation failed: {', '.join(validation_errors)}",
                    validation_errors=validation_errors
                )
            
            self._view_model = view_model
            self._emit_change_notifications()
            self.logger.debug("View model updated successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to set view model: {e}")
            raise ViewModelError(f"Failed to set view model: {e}")
    
    def update_file_info(self, file_path: str, info: Dict[str, Any]) -> None:
        """
        Update file information in the view model.
        
        Args:
            file_path: Path to the loaded file
            info: File information dictionary
        """
        try:
            self._view_model.update_file_info(file_path, info)
            self._emit_change_notifications()
            self.logger.info(f"File info updated: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to update file info: {e}")
            raise ViewModelError(f"Failed to update file info: {e}")
    
    def update_detection_status(self, running: bool, progress: float = None) -> None:
        """
        Update detection status in the view model.
        
        Args:
            running: Whether detection is running
            progress: Optional progress percentage (0-100)
        """
        try:
            self._view_model.detection_running = running
            if progress is not None:
                self._view_model.detection_progress = max(0.0, min(100.0, progress))
            
            self._emit_change_notifications()
            self.logger.debug(f"Detection status updated: running={running}, progress={progress}")
            
        except Exception as e:
            self.logger.error(f"Failed to update detection status: {e}")
            raise ViewModelError(f"Failed to update detection status: {e}")
    
    def update_detection_progress(self, progress: float, completed: int, pending: int) -> None:
        """
        Update detection progress information.
        
        Args:
            progress: Progress percentage (0-100)
            completed: Number of completed holes
            pending: Number of pending holes
        """
        try:
            self._view_model.update_detection_progress(progress, completed, pending)
            self._emit_change_notifications()
            self.logger.debug(f"Detection progress updated: {progress}% ({completed}/{completed + pending})")
            
        except Exception as e:
            self.logger.error(f"Failed to update detection progress: {e}")
            raise ViewModelError(f"Failed to update detection progress: {e}")
    
    def update_status_summary(self, status_counts: Dict[str, int]) -> None:
        """
        Update status summary information.
        
        Args:
            status_counts: Dictionary of status names to counts
        """
        try:
            self._view_model.update_status_summary(status_counts)
            self._emit_change_notifications()
            self.logger.debug(f"Status summary updated: {status_counts}")
            
        except Exception as e:
            self.logger.error(f"Failed to update status summary: {e}")
            raise ViewModelError(f"Failed to update status summary: {e}")
    
    def update_hole_collection(self, collection: Any) -> None:
        """
        Update hole collection in the view model.
        
        Args:
            collection: Hole collection object
        """
        try:
            self._view_model.hole_collection = collection
            self._emit_change_notifications()
            self.logger.debug("Hole collection updated")
            
        except Exception as e:
            self.logger.error(f"Failed to update hole collection: {e}")
            raise ViewModelError(f"Failed to update hole collection: {e}")
    
    def update_search_results(self, query: str, results: List[str]) -> None:
        """
        Update search results in the view model.
        
        Args:
            query: Search query string
            results: List of search result IDs
        """
        try:
            self._view_model.update_search_results(query, results)
            self._emit_change_notifications()
            self.logger.debug(f"Search results updated: {len(results)} results for '{query}'")
            
        except Exception as e:
            self.logger.error(f"Failed to update search results: {e}")
            raise ViewModelError(f"Failed to update search results: {e}")
    
    def set_message(self, message: str, level: MessageLevel = MessageLevel.INFO) -> None:
        """
        Set status message in the view model.
        
        Args:
            message: Message text
            level: Message level
        """
        try:
            self._view_model.set_message(message, level)
            self._emit_change_notifications()
            self.logger.info(f"Message set: [{level.value}] {message}")
            
        except Exception as e:
            self.logger.error(f"Failed to set message: {e}")
            raise ViewModelError(f"Failed to set message: {e}")
    
    def clear_message(self) -> None:
        """Clear the current status message."""
        try:
            self._view_model.clear_message()
            self._emit_change_notifications()
            self.logger.debug("Message cleared")
            
        except Exception as e:
            self.logger.error(f"Failed to clear message: {e}")
            raise ViewModelError(f"Failed to clear message: {e}")
    
    def set_loading_state(self, loading: bool) -> None:
        """
        Set loading state in the view model.
        
        Args:
            loading: True to show loading state, False to hide
        """
        try:
            self._view_model.loading = loading
            self._emit_change_notifications()
            self.logger.debug(f"Loading state set to: {loading}")
            
        except Exception as e:
            self.logger.error(f"Failed to set loading state: {e}")
            raise ViewModelError(f"Failed to set loading state: {e}")
    
    def select_hole(self, hole_id: Optional[str]) -> None:
        """
        Select a hole in the view model.
        
        Args:
            hole_id: ID of the hole to select, or None to deselect
        """
        try:
            self._view_model.current_hole_id = hole_id
            self._emit_change_notifications()
            self.logger.debug(f"Hole selected: {hole_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to select hole: {e}")
            raise ViewModelError(f"Failed to select hole: {e}")
    
    def set_view_filter(self, filter_type: str) -> None:
        """
        Set view filter in the view model.
        
        Args:
            filter_type: Type of filter ("all", "pending", "qualified", "defective")
        """
        try:
            valid_filters = ["all", "pending", "qualified", "defective"]
            if filter_type not in valid_filters:
                raise ViewModelError(f"Invalid filter type: {filter_type}")
            
            self._view_model.view_filter = filter_type
            self._emit_change_notifications()
            self.logger.debug(f"View filter set to: {filter_type}")
            
        except Exception as e:
            self.logger.error(f"Failed to set view filter: {e}")
            raise ViewModelError(f"Failed to set view filter: {e}")
    
    def set_snake_path_options(self, enabled: bool, strategy: str = None, debug: bool = None) -> None:
        """
        Set snake path options in the view model.
        
        Args:
            enabled: Whether snake path is enabled
            strategy: Optional strategy type
            debug: Optional debug mode flag
        """
        try:
            self._view_model.snake_path_enabled = enabled
            if strategy is not None:
                self._view_model.snake_path_strategy = strategy
            if debug is not None:
                self._view_model.snake_path_debug = debug
            
            self._emit_change_notifications()
            self.logger.debug(f"Snake path options updated: enabled={enabled}")
            
        except Exception as e:
            self.logger.error(f"Failed to set snake path options: {e}")
            raise ViewModelError(f"Failed to set snake path options: {e}")
    
    def update_detection_time(self, seconds: int) -> None:
        """
        Update detection time in the view model.
        
        Args:
            seconds: Detection time in seconds
        """
        try:
            self._view_model.detection_time_seconds = max(0, seconds)
            self._emit_change_notifications()
            
        except Exception as e:
            self.logger.error(f"Failed to update detection time: {e}")
            raise ViewModelError(f"Failed to update detection time: {e}")
    
    def _emit_change_notifications(self) -> None:
        """Emit change notifications for view model updates."""
        try:
            # Check for specific changes that need individual signals
            if self._view_model.message != self._previous_message or \
               self._view_model.message_level != self._previous_message_level:
                self.message_changed.emit(self._view_model.message, self._view_model.message_level)
                self._previous_message = self._view_model.message
                self._previous_message_level = self._view_model.message_level
            
            if self._view_model.loading != self._previous_loading:
                self.loading_changed.emit(self._view_model.loading)
                self._previous_loading = self._view_model.loading
            
            if self._view_model.detection_progress != self._previous_progress:
                self.progress_changed.emit(self._view_model.detection_progress)
                self._previous_progress = self._view_model.detection_progress
            
            # Emit throttled general change notification
            self._throttler.emit_throttled(self._view_model)
            
        except Exception as e:
            self.logger.error(f"Failed to emit change notifications: {e}")
    
    def _emit_view_model_changed(self, view_model: MainViewModel) -> None:
        """
        Emit the view model changed signal.
        
        Args:
            view_model: The changed view model
        """
        try:
            self.view_model_changed.emit(view_model)
        except Exception as e:
            self.logger.error(f"Failed to emit view model changed signal: {e}")
    
    def reset(self) -> None:
        """Reset the view model to initial state."""
        try:
            self._view_model = MainViewModel()
            self._emit_change_notifications()
            self.logger.info("View model reset to initial state")
            
        except Exception as e:
            self.logger.error(f"Failed to reset view model: {e}")
            raise ViewModelError(f"Failed to reset view model: {e}")
    
    def get_state_snapshot(self) -> Dict[str, Any]:
        """
        Get a snapshot of the current view model state.
        
        Returns:
            Dictionary representation of current state
        """
        try:
            return self._view_model.to_dict()
        except Exception as e:
            self.logger.error(f"Failed to get state snapshot: {e}")
            raise ViewModelError(f"Failed to get state snapshot: {e}")
    
    def restore_state_snapshot(self, state: Dict[str, Any]) -> None:
        """
        Restore view model state from a snapshot.
        
        Args:
            state: Dictionary containing view model state
        """
        try:
            restored_model = MainViewModel.from_dict(state)
            self.set_view_model(restored_model)
            self.logger.info("View model state restored from snapshot")
            
        except Exception as e:
            self.logger.error(f"Failed to restore state snapshot: {e}")
            raise ViewModelError(f"Failed to restore state snapshot: {e}")