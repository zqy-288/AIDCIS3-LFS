"""
共享数据模型
"""

from .hole_data import HoleData, HoleStatus, HoleCollection, convert_hole_id

__all__ = [
    'HoleData', 
    'HoleStatus', 
    'HoleCollection',
    'convert_hole_id'
]