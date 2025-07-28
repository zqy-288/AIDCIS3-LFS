"""
全景图状态管理器实现
负责批量状态更新的优化管理
"""

from typing import Dict
from PySide6.QtCore import QObject, QTimer, Signal
from src.core_business.graphics.panorama.interfaces import IPanoramaStatusManager, IPanoramaDataModel
from src.core_business.models.hole_data import HoleStatus


class PanoramaStatusManager(QObject):
    """状态管理器实现"""
    
    # 信号
    batch_update_started = Signal()
    batch_update_completed = Signal(int)  # 更新数量
    
    def __init__(self, data_model: IPanoramaDataModel):
        super().__init__()
        self.data_model = data_model
        
        # 批量更新配置
        self.batch_interval = 200  # 默认200ms
        self.pending_updates: Dict[str, HoleStatus] = {}
        self._update_lock = False
        
        # 批量更新定时器
        self.batch_timer = QTimer()
        self.batch_timer.timeout.connect(self._execute_batch_update)
        self.batch_timer.setSingleShot(True)
    
    def queue_status_update(self, hole_id: str, status: HoleStatus) -> None:
        """
        队列化状态更新
        
        Args:
            hole_id: 孔位ID
            status: 新状态
        """
        # 添加到待处理队列
        self.pending_updates[hole_id] = status
        
        # 启动批量更新定时器
        if not self.batch_timer.isActive() and not self._update_lock:
            self.batch_timer.start(self.batch_interval)
    
    def flush_updates(self) -> int:
        """
        立即刷新所有待处理更新
        
        Returns:
            更新的数量
        """
        if self._update_lock or not self.pending_updates:
            return 0
        
        # 停止定时器
        self.batch_timer.stop()
        
        # 执行批量更新
        return self._execute_batch_update()
    
    def set_batch_interval(self, interval_ms: int) -> None:
        """
        设置批量更新间隔
        
        Args:
            interval_ms: 间隔时间（毫秒）
        """
        self.batch_interval = max(50, min(1000, interval_ms))  # 限制在50-1000ms
    
    def _execute_batch_update(self) -> int:
        """
        执行批量更新
        
        Returns:
            更新的数量
        """
        if self._update_lock or not self.pending_updates:
            return 0
        
        self._update_lock = True
        self.batch_update_started.emit()
        
        # 复制待更新项
        updates_to_process = self.pending_updates.copy()
        self.pending_updates.clear()
        
        # 执行更新
        update_count = 0
        for hole_id, status in updates_to_process.items():
            if self.data_model.update_hole_status(hole_id, status):
                update_count += 1
        
        self._update_lock = False
        self.batch_update_completed.emit(update_count)
        
        return update_count
    
    def clear_pending_updates(self) -> None:
        """清空待处理更新"""
        self.pending_updates.clear()
        self.batch_timer.stop()
    
    def get_pending_count(self) -> int:
        """获取待处理更新数量"""
        return len(self.pending_updates)
    
    def is_updating(self) -> bool:
        """是否正在更新"""
        return self._update_lock