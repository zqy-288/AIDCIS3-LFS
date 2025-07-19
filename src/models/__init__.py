"""
数据模型包
包含应用程序的核心数据模型和相关常量定义
"""

from .event_types import EventTypes
from .detection_state import DetectionState, DetectionStateManager
from .application_model import ApplicationModel

__all__ = [
    'EventTypes',
    'DetectionState',
    'DetectionStateManager',
    'ApplicationModel'
]