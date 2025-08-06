"""
UI组件基类和生命周期管理系统
集成依赖注入框架，提供标准化的组件生命周期管理
"""

import gc
import weakref
import threading
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, List, Optional, Set, Callable, Type
from datetime import datetime

from PySide6.QtCore import QObject, Signal, QTimer, Qt
from PySide6.QtWidgets import QWidget

try:
    from ..core.dependency_injection import DependencyContainer, injectable, ServiceLifetime
except ImportError:
    # 从项目根目录运行时的导入路径
    from core.dependency_injection import DependencyContainer, injectable, ServiceLifetime


class ComponentState(Enum):
    """组件状态枚举"""
    UNINITIALIZED = "uninitialized"  # 未初始化
    INITIALIZING = "initializing"    # 初始化中
    INITIALIZED = "initialized"      # 已初始化
    STARTING = "starting"            # 启动中
    RUNNING = "running"              # 运行中
    STOPPING = "stopping"            # 停止中
    STOPPED = "stopped"              # 已停止
    ERROR = "error"                  # 错误状态
    DESTROYED = "destroyed"          # 已销毁


class ComponentLifecycleEvent(Enum):
    """组件生命周期事件"""
    BEFORE_INIT = "before_init"
    AFTER_INIT = "after_init"
    BEFORE_START = "before_start"
    AFTER_START = "after_start"
    BEFORE_STOP = "before_stop"
    AFTER_STOP = "after_stop"
    BEFORE_CLEANUP = "before_cleanup"
    AFTER_CLEANUP = "after_cleanup"
    STATE_CHANGED = "state_changed"
    ERROR_OCCURRED = "error_occurred"


class UIComponentError(Exception):
    """UI组件异常基类"""
    pass


class ComponentStateError(UIComponentError):
    """组件状态异常"""
    pass


class ComponentDependencyError(UIComponentError):
    """组件依赖异常"""
    pass


# 解决QObject和ABC的metaclass冲突
class QObjectABCMeta(type(QObject), type(ABC)):
    pass


class IUIComponent(ABC):
    """UI组件接口定义"""
    
    @abstractmethod
    def initialize(self) -> bool:
        """初始化组件"""
        pass
    
    @abstractmethod
    def start(self) -> bool:
        """启动组件"""
        pass
    
    @abstractmethod
    def stop(self) -> bool:
        """停止组件"""
        pass
    
    @abstractmethod
    def cleanup(self) -> bool:
        """清理组件资源"""
        pass
    
    @abstractmethod
    def get_state(self) -> ComponentState:
        """获取组件状态"""
        pass


class UIComponentBase(QObject, IUIComponent, metaclass=QObjectABCMeta):
    """UI组件基类
    
    提供标准化的组件生命周期管理、依赖注入集成、事件通信和内存管理
    """
    
    # 组件生命周期信号
    state_changed = Signal(ComponentState, ComponentState)  # 状态变更信号 (from_state, to_state)
    lifecycle_event = Signal(ComponentLifecycleEvent, object)  # 生命周期事件信号
    error_occurred = Signal(str, Exception)  # 错误信号
    dependency_ready = Signal(str)  # 依赖就绪信号
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # 组件基本信息
        self.component_id = f"{self.__class__.__name__}_{id(self)}"
        self.component_name = self.__class__.__name__
        self.created_at = datetime.now()
        
        # 状态管理
        self._state = ComponentState.UNINITIALIZED
        self._previous_state = None
        self._state_lock = threading.RLock()
        
        # 生命周期管理
        self._initialized = False
        self._started = False
        self._cleanup_called = False
        self._destroyed = False
        
        # 依赖管理
        self._dependencies: Dict[str, Any] = {}
        self._dependency_types: Dict[str, Type] = {}
        self._required_dependencies: Set[str] = set()
        self._optional_dependencies: Set[str] = set()
        self._dependency_ready_flags: Dict[str, bool] = {}
        
        # 事件和信号管理
        self._signal_connections: List[tuple] = []
        self._event_listeners: Dict[ComponentLifecycleEvent, List[Callable]] = {}
        self._child_components: weakref.WeakSet = weakref.WeakSet()
        
        # 内存管理
        self._widget_refs = weakref.WeakSet()
        
        # 性能监控
        self._performance_metrics = {
            'init_time': 0.0,
            'start_time': 0.0,
            'stop_time': 0.0,
            'cleanup_time': 0.0
        }
        
        # 获取依赖注入容器
        self._di_container = DependencyContainer()
        
        # 注册到内存监控
        self._register_to_memory_monitor()
        
        # 初始化组件声明的依赖
        self._initialize_dependencies()
        
        print(f"🔧 创建UI组件: {self.component_id}")
    
    def _register_to_memory_monitor(self):
        """注册到内存监控系统"""
        try:
            from .memory_monitor import register_widget_for_monitoring
            if isinstance(self.parent(), QWidget):
                register_widget_for_monitoring(self.parent())
        except ImportError:
            pass
    
    def _initialize_dependencies(self):
        """初始化组件依赖声明"""
        # 子类可以重写此方法来声明依赖
        pass
    
    def declare_dependency(self, 
                          name: str, 
                          dependency_type: Type, 
                          required: bool = True):
        """声明组件依赖
        
        Args:
            name: 依赖名称
            dependency_type: 依赖类型
            required: 是否为必需依赖
        """
        self._dependency_types[name] = dependency_type
        self._dependency_ready_flags[name] = False
        
        if required:
            self._required_dependencies.add(name)
        else:
            self._optional_dependencies.add(name)
        
        # 尝试从DI容器解析依赖
        self._resolve_dependency(name)
    
    def _resolve_dependency(self, name: str) -> bool:
        """解析单个依赖"""
        try:
            dependency_type = self._dependency_types[name]
            if self._di_container.is_registered(dependency_type):
                self._dependencies[name] = self._di_container.resolve(dependency_type)
                self._dependency_ready_flags[name] = True
                self.dependency_ready.emit(name)
                print(f"✅ 解析依赖成功: {name} -> {dependency_type.__name__}")
                return True
        except Exception as e:
            print(f"❌ 解析依赖失败: {name} -> {e}")
            return False
        return False
    
    def get_dependency(self, name: str) -> Optional[Any]:
        """获取依赖实例"""
        return self._dependencies.get(name)
    
    def has_dependency(self, name: str) -> bool:
        """检查是否有指定依赖"""
        return name in self._dependencies
    
    def are_required_dependencies_ready(self) -> bool:
        """检查所有必需依赖是否就绪"""
        for dep_name in self._required_dependencies:
            if not self._dependency_ready_flags.get(dep_name, False):
                return False
        return True
    
    def _connect_signal(self, signal, slot) -> Optional[object]:
        """安全连接信号并跟踪连接"""
        try:
            connection = signal.connect(slot)
            self._signal_connections.append((signal, slot, connection))
            return connection
        except Exception as e:
            print(f"❌ 信号连接失败: {e}")
            return None
    
    def _disconnect_all_signals(self):
        """断开所有信号连接"""
        for signal, slot, connection in self._signal_connections:
            try:
                signal.disconnect(slot)
            except:
                pass
        self._signal_connections.clear()
    
    def add_event_listener(self, 
                          event: ComponentLifecycleEvent, 
                          listener: Callable):
        """添加生命周期事件监听器"""
        if event not in self._event_listeners:
            self._event_listeners[event] = []
        self._event_listeners[event].append(listener)
    
    def remove_event_listener(self, 
                             event: ComponentLifecycleEvent, 
                             listener: Callable):
        """移除生命周期事件监听器"""
        if event in self._event_listeners:
            try:
                self._event_listeners[event].remove(listener)
            except ValueError:
                pass
    
    def _fire_event(self, event: ComponentLifecycleEvent, data: Any = None):
        """触发生命周期事件"""
        # 触发信号
        self.lifecycle_event.emit(event, data)
        
        # 触发监听器
        if event in self._event_listeners:
            for listener in self._event_listeners[event]:
                try:
                    listener(self, event, data)
                except Exception as e:
                    print(f"❌ 事件监听器执行失败: {e}")
    
    def _set_state(self, new_state: ComponentState):
        """设置组件状态"""
        with self._state_lock:
            if self._state != new_state:
                old_state = self._state
                self._previous_state = old_state
                self._state = new_state
                
                print(f"🔄 组件状态变更: {self.component_id} {old_state.value} -> {new_state.value}")
                
                # 触发状态变更事件
                self.state_changed.emit(old_state, new_state)
                self._fire_event(ComponentLifecycleEvent.STATE_CHANGED, {
                    'from_state': old_state,
                    'to_state': new_state
                })
    
    def get_state(self) -> ComponentState:
        """获取组件当前状态"""
        return self._state
    
    def is_state(self, state: ComponentState) -> bool:
        """检查是否为指定状态"""
        return self._state == state
    
    def can_transition_to(self, target_state: ComponentState) -> bool:
        """检查是否可以转换到目标状态"""
        current = self._state
        
        # 定义状态转换规则
        valid_transitions = {
            ComponentState.UNINITIALIZED: [ComponentState.INITIALIZING, ComponentState.ERROR],
            ComponentState.INITIALIZING: [ComponentState.INITIALIZED, ComponentState.ERROR],
            ComponentState.INITIALIZED: [ComponentState.STARTING, ComponentState.DESTROYED, ComponentState.ERROR],
            ComponentState.STARTING: [ComponentState.RUNNING, ComponentState.ERROR],
            ComponentState.RUNNING: [ComponentState.STOPPING, ComponentState.ERROR],
            ComponentState.STOPPING: [ComponentState.STOPPED, ComponentState.ERROR],
            ComponentState.STOPPED: [ComponentState.STARTING, ComponentState.DESTROYED, ComponentState.ERROR],
            ComponentState.ERROR: [ComponentState.DESTROYED],
            ComponentState.DESTROYED: []  # 最终状态
        }
        
        return target_state in valid_transitions.get(current, [])
    
    def initialize(self) -> bool:
        """初始化组件"""
        if self._initialized:
            return True
        
        if not self.can_transition_to(ComponentState.INITIALIZING):
            raise ComponentStateError(f"无法从状态 {self._state} 转换到 INITIALIZING")
        
        self._set_state(ComponentState.INITIALIZING)
        self._fire_event(ComponentLifecycleEvent.BEFORE_INIT)
        
        start_time = datetime.now()
        
        try:
            # 检查必需依赖
            if not self.are_required_dependencies_ready():
                missing_deps = [name for name in self._required_dependencies 
                              if not self._dependency_ready_flags.get(name, False)]
                raise ComponentDependencyError(f"缺少必需依赖: {missing_deps}")
            
            # 执行初始化
            success = self._do_initialize()
            
            if success:
                self._initialized = True
                self._set_state(ComponentState.INITIALIZED)
                self._fire_event(ComponentLifecycleEvent.AFTER_INIT)
                
                # 记录性能指标
                self._performance_metrics['init_time'] = (datetime.now() - start_time).total_seconds()
                
                print(f"✅ 组件初始化完成: {self.component_id}")
                return True
            else:
                self._set_state(ComponentState.ERROR)
                return False
                
        except Exception as e:
            self._set_state(ComponentState.ERROR)
            self.error_occurred.emit(f"初始化失败: {str(e)}", e)
            self._fire_event(ComponentLifecycleEvent.ERROR_OCCURRED, e)
            print(f"❌ 组件初始化失败: {self.component_id} -> {e}")
            return False
    
    @abstractmethod
    def _do_initialize(self) -> bool:
        """子类实现的初始化逻辑"""
        pass
    
    def start(self) -> bool:
        """启动组件"""
        if self._started:
            return True
        
        if not self._initialized:
            if not self.initialize():
                return False
        
        if not self.can_transition_to(ComponentState.STARTING):
            raise ComponentStateError(f"无法从状态 {self._state} 转换到 STARTING")
        
        self._set_state(ComponentState.STARTING)
        self._fire_event(ComponentLifecycleEvent.BEFORE_START)
        
        start_time = datetime.now()
        
        try:
            success = self._do_start()
            
            if success:
                self._started = True
                self._set_state(ComponentState.RUNNING)
                self._fire_event(ComponentLifecycleEvent.AFTER_START)
                
                # 记录性能指标
                self._performance_metrics['start_time'] = (datetime.now() - start_time).total_seconds()
                
                print(f"✅ 组件启动完成: {self.component_id}")
                return True
            else:
                self._set_state(ComponentState.ERROR)
                return False
                
        except Exception as e:
            self._set_state(ComponentState.ERROR)
            self.error_occurred.emit(f"启动失败: {str(e)}", e)
            self._fire_event(ComponentLifecycleEvent.ERROR_OCCURRED, e)
            print(f"❌ 组件启动失败: {self.component_id} -> {e}")
            return False
    
    @abstractmethod
    def _do_start(self) -> bool:
        """子类实现的启动逻辑"""
        pass
    
    def stop(self) -> bool:
        """停止组件"""
        if not self._started:
            return True
        
        if not self.can_transition_to(ComponentState.STOPPING):
            return True  # 已经停止状态
        
        self._set_state(ComponentState.STOPPING)
        self._fire_event(ComponentLifecycleEvent.BEFORE_STOP)
        
        start_time = datetime.now()
        
        try:
            success = self._do_stop()
            
            if success:
                self._started = False
                self._set_state(ComponentState.STOPPED)
                self._fire_event(ComponentLifecycleEvent.AFTER_STOP)
                
                # 记录性能指标
                self._performance_metrics['stop_time'] = (datetime.now() - start_time).total_seconds()
                
                print(f"✅ 组件停止完成: {self.component_id}")
                return True
            else:
                self._set_state(ComponentState.ERROR)
                return False
                
        except Exception as e:
            self._set_state(ComponentState.ERROR)
            self.error_occurred.emit(f"停止失败: {str(e)}", e)
            self._fire_event(ComponentLifecycleEvent.ERROR_OCCURRED, e)
            print(f"❌ 组件停止失败: {self.component_id} -> {e}")
            return False
    
    @abstractmethod
    def _do_stop(self) -> bool:
        """子类实现的停止逻辑"""
        pass
    
    def cleanup(self) -> bool:
        """清理组件资源"""
        if self._cleanup_called:
            return True
        
        self._cleanup_called = True
        self._fire_event(ComponentLifecycleEvent.BEFORE_CLEANUP)
        
        start_time = datetime.now()
        
        try:
            # 先停止组件
            if self._started:
                self.stop()
            
            # 执行清理
            success = self._do_cleanup()
            
            if success:
                # 断开所有信号连接
                self._disconnect_all_signals()
                
                # 清理子组件
                for child in list(self._child_components):
                    if hasattr(child, 'cleanup'):
                        child.cleanup()
                
                # 清理依赖
                self._dependencies.clear()
                self._dependency_ready_flags.clear()
                
                # 清理事件监听器
                self._event_listeners.clear()
                
                # 清理弱引用
                self._widget_refs.clear()
                self._child_components.clear()
                
                # 从内存监控中移除
                try:
                    from .memory_monitor import unregister_widget_from_monitoring
                    if isinstance(self.parent(), QWidget):
                        unregister_widget_from_monitoring(self.parent())
                except ImportError:
                    pass
                
                # 设置为销毁状态
                self._set_state(ComponentState.DESTROYED)
                self._destroyed = True
                
                # 强制垃圾回收
                gc.collect()
                
                # 记录性能指标
                self._performance_metrics['cleanup_time'] = (datetime.now() - start_time).total_seconds()
                
                self._fire_event(ComponentLifecycleEvent.AFTER_CLEANUP)
                
                print(f"✅ 组件清理完成: {self.component_id}")
                return True
            else:
                return False
                
        except Exception as e:
            self.error_occurred.emit(f"清理失败: {str(e)}", e)
            self._fire_event(ComponentLifecycleEvent.ERROR_OCCURRED, e)
            print(f"❌ 组件清理失败: {self.component_id} -> {e}")
            return False
    
    @abstractmethod
    def _do_cleanup(self) -> bool:
        """子类实现的清理逻辑"""
        pass
    
    def add_child_component(self, child: 'UIComponentBase'):
        """添加子组件"""
        self._child_components.add(child)
    
    def remove_child_component(self, child: 'UIComponentBase'):
        """移除子组件"""
        self._child_components.discard(child)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return {
            'component_id': self.component_id,
            'component_name': self.component_name,
            'created_at': self.created_at,
            'state': self._state.value,
            'performance_metrics': self._performance_metrics.copy(),
            'dependency_count': len(self._dependencies),
            'child_count': len(self._child_components)
        }
    
    def __del__(self):
        """析构函数"""
        if not self._destroyed:
            self.cleanup()


class UIWidgetComponent(UIComponentBase):
    """UI Widget组件基类
    
    专门用于继承自QWidget的UI组件
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._widget = None
    
    def set_widget(self, widget: QWidget):
        """设置关联的widget"""
        self._widget = widget
        self._widget_refs.add(widget)
        
        # 连接widget的销毁信号
        if hasattr(widget, 'destroyed'):
            self._connect_signal(widget.destroyed, self._on_widget_destroyed)
    
    def get_widget(self) -> Optional[QWidget]:
        """获取关联的widget"""
        return self._widget
    
    def _on_widget_destroyed(self):
        """widget被销毁时的处理"""
        print(f"🗑️ Widget被销毁: {self.component_id}")
        self.cleanup()
    
    def _do_cleanup(self) -> bool:
        """清理widget资源"""
        try:
            if self._widget and not self._widget.isWidgetType():
                return True
                
            if self._widget:
                # 清理widget
                self._widget.close()
                self._widget.deleteLater()
                self._widget = None
            
            return True
        except Exception as e:
            print(f"❌ 清理Widget失败: {e}")
            return False


# 组件装饰器
def ui_component(name: Optional[str] = None, 
                dependencies: Optional[List[str]] = None,
                lazy_load: bool = False,
                auto_start: bool = True):
    """UI组件装饰器
    
    Args:
        name: 组件名称
        dependencies: 依赖列表
        lazy_load: 是否懒加载
        auto_start: 是否自动启动
    """
    def decorator(cls):
        # 设置组件元数据
        cls.__component_name__ = name or cls.__name__
        cls.__component_dependencies__ = dependencies or []
        cls.__component_lazy_load__ = lazy_load
        cls.__component_auto_start__ = auto_start
        
        # 自动注册到DI容器
        container = DependencyContainer()
        container.register_singleton(cls)
        
        return cls
    
    return decorator


@injectable(ServiceLifetime.SINGLETON)
class UIComponentManager(QObject):
    """UI组件管理器
    
    负责管理所有UI组件的生命周期、依赖关系和事件通信
    """
    
    # 全局事件信号
    component_registered = Signal(str, object)  # 组件注册信号
    component_unregistered = Signal(str)        # 组件注销信号
    component_state_changed = Signal(str, ComponentState, ComponentState)  # 组件状态变更
    global_error_occurred = Signal(str, str, Exception)  # 全局错误信号
    
    def __init__(self):
        super().__init__()
        
        # 组件注册表
        self._components: Dict[str, UIComponentBase] = {}
        self._component_types: Dict[Type, str] = {}
        self._component_metadata: Dict[str, Dict[str, Any]] = {}
        
        # 依赖关系图
        self._dependency_graph: Dict[str, Set[str]] = {}
        self._reverse_dependency_graph: Dict[str, Set[str]] = {}
        
        # 启动顺序
        self._startup_order: List[str] = []
        self._shutdown_order: List[str] = []
        
        # 事件总线
        self._event_bus: Dict[str, List[Callable]] = {}
        
        # 性能监控
        self._performance_stats = {
            'total_components': 0,
            'active_components': 0,
            'failed_components': 0,
            'startup_time': 0.0,
            'shutdown_time': 0.0
        }
        
        # 线程安全
        self._lock = threading.RLock()
        
        # 依赖注入容器
        self._di_container = DependencyContainer()
        
        print("🎛️ UI组件管理器已初始化")
    
    def register_component(self, 
                          component: UIComponentBase,
                          name: Optional[str] = None,
                          dependencies: Optional[List[str]] = None,
                          auto_start: bool = True) -> bool:
        """注册UI组件
        
        Args:
            component: 组件实例
            name: 组件名称
            dependencies: 依赖组件列表
            auto_start: 是否自动启动
        """
        with self._lock:
            try:
                # 确定组件名称
                component_name = name or getattr(component, '__component_name__', component.component_id)
                
                # 检查是否已注册
                if component_name in self._components:
                    print(f"⚠️ 组件已注册: {component_name}")
                    return False
                
                # 注册组件
                self._components[component_name] = component
                self._component_types[type(component)] = component_name
                
                # 保存元数据
                self._component_metadata[component_name] = {
                    'type': type(component).__name__,
                    'dependencies': dependencies or getattr(component, '__component_dependencies__', []),
                    'auto_start': auto_start,
                    'lazy_load': getattr(component, '__component_lazy_load__', False),
                    'registered_at': datetime.now()
                }
                
                # 构建依赖关系图
                self._build_dependency_graph(component_name, dependencies or [])
                
                # 连接组件信号
                self._connect_component_signals(component, component_name)
                
                # 更新统计
                self._performance_stats['total_components'] += 1
                
                # 触发注册事件
                self.component_registered.emit(component_name, component)
                
                print(f"✅ 组件注册成功: {component_name}")
                
                # 自动启动组件（如果满足条件）
                if auto_start and not getattr(component, '__component_lazy_load__', False):
                    self._try_start_component(component_name)
                
                return True
                
            except Exception as e:
                print(f"❌ 组件注册失败: {e}")
                return False
    
    def unregister_component(self, name_or_component) -> bool:
        """注销组件"""
        with self._lock:
            try:
                # 确定组件名称
                if isinstance(name_or_component, str):
                    component_name = name_or_component
                    component = self._components.get(component_name)
                else:
                    component = name_or_component
                    component_name = self._component_types.get(type(component))
                
                if not component_name or component_name not in self._components:
                    print(f"⚠️ 组件未找到: {name_or_component}")
                    return False
                
                # 停止组件
                if component and component.get_state() == ComponentState.RUNNING:
                    component.stop()
                
                # 清理组件
                if component:
                    component.cleanup()
                
                # 从注册表中移除
                del self._components[component_name]
                if type(component) in self._component_types:
                    del self._component_types[type(component)]
                if component_name in self._component_metadata:
                    del self._component_metadata[component_name]
                
                # 更新依赖关系图
                self._remove_from_dependency_graph(component_name)
                
                # 更新统计
                self._performance_stats['total_components'] -= 1
                
                # 触发注销事件
                self.component_unregistered.emit(component_name)
                
                print(f"✅ 组件注销成功: {component_name}")
                return True
                
            except Exception as e:
                print(f"❌ 组件注销失败: {e}")
                return False
    
    def get_component(self, name: str) -> Optional[UIComponentBase]:
        """获取组件实例"""
        return self._components.get(name)
    
    def get_component_by_type(self, component_type: Type) -> Optional[UIComponentBase]:
        """根据类型获取组件实例"""
        component_name = self._component_types.get(component_type)
        if component_name:
            return self._components.get(component_name)
        return None
    
    def list_components(self) -> List[str]:
        """列出所有注册的组件"""
        return list(self._components.keys())
    
    def start_component(self, name: str) -> bool:
        """启动指定组件"""
        return self._try_start_component(name)
    
    def stop_component(self, name: str) -> bool:
        """停止指定组件"""
        component = self._components.get(name)
        if component:
            return component.stop()
        return False
    
    def start_all_components(self) -> bool:
        """启动所有组件"""
        start_time = datetime.now()
        
        try:
            # 按依赖顺序启动
            startup_order = self._calculate_startup_order()
            
            for component_name in startup_order:
                if not self._try_start_component(component_name):
                    print(f"❌ 启动组件失败: {component_name}")
                    return False
            
            # 记录启动时间
            self._performance_stats['startup_time'] = (datetime.now() - start_time).total_seconds()
            
            print(f"✅ 所有组件启动完成，耗时: {self._performance_stats['startup_time']:.3f}秒")
            return True
            
        except Exception as e:
            print(f"❌ 批量启动组件失败: {e}")
            return False
    
    def stop_all_components(self) -> bool:
        """停止所有组件"""
        start_time = datetime.now()
        
        try:
            # 按反向依赖顺序停止
            shutdown_order = self._calculate_shutdown_order()
            
            for component_name in shutdown_order:
                component = self._components.get(component_name)
                if component and component.get_state() == ComponentState.RUNNING:
                    if not component.stop():
                        print(f"❌ 停止组件失败: {component_name}")
            
            # 记录停止时间
            self._performance_stats['shutdown_time'] = (datetime.now() - start_time).total_seconds()
            
            print(f"✅ 所有组件停止完成，耗时: {self._performance_stats['shutdown_time']:.3f}秒")
            return True
            
        except Exception as e:
            print(f"❌ 批量停止组件失败: {e}")
            return False
    
    def _try_start_component(self, component_name: str) -> bool:
        """尝试启动组件"""
        component = self._components.get(component_name)
        if not component:
            return False
        
        # 检查状态
        if component.get_state() == ComponentState.RUNNING:
            return True
        
        # 检查依赖
        metadata = self._component_metadata.get(component_name, {})
        dependencies = metadata.get('dependencies', [])
        
        for dep_name in dependencies:
            dep_component = self._components.get(dep_name)
            if not dep_component or dep_component.get_state() != ComponentState.RUNNING:
                print(f"⚠️ 组件 {component_name} 的依赖 {dep_name} 未就绪")
                return False
        
        # 启动组件
        try:
            success = component.start()
            if success:
                self._performance_stats['active_components'] += 1
            else:
                self._performance_stats['failed_components'] += 1
            return success
        except Exception as e:
            print(f"❌ 启动组件异常: {component_name} -> {e}")
            self._performance_stats['failed_components'] += 1
            return False
    
    def _build_dependency_graph(self, component_name: str, dependencies: List[str]):
        """构建依赖关系图"""
        self._dependency_graph[component_name] = set(dependencies)
        
        # 构建反向依赖图
        for dep in dependencies:
            if dep not in self._reverse_dependency_graph:
                self._reverse_dependency_graph[dep] = set()
            self._reverse_dependency_graph[dep].add(component_name)
    
    def _remove_from_dependency_graph(self, component_name: str):
        """从依赖关系图中移除组件"""
        if component_name in self._dependency_graph:
            del self._dependency_graph[component_name]
        
        # 从反向依赖图中移除
        for dep_set in self._reverse_dependency_graph.values():
            dep_set.discard(component_name)
        
        if component_name in self._reverse_dependency_graph:
            del self._reverse_dependency_graph[component_name]
    
    def _calculate_startup_order(self) -> List[str]:
        """计算启动顺序（拓扑排序）"""
        # 简化的拓扑排序实现
        in_degree = {}
        for component in self._components.keys():
            in_degree[component] = len(self._dependency_graph.get(component, set()))
        
        queue = [comp for comp, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            # 更新依赖于当前组件的其他组件
            for dependent in self._reverse_dependency_graph.get(current, set()):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        return result
    
    def _calculate_shutdown_order(self) -> List[str]:
        """计算停止顺序（启动顺序的反向）"""
        return list(reversed(self._calculate_startup_order()))
    
    def _connect_component_signals(self, component: UIComponentBase, component_name: str):
        """连接组件信号"""
        # 连接状态变更信号
        component.state_changed.connect(
            lambda from_state, to_state: self.component_state_changed.emit(
                component_name, from_state, to_state
            )
        )
        
        # 连接错误信号
        component.error_occurred.connect(
            lambda message, exception: self.global_error_occurred.emit(
                component_name, message, exception
            )
        )
    
    def publish_event(self, event_name: str, data: Any = None):
        """发布全局事件"""
        if event_name in self._event_bus:
            for handler in self._event_bus[event_name]:
                try:
                    handler(data)
                except Exception as e:
                    print(f"❌ 事件处理器执行失败: {event_name} -> {e}")
    
    def subscribe_event(self, event_name: str, handler: Callable):
        """订阅全局事件"""
        if event_name not in self._event_bus:
            self._event_bus[event_name] = []
        self._event_bus[event_name].append(handler)
    
    def unsubscribe_event(self, event_name: str, handler: Callable):
        """取消订阅全局事件"""
        if event_name in self._event_bus:
            try:
                self._event_bus[event_name].remove(handler)
            except ValueError:
                pass
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        active_count = sum(1 for comp in self._components.values() 
                          if comp.get_state() == ComponentState.RUNNING)
        
        self._performance_stats['active_components'] = active_count
        
        return {
            **self._performance_stats,
            'component_states': {name: comp.get_state().value 
                               for name, comp in self._components.items()},
            'dependency_graph': {name: list(deps) 
                               for name, deps in self._dependency_graph.items()}
        }
    
    def get_component_info(self, name: str) -> Optional[Dict[str, Any]]:
        """获取组件详细信息"""
        component = self._components.get(name)
        if not component:
            return None
        
        metadata = self._component_metadata.get(name, {})
        
        return {
            'name': name,
            'type': type(component).__name__,
            'state': component.get_state().value,
            'metadata': metadata,
            'performance_metrics': component.get_performance_metrics(),
            'dependencies': list(self._dependency_graph.get(name, set())),
            'dependents': list(self._reverse_dependency_graph.get(name, set()))
        }
    
    def cleanup(self):
        """清理管理器"""
        print("🧹 正在清理UI组件管理器...")
        
        # 停止所有组件
        self.stop_all_components()
        
        # 注销所有组件
        for component_name in list(self._components.keys()):
            self.unregister_component(component_name)
        
        # 清理事件总线
        self._event_bus.clear()
        
        print("✅ UI组件管理器清理完成")


# 全局UI组件管理器实例
ui_component_manager = UIComponentManager()