"""
单例管理器
确保关键组件只被初始化一次
"""

import logging
from typing import Dict, Type, Any, Optional
from threading import Lock
import weakref

class SingletonManager:
    """单例管理器 - 确保组件只被初始化一次"""
    
    _instance = None
    _lock = Lock()
    _singletons: Dict[Type, Any] = {}
    _logger = logging.getLogger(__name__)
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._logger.info("SingletonManager initialized")
    
    @classmethod
    def get_or_create(cls, component_type: Type, factory_func=None, *args, **kwargs) -> Any:
        """获取或创建单例组件"""
        if component_type in cls._singletons:
            instance = cls._singletons[component_type]
            # 检查弱引用是否仍然有效
            if isinstance(instance, weakref.ref):
                actual_instance = instance()
                if actual_instance is not None:
                    cls._logger.debug(f"返回现有单例: {component_type.__name__}")
                    return actual_instance
                else:
                    # 弱引用已失效，移除并重新创建
                    del cls._singletons[component_type]
            else:
                cls._logger.debug(f"返回现有单例: {component_type.__name__}")
                return instance
        
        # 创建新实例
        try:
            if factory_func:
                instance = factory_func(*args, **kwargs)
            else:
                instance = component_type(*args, **kwargs)
            
            # 对于QObject子类，使用弱引用以避免循环引用
            from PySide6.QtCore import QObject
            if isinstance(instance, QObject):
                cls._singletons[component_type] = weakref.ref(instance)
            else:
                cls._singletons[component_type] = instance
            
            cls._logger.info(f"创建新单例: {component_type.__name__}")
            return instance
            
        except Exception as e:
            cls._logger.error(f"创建单例失败 {component_type.__name__}: {e}")
            raise
    
    @classmethod
    def register_instance(cls, component_type: Type, instance: Any):
        """注册现有实例为单例"""
        from PySide6.QtCore import QObject
        if isinstance(instance, QObject):
            cls._singletons[component_type] = weakref.ref(instance)
        else:
            cls._singletons[component_type] = instance
        cls._logger.info(f"注册现有实例为单例: {component_type.__name__}")
    
    @classmethod
    def has_instance(cls, component_type: Type) -> bool:
        """检查是否已有实例"""
        if component_type not in cls._singletons:
            return False
        
        instance = cls._singletons[component_type]
        if isinstance(instance, weakref.ref):
            return instance() is not None
        return True
    
    @classmethod
    def clear_instance(cls, component_type: Type):
        """清除指定类型的实例"""
        if component_type in cls._singletons:
            del cls._singletons[component_type]
            cls._logger.info(f"清除单例: {component_type.__name__}")
    
    @classmethod
    def clear_all(cls):
        """清除所有单例"""
        cls._singletons.clear()
        cls._logger.info("清除所有单例")
    
    @classmethod
    def get_active_singletons(cls) -> Dict[str, Any]:
        """获取所有活跃的单例"""
        active = {}
        for component_type, instance in cls._singletons.items():
            if isinstance(instance, weakref.ref):
                actual_instance = instance()
                if actual_instance is not None:
                    active[component_type.__name__] = actual_instance
            else:
                active[component_type.__name__] = instance
        return active


# 便捷函数
def get_singleton(component_type: Type, factory_func=None, *args, **kwargs):
    """获取单例实例的便捷函数"""
    return SingletonManager.get_or_create(component_type, factory_func, *args, **kwargs)


def register_singleton(component_type: Type, instance: Any):
    """注册单例实例的便捷函数"""
    SingletonManager.register_instance(component_type, instance)


def clear_singleton(component_type: Type):
    """清除单例实例的便捷函数"""
    SingletonManager.clear_instance(component_type)
