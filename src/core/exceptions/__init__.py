"""
Exceptions package for MainWindow refactoring.

Contains custom exception classes for better error handling:
- main_exceptions: Main component exceptions
"""

from .main_exceptions import (
    MainWindowError,
    ViewControllerError,
    BusinessControllerError,
    ViewModelError,
    CoordinatorError
)

__all__ = [
    'MainWindowError',
    'ViewControllerError', 
    'BusinessControllerError',
    'ViewModelError',
    'CoordinatorError'
]