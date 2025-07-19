"""
检测流程控制器
负责管理整个检测流程的状态和进度
"""

import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from enum import Enum

from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QWidget

from src.core.dependency_injection import injectable
from src.core.application import EventBus, ApplicationEvent
from src.core_business.models.hole_data import HoleData, HoleStatus
from src.models.batch_data_manager import BatchDataManager


class DetectionState(Enum):
    """检测状态枚举"""
    IDLE = "idle"           # 空闲
    PREPARING = "preparing" # 准备中
    RUNNING = "running"     # 运行中
    PAUSED = "paused"       # 暂停
    COMPLETED = "completed" # 完成
    ERROR = "error"         # 错误


@injectable()
class DetectionController(QObject):
    """
    检测控制器类
    管理检测流程的状态、进度和时序控制
    """
    
    # 局部信号
    detection_started = Signal(dict)    # 检测开始，参数：检测配置
    detection_paused = Signal(dict)     # 检测暂停，参数：暂停信息
    detection_resumed = Signal(dict)    # 检测恢复，参数：恢复信息
    detection_completed = Signal(dict)  # 检测完成，参数：完成信息
    detection_progress = Signal(dict)   # 检测进度，参数：进度信息
    detection_error = Signal(dict)      # 检测错误，参数：错误信息
    
    def __init__(self, event_bus: EventBus, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        
        # 数据管理器
        self.batch_manager = BatchDataManager()
        
        # 检测状态
        self._detection_state = DetectionState.IDLE
        self._detection_holes: List[HoleData] = []
        self._current_hole_index = 0
        self._detection_config = {}
        
        # 时间统计
        self._detection_start_time: Optional[datetime] = None
        self._detection_pause_time: Optional[datetime] = None
        self._total_pause_duration = timedelta(0)
        
        # 进度统计
        self._total_holes = 0
        self._completed_holes = 0
        self._failed_holes = 0
        
        # 定时器
        self._detection_timer = QTimer()
        self._detection_timer.timeout.connect(self._process_detection_step)
        
        self._progress_timer = QTimer()
        self._progress_timer.timeout.connect(self._update_progress)
        
        # 检测参数
        self._detection_interval = 100  # 默认每100ms检测一个孔位
        self._single_hole_detection_time = 50  # 每个孔位检测时间50ms
        
        # 订阅事件
        self._setup_event_subscriptions()
        
        self.logger.info("检测控制器初始化完成")
    
    def _setup_event_subscriptions(self):
        """设置事件订阅"""
        # 订阅检测请求事件
        self.event_bus.subscribe("DETECTION_REQUEST", self._on_detection_request)
        
        # 订阅检测控制事件
        self.event_bus.subscribe("DETECTION_CONTROL", self._on_detection_control)
        
        # 订阅孔位检测完成事件
        self.event_bus.subscribe("HOLE_DETECTION_COMPLETED", self._on_hole_detection_completed)
        
        self.logger.debug("检测控制器事件订阅设置完成")
    
    def start_detection(self, holes: List[HoleData], config: Optional[Dict[str, Any]] = None):
        """
        开始检测
        
        Args:
            holes: 待检测孔位列表
            config: 检测配置
        """
        try:
            if self._detection_state != DetectionState.IDLE:
                self.logger.warning(f"检测已在进行中，当前状态: {self._detection_state.value}")
                return False
            
            # 设置检测状态
            self._detection_state = DetectionState.PREPARING
            self._detection_holes = holes.copy()
            self._current_hole_index = 0
            self._detection_config = config or {}
            
            # 重置统计信息
            self._total_holes = len(holes)
            self._completed_holes = 0
            self._failed_holes = 0
            self._detection_start_time = datetime.now()
            self._total_pause_duration = timedelta(0)
            
            # 更新检测参数
            self._detection_interval = self._detection_config.get("interval", 100)
            self._single_hole_detection_time = self._detection_config.get("hole_detection_time", 50)
            
            # 发布检测开始事件
            start_info = {
                "total_holes": self._total_holes,
                "start_time": self._detection_start_time.isoformat(),
                "config": self._detection_config,
                "estimated_duration": self._calculate_estimated_duration()
            }
            
            event = ApplicationEvent("DETECTION_STARTED", start_info)
            self.event_bus.post_event(event)
            
            # 发出检测开始信号
            self.detection_started.emit(start_info)
            
            # 开始检测流程
            self._detection_state = DetectionState.RUNNING
            self._detection_timer.start(self._detection_interval)
            self._progress_timer.start(1000)  # 每秒更新一次进度
            
            self.logger.info(f"检测开始，共 {self._total_holes} 个孔位")
            return True
            
        except Exception as e:
            self.logger.error(f"开始检测失败: {e}")
            self._detection_state = DetectionState.ERROR
            self._emit_error("检测启动失败", str(e))
            return False
    
    def pause_detection(self):
        """暂停检测"""
        try:
            if self._detection_state != DetectionState.RUNNING:
                self.logger.warning(f"检测未在运行中，无法暂停，当前状态: {self._detection_state.value}")
                return False
            
            # 暂停定时器
            self._detection_timer.stop()
            self._progress_timer.stop()
            
            # 设置暂停状态
            self._detection_state = DetectionState.PAUSED
            self._detection_pause_time = datetime.now()
            
            # 构建暂停信息
            pause_info = {
                "pause_time": self._detection_pause_time.isoformat(),
                "completed_holes": self._completed_holes,
                "remaining_holes": self._total_holes - self._completed_holes,
                "progress_percent": (self._completed_holes / self._total_holes * 100) if self._total_holes > 0 else 0
            }
            
            # 发布暂停事件
            event = ApplicationEvent("DETECTION_PAUSED", pause_info)
            self.event_bus.post_event(event)
            
            # 发出暂停信号
            self.detection_paused.emit(pause_info)
            
            self.logger.info("检测已暂停")
            return True
            
        except Exception as e:
            self.logger.error(f"暂停检测失败: {e}")
            return False
    
    def resume_detection(self):
        """恢复检测"""
        try:
            if self._detection_state != DetectionState.PAUSED:
                self.logger.warning(f"检测未暂停，无法恢复，当前状态: {self._detection_state.value}")
                return False
            
            # 计算暂停时长
            if self._detection_pause_time:
                pause_duration = datetime.now() - self._detection_pause_time
                self._total_pause_duration += pause_duration
                self._detection_pause_time = None
            
            # 恢复检测状态
            self._detection_state = DetectionState.RUNNING
            self._detection_timer.start(self._detection_interval)
            self._progress_timer.start(1000)
            
            # 构建恢复信息
            resume_info = {
                "resume_time": datetime.now().isoformat(),
                "total_pause_duration": str(self._total_pause_duration),
                "remaining_holes": self._total_holes - self._completed_holes
            }
            
            # 发布恢复事件
            event = ApplicationEvent("DETECTION_RESUMED", resume_info)
            self.event_bus.post_event(event)
            
            # 发出恢复信号
            self.detection_resumed.emit(resume_info)
            
            self.logger.info("检测已恢复")
            return True
            
        except Exception as e:
            self.logger.error(f"恢复检测失败: {e}")
            return False
    
    def stop_detection(self):
        """停止检测"""
        try:
            if self._detection_state in [DetectionState.IDLE, DetectionState.COMPLETED]:
                self.logger.warning(f"检测未在进行中，无法停止，当前状态: {self._detection_state.value}")
                return False
            
            # 停止定时器
            self._detection_timer.stop()
            self._progress_timer.stop()
            
            # 完成检测
            self._complete_detection(forced=True)
            
            self.logger.info("检测已停止")
            return True
            
        except Exception as e:
            self.logger.error(f"停止检测失败: {e}")
            return False
    
    def get_detection_state(self) -> DetectionState:
        """获取检测状态"""
        return self._detection_state
    
    def get_detection_progress(self) -> Dict[str, Any]:
        """获取检测进度信息"""
        if self._detection_state == DetectionState.IDLE:
            return {"state": "idle", "progress": 0}
        
        elapsed_time = self._get_elapsed_time()
        estimated_total = self._calculate_estimated_duration()
        estimated_remaining = max(0, estimated_total - elapsed_time.total_seconds())
        
        return {
            "state": self._detection_state.value,
            "total_holes": self._total_holes,
            "completed_holes": self._completed_holes,
            "failed_holes": self._failed_holes,
            "current_hole_index": self._current_hole_index,
            "progress_percent": (self._completed_holes / self._total_holes * 100) if self._total_holes > 0 else 0,
            "elapsed_time": str(elapsed_time),
            "estimated_remaining": estimated_remaining,
            "detection_rate": self._completed_holes / elapsed_time.total_seconds() if elapsed_time.total_seconds() > 0 else 0
        }
    
    # 私有方法
    def _process_detection_step(self):
        """处理检测步骤（定时器调用）"""
        try:
            if self._current_hole_index >= len(self._detection_holes):
                # 所有孔位检测完成
                self._complete_detection()
                return
            
            current_hole = self._detection_holes[self._current_hole_index]
            
            # 模拟检测过程
            self._simulate_hole_detection(current_hole)
            
            # 移动到下一个孔位
            self._current_hole_index += 1
            
        except Exception as e:
            self.logger.error(f"处理检测步骤失败: {e}")
            self._emit_error("检测步骤处理失败", str(e))
    
    def _simulate_hole_detection(self, hole: HoleData):
        """模拟孔位检测"""
        try:
            # 设置为检测中状态
            hole.status = HoleStatus.PROCESSING
            
            # 发布孔位检测开始事件
            event = ApplicationEvent("HOLE_DETECTION_STARTED", {
                "hole_id": hole.hole_id,
                "hole_data": hole,
                "detection_index": self._current_hole_index
            })
            self.event_bus.post_event(event)
            
            # 使用定时器模拟检测时间
            QTimer.singleShot(self._single_hole_detection_time, 
                            lambda: self._finish_hole_detection(hole))
            
        except Exception as e:
            self.logger.error(f"模拟孔位检测失败: {e}")
            self._failed_holes += 1
    
    def _finish_hole_detection(self, hole: HoleData):
        """完成孔位检测"""
        try:
            # 模拟检测结果
            import random
            detection_results = [
                HoleStatus.QUALIFIED,
                HoleStatus.DEFECTIVE,
                HoleStatus.BLIND,
                HoleStatus.TIE_ROD
            ]
            
            # 根据配置设置检测结果概率
            success_rate = self._detection_config.get("success_rate", 0.8)
            if random.random() < success_rate:
                hole.status = HoleStatus.QUALIFIED
            else:
                hole.status = random.choice([HoleStatus.DEFECTIVE, HoleStatus.BLIND])
            
            self._completed_holes += 1
            
            # 发布孔位检测完成事件
            event = ApplicationEvent("HOLE_DETECTION_COMPLETED", {
                "hole_id": hole.hole_id,
                "hole_data": hole,
                "detection_result": hole.status.value,
                "detection_index": self._current_hole_index - 1
            })
            self.event_bus.post_event(event)
            
            self.logger.debug(f"孔位 {hole.hole_id} 检测完成，结果: {hole.status.value}")
            
        except Exception as e:
            self.logger.error(f"完成孔位检测失败: {e}")
            self._failed_holes += 1
    
    def _complete_detection(self, forced: bool = False):
        """完成检测"""
        try:
            # 停止定时器
            self._detection_timer.stop()
            self._progress_timer.stop()
            
            # 设置完成状态
            self._detection_state = DetectionState.COMPLETED
            end_time = datetime.now()
            
            # 计算统计信息
            total_duration = end_time - self._detection_start_time if self._detection_start_time else timedelta(0)
            effective_duration = total_duration - self._total_pause_duration
            
            completion_info = {
                "end_time": end_time.isoformat(),
                "total_duration": str(total_duration),
                "effective_duration": str(effective_duration),
                "total_holes": self._total_holes,
                "completed_holes": self._completed_holes,
                "failed_holes": self._failed_holes,
                "success_rate": (self._completed_holes / self._total_holes * 100) if self._total_holes > 0 else 0,
                "average_time_per_hole": effective_duration.total_seconds() / self._completed_holes if self._completed_holes > 0 else 0,
                "forced": forced
            }
            
            # 发布检测完成事件
            event = ApplicationEvent("DETECTION_COMPLETED", completion_info)
            self.event_bus.post_event(event)
            
            # 发出检测完成信号
            self.detection_completed.emit(completion_info)
            
            self.logger.info(f"检测完成，耗时: {total_duration}, 完成率: {completion_info['success_rate']:.1f}%")
            
        except Exception as e:
            self.logger.error(f"完成检测失败: {e}")
            self._emit_error("检测完成失败", str(e))
    
    def _update_progress(self):
        """更新进度（定时器调用）"""
        try:
            progress_info = self.get_detection_progress()
            
            # 发出进度更新信号
            self.detection_progress.emit(progress_info)
            
            # 发布进度更新事件
            event = ApplicationEvent("DETECTION_PROGRESS", progress_info)
            self.event_bus.post_event(event)
            
        except Exception as e:
            self.logger.error(f"更新进度失败: {e}")
    
    def _calculate_estimated_duration(self) -> float:
        """计算预计检测时长（秒）"""
        if not self._detection_holes:
            return 0
        
        # 基于检测间隔和单孔检测时间计算
        hole_count = len(self._detection_holes)
        estimated_seconds = hole_count * (self._detection_interval + self._single_hole_detection_time) / 1000
        
        return estimated_seconds
    
    def _get_elapsed_time(self) -> timedelta:
        """获取已经过时间"""
        if not self._detection_start_time:
            return timedelta(0)
        
        current_time = datetime.now()
        elapsed = current_time - self._detection_start_time
        
        # 如果当前是暂停状态，需要减去当前暂停时长
        if self._detection_state == DetectionState.PAUSED and self._detection_pause_time:
            current_pause = current_time - self._detection_pause_time
            elapsed = elapsed - current_pause
        
        # 减去总暂停时长
        elapsed = elapsed - self._total_pause_duration
        
        return max(elapsed, timedelta(0))
    
    def _emit_error(self, error_type: str, error_message: str):
        """发出错误信号"""
        error_info = {
            "error_type": error_type,
            "error_message": error_message,
            "timestamp": datetime.now().isoformat(),
            "detection_state": self._detection_state.value
        }
        
        # 发出错误信号
        self.detection_error.emit(error_info)
        
        # 发布错误事件
        event = ApplicationEvent("DETECTION_ERROR", error_info)
        self.event_bus.post_event(event)
    
    # 事件处理方法
    def _on_detection_request(self, event: ApplicationEvent):
        """处理检测请求事件"""
        try:
            holes = event.data.get("holes", [])
            config = event.data.get("config", {})
            
            if isinstance(holes, list) and len(holes) > 0:
                self.start_detection(holes, config)
            else:
                self.logger.warning("检测请求中没有有效的孔位数据")
                
        except Exception as e:
            self.logger.error(f"处理检测请求事件失败: {e}")
    
    def _on_detection_control(self, event: ApplicationEvent):
        """处理检测控制事件"""
        try:
            action = event.data.get("action")
            
            if action == "pause":
                self.pause_detection()
            elif action == "resume":
                self.resume_detection()
            elif action == "stop":
                self.stop_detection()
            else:
                self.logger.warning(f"未知的检测控制动作: {action}")
                
        except Exception as e:
            self.logger.error(f"处理检测控制事件失败: {e}")
    
    def _on_hole_detection_completed(self, event: ApplicationEvent):
        """处理孔位检测完成事件"""
        try:
            hole_id = event.data.get("hole_id")
            if hole_id:
                self.logger.debug(f"孔位 {hole_id} 检测完成处理")
                
        except Exception as e:
            self.logger.error(f"处理孔位检测完成事件失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        try:
            # 停止所有定时器
            self._detection_timer.stop()
            self._progress_timer.stop()
            
            # 取消事件订阅
            self.event_bus.unsubscribe("DETECTION_REQUEST", self._on_detection_request)
            self.event_bus.unsubscribe("DETECTION_CONTROL", self._on_detection_control)
            self.event_bus.unsubscribe("HOLE_DETECTION_COMPLETED", self._on_hole_detection_completed)
            
            # 重置状态
            self._detection_state = DetectionState.IDLE
            
            self.logger.info("检测控制器资源清理完成")
            
        except Exception as e:
            self.logger.error(f"清理检测控制器资源失败: {e}")