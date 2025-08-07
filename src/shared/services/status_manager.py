"""
统一的状态管理器
整合了多个版本的最佳功能，提供完整的状态管理服务
"""

from typing import Dict, List, Optional, Callable, Any
from collections import defaultdict
from datetime import datetime
from enum import Enum
import logging
import weakref

from PySide6.QtCore import QObject, Signal, QTimer

# 尝试导入HoleStatus，兼容不同的导入路径
try:
    from src.shared.models.hole_data import HoleData, HoleCollection, HoleStatus
except ImportError:
    try:
        from src.shared.models.hole_data import HoleData, HoleCollection, HoleStatus
    except ImportError:
        # 如果都失败，定义一个简单的HoleStatus
        class HoleStatus(Enum):
            PENDING = "pending"
            QUALIFIED = "qualified"
            DEFECTIVE = "defective"
            BLIND = "blind"
            TIE_ROD = "tie_rod"
            PROCESSING = "processing"


class UnifiedStatusManager(QObject):
    """
    统一的状态管理器
    整合了三个版本的功能：
    1. 完整的状态管理功能（来自core_business/models）
    2. 回调机制（来自core_business/managers）
    3. UI优化的批量更新（来自P1/panorama_view）
    """
    
    # 信号定义
    status_updated = Signal(str, object)  # hole_id, new_status
    batch_update_started = Signal()
    batch_update_completed = Signal(int)  # update_count
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # 状态历史记录
        self._status_history = defaultdict(list)
        
        # 回调管理
        self._status_callbacks = []
        
        # 批量更新优化
        self._pending_updates: Dict[str, HoleStatus] = {}
        self._update_lock = False
        self.batch_interval = 200  # 批量更新间隔（毫秒）
        
        # 批量更新定时器
        self._batch_timer = QTimer()
        self._batch_timer.timeout.connect(self._execute_batch_update)
        self._batch_timer.setSingleShot(True)
        
        # 弱引用存储孔位集合
        self._hole_collection_ref = None
        
        # 状态映射（兼容字符串到枚举的转换）
        self._status_mapping = {
            'qualified': HoleStatus.QUALIFIED,
            'defective': HoleStatus.DEFECTIVE,
            'blind': HoleStatus.BLIND,
            'pending': HoleStatus.PENDING,
            'tie_rod': HoleStatus.TIE_ROD,
            'processing': HoleStatus.PROCESSING
        }
    
    # ========== 基础功能 ==========
    
    def set_hole_collection(self, hole_collection: HoleCollection) -> None:
        """设置孔位集合（使用弱引用避免循环引用）"""
        if hole_collection:
            self._hole_collection_ref = weakref.ref(hole_collection)
            self.logger.info(f"已关联孔位集合，共 {len(hole_collection)} 个孔位")
    
    def get_hole_collection(self) -> Optional[HoleCollection]:
        """获取孔位集合"""
        if self._hole_collection_ref:
            collection = self._hole_collection_ref()
            if collection:
                return collection
        
        # 尝试从共享数据管理器获取
        try:
            from src.core.shared_data_manager import SharedDataManager
            shared_data = SharedDataManager()
            collection = shared_data.get_hole_collection()
            if collection:
                self.set_hole_collection(collection)
                return collection
        except Exception as e:
            self.logger.debug(f"无法从共享数据管理器获取孔位集合: {e}")
        
        return None
    
    def update_status(self, hole_id: str, new_status: Any, reason: str = "", immediate: bool = False) -> bool:
        """
        更新孔位状态
        
        Args:
            hole_id: 孔位ID
            new_status: 新状态（字符串或HoleStatus枚举）
            reason: 状态变更原因
            immediate: 是否立即更新（跳过批量优化）
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 转换状态到枚举
            if isinstance(new_status, str):
                new_status = self._status_mapping.get(new_status.lower(), HoleStatus.PENDING)
            
            if immediate:
                # 立即更新
                return self._update_single_status(hole_id, new_status, reason)
            else:
                # 加入批量更新队列
                self.queue_status_update(hole_id, new_status)
                return True
                
        except Exception as e:
            self.logger.error(f"更新孔位状态失败: {e}")
            return False
    
    def _update_single_status(self, hole_id: str, new_status: HoleStatus, reason: str = "") -> bool:
        """更新单个孔位状态（内部方法）"""
        collection = self.get_hole_collection()
        if not collection:
            self.logger.warning("无法获取孔位集合")
            return False
        
        old_status = None
        updated = False
        
        # 更新状态
        if hasattr(collection, 'holes') and hole_id in collection.holes:
            hole = collection.holes[hole_id]
            old_status = hole.status
            hole.status = new_status
            updated = True
        elif hasattr(collection, 'update_hole_status'):
            # 使用集合的更新方法
            old_status = collection.get_hole_by_id(hole_id).status if hasattr(collection, 'get_hole_by_id') else None
            updated = collection.update_hole_status(hole_id, new_status)
        
        if updated:
            # 记录历史
            self._record_status_change(hole_id, old_status, new_status, reason)
            
            # 触发信号
            self.status_updated.emit(hole_id, new_status)
            
            # 触发回调
            self._trigger_callbacks(hole_id, new_status)
            
            self.logger.info(f"孔位 {hole_id} 状态更新: {old_status} -> {new_status}")
        
        return updated
    
    # ========== 批量更新优化 ==========
    
    def queue_status_update(self, hole_id: str, status: HoleStatus) -> None:
        """队列化状态更新（UI优化）"""
        self._pending_updates[hole_id] = status
        
        if not self._batch_timer.isActive() and not self._update_lock:
            self._batch_timer.start(self.batch_interval)
    
    def flush_updates(self) -> int:
        """立即刷新所有待处理更新"""
        if self._update_lock or not self._pending_updates:
            return 0
        
        self._batch_timer.stop()
        return self._execute_batch_update()
    
    def _execute_batch_update(self) -> int:
        """执行批量更新"""
        if self._update_lock or not self._pending_updates:
            return 0
        
        self._update_lock = True
        self.batch_update_started.emit()
        
        updates = self._pending_updates.copy()
        self._pending_updates.clear()
        
        update_count = 0
        for hole_id, status in updates.items():
            if self._update_single_status(hole_id, status):
                update_count += 1
        
        self._update_lock = False
        self.batch_update_completed.emit(update_count)
        
        return update_count
    
    def set_batch_interval(self, interval_ms: int) -> None:
        """设置批量更新间隔"""
        self.batch_interval = max(50, min(1000, interval_ms))
    
    # ========== 回调机制 ==========
    
    def add_status_callback(self, callback: Callable) -> None:
        """添加状态变更回调"""
        if callback not in self._status_callbacks:
            self._status_callbacks.append(callback)
    
    def remove_status_callback(self, callback: Callable) -> None:
        """移除状态变更回调"""
        if callback in self._status_callbacks:
            self._status_callbacks.remove(callback)
    
    def _trigger_callbacks(self, hole_id: str, new_status: HoleStatus) -> None:
        """触发所有回调"""
        for callback in self._status_callbacks:
            try:
                callback(hole_id, new_status)
            except Exception as e:
                self.logger.error(f"状态回调失败: {e}")
    
    # ========== 状态历史 ==========
    
    def _record_status_change(self, hole_id: str, old_status: Optional[HoleStatus], 
                            new_status: HoleStatus, reason: str) -> None:
        """记录状态变更历史"""
        self._status_history[hole_id].append({
            'old_status': old_status.value if old_status else 'unknown',
            'new_status': new_status.value,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_status_history(self, hole_id: str) -> List[Dict]:
        """获取状态变更历史"""
        return self._status_history.get(hole_id, [])
    
    def clear_status_history(self, hole_id: Optional[str] = None) -> None:
        """清理状态历史"""
        if hole_id:
            self._status_history.pop(hole_id, None)
        else:
            self._status_history.clear()
    
    # ========== 统计功能 ==========
    
    def get_status_statistics(self) -> Dict[HoleStatus, int]:
        """获取状态统计"""
        collection = self.get_hole_collection()
        if not collection:
            return {status: 0 for status in HoleStatus}
        
        if hasattr(collection, 'get_status_counts'):
            return collection.get_status_counts()
        
        # 手动统计
        counts = defaultdict(int)
        if hasattr(collection, 'holes'):
            for hole in collection.holes.values():
                counts[hole.status] += 1
        
        return dict(counts)
    
    def get_status_percentage(self) -> Dict[HoleStatus, float]:
        """获取状态百分比"""
        counts = self.get_status_statistics()
        total = sum(counts.values())
        
        if total == 0:
            return {status: 0.0 for status in HoleStatus}
        
        return {status: (count / total) * 100 for status, count in counts.items()}
    
    def get_completion_rate(self) -> float:
        """获取完成率"""
        counts = self.get_status_statistics()
        total = sum(counts.values())
        
        if total == 0:
            return 0.0
        
        completed_statuses = [
            HoleStatus.QUALIFIED,
            HoleStatus.DEFECTIVE,
            HoleStatus.BLIND,
            HoleStatus.TIE_ROD
        ]
        
        completed = sum(counts.get(status, 0) for status in completed_statuses)
        return (completed / total) * 100
    
    def get_quality_rate(self) -> float:
        """获取合格率"""
        counts = self.get_status_statistics()
        
        detected_statuses = [
            HoleStatus.QUALIFIED,
            HoleStatus.DEFECTIVE,
            HoleStatus.BLIND,
            HoleStatus.TIE_ROD
        ]
        
        detected = sum(counts.get(status, 0) for status in detected_statuses)
        
        if detected == 0:
            return 0.0
        
        qualified = counts.get(HoleStatus.QUALIFIED, 0)
        return (qualified / detected) * 100
    
    def export_status_report(self) -> Dict:
        """导出状态报告"""
        collection = self.get_hole_collection()
        total_holes = len(collection) if collection else 0
        
        return {
            'total_holes': total_holes,
            'completion_rate': self.get_completion_rate(),
            'quality_rate': self.get_quality_rate(),
            'status_counts': {
                status.value: count 
                for status, count in self.get_status_statistics().items()
            },
            'status_percentages': {
                status.value: percentage 
                for status, percentage in self.get_status_percentage().items()
            },
            'timestamp': datetime.now().isoformat()
        }
    
    # ========== 查询功能 ==========
    
    def get_holes_by_status(self, status: HoleStatus) -> List[HoleData]:
        """按状态获取孔位列表"""
        collection = self.get_hole_collection()
        if not collection:
            return []
        
        if hasattr(collection, 'get_holes_by_status'):
            return collection.get_holes_by_status(status)
        
        # 手动过滤
        holes = []
        if hasattr(collection, 'holes'):
            for hole in collection.holes.values():
                if hole.status == status:
                    holes.append(hole)
        
        return holes
    
    def get_pending_holes(self) -> List[HoleData]:
        """获取待检测孔位"""
        return self.get_holes_by_status(HoleStatus.PENDING)
    
    def get_qualified_holes(self) -> List[HoleData]:
        """获取合格孔位"""
        return self.get_holes_by_status(HoleStatus.QUALIFIED)
    
    def get_defective_holes(self) -> List[HoleData]:
        """获取异常孔位"""
        return self.get_holes_by_status(HoleStatus.DEFECTIVE)
    
    # ========== 批量操作 ==========
    
    def batch_update_status(self, updates: Dict[str, Any], immediate: bool = True) -> int:
        """
        批量更新状态
        
        Args:
            updates: {hole_id: status} 字典
            immediate: 是否立即执行
            
        Returns:
            成功更新的数量
        """
        if immediate:
            success_count = 0
            for hole_id, status in updates.items():
                if self.update_status(hole_id, status, immediate=True):
                    success_count += 1
            return success_count
        else:
            # 加入批量队列
            for hole_id, status in updates.items():
                self.queue_status_update(hole_id, status)
            return len(updates)
    
    def cleanup(self) -> None:
        """清理资源"""
        self._batch_timer.stop()
        self._pending_updates.clear()
        self._status_callbacks.clear()
        self._hole_collection_ref = None


# 为了兼容性，同时提供StatusManager别名
StatusManager = UnifiedStatusManager


# 全局实例管理
_global_status_manager = None


def get_status_manager() -> UnifiedStatusManager:
    """获取全局状态管理器实例"""
    global _global_status_manager
    if _global_status_manager is None:
        _global_status_manager = UnifiedStatusManager()
    return _global_status_manager