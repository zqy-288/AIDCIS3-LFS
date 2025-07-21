"""
状态管理器
管理孔位状态的更新和统计
"""

from typing import Dict, List, Optional
from collections import defaultdict
import logging

from .hole_data import HoleData, HoleCollection, HoleStatus


class StatusManager:
    """状态管理器类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._status_history = defaultdict(list)  # 状态变更历史
        
    def update_hole_status(self, hole: HoleData, new_status: HoleStatus, reason: str = "") -> bool:
        """
        更新单个孔位状态
        
        Args:
            hole: 孔位数据
            new_status: 新状态
            reason: 状态变更原因
            
        Returns:
            bool: 更新是否成功
        """
        try:
            old_status = hole.status
            hole.status = new_status
            
            # 记录状态变更历史
            self._status_history[hole.hole_id].append({
                'old_status': old_status,
                'new_status': new_status,
                'reason': reason,
                'timestamp': self._get_current_timestamp()
            })
            
            self.logger.info(f"孔位 {hole.hole_id} 状态从 {old_status.value} 更新为 {new_status.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新孔位状态失败: {e}")
            return False
    
    def batch_update_status(self, holes: List[HoleData], new_status: HoleStatus, reason: str = "") -> int:
        """
        批量更新孔位状态
        
        Args:
            holes: 孔位数据列表
            new_status: 新状态
            reason: 状态变更原因
            
        Returns:
            int: 成功更新的数量
        """
        success_count = 0
        
        for hole in holes:
            if self.update_hole_status(hole, new_status, reason):
                success_count += 1
        
        self.logger.info(f"批量更新完成，成功更新 {success_count}/{len(holes)} 个孔位")
        return success_count
    
    def get_status_statistics(self, hole_collection: HoleCollection) -> Dict[HoleStatus, int]:
        """
        获取状态统计信息
        
        Args:
            hole_collection: 孔位集合
            
        Returns:
            Dict[HoleStatus, int]: 各状态的数量统计
        """
        return hole_collection.get_status_counts()
    
    def get_status_percentage(self, hole_collection: HoleCollection) -> Dict[HoleStatus, float]:
        """
        获取状态百分比
        
        Args:
            hole_collection: 孔位集合
            
        Returns:
            Dict[HoleStatus, float]: 各状态的百分比
        """
        counts = self.get_status_statistics(hole_collection)
        total = sum(counts.values())
        
        if total == 0:
            return {status: 0.0 for status in HoleStatus}
        
        return {status: (count / total) * 100 for status, count in counts.items()}
    
    def get_holes_by_status(self, hole_collection: HoleCollection, status: HoleStatus) -> List[HoleData]:
        """
        按状态获取孔位列表
        
        Args:
            hole_collection: 孔位集合
            status: 目标状态
            
        Returns:
            List[HoleData]: 指定状态的孔位列表
        """
        return hole_collection.get_holes_by_status(status)
    
    def get_pending_holes(self, hole_collection: HoleCollection) -> List[HoleData]:
        """获取待检测孔位"""
        return self.get_holes_by_status(hole_collection, HoleStatus.PENDING)
    
    def get_qualified_holes(self, hole_collection: HoleCollection) -> List[HoleData]:
        """获取合格孔位"""
        return self.get_holes_by_status(hole_collection, HoleStatus.QUALIFIED)
    
    def get_defective_holes(self, hole_collection: HoleCollection) -> List[HoleData]:
        """获取异常孔位"""
        return self.get_holes_by_status(hole_collection, HoleStatus.DEFECTIVE)
    
    def get_processing_holes(self, hole_collection: HoleCollection) -> List[HoleData]:
        """获取检测中孔位"""
        return self.get_holes_by_status(hole_collection, HoleStatus.PROCESSING)
    
    def get_status_history(self, hole_id: str) -> List[Dict]:
        """
        获取孔位状态变更历史
        
        Args:
            hole_id: 孔位ID
            
        Returns:
            List[Dict]: 状态变更历史
        """
        return self._status_history.get(hole_id, [])
    
    def clear_status_history(self, hole_id: Optional[str] = None) -> None:
        """
        清理状态历史
        
        Args:
            hole_id: 孔位ID，如果为None则清理所有历史
        """
        if hole_id:
            self._status_history.pop(hole_id, None)
        else:
            self._status_history.clear()
    
    def get_completion_rate(self, hole_collection: HoleCollection) -> float:
        """
        获取完成率（已检测的孔位比例）
        
        Args:
            hole_collection: 孔位集合
            
        Returns:
            float: 完成率百分比
        """
        counts = self.get_status_statistics(hole_collection)
        total = sum(counts.values())
        
        if total == 0:
            return 0.0
        
        # 已完成的状态包括：合格、异常、盲孔、拉杆孔
        completed_statuses = [
            HoleStatus.QUALIFIED,
            HoleStatus.DEFECTIVE,
            HoleStatus.BLIND,
            HoleStatus.TIE_ROD
        ]
        
        completed_count = sum(counts[status] for status in completed_statuses)
        return (completed_count / total) * 100
    
    def get_quality_rate(self, hole_collection: HoleCollection) -> float:
        """
        获取质量合格率
        
        Args:
            hole_collection: 孔位集合
            
        Returns:
            float: 质量合格率百分比
        """
        counts = self.get_status_statistics(hole_collection)
        
        # 已检测的孔位（排除待检和检测中）
        detected_statuses = [
            HoleStatus.QUALIFIED,
            HoleStatus.DEFECTIVE,
            HoleStatus.BLIND,
            HoleStatus.TIE_ROD
        ]
        
        detected_count = sum(counts[status] for status in detected_statuses)
        
        if detected_count == 0:
            return 0.0
        
        # 合格的孔位
        qualified_count = counts[HoleStatus.QUALIFIED]
        return (qualified_count / detected_count) * 100
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def export_status_report(self, hole_collection: HoleCollection) -> Dict:
        """
        导出状态报告
        
        Args:
            hole_collection: 孔位集合
            
        Returns:
            Dict: 状态报告
        """
        statistics = self.get_status_statistics(hole_collection)
        percentages = self.get_status_percentage(hole_collection)
        
        return {
            'total_holes': len(hole_collection),
            'completion_rate': self.get_completion_rate(hole_collection),
            'quality_rate': self.get_quality_rate(hole_collection),
            'status_counts': {status.value: count for status, count in statistics.items()},
            'status_percentages': {status.value: percentage for status, percentage in percentages.items()},
            'timestamp': self._get_current_timestamp()
        }
