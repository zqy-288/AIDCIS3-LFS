"""
Custom exception classes for MainWindow refactoring.

This module defines specific exception types for better error handling
and debugging in the MVVM architecture.
"""

from typing import Optional, Dict, Any


class MainWindowError(Exception):
    """
    Base exception class for all MainWindow-related errors.
    
    This is the root exception class that all other MainWindow exceptions
    inherit from, allowing for unified error handling.
    """
    
    def __init__(
        self, 
        message: str, 
        component: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the MainWindow error.
        
        Args:
            message: Human-readable error message
            component: Name of the component where error occurred
            context: Additional context information
        """
        super().__init__(message)
        self.component = component
        self.context = context or {}
        
    def __str__(self) -> str:
        """Return formatted error message."""
        if self.component:
            return f"[{self.component}] {super().__str__()}"
        return super().__str__()


class ViewControllerError(MainWindowError):
    """
    Exception for UI layer (View Controller) errors.
    
    Raised when errors occur in the MainViewController or UI components,
    such as widget creation failures, layout issues, or UI state problems.
    """
    
    def __init__(
        self, 
        message: str, 
        widget_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the view controller error.
        
        Args:
            message: Human-readable error message
            widget_name: Name of the widget where error occurred
            context: Additional context information
        """
        super().__init__(message, "ViewController", context)
        self.widget_name = widget_name


class BusinessControllerError(MainWindowError):
    """
    Exception for business logic layer errors.
    
    Raised when errors occur in the MainBusinessController or business services,
    such as service initialization failures, business rule violations,
    or data processing errors.
    """
    
    def __init__(
        self, 
        message: str, 
        service_name: Optional[str] = None,
        operation: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the business controller error.
        
        Args:
            message: Human-readable error message
            service_name: Name of the service where error occurred
            operation: Name of the operation that failed
            context: Additional context information
        """
        super().__init__(message, "BusinessController", context)
        self.service_name = service_name
        self.operation = operation


class ViewModelError(MainWindowError):
    """
    Exception for view model layer errors.
    
    Raised when errors occur in the MainViewModel or view model management,
    such as data validation failures, state inconsistencies,
    or serialization errors.
    """
    
    def __init__(
        self, 
        message: str, 
        field_name: Optional[str] = None,
        validation_errors: Optional[list] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the view model error.
        
        Args:
            message: Human-readable error message
            field_name: Name of the field where error occurred
            validation_errors: List of validation error messages
            context: Additional context information
        """
        super().__init__(message, "ViewModel", context)
        self.field_name = field_name
        self.validation_errors = validation_errors or []


class CoordinatorError(MainWindowError):
    """
    Exception for coordinator layer errors.
    
    Raised when errors occur in the MainWindowCoordinator,
    such as component communication failures, lifecycle management issues,
    or dependency injection problems.
    """
    
    def __init__(
        self, 
        message: str, 
        coordination_phase: Optional[str] = None,
        failed_components: Optional[list] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the coordinator error.
        
        Args:
            message: Human-readable error message
            coordination_phase: Phase of coordination where error occurred
            failed_components: List of components that failed
            context: Additional context information
        """
        super().__init__(message, "Coordinator", context)
        self.coordination_phase = coordination_phase
        self.failed_components = failed_components or []


class ServiceInitializationError(BusinessControllerError):
    """
    Exception for service initialization failures.
    
    Raised when a business service fails to initialize properly,
    such as missing dependencies, configuration errors, or resource unavailability.
    """
    
    def __init__(
        self, 
        service_name: str, 
        message: str,
        dependencies: Optional[list] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the service initialization error.
        
        Args:
            service_name: Name of the service that failed to initialize
            message: Human-readable error message
            dependencies: List of missing or failed dependencies
            context: Additional context information
        """
        super().__init__(
            message, 
            service_name, 
            "initialization", 
            context
        )
        self.dependencies = dependencies or []


class ComponentCommunicationError(CoordinatorError):
    """
    Exception for component communication failures.
    
    Raised when components fail to communicate properly,
    such as signal connection failures, message passing errors,
    or component interface mismatches.
    """
    
    def __init__(
        self, 
        message: str, 
        source_component: Optional[str] = None,
        target_component: Optional[str] = None,
        signal_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the component communication error.
        
        Args:
            message: Human-readable error message
            source_component: Component that sent the message/signal
            target_component: Component that should receive the message/signal
            signal_name: Name of the signal that failed
            context: Additional context information
        """
        super().__init__(message, "communication", None, context)
        self.source_component = source_component
        self.target_component = target_component
        self.signal_name = signal_name


class DataValidationError(ViewModelError):
    """
    Exception for data validation failures.
    
    Raised when view model data fails validation,
    such as invalid field values, missing required data,
    or business rule violations.
    """
    
    def __init__(
        self, 
        message: str, 
        field_name: str,
        field_value: Any = None,
        validation_rule: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the data validation error.
        
        Args:
            message: Human-readable error message
            field_name: Name of the field that failed validation
            field_value: Value that failed validation
            validation_rule: Name of the validation rule that failed
            context: Additional context information
        """
        super().__init__(message, field_name, [message], context)
        self.field_value = field_value
        self.validation_rule = validation_rule