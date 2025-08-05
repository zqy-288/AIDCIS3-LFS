"""
Type checking and validation utilities for MainWindow refactoring.

This module provides type checking utilities and validation helpers
to ensure type safety throughout the MVVM architecture.
"""

from typing import Any, Dict, List, Optional, Union, Type, TypeVar, get_origin, get_args
import inspect
from dataclasses import is_dataclass, fields
from enum import Enum
import logging

T = TypeVar('T')

logger = logging.getLogger(__name__)


class TypeValidator:
    """
    Utility class for runtime type validation.
    
    Provides methods to validate that values match expected types,
    which is especially useful for validating data at component boundaries.
    """
    
    @staticmethod
    def is_valid_type(value: Any, expected_type: Type) -> bool:
        """
        Check if a value matches the expected type.
        
        Args:
            value: Value to check
            expected_type: Expected type
            
        Returns:
            True if value matches type, False otherwise
        """
        try:
            # Handle None values
            if value is None:
                return expected_type is type(None) or (
                    hasattr(expected_type, '__origin__') and 
                    type(None) in get_args(expected_type)
                )
            
            # Handle Union types (including Optional)
            origin = get_origin(expected_type)
            if origin is Union:
                return any(
                    TypeValidator.is_valid_type(value, arg) 
                    for arg in get_args(expected_type)
                )
            
            # Handle List types
            if origin is list:
                if not isinstance(value, list):
                    return False
                if get_args(expected_type):
                    element_type = get_args(expected_type)[0]
                    return all(
                        TypeValidator.is_valid_type(item, element_type) 
                        for item in value
                    )
                return True
            
            # Handle Dict types
            if origin is dict:
                if not isinstance(value, dict):
                    return False
                args = get_args(expected_type)
                if len(args) == 2:
                    key_type, value_type = args
                    return all(
                        TypeValidator.is_valid_type(k, key_type) and 
                        TypeValidator.is_valid_type(v, value_type)
                        for k, v in value.items()
                    )
                return True
            
            # Handle basic types
            return isinstance(value, expected_type)
            
        except Exception as e:
            logger.warning(f"Type validation error: {e}")
            return False
    
    @staticmethod
    def validate_dataclass_fields(instance: Any) -> List[str]:
        """
        Validate all fields of a dataclass instance.
        
        Args:
            instance: Dataclass instance to validate
            
        Returns:
            List of validation error messages
        """
        if not is_dataclass(instance):
            return ["Instance is not a dataclass"]
        
        errors = []
        for field in fields(instance):
            field_value = getattr(instance, field.name)
            if not TypeValidator.is_valid_type(field_value, field.type):
                errors.append(
                    f"Field '{field.name}' has invalid type. "
                    f"Expected {field.type}, got {type(field_value)}"
                )
        
        return errors
    
    @staticmethod
    def validate_function_signature(func: callable, args: tuple, kwargs: dict) -> List[str]:
        """
        Validate function call arguments against signature.
        
        Args:
            func: Function to validate
            args: Positional arguments
            kwargs: Keyword arguments
            
        Returns:
            List of validation error messages
        """
        try:
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            errors = []
            for param_name, param in sig.parameters.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if param.annotation != inspect.Parameter.empty:
                        if not TypeValidator.is_valid_type(value, param.annotation):
                            errors.append(
                                f"Parameter '{param_name}' has invalid type. "
                                f"Expected {param.annotation}, got {type(value)}"
                            )
            
            return errors
            
        except Exception as e:
            return [f"Signature validation error: {e}"]


def safe_cast(value: Any, target_type: Type[T], default: Optional[T] = None) -> Optional[T]:
    """
    Safely cast a value to target type with optional default.
    
    Args:
        value: Value to cast
        target_type: Target type to cast to
        default: Default value if cast fails
        
    Returns:
        Cast value or default if cast fails
    """
    try:
        if value is None:
            return default
        
        # Handle string to number conversions
        if target_type in (int, float) and isinstance(value, str):
            return target_type(value)
        
        # Handle number conversions
        if target_type == int and isinstance(value, float):
            return int(value)
        
        if target_type == float and isinstance(value, int):
            return float(value)
        
        # Handle string conversions
        if target_type == str:
            return str(value)
        
        # Handle bool conversions
        if target_type == bool:
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'yes', 'on')
            return bool(value)
        
        # Direct type check
        if isinstance(value, target_type):
            return value
        
        return default
        
    except Exception as e:
        logger.warning(f"Failed to cast {value} to {target_type}: {e}")
        return default


def ensure_type(value: Any, expected_type: Type[T], error_message: str = None) -> T:
    """
    Ensure a value is of the expected type, raise TypeError if not.
    
    Args:
        value: Value to check
        expected_type: Expected type
        error_message: Custom error message
        
    Returns:
        The value if type matches
        
    Raises:
        TypeError: If value doesn't match expected type
    """
    if not TypeValidator.is_valid_type(value, expected_type):
        if error_message is None:
            error_message = f"Expected {expected_type}, got {type(value)}"
        raise TypeError(error_message)
    
    return value


def get_type_name(obj: Any) -> str:
    """
    Get a human-readable type name for an object.
    
    Args:
        obj: Object to get type name for
        
    Returns:
        Human-readable type name
    """
    if obj is None:
        return "None"
    
    obj_type = type(obj)
    
    # Handle generic types
    if hasattr(obj_type, '__origin__'):
        origin = obj_type.__origin__
        args = getattr(obj_type, '__args__', ())
        if args:
            arg_names = [get_type_name(arg) for arg in args]
            return f"{origin.__name__}[{', '.join(arg_names)}]"
        return origin.__name__
    
    return obj_type.__name__


class EnumValidator:
    """Utility class for validating enum values."""
    
    @staticmethod
    def is_valid_enum_value(value: Any, enum_class: Type[Enum]) -> bool:
        """
        Check if value is valid for enum class.
        
        Args:
            value: Value to check
            enum_class: Enum class to validate against
            
        Returns:
            True if value is valid enum value
        """
        try:
            if isinstance(value, enum_class):
                return True
            
            # Try to create enum instance
            enum_class(value)
            return True
            
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def get_enum_values(enum_class: Type[Enum]) -> List[Any]:
        """
        Get all valid values for an enum class.
        
        Args:
            enum_class: Enum class
            
        Returns:
            List of valid enum values
        """
        return [item.value for item in enum_class]


class DataclassValidator:
    """Utility class for validating dataclass instances."""
    
    @staticmethod
    def validate_required_fields(instance: Any, required_fields: List[str]) -> List[str]:
        """
        Validate that required fields are not None or empty.
        
        Args:
            instance: Dataclass instance
            required_fields: List of required field names
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        for field_name in required_fields:
            if not hasattr(instance, field_name):
                errors.append(f"Missing required field: {field_name}")
                continue
            
            value = getattr(instance, field_name)
            if value is None:
                errors.append(f"Required field '{field_name}' cannot be None")
            elif isinstance(value, (str, list, dict)) and len(value) == 0:
                errors.append(f"Required field '{field_name}' cannot be empty")
        
        return errors
    
    @staticmethod
    def validate_field_constraints(
        instance: Any, 
        field_constraints: Dict[str, callable]
    ) -> List[str]:
        """
        Validate fields against custom constraint functions.
        
        Args:
            instance: Dataclass instance
            field_constraints: Dict of field names to constraint functions
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        for field_name, constraint in field_constraints.items():
            if not hasattr(instance, field_name):
                continue
            
            value = getattr(instance, field_name)
            try:
                if not constraint(value):
                    errors.append(f"Field '{field_name}' failed constraint validation")
            except Exception as e:
                errors.append(f"Constraint validation error for '{field_name}': {e}")
        
        return errors