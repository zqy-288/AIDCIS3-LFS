"""
Enums for view models
"""

from enum import Enum


class DetectionState(Enum):
    """检测状态枚举"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"


class SimulationState(Enum):
    """模拟状态枚举"""
    IDLE = "idle"
    RUNNING = "running"
    STOPPED = "stopped"


class ViewMode(Enum):
    """视图模式枚举"""
    MACRO = "macro"  # 宏观区域视图
    MICRO = "micro"  # 微观管孔视图
    PANORAMA = "panorama"  # 全景视图


class MessageLevel(Enum):
    """消息级别枚举"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"