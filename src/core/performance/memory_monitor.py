"""
Memory Leak Detection and Monitoring System
Tracks memory usage, detects leaks, and provides memory optimization
"""

import gc
import sys
import time
import threading
import psutil
import weakref
from typing import Dict, Any, List, Optional, Set, Type, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
from PySide6.QtCore import QObject, Signal, QTimer


@dataclass
class MemorySnapshot:
    """Snapshot of memory state at a point in time"""
    timestamp: float
    total_memory_mb: float
    process_memory_mb: float
    python_memory_mb: float
    object_counts: Dict[Type, int] = field(default_factory=dict)
    large_objects: List[Any] = field(default_factory=list)
    gc_stats: Dict[str, int] = field(default_factory=dict)


@dataclass
class MemoryLeak:
    """Information about a detected memory leak"""
    object_type: Type
    initial_count: int
    current_count: int
    growth_rate: float  # objects per second
    first_detected: float
    last_updated: float
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL


class ObjectTracker:
    """
    Tracks object creation and destruction to detect leaks
    """
    
    def __init__(self):
        self.object_refs: Dict[Type, Set[weakref.ref]] = defaultdict(set)
        self.creation_counts: Dict[Type, int] = defaultdict(int)
        self.destruction_counts: Dict[Type, int] = defaultdict(int)
        self.lock = threading.RLock()
        
    def track_object(self, obj: Any):
        """Start tracking an object"""
        obj_type = type(obj)
        
        with self.lock:
            # Create weak reference with cleanup callback
            weak_ref = weakref.ref(obj, lambda ref: self._on_object_destroyed(obj_type, ref))
            self.object_refs[obj_type].add(weak_ref)
            self.creation_counts[obj_type] += 1
            
    def _on_object_destroyed(self, obj_type: Type, ref: weakref.ref):
        """Called when a tracked object is destroyed"""
        with self.lock:
            self.object_refs[obj_type].discard(ref)
            self.destruction_counts[obj_type] += 1
            
    def get_live_object_count(self, obj_type: Type) -> int:
        """Get count of live objects of a specific type"""
        with self.lock:
            # Clean up dead references
            self.object_refs[obj_type] = {
                ref for ref in self.object_refs[obj_type] 
                if ref() is not None
            }
            return len(self.object_refs[obj_type])
            
    def get_all_live_counts(self) -> Dict[Type, int]:
        """Get counts of all live tracked objects"""
        with self.lock:
            counts = {}
            for obj_type in self.object_refs:
                counts[obj_type] = self.get_live_object_count(obj_type)
            return counts
            
    def get_creation_stats(self) -> Dict[Type, Dict[str, int]]:
        """Get creation and destruction statistics"""
        with self.lock:
            stats = {}
            for obj_type in self.creation_counts:
                stats[obj_type] = {
                    "created": self.creation_counts[obj_type],
                    "destroyed": self.destruction_counts[obj_type],
                    "live": self.get_live_object_count(obj_type)
                }
            return stats


class MemoryMonitor(QObject):
    """
    Comprehensive memory monitoring and leak detection system
    """
    
    # Signals for memory events
    memory_snapshot_taken = Signal(object)  # MemorySnapshot
    memory_leak_detected = Signal(object)   # MemoryLeak
    memory_warning = Signal(str, float)     # message, memory_mb
    memory_critical = Signal(str, float)    # message, memory_mb
    
    def __init__(self, 
                 snapshot_interval: int = 30000,  # 30 seconds
                 leak_detection_threshold: float = 1.2,  # 20% growth
                 warning_threshold_mb: float = 1000.0,  # 1GB
                 critical_threshold_mb: float = 2000.0):  # 2GB
        super().__init__()
        
        # Configuration
        self.snapshot_interval = snapshot_interval
        self.leak_detection_threshold = leak_detection_threshold
        self.warning_threshold_mb = warning_threshold_mb
        self.critical_threshold_mb = critical_threshold_mb
        
        # Memory tracking
        self.snapshots: deque = deque(maxlen=100)  # Keep last 100 snapshots
        self.object_tracker = ObjectTracker()
        self.detected_leaks: Dict[Type, MemoryLeak] = {}
        
        # Monitoring state
        self.monitoring_active = False
        self.last_warning_time = 0
        self.last_critical_time = 0
        
        # Timers
        self.snapshot_timer = QTimer()
        self.snapshot_timer.timeout.connect(self.take_memory_snapshot)
        
        self.leak_detection_timer = QTimer()
        self.leak_detection_timer.timeout.connect(self.detect_memory_leaks)
        
        # Process handle
        self.process = psutil.Process()
        
        # Performance statistics
        self.stats = {
            "snapshots_taken": 0,
            "leaks_detected": 0,
            "warnings_issued": 0,
            "critical_alerts": 0,
            "memory_peak_mb": 0.0,
            "monitoring_start_time": 0.0
        }
        
    def start_monitoring(self):
        """Start memory monitoring"""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        self.stats["monitoring_start_time"] = time.time()
        
        # Take initial snapshot
        self.take_memory_snapshot()
        
        # Start timers
        self.snapshot_timer.start(self.snapshot_interval)
        self.leak_detection_timer.start(self.snapshot_interval * 2)  # Check for leaks less frequently
        
    def stop_monitoring(self):
        """Stop memory monitoring"""
        self.monitoring_active = False
        self.snapshot_timer.stop()
        self.leak_detection_timer.stop()
        
    def take_memory_snapshot(self) -> MemorySnapshot:
        """Take a snapshot of current memory usage"""
        try:
            current_time = time.time()
            
            # Get memory information
            memory_info = self.process.memory_info()
            process_memory_mb = memory_info.rss / 1024 / 1024
            
            # Get system memory
            virtual_memory = psutil.virtual_memory()
            total_memory_mb = virtual_memory.total / 1024 / 1024
            
            # Estimate Python memory usage
            python_memory_mb = self._estimate_python_memory()
            
            # Get object counts
            object_counts = self._get_object_counts()
            
            # Get large objects
            large_objects = self._find_large_objects()
            
            # Get GC statistics
            gc_stats = self._get_gc_stats()
            
            # Create snapshot
            snapshot = MemorySnapshot(
                timestamp=current_time,
                total_memory_mb=total_memory_mb,
                process_memory_mb=process_memory_mb,
                python_memory_mb=python_memory_mb,
                object_counts=object_counts,
                large_objects=large_objects,
                gc_stats=gc_stats
            )
            
            # Store snapshot
            self.snapshots.append(snapshot)
            self.stats["snapshots_taken"] += 1
            
            # Update peak memory
            if process_memory_mb > self.stats["memory_peak_mb"]:
                self.stats["memory_peak_mb"] = process_memory_mb
                
            # Check thresholds
            self._check_memory_thresholds(process_memory_mb)
            
            # Emit signal
            self.memory_snapshot_taken.emit(snapshot)
            
            return snapshot
            
        except Exception as e:
            print(f"Error taking memory snapshot: {e}")
            return None
            
    def _estimate_python_memory(self) -> float:
        """Estimate Python heap memory usage"""
        try:
            # Force garbage collection
            gc.collect()
            
            # Get object counts and estimate memory
            estimated_memory = 0
            
            for obj in gc.get_objects():
                try:
                    estimated_memory += sys.getsizeof(obj)
                except (TypeError, ValueError):
                    # Some objects don't support getsizeof
                    estimated_memory += 64  # Rough estimate
                    
            return estimated_memory / 1024 / 1024  # Convert to MB
            
        except Exception as e:
            print(f"Error estimating Python memory: {e}")
            return 0.0
            
    def _get_object_counts(self) -> Dict[Type, int]:
        """Get counts of objects by type"""
        try:
            object_counts = defaultdict(int)
            
            for obj in gc.get_objects():
                obj_type = type(obj)
                object_counts[obj_type] += 1
                
            return dict(object_counts)
            
        except Exception as e:
            print(f"Error getting object counts: {e}")
            return {}
            
    def _find_large_objects(self, size_threshold: int = 1024 * 1024) -> List[Any]:
        """Find objects larger than threshold"""
        try:
            large_objects = []
            
            for obj in gc.get_objects():
                try:
                    size = sys.getsizeof(obj)
                    if size > size_threshold:
                        large_objects.append({
                            "type": type(obj).__name__,
                            "size": size,
                            "id": id(obj)
                        })
                except (TypeError, ValueError):
                    continue
                    
            # Sort by size
            large_objects.sort(key=lambda x: x["size"], reverse=True)
            return large_objects[:20]  # Return top 20
            
        except Exception as e:
            print(f"Error finding large objects: {e}")
            return []
            
    def _get_gc_stats(self) -> Dict[str, int]:
        """Get garbage collection statistics"""
        try:
            stats = {}
            
            # Get GC counts
            counts = gc.get_counts()
            stats["gen0_count"] = counts[0] if len(counts) > 0 else 0
            stats["gen1_count"] = counts[1] if len(counts) > 1 else 0
            stats["gen2_count"] = counts[2] if len(counts) > 2 else 0
            
            # Get GC stats (if available)
            if hasattr(gc, 'get_stats'):
                gc_stats = gc.get_stats()
                for i, generation_stats in enumerate(gc_stats):
                    stats[f"gen{i}_collections"] = generation_stats.get("collections", 0)
                    stats[f"gen{i}_collected"] = generation_stats.get("collected", 0)
                    stats[f"gen{i}_uncollectable"] = generation_stats.get("uncollectable", 0)
                    
            return stats
            
        except Exception as e:
            print(f"Error getting GC stats: {e}")
            return {}
            
    def _check_memory_thresholds(self, memory_mb: float):
        """Check if memory usage exceeds thresholds"""
        current_time = time.time()
        
        # Critical threshold
        if memory_mb > self.critical_threshold_mb:
            if current_time - self.last_critical_time > 60:  # Don't spam critical alerts
                self.memory_critical.emit(
                    f"Critical memory usage: {memory_mb:.1f}MB", 
                    memory_mb
                )
                self.last_critical_time = current_time
                self.stats["critical_alerts"] += 1
                
        # Warning threshold
        elif memory_mb > self.warning_threshold_mb:
            if current_time - self.last_warning_time > 120:  # Don't spam warnings
                self.memory_warning.emit(
                    f"High memory usage: {memory_mb:.1f}MB", 
                    memory_mb
                )
                self.last_warning_time = current_time
                self.stats["warnings_issued"] += 1
                
    def detect_memory_leaks(self):
        """Detect potential memory leaks"""
        if len(self.snapshots) < 3:
            return  # Need at least 3 snapshots for trend analysis
            
        try:
            # Analyze object count trends
            current_snapshot = self.snapshots[-1]
            previous_snapshot = self.snapshots[-3]  # Compare with 2 snapshots ago
            
            time_diff = current_snapshot.timestamp - previous_snapshot.timestamp
            if time_diff <= 0:
                return
                
            # Check each object type for growth
            for obj_type, current_count in current_snapshot.object_counts.items():
                previous_count = previous_snapshot.object_counts.get(obj_type, 0)
                
                if previous_count == 0:
                    continue  # New object type
                    
                growth_ratio = current_count / previous_count
                
                if growth_ratio > self.leak_detection_threshold:
                    growth_rate = (current_count - previous_count) / time_diff
                    
                    # Check if this is a new leak or update existing
                    if obj_type in self.detected_leaks:
                        leak = self.detected_leaks[obj_type]
                        leak.current_count = current_count
                        leak.growth_rate = growth_rate
                        leak.last_updated = current_snapshot.timestamp
                        leak.severity = self._calculate_severity(growth_rate, current_count)
                    else:
                        leak = MemoryLeak(
                            object_type=obj_type,
                            initial_count=previous_count,
                            current_count=current_count,
                            growth_rate=growth_rate,
                            first_detected=current_snapshot.timestamp,
                            last_updated=current_snapshot.timestamp,
                            severity=self._calculate_severity(growth_rate, current_count)
                        )
                        self.detected_leaks[obj_type] = leak
                        self.stats["leaks_detected"] += 1
                        
                    # Emit leak detection signal
                    self.memory_leak_detected.emit(leak)
                    
        except Exception as e:
            print(f"Error detecting memory leaks: {e}")
            
    def _calculate_severity(self, growth_rate: float, object_count: int) -> str:
        """Calculate severity of a memory leak"""
        if growth_rate > 100 or object_count > 10000:
            return "CRITICAL"
        elif growth_rate > 50 or object_count > 5000:
            return "HIGH"
        elif growth_rate > 10 or object_count > 1000:
            return "MEDIUM"
        else:
            return "LOW"
            
    def force_garbage_collection(self):
        """Force garbage collection and take snapshot"""
        gc.collect()
        return self.take_memory_snapshot()
        
    def get_memory_trend(self, lookback_snapshots: int = 10) -> Dict[str, Any]:
        """Get memory usage trend over recent snapshots"""
        if len(self.snapshots) < 2:
            return {}
            
        recent_snapshots = list(self.snapshots)[-lookback_snapshots:]
        
        if len(recent_snapshots) < 2:
            return {}
            
        # Calculate trend
        first_snapshot = recent_snapshots[0]
        last_snapshot = recent_snapshots[-1]
        
        time_diff = last_snapshot.timestamp - first_snapshot.timestamp
        memory_diff = last_snapshot.process_memory_mb - first_snapshot.process_memory_mb
        
        trend = {
            "time_span_seconds": time_diff,
            "memory_change_mb": memory_diff,
            "memory_rate_mb_per_second": memory_diff / time_diff if time_diff > 0 else 0,
            "current_memory_mb": last_snapshot.process_memory_mb,
            "trend_direction": "increasing" if memory_diff > 0 else "decreasing" if memory_diff < 0 else "stable"
        }
        
        return trend
        
    def get_top_memory_consumers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top memory consuming object types"""
        if not self.snapshots:
            return []
            
        latest_snapshot = self.snapshots[-1]
        
        # Sort object types by count
        sorted_objects = sorted(
            latest_snapshot.object_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            {"type": obj_type.__name__, "count": count}
            for obj_type, count in sorted_objects[:limit]
        ]
        
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Get comprehensive memory monitoring report"""
        current_time = time.time()
        monitoring_duration = current_time - self.stats["monitoring_start_time"]
        
        report = {
            "monitoring_active": self.monitoring_active,
            "monitoring_duration_seconds": monitoring_duration,
            "statistics": self.stats.copy(),
            "current_memory_mb": self.snapshots[-1].process_memory_mb if self.snapshots else 0,
            "memory_trend": self.get_memory_trend(),
            "top_memory_consumers": self.get_top_memory_consumers(),
            "detected_leaks": [
                {
                    "type": leak.object_type.__name__,
                    "growth_rate": leak.growth_rate,
                    "current_count": leak.current_count,
                    "severity": leak.severity
                }
                for leak in self.detected_leaks.values()
            ],
            "large_objects": self.snapshots[-1].large_objects if self.snapshots else [],
            "gc_stats": self.snapshots[-1].gc_stats if self.snapshots else {}
        }
        
        return report
        
    def optimize_memory(self):
        """Perform memory optimization"""
        # Force garbage collection
        collected = gc.collect()
        
        # Clear any caches if objects have clear methods
        for obj in gc.get_objects():
            if hasattr(obj, 'clear') and callable(getattr(obj, 'clear')):
                try:
                    if hasattr(obj, '__len__') and len(obj) > 1000:  # Only clear large collections
                        obj.clear()
                except Exception:
                    pass  # Ignore errors
                    
        return {
            "garbage_collected": collected,
            "optimization_time": time.time()
        }


def track_object(obj: Any):
    """Decorator/function to track object for memory monitoring"""
    monitor = get_global_memory_monitor()
    monitor.object_tracker.track_object(obj)
    return obj


# Global memory monitor instance
_global_memory_monitor: Optional[MemoryMonitor] = None


def get_global_memory_monitor() -> MemoryMonitor:
    """Get the global memory monitor instance"""
    global _global_memory_monitor
    if _global_memory_monitor is None:
        _global_memory_monitor = MemoryMonitor()
    return _global_memory_monitor


def start_memory_monitoring():
    """Start global memory monitoring"""
    monitor = get_global_memory_monitor()
    monitor.start_monitoring()
    return monitor