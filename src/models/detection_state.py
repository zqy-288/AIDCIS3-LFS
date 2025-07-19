"""
检测状态枚举定义
定义应用程序中所有检测状态的枚举类型
"""

from enum import Enum, auto
from typing import Dict, List, Optional, Set
import logging
from PySide6.QtCore import QObject, Signal


class DetectionState(Enum):
    """
    检测状态枚举
    
    定义检测流程中的所有可能状态，用于状态机管理和UI显示。
    每个状态都有明确的含义和转换规则。
    """
    
    IDLE = "idle"
    """空闲状态 - 系统准备就绪，但未开始检测"""
    
    LOADING = "loading"
    """加载状态 - 正在加载工件数据或配置"""
    
    DETECTING = "detecting"
    """检测状态 - 正在进行检测"""
    
    PAUSED = "paused"
    """暂停状态 - 检测已暂停，可以恢复"""
    
    COMPLETED = "completed"
    """完成状态 - 检测已完成"""
    
    ERROR = "error"
    """错误状态 - 检测过程中发生错误"""
    
    PREPARING = "preparing"
    """准备状态 - 正在准备检测（设备初始化等）"""
    
    STOPPING = "stopping"
    """停止状态 - 正在停止检测"""
    
    CALIBRATING = "calibrating"
    """校准状态 - 正在进行设备校准"""
    
    def __str__(self) -> str:
        """返回状态的字符串表示"""
        return self.value
    
    def __repr__(self) -> str:
        """返回状态的详细字符串表示"""
        return f"DetectionState.{self.name}"
    
    @classmethod
    def from_string(cls, state_str: str) -> 'DetectionState':
        """
        从字符串创建检测状态
        
        Args:
            state_str: 状态字符串
            
        Returns:
            DetectionState: 对应的检测状态
            
        Raises:
            ValueError: 如果状态字符串无效
        """
        for state in cls:
            if state.value == state_str.lower():
                return state
        raise ValueError(f"Invalid detection state: {state_str}")
    
    @classmethod
    def get_all_states(cls) -> List['DetectionState']:
        """
        获取所有检测状态
        
        Returns:
            List[DetectionState]: 所有检测状态的列表
        """
        return list(cls)
    
    @classmethod
    def get_active_states(cls) -> List['DetectionState']:
        """
        获取活跃状态（非终止状态）
        
        Returns:
            List[DetectionState]: 活跃状态列表
        """
        return [
            cls.LOADING, cls.DETECTING, cls.PAUSED, 
            cls.PREPARING, cls.STOPPING, cls.CALIBRATING
        ]
    
    @classmethod
    def get_terminal_states(cls) -> List['DetectionState']:
        """
        获取终止状态
        
        Returns:
            List[DetectionState]: 终止状态列表
        """
        return [cls.IDLE, cls.COMPLETED, cls.ERROR]
    
    def is_active(self) -> bool:
        """
        判断是否为活跃状态
        
        Returns:
            bool: 是否为活跃状态
        """
        return self in self.get_active_states()
    
    def is_terminal(self) -> bool:
        """
        判断是否为终止状态
        
        Returns:
            bool: 是否为终止状态
        """
        return self in self.get_terminal_states()
    
    def can_transition_to(self, target_state: 'DetectionState') -> bool:
        """
        判断是否可以转换到目标状态
        
        Args:
            target_state: 目标状态
            
        Returns:
            bool: 是否可以转换
        """
        return target_state in self.get_valid_transitions()
    
    def get_valid_transitions(self) -> Set['DetectionState']:
        """
        获取当前状态可以转换到的有效状态集合
        
        Returns:
            Set[DetectionState]: 有效转换状态集合
        """
        transitions = {
            DetectionState.IDLE: {
                DetectionState.LOADING, DetectionState.PREPARING, 
                DetectionState.CALIBRATING
            },
            DetectionState.LOADING: {
                DetectionState.DETECTING, DetectionState.ERROR, 
                DetectionState.IDLE
            },
            DetectionState.PREPARING: {
                DetectionState.DETECTING, DetectionState.ERROR, 
                DetectionState.IDLE
            },
            DetectionState.CALIBRATING: {
                DetectionState.DETECTING, DetectionState.ERROR, 
                DetectionState.IDLE
            },
            DetectionState.DETECTING: {
                DetectionState.PAUSED, DetectionState.STOPPING, 
                DetectionState.COMPLETED, DetectionState.ERROR
            },
            DetectionState.PAUSED: {
                DetectionState.DETECTING, DetectionState.STOPPING, 
                DetectionState.ERROR
            },
            DetectionState.STOPPING: {
                DetectionState.IDLE, DetectionState.ERROR
            },
            DetectionState.COMPLETED: {
                DetectionState.IDLE, DetectionState.LOADING
            },
            DetectionState.ERROR: {
                DetectionState.IDLE, DetectionState.LOADING
            }
        }
        
        return transitions.get(self, set())
    
    def get_display_name(self) -> str:
        """
        获取用于显示的本地化名称
        
        Returns:
            str: 显示名称
        """
        display_names = {
            DetectionState.IDLE: "空闲",
            DetectionState.LOADING: "加载中",
            DetectionState.DETECTING: "检测中",
            DetectionState.PAUSED: "已暂停",
            DetectionState.COMPLETED: "已完成",
            DetectionState.ERROR: "错误",
            DetectionState.PREPARING: "准备中",
            DetectionState.STOPPING: "停止中",
            DetectionState.CALIBRATING: "校准中"
        }
        
        return display_names.get(self, self.value)
    
    def get_color(self) -> str:
        """
        获取状态对应的颜色代码（用于UI显示）
        
        Returns:
            str: 颜色代码
        """
        colors = {
            DetectionState.IDLE: "#28a745",      # 绿色
            DetectionState.LOADING: "#ffc107",    # 黄色
            DetectionState.DETECTING: "#007bff",  # 蓝色
            DetectionState.PAUSED: "#fd7e14",     # 橙色
            DetectionState.COMPLETED: "#28a745",  # 绿色
            DetectionState.ERROR: "#dc3545",      # 红色
            DetectionState.PREPARING: "#6f42c1",  # 紫色
            DetectionState.STOPPING: "#6c757d",   # 灰色
            DetectionState.CALIBRATING: "#17a2b8" # 青色
        }
        
        return colors.get(self, "#6c757d")
    
    def get_icon(self) -> str:
        """
        获取状态对应的图标名称
        
        Returns:
            str: 图标名称
        """
        icons = {
            DetectionState.IDLE: "play-circle",
            DetectionState.LOADING: "download",
            DetectionState.DETECTING: "activity",
            DetectionState.PAUSED: "pause-circle",
            DetectionState.COMPLETED: "check-circle",
            DetectionState.ERROR: "x-circle",
            DetectionState.PREPARING: "settings",
            DetectionState.STOPPING: "stop-circle",
            DetectionState.CALIBRATING: "target"
        }
        
        return icons.get(self, "help-circle")


class DetectionStateManager(QObject):
    """
    检测状态管理器
    
    负责管理检测状态的转换、验证和历史记录。
    提供状态变化的事件通知机制。
    """
    
    # 信号定义
    state_changed = Signal(str)  # 状态变化信号
    
    def __init__(self):
        """初始化状态管理器"""
        super().__init__()
        self._current_state: DetectionState = DetectionState.IDLE
        self._state_history: List[Dict] = []
        self._max_history_size: int = 100
        self._logger = logging.getLogger(__name__)
        
        # 状态变化回调函数列表
        self._state_change_callbacks: List[callable] = []
    
    @property
    def current_state(self) -> DetectionState:
        """获取当前状态"""
        return self._current_state
    
    def add_state_change_callback(self, callback: callable) -> None:
        """
        添加状态变化回调函数
        
        Args:
            callback: 回调函数，接收(old_state, new_state)参数
        """
        if callback not in self._state_change_callbacks:
            self._state_change_callbacks.append(callback)
    
    def remove_state_change_callback(self, callback: callable) -> None:
        """
        移除状态变化回调函数
        
        Args:
            callback: 要移除的回调函数
        """
        if callback in self._state_change_callbacks:
            self._state_change_callbacks.remove(callback)
    
    def transition_to(self, new_state: DetectionState, reason: str = "") -> bool:
        """
        转换到新状态
        
        Args:
            new_state: 目标状态
            reason: 转换原因
            
        Returns:
            bool: 转换是否成功
        """
        if not self._current_state.can_transition_to(new_state):
            self._logger.warning(
                f"Invalid state transition from {self._current_state} to {new_state}"
            )
            return False
        
        old_state = self._current_state
        self._current_state = new_state
        
        # 记录状态变化历史
        self._record_state_change(old_state, new_state, reason)
        
        # 通知状态变化回调
        self._notify_state_change(old_state, new_state)
        
        self._logger.info(
            f"State transition: {old_state} -> {new_state}"
            f"{f' ({reason})' if reason else ''}"
        )
        
        return True
    
    def force_transition_to(self, new_state: DetectionState, reason: str = "") -> None:
        """
        强制转换到新状态（忽略转换规则）
        
        Args:
            new_state: 目标状态
            reason: 转换原因
        """
        old_state = self._current_state
        self._current_state = new_state
        
        # 记录状态变化历史
        self._record_state_change(old_state, new_state, f"FORCED: {reason}")
        
        # 通知状态变化回调
        self._notify_state_change(old_state, new_state)
        
        self._logger.warning(
            f"Forced state transition: {old_state} -> {new_state}"
            f"{f' ({reason})' if reason else ''}"
        )
    
    def can_transition_to(self, target_state: DetectionState) -> bool:
        """
        检查是否可以转换到目标状态
        
        Args:
            target_state: 目标状态
            
        Returns:
            bool: 是否可以转换
        """
        return self._current_state.can_transition_to(target_state)
    
    def get_valid_transitions(self) -> Set[DetectionState]:
        """
        获取当前状态的有效转换状态
        
        Returns:
            Set[DetectionState]: 有效转换状态集合
        """
        return self._current_state.get_valid_transitions()
    
    def get_state_history(self) -> List[Dict]:
        """
        获取状态变化历史
        
        Returns:
            List[Dict]: 状态变化历史记录
        """
        return self._state_history.copy()
    
    def clear_state_history(self) -> None:
        """清空状态变化历史"""
        self._state_history.clear()
        self._logger.info("State history cleared")
    
    def reset_to_idle(self, reason: str = "Reset") -> bool:
        """
        重置到空闲状态
        
        Args:
            reason: 重置原因
            
        Returns:
            bool: 重置是否成功
        """
        if self._current_state == DetectionState.IDLE:
            return True
        
        # 如果是活跃状态，需要先停止
        if self._current_state.is_active():
            if not self.transition_to(DetectionState.STOPPING, "Reset requested"):
                return False
        
        return self.transition_to(DetectionState.IDLE, reason)
    
    def is_busy(self) -> bool:
        """
        判断是否处于忙碌状态
        
        Returns:
            bool: 是否忙碌
        """
        return self._current_state.is_active()
    
    def _record_state_change(self, old_state: DetectionState, 
                           new_state: DetectionState, reason: str) -> None:
        """
        记录状态变化历史
        
        Args:
            old_state: 旧状态
            new_state: 新状态
            reason: 变化原因
        """
        from datetime import datetime
        
        record = {
            'timestamp': datetime.now().isoformat(),
            'old_state': old_state.value,
            'new_state': new_state.value,
            'reason': reason
        }
        
        self._state_history.append(record)
        
        # 限制历史记录大小
        if len(self._state_history) > self._max_history_size:
            self._state_history.pop(0)
    
    def _notify_state_change(self, old_state: DetectionState, 
                           new_state: DetectionState) -> None:
        """
        通知状态变化回调
        
        Args:
            old_state: 旧状态
            new_state: 新状态
        """
        # 发射Qt信号
        self.state_changed.emit(new_state.value)
        
        # 调用回调函数
        for callback in self._state_change_callbacks:
            try:
                callback(old_state, new_state)
            except Exception as e:
                self._logger.error(f"State change callback error: {e}")
    
    def get_status_info(self) -> Dict:
        """
        获取状态管理器的状态信息
        
        Returns:
            Dict: 状态信息
        """
        return {
            'current_state': self._current_state.value,
            'display_name': self._current_state.get_display_name(),
            'color': self._current_state.get_color(),
            'icon': self._current_state.get_icon(),
            'is_active': self._current_state.is_active(),
            'is_terminal': self._current_state.is_terminal(),
            'valid_transitions': [state.value for state in self.get_valid_transitions()],
            'history_count': len(self._state_history)
        }