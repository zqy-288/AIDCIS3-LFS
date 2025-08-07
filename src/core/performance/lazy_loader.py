"""
Lazy Loading System for High-Performance Component Initialization
Implements lazy initialization patterns to reduce startup time and memory usage
"""

import time
import threading
import weakref
from typing import Dict, Any, Callable, Optional, Type, TypeVar, Generic, Set
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from PySide6.QtCore import QObject, Signal, QTimer


T = TypeVar('T')


class LoadPriority(Enum):
    """Component loading priority levels"""
    CRITICAL = 1    # Must load immediately (core UI components)
    HIGH = 2        # Load on first access (frequently used components)
    NORMAL = 3      # Load on demand (occasionally used components)
    LOW = 4         # Load in background (rarely used components)
    DEFERRED = 5    # Load only when explicitly requested


@dataclass
class ComponentMetadata:
    """Metadata for a lazy-loaded component"""
    name: str
    factory: Callable[[], Any]
    priority: LoadPriority
    dependencies: Set[str] = None
    max_instances: int = 1
    auto_cleanup: bool = True
    load_timeout: float = 30.0  # seconds
    created_at: Optional[float] = None
    last_accessed: Optional[float] = None
    access_count: int = 0


class LazyProxy(Generic[T]):
    """
    Proxy object that lazily loads the actual component when accessed
    """
    
    def __init__(self, loader: 'LazyComponentLoader', component_name: str):
        self._loader = loader
        self._component_name = component_name
        self._loaded_instance: Optional[T] = None
        self._loading = False
        self._loading_event = threading.Event()
        
    def __getattr__(self, name: str) -> Any:
        """Intercept attribute access and load component if necessary"""
        instance = self._get_or_load_instance()
        return getattr(instance, name)
        
    def __call__(self, *args, **kwargs):
        """Make proxy callable if the wrapped object is callable"""
        instance = self._get_or_load_instance()
        return instance(*args, **kwargs)
        
    def _get_or_load_instance(self) -> T:
        """Get the loaded instance, loading it if necessary"""
        if self._loaded_instance is not None:
            self._loader._update_access_time(self._component_name)
            return self._loaded_instance
            
        # Handle concurrent access
        if self._loading:
            self._loading_event.wait(timeout=30.0)
            if self._loaded_instance is not None:
                return self._loaded_instance
            raise RuntimeError(f"Failed to load component {self._component_name} within timeout")
            
        try:
            self._loading = True
            self._loaded_instance = self._loader._load_component_now(self._component_name)
            self._loading_event.set()
            return self._loaded_instance
        finally:
            self._loading = False
            
    def is_loaded(self) -> bool:
        """Check if the component has been loaded"""
        return self._loaded_instance is not None
        
    def unload(self):
        """Unload the component to free memory"""
        if self._loaded_instance is not None:
            self._loader._unload_component(self._component_name)
            self._loaded_instance = None
            self._loading_event.clear()


class LazyComponentLoader(QObject):
    """
    Central lazy loading manager that coordinates component initialization
    """
    
    # Signals for monitoring loading progress
    component_loading = Signal(str)  # component_name
    component_loaded = Signal(str, float)  # component_name, load_time
    component_unloaded = Signal(str)  # component_name
    background_loading_progress = Signal(int, int)  # current, total
    
    def __init__(self):
        super().__init__()
        
        # Component registry
        self._components: Dict[str, ComponentMetadata] = {}
        self._loaded_instances: Dict[str, Any] = {}
        self._instance_refs: Dict[str, weakref.ref] = {}
        
        # Loading state
        self._loading_lock = threading.RLock()
        self._background_loader: Optional[QTimer] = None
        self._background_queue: List[str] = []
        
        # Performance tracking
        self._load_times: Dict[str, float] = {}
        self._startup_time = time.time()
        
        # Statistics
        self._stats = {
            "total_registered": 0,
            "total_loaded": 0,
            "total_unloaded": 0,
            "background_loads": 0,
            "average_load_time": 0.0,
            "memory_saved_mb": 0.0
        }
        
        # Initialize background loader
        self._init_background_loader()
        
    def register_component(self, name: str, factory: Callable[[], T], 
                          priority: LoadPriority = LoadPriority.NORMAL,
                          dependencies: Set[str] = None,
                          max_instances: int = 1,
                          auto_cleanup: bool = True) -> LazyProxy[T]:
        """
        Register a component for lazy loading
        
        Args:
            name: Unique component name
            factory: Function that creates the component
            priority: Loading priority
            dependencies: Set of component names this depends on
            max_instances: Maximum number of instances to keep
            auto_cleanup: Whether to auto-cleanup unused instances
            
        Returns:
            LazyProxy that will load the component on first access
        """
        if name in self._components:
            raise ValueError(f"Component {name} is already registered")
            
        metadata = ComponentMetadata(
            name=name,
            factory=factory,
            priority=priority,
            dependencies=dependencies or set(),
            max_instances=max_instances,
            auto_cleanup=auto_cleanup
        )
        
        self._components[name] = metadata
        self._stats["total_registered"] += 1
        
        # Add to background loading queue if appropriate priority
        if priority in [LoadPriority.HIGH, LoadPriority.NORMAL]:
            self._background_queue.append(name)
            
        return LazyProxy[T](self, name)
        
    def load_component(self, name: str, force_reload: bool = False) -> Any:
        """
        Explicitly load a component
        
        Args:
            name: Component name
            force_reload: Force reload even if already loaded
            
        Returns:
            Loaded component instance
        """
        if name not in self._components:
            raise ValueError(f"Component {name} is not registered")
            
        if not force_reload and name in self._loaded_instances:
            self._update_access_time(name)
            return self._loaded_instances[name]
            
        return self._load_component_now(name)
        
    def _load_component_now(self, name: str) -> Any:
        """Internal method to load a component immediately"""
        with self._loading_lock:
            metadata = self._components[name]
            
            # Check dependencies
            self._ensure_dependencies_loaded(metadata.dependencies)
            
            # Emit loading signal
            self.component_loading.emit(name)
            
            start_time = time.time()
            try:
                # Create instance
                instance = metadata.factory()
                load_time = time.time() - start_time
                
                # Store instance
                self._loaded_instances[name] = instance
                self._load_times[name] = load_time
                
                # Update metadata
                metadata.created_at = start_time
                metadata.last_accessed = time.time()
                metadata.access_count = 1
                
                # Create weak reference for cleanup tracking
                if metadata.auto_cleanup:
                    self._instance_refs[name] = weakref.ref(
                        instance, 
                        lambda ref: self._on_instance_garbage_collected(name)
                    )
                
                # Update statistics
                self._stats["total_loaded"] += 1
                self._update_average_load_time(load_time)
                
                # Emit loaded signal
                self.component_loaded.emit(name, load_time)
                
                return instance
                
            except Exception as e:
                load_time = time.time() - start_time
                self.component_loaded.emit(name, load_time)  # Still emit for monitoring
                raise RuntimeError(f"Failed to load component {name}: {e}")
                
    def _ensure_dependencies_loaded(self, dependencies: Set[str]):
        """Ensure all dependencies are loaded"""
        for dep_name in dependencies:
            if dep_name not in self._loaded_instances:
                self._load_component_now(dep_name)
                
    def _update_access_time(self, name: str):
        """Update access time and count for a component"""
        if name in self._components:
            metadata = self._components[name]
            metadata.last_accessed = time.time()
            metadata.access_count += 1
            
    def unload_component(self, name: str):
        """Explicitly unload a component"""
        self._unload_component(name)
        
    def _unload_component(self, name: str):
        """Internal method to unload a component"""
        with self._loading_lock:
            if name in self._loaded_instances:
                instance = self._loaded_instances[name]
                
                # Call cleanup method if available
                if hasattr(instance, 'cleanup'):
                    try:
                        instance.cleanup()
                    except Exception as e:
                        print(f"Error during cleanup of {name}: {e}")
                        
                # Remove from loaded instances
                del self._loaded_instances[name]
                if name in self._instance_refs:
                    del self._instance_refs[name]
                    
                self._stats["total_unloaded"] += 1
                self.component_unloaded.emit(name)
                
    def _on_instance_garbage_collected(self, name: str):
        """Called when an instance is garbage collected"""
        with self._loading_lock:
            if name in self._loaded_instances:
                del self._loaded_instances[name]
                self._stats["total_unloaded"] += 1
                
    def _init_background_loader(self):
        """Initialize background loading timer"""
        self._background_loader = QTimer()
        self._background_loader.timeout.connect(self._process_background_queue)
        self._background_loader.start(100)  # Process every 100ms
        
    def _process_background_queue(self):
        """Process background loading queue"""
        if not self._background_queue:
            return
            
        # Load one component per timer cycle to avoid blocking
        name = self._background_queue.pop(0)
        
        # Only load if not already loaded and appropriate priority
        if (name not in self._loaded_instances and 
            name in self._components and
            self._components[name].priority in [LoadPriority.HIGH, LoadPriority.NORMAL]):
            
            try:
                self._load_component_now(name)
                self._stats["background_loads"] += 1
            except Exception as e:
                print(f"Background loading failed for {name}: {e}")
                
        # Emit progress
        total_to_load = len([c for c in self._components.values() 
                           if c.priority in [LoadPriority.HIGH, LoadPriority.NORMAL]])
        current_loaded = len(self._loaded_instances)
        self.background_loading_progress.emit(current_loaded, total_to_load)
        
    def preload_critical_components(self):
        """Preload all critical priority components"""
        critical_components = [
            name for name, metadata in self._components.items()
            if metadata.priority == LoadPriority.CRITICAL
        ]
        
        for name in critical_components:
            if name not in self._loaded_instances:
                self._load_component_now(name)
                
    def cleanup_unused_components(self, max_idle_time: float = 300.0):
        """
        Cleanup components that haven't been accessed recently
        
        Args:
            max_idle_time: Maximum idle time in seconds before cleanup
        """
        current_time = time.time()
        to_unload = []
        
        for name, metadata in self._components.items():
            if (name in self._loaded_instances and 
                metadata.auto_cleanup and
                metadata.last_accessed and
                current_time - metadata.last_accessed > max_idle_time):
                to_unload.append(name)
                
        for name in to_unload:
            self._unload_component(name)
            
    def get_loading_statistics(self) -> Dict[str, Any]:
        """Get comprehensive loading statistics"""
        current_time = time.time()
        
        component_stats = {}
        for name, metadata in self._components.items():
            is_loaded = name in self._loaded_instances
            component_stats[name] = {
                "priority": metadata.priority.name,
                "loaded": is_loaded,
                "access_count": metadata.access_count,
                "last_accessed": metadata.last_accessed,
                "load_time": self._load_times.get(name, 0.0),
                "idle_time": (current_time - metadata.last_accessed) if metadata.last_accessed else None
            }
            
        total_time_since_startup = current_time - self._startup_time
        
        return {
            **self._stats,
            "startup_time_seconds": total_time_since_startup,
            "components_loaded_percent": (
                self._stats["total_loaded"] / max(self._stats["total_registered"], 1) * 100
            ),
            "background_queue_size": len(self._background_queue),
            "component_details": component_stats,
            "memory_efficiency": self._calculate_memory_efficiency()
        }
        
    def _update_average_load_time(self, new_load_time: float):
        """Update average load time statistic"""
        total_loads = self._stats["total_loaded"]
        current_avg = self._stats["average_load_time"]
        
        if total_loads == 1:
            self._stats["average_load_time"] = new_load_time
        else:
            new_avg = (current_avg * (total_loads - 1) + new_load_time) / total_loads
            self._stats["average_load_time"] = new_avg
            
    def _calculate_memory_efficiency(self) -> float:
        """Calculate memory efficiency score"""
        if self._stats["total_registered"] == 0:
            return 100.0
            
        # Efficiency based on load ratio and cleanup ratio
        load_ratio = self._stats["total_loaded"] / self._stats["total_registered"]
        cleanup_ratio = self._stats["total_unloaded"] / max(self._stats["total_loaded"], 1)
        
        # Lower load ratio and higher cleanup ratio = better efficiency
        efficiency = (1 - load_ratio) * 50 + cleanup_ratio * 50
        return min(100.0, max(0.0, efficiency))
        
    def optimize_loading_strategy(self):
        """Automatically optimize loading strategy based on usage patterns"""
        stats = self.get_loading_statistics()
        
        # Promote frequently accessed low-priority components
        for name, component_stats in stats["component_details"].items():
            if (component_stats["access_count"] > 10 and 
                self._components[name].priority == LoadPriority.LOW):
                self._components[name].priority = LoadPriority.NORMAL
                
        # Demote rarely accessed high-priority components
        for name, component_stats in stats["component_details"].items():
            if (component_stats["access_count"] < 2 and 
                component_stats.get("idle_time", 0) > 600 and  # 10 minutes
                self._components[name].priority == LoadPriority.HIGH):
                self._components[name].priority = LoadPriority.NORMAL


def lazy_component(name: str, priority: LoadPriority = LoadPriority.NORMAL,
                  dependencies: Set[str] = None):
    """
    Decorator for creating lazy-loaded components
    
    Args:
        name: Component name
        priority: Loading priority
        dependencies: Component dependencies
    """
    def decorator(factory_func: Callable[[], T]) -> LazyProxy[T]:
        loader = get_global_lazy_loader()
        return loader.register_component(
            name=name,
            factory=factory_func,
            priority=priority,
            dependencies=dependencies
        )
    return decorator


# Global lazy loader instance
_global_lazy_loader: Optional[LazyComponentLoader] = None


def get_global_lazy_loader() -> LazyComponentLoader:
    """Get the global lazy loader instance"""
    global _global_lazy_loader
    if _global_lazy_loader is None:
        _global_lazy_loader = LazyComponentLoader()
    return _global_lazy_loader


def initialize_lazy_loading_system():
    """Initialize the global lazy loading system"""
    global _global_lazy_loader
    if _global_lazy_loader is None:
        _global_lazy_loader = LazyComponentLoader()
        
        # Preload critical components
        _global_lazy_loader.preload_critical_components()
        
    return _global_lazy_loader