"""
View models package.

Contains data models for UI binding in MVVM pattern:
- main_view_model: Main view model data class
- view_model_manager: ViewModel lifecycle management
"""

from .main_view_model import MainViewModel
from .view_model_manager import MainViewModelManager

__all__ = ['MainViewModel', 'MainViewModelManager']