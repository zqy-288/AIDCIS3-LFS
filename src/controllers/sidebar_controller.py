"""
侧边栏UI控制器
负责管理侧边栏的各个面板：文件信息、状态统计、孔位信息、过滤器
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QWidget

from src.core.dependency_injection import injectable
from src.core.application import EventBus, ApplicationEvent
from src.core_business.models.hole_data import HoleData, HoleStatus
from src.models.batch_data_manager import BatchDataManager


@injectable()
class SidebarController(QObject):
    """
    侧边栏控制器类
    管理侧边栏的各个面板和数据展示
    """
    
    # 局部信号
    hole_info_requested = Signal(str)  # 请求孔位信息，参数：hole_id
    status_filter_changed = Signal(str)  # 状态过滤器改变，参数：filter_type
    file_info_updated = Signal(dict)  # 文件信息更新
    statistics_updated = Signal(dict)  # 统计信息更新
    
    def __init__(self, event_bus: EventBus, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        
        # 数据管理器
        self.batch_manager = BatchDataManager()
        
        # 当前状态数据
        self._current_file_info = {}
        self._current_statistics = {}
        self._current_hole_data: Optional[HoleData] = None
        self._status_filter = "all"  # all, pending, qualified, defective, etc.
        
        # 定时器用于定期更新统计信息
        self._stats_update_timer = QTimer()
        self._stats_update_timer.timeout.connect(self._update_statistics_internal)
        self._stats_update_timer.start(2000)  # 每2秒更新一次
        
        # 订阅事件
        self._setup_event_subscriptions()
        
        self.logger.info("侧边栏控制器初始化完成")
    
    def _setup_event_subscriptions(self):
        """设置事件订阅"""
        # 订阅孔位选择事件
        self.event_bus.subscribe("HOLE_SELECTED", self._on_hole_selected)
        
        # 订阅检测完成事件
        self.event_bus.subscribe("DETECTION_COMPLETED", self._on_detection_completed)
        
        # 订阅文件加载事件
        self.event_bus.subscribe("FILE_LOADED", self._on_file_loaded)
        
        # 订阅检测状态变化事件
        self.event_bus.subscribe("DETECTION_STATUS_CHANGED", self._on_detection_status_changed)
        
        self.logger.debug("事件订阅设置完成")
    
    def update_hole_info(self, hole_data: HoleData):
        """
        更新孔位信息显示
        
        Args:
            hole_data: 孔位数据对象
        """
        try:
            self._current_hole_data = hole_data
            
            # 构建孔位信息字典
            hole_info = {
                "hole_id": hole_data.hole_id,
                "position": f"({hole_data.center_x:.2f}, {hole_data.center_y:.2f})",
                "radius": f"{hole_data.radius:.3f}",
                "diameter": f"{hole_data.radius * 2:.3f}",
                "status": hole_data.status.value,
                "status_display": self._get_status_display_name(hole_data.status),
                "layer": hole_data.layer,
                "row": hole_data.row,
                "column": hole_data.column,
                "region": hole_data.region,
                "last_updated": datetime.now().strftime("%H:%M:%S")
            }
            
            # 添加元数据信息
            if hole_data.metadata:
                hole_info.update(hole_data.metadata)
            
            # 发出信号更新UI
            self.hole_info_requested.emit(hole_data.hole_id)
            
            self.logger.debug(f"孔位信息更新完成: {hole_data.hole_id}")
            
        except Exception as e:
            self.logger.error(f"更新孔位信息失败: {e}")
    
    def update_statistics(self, force_update: bool = False):
        """
        更新统计信息
        
        Args:
            force_update: 是否强制更新
        """
        try:
            # 获取当前批次数据
            current_batch = self.batch_manager.get_current_batch()
            if not current_batch:
                self.logger.debug("当前无批次数据，跳过统计更新")
                return
            
            # 计算各状态的孔位数量
            status_counts = self._calculate_status_counts(current_batch.get("holes", []))
            
            # 计算进度信息
            progress_info = self._calculate_progress_info(status_counts)
            
            # 计算文件信息
            file_info = self._get_current_file_info()
            
            # 构建统计信息
            statistics = {
                "status_counts": status_counts,
                "progress_info": progress_info,
                "file_info": file_info,
                "total_holes": sum(status_counts.values()),
                "last_updated": datetime.now().strftime("%H:%M:%S")
            }
            
            self._current_statistics = statistics
            
            # 发出统计更新信号
            self.statistics_updated.emit(statistics)
            
            self.logger.debug("统计信息更新完成")
            
        except Exception as e:
            self.logger.error(f"更新统计信息失败: {e}")
    
    def set_status_filter(self, filter_type: str):
        """
        设置状态过滤器
        
        Args:
            filter_type: 过滤类型 (all, pending, qualified, defective, etc.)
        """
        try:
            old_filter = self._status_filter
            self._status_filter = filter_type
            
            # 发出过滤器变化信号
            self.status_filter_changed.emit(filter_type)
            
            # 发布过滤器变化事件
            event = ApplicationEvent("STATUS_FILTER_CHANGED", {
                "old_filter": old_filter,
                "new_filter": filter_type
            })
            self.event_bus.post_event(event)
            
            self.logger.info(f"状态过滤器设置为: {filter_type}")
            
        except Exception as e:
            self.logger.error(f"设置状态过滤器失败: {e}")
    
    def get_current_hole_info(self) -> Optional[Dict[str, Any]]:
        """获取当前孔位信息"""
        if self._current_hole_data:
            return {
                "hole_id": self._current_hole_data.hole_id,
                "position": f"({self._current_hole_data.center_x:.2f}, {self._current_hole_data.center_y:.2f})",
                "radius": f"{self._current_hole_data.radius:.3f}",
                "status": self._current_hole_data.status.value,
                "status_display": self._get_status_display_name(self._current_hole_data.status)
            }
        return None
    
    def get_current_statistics(self) -> Dict[str, Any]:
        """获取当前统计信息"""
        return self._current_statistics.copy()
    
    def get_status_filter(self) -> str:
        """获取当前状态过滤器"""
        return self._status_filter
    
    # 私有方法
    def _calculate_status_counts(self, holes: List[Dict[str, Any]]) -> Dict[str, int]:
        """计算各状态的孔位数量"""
        counts = {
            "pending": 0,
            "qualified": 0, 
            "defective": 0,
            "blind": 0,
            "tie_rod": 0,
            "processing": 0
        }
        
        for hole in holes:
            status = hole.get("status", "pending")
            if status in counts:
                counts[status] += 1
        
        return counts
    
    def _calculate_progress_info(self, status_counts: Dict[str, int]) -> Dict[str, Any]:
        """计算进度信息"""
        total = sum(status_counts.values())
        completed = status_counts["qualified"] + status_counts["defective"] + status_counts["blind"] + status_counts["tie_rod"]
        
        progress_info = {
            "total_holes": total,
            "completed_holes": completed,
            "pending_holes": status_counts["pending"],
            "processing_holes": status_counts["processing"],
            "completion_rate": (completed / total * 100) if total > 0 else 0,
            "qualification_rate": (status_counts["qualified"] / completed * 100) if completed > 0 else 0
        }
        
        return progress_info
    
    def _get_current_file_info(self) -> Dict[str, Any]:
        """获取当前文件信息"""
        current_batch = self.batch_manager.get_current_batch()
        if current_batch:
            file_path = current_batch.get("file_path", "")
            if file_path and Path(file_path).exists():
                file_stat = Path(file_path).stat()
                return {
                    "file_name": Path(file_path).name,
                    "file_path": str(file_path),
                    "file_size": f"{file_stat.st_size / 1024:.1f} KB",
                    "load_time": current_batch.get("created_time", "未知"),
                    "hole_count": len(current_batch.get("holes", []))
                }
        
        return {
            "file_name": "未加载文件",
            "file_path": "-",
            "file_size": "-",
            "load_time": "-",
            "hole_count": 0
        }
    
    def _get_status_display_name(self, status: HoleStatus) -> str:
        """获取状态的显示名称"""
        status_names = {
            HoleStatus.PENDING: "待检",
            HoleStatus.QUALIFIED: "合格",
            HoleStatus.DEFECTIVE: "异常",
            HoleStatus.BLIND: "盲孔",
            HoleStatus.TIE_ROD: "拉杆孔",
            HoleStatus.PROCESSING: "检测中"
        }
        return status_names.get(status, str(status.value))
    
    def _update_statistics_internal(self):
        """内部统计更新方法（定时器调用）"""
        self.update_statistics()
    
    # 事件处理方法
    def _on_hole_selected(self, event: ApplicationEvent):
        """处理孔位选择事件"""
        try:
            hole_data = event.data.get("hole_data")
            if isinstance(hole_data, HoleData):
                self.update_hole_info(hole_data)
        except Exception as e:
            self.logger.error(f"处理孔位选择事件失败: {e}")
    
    def _on_detection_completed(self, event: ApplicationEvent):
        """处理检测完成事件"""
        try:
            # 检测完成后强制更新统计信息
            self.update_statistics(force_update=True)
            
            hole_id = event.data.get("hole_id")
            if hole_id:
                self.logger.info(f"检测完成，更新孔位 {hole_id} 信息")
        except Exception as e:
            self.logger.error(f"处理检测完成事件失败: {e}")
    
    def _on_file_loaded(self, event: ApplicationEvent):
        """处理文件加载事件"""
        try:
            file_path = event.data.get("file_path")
            if file_path:
                # 更新文件信息
                self._current_file_info = self._get_current_file_info()
                self.file_info_updated.emit(self._current_file_info)
                
                # 强制更新统计信息
                self.update_statistics(force_update=True)
                
                self.logger.info(f"文件加载完成，更新侧边栏信息: {file_path}")
        except Exception as e:
            self.logger.error(f"处理文件加载事件失败: {e}")
    
    def _on_detection_status_changed(self, event: ApplicationEvent):
        """处理检测状态变化事件"""
        try:
            # 检测状态变化时更新统计信息
            self.update_statistics()
        except Exception as e:
            self.logger.error(f"处理检测状态变化事件失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        try:
            # 停止定时器
            if self._stats_update_timer:
                self._stats_update_timer.stop()
            
            # 取消事件订阅
            self.event_bus.unsubscribe("HOLE_SELECTED", self._on_hole_selected)
            self.event_bus.unsubscribe("DETECTION_COMPLETED", self._on_detection_completed)
            self.event_bus.unsubscribe("FILE_LOADED", self._on_file_loaded)
            self.event_bus.unsubscribe("DETECTION_STATUS_CHANGED", self._on_detection_status_changed)
            
            self.logger.info("侧边栏控制器资源清理完成")
            
        except Exception as e:
            self.logger.error(f"清理侧边栏控制器资源失败: {e}")