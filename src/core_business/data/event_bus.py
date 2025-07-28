"""
事件总线实现 - 用于解耦组件间通信
替代直接的信号连接和全局状态访问
"""

from typing import Dict, List, Callable, Any
from PySide6.QtCore import QObject, Signal
import weakref


class EventBus(QObject):
    """
    事件总线 - 发布/订阅模式实现
    支持弱引用以避免内存泄漏
    """
    
    # 通用事件信号
    event_published = Signal(str, object)  # event_type, data
    
    def __init__(self):
        super().__init__()
        self._handlers: Dict[str, List[weakref.ref]] = {}
        self._subscription_counter = 0
        self._subscriptions: Dict[str, tuple] = {}  # subscription_id -> (event_type, handler_ref)
    
    def publish(self, event_type: str, data: Any = None):
        """
        发布事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
        """
        # 发送Qt信号
        self.event_published.emit(event_type, data)
        
        # 调用注册的处理器
        if event_type in self._handlers:
            # 清理无效的弱引用
            valid_handlers = []
            for handler_ref in self._handlers[event_type]:
                handler = handler_ref()
                if handler:
                    try:
                        handler(data)
                    except Exception as e:
                        print(f"事件处理器错误 [{event_type}]: {e}")
                    valid_handlers.append(handler_ref)
            
            self._handlers[event_type] = valid_handlers
    
    def subscribe(self, event_type: str, handler: Callable[[Any], None]) -> str:
        """
        订阅事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理函数
            
        Returns:
            订阅ID
        """
        # 创建弱引用
        handler_ref = weakref.ref(handler)
        
        # 添加到处理器列表
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler_ref)
        
        # 生成订阅ID
        subscription_id = f"sub_{self._subscription_counter}"
        self._subscription_counter += 1
        self._subscriptions[subscription_id] = (event_type, handler_ref)
        
        return subscription_id
    
    def unsubscribe(self, subscription_id: str):
        """
        取消订阅
        
        Args:
            subscription_id: 订阅ID
        """
        if subscription_id in self._subscriptions:
            event_type, handler_ref = self._subscriptions.pop(subscription_id)
            
            # 从处理器列表中移除
            if event_type in self._handlers:
                try:
                    self._handlers[event_type].remove(handler_ref)
                except ValueError:
                    pass  # 处理器可能已经被垃圾回收
    
    def unsubscribe_all(self, event_type: str):
        """
        取消指定事件类型的所有订阅
        
        Args:
            event_type: 事件类型
        """
        if event_type in self._handlers:
            del self._handlers[event_type]
        
        # 清理订阅记录
        to_remove = []
        for sub_id, (evt_type, _) in self._subscriptions.items():
            if evt_type == event_type:
                to_remove.append(sub_id)
        
        for sub_id in to_remove:
            del self._subscriptions[sub_id]


class Events:
    """事件类型常量定义"""
    
    # 数据事件
    HOLE_COLLECTION_LOADED = "hole_collection_loaded"
    HOLE_STATUS_CHANGED = "hole_status_changed"
    SECTOR_ASSIGNMENTS_CHANGED = "sector_assignments_changed"
    
    # UI事件
    SECTOR_SELECTED = "sector_selected"
    ZOOM_CHANGED = "zoom_changed"
    VIEW_RESET = "view_reset"
    
    # 项目事件
    PROJECT_LOADED = "project_loaded"
    WORKPIECE_SELECTED = "workpiece_selected"
    DXF_LOADED = "dxf_loaded"
    
    # 检测事件
    DETECTION_STARTED = "detection_started"
    DETECTION_COMPLETED = "detection_completed"
    DETECTION_PROGRESS = "detection_progress"
    
    # 系统事件
    THEME_CHANGED = "theme_changed"
    LANGUAGE_CHANGED = "language_changed"
    ERROR_OCCURRED = "error_occurred"