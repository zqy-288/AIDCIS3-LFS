"""
Interfaces package for MainWindow refactoring.

Contains all interface definitions for the MVVM pattern:
- main_interfaces: Core interfaces for main components
"""

from .main_interfaces import (
    IMainViewController,
    IMainBusinessController, 
    IMainViewModel,
    IMainWindowCoordinator
)

__all__ = [
    'IMainViewController',
    'IMainBusinessController',
    'IMainViewModel', 
    'IMainWindowCoordinator'
]