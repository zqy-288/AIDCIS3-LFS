"""
Status service implementation for business logic layer.

This module handles status management, statistics calculation,
and status-related operations.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Callable
from PySide6.QtCore import QObject, Signal, QTimer

from src.core.exceptions import BusinessControllerError


class StatusService(QObject):
    """
    Service for handling status management and statistics.
    
    This service manages hole status updates, calculates statistics,
    and provides status-related functionality.
    """
    
    # Signals for status operations
    status_updated = Signal(str, str)  # hole_id, new_status
    statistics_updated = Signal(dict)  # statistics_data
    summary_updated = Signal(dict)  # summary_data
    
    def __init__(self):
        """Initialize the status service."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Status tracking
        self._hole_statuses: Dict[str, str] = {}
        self._status_history: List[Dict[str, Any]] = []
        self._statistics_cache: Dict[str, Any] = {}
        self._last_update_time = 0
        
        # Data sources
        self._hole_collection: Optional[Any] = None
        
        # Statistics update timer
        self._stats_timer = QTimer()
        self._stats_timer.timeout.connect(self._update_statistics)
        self._stats_timer.start(1000)  # Update every second
        
        self.logger.debug("Status service initialized")
    
    @property
    def hole_statuses(self) -> Dict[str, str]:
        """Get current hole statuses."""
        return self._hole_statuses.copy()
    
    @property
    def statistics(self) -> Dict[str, Any]:
        """Get current statistics."""
        return self._statistics_cache.copy()
    
    def set_hole_collection(self, hole_collection: Any) -> None:
        """
        Set the hole collection for status management.
        
        Args:
            hole_collection: Collection of holes to manage
        """
        try:
            self._hole_collection = hole_collection
            self._sync_hole_statuses()
            self.logger.debug("Hole collection updated for status management")
            
        except Exception as e:
            self.logger.error(f"Failed to set hole collection: {e}")
    
    def _sync_hole_statuses(self) -> None:
        """Synchronize hole statuses from collection."""
        try:
            if not self._hole_collection:
                return
            
            # Extract holes from collection
            holes = []
            if hasattr(self._hole_collection, 'holes'):
                holes = self._hole_collection.holes
            elif hasattr(self._hole_collection, 'get_all_holes'):
                holes = self._hole_collection.get_all_holes()
            elif isinstance(self._hole_collection, list):
                holes = self._hole_collection
            
            # Update status tracking
            new_statuses = {}
            for hole in holes:
                hole_id = self._get_hole_id(hole)
                status = getattr(hole, 'status', 'pending')
                new_statuses[hole_id] = status
            
            self._hole_statuses = new_statuses
            self._update_statistics()
            
            self.logger.debug(f"Synchronized statuses for {len(self._hole_statuses)} holes")
            
        except Exception as e:
            self.logger.error(f"Failed to sync hole statuses: {e}")
    
    def update_hole_status(self, hole_id: str, new_status: str) -> None:
        """
        Update the status of a specific hole.
        
        Args:
            hole_id: ID of the hole to update
            new_status: New status value
        """
        try:
            if not hole_id:
                raise BusinessControllerError("Hole ID cannot be empty")
            
            old_status = self._hole_statuses.get(hole_id, 'unknown')
            
            # Update internal tracking
            self._hole_statuses[hole_id] = new_status
            
            # Add to history
            self._add_status_history(hole_id, old_status, new_status)
            
            # Update hole in collection if available
            if self._hole_collection:
                self._update_hole_in_collection(hole_id, new_status)
            
            # Emit signals
            self.status_updated.emit(hole_id, new_status)
            self._update_statistics()
            
            self.logger.debug(f"Status updated: {hole_id} {old_status} -> {new_status}")
            
        except Exception as e:
            error_msg = f"Failed to update hole status: {e}"
            self.logger.error(error_msg)
            raise BusinessControllerError(error_msg)
    
    def _add_status_history(self, hole_id: str, old_status: str, new_status: str) -> None:
        """Add status change to history."""
        try:
            history_entry = {
                'hole_id': hole_id,
                'old_status': old_status,
                'new_status': new_status,
                'timestamp': time.time(),
                'time_str': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self._status_history.append(history_entry)
            
            # Keep only last 1000 entries
            if len(self._status_history) > 1000:
                self._status_history = self._status_history[-1000:]
            
        except Exception as e:
            self.logger.warning(f"Failed to add status history: {e}")
    
    def _update_hole_in_collection(self, hole_id: str, new_status: str) -> None:
        """Update hole status in the collection."""
        try:
            if not self._hole_collection:
                return
            
            # Find and update the hole
            holes = []
            if hasattr(self._hole_collection, 'holes'):
                holes = self._hole_collection.holes
            elif hasattr(self._hole_collection, 'get_all_holes'):
                holes = self._hole_collection.get_all_holes()
            elif isinstance(self._hole_collection, list):
                holes = self._hole_collection
            
            for hole in holes:
                if self._get_hole_id(hole) == hole_id:
                    if hasattr(hole, 'status'):
                        hole.status = new_status
                    break
            
        except Exception as e:
            self.logger.warning(f"Failed to update hole in collection: {e}")
    
    def batch_update_statuses(self, status_updates: Dict[str, str]) -> None:
        """
        Update multiple hole statuses in a batch.
        
        Args:
            status_updates: Dictionary of hole_id -> new_status
        """
        try:
            updated_holes = []
            
            for hole_id, new_status in status_updates.items():
                try:
                    old_status = self._hole_statuses.get(hole_id, 'unknown')
                    self._hole_statuses[hole_id] = new_status
                    self._add_status_history(hole_id, old_status, new_status)
                    
                    if self._hole_collection:
                        self._update_hole_in_collection(hole_id, new_status)
                    
                    updated_holes.append(hole_id)
                    self.status_updated.emit(hole_id, new_status)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to update hole {hole_id}: {e}")
            
            # Update statistics once for all changes
            self._update_statistics()
            
            self.logger.info(f"Batch updated {len(updated_holes)} hole statuses")
            
        except Exception as e:
            error_msg = f"Failed to batch update statuses: {e}"
            self.logger.error(error_msg)
            raise BusinessControllerError(error_msg)
    
    def get_status_summary(self) -> Dict[str, int]:
        """
        Get summary of status counts.
        
        Returns:
            Dictionary with status counts
        """
        try:
            summary = {
                'total': len(self._hole_statuses),
                'pending': 0,
                'qualified': 0,
                'defective': 0,
                'blind': 0,
                'tie_rod': 0,
                'processing': 0,
                'unknown': 0
            }
            
            for status in self._hole_statuses.values():
                status_lower = status.lower()
                
                if status_lower in ['pending', 'waiting', 'todo']:
                    summary['pending'] += 1
                elif status_lower in ['qualified', 'pass', 'ok', 'good']:
                    summary['qualified'] += 1
                elif status_lower in ['defective', 'fail', 'bad', 'error']:
                    summary['defective'] += 1
                elif status_lower in ['blind']:
                    summary['blind'] += 1
                elif status_lower in ['tie_rod', 'tie-rod']:
                    summary['tie_rod'] += 1
                elif status_lower in ['processing', 'running', 'active']:
                    summary['processing'] += 1
                else:
                    summary['unknown'] += 1
            
            return summary
            
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
            total = len(self._hole_statuses)
            if total == 0:
                return {
                    'total_holes': 0,
                    'completed_holes': 0,
                    'pending_holes': 0,
                    'completion_rate': 0.0,
                    'qualification_rate': 0.0,
                    'defect_rate': 0.0
                }
            
            summary = self.get_status_summary()
            
            # Calculate completion (anything not pending)
            pending = summary.get('pending', 0)
            completed = total - pending
            
            # Calculate quality rates
            qualified = summary.get('qualified', 0)
            defective = summary.get('defective', 0)
            
            completion_rate = (completed / total) * 100.0 if total > 0 else 0.0
            qualification_rate = (qualified / total) * 100.0 if total > 0 else 0.0
            defect_rate = (defective / total) * 100.0 if total > 0 else 0.0
            
            return {
                'total_holes': total,
                'completed_holes': completed,
                'pending_holes': pending,
                'qualified_holes': qualified,
                'defective_holes': defective,
                'completion_rate': completion_rate,
                'qualification_rate': qualification_rate,
                'defect_rate': defect_rate,
                'last_updated': time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get completion statistics: {e}")
            return {}
    
    def _update_statistics(self) -> None:
        """Update cached statistics and emit signals."""
        try:
            current_time = time.time()
            
            # Throttle updates to once per second
            if current_time - self._last_update_time < 1.0:
                return
            
            self._last_update_time = current_time
            
            # Calculate statistics
            summary = self.get_status_summary()
            completion_stats = self.get_completion_statistics()
            
            # Combine all statistics
            all_stats = {
                'summary': summary,
                'completion': completion_stats,
                'timestamp': current_time
            }
            
            # Cache and emit
            self._statistics_cache = all_stats
            self.statistics_updated.emit(all_stats)
            self.summary_updated.emit(summary)
            
        except Exception as e:
            self.logger.warning(f"Failed to update statistics: {e}")
    
    def get_status_history(self, hole_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get status change history.
        
        Args:
            hole_id: Optional hole ID to filter by
            limit: Maximum number of entries to return
            
        Returns:
            List of status history entries
        """
        try:
            history = self._status_history
            
            # Filter by hole ID if specified
            if hole_id:
                history = [entry for entry in history if entry['hole_id'] == hole_id]
            
            # Sort by timestamp (most recent first) and limit
            history = sorted(history, key=lambda x: x['timestamp'], reverse=True)
            return history[:limit]
            
        except Exception as e:
            self.logger.error(f"Failed to get status history: {e}")
            return []
    
    def get_holes_by_status(self, status: str) -> List[str]:
        """
        Get list of hole IDs with a specific status.
        
        Args:
            status: Status to filter by
            
        Returns:
            List of hole IDs with the specified status
        """
        try:
            status_lower = status.lower()
            matching_holes = []
            
            for hole_id, hole_status in self._hole_statuses.items():
                hole_status_lower = hole_status.lower()
                
                # Handle status aliases
                if status_lower in ['pending', 'waiting', 'todo']:
                    if hole_status_lower in ['pending', 'waiting', 'todo']:
                        matching_holes.append(hole_id)
                elif status_lower in ['qualified', 'pass', 'ok', 'good']:
                    if hole_status_lower in ['qualified', 'pass', 'ok', 'good']:
                        matching_holes.append(hole_id)
                elif status_lower in ['defective', 'fail', 'bad', 'error']:
                    if hole_status_lower in ['defective', 'fail', 'bad', 'error']:
                        matching_holes.append(hole_id)
                elif hole_status_lower == status_lower:
                    matching_holes.append(hole_id)
            
            return matching_holes
            
        except Exception as e:
            self.logger.error(f"Failed to get holes by status: {e}")
            return []
    
    def reset_all_statuses(self, default_status: str = "pending") -> None:
        """
        Reset all hole statuses to a default value.
        
        Args:
            default_status: Status to set for all holes
        """
        try:
            reset_count = 0
            
            for hole_id in list(self._hole_statuses.keys()):
                old_status = self._hole_statuses[hole_id]
                self._hole_statuses[hole_id] = default_status
                self._add_status_history(hole_id, old_status, default_status)
                
                if self._hole_collection:
                    self._update_hole_in_collection(hole_id, default_status)
                
                self.status_updated.emit(hole_id, default_status)
                reset_count += 1
            
            self._update_statistics()
            self.logger.info(f"Reset {reset_count} hole statuses to '{default_status}'")
            
        except Exception as e:
            error_msg = f"Failed to reset statuses: {e}"
            self.logger.error(error_msg)
            raise BusinessControllerError(error_msg)
    
    def _get_hole_id(self, hole: Any) -> str:
        """Get hole ID from hole object."""
        if hasattr(hole, 'id'):
            return hole.id
        elif hasattr(hole, 'hole_id'):
            return hole.hole_id
        elif hasattr(hole, 'name'):
            return hole.name
        else:
            return str(hole)
    
    def cleanup(self) -> None:
        """Clean up resources when shutting down."""
        try:
            self._stats_timer.stop()
            self._hole_statuses.clear()
            self._status_history.clear()
            self._statistics_cache.clear()
            self._hole_collection = None
            
            self.logger.debug("Status service cleaned up")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup status service: {e}")