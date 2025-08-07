"""
数据访问层模块
提供配置管理功能
"""

from .config_manager import config_manager, get_config

__all__ = [
    'config_manager',
    'get_config'
]