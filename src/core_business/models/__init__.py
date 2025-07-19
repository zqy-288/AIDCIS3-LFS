"""
AIDCIS2 数据模型包
"""

from .hole_data import HoleData, HoleCollection, HoleStatus
from .status_manager import StatusManager

__all__ = ['HoleData', 'HoleCollection', 'HoleStatus', 'StatusManager']
