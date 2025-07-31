"""
兼容性模块 - 重新导出主异常类
为了兼容那些期望从src.pages.exceptions.main_exceptions导入的代码
"""

# 从真正的异常模块导入
from src.exceptions.main_exceptions import (
    DataValidationError,
    ViewModelError, 
    BusinessControllerError,
    ViewControllerError,
    CoordinatorError
)

# 重新导出，保持兼容性
__all__ = [
    'DataValidationError',
    'ViewModelError',
    'BusinessControllerError', 
    'ViewControllerError',
    'CoordinatorError'
]