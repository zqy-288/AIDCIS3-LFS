"""
事件总线实现
用于解耦组件间的通信
"""

from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from datetime import datetime
import weakref
from enum import Enum


class EventType(Enum):
    """事件类型枚举"""
    # 批次事件
    BATCH_CREATED = "batch.created"
    BATCH_STARTED = "batch.started"
    BATCH_PAUSED = "batch.paused"
    BATCH_RESUMED = "batch.resumed"
    BATCH_TERMINATED = "batch.terminated"
    BATCH_COMPLETED = "batch.completed"
    
    # 检测事件
    DETECTION_STARTED = "detection.started"
    DETECTION_PAUSED = "detection.paused"
    DETECTION_RESUMED = "detection.resumed"
    DETECTION_STOPPED = "detection.stopped"
    DETECTION_PROGRESS = "detection.progress"
    
    # 孔位事件
    HOLE_DETECTED = "hole.detected"
    HOLE_QUALIFIED = "hole.qualified"
    HOLE_DEFECTIVE = "hole.defective"
    
    # UI事件
    UI_PRODUCT_SELECTED = "ui.product_selected"
    UI_DXF_LOADED = "ui.dxf_loaded"
    UI_VIEW_CHANGED = "ui.view_changed"


@dataclass
class Event:
    """事件对象"""
    type: EventType
    data: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class EventBus:
    """事件总线"""
    
    def __init__(self):
        """初始化事件总线"""
        # 存储订阅信息：event_type -> [(handler, subscriber_ref)]
        self._subscriptions: Dict[EventType, List[tuple]] = {}
    
    def subscribe(self, event_type: EventType, handler: Callable[[Event], None], 
                 subscriber: Any = None) -> None:
        """
        订阅事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理函数
            subscriber: 订阅者对象（可选，用于自动清理）
        """
        if event_type not in self._subscriptions:
            self._subscriptions[event_type] = []
        
        # 如果提供了订阅者对象，创建弱引用
        if subscriber is not None:
            weak_ref = weakref.ref(subscriber)
            self._subscriptions[event_type].append((handler, weak_ref))
        else:
            # 没有订阅者，只存储handler
            self._subscriptions[event_type].append((handler, None))
    
    def unsubscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """
        取消订阅事件
        
        Args:
            event_type: 事件类型
            handler: 要移除的事件处理函数
        """
        if event_type in self._subscriptions:
            # 移除匹配的handler
            self._subscriptions[event_type] = [
                (h, ref) for h, ref in self._subscriptions[event_type]
                if h != handler
            ]
    
    def publish(self, event: Event) -> None:
        """
        发布事件
        
        Args:
            event: 要发布的事件
        """
        if event.type in self._subscriptions:
            # 过滤掉已经被垃圾回收的订阅者
            active_subscriptions = []
            
            for handler, subscriber_ref in self._subscriptions[event.type]:
                # 检查订阅者是否还存在
                if subscriber_ref is None or subscriber_ref() is not None:
                    # 订阅者还存在或没有订阅者引用
                    active_subscriptions.append((handler, subscriber_ref))
                    
                    # 调用handler
                    try:
                        handler(event)
                    except Exception as e:
                        print(f"事件处理出错: {event.type.value}, 错误: {e}")
            
            # 更新订阅列表，移除已经被垃圾回收的订阅
            self._subscriptions[event.type] = active_subscriptions
    
    def publish_async(self, event: Event) -> None:
        """
        异步发布事件（使用Qt的事件循环）
        
        Args:
            event: 要发布的事件
        """
        try:
            from PySide6.QtCore import QTimer
            QTimer.singleShot(0, lambda: self.publish(event))
        except ImportError:
            # 如果没有Qt，直接同步发布
            self.publish(event)
    
    
    def clear(self) -> None:
        """清空所有订阅"""
        self._subscriptions.clear()
    
    def get_subscriber_count(self, event_type: EventType) -> int:
        """获取指定事件类型的订阅者数量"""
        if event_type in self._subscriptions:
            # 只计算活跃的订阅（订阅者还存在的）
            count = 0
            for handler, subscriber_ref in self._subscriptions[event_type]:
                if subscriber_ref is None or subscriber_ref() is not None:
                    count += 1
            return count
        return 0


# 全局事件总线实例
_event_bus = None


def get_event_bus() -> EventBus:
    """获取全局事件总线实例"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


# 便捷函数
def publish_event(event_type: EventType, data: Dict[str, Any]) -> None:
    """发布事件的便捷函数"""
    event = Event(type=event_type, data=data)
    get_event_bus().publish(event)


def subscribe_event(event_type: EventType, handler: Callable[[Event], None], 
                   subscriber: Any = None) -> None:
    """订阅事件的便捷函数"""
    get_event_bus().subscribe(event_type, handler, subscriber)