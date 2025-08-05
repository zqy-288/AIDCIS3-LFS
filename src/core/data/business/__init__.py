"""
数据层模块
提供依赖注入和接口隔离的数据管理方案
"""

from .interfaces import (
    IHoleDataProvider,
    IHoleDataWriter,
    ISectorDataProvider,
    IProjectDataProvider,
    IDataEventBus,
    IDataRepository
)

from .data_repository import DataRepository
from .event_bus import EventBus, Events

__all__ = [
    # 接口
    'IHoleDataProvider',
    'IHoleDataWriter',
    'ISectorDataProvider',
    'IProjectDataProvider',
    'IDataEventBus',
    'IDataRepository',
    
    # 实现
    'DataRepository',
    'EventBus',
    'Events'
]