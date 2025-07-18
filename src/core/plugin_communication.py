"""
插件间通信机制
提供插件之间的消息传递、事件广播、服务调用等通信功能
"""

import asyncio
import threading
import time
import uuid
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Union, Type, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import logging
import weakref
import json

from .application import EventBus, ApplicationEvent
from .interfaces.plugin_interfaces import IPluginCommunicator


class MessageType(Enum):
    """消息类型"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    BROADCAST = "broadcast"
    EVENT = "event"
    SERVICE_CALL = "service_call"
    SERVICE_RESPONSE = "service_response"


class MessagePriority(Enum):
    """消息优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class DeliveryMode(Enum):
    """消息传递模式"""
    DIRECT = "direct"  # 直接传递
    QUEUED = "queued"  # 队列传递
    ASYNC = "async"    # 异步传递
    SYNC = "sync"      # 同步传递


@dataclass
class Message:
    """消息对象"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: MessageType = MessageType.NOTIFICATION
    sender: str = ""
    receiver: str = ""
    channel: str = "default"
    content: Any = None
    headers: Dict[str, Any] = field(default_factory=dict)
    priority: MessagePriority = MessagePriority.NORMAL
    delivery_mode: DeliveryMode = DeliveryMode.DIRECT
    timestamp: float = field(default_factory=time.time)
    expiry_time: Optional[float] = None
    reply_to: Optional[str] = None
    correlation_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def is_expired(self) -> bool:
        """检查消息是否过期"""
        if self.expiry_time is None:
            return False
        return time.time() > self.expiry_time
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'message_type': self.message_type.value,
            'sender': self.sender,
            'receiver': self.receiver,
            'channel': self.channel,
            'content': self.content,
            'headers': self.headers,
            'priority': self.priority.value,
            'delivery_mode': self.delivery_mode.value,
            'timestamp': self.timestamp,
            'expiry_time': self.expiry_time,
            'reply_to': self.reply_to,
            'correlation_id': self.correlation_id,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """从字典创建消息"""
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            message_type=MessageType(data.get('message_type', 'notification')),
            sender=data.get('sender', ''),
            receiver=data.get('receiver', ''),
            channel=data.get('channel', 'default'),
            content=data.get('content'),
            headers=data.get('headers', {}),
            priority=MessagePriority(data.get('priority', 2)),
            delivery_mode=DeliveryMode(data.get('delivery_mode', 'direct')),
            timestamp=data.get('timestamp', time.time()),
            expiry_time=data.get('expiry_time'),
            reply_to=data.get('reply_to'),
            correlation_id=data.get('correlation_id'),
            retry_count=data.get('retry_count', 0),
            max_retries=data.get('max_retries', 3)
        )


@dataclass
class ServiceDefinition:
    """服务定义"""
    name: str
    provider: str
    description: str = ""
    version: str = "1.0.0"
    methods: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    return_type: Optional[Type] = None
    is_async: bool = False
    timeout: float = 30.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'provider': self.provider,
            'description': self.description,
            'version': self.version,
            'methods': self.methods,
            'parameters': self.parameters,
            'return_type': str(self.return_type) if self.return_type else None,
            'is_async': self.is_async,
            'timeout': self.timeout
        }


class IMessageHandler(ABC):
    """消息处理器接口"""
    
    @abstractmethod
    def can_handle(self, message: Message) -> bool:
        """检查是否可以处理消息"""
        pass
    
    @abstractmethod
    def handle_message(self, message: Message) -> Optional[Message]:
        """处理消息，返回响应消息（如果有）"""
        pass
    
    @abstractmethod
    def get_priority(self) -> int:
        """获取处理器优先级"""
        pass


class IMessageFilter(ABC):
    """消息过滤器接口"""
    
    @abstractmethod
    def should_deliver(self, message: Message) -> bool:
        """检查是否应该传递消息"""
        pass


class MessageQueue:
    """消息队列"""
    
    def __init__(self, max_size: int = 1000):
        self._queue: deque = deque(maxlen=max_size)
        self._lock = threading.RLock()
        self._not_empty = threading.Condition(self._lock)
        self._stats = {
            'total_messages': 0,
            'delivered_messages': 0,
            'failed_messages': 0,
            'expired_messages': 0
        }
    
    def put(self, message: Message) -> bool:
        """添加消息到队列"""
        with self._lock:
            if message.is_expired():
                self._stats['expired_messages'] += 1
                return False
            
            # 按优先级插入
            inserted = False
            for i, existing_message in enumerate(self._queue):
                if message.priority.value > existing_message.priority.value:
                    self._queue.insert(i, message)
                    inserted = True
                    break
            
            if not inserted:
                self._queue.append(message)
            
            self._stats['total_messages'] += 1
            self._not_empty.notify()
            return True
    
    def get(self, timeout: Optional[float] = None) -> Optional[Message]:
        """从队列获取消息"""
        with self._not_empty:
            if not self._queue:
                if timeout is None:
                    self._not_empty.wait()
                else:
                    self._not_empty.wait(timeout)
            
            if self._queue:
                # 检查并移除过期消息
                while self._queue and self._queue[0].is_expired():
                    expired = self._queue.popleft()
                    self._stats['expired_messages'] += 1
                
                if self._queue:
                    return self._queue.popleft()
            
            return None
    
    def size(self) -> int:
        """获取队列大小"""
        with self._lock:
            return len(self._queue)
    
    def clear(self):
        """清空队列"""
        with self._lock:
            self._queue.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取队列统计"""
        with self._lock:
            return self._stats.copy()


class MessageRouter:
    """消息路由器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self._logger = logger or logging.getLogger(__name__)
        self._routes: Dict[str, List[str]] = defaultdict(list)  # channel -> [plugin_ids]
        self._plugin_channels: Dict[str, Set[str]] = defaultdict(set)  # plugin_id -> {channels}
        self._patterns: List[Tuple[str, Callable[[Message], List[str]]]] = []  # (pattern, resolver)
    
    def add_route(self, channel: str, plugin_id: str):
        """添加路由"""
        if plugin_id not in self._routes[channel]:
            self._routes[channel].append(plugin_id)
            self._plugin_channels[plugin_id].add(channel)
            
            if self._logger:
                self._logger.debug(f"Added route: {channel} -> {plugin_id}")
    
    def remove_route(self, channel: str, plugin_id: str):
        """移除路由"""
        if plugin_id in self._routes[channel]:
            self._routes[channel].remove(plugin_id)
            self._plugin_channels[plugin_id].discard(channel)
            
            if self._logger:
                self._logger.debug(f"Removed route: {channel} -> {plugin_id}")
    
    def add_pattern_route(self, pattern: str, resolver: Callable[[Message], List[str]]):
        """添加模式路由"""
        self._patterns.append((pattern, resolver))
    
    def route_message(self, message: Message) -> List[str]:
        """路由消息，返回目标插件列表"""
        targets = []
        
        # 直接目标
        if message.receiver:
            targets.append(message.receiver)
        
        # 频道路由
        if message.channel in self._routes:
            targets.extend(self._routes[message.channel])
        
        # 模式路由
        for pattern, resolver in self._patterns:
            try:
                pattern_targets = resolver(message)
                if pattern_targets:
                    targets.extend(pattern_targets)
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Pattern route error for {pattern}: {e}")
        
        # 去重
        return list(set(targets))
    
    def get_plugin_channels(self, plugin_id: str) -> Set[str]:
        """获取插件订阅的频道"""
        return self._plugin_channels.get(plugin_id, set()).copy()
    
    def get_channel_subscribers(self, channel: str) -> List[str]:
        """获取频道的订阅者"""
        return self._routes.get(channel, []).copy()


class ServiceRegistry:
    """服务注册表"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self._logger = logger or logging.getLogger(__name__)
        self._services: Dict[str, ServiceDefinition] = {}
        self._service_instances: Dict[str, Any] = {}
        self._lock = threading.RLock()
    
    def register_service(self, service_def: ServiceDefinition, instance: Any) -> bool:
        """注册服务"""
        try:
            with self._lock:
                self._services[service_def.name] = service_def
                self._service_instances[service_def.name] = instance
                
                if self._logger:
                    self._logger.info(f"Registered service: {service_def.name} by {service_def.provider}")
                
                return True
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to register service {service_def.name}: {e}")
            return False
    
    def unregister_service(self, service_name: str) -> bool:
        """注销服务"""
        try:
            with self._lock:
                if service_name in self._services:
                    del self._services[service_name]
                    del self._service_instances[service_name]
                    
                    if self._logger:
                        self._logger.info(f"Unregistered service: {service_name}")
                    
                    return True
                return False
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to unregister service {service_name}: {e}")
            return False
    
    def get_service(self, service_name: str) -> Optional[Tuple[ServiceDefinition, Any]]:
        """获取服务"""
        with self._lock:
            if service_name in self._services:
                return self._services[service_name], self._service_instances[service_name]
            return None
    
    def list_services(self, provider: Optional[str] = None) -> List[ServiceDefinition]:
        """列出服务"""
        with self._lock:
            services = list(self._services.values())
            if provider:
                services = [s for s in services if s.provider == provider]
            return services
    
    def find_services_by_method(self, method: str) -> List[ServiceDefinition]:
        """按方法查找服务"""
        with self._lock:
            return [s for s in self._services.values() if method in s.methods]


class PluginCommunicationHub(IPluginCommunicator):
    """插件通信中心"""
    
    def __init__(self, 
                 event_bus: Optional[EventBus] = None,
                 logger: Optional[logging.Logger] = None):
        self._event_bus = event_bus
        self._logger = logger or logging.getLogger(__name__)
        
        # 消息队列和路由
        self._message_queues: Dict[str, MessageQueue] = {}
        self._router = MessageRouter(logger)
        self._service_registry = ServiceRegistry(logger)
        
        # 消息处理
        self._handlers: Dict[str, List[IMessageHandler]] = defaultdict(list)  # plugin_id -> handlers
        self._filters: List[IMessageFilter] = []
        self._middleware: List[Callable[[Message], Message]] = []
        
        # 消息统计
        self._message_stats = {
            'total_sent': 0,
            'total_received': 0,
            'total_failed': 0,
            'total_expired': 0,
            'by_type': defaultdict(int),
            'by_plugin': defaultdict(int)
        }
        
        # 异步消息处理
        self._async_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._running = False
        self._worker_threads: List[threading.Thread] = []
        
        # 插件状态跟踪
        self._active_plugins: Set[str] = set()
        self._plugin_refs: Dict[str, weakref.ref] = {}
        
        if self._logger:
            self._logger.info("PluginCommunicationHub initialized")
    
    def start(self):
        """启动通信中心"""
        if self._running:
            return
        
        self._running = True
        
        # 启动消息处理工作线程
        for i in range(3):  # 启动3个工作线程
            worker = threading.Thread(target=self._message_worker, name=f"MessageWorker-{i}")
            worker.daemon = True
            worker.start()
            self._worker_threads.append(worker)
        
        if self._logger:
            self._logger.info("PluginCommunicationHub started")
    
    def stop(self):
        """停止通信中心"""
        if not self._running:
            return
        
        self._running = False
        
        # 等待工作线程结束
        for worker in self._worker_threads:
            worker.join(timeout=5.0)
        
        self._worker_threads.clear()
        
        if self._logger:
            self._logger.info("PluginCommunicationHub stopped")
    
    def register_plugin(self, plugin_id: str, plugin_ref: Any = None):
        """注册插件"""
        self._active_plugins.add(plugin_id)
        
        if plugin_ref:
            self._plugin_refs[plugin_id] = weakref.ref(plugin_ref)
        
        # 为插件创建消息队列
        if plugin_id not in self._message_queues:
            self._message_queues[plugin_id] = MessageQueue()
        
        if self._logger:
            self._logger.info(f"Registered plugin for communication: {plugin_id}")
    
    def unregister_plugin(self, plugin_id: str):
        """注销插件"""
        self._active_plugins.discard(plugin_id)
        self._plugin_refs.pop(plugin_id, None)
        
        # 清理消息队列
        if plugin_id in self._message_queues:
            self._message_queues[plugin_id].clear()
            del self._message_queues[plugin_id]
        
        # 清理处理器
        self._handlers.pop(plugin_id, None)
        self._async_handlers.pop(plugin_id, None)
        
        # 清理路由
        for channel in self._router.get_plugin_channels(plugin_id):
            self._router.remove_route(channel, plugin_id)
        
        # 注销插件提供的服务
        services_to_remove = []
        for service_def in self._service_registry.list_services():
            if service_def.provider == plugin_id:
                services_to_remove.append(service_def.name)
        
        for service_name in services_to_remove:
            self._service_registry.unregister_service(service_name)
        
        if self._logger:
            self._logger.info(f"Unregistered plugin from communication: {plugin_id}")
    
    # IPluginCommunicator接口实现
    def send_message(self, target_plugin: str, message: Any) -> bool:
        """发送消息到目标插件"""
        try:
            if isinstance(message, Message):
                msg = message
            else:
                msg = Message(
                    message_type=MessageType.NOTIFICATION,
                    receiver=target_plugin,
                    content=message
                )
            
            return self._deliver_message(msg)
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to send message to {target_plugin}: {e}")
            return False
    
    def broadcast_message(self, message: Any, plugin_type: str = None) -> None:
        """广播消息"""
        try:
            if isinstance(message, Message):
                msg = message
            else:
                msg = Message(
                    message_type=MessageType.BROADCAST,
                    content=message
                )
            
            # 获取目标插件列表
            targets = list(self._active_plugins)
            
            # 如果指定了插件类型，需要过滤（这里简化处理）
            if plugin_type:
                # 实际实现中需要根据插件类型过滤
                pass
            
            # 发送给所有目标
            for target in targets:
                target_msg = Message(
                    message_type=msg.message_type,
                    sender=msg.sender,
                    receiver=target,
                    channel=msg.channel,
                    content=msg.content,
                    headers=msg.headers.copy(),
                    priority=msg.priority,
                    delivery_mode=msg.delivery_mode
                )
                self._deliver_message(target_msg)
                
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to broadcast message: {e}")
    
    def register_message_handler(self, message_type: str, handler: Callable) -> None:
        """注册消息处理器"""
        # 这里需要知道是哪个插件注册的处理器
        # 简化实现，使用默认插件ID
        plugin_id = "default"
        
        # 创建处理器包装器
        class HandlerWrapper(IMessageHandler):
            def __init__(self, handler_func):
                self.handler_func = handler_func
            
            def can_handle(self, message: Message) -> bool:
                return message.message_type.value == message_type
            
            def handle_message(self, message: Message) -> Optional[Message]:
                try:
                    result = self.handler_func(message.content)
                    if result is not None:
                        return Message(
                            message_type=MessageType.RESPONSE,
                            sender=plugin_id,
                            receiver=message.sender,
                            content=result,
                            correlation_id=message.id
                        )
                except Exception as e:
                    if self._logger:
                        self._logger.error(f"Message handler error: {e}")
                return None
            
            def get_priority(self) -> int:
                return 100
        
        wrapper = HandlerWrapper(handler)
        self._handlers[plugin_id].append(wrapper)
        
        if self._logger:
            self._logger.debug(f"Registered message handler for type: {message_type}")
    
    def unregister_message_handler(self, message_type: str, handler: Callable) -> None:
        """注销消息处理器"""
        # 简化实现
        plugin_id = "default"
        handlers = self._handlers.get(plugin_id, [])
        
        # 移除对应的处理器（这里简化处理）
        self._handlers[plugin_id] = [h for h in handlers if h.handler_func != handler]
    
    # 高级通信功能
    def send_request(self, target_plugin: str, request: Any, 
                    timeout: float = 30.0) -> Optional[Any]:
        """发送请求并等待响应"""
        try:
            correlation_id = str(uuid.uuid4())
            
            # 创建请求消息
            request_msg = Message(
                message_type=MessageType.REQUEST,
                receiver=target_plugin,
                content=request,
                correlation_id=correlation_id,
                reply_to="response_handler"
            )
            
            # 创建响应等待机制
            response_event = threading.Event()
            response_data = {'result': None}
            
            def response_handler(message: Message):
                if message.correlation_id == correlation_id:
                    response_data['result'] = message.content
                    response_event.set()
            
            # 注册临时响应处理器
            self._temp_response_handlers = getattr(self, '_temp_response_handlers', {})
            self._temp_response_handlers[correlation_id] = response_handler
            
            # 发送请求
            if self._deliver_message(request_msg):
                # 等待响应
                if response_event.wait(timeout):
                    return response_data['result']
                else:
                    if self._logger:
                        self._logger.warning(f"Request to {target_plugin} timed out")
            
            return None
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to send request to {target_plugin}: {e}")
            return None
        finally:
            # 清理临时处理器
            self._temp_response_handlers.pop(correlation_id, None)
    
    def subscribe_channel(self, plugin_id: str, channel: str):
        """订阅频道"""
        self._router.add_route(channel, plugin_id)
        
        if self._logger:
            self._logger.debug(f"Plugin {plugin_id} subscribed to channel: {channel}")
    
    def unsubscribe_channel(self, plugin_id: str, channel: str):
        """取消订阅频道"""
        self._router.remove_route(channel, plugin_id)
        
        if self._logger:
            self._logger.debug(f"Plugin {plugin_id} unsubscribed from channel: {channel}")
    
    def publish_to_channel(self, channel: str, message: Any, sender: str = ""):
        """发布消息到频道"""
        try:
            msg = Message(
                message_type=MessageType.BROADCAST,
                sender=sender,
                channel=channel,
                content=message
            )
            
            # 获取频道订阅者
            subscribers = self._router.get_channel_subscribers(channel)
            
            # 发送给所有订阅者
            for subscriber in subscribers:
                target_msg = Message(
                    message_type=msg.message_type,
                    sender=msg.sender,
                    receiver=subscriber,
                    channel=msg.channel,
                    content=msg.content,
                    headers=msg.headers.copy()
                )
                self._deliver_message(target_msg)
                
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to publish to channel {channel}: {e}")
    
    # 服务调用功能
    def register_service(self, service_name: str, service_instance: Any, 
                        provider: str, description: str = "", 
                        methods: List[str] = None) -> bool:
        """注册服务"""
        try:
            service_def = ServiceDefinition(
                name=service_name,
                provider=provider,
                description=description,
                methods=methods or [],
                is_async=asyncio.iscoroutinefunction(getattr(service_instance, methods[0], None)) if methods else False
            )
            
            return self._service_registry.register_service(service_def, service_instance)
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to register service {service_name}: {e}")
            return False
    
    def unregister_service(self, service_name: str) -> bool:
        """注销服务"""
        return self._service_registry.unregister_service(service_name)
    
    def call_service(self, service_name: str, method: str, 
                    args: List[Any] = None, kwargs: Dict[str, Any] = None,
                    timeout: float = 30.0) -> Any:
        """调用服务"""
        try:
            service_info = self._service_registry.get_service(service_name)
            if not service_info:
                raise RuntimeError(f"Service {service_name} not found")
            
            service_def, service_instance = service_info
            
            if method not in service_def.methods:
                raise RuntimeError(f"Method {method} not found in service {service_name}")
            
            # 获取方法
            service_method = getattr(service_instance, method)
            if not service_method:
                raise RuntimeError(f"Method {method} not implemented in service {service_name}")
            
            # 调用方法
            if args is None:
                args = []
            if kwargs is None:
                kwargs = {}
            
            if service_def.is_async:
                # 异步调用
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(
                    asyncio.wait_for(service_method(*args, **kwargs), timeout)
                )
            else:
                # 同步调用
                return service_method(*args, **kwargs)
                
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to call service {service_name}.{method}: {e}")
            raise
    
    def list_services(self, provider: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出可用服务"""
        services = self._service_registry.list_services(provider)
        return [service.to_dict() for service in services]
    
    # 消息处理
    def _deliver_message(self, message: Message) -> bool:
        """传递消息"""
        try:
            # 应用中间件
            for middleware in self._middleware:
                message = middleware(message)
                if message is None:
                    return False
            
            # 应用过滤器
            for filter_obj in self._filters:
                if not filter_obj.should_deliver(message):
                    return False
            
            # 更新统计
            self._update_message_stats(message, 'sent')
            
            # 根据传递模式处理
            if message.delivery_mode == DeliveryMode.DIRECT:
                return self._deliver_direct(message)
            elif message.delivery_mode == DeliveryMode.QUEUED:
                return self._deliver_queued(message)
            elif message.delivery_mode == DeliveryMode.ASYNC:
                return self._deliver_async(message)
            elif message.delivery_mode == DeliveryMode.SYNC:
                return self._deliver_sync(message)
            else:
                return self._deliver_direct(message)
                
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to deliver message {message.id}: {e}")
            self._update_message_stats(message, 'failed')
            return False
    
    def _deliver_direct(self, message: Message) -> bool:
        """直接传递消息"""
        # 路由消息
        targets = self._router.route_message(message)
        
        if not targets:
            if self._logger:
                self._logger.warning(f"No targets found for message {message.id}")
            return False
        
        success = True
        for target in targets:
            if not self._deliver_to_plugin(message, target):
                success = False
        
        return success
    
    def _deliver_queued(self, message: Message) -> bool:
        """队列传递消息"""
        targets = self._router.route_message(message)
        
        for target in targets:
            if target in self._message_queues:
                self._message_queues[target].put(message)
            else:
                if self._logger:
                    self._logger.warning(f"No queue found for plugin: {target}")
                return False
        
        return True
    
    def _deliver_async(self, message: Message) -> bool:
        """异步传递消息"""
        # 简化实现，使用线程池
        def async_deliver():
            self._deliver_direct(message)
        
        thread = threading.Thread(target=async_deliver)
        thread.daemon = True
        thread.start()
        
        return True
    
    def _deliver_sync(self, message: Message) -> bool:
        """同步传递消息"""
        return self._deliver_direct(message)
    
    def _deliver_to_plugin(self, message: Message, plugin_id: str) -> bool:
        """传递消息到特定插件"""
        try:
            # 查找插件的消息处理器
            handlers = self._handlers.get(plugin_id, [])
            
            handled = False
            for handler in handlers:
                if handler.can_handle(message):
                    response = handler.handle_message(message)
                    handled = True
                    
                    # 如果有响应，发送回复
                    if response and message.reply_to:
                        self._deliver_message(response)
            
            if not handled:
                # 如果没有处理器，尝试放入队列
                if plugin_id in self._message_queues:
                    self._message_queues[plugin_id].put(message)
                    handled = True
            
            if handled:
                self._update_message_stats(message, 'received')
            
            return handled
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to deliver message to plugin {plugin_id}: {e}")
            return False
    
    def _message_worker(self):
        """消息处理工作线程"""
        while self._running:
            try:
                # 处理所有插件的队列
                for plugin_id, queue in self._message_queues.items():
                    if not self._running:
                        break
                    
                    message = queue.get(timeout=0.1)
                    if message:
                        self._deliver_to_plugin(message, plugin_id)
                
                time.sleep(0.01)  # 短暂休眠避免CPU占用过高
                
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Message worker error: {e}")
    
    def _update_message_stats(self, message: Message, action: str):
        """更新消息统计"""
        if action == 'sent':
            self._message_stats['total_sent'] += 1
        elif action == 'received':
            self._message_stats['total_received'] += 1
        elif action == 'failed':
            self._message_stats['total_failed'] += 1
        elif action == 'expired':
            self._message_stats['total_expired'] += 1
        
        self._message_stats['by_type'][message.message_type.value] += 1
        self._message_stats['by_plugin'][message.sender] += 1
    
    # 查询和管理
    def get_message_stats(self) -> Dict[str, Any]:
        """获取消息统计"""
        stats = self._message_stats.copy()
        
        # 添加队列统计
        queue_stats = {}
        for plugin_id, queue in self._message_queues.items():
            queue_stats[plugin_id] = queue.get_stats()
        
        stats['queue_stats'] = queue_stats
        return stats
    
    def get_active_plugins(self) -> List[str]:
        """获取活跃插件列表"""
        return list(self._active_plugins)
    
    def add_message_filter(self, filter_obj: IMessageFilter):
        """添加消息过滤器"""
        self._filters.append(filter_obj)
    
    def remove_message_filter(self, filter_obj: IMessageFilter):
        """移除消息过滤器"""
        try:
            self._filters.remove(filter_obj)
        except ValueError:
            pass
    
    def add_middleware(self, middleware: Callable[[Message], Message]):
        """添加中间件"""
        self._middleware.append(middleware)
    
    def remove_middleware(self, middleware: Callable[[Message], Message]):
        """移除中间件"""
        try:
            self._middleware.remove(middleware)
        except ValueError:
            pass


# 便捷函数
def create_communication_hub(event_bus: Optional[EventBus] = None,
                           logger: Optional[logging.Logger] = None) -> PluginCommunicationHub:
    """创建插件通信中心"""
    return PluginCommunicationHub(event_bus, logger)


def create_message(message_type: MessageType = MessageType.NOTIFICATION,
                  sender: str = "", receiver: str = "", content: Any = None,
                  channel: str = "default", priority: MessagePriority = MessagePriority.NORMAL) -> Message:
    """创建消息"""
    return Message(
        message_type=message_type,
        sender=sender,
        receiver=receiver,
        content=content,
        channel=channel,
        priority=priority
    )