"""状态服务模块"""
import logging
from typing import Optional, Dict
from PySide6.QtCore import QObject, Signal, QTimer
from datetime import datetime

from aidcis2.models.hole_data import HoleCollection, HoleStatus


class StatusService(QObject):
    """
    状态服务
    负责状态更新、时间追踪和统计
    """
    
    # 信号定义
    status_updated = Signal(dict)  # 状态统计数据
    time_updated = Signal(str, str)  # 经过时间, 估计剩余时间
    log_message = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 数据
        self.hole_collection: Optional[HoleCollection] = None
        
        # 时间追踪
        self.detection_start_time: Optional[datetime] = None
        self.detection_elapsed_seconds = 0
        
        # 定时器
        self.time_update_timer = QTimer()
        self.time_update_timer.timeout.connect(self._update_time)
        self.time_update_timer.start(1000)  # 每秒更新
        
        # UI组件引用
        self.status_labels = {}
        
    def set_hole_collection(self, hole_collection: HoleCollection):
        """设置孔位集合"""
        self.hole_collection = hole_collection
        self.update_status_display()
        
    def set_status_labels(self, labels: Dict[str, any]):
        """设置状态标签引用"""
        self.status_labels = labels
        
    def start_detection_timer(self):
        """开始检测计时"""
        self.detection_start_time = datetime.now()
        self.detection_elapsed_seconds = 0
        
    def stop_detection_timer(self):
        """停止检测计时"""
        self.detection_start_time = None
        
    def update_status_display(self):
        """更新状态显示"""
        if not self.hole_collection:
            stats = {
                'total': 0,
                'pending': 0,
                'processing': 0,
                'qualified': 0,
                'defective': 0,
                'blind': 0,
                'tie_rod': 0
            }
        else:
            # 统计各状态的孔位数量
            stats = self._calculate_statistics()
            
        # 更新UI标签
        self._update_ui_labels(stats)
        
        # 发送信号
        self.status_updated.emit(stats)
        
        # 记录日志
        self.log_message.emit(
            f"状态更新 - 总计: {stats['total']}, "
            f"待检: {stats['pending']}, "
            f"检测中: {stats['processing']}, "
            f"合格: {stats['qualified']}, "
            f"异常: {stats['defective']}"
        )
        
    def _calculate_statistics(self) -> Dict[str, int]:
        """计算统计数据"""
        stats = {
            'total': 0,
            'pending': 0,
            'processing': 0,
            'qualified': 0,
            'defective': 0,
            'blind': 0,
            'tie_rod': 0
        }
        
        if not self.hole_collection:
            return stats
            
        for hole in self.hole_collection.holes.values():
            stats['total'] += 1
            
            if hole.status == HoleStatus.PENDING:
                stats['pending'] += 1
            elif hole.status == HoleStatus.PROCESSING:
                stats['processing'] += 1
            elif hole.status == HoleStatus.QUALIFIED:
                stats['qualified'] += 1
            elif hole.status == HoleStatus.DEFECTIVE:
                stats['defective'] += 1
            elif hole.status == HoleStatus.BLIND:
                stats['blind'] += 1
            elif hole.status == HoleStatus.TIE_ROD:
                stats['tie_rod'] += 1
                
        return stats
        
    def _update_ui_labels(self, stats: Dict[str, int]):
        """更新UI标签"""
        label_mapping = {
            'total_count_label': f"{stats['total']}",
            'pending_count_label': f"{stats['pending']}",
            'processing_count_label': f"{stats['processing']}",
            'qualified_count_label': f"{stats['qualified']}",
            'defective_count_label': f"{stats['defective']}",
            'blind_count_label': f"{stats['blind']}",
            'tie_rod_count_label': f"{stats['tie_rod']}"
        }
        
        for label_name, text in label_mapping.items():
            if label_name in self.status_labels:
                self.status_labels[label_name].setText(text)
                
    def _update_time(self):
        """更新时间显示"""
        # 更新检测时间
        elapsed_time = self._get_detection_elapsed_time()
        
        # 估算剩余时间
        estimated_time = self._estimate_remaining_time()
        
        # 发送信号
        self.time_updated.emit(elapsed_time, estimated_time)
        
    def _get_detection_elapsed_time(self) -> str:
        """获取检测经过时间"""
        if self.detection_start_time:
            elapsed = datetime.now() - self.detection_start_time
            hours = int(elapsed.total_seconds() // 3600)
            minutes = int((elapsed.total_seconds() % 3600) // 60)
            seconds = int(elapsed.total_seconds() % 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return "00:00:00"
        
    def _estimate_remaining_time(self) -> str:
        """估算剩余时间"""
        if not self.hole_collection or not self.detection_start_time:
            return "--:--:--"
            
        stats = self._calculate_statistics()
        completed = stats['qualified'] + stats['defective'] + stats['blind'] + stats['tie_rod']
        remaining = stats['pending'] + stats['processing']
        
        if completed == 0 or remaining == 0:
            return "--:--:--"
            
        # 计算平均每个孔位的时间
        elapsed_seconds = (datetime.now() - self.detection_start_time).total_seconds()
        avg_time_per_hole = elapsed_seconds / completed
        
        # 估算剩余时间
        estimated_seconds = remaining * avg_time_per_hole
        hours = int(estimated_seconds // 3600)
        minutes = int((estimated_seconds % 3600) // 60)
        seconds = int(estimated_seconds % 60)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
    def get_completed_count(self) -> int:
        """获取已完成的孔位数量"""
        if not self.hole_collection:
            return 0
            
        stats = self._calculate_statistics()
        return stats['qualified'] + stats['defective'] + stats['blind'] + stats['tie_rod']