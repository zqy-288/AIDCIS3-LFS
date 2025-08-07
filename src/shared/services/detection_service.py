"""
检测服务层
封装检测流程和逻辑
"""

from typing import Optional, Dict, Any, List, Callable
from PySide6.QtCore import QObject, Signal, QTimer
from datetime import datetime
import json


class DetectionService(QObject):
    """
    检测服务
    管理检测流程和状态
    """
    
    # 检测相关信号
    detection_started = Signal()
    detection_stopped = Signal()  
    detection_paused = Signal()
    detection_resumed = Signal()
    detection_completed = Signal(dict)  # result_info
    detection_progress = Signal(int, int)  # current, total
    detection_progress_updated = Signal(float)  # progress percentage
    simulation_progress_updated = Signal(float)  # simulation progress percentage
    hole_detected = Signal(str, str)  # hole_id, result
    hole_status_updated = Signal(str, str)  # hole_id, status
    detection_state_changed = Signal(str)  # state
    simulation_state_changed = Signal(str)  # simulation state
    
    def __init__(self):
        super().__init__()
        
        # 检测状态
        self.is_running = False
        self.is_paused = False
        self.current_index = 0
        self.holes_to_detect = []
        
        # 批次相关
        self.current_batch_id = None
        self.batch_service = None
        self.detection_results = {}  # 保存检测结果
        self.is_mock = False
        
        # 模拟参数
        self.simulation_params = {
            'speed': 10,
            'auto_mode': True,
            'interval': 10000,  # 10秒间隔，保持与SimulationController一致
            'success_rate': 0.995,
            'defect_rate': 0.004,
            'blind_rate': 0.001
        }
        
        # 检测定时器
        self.detection_timer = QTimer()
        self.detection_timer.timeout.connect(self._process_next_hole)
        
    def set_batch_service(self, batch_service):
        """设置批次服务"""
        self.batch_service = batch_service
    
    def start_detection(self, holes: List[Any], batch_id: str = None, is_mock: bool = False) -> bool:
        """开始检测"""
        try:
            if self.is_running:
                return False
                
            self.holes_to_detect = holes
            self.current_index = 0
            self.is_running = True
            self.is_paused = False
            self.current_batch_id = batch_id
            self.is_mock = is_mock
            self.detection_results = {}
            
            # 初始化所有孔位状态为PENDING
            from src.shared.models.hole_data import HoleStatus
            for hole in holes:
                if hasattr(hole, 'status'):
                    hole.status = HoleStatus.PENDING
            
            # 设置定时器间隔
            interval = self.simulation_params['interval'] if is_mock else 100
            self.detection_timer.setInterval(interval)
            
            # 添加调试日志
            mode_text = "模拟检测" if is_mock else "实际检测"
            print(f"🚀 [DetectionService] 开始{mode_text}, 间隔: {interval}ms, 总孔位: {len(holes)}")
            print(f"📍 [DetectionService] 文件位置: src/services/detection_service.py")
            print(f"⏱️ [DetectionService] 定时器已设置为 {interval}ms 间隔")
            
            self.detection_started.emit()
            self.detection_timer.start()
            
            return True
        except Exception as e:
            print(f"Error starting detection: {e}")
            return False
    
    def resume_detection(self, detection_state: dict) -> bool:
        """从保存的状态恢复检测"""
        try:
            if self.is_running:
                return False
            
            # 恢复状态
            self.current_index = detection_state.get('current_index', 0)
            self.detection_results = detection_state.get('detection_results', {})
            self.is_mock = detection_state.get('is_mock', False)
            self.simulation_params = detection_state.get('simulation_params', self.simulation_params)
            
            # 恢复检测列表（从状态中获取待检测的孔位）
            self.holes_to_detect = detection_state.get('pending_holes', [])
            
            self.is_running = True
            self.is_paused = False
            
            # 设置定时器间隔
            interval = self.simulation_params['interval'] if self.is_mock else 100
            self.detection_timer.setInterval(interval)
            
            self.detection_resumed.emit()
            self.detection_timer.start()
            
            return True
        except Exception as e:
            print(f"Error resuming detection: {e}")
            return False
            
    def pause_detection(self) -> bool:
        """暂停检测"""
        try:
            if not self.is_running or self.is_paused:
                return False
                
            self.is_paused = True
            self.detection_timer.stop()
            
            # 保存检测状态
            if self.batch_service and self.current_batch_id:
                detection_state = self._get_detection_state()
                self.batch_service.pause_batch(self.current_batch_id, detection_state)
            
            self.detection_paused.emit()
            
            return True
        except Exception as e:
            print(f"Error pausing detection: {e}")
            return False
    
    def _get_detection_state(self) -> dict:
        """获取当前检测状态"""
        # 获取待检测的孔位ID列表
        pending_holes = []
        if hasattr(self.holes_to_detect[0], 'hole_id'):
            pending_holes = [h.hole_id for h in self.holes_to_detect[self.current_index:]]
        
        return {
            'batch_id': self.current_batch_id,
            'is_mock': self.is_mock,
            'detection_status': {
                'is_running': self.is_running,
                'is_paused': self.is_paused,
                'pause_time': datetime.now().isoformat()
            },
            'progress': {
                'current_index': self.current_index,
                'total_holes': len(self.holes_to_detect),
                'completed_holes': self.current_index,
                'pending_holes': pending_holes
            },
            'detection_results': self.detection_results,
            'simulation_params': self.simulation_params
        }
            
    def stop_detection(self) -> bool:
        """停止检测"""
        try:
            self.is_running = False
            self.is_paused = False
            self.detection_timer.stop()
            self.detection_stopped.emit()
            
            return True
        except Exception as e:
            print(f"Error stopping detection: {e}")
            return False
            
    def _process_next_hole(self):
        """处理下一个孔位"""
        if not self.is_running or self.is_paused:
            return
            
        if self.current_index >= len(self.holes_to_detect):
            # 检测完成
            self.stop_detection()
            return
            
        # 模拟检测当前孔位
        current_hole = self.holes_to_detect[self.current_index]
        hole_id = getattr(current_hole, 'hole_id', f'hole_{self.current_index}')
        
        # 模拟检测结果
        import random
        result = random.choice(['qualified', 'defective', 'blind'])
        
        # 发射信号
        self.hole_detected.emit(hole_id, result)
        self.detection_progress.emit(self.current_index + 1, len(self.holes_to_detect))
        
        # 移动到下一个孔位
        self.current_index += 1
        
    def get_detection_status(self) -> Dict[str, Any]:
        """获取检测状态"""
        return {
            'is_running': self.is_running,
            'is_paused': self.is_paused,
            'current_index': self.current_index,
            'total_holes': len(self.holes_to_detect),
            'progress_percent': (self.current_index / max(len(self.holes_to_detect), 1)) * 100
        }


# 全局检测服务实例
_global_detection_service = None


def get_detection_service() -> DetectionService:
    """获取全局检测服务实例"""
    global _global_detection_service
    if _global_detection_service is None:
        _global_detection_service = DetectionService()
    return _global_detection_service