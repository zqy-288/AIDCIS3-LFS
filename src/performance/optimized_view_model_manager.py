"""
Optimized View Model Manager for High-Performance MVVM
Implements efficient view model updates with change tracking and batching
"""

import time
import hashlib
from typing import Dict, Any, Optional, Set, List, Callable
from dataclasses import dataclass, asdict
from PySide6.QtCore import QObject, Signal, QTimer
from collections import defaultdict

from src.ui.view_models.main_view_model import MainViewModel
from src.performance.signal_optimizer import get_signal_manager, SignalPriority


@dataclass
class ChangeSet:
    """Represents a set of changes to the view model"""
    field_name: str
    old_value: Any
    new_value: Any
    timestamp: float
    priority: SignalPriority = SignalPriority.NORMAL


class ViewModelChangeTracker:
    """
    Tracks changes to view model fields and determines update necessity
    """
    
    def __init__(self):
        self.field_hashes: Dict[str, str] = {}
        self.last_update_times: Dict[str, float] = {}
        self.change_frequency: Dict[str, int] = defaultdict(int)
        self.ignore_fields: Set[str] = set()
        
        # Field priority mapping
        self.field_priorities = {
            # High priority fields (immediate UI impact)
            "detection_running": SignalPriority.HIGH,
            "detection_progress": SignalPriority.HIGH,
            "message": SignalPriority.HIGH,
            "loading": SignalPriority.HIGH,
            
            # Normal priority fields
            "current_hole_id": SignalPriority.NORMAL,
            "current_sector": SignalPriority.NORMAL,
            "search_query": SignalPriority.NORMAL,
            "search_results": SignalPriority.NORMAL,
            
            # Low priority fields (background updates)
            "detection_time_seconds": SignalPriority.LOW,
            "estimated_time_seconds": SignalPriority.LOW,
            "file_info": SignalPriority.LOW,
            "product_info": SignalPriority.LOW
        }
        
    def calculate_field_hash(self, value: Any) -> str:
        """Calculate hash for a field value"""
        try:
            if isinstance(value, (dict, list)):
                # For complex objects, convert to string representation
                value_str = str(sorted(value.items())) if isinstance(value, dict) else str(value)
            else:
                value_str = str(value)
            return hashlib.md5(value_str.encode()).hexdigest()[:8]
        except Exception:
            return "unknown"
            
    def has_field_changed(self, field_name: str, new_value: Any) -> bool:
        """Check if a field has actually changed"""
        new_hash = self.calculate_field_hash(new_value)
        old_hash = self.field_hashes.get(field_name)
        
        if old_hash != new_hash:
            self.field_hashes[field_name] = new_hash
            self.change_frequency[field_name] += 1
            return True
        return False
        
    def should_update_field(self, field_name: str, min_interval: float = 0.016) -> bool:
        """
        Determine if field should be updated based on frequency and timing
        min_interval: Minimum time between updates (default: ~60fps)
        """
        if field_name in self.ignore_fields:
            return False
            
        current_time = time.time()
        last_update = self.last_update_times.get(field_name, 0)
        
        # Check minimum interval
        if current_time - last_update < min_interval:
            # Allow high-priority fields to update more frequently
            priority = self.field_priorities.get(field_name, SignalPriority.NORMAL)
            if priority != SignalPriority.HIGH:
                return False
                
        self.last_update_times[field_name] = current_time
        return True
        
    def get_field_priority(self, field_name: str) -> SignalPriority:
        """Get priority for a field"""
        return self.field_priorities.get(field_name, SignalPriority.NORMAL)
        
    def add_ignore_field(self, field_name: str):
        """Add field to ignore list"""
        self.ignore_fields.add(field_name)
        
    def remove_ignore_field(self, field_name: str):
        """Remove field from ignore list"""
        self.ignore_fields.discard(field_name)
        
    def get_change_statistics(self) -> Dict[str, Any]:
        """Get statistics about field changes"""
        return {
            "total_fields_tracked": len(self.field_hashes),
            "change_frequency": dict(self.change_frequency),
            "ignored_fields": list(self.ignore_fields),
            "field_priorities": {k: v.name for k, v in self.field_priorities.items()}
        }


class OptimizedViewModelManager(QObject):
    """
    High-performance view model manager with intelligent change tracking
    and batched updates
    """
    
    # Optimized signals with reduced frequency
    view_model_changed = Signal(object)  # Batched view model changes
    field_changed = Signal(str, object, object)  # field_name, old_value, new_value
    critical_update = Signal(str, object)  # field_name, new_value (for immediate updates)
    
    def __init__(self, initial_view_model: Optional[MainViewModel] = None):
        super().__init__()
        
        # Initialize view model
        self._view_model = initial_view_model or MainViewModel()
        self._previous_view_model = self._view_model.copy() if hasattr(self._view_model, 'copy') else None
        
        # Change tracking
        self.change_tracker = ViewModelChangeTracker()
        self.pending_changes: List[ChangeSet] = []
        
        # Signal manager integration
        self.signal_manager = get_signal_manager()
        
        # Batch update timer
        self.batch_timer = QTimer()
        self.batch_timer.timeout.connect(self._process_pending_changes)
        self.batch_timer.setSingleShot(True)
        self.batch_interval = 50  # 50ms batching interval
        
        # Performance monitoring
        self.update_stats = {
            "total_updates": 0,
            "batched_updates": 0,
            "immediate_updates": 0,
            "skipped_updates": 0,
            "average_batch_size": 0
        }
        
        # Callback registry for field-specific handlers
        self.field_callbacks: Dict[str, List[Callable]] = defaultdict(list)
        
    @property
    def view_model(self) -> MainViewModel:
        """Get current view model"""
        return self._view_model
        
    def update_field(self, field_name: str, new_value: Any, 
                    force_update: bool = False,
                    immediate: bool = False) -> bool:
        """
        Update a single field in the view model with optimization
        
        Args:
            field_name: Name of the field to update
            new_value: New value for the field
            force_update: Force update even if value hasn't changed
            immediate: Emit immediate signal (bypass batching)
            
        Returns:
            True if update was processed, False if skipped
        """
        # Get current value
        old_value = getattr(self._view_model, field_name, None)
        
        # Check if change is necessary
        if not force_update:
            if not self.change_tracker.has_field_changed(field_name, new_value):
                self.update_stats["skipped_updates"] += 1
                return False
                
            if not self.change_tracker.should_update_field(field_name):
                self.update_stats["skipped_updates"] += 1
                return False
                
        # Update the field
        try:
            setattr(self._view_model, field_name, new_value)
        except AttributeError:
            # Field doesn't exist
            return False
            
        # Determine priority and handling
        priority = self.change_tracker.get_field_priority(field_name)
        
        if immediate or priority == SignalPriority.CRITICAL:
            # Emit immediate signal
            self.critical_update.emit(field_name, new_value)
            self.update_stats["immediate_updates"] += 1
        else:
            # Add to pending changes for batching
            change = ChangeSet(
                field_name=field_name,
                old_value=old_value,
                new_value=new_value,
                timestamp=time.time(),
                priority=priority
            )
            self.pending_changes.append(change)
            
            # Start batch timer if not already running
            if not self.batch_timer.isActive():
                self.batch_timer.start(self.batch_interval)
                
        # Emit field-specific signal
        self.field_changed.emit(field_name, old_value, new_value)
        
        # Execute field-specific callbacks
        self._execute_field_callbacks(field_name, old_value, new_value)
        
        self.update_stats["total_updates"] += 1
        return True
        
    def update_multiple_fields(self, field_updates: Dict[str, Any], 
                              force_update: bool = False) -> Dict[str, bool]:
        """
        Update multiple fields efficiently
        
        Args:
            field_updates: Dictionary of field_name -> new_value
            force_update: Force all updates
            
        Returns:
            Dictionary of field_name -> update_success
        """
        results = {}
        
        # Sort updates by priority
        prioritized_updates = []
        for field_name, new_value in field_updates.items():
            priority = self.change_tracker.get_field_priority(field_name)
            prioritized_updates.append((priority.value, field_name, new_value))
            
        # Process in priority order
        prioritized_updates.sort(key=lambda x: x[0], reverse=True)
        
        for _, field_name, new_value in prioritized_updates:
            results[field_name] = self.update_field(field_name, new_value, force_update)
            
        return results
        
    def _process_pending_changes(self):
        """Process all pending changes in a batch"""
        if not self.pending_changes:
            return
            
        # Sort changes by priority
        self.pending_changes.sort(key=lambda c: c.priority.value, reverse=True)
        
        # Group changes by priority for efficient processing
        high_priority_changes = [c for c in self.pending_changes if c.priority == SignalPriority.HIGH]
        normal_priority_changes = [c for c in self.pending_changes if c.priority == SignalPriority.NORMAL]
        low_priority_changes = [c for c in self.pending_changes if c.priority == SignalPriority.LOW]
        
        # Process high priority changes first
        if high_priority_changes:
            self._emit_batch_update(high_priority_changes)
            
        # Process normal priority changes
        if normal_priority_changes:
            self._emit_batch_update(normal_priority_changes)
            
        # Process low priority changes (limit to prevent UI lag)
        if low_priority_changes:
            # Limit low priority changes per batch
            limited_changes = low_priority_changes[:10]
            self._emit_batch_update(limited_changes)
            
            # Keep remaining changes for next batch
            remaining_changes = low_priority_changes[10:]
            if remaining_changes:
                self.pending_changes = remaining_changes
                self.batch_timer.start(self.batch_interval * 2)  # Longer interval for low priority
                return
                
        # Update statistics
        total_changes = len(self.pending_changes)
        self.update_stats["batched_updates"] += 1
        
        # Update average batch size
        current_avg = self.update_stats.get("average_batch_size", 0)
        total_batches = self.update_stats["batched_updates"]
        new_avg = (current_avg * (total_batches - 1) + total_changes) / total_batches
        self.update_stats["average_batch_size"] = new_avg
        
        # Clear pending changes
        self.pending_changes.clear()
        
    def _emit_batch_update(self, changes: List[ChangeSet]):
        """Emit a batch of changes"""
        if changes:
            # Emit main view model changed signal
            self.view_model_changed.emit(self._view_model)
            
            # Use signal manager for efficient transmission
            self.signal_manager.emit_signal(
                "view_model_batch_update",
                changes,
                priority=changes[0].priority if changes else SignalPriority.NORMAL,
                source_id="optimized_view_model_manager",
                use_batching=True
            )
            
    def register_field_callback(self, field_name: str, callback: Callable[[Any, Any], None]):
        """
        Register a callback for field changes
        
        Args:
            field_name: Field to monitor
            callback: Function to call with (old_value, new_value)
        """
        self.field_callbacks[field_name].append(callback)
        
    def unregister_field_callback(self, field_name: str, callback: Callable):
        """Unregister a field callback"""
        if field_name in self.field_callbacks:
            try:
                self.field_callbacks[field_name].remove(callback)
            except ValueError:
                pass
                
    def _execute_field_callbacks(self, field_name: str, old_value: Any, new_value: Any):
        """Execute callbacks for a field change"""
        for callback in self.field_callbacks.get(field_name, []):
            try:
                callback(old_value, new_value)
            except Exception as e:
                # Log error but don't interrupt processing
                print(f"Error in field callback for {field_name}: {e}")
                
    def set_batch_interval(self, interval_ms: int):
        """Set the batching interval"""
        self.batch_interval = max(16, min(200, interval_ms))  # 16ms (60fps) to 200ms
        
    def optimize_performance(self):
        """Automatically optimize performance based on current statistics"""
        stats = self.get_performance_statistics()
        
        # Adjust batch interval based on update frequency
        avg_batch_size = stats.get("average_batch_size", 0)
        
        if avg_batch_size > 20:
            # High update frequency - reduce batch interval
            self.set_batch_interval(max(25, self.batch_interval - 5))
        elif avg_batch_size < 5:
            # Low update frequency - increase batch interval
            self.set_batch_interval(min(100, self.batch_interval + 10))
            
        # Optimize signal manager
        self.signal_manager.optimize_settings()
        
    def ignore_field_updates(self, field_name: str, ignore: bool = True):
        """
        Ignore or unignore updates for a specific field
        
        Args:
            field_name: Field to ignore/unignore
            ignore: True to ignore, False to unignore
        """
        if ignore:
            self.change_tracker.add_ignore_field(field_name)
        else:
            self.change_tracker.remove_ignore_field(field_name)
            
    def get_performance_statistics(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        change_stats = self.change_tracker.get_change_statistics()
        signal_stats = self.signal_manager.get_performance_report()
        
        return {
            "update_stats": self.update_stats.copy(),
            "change_tracking": change_stats,
            "signal_management": signal_stats,
            "current_batch_size": len(self.pending_changes),
            "batch_interval_ms": self.batch_interval,
            "performance_score": self._calculate_performance_score()
        }
        
    def _calculate_performance_score(self) -> float:
        """Calculate overall performance score (0-100)"""
        if self.update_stats["total_updates"] == 0:
            return 100.0
            
        # Factors for performance score
        skip_ratio = self.update_stats["skipped_updates"] / self.update_stats["total_updates"]
        batch_ratio = self.update_stats["batched_updates"] / max(self.update_stats["total_updates"], 1)
        
        # Higher skip ratio and batch ratio = better performance
        score = (skip_ratio * 40 + batch_ratio * 40 + 20)  # Base 20 points
        return min(100.0, max(0.0, score))
        
    def reset_statistics(self):
        """Reset all performance statistics"""
        self.update_stats = {
            "total_updates": 0,
            "batched_updates": 0,
            "immediate_updates": 0,
            "skipped_updates": 0,
            "average_batch_size": 0
        }
        self.change_tracker.change_frequency.clear()
        
    def flush_pending_changes(self):
        """Immediately process all pending changes"""
        if self.pending_changes:
            self.batch_timer.stop()
            self._process_pending_changes()


# Factory function for creating optimized view model manager
def create_optimized_view_model_manager(initial_view_model: Optional[MainViewModel] = None) -> OptimizedViewModelManager:
    """Create an optimized view model manager instance"""
    return OptimizedViewModelManager(initial_view_model)