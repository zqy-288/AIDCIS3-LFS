"""
UI layer package for MainWindow refactoring.

This package contains all UI-related components following the MVVM pattern:
- main_view_controller: Main UI controller
- components: UI widget components  
- view_models: Data models for UI binding
"""

# Import view models
from .view_models.main_view_model import MainViewModel
from .view_models.view_model_manager import MainViewModelManager

__all__ = ['MainViewModel', 'MainViewModelManager']