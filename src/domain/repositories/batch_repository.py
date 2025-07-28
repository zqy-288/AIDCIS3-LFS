"""
批次仓储接口定义
定义批次数据访问的抽象接口
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.domain.models.detection_batch import DetectionBatch


class IBatchRepository(ABC):
    """批次仓储接口"""
    
    @abstractmethod
    def save(self, batch: DetectionBatch) -> bool:
        """保存批次"""
        pass
    
    @abstractmethod
    def find_by_id(self, batch_id: str) -> Optional[DetectionBatch]:
        """根据ID查找批次"""
        pass
    
    @abstractmethod
    def find_by_product(self, product_id: int, detection_type: str = None) -> List[DetectionBatch]:
        """根据产品查找批次"""
        pass
    
    @abstractmethod
    def find_resumable(self, product_id: int, detection_type: str) -> Optional[DetectionBatch]:
        """查找可恢复的批次"""
        pass
    
    @abstractmethod
    def get_next_detection_number(self, product_id: int) -> int:
        """获取下一个检测序号"""
        pass
    
    @abstractmethod
    def delete(self, batch_id: str) -> bool:
        """删除批次"""
        pass
    
    @abstractmethod
    def update_progress(self, batch_id: str, progress: Dict[str, Any]) -> bool:
        """更新进度"""
        pass
    
    @abstractmethod
    def save_state(self, batch_id: str, state: Dict[str, Any]) -> bool:
        """保存状态到文件"""
        pass
    
    @abstractmethod
    def load_state(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """从文件加载状态"""
        pass