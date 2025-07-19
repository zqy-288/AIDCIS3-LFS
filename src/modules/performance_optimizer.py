"""
性能优化模块
实现大数据量渲染优化、内存使用优化、异步操作等功能
支持10000+孔位流畅显示，内存占用<500MB，界面响应时间<100ms
"""

import logging
import gc
import threading
import time
import weakref
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from enum import Enum
from dataclasses import dataclass, field
from collections import deque
from functools import lru_cache
import psutil
import os

from PySide6.QtCore import (QObject, Signal, QThread, QTimer, QRect, QRectF, 
                           QMutex, QMutexLocker, QReadWriteLock, QReadLocker, QWriteLocker)
from PySide6.QtWidgets import QWidget, QGraphicsView, QGraphicsScene, QGraphicsItem
from PySide6.QtGui import QPainter, QTransform


class RenderingStrategy(Enum):
    """渲染策略枚举"""
    IMMEDIATE = "immediate"          # 立即渲染
    LAZY = "lazy"                   # 延迟渲染
    VIEWPORT_ONLY = "viewport_only"  # 仅渲染可视区域
    LOD = "level_of_detail"         # 层次细节渲染


class MemoryStrategy(Enum):
    """内存管理策略枚举"""
    AGGRESSIVE = "aggressive"        # 激进回收
    BALANCED = "balanced"           # 平衡模式
    CONSERVATIVE = "conservative"    # 保守模式


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    frame_rate: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    render_time_ms: float = 0.0
    item_count: int = 0
    visible_item_count: int = 0
    cache_hit_rate: float = 0.0
    gc_collection_count: int = 0
    
    # 历史数据
    frame_rate_history: List[float] = field(default_factory=list)
    memory_history: List[float] = field(default_factory=list)
    render_time_history: List[float] = field(default_factory=list)


@dataclass
class OptimizationConfig:
    """优化配置"""
    # 渲染优化
    rendering_strategy: RenderingStrategy = RenderingStrategy.VIEWPORT_ONLY
    max_visible_items: int = 500  # 减少可见项目数量
    lod_distance_threshold: float = 300.0  # 降低LOD阈值
    frame_rate_target: float = 30.0  # 降低目标帧率到更现实的水平
    
    # 内存优化
    memory_strategy: MemoryStrategy = MemoryStrategy.BALANCED
    max_memory_mb: float = 500.0
    cache_size_limit: int = 5000  # 减少缓存大小
    gc_threshold_mb: float = 350.0  # 更早触发垃圾回收
    
    # 异步处理
    enable_async_rendering: bool = True
    worker_thread_count: int = 1  # 减少工作线程数量
    batch_size: int = 50  # 减少批次大小
    update_interval_ms: int = 100  # 降低更新频率，减少CPU占用
    
    # 调试选项
    enable_performance_monitoring: bool = True
    log_performance_warnings: bool = False  # 禁用频繁的性能警告


class ViewportTracker(QObject):
    """视口跟踪器"""
    
    viewport_changed = Signal(QRectF)  # 视口变化信号
    
    def __init__(self, graphics_view: QGraphicsView):
        super().__init__()
        self.graphics_view = graphics_view
        self.last_viewport = QRectF()
        self.viewport_change_threshold = 10.0  # 像素
        
        # 连接视图信号
        if hasattr(graphics_view, 'viewport'):
            graphics_view.viewport().installEventFilter(self)
    
    def get_current_viewport(self) -> QRectF:
        """获取当前视口矩形"""
        if self.graphics_view and self.graphics_view.scene():
            return self.graphics_view.mapToScene(self.graphics_view.viewport().rect()).boundingRect()
        return QRectF()
    
    def check_viewport_change(self):
        """检查视口是否发生变化"""
        current_viewport = self.get_current_viewport()
        
        if self._viewport_significantly_changed(current_viewport):
            self.last_viewport = current_viewport
            self.viewport_changed.emit(current_viewport)
    
    def _viewport_significantly_changed(self, new_viewport: QRectF) -> bool:
        """检查视口是否显著变化"""
        if self.last_viewport.isEmpty():
            return True
        
        # 计算位置变化
        dx = abs(new_viewport.x() - self.last_viewport.x())
        dy = abs(new_viewport.y() - self.last_viewport.y())
        
        # 计算大小变化
        dw = abs(new_viewport.width() - self.last_viewport.width())
        dh = abs(new_viewport.height() - self.last_viewport.height())
        
        return (dx > self.viewport_change_threshold or 
                dy > self.viewport_change_threshold or
                dw > self.viewport_change_threshold or 
                dh > self.viewport_change_threshold)


class RenderCache:
    """渲染缓存管理器"""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.cache: Dict[str, Any] = {}
        self.access_order = deque()
        self.hit_count = 0
        self.miss_count = 0
        self.lock = QMutex()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存项"""
        with QMutexLocker(self.lock):
            if key in self.cache:
                # 更新访问顺序
                self.access_order.remove(key)
                self.access_order.append(key)
                self.hit_count += 1
                return self.cache[key]
            
            self.miss_count += 1
            return None
    
    def put(self, key: str, value: Any):
        """添加缓存项"""
        with QMutexLocker(self.lock):
            if key in self.cache:
                # 更新现有项
                self.access_order.remove(key)
            elif len(self.cache) >= self.max_size:
                # 移除最老的项
                oldest_key = self.access_order.popleft()
                del self.cache[oldest_key]
            
            self.cache[key] = value
            self.access_order.append(key)
    
    def clear(self):
        """清空缓存"""
        with QMutexLocker(self.lock):
            self.cache.clear()
            self.access_order.clear()
    
    def get_hit_rate(self) -> float:
        """获取缓存命中率"""
        total = self.hit_count + self.miss_count
        return self.hit_count / total if total > 0 else 0.0
    
    def get_size(self) -> int:
        """获取缓存大小"""
        return len(self.cache)


class AsyncRenderWorker(QThread):
    """异步渲染工作线程"""
    
    render_completed = Signal(str, object)  # item_id, render_data
    batch_completed = Signal(list)  # batch_results
    
    def __init__(self, worker_id: str):
        super().__init__()
        self.worker_id = worker_id
        self.render_queue = deque()
        self.is_running = False
        self.queue_lock = QMutex()
        self.logger = logging.getLogger(__name__)
    
    def add_render_task(self, item_id: str, render_func: Callable, *args, **kwargs):
        """添加渲染任务"""
        with QMutexLocker(self.queue_lock):
            self.render_queue.append({
                'item_id': item_id,
                'render_func': render_func,
                'args': args,
                'kwargs': kwargs
            })
    
    def run(self):
        """运行工作线程"""
        self.is_running = True
        batch_results = []
        
        while self.is_running:
            tasks_to_process = []
            
            # 获取批次任务
            with QMutexLocker(self.queue_lock):
                while self.render_queue and len(tasks_to_process) < 10:
                    tasks_to_process.append(self.render_queue.popleft())
            
            if not tasks_to_process:
                self.msleep(1)  # 短暂等待
                continue
            
            # 处理任务
            for task in tasks_to_process:
                try:
                    result = task['render_func'](*task['args'], **task['kwargs'])
                    self.render_completed.emit(task['item_id'], result)
                    batch_results.append((task['item_id'], result))
                    
                except Exception as e:
                    self.logger.error(f"渲染任务失败 {task['item_id']}: {e}")
            
            if batch_results:
                self.batch_completed.emit(batch_results.copy())
                batch_results.clear()
    
    def stop(self):
        """停止工作线程"""
        self.is_running = False
        self.wait(3000)


class MemoryMonitor(QObject):
    """内存监视器"""
    
    memory_warning = Signal(float)  # current_memory_mb
    memory_critical = Signal(float)  # current_memory_mb
    
    def __init__(self, config: OptimizationConfig):
        super().__init__()
        self.config = config
        self.process = psutil.Process(os.getpid())
        self.logger = logging.getLogger(__name__)
        
        # 监控定时器
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.check_memory_usage)
        self.monitor_timer.start(1000)  # 每秒检查一次
    
    def get_current_memory_mb(self) -> float:
        """获取当前内存使用量(MB)"""
        try:
            memory_info = self.process.memory_info()
            return memory_info.rss / 1024 / 1024  # 转换为MB
        except Exception as e:
            self.logger.error(f"获取内存信息失败: {e}")
            return 0.0
    
    def check_memory_usage(self):
        """检查内存使用情况"""
        current_memory = self.get_current_memory_mb()
        
        # 添加冷却时间，避免频繁触发
        if not hasattr(self, '_last_memory_warning_time'):
            self._last_memory_warning_time = 0
        
        current_time = time.time()
        if current_time - self._last_memory_warning_time < 5.0:  # 5秒冷却
            return
        
        if current_memory > self.config.max_memory_mb:
            self.memory_critical.emit(current_memory)
            self._last_memory_warning_time = current_time
        elif current_memory > self.config.max_memory_mb * 0.85:  # 提高阈值
            self.memory_warning.emit(current_memory)
            self._last_memory_warning_time = current_time
    
    def force_garbage_collection(self):
        """强制垃圾回收"""
        collected = gc.collect()
        self.logger.debug(f"垃圾回收: 清理了 {collected} 个对象")
        return collected


class PerformanceOptimizer(QObject):
    """性能优化器主类"""
    
    # 信号定义
    metrics_updated = Signal(dict)  # performance metrics
    optimization_applied = Signal(str)  # optimization description
    warning_issued = Signal(str)  # warning message
    
    def __init__(self, config: OptimizationConfig = None):
        super().__init__()
        self.config = config or OptimizationConfig()
        self.logger = logging.getLogger(__name__)
        
        # 组件初始化
        self.render_cache = RenderCache(self.config.cache_size_limit)
        self.memory_monitor = MemoryMonitor(self.config)
        self.viewport_tracker: Optional[ViewportTracker] = None
        self.async_workers: List[AsyncRenderWorker] = []
        
        # 性能指标
        self.metrics = PerformanceMetrics()
        self.last_frame_time = time.time()
        
        # 连接信号
        self.memory_monitor.memory_warning.connect(self._on_memory_warning)
        self.memory_monitor.memory_critical.connect(self._on_memory_critical)
        
        # 性能监控定时器
        if self.config.enable_performance_monitoring:
            self.metrics_timer = QTimer()
            self.metrics_timer.timeout.connect(self._update_metrics)
            self.metrics_timer.start(self.config.update_interval_ms)
        
        # 初始化异步工作线程
        if self.config.enable_async_rendering:
            self._initialize_async_workers()
        
        self.logger.info(f"🚀 性能优化器初始化完成 - 策略: {self.config.rendering_strategy.value}")
    
    def set_graphics_view(self, graphics_view: QGraphicsView):
        """设置图形视图"""
        self.viewport_tracker = ViewportTracker(graphics_view)
        self.viewport_tracker.viewport_changed.connect(self._on_viewport_changed)
        self.logger.info("📺 图形视图已关联到性能优化器")
    
    def optimize_rendering(self, items: List[QGraphicsItem], viewport: QRectF) -> List[QGraphicsItem]:
        """优化渲染项目列表"""
        if self.config.rendering_strategy == RenderingStrategy.IMMEDIATE:
            return items
        
        start_time = time.time()
        optimized_items = []
        
        try:
            if self.config.rendering_strategy == RenderingStrategy.VIEWPORT_ONLY:
                optimized_items = self._filter_viewport_items(items, viewport)
            elif self.config.rendering_strategy == RenderingStrategy.LOD:
                optimized_items = self._apply_lod_filtering(items, viewport)
            elif self.config.rendering_strategy == RenderingStrategy.LAZY:
                optimized_items = self._apply_lazy_rendering(items)
            
            # 限制可见项目数量
            if len(optimized_items) > self.config.max_visible_items:
                optimized_items = optimized_items[:self.config.max_visible_items]
                if self.config.log_performance_warnings:
                    self.logger.warning(f"⚠️ 渲染项目数量超限，已限制为 {self.config.max_visible_items}")
            
            render_time = (time.time() - start_time) * 1000
            self.metrics.render_time_ms = render_time
            self.metrics.visible_item_count = len(optimized_items)
            
            return optimized_items
            
        except Exception as e:
            self.logger.error(f"❌ 渲染优化失败: {e}")
            return items[:self.config.max_visible_items]
    
    def _filter_viewport_items(self, items: List[QGraphicsItem], viewport: QRectF) -> List[QGraphicsItem]:
        """过滤视口内的项目"""
        visible_items = []
        
        for item in items:
            if item.isVisible() and viewport.intersects(item.sceneBoundingRect()):
                visible_items.append(item)
        
        return visible_items
    
    def _apply_lod_filtering(self, items: List[QGraphicsItem], viewport: QRectF) -> List[QGraphicsItem]:
        """应用层次细节过滤"""
        lod_items = []
        center = viewport.center()
        
        for item in items:
            item_center = item.sceneBoundingRect().center()
            distance = ((center.x() - item_center.x()) ** 2 + (center.y() - item_center.y()) ** 2) ** 0.5
            
            # 根据距离决定是否渲染
            if distance <= self.config.lod_distance_threshold:
                lod_items.append(item)
            elif distance <= self.config.lod_distance_threshold * 2:
                # 远距离项目使用简化渲染
                if hasattr(item, 'setDetailLevel'):
                    item.setDetailLevel('low')
                lod_items.append(item)
        
        return lod_items
    
    def _apply_lazy_rendering(self, items: List[QGraphicsItem]) -> List[QGraphicsItem]:
        """应用延迟渲染"""
        # 优先显示最近更新的项目
        recently_updated = [item for item in items if hasattr(item, 'last_update_time') 
                           and time.time() - item.last_update_time < 1.0]
        
        if len(recently_updated) < self.config.max_visible_items:
            remaining_slots = self.config.max_visible_items - len(recently_updated)
            other_items = [item for item in items if item not in recently_updated]
            recently_updated.extend(other_items[:remaining_slots])
        
        return recently_updated
    
    def optimize_memory_usage(self):
        """优化内存使用"""
        try:
            current_memory = self.memory_monitor.get_current_memory_mb()
            
            if current_memory > self.config.gc_threshold_mb:
                # 添加冷却时间，避免频繁优化
                if not hasattr(self, '_last_optimization_time'):
                    self._last_optimization_time = 0
                
                current_time = time.time()
                if current_time - self._last_optimization_time < 10.0:  # 10秒冷却
                    return
                
                self._last_optimization_time = current_time
                
                # 执行垃圾回收
                collected = self.memory_monitor.force_garbage_collection()
                
                # 清理缓存
                if self.config.memory_strategy == MemoryStrategy.AGGRESSIVE:
                    self.render_cache.clear()
                elif self.config.memory_strategy == MemoryStrategy.BALANCED:
                    # 清理缓存
                    cache_size = self.render_cache.get_size()
                    if cache_size > self.config.cache_size_limit * 0.7:
                        # 清理一半缓存
                        current_keys = list(self.render_cache.cache.keys())
                        for key in current_keys[:len(current_keys)//2]:
                            if key in self.render_cache.cache:
                                del self.render_cache.cache[key]
                        self.render_cache.access_order.clear()
                        for key in self.render_cache.cache.keys():
                            self.render_cache.access_order.append(key)
                
                # 等待一下让垃圾回收生效
                import time
                time.sleep(0.1)
                
                new_memory = self.memory_monitor.get_current_memory_mb()
                memory_freed = current_memory - new_memory
                
                if memory_freed > 0.1:  # 只有真正释放了内存才报告
                    self.optimization_applied.emit(f"内存优化: 释放 {memory_freed:.1f}MB")
                    self.logger.info(f"🧹 内存优化完成: 释放 {memory_freed:.1f}MB")
            
        except Exception as e:
            self.logger.error(f"❌ 内存优化失败: {e}")
    
    def submit_async_render_task(self, item_id: str, render_func: Callable, *args, **kwargs):
        """提交异步渲染任务"""
        if not self.async_workers:
            return False
        
        # 选择负载最少的工作线程
        worker = min(self.async_workers, key=lambda w: w.render_queue.__len__())
        worker.add_render_task(item_id, render_func, *args, **kwargs)
        return True
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return {
            'frame_rate': self.metrics.frame_rate,
            'memory_usage_mb': self.metrics.memory_usage_mb,
            'cpu_usage_percent': self.metrics.cpu_usage_percent,
            'render_time_ms': self.metrics.render_time_ms,
            'item_count': self.metrics.item_count,
            'visible_item_count': self.metrics.visible_item_count,
            'cache_hit_rate': self.render_cache.get_hit_rate(),
            'cache_size': self.render_cache.get_size(),
            'worker_count': len(self.async_workers),
            'memory_strategy': self.config.memory_strategy.value,
            'rendering_strategy': self.config.rendering_strategy.value
        }
    
    def _initialize_async_workers(self):
        """初始化异步工作线程"""
        for i in range(self.config.worker_thread_count):
            worker = AsyncRenderWorker(f"worker_{i}")
            worker.render_completed.connect(self._on_async_render_completed)
            worker.batch_completed.connect(self._on_batch_completed)
            worker.start()
            self.async_workers.append(worker)
        
        self.logger.info(f"🔧 初始化了 {len(self.async_workers)} 个异步渲染工作线程")
    
    def _update_metrics(self):
        """更新性能指标"""
        try:
            current_time = time.time()
            frame_time = current_time - self.last_frame_time
            self.last_frame_time = current_time
            
            # 更新帧率
            if frame_time > 0:
                self.metrics.frame_rate = 1.0 / frame_time
                self.metrics.frame_rate_history.append(self.metrics.frame_rate)
                if len(self.metrics.frame_rate_history) > 100:
                    self.metrics.frame_rate_history.pop(0)
            
            # 更新内存使用
            self.metrics.memory_usage_mb = self.memory_monitor.get_current_memory_mb()
            self.metrics.memory_history.append(self.metrics.memory_usage_mb)
            if len(self.metrics.memory_history) > 100:
                self.metrics.memory_history.pop(0)
            
            # 更新CPU使用率
            try:
                self.metrics.cpu_usage_percent = self.memory_monitor.process.cpu_percent()
            except:
                pass
            
            # 更新缓存命中率
            self.metrics.cache_hit_rate = self.render_cache.get_hit_rate()
            
            # 发送指标更新信号
            self.metrics_updated.emit(self.get_performance_metrics())
            
            # 检查性能警告
            self._check_performance_warnings()
            
        except Exception as e:
            self.logger.error(f"❌ 更新性能指标失败: {e}")
    
    def _check_performance_warnings(self):
        """检查性能警告"""
        if not self.config.log_performance_warnings:
            return
        
        # 添加冷却时间，避免频繁警告
        if not hasattr(self, '_last_warning_time'):
            self._last_warning_time = {}
        
        current_time = time.time()
        
        # 检查帧率警告（5秒冷却）
        if self.metrics.frame_rate < self.config.frame_rate_target * 0.7:  # 降低敏感度
            last_fps_warning = self._last_warning_time.get('fps', 0)
            if current_time - last_fps_warning > 5.0:
                self.warning_issued.emit(f"帧率过低: {self.metrics.frame_rate:.1f} FPS")
                self._last_warning_time['fps'] = current_time
        
        # 检查渲染时间警告（10秒冷却）
        if self.metrics.render_time_ms > 200:  # 提高阈值
            last_render_warning = self._last_warning_time.get('render', 0)
            if current_time - last_render_warning > 10.0:
                self.warning_issued.emit(f"渲染时间过长: {self.metrics.render_time_ms:.1f}ms")
                self._last_warning_time['render'] = current_time
    
    def _on_viewport_changed(self, viewport: QRectF):
        """处理视口变化"""
        self.logger.debug(f"📺 视口变化: {viewport.width()}x{viewport.height()}")
        # 可以在这里触发渲染优化
    
    def _on_memory_warning(self, memory_mb: float):
        """处理内存警告"""
        self.warning_issued.emit(f"内存使用警告: {memory_mb:.1f}MB")
        if self.config.memory_strategy != MemoryStrategy.CONSERVATIVE:
            self.optimize_memory_usage()
    
    def _on_memory_critical(self, memory_mb: float):
        """处理内存严重警告"""
        self.warning_issued.emit(f"内存使用严重警告: {memory_mb:.1f}MB")
        self.optimize_memory_usage()
    
    def _on_async_render_completed(self, item_id: str, render_data: object):
        """处理异步渲染完成"""
        # 将渲染结果存入缓存
        self.render_cache.put(f"render_{item_id}", render_data)
    
    def _on_batch_completed(self, batch_results: List[Tuple[str, Any]]):
        """处理批次渲染完成"""
        self.logger.debug(f"🎨 批次渲染完成: {len(batch_results)} 个项目")
    
    def cleanup(self):
        """清理资源"""
        try:
            # 停止工作线程
            for worker in self.async_workers:
                worker.stop()
            
            # 停止定时器
            if hasattr(self, 'metrics_timer'):
                self.metrics_timer.stop()
            
            # 清理缓存
            self.render_cache.clear()
            
            self.logger.info("🧹 性能优化器清理完成")
            
        except Exception as e:
            self.logger.error(f"❌ 性能优化器清理失败: {e}")


# 全局性能优化器实例
_global_performance_optimizer = None

def get_performance_optimizer(config: OptimizationConfig = None) -> PerformanceOptimizer:
    """获取全局性能优化器实例"""
    global _global_performance_optimizer
    if _global_performance_optimizer is None:
        _global_performance_optimizer = PerformanceOptimizer(config)
    return _global_performance_optimizer


# 导出的公共接口
__all__ = [
    'PerformanceOptimizer',
    'OptimizationConfig',
    'RenderingStrategy',
    'MemoryStrategy',
    'PerformanceMetrics',
    'ViewportTracker',
    'RenderCache',
    'MemoryMonitor',
    'get_performance_optimizer'
]