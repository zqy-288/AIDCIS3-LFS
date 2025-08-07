"""
领域模型统一模块
"""

from .detection_batch import (
    DetectionBatch,
    BatchStatus,
    DetectionType,
    DetectionProgress,
    DetectionState
)

__all__ = [
    'DetectionBatch',
    'BatchStatus',
    'DetectionType', 
    'DetectionProgress',
    'DetectionState'
]