"""
[DEPRECATED] DetectionService检测服务 - 已废弃
处理检测相关的业务逻辑，包括检测流程控制、状态管理、模拟等

⚠️ 此文件已被重构后的新架构替代：
- 领域服务: /src/domain/services/batch_service.py
- 用例层: /src/application/use_cases/batch_detection_use_case.py
- 领域模型: /src/domain/models/detection_batch.py

新架构将检测逻辑重组为符合DDD原则的服务和用例。
请使用新的服务实现，本文件仅保留用于向后兼容。
"""

import random
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from PySide6.QtCore import QObject, Signal, QTimer

from src.core.interfaces.service_interfaces import IService, ServiceStatus
from src.core_business.models.hole_data import HoleData, HoleCollection, HoleStatus
from src.core_business.dxf_parser import DXFParser
from src.core_business.models.status_manager import StatusManager


class DetectionService(QObject):
    """
    检测服务
    负责检测流程的控制和管理
    """
    
    # 检测状态变化信号
    detection_state_changed = Signal(object)  # DetectionState
    
    # 检测进度信号
    detection_progress_updated = Signal(dict)  # progress_info
    
    # 孔位状态更新信号
    hole_status_updated = Signal(str, object)  # hole_id, status
    
    # 检测完成信号
    detection_completed = Signal(dict)  # result_info
    
    # 模拟相关信号
    simulation_state_changed = Signal(object)  # SimulationState
    simulation_progress_updated = Signal(dict)  # progress_info
    
    def __init__(self, dxf_parser: DXFParser, status_manager: StatusManager):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.dxf_parser = dxf_parser
        self.status_manager = status_manager
        
        # 检测状态
        self._service_status = ServiceStatus.INACTIVE
        self._detection_running = False
        self._detection_paused = False
        self._simulation_running = False
        
        # 检测数据
        self._detection_holes: List[HoleData] = []
        self._current_hole_index = 0
        self._detection_start_time: Optional[datetime] = None
        
        # 计时器
        self._detection_timer = QTimer()
        self._detection_timer.timeout.connect(self._process_detection_step)
        
        # 统计数据
        self._detection_stats = {
            "completed": 0,
            "pending": 0,
            "qualified": 0,
            "defective": 0,
            "blind": 0,
            "tie_rod": 0,
            "processing": 0,
            "completion_rate": 0.0,
            "qualification_rate": 0.0
        }
        
    def start(self) -> None:
        """启动服务"""
        self._service_status = ServiceStatus.STARTING
        self.logger.info("启动检测服务")
        self._service_status = ServiceStatus.ACTIVE
        
    def stop(self) -> None:
        """停止服务"""
        self._service_status = ServiceStatus.STOPPING
        self.stop_detection()
        self.stop_simulation()
        self._detection_timer.stop()
        self.logger.info("停止检测服务")
        self._service_status = ServiceStatus.INACTIVE
        
    def get_status(self) -> ServiceStatus:
        """获取服务状态"""
        return self._service_status
        
    def is_healthy(self) -> bool:
        """检查服务健康状态"""
        return self._service_status in [ServiceStatus.ACTIVE, ServiceStatus.INACTIVE]
        
    def start_detection(self, hole_collection: HoleCollection) -> Dict[str, Any]:
        """
        开始检测
        
        Args:
            hole_collection: 孔位集合
            
        Returns:
            操作结果
        """
        try:
            if self._detection_running:
                return {"success": False, "error": "检测已在运行中"}
                
            if not hole_collection or len(hole_collection.holes) == 0:
                return {"success": False, "error": "没有可检测的孔位"}
                
            # 创建有序的孔位列表
            self._detection_holes = self._create_ordered_hole_list(hole_collection)
            self._current_hole_index = 0
            self._detection_running = True
            self._detection_paused = False
            self._detection_start_time = datetime.now()
            
            # 重置统计数据
            self._reset_detection_stats(len(self._detection_holes))
            
            # 启动检测计时器
            self._detection_timer.start(1000)  # 每秒处理一个孔位
            
            # 发出状态变化信号
            from src.ui.view_models.enums import DetectionState
            self.detection_state_changed.emit(DetectionState.RUNNING)
            
            self.logger.info(f"开始检测，共{len(self._detection_holes)}个孔位")
            return {"success": True, "hole_count": len(self._detection_holes)}
            
        except Exception as e:
            self.logger.error(f"开始检测失败: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
            
    def pause_detection(self) -> Dict[str, Any]:
        """
        暂停/恢复检测
        
        Returns:
            操作结果
        """
        try:
            if not self._detection_running:
                return {"success": False, "error": "检测未在运行"}
                
            if self._detection_paused:
                # 恢复检测
                self._detection_timer.start(1000)
                self._detection_paused = False
                self.logger.info("恢复检测")
                
                from src.ui.view_models.enums import DetectionState
                self.detection_state_changed.emit(DetectionState.RUNNING)
                
                return {"success": True, "paused": False}
            else:
                # 暂停检测
                self._detection_timer.stop()
                self._detection_paused = True
                self.logger.info("暂停检测")
                
                from src.ui.view_models.enums import DetectionState
                self.detection_state_changed.emit(DetectionState.PAUSED)
                
                return {"success": True, "paused": True}
                
        except Exception as e:
            self.logger.error(f"暂停/恢复检测失败: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
            
    def stop_detection(self) -> Dict[str, Any]:
        """
        停止检测
        
        Returns:
            操作结果
        """
        try:
            if not self._detection_running:
                return {"success": True, "message": "检测未在运行"}
                
            self._detection_timer.stop()
            self._detection_running = False
            self._detection_paused = False
            self._detection_start_time = None
            
            # 发出状态变化信号
            from src.ui.view_models.enums import DetectionState
            self.detection_state_changed.emit(DetectionState.IDLE)
            
            self.logger.info("停止检测")
            return {"success": True}
            
        except Exception as e:
            self.logger.error(f"停止检测失败: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
            
    def start_simulation(self, hole_collection: HoleCollection) -> Dict[str, Any]:
        """
        开始模拟
        
        Args:
            hole_collection: 孔位集合
            
        Returns:
            操作结果
        """
        try:
            if self._simulation_running:
                return {"success": False, "error": "模拟已在运行中"}
                
            if not hole_collection or len(hole_collection.holes) == 0:
                return {"success": False, "error": "没有可模拟的孔位"}
                
            self._simulation_running = True
            
            # 创建模拟数据
            simulation_holes = list(hole_collection.holes.values())
            self._simulate_detection_batch(simulation_holes)
            
            from src.ui.view_models.enums import SimulationState
            self.simulation_state_changed.emit(SimulationState.RUNNING)
            
            self.logger.info(f"开始模拟，共{len(simulation_holes)}个孔位")
            return {"success": True, "hole_count": len(simulation_holes)}
            
        except Exception as e:
            self.logger.error(f"开始模拟失败: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
            
    def stop_simulation(self) -> Dict[str, Any]:
        """
        停止模拟
        
        Returns:
            操作结果
        """
        try:
            if not self._simulation_running:
                return {"success": True, "message": "模拟未在运行"}
                
            self._simulation_running = False
            
            from src.ui.view_models.enums import SimulationState
            self.simulation_state_changed.emit(SimulationState.STOPPED)
            
            self.logger.info("停止模拟")
            return {"success": True}
            
        except Exception as e:
            self.logger.error(f"停止模拟失败: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
            
    def _process_detection_step(self) -> None:
        """处理检测步骤"""
        try:
            if not self._detection_holes or self._current_hole_index >= len(self._detection_holes):
                # 检测完成
                self._complete_detection()
                return
                
            # 获取当前要检测的孔位
            current_hole = self._detection_holes[self._current_hole_index]
            
            # 设置为处理中状态
            current_hole.status = HoleStatus.PROCESSING
            self._update_hole_status(current_hole)
            
            # 模拟检测过程（实际项目中这里会调用真实的检测算法）
            detected_status = self._simulate_detection_result()
            current_hole.status = detected_status
            
            # 更新孔位状态
            self._update_hole_status(current_hole)
            
            # 更新统计数据
            self._update_detection_stats()
            
            # 移动到下一个孔位
            self._current_hole_index += 1
            
            # 发出进度更新信号
            progress_info = {
                "current": self._current_hole_index,
                "total": len(self._detection_holes),
                "current_hole": current_hole,
                "stats": self._detection_stats
            }
            self.detection_progress_updated.emit(progress_info)
            
        except Exception as e:
            self.logger.error(f"处理检测步骤失败: {e}", exc_info=True)
            self.stop_detection()
            
    def _complete_detection(self) -> None:
        """完成检测"""
        self._detection_running = False
        self._detection_paused = False
        self._detection_timer.stop()
        
        # 计算最终统计
        elapsed_time = None
        if self._detection_start_time:
            elapsed_time = (datetime.now() - self._detection_start_time).total_seconds()
            
        result_info = {
            "total_holes": len(self._detection_holes),
            "elapsed_time": elapsed_time,
            "stats": self._detection_stats
        }
        
        # 发出完成信号
        self.detection_completed.emit(result_info)
        
        from src.ui.view_models.enums import DetectionState
        self.detection_state_changed.emit(DetectionState.IDLE)
        
        self.logger.info(f"检测完成，用时{elapsed_time:.1f}秒" if elapsed_time else "检测完成")
        
    def _simulate_detection_result(self) -> HoleStatus:
        """
        模拟检测结果
        按照指定比例分配状态：99.5%合格，0.49%异常，0.01%其他
        
        Returns:
            检测状态
        """
        rand_value = random.random()
        
        if rand_value < 0.995:  # 99.5%概率合格
            return HoleStatus.QUALIFIED
        elif rand_value < 0.9999:  # 0.49%概率异常
            return HoleStatus.DEFECTIVE
        else:  # 0.01%概率其他状态
            other_statuses = [HoleStatus.BLIND, HoleStatus.TIE_ROD]
            return random.choice(other_statuses)
            
    def _simulate_detection_batch(self, holes: List[HoleData]) -> None:
        """
        批量模拟检测结果
        
        Args:
            holes: 孔位列表
        """
        for hole in holes:
            hole.status = self._simulate_detection_result()
            self._update_hole_status(hole)
            
        # 更新统计数据
        self._calculate_simulation_stats(holes)
        
        # 发出模拟进度信号
        progress_info = {
            "total": len(holes),
            "completed": len(holes),
            "stats": self._detection_stats
        }
        self.simulation_progress_updated.emit(progress_info)
        
    def _create_ordered_hole_list(self, hole_collection: HoleCollection) -> List[HoleData]:
        """
        创建有序的孔位列表
        
        Args:
            hole_collection: 孔位集合
            
        Returns:
            有序的孔位列表
        """
        holes = list(hole_collection.holes.values())
        
        # 按孔位ID排序
        holes.sort(key=lambda h: h.hole_id)
        
        # 重置所有孔位状态为待检
        for hole in holes:
            hole.status = HoleStatus.PENDING
            
        return holes
        
    def _update_hole_status(self, hole: HoleData) -> None:
        """
        更新孔位状态
        
        Args:
            hole: 孔位数据
        """
        self.hole_status_updated.emit(hole.hole_id, hole.status)
        
    def _reset_detection_stats(self, total_holes: int) -> None:
        """
        重置检测统计数据
        
        Args:
            total_holes: 总孔位数
        """
        self._detection_stats = {
            "completed": 0,
            "pending": total_holes,
            "qualified": 0,
            "defective": 0,
            "blind": 0,
            "tie_rod": 0,
            "processing": 0,
            "completion_rate": 0.0,
            "qualification_rate": 0.0
        }
        
    def _update_detection_stats(self) -> None:
        """更新检测统计数据"""
        # 计算各状态数量
        stats = {
            "completed": self._current_hole_index,
            "pending": len(self._detection_holes) - self._current_hole_index,
            "qualified": 0,
            "defective": 0,
            "blind": 0,
            "tie_rod": 0,
            "processing": 1 if self._current_hole_index < len(self._detection_holes) else 0
        }
        
        # 统计已完成孔位的状态
        for i in range(self._current_hole_index):
            if i < len(self._detection_holes):
                hole = self._detection_holes[i]
                if hole.status == HoleStatus.QUALIFIED:
                    stats["qualified"] += 1
                elif hole.status == HoleStatus.DEFECTIVE:
                    stats["defective"] += 1
                elif hole.status == HoleStatus.BLIND:
                    stats["blind"] += 1
                elif hole.status == HoleStatus.TIE_ROD:
                    stats["tie_rod"] += 1
                    
        # 计算比率
        total = len(self._detection_holes)
        stats["completion_rate"] = (self._current_hole_index / total * 100.0) if total > 0 else 0.0
        
        completed_total = stats["qualified"] + stats["defective"] + stats["blind"] + stats["tie_rod"]
        stats["qualification_rate"] = (stats["qualified"] / completed_total * 100.0) if completed_total > 0 else 0.0
        
        self._detection_stats = stats
        
    def _calculate_simulation_stats(self, holes: List[HoleData]) -> None:
        """
        计算模拟统计数据
        
        Args:
            holes: 孔位列表
        """
        stats = {
            "completed": len(holes),
            "pending": 0,
            "qualified": 0,
            "defective": 0,
            "blind": 0,
            "tie_rod": 0,
            "processing": 0,
            "completion_rate": 100.0,
            "qualification_rate": 0.0
        }
        
        # 统计各状态数量
        for hole in holes:
            if hole.status == HoleStatus.QUALIFIED:
                stats["qualified"] += 1
            elif hole.status == HoleStatus.DEFECTIVE:
                stats["defective"] += 1
            elif hole.status == HoleStatus.BLIND:
                stats["blind"] += 1
            elif hole.status == HoleStatus.TIE_ROD:
                stats["tie_rod"] += 1
                
        # 计算合格率
        total = len(holes)
        stats["qualification_rate"] = (stats["qualified"] / total * 100.0) if total > 0 else 0.0
        
        self._detection_stats = stats
        
    def get_detection_stats(self) -> Dict[str, Any]:
        """获取检测统计数据"""
        return self._detection_stats.copy()
        
    def is_detection_running(self) -> bool:
        """检查检测是否在运行"""
        return self._detection_running
        
    def is_detection_paused(self) -> bool:
        """检查检测是否暂停"""
        return self._detection_paused
        
    def is_simulation_running(self) -> bool:
        """检查模拟是否在运行"""
        return self._simulation_running
        
    def cleanup(self) -> None:
        """清理资源"""
        self.stop_detection()
        self.stop_simulation()
        self._detection_timer.stop()
        self.logger.info("检测服务清理完成")