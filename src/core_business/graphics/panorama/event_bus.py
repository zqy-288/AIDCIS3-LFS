"""
全景图事件总线
用于组件间的解耦通信
"""

from enum import Enum
from dataclasses import dataclass
from typing import Any, Callable, Dict, List
from PySide6.QtCore import QObject, Signal


class PanoramaEvent(Enum):
    """全景图事件类型"""
    # 数据相关事件
    DATA_LOADED = "data_loaded"
    DATA_CLEARED = "data_cleared"
    HOLE_STATUS_CHANGED = "hole_status_changed"
    
    # 交互相关事件
    SECTOR_CLICKED = "sector_clicked"
    SECTOR_HIGHLIGHTED = "sector_highlighted"
    HIGHLIGHT_CLEARED = "highlight_cleared"
    
    # 渲染相关事件
    GEOMETRY_CHANGED = "geometry_changed"
    RENDER_REQUESTED = "render_requested"
    THEME_CHANGED = "theme_changed"
    
    # 路径相关事件
    SNAKE_PATH_ENABLED = "snake_path_enabled"
    SNAKE_PATH_DISABLED = "snake_path_disabled"
    SNAKE_PATH_UPDATED = "snake_path_updated"


@dataclass
class EventData:
    """事件数据包装器"""
    event_type: PanoramaEvent
    data: Any = None
    sender: str = None  # 发送者标识


class PanoramaEventBus(QObject):
    """
    全景图事件总线
    提供发布-订阅模式的事件通信机制
    """
    
    # Qt信号用于线程安全
    event_published = Signal(EventData)
    
    def __init__(self):
        super().__init__()
        # 订阅者字典：事件类型 -> 回调函数列表
        self._subscribers: Dict[PanoramaEvent, List[Callable]] = {}
        
        # 连接Qt信号到分发方法
        self.event_published.connect(self._dispatch_event)
    
    def publish(self, event_type: PanoramaEvent, data: Any = None, sender: str = None) -> None:
        """
        发布事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
            sender: 发送者标识
        """
        event_data = EventData(event_type, data, sender)
        self.event_published.emit(event_data)
    
    def subscribe(self, event_type: PanoramaEvent, callback: Callable) -> None:
        """
        订阅特定事件
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: PanoramaEvent, callback: Callable) -> None:
        """
        取消订阅
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        if event_type in self._subscribers:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
    
    def subscribe_all(self, callback: Callable) -> None:
        """
        订阅所有事件
        
        Args:
            callback: 回调函数
        """
        self.event_published.connect(lambda event_data: callback(event_data))
    
    def _dispatch_event(self, event_data: EventData) -> None:
        """
        分发事件到订阅者
        
        Args:
            event_data: 事件数据
        """
        event_type = event_data.event_type
        
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(event_data)
                except Exception as e:
                    print(f"Event callback error for {event_type}: {e}")
    
    def clear_subscribers(self, event_type: PanoramaEvent = None) -> None:
        """
        清除订阅者
        
        Args:
            event_type: 事件类型，如果为None则清除所有
        """
        if event_type:
            self._subscribers.pop(event_type, None)
        else:
            self._subscribers.clear()