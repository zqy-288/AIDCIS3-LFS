"""
Core领域层统一模块
提供领域模型、仓储接口和领域服务
"""

from .models.detection_batch import (
    DetectionBatch,
    BatchStatus,
    DetectionType,
    DetectionProgress,
    DetectionState
)
from .repositories.batch_repository import IBatchRepository
from .services.batch_service import BatchService

__all__ = [
    # 领域模型
    'DetectionBatch',
    'BatchStatus', 
    'DetectionType',
    'DetectionProgress',
    'DetectionState',
    
    # 仓储接口
    'IBatchRepository',
    
    # 领域服务
    'BatchService'
]