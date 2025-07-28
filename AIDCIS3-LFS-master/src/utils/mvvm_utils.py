"""
MVVM pattern utilities for MainWindow refactoring.

This module provides helper functions and utilities to support
the MVVM pattern implementation.
"""

from typing import Any, Dict, List, Optional, Callable, TypeVar, Generic
from functools import wraps
from dataclasses import dataclass, field
import logging
from PySide6.QtCore import QObject, Signal, QTimer

T = TypeVar('T')

logger = logging.getLogger(__name__)


class SignalThrottler(QObject):
    """
    Utility class to throttle signal emissions.
    
    Prevents excessive signal emissions that could cause performance issues
    in the UI update cycle.
    """
    
    throttled_signal = Signal(object)
    
    def __init__(self, delay_ms: int = 100):
        """
        Initialize the signal throttler.
        
        Args:
            delay_ms: Delay in milliseconds before emitting throttled signal
        """
        super().__init__()
        self.delay_ms = delay_ms
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._emit_throttled)
        self.pending_data = None
        
    def emit_throttled(self, data: Any) -> None:
        """
        Emit data through throttled signal.
        
        Args:
            data: Data to emit
        """
        self.pending_data = data
        if not self.timer.isActive():
            self.timer.start(self.delay_ms)
    
    def _emit_throttled(self) -> None:
        """Internal method to emit the throttled signal."""
        if self.pending_data is not None:
            self.throttled_signal.emit(self.pending_data)
            self.pending_data = None


@dataclass
class ViewModelState:
    """
    Utility class to capture and restore view model state.
    
    Useful for implementing undo/redo functionality or
    temporary state changes.
    """
    
    timestamp: float = field(default_factory=lambda: __import__('time').time())
    state_data: Dict[str, Any] = field(default_factory=dict)
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return {
            'timestamp': self.timestamp,
            'state_data': self.state_data,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ViewModelState':
        """Create state from dictionary."""
        return cls(
            timestamp=data.get('timestamp', 0),
            state_data=data.get('state_data', {}),
            description=data.get('description')
        )


class ViewModelValidator:
    """
    Utility class for validating view model data.
    
    Provides a framework for defining and executing validation rules
    on view model fields.
    """
    
    def __init__(self):
        """Initialize the validator."""
        self.rules: Dict[str, List[Callable]] = {}
        
    def add_rule(self, field_name: str, validator: Callable[[Any], bool], message: str) -> None:
        """
        Add a validation rule for a field.
        
        Args:
            field_name: Name of the field to validate
            validator: Function that returns True if valid
            message: Error message if validation fails
        """
        if field_name not in self.rules:
            self.rules[field_name] = []
        
        def rule_wrapper(value: Any) -> Optional[str]:
            if not validator(value):
                return message
            return None
            
        self.rules[field_name].append(rule_wrapper)
    
    def validate(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate data against all rules.
        
        Args:
            data: Dictionary of field names to values
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        for field_name, validators in self.rules.items():
            if field_name in data:
                value = data[field_name]
                for validator in validators:
                    error = validator(value)
                    if error:
                        errors.append(f"{field_name}: {error}")
        
        return errors


def validate_not_empty(value: Any) -> bool:
    """Validate that value is not empty."""
    if value is None:
        return False
    if isinstance(value, (str, list, dict)) and len(value) == 0:
        return False
    return True


def validate_positive_number(value: Any) -> bool:
    """Validate that value is a positive number."""
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False


def validate_in_range(min_val: float, max_val: float) -> Callable[[Any], bool]:
    """Create a validator for numeric range."""
    def validator(value: Any) -> bool:
        try:
            num_val = float(value)
            return min_val <= num_val <= max_val
        except (TypeError, ValueError):
            return False
    return validator


def validate_string_length(min_length: int = 0, max_length: int = 1000) -> Callable[[Any], bool]:
    """Create a validator for string length."""
    def validator(value: Any) -> bool:
        if not isinstance(value, str):
            return False
        return min_length <= len(value) <= max_length
    return validator


def safe_emit(signal: Signal, *args, **kwargs) -> bool:
    """
    Safely emit a signal with error handling.
    
    Args:
        signal: The signal to emit
        *args: Signal arguments
        **kwargs: Signal keyword arguments
        
    Returns:
        True if emission was successful, False otherwise
    """
    try:
        signal.emit(*args, **kwargs)
        return True
    except Exception as e:
        logger.error(f"Failed to emit signal: {e}")
        return False


def debounce(delay_ms: int):
    """
    Decorator to debounce function calls.
    
    Args:
        delay_ms: Delay in milliseconds before function execution
    """
    def decorator(func):
        timer = None
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal timer
            
            def execute():
                func(*args, **kwargs)
            
            if timer:
                timer.stop()
            
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(execute)
            timer.start(delay_ms)
            
        return wrapper
    return decorator


class PropertyBinder(QObject):
    """
    Utility class for binding properties between objects.
    
    Enables automatic synchronization of properties between
    view models and UI components.
    """
    
    def __init__(self):
        """Initialize the property binder."""
        super().__init__()
        self.bindings: List[Dict[str, Any]] = []
    
    def bind(
        self, 
        source: QObject, 
        source_property: str,
        target: QObject, 
        target_property: str,
        converter: Optional[Callable] = None
    ) -> None:
        """
        Create a property binding.
        
        Args:
            source: Source object
            source_property: Source property name
            target: Target object  
            target_property: Target property name
            converter: Optional value converter function
        """
        binding = {
            'source': source,
            'source_property': source_property,
            'target': target,
            'target_property': target_property,
            'converter': converter
        }
        self.bindings.append(binding)
        
        # Connect to source property changes
        signal_name = f"{source_property}Changed"
        if hasattr(source, signal_name):
            signal = getattr(source, signal_name)
            signal.connect(lambda: self._update_binding(binding))
    
    def _update_binding(self, binding: Dict[str, Any]) -> None:
        """Update a property binding."""
        try:
            source_value = getattr(binding['source'], binding['source_property'])
            
            if binding['converter']:
                target_value = binding['converter'](source_value)
            else:
                target_value = source_value
                
            setattr(binding['target'], binding['target_property'], target_value)
            
        except Exception as e:
            logger.error(f"Failed to update property binding: {e}")
    
    def unbind_all(self) -> None:
        """Remove all property bindings."""
        self.bindings.clear()


class ComponentRegistry:
    """
    Registry for managing component instances in the MVVM architecture.
    
    Provides a centralized way to register and retrieve components,
    useful for dependency injection and testing.
    """
    
    def __init__(self):
        """Initialize the component registry."""
        self._components: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
    
    def register(self, name: str, component: Any) -> None:
        """
        Register a component instance.
        
        Args:
            name: Component name
            component: Component instance
        """
        self._components[name] = component
    
    def register_factory(self, name: str, factory: Callable) -> None:
        """
        Register a component factory.
        
        Args:
            name: Component name
            factory: Factory function that creates the component
        """
        self._factories[name] = factory
    
    def get(self, name: str) -> Optional[Any]:
        """
        Get a component by name.
        
        Args:
            name: Component name
            
        Returns:
            Component instance or None if not found
        """
        if name in self._components:
            return self._components[name]
        
        if name in self._factories:
            component = self._factories[name]()
            self._components[name] = component
            return component
        
        return None
    
    def clear(self) -> None:
        """Clear all registered components and factories."""
        self._components.clear()
        self._factories.clear()


# Global component registry instance
component_registry = ComponentRegistry()