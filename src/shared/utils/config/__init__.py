"""
配置管理工具
提供路径配置、系统配置等统一管理功能
"""

from .path_config import PathConfig, PathType

__all__ = [
    'PathConfig',
    'PathType'
]