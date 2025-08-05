"""
坐标管理服务模块
负责所有坐标转换、旋转、扇形分配的统一管理
"""

from .coordinate_manager import (
    UnifiedCoordinateManager,
    CoordinateSystem,
    CoordinateConfig,
    SectorInfo,
    SectorQuadrant,
    SectorProgress
)

__all__ = [
    'UnifiedCoordinateManager',
    'CoordinateSystem',
    'CoordinateConfig',
    'SectorInfo',
    'SectorQuadrant',
    'SectorProgress'
]