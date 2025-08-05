"""
Signal Optimizer for High-Performance MVVM
Implements efficient signal transmission with throttling and batching
"""

import time
import threading
from typing import Dict, Any, List, Callable, Optional
from collections import defaultdict, deque
from PySide6.QtCore import QObject, Signal, QTimer, pyqtSignal
from dataclasses import dataclass
from enum import Enum


class SignalPriority(Enum):
    """Signal priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class SignalMessage:
    """Signal message container"""
    signal_name: str
    args: tuple
    kwargs: dict
    priority: SignalPriority
    timestamp: float
    source_id: str


class SignalThrottler(QObject):
    """
    Signal throttling mechanism to prevent excessive signal emissions
    Groups related signals and emits them at controlled intervals
    """
    
    # Throttled signal emission
    throttled_signal = Signal(object)  # Emits the actual signal data
    
    def __init__(self, throttle_interval: int = 50, max_queue_size: int = 1000):
        super().__init__()
        self.throttle_interval = throttle_interval  # milliseconds
        self.max_queue_size = max_queue_size
        
        # Signal queues by priority
        self.signal_queues = {
            SignalPriority.CRITICAL: deque(),
            SignalPriority.HIGH: deque(),
            SignalPriority.NORMAL: deque(),
            SignalPriority.LOW: deque()
        }
        
        # Throttle timers
        self.throttle_timer = QTimer()
        self.throttle_timer.timeout.connect(self._process_signal_queue)
        self.throttle_timer.start(self.throttle_interval)
        
        # Signal deduplication
        self.last_signals = {}  # signal_name -> (args, kwargs, timestamp)
        self.dedup_window = 0.1  # 100ms deduplication window
        
        # Statistics
        self.stats = {
            "signals_queued": 0,
            "signals_emitted": 0,
            "signals_deduplicated": 0,
            "signals_dropped": 0
        }
        
    def emit_throttled(self, signal_name: str, *args, priority: SignalPriority = SignalPriority.NORMAL, 
                      source_id: str = "unknown", **kwargs):
        """
        Emit a signal through the throttling mechanism
        
        Args:
            signal_name: Name/identifier of the signal
            *args: Signal arguments
            priority: Signal priority level
            source_id: Identifier of the signal source
            **kwargs: Signal keyword arguments
        """
        current_time = time.time()
        
        # Check for deduplication
        dedup_key = f"{signal_name}_{source_id}"
        if self._should_deduplicate(dedup_key, args, kwargs, current_time):
            self.stats["signals_deduplicated"] += 1
            return
            
        # Create signal message
        message = SignalMessage(
            signal_name=signal_name,
            args=args,
            kwargs=kwargs,
            priority=priority,
            timestamp=current_time,
            source_id=source_id
        )
        
        # Add to appropriate queue
        queue = self.signal_queues[priority]
        
        # Check queue size limit
        if len(queue) >= self.max_queue_size // 4:  # 25% per priority level
            # Drop oldest low-priority signals if queue is full
            if priority == SignalPriority.LOW:
                queue.popleft()
                self.stats["signals_dropped"] += 1
            elif len(queue) >= self.max_queue_size // 2:
                queue.popleft()
                self.stats["signals_dropped"] += 1
                
        queue.append(message)
        self.stats["signals_queued"] += 1
        
        # Update last signal for deduplication
        self.last_signals[dedup_key] = (args, kwargs, current_time)
        
    def _should_deduplicate(self, dedup_key: str, args: tuple, kwargs: dict, current_time: float) -> bool:
        """Check if signal should be deduplicated"""
        if dedup_key not in self.last_signals:
            return False
            
        last_args, last_kwargs, last_time = self.last_signals[dedup_key]
        
        # Check time window
        if current_time - last_time > self.dedup_window:
            return False
            
        # Check if signal content is identical
        return args == last_args and kwargs == last_kwargs
        
    def _process_signal_queue(self):
        """Process queued signals in priority order"""
        signals_to_emit = []
        
        # Process by priority (CRITICAL -> HIGH -> NORMAL -> LOW)
        for priority in [SignalPriority.CRITICAL, SignalPriority.HIGH, 
                        SignalPriority.NORMAL, SignalPriority.LOW]:
            queue = self.signal_queues[priority]
            
            # Emit up to certain number of signals per cycle based on priority
            max_signals = {
                SignalPriority.CRITICAL: 10,
                SignalPriority.HIGH: 5,
                SignalPriority.NORMAL: 3,
                SignalPriority.LOW: 1
            }[priority]
            
            for _ in range(min(len(queue), max_signals)):
                if queue:
                    signals_to_emit.append(queue.popleft())
                    
        # Emit collected signals
        for message in signals_to_emit:
            self.throttled_signal.emit(message)
            self.stats["signals_emitted"] += 1
            
    def get_statistics(self) -> Dict[str, Any]:
        """Get throttling statistics"""
        total_queued = sum(len(queue) for queue in self.signal_queues.values())
        return {
            **self.stats,
            "current_queue_size": total_queued,
            "queue_sizes": {priority.name: len(queue) for priority, queue in self.signal_queues.items()}
        }
        
    def clear_queues(self):
        """Clear all signal queues"""
        for queue in self.signal_queues.values():
            queue.clear()
        self.last_signals.clear()


class BatchSignalProcessor(QObject):
    """
    Batch signal processor for efficient handling of multiple related signals
    """
    
    batch_processed = Signal(list)  # Emits list of processed signals
    
    def __init__(self, batch_size: int = 10, batch_timeout: int = 100):
        super().__init__()
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout  # milliseconds
        
        self.current_batch = []
        self.batch_timer = QTimer()
        self.batch_timer.timeout.connect(self._flush_batch)
        self.batch_timer.setSingleShot(True)
        
    def add_to_batch(self, signal_data: Any):
        """Add signal data to current batch"""
        self.current_batch.append(signal_data)
        
        # Start/restart timer
        self.batch_timer.start(self.batch_timeout)
        
        # Check if batch is full
        if len(self.current_batch) >= self.batch_size:
            self._flush_batch()
            
    def _flush_batch(self):
        """Flush current batch"""
        if self.current_batch:
            self.batch_processed.emit(self.current_batch.copy())
            self.current_batch.clear()
            
        self.batch_timer.stop()


class PerformantSignalManager(QObject):
    """
    High-performance signal manager that coordinates throttling and batching
    """
    
    def __init__(self):
        super().__init__()
        
        # Initialize throttler and batch processor
        self.throttler = SignalThrottler(throttle_interval=50, max_queue_size=2000)
        self.batch_processor = BatchSignalProcessor(batch_size=20, batch_timeout=50)
        
        # Connect signals
        self.throttler.throttled_signal.connect(self._handle_throttled_signal)
        self.batch_processor.batch_processed.connect(self._handle_batch_processed)
        
        # Performance tracking
        self.performance_stats = {
            "total_signals_processed": 0,
            "average_processing_time": 0.0,
            "peak_processing_time": 0.0,
            "signal_types": defaultdict(int)
        }
        
    def emit_signal(self, signal_name: str, *args, 
                   priority: SignalPriority = SignalPriority.NORMAL,
                   source_id: str = "unknown",
                   use_batching: bool = False, **kwargs):
        """
        Emit a signal through the performance-optimized pipeline
        
        Args:
            signal_name: Signal identifier
            *args: Signal arguments
            priority: Signal priority
            source_id: Source identifier
            use_batching: Whether to use batch processing
            **kwargs: Signal keyword arguments
        """
        start_time = time.time()
        
        try:
            if use_batching and priority in [SignalPriority.LOW, SignalPriority.NORMAL]:
                # Use batch processing for non-critical signals
                signal_data = {
                    "signal_name": signal_name,
                    "args": args,
                    "kwargs": kwargs,
                    "source_id": source_id,
                    "timestamp": start_time
                }
                self.batch_processor.add_to_batch(signal_data)
            else:
                # Use throttling for individual signals
                self.throttler.emit_throttled(
                    signal_name, *args,
                    priority=priority,
                    source_id=source_id,
                    **kwargs
                )
                
        finally:
            # Update performance statistics
            processing_time = time.time() - start_time
            self._update_performance_stats(signal_name, processing_time)
            
    def _handle_throttled_signal(self, message: SignalMessage):
        """Handle individual throttled signal"""
        # This would connect to actual signal handlers
        pass
        
    def _handle_batch_processed(self, signal_batch: List[Dict[str, Any]]):
        """Handle batch of processed signals"""
        # Process batch efficiently
        for signal_data in signal_batch:
            # This would connect to actual signal handlers
            pass
            
    def _update_performance_stats(self, signal_name: str, processing_time: float):
        """Update performance statistics"""
        self.performance_stats["total_signals_processed"] += 1
        self.performance_stats["signal_types"][signal_name] += 1
        
        # Update average processing time
        total = self.performance_stats["total_signals_processed"]
        current_avg = self.performance_stats["average_processing_time"]
        new_avg = (current_avg * (total - 1) + processing_time) / total
        self.performance_stats["average_processing_time"] = new_avg
        
        # Update peak processing time
        if processing_time > self.performance_stats["peak_processing_time"]:
            self.performance_stats["peak_processing_time"] = processing_time
            
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        throttler_stats = self.throttler.get_statistics()
        
        return {
            "signal_manager_stats": self.performance_stats.copy(),
            "throttler_stats": throttler_stats,
            "current_batch_size": len(self.batch_processor.current_batch),
            "efficiency_ratio": (
                throttler_stats["signals_emitted"] / max(throttler_stats["signals_queued"], 1)
            ),
            "deduplication_ratio": (
                throttler_stats["signals_deduplicated"] / max(throttler_stats["signals_queued"], 1)
            )
        }
        
    def optimize_settings(self, target_latency: float = 0.1):
        """Automatically optimize settings based on current performance"""
        stats = self.get_performance_report()
        
        # Adjust throttle interval based on queue sizes
        total_queue_size = sum(stats["throttler_stats"]["queue_sizes"].values())
        
        if total_queue_size > 100:
            # Reduce throttle interval to process signals faster
            new_interval = max(25, self.throttler.throttle_interval - 5)
            self.throttler.throttle_timer.setInterval(new_interval)
        elif total_queue_size < 10:
            # Increase throttle interval to reduce CPU usage
            new_interval = min(100, self.throttler.throttle_interval + 5)
            self.throttler.throttle_timer.setInterval(new_interval)
            
        # Adjust batch size based on processing time
        avg_time = stats["signal_manager_stats"]["average_processing_time"]
        if avg_time > target_latency:
            # Reduce batch size
            self.batch_processor.batch_size = max(5, self.batch_processor.batch_size - 2)
        elif avg_time < target_latency * 0.5:
            # Increase batch size
            self.batch_processor.batch_size = min(50, self.batch_processor.batch_size + 2)


# Singleton instance for global use
_global_signal_manager = None

def get_signal_manager() -> PerformantSignalManager:
    """Get global signal manager instance"""
    global _global_signal_manager
    if _global_signal_manager is None:
        _global_signal_manager = PerformantSignalManager()
    return _global_signal_manager