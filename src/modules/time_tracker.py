"""
时间管理器
用于跟踪检测开始/结束时间、计算平均检测速度和估算剩余时间
"""

import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal


@dataclass
class TimeStats:
    """时间统计信息"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    completed_count: int = 0
    total_count: int = 0
    average_time_per_hole: float = 0.0  # 每个孔的平均检测时间（秒）
    estimated_total_time: float = 0.0   # 预计总时间（秒）
    remaining_time: float = 0.0         # 剩余时间（秒）
    
    @property
    def elapsed_time(self) -> float:
        """获取已用时间（秒）"""
        if self.start_time:
            end = self.end_time or datetime.now()
            return (end - self.start_time).total_seconds()
        return 0.0
    
    @property
    def completion_rate(self) -> float:
        """获取完成率（0.0-1.0）"""
        if self.total_count > 0:
            return self.completed_count / self.total_count
        return 0.0
    
    @property
    def progress_percentage(self) -> float:
        """获取进度百分比（0.0-100.0）"""
        return self.completion_rate * 100


class TimeTracker(QObject):
    """时间跟踪器"""
    
    # 信号定义
    time_updated = Signal(object)  # 发射TimeStats对象
    progress_updated = Signal(float, float)  # 进度百分比, 剩余时间（秒）
    
    def __init__(self):
        super().__init__()
        self.reset()
        
        # 历史记录，用于优化时间估算
        self.historical_times: List[float] = []
        self.max_history_size = 20  # 保留最近20次的记录
        
    def reset(self):
        """重置所有计时器"""
        self.stats = TimeStats()
        self.hole_start_times: Dict[str, datetime] = {}
        self.hole_completion_times: List[float] = []
        
    def start_detection(self, total_holes: int):
        """开始检测任务"""
        self.stats.start_time = datetime.now()
        self.stats.total_count = total_holes
        self.stats.completed_count = 0
        self.hole_completion_times.clear()
        self.hole_start_times.clear()
        
        print(f"🕐 [时间跟踪] 开始检测任务: {total_holes}个孔位")
        self._emit_updates()
    
    def end_detection(self):
        """结束检测任务"""
        if self.stats.start_time:
            self.stats.end_time = datetime.now()
            
            # 更新历史记录
            if self.stats.average_time_per_hole > 0:
                self.historical_times.append(self.stats.average_time_per_hole)
                # 保持历史记录大小
                if len(self.historical_times) > self.max_history_size:
                    self.historical_times.pop(0)
            
            print(f"⏰ [时间跟踪] 检测任务完成，总用时: {self._format_duration(self.stats.elapsed_time)}")
            self._emit_updates()
    
    def start_hole_detection(self, hole_id: str):
        """开始检测特定孔位"""
        self.hole_start_times[hole_id] = datetime.now()
        
    def complete_hole_detection(self, hole_id: str):
        """完成特定孔位检测"""
        if hole_id in self.hole_start_times:
            start_time = self.hole_start_times[hole_id]
            completion_time = (datetime.now() - start_time).total_seconds()
            
            self.hole_completion_times.append(completion_time)
            self.stats.completed_count += 1
            
            # 更新平均时间和估算
            self._update_time_estimates()
            
            # 清理已完成的孔位记录
            del self.hole_start_times[hole_id]
            
            print(f"✅ [时间跟踪] 孔位 {hole_id} 完成，用时: {completion_time:.2f}秒")
            self._emit_updates()
    
    def update_progress(self, completed_count: int, total_count: int = None):
        """更新进度（手动方式，不依赖孔位级别的跟踪）"""
        self.stats.completed_count = completed_count
        if total_count is not None:
            self.stats.total_count = total_count
        
        # 使用历史数据估算时间
        self._update_time_estimates_from_history()
        
        self._emit_updates()
    
    def force_sync_progress(self, completed_count: int, total_count: int):
        """强制同步进度数据（解决数据不一致问题，生命安全相关）"""
        # 记录同步前的状态
        old_completed = self.stats.completed_count
        old_total = self.stats.total_count
        
        # 强制更新数据
        self.stats.completed_count = completed_count
        self.stats.total_count = total_count
        
        # 如果数据发生了变化，记录日志
        if old_completed != completed_count or old_total != total_count:
            print(f"🔄 [强制同步] 进度数据已同步: {old_completed}/{old_total} -> {completed_count}/{total_count}")
        
        # 重新计算时间估算
        self._update_time_estimates_from_history()
        
        # 发射更新信号
        self._emit_updates()
    
    def _update_time_estimates(self):
        """更新时间估算（基于当前检测数据）"""
        if len(self.hole_completion_times) > 0:
            # 计算平均时间（使用最近的几次检测来提高准确性）
            recent_times = self.hole_completion_times[-10:]  # 最近10次
            self.stats.average_time_per_hole = sum(recent_times) / len(recent_times)
            
            # 估算总时间和剩余时间
            self.stats.estimated_total_time = self.stats.average_time_per_hole * self.stats.total_count
            remaining_holes = self.stats.total_count - self.stats.completed_count
            self.stats.remaining_time = self.stats.average_time_per_hole * remaining_holes
    
    def _update_time_estimates_from_history(self):
        """使用历史数据更新时间估算"""
        if self.historical_times:
            # 使用历史平均值作为基础估算
            historical_avg = sum(self.historical_times) / len(self.historical_times)
            
            # 如果有当前检测数据，进行加权平均
            if self.hole_completion_times:
                current_avg = sum(self.hole_completion_times) / len(self.hole_completion_times)
                # 70%历史数据 + 30%当前数据
                self.stats.average_time_per_hole = historical_avg * 0.7 + current_avg * 0.3
            else:
                self.stats.average_time_per_hole = historical_avg
            
            # 估算剩余时间
            remaining_holes = self.stats.total_count - self.stats.completed_count
            self.stats.remaining_time = self.stats.average_time_per_hole * remaining_holes
            self.stats.estimated_total_time = self.stats.average_time_per_hole * self.stats.total_count
    
    def _emit_updates(self):
        """发射更新信号"""
        self.time_updated.emit(self.stats)
        self.progress_updated.emit(
            self.stats.progress_percentage,
            self.stats.remaining_time
        )
    
    def get_time_summary(self) -> Dict:
        """获取时间汇总信息"""
        return {
            'elapsed_time': self.stats.elapsed_time,
            'elapsed_time_str': self._format_duration(self.stats.elapsed_time),
            'estimated_total_time': self.stats.estimated_total_time,
            'estimated_total_time_str': self._format_duration(self.stats.estimated_total_time),
            'remaining_time': self.stats.remaining_time,
            'remaining_time_str': self._format_duration(self.stats.remaining_time),
            'completion_rate': self.stats.completion_rate,
            'progress_percentage': self.stats.progress_percentage,
            'average_time_per_hole': self.stats.average_time_per_hole,
            'completed_count': self.stats.completed_count,
            'total_count': self.stats.total_count,
            'holes_per_minute': 60 / self.stats.average_time_per_hole if self.stats.average_time_per_hole > 0 else 0
        }
    
    def calculate_completion_rate(self) -> float:
        """计算完成率"""
        return self.stats.completion_rate
    
    def calculate_qualification_rate(self, qualified_count: int) -> float:
        """计算合格率"""
        if self.stats.completed_count > 0:
            return qualified_count / self.stats.completed_count
        return 0.0
    
    def estimate_remaining_time(self) -> float:
        """估算剩余时间（秒）"""
        return self.stats.remaining_time
    
    def get_formatted_remaining_time(self) -> str:
        """获取格式化的剩余时间字符串"""
        return self._format_duration(self.stats.remaining_time)
    
    def get_formatted_elapsed_time(self) -> str:
        """获取格式化的已用时间字符串"""
        return self._format_duration(self.stats.elapsed_time)
    
    def _format_duration(self, seconds: float) -> str:
        """格式化时间长度为HH:MM:SS格式"""
        if seconds <= 0:
            return "00:00:00"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def is_detection_active(self) -> bool:
        """检查是否有活跃的检测任务"""
        return self.stats.start_time is not None and self.stats.end_time is None
    
    def get_detection_speed(self) -> float:
        """获取检测速度（孔/分钟）"""
        if self.stats.average_time_per_hole > 0:
            return 60 / self.stats.average_time_per_hole
        return 0.0


class ProgressTracker:
    """进度跟踪器（兼容原有接口）"""
    
    def __init__(self):
        self.time_tracker = TimeTracker()
        self.start_time = None
        self.completed_count = 0
        self.total_count = 0
        
    def calculate_completion_rate(self) -> float:
        """计算完成率"""
        return self.time_tracker.calculate_completion_rate()
    
    def calculate_qualification_rate(self, qualified_count: int) -> float:
        """计算合格率"""
        return self.time_tracker.calculate_qualification_rate(qualified_count)
    
    def estimate_remaining_time(self) -> float:
        """估算剩余时间"""
        return self.time_tracker.estimate_remaining_time()


# 单例实例
_time_tracker = None

def get_time_tracker():
    """获取时间跟踪器单例"""
    global _time_tracker
    if _time_tracker is None:
        _time_tracker = TimeTracker()
    return _time_tracker