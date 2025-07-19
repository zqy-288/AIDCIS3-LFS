"""
应用程序数据模型
作为应用程序的单一数据源，管理所有核心数据和状态
"""

from typing import Dict, Any, List, Optional, Set
import logging
from datetime import datetime
from PySide6.QtCore import QObject, Signal, QTimer

# 导入现有的业务模型
from src.core_business.models.hole_data import HoleData, HoleCollection, HoleStatus
from src.core_business.models.status_manager import StatusManager
from src.models.detection_state import DetectionState, DetectionStateManager
from src.models.event_types import EventTypes


class ApplicationModel(QObject):
    
    # 信号定义
    data_loaded = Signal(str, object)  # 数据加载信号 (file_path, hole_collection)

    """
    应用程序数据模型
    
    作为应用程序的单一数据源（Single Source of Truth），
    管理所有核心数据状态和业务逻辑状态。
    使用Qt信号机制通知数据变化。
    """
    
    # ===================
    # Qt信号定义
    # ===================
    
    # 工件相关信号
    workpiece_loaded = Signal(str)  # 工件加载完成，参数：工件ID
    workpiece_unloaded = Signal()   # 工件卸载
    workpiece_changed = Signal(str, dict)  # 工件信息变化，参数：工件ID，变化数据
    
    # 孔位数据相关信号
    hole_data_changed = Signal(str, dict)  # 孔位数据变化，参数：孔位ID，变化数据
    hole_status_changed = Signal(str, str, str)  # 孔位状态变化，参数：孔位ID，旧状态，新状态
    hole_selected = Signal(str)  # 孔位选中，参数：孔位ID
    hole_deselected = Signal(str)  # 孔位取消选中，参数：孔位ID
    hole_collection_updated = Signal()  # 孔位集合更新
    
    # 检测状态相关信号
    detection_state_changed = Signal(str, str)  # 检测状态变化，参数：旧状态，新状态
    detection_progress_changed = Signal(int, str)  # 检测进度变化，参数：进度百分比，当前孔位ID
    detection_results_updated = Signal(dict)  # 检测结果更新，参数：结果数据
    
    # 应用程序状态相关信号
    application_state_changed = Signal(str, object)  # 应用状态变化，参数：状态键，状态值
    configuration_changed = Signal(str, dict)  # 配置变化，参数：配置键，配置数据
    
    # 数据统计相关信号
    statistics_updated = Signal(dict)  # 统计数据更新，参数：统计数据
    
    # 错误和状态消息信号
    error_occurred = Signal(str, str)  # 错误发生，参数：错误类型，错误消息
    status_message_changed = Signal(str)  # 状态消息变化，参数：状态消息
    
    def __init__(self):
        """初始化应用程序数据模型"""
        super().__init__()
        
        # 初始化日志记录器
        self._logger = logging.getLogger(__name__)
        
        # 核心数据状态
        self._current_workpiece: Optional[str] = None
        self._hole_collection: Optional[HoleCollection] = None
        self._selected_holes: Set[str] = set()
        self._detection_results: Dict[str, Dict[str, Any]] = {}
        
        # 应用程序配置和状态
        self._application_config: Dict[str, Any] = {}
        self._application_state: Dict[str, Any] = {}
        
        # 检测状态管理
        self._detection_state_manager = DetectionStateManager()
        self._detection_state_manager.add_state_change_callback(self._on_detection_state_changed)
        
        # 孔位状态管理
        self._status_manager = StatusManager()
        
        # 统计数据缓存
        self._statistics_cache: Dict[str, Any] = {}
        self._statistics_cache_timestamp: Optional[datetime] = None
        self._statistics_cache_ttl: int = 5  # 缓存生存时间（秒）
        
        # 数据变化监听
        self._data_change_listeners: List[callable] = []
        
        # 定时器用于定期更新统计数据
        self._statistics_timer = QTimer()
        self._statistics_timer.timeout.connect(self._update_statistics_cache)
        self._statistics_timer.start(1000)  # 每秒更新一次
        
        self._logger.info("ApplicationModel initialized")
    
    # ===================
    # 工件管理
    # ===================
    
    @property
    def current_workpiece(self) -> Optional[str]:
        """获取当前工件ID"""
        return self._current_workpiece
    
    @current_workpiece.setter
    def current_workpiece(self, workpiece_id: Optional[str]) -> None:
        """设置当前工件ID"""
        if self._current_workpiece != workpiece_id:
            old_workpiece = self._current_workpiece
            self._current_workpiece = workpiece_id
            
            if workpiece_id:
                self.workpiece_loaded.emit(workpiece_id)
                self._logger.info(f"Workpiece loaded: {workpiece_id}")
            else:
                self.workpiece_unloaded.emit()
                self._logger.info("Workpiece unloaded")
            
            # 清理相关数据
            if old_workpiece != workpiece_id:
                self._clear_workpiece_data()
    
    def load_workpiece(self, workpiece_id: str, workpiece_data: Dict[str, Any]) -> bool:
        """
        加载工件数据
        
        Args:
            workpiece_id: 工件ID
            workpiece_data: 工件数据
            
        Returns:
            bool: 加载是否成功
        """
        try:
            # 设置当前工件
            self.current_workpiece = workpiece_id
            
            # 更新工件相关的应用状态
            self._application_state.update({
                'workpiece_id': workpiece_id,
                'workpiece_data': workpiece_data,
                'load_timestamp': datetime.now().isoformat()
            })
            
            # 发送工件变化信号
            self.workpiece_changed.emit(workpiece_id, workpiece_data)
            
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to load workpiece {workpiece_id}: {e}")
            self.error_occurred.emit("workpiece_load_error", str(e))
            return False
    
    def unload_workpiece(self) -> bool:
        """
        卸载当前工件
        
        Returns:
            bool: 卸载是否成功
        """
        try:
            if self._current_workpiece:
                old_workpiece = self._current_workpiece
                self.current_workpiece = None
                self._logger.info(f"Workpiece unloaded: {old_workpiece}")
            
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to unload workpiece: {e}")
            self.error_occurred.emit("workpiece_unload_error", str(e))
            return False
    
    def _clear_workpiece_data(self) -> None:
        """清理工件相关数据"""
        self._hole_collection = None
        self._selected_holes.clear()
        self._detection_results.clear()
        self._statistics_cache.clear()
        self._statistics_cache_timestamp = None
        
        # 重置检测状态
        self._detection_state_manager.reset_to_idle("Workpiece changed")
    
    # ===================
    # 孔位数据管理
    # ===================
    
    @property
    def hole_collection(self) -> Optional[HoleCollection]:
        """获取孔位集合"""
        return self._hole_collection
    
    @hole_collection.setter
    def hole_collection(self, collection: Optional[HoleCollection]) -> None:
        """设置孔位集合"""
        if self._hole_collection != collection:
            self._hole_collection = collection
            self._selected_holes.clear()
            
            # 发送孔位集合更新信号
            self.hole_collection_updated.emit()
            
            # 更新统计数据
            self._update_statistics_cache()
            
            if collection:
                self._logger.info(f"Hole collection updated: {len(collection)} holes")
            else:
                self._logger.info("Hole collection cleared")
    
    def get_hole_data(self, hole_id: str) -> Optional[HoleData]:
        """
        获取指定孔位的数据
        
        Args:
            hole_id: 孔位ID
            
        Returns:
            Optional[HoleData]: 孔位数据，如果不存在返回None
        """
        if self._hole_collection:
            return self._hole_collection.get_hole(hole_id)
        return None
    
    def update_hole_data(self, hole_id: str, data: Dict[str, Any]) -> bool:
        """
        更新孔位数据
        
        Args:
            hole_id: 孔位ID
            data: 要更新的数据
            
        Returns:
            bool: 更新是否成功
        """
        try:
            if not self._hole_collection:
                self._logger.warning("No hole collection available for update")
                return False
            
            hole = self._hole_collection.get_hole(hole_id)
            if not hole:
                self._logger.warning(f"Hole {hole_id} not found")
                return False
            
            # 更新孔位数据
            old_status = hole.status
            
            # 更新位置信息
            if 'center_x' in data:
                hole.center_x = data['center_x']
            if 'center_y' in data:
                hole.center_y = data['center_y']
            if 'radius' in data:
                hole.radius = data['radius']
            
            # 更新状态
            if 'status' in data:
                new_status = data['status']
                if isinstance(new_status, str):
                    new_status = HoleStatus(new_status)
                if hole.status != new_status:
                    hole.status = new_status
                    self.hole_status_changed.emit(hole_id, old_status.value, new_status.value)
            
            # 更新元数据
            if 'metadata' in data:
                hole.metadata.update(data['metadata'])
            
            # 发送数据变化信号
            self.hole_data_changed.emit(hole_id, data)
            
            self._logger.debug(f"Hole data updated: {hole_id}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to update hole data {hole_id}: {e}")
            self.error_occurred.emit("hole_data_update_error", str(e))
            return False
    
    def update_hole_status(self, hole_id: str, status: HoleStatus, reason: str = "") -> bool:
        """
        更新孔位状态
        
        Args:
            hole_id: 孔位ID
            status: 新状态
            reason: 状态变更原因
            
        Returns:
            bool: 更新是否成功
        """
        try:
            hole = self.get_hole_data(hole_id)
            if not hole:
                return False
            
            # 使用状态管理器更新状态
            success = self._status_manager.update_hole_status(hole, status, reason)
            
            if success:
                # 发送状态变化信号
                self.hole_status_changed.emit(hole_id, hole.status.value, status.value)
                
                # 更新统计数据
                self._update_statistics_cache()
            
            return success
            
        except Exception as e:
            self._logger.error(f"Failed to update hole status {hole_id}: {e}")
            self.error_occurred.emit("hole_status_update_error", str(e))
            return False
    
    # ===================
    # 孔位选择管理
    # ===================
    
    @property
    def selected_holes(self) -> Set[str]:
        """获取选中的孔位ID集合"""
        return self._selected_holes.copy()
    
    def select_hole(self, hole_id: str) -> bool:
        """
        选择孔位
        
        Args:
            hole_id: 孔位ID
            
        Returns:
            bool: 选择是否成功
        """
        if hole_id not in self._selected_holes:
            if self.get_hole_data(hole_id):
                self._selected_holes.add(hole_id)
                self.hole_selected.emit(hole_id)
                self._logger.debug(f"Hole selected: {hole_id}")
                return True
            else:
                self._logger.warning(f"Cannot select non-existent hole: {hole_id}")
                return False
        return True
    
    def deselect_hole(self, hole_id: str) -> bool:
        """
        取消选择孔位
        
        Args:
            hole_id: 孔位ID
            
        Returns:
            bool: 取消选择是否成功
        """
        if hole_id in self._selected_holes:
            self._selected_holes.remove(hole_id)
            self.hole_deselected.emit(hole_id)
            self._logger.debug(f"Hole deselected: {hole_id}")
            return True
        return False
    
    def select_multiple_holes(self, hole_ids: List[str]) -> int:
        """
        选择多个孔位
        
        Args:
            hole_ids: 孔位ID列表
            
        Returns:
            int: 成功选择的孔位数量
        """
        success_count = 0
        for hole_id in hole_ids:
            if self.select_hole(hole_id):
                success_count += 1
        
        return success_count
    
    def clear_selection(self) -> None:
        """清除所有选择"""
        selected_holes = self._selected_holes.copy()
        self._selected_holes.clear()
        
        # 发送取消选择信号
        for hole_id in selected_holes:
            self.hole_deselected.emit(hole_id)
        
        if selected_holes:
            self._logger.debug(f"Cleared selection of {len(selected_holes)} holes")
    
    # ===================
    # 检测状态管理
    # ===================
    
    @property
    def detection_state(self) -> DetectionState:
        """获取当前检测状态"""
        return self._detection_state_manager.current_state
    
    @detection_state.setter
    def detection_state(self, state: DetectionState) -> None:
        """设置检测状态"""
        self._detection_state_manager.transition_to(state)
    
    def transition_detection_state(self, state: DetectionState, reason: str = "") -> bool:
        """
        转换检测状态
        
        Args:
            state: 目标状态
            reason: 转换原因
            
        Returns:
            bool: 转换是否成功
        """
        return self._detection_state_manager.transition_to(state, reason)
    
    def can_transition_to_detection_state(self, state: DetectionState) -> bool:
        """
        检查是否可以转换到指定检测状态
        
        Args:
            state: 目标状态
            
        Returns:
            bool: 是否可以转换
        """
        return self._detection_state_manager.can_transition_to(state)
    
    def _on_detection_state_changed(self, old_state: DetectionState, new_state: DetectionState) -> None:
        """
        检测状态变化回调
        
        Args:
            old_state: 旧状态
            new_state: 新状态
        """
        self.detection_state_changed.emit(old_state.value, new_state.value)
        self._logger.info(f"Detection state changed: {old_state.value} -> {new_state.value}")
    
    # ===================
    # 检测结果管理
    # ===================
    
    def update_detection_results(self, hole_id: str, results: Dict[str, Any]) -> None:
        """
        更新检测结果
        
        Args:
            hole_id: 孔位ID
            results: 检测结果数据
        """
        self._detection_results[hole_id] = {
            **results,
            'timestamp': datetime.now().isoformat(),
            'hole_id': hole_id
        }
        
        # 发送检测结果更新信号
        self.detection_results_updated.emit(self._detection_results[hole_id])
        
        # 更新统计数据
        self._update_statistics_cache()
        
        self._logger.debug(f"Detection results updated for hole: {hole_id}")
    
    def get_detection_results(self, hole_id: str) -> Optional[Dict[str, Any]]:
        """
        获取指定孔位的检测结果
        
        Args:
            hole_id: 孔位ID
            
        Returns:
            Optional[Dict[str, Any]]: 检测结果，如果不存在返回None
        """
        return self._detection_results.get(hole_id)
    
    def get_all_detection_results(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有检测结果
        
        Returns:
            Dict[str, Dict[str, Any]]: 所有检测结果
        """
        return self._detection_results.copy()
    
    def clear_detection_results(self) -> None:
        """清除所有检测结果"""
        self._detection_results.clear()
        self._update_statistics_cache()
        self._logger.info("Detection results cleared")
    
    # ===================
    # 统计数据管理
    # ===================
    
    def get_detection_summary(self) -> Dict[str, Any]:
        """
        获取检测摘要信息
        
        Returns:
            Dict[str, Any]: 检测摘要数据
        """
        if not self._hole_collection:
            return {
                'total_holes': 0,
                'detected_holes': 0,
                'detection_rate': 0.0,
                'completion_rate': 0.0,
                'quality_rate': 0.0
            }
        
        # 检查缓存是否有效
        if self._is_statistics_cache_valid():
            return self._statistics_cache
        
        # 计算统计数据
        total_holes = len(self._hole_collection)
        detected_holes = len(self._detection_results)
        
        # 获取状态统计
        status_counts = self._status_manager.get_status_statistics(self._hole_collection)
        completion_rate = self._status_manager.get_completion_rate(self._hole_collection)
        quality_rate = self._status_manager.get_quality_rate(self._hole_collection)
        
        detection_rate = (detected_holes / total_holes * 100) if total_holes > 0 else 0.0
        
        summary = {
            'total_holes': total_holes,
            'detected_holes': detected_holes,
            'detection_rate': round(detection_rate, 2),
            'completion_rate': round(completion_rate, 2),
            'quality_rate': round(quality_rate, 2),
            'status_counts': {status.value: count for status, count in status_counts.items()},
            'selected_holes_count': len(self._selected_holes),
            'detection_state': self._detection_state_manager.current_state.value,
            'last_updated': datetime.now().isoformat()
        }
        
        # 更新缓存
        self._statistics_cache = summary
        self._statistics_cache_timestamp = datetime.now()
        
        return summary
    
    def _is_statistics_cache_valid(self) -> bool:
        """检查统计数据缓存是否有效"""
        if not self._statistics_cache_timestamp:
            return False
        
        elapsed = (datetime.now() - self._statistics_cache_timestamp).total_seconds()
        return elapsed < self._statistics_cache_ttl
    
    def _update_statistics_cache(self) -> None:
        """更新统计数据缓存"""
        summary = self.get_detection_summary()
        self.statistics_updated.emit(summary)
    
    # ===================
    # 应用程序状态管理
    # ===================
    
    def get_application_state(self, key: str) -> Any:
        """
        获取应用程序状态
        
        Args:
            key: 状态键
            
        Returns:
            Any: 状态值
        """
        return self._application_state.get(key)
    
    def set_application_state(self, key: str, value: Any) -> None:
        """
        设置应用程序状态
        
        Args:
            key: 状态键
            value: 状态值
        """
        old_value = self._application_state.get(key)
        if old_value != value:
            self._application_state[key] = value
            self.application_state_changed.emit(key, value)
            self._logger.debug(f"Application state changed: {key} = {value}")
    
    def get_application_config(self, key: str) -> Any:
        """
        获取应用程序配置
        
        Args:
            key: 配置键
            
        Returns:
            Any: 配置值
        """
        return self._application_config.get(key)
    
    def set_application_config(self, key: str, value: Any) -> None:
        """
        设置应用程序配置
        
        Args:
            key: 配置键
            value: 配置值
        """
        old_value = self._application_config.get(key)
        if old_value != value:
            self._application_config[key] = value
            self.configuration_changed.emit(key, {key: value})
            self._logger.debug(f"Application config changed: {key} = {value}")
    
    # ===================
    # 状态消息管理
    # ===================
    
    def set_status_message(self, message: str) -> None:
        """
        设置状态消息
        
        Args:
            message: 状态消息
        """
        self.status_message_changed.emit(message)
        self._logger.info(f"Status message: {message}")
    
    def report_error(self, error_type: str, message: str) -> None:
        """
        报告错误
        
        Args:
            error_type: 错误类型
            message: 错误消息
        """
        self.error_occurred.emit(error_type, message)
        self._logger.error(f"Error {error_type}: {message}")
    
    # ===================
    # 数据导出和导入
    # ===================
    
    def export_data(self) -> Dict[str, Any]:
        """
        导出应用程序数据
        
        Returns:
            Dict[str, Any]: 导出的数据
        """
        return {
            'workpiece_id': self._current_workpiece,
            'hole_collection': self._hole_collection.to_dict() if self._hole_collection else None,
            'selected_holes': list(self._selected_holes),
            'detection_results': self._detection_results,
            'detection_state': self._detection_state_manager.current_state.value,
            'application_state': self._application_state,
            'application_config': self._application_config,
            'export_timestamp': datetime.now().isoformat()
        }
    
    def import_data(self, data: Dict[str, Any]) -> bool:
        """
        导入应用程序数据
        
        Args:
            data: 要导入的数据
            
        Returns:
            bool: 导入是否成功
        """
        try:
            # 导入工件ID
            if 'workpiece_id' in data:
                self.current_workpiece = data['workpiece_id']
            
            # 导入孔位集合
            if 'hole_collection' in data and data['hole_collection']:
                # 这里需要实现从字典创建HoleCollection的逻辑
                # self.hole_collection = HoleCollection.from_dict(data['hole_collection'])
                pass
            
            # 导入选中的孔位
            if 'selected_holes' in data:
                self._selected_holes = set(data['selected_holes'])
            
            # 导入检测结果
            if 'detection_results' in data:
                self._detection_results = data['detection_results']
            
            # 导入检测状态
            if 'detection_state' in data:
                state = DetectionState.from_string(data['detection_state'])
                self._detection_state_manager.force_transition_to(state, "Data import")
            
            # 导入应用状态和配置
            if 'application_state' in data:
                self._application_state.update(data['application_state'])
            
            if 'application_config' in data:
                self._application_config.update(data['application_config'])
            
            # 更新统计数据
            self._update_statistics_cache()
            
            self._logger.info("Data imported successfully")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to import data: {e}")
            self.error_occurred.emit("data_import_error", str(e))
            return False
    
    # ===================
    # 资源清理
    # ===================
    
    def cleanup(self) -> None:
        """清理资源"""
        # 停止定时器
        if self._statistics_timer.isActive():
            self._statistics_timer.stop()
        
        # 清理数据
        self._clear_workpiece_data()
        self._application_state.clear()
        self._application_config.clear()
        
        # 清理回调
        self._data_change_listeners.clear()
        
        self._logger.info("ApplicationModel cleanup completed")
    
    def __del__(self):
        """析构函数"""
        self.cleanup()