"""
UI组件内存监控和管理系统
用于监控和预警内存使用情况，防止内存泄漏
"""

import gc
import sys
import psutil
import weakref
from datetime import datetime
from typing import Dict, List, Optional, Any
from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QWidget


class MemoryMonitor(QObject):
    """内存监控器"""
    
    # 信号定义
    memory_warning = Signal(str)  # 内存警告信号
    memory_critical = Signal(str)  # 内存严重警告信号
    memory_leak_detected = Signal(str)  # 内存泄漏检测信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.widget_registry = weakref.WeakSet()
        self.memory_history = []
        self.widget_count_history = []
        self.monitoring_enabled = True
        self.warning_threshold = 80  # 内存使用80%时警告
        self.critical_threshold = 90  # 内存使用90%时严重警告
        
        # 设置监控定时器
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._check_memory_usage)
        self.monitor_timer.start(5000)  # 每5秒检查一次
        
        # 设置清理定时器
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self._cleanup_dead_refs)
        self.cleanup_timer.start(30000)  # 每30秒清理一次
        
    def register_widget(self, widget: QWidget):
        """注册widget到监控系统"""
        if widget and hasattr(widget, '__class__'):
            self.widget_registry.add(widget)
            
    def unregister_widget(self, widget: QWidget):
        """从监控系统中移除widget"""
        if widget in self.widget_registry:
            self.widget_registry.discard(widget)
            
    def get_memory_usage(self) -> Dict[str, Any]:
        """获取当前内存使用情况"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            return {
                'rss': memory_info.rss / 1024 / 1024,  # MB
                'vms': memory_info.vms / 1024 / 1024,  # MB
                'percent': memory_percent,
                'widget_count': len(self.widget_registry),
                'timestamp': datetime.now()
            }
        except Exception as e:
            return {
                'rss': 0,
                'vms': 0,
                'percent': 0,
                'widget_count': 0,
                'timestamp': datetime.now(),
                'error': str(e)
            }
    
    def _check_memory_usage(self):
        """检查内存使用情况"""
        if not self.monitoring_enabled:
            return
            
        memory_info = self.get_memory_usage()
        self.memory_history.append(memory_info)
        
        # 保持历史记录在合理范围内
        if len(self.memory_history) > 100:
            self.memory_history.pop(0)
            
        # 检查内存使用阈值
        memory_percent = memory_info['percent']
        
        if memory_percent > self.critical_threshold:
            self.memory_critical.emit(
                f"内存使用严重警告: {memory_percent:.1f}% "
                f"(RSS: {memory_info['rss']:.1f}MB, "
                f"Widgets: {memory_info['widget_count']})"
            )
            self._force_cleanup()
            
        elif memory_percent > self.warning_threshold:
            self.memory_warning.emit(
                f"内存使用警告: {memory_percent:.1f}% "
                f"(RSS: {memory_info['rss']:.1f}MB, "
                f"Widgets: {memory_info['widget_count']})"
            )
            
        # 检查内存泄漏
        self._check_memory_leak()
        
    def _check_memory_leak(self):
        """检查是否存在内存泄漏"""
        if len(self.memory_history) < 10:
            return
            
        # 检查最近10次的内存使用趋势
        recent_memory = [info['rss'] for info in self.memory_history[-10:]]
        
        # 如果内存持续增长且增长幅度超过50MB
        if all(recent_memory[i] <= recent_memory[i+1] for i in range(len(recent_memory)-1)):
            growth = recent_memory[-1] - recent_memory[0]
            if growth > 50:  # 50MB
                self.memory_leak_detected.emit(
                    f"检测到可能的内存泄漏: "
                    f"内存增长 {growth:.1f}MB "
                    f"在过去 {len(recent_memory)} 次检查中"
                )
                
    def _cleanup_dead_refs(self):
        """清理死引用"""
        # 弱引用集合会自动清理死引用
        # 这里主要是触发垃圾回收
        gc.collect()
        
    def _force_cleanup(self):
        """强制清理内存"""
        # 触发垃圾回收
        gc.collect()
        
        # 清理所有注册的widget
        dead_widgets = []
        for widget_ref in list(self.widget_registry):
            try:
                widget = widget_ref()
                if widget is None:
                    dead_widgets.append(widget_ref)
                elif hasattr(widget, 'cleanup'):
                    widget.cleanup()
            except:
                dead_widgets.append(widget_ref)
                
        # 移除死引用
        for dead_ref in dead_widgets:
            self.widget_registry.discard(dead_ref)
            
    def get_widget_statistics(self) -> Dict[str, int]:
        """获取widget统计信息"""
        stats = {}
        for widget_ref in self.widget_registry:
            try:
                widget = widget_ref()
                if widget:
                    widget_type = widget.__class__.__name__
                    stats[widget_type] = stats.get(widget_type, 0) + 1
            except:
                pass
        return stats
        
    def generate_memory_report(self) -> str:
        """生成内存使用报告"""
        current_memory = self.get_memory_usage()
        widget_stats = self.get_widget_statistics()
        
        report = []
        report.append("=" * 50)
        report.append("内存使用报告")
        report.append("=" * 50)
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 当前内存使用
        report.append("当前内存使用:")
        report.append(f"  RSS内存: {current_memory['rss']:.1f} MB")
        report.append(f"  VMS内存: {current_memory['vms']:.1f} MB")
        report.append(f"  内存占用率: {current_memory['percent']:.1f}%")
        report.append(f"  注册Widget数量: {current_memory['widget_count']}")
        report.append("")
        
        # Widget统计
        if widget_stats:
            report.append("Widget类型统计:")
            for widget_type, count in sorted(widget_stats.items()):
                report.append(f"  {widget_type}: {count}")
            report.append("")
        
        # 内存历史趋势
        if self.memory_history:
            report.append("内存使用历史 (最近10次):")
            for i, info in enumerate(self.memory_history[-10:], 1):
                report.append(f"  {i:2d}. {info['timestamp'].strftime('%H:%M:%S')} - "
                            f"RSS: {info['rss']:6.1f}MB, "
                            f"使用率: {info['percent']:5.1f}%, "
                            f"Widgets: {info['widget_count']:3d}")
        
        return "\n".join(report)
        
    def enable_monitoring(self):
        """启用内存监控"""
        self.monitoring_enabled = True
        if not self.monitor_timer.isActive():
            self.monitor_timer.start()
            
    def disable_monitoring(self):
        """禁用内存监控"""
        self.monitoring_enabled = False
        if self.monitor_timer.isActive():
            self.monitor_timer.stop()
            
    def cleanup(self):
        """清理监控器资源"""
        if self.monitor_timer.isActive():
            self.monitor_timer.stop()
        if self.cleanup_timer.isActive():
            self.cleanup_timer.stop()
            
        self.widget_registry.clear()
        self.memory_history.clear()
        self.widget_count_history.clear()


class MemoryPool:
    """UI组件内存池 - 优化版本"""
    
    def __init__(self, max_size: int = 50):  # 减少默认池大小
        self.max_size = max_size
        self.pools = {}  # 按类型分组的对象池
        self.pool_stats = {
            'total_created': 0,
            'total_reused': 0,
            'total_returned': 0,
            'total_discarded': 0
        }
        
    def get_object(self, obj_type: type, *args, **kwargs):
        """从池中获取对象"""
        pool_key = obj_type.__name__
        
        if pool_key not in self.pools:
            self.pools[pool_key] = []
            
        pool = self.pools[pool_key]
        
        if pool:
            # 从池中取出对象
            obj = pool.pop()
            self.pool_stats['total_reused'] += 1
            
            # 重新初始化对象
            try:
                if hasattr(obj, 'reset'):
                    obj.reset(*args, **kwargs)
                elif hasattr(obj, '__init__'):
                    # 如果没有reset方法，尝试重新初始化
                    obj.__init__(*args, **kwargs)
            except Exception as e:
                print(f"重新初始化对象失败: {e}")
                # 创建新对象作为备选
                obj = obj_type(*args, **kwargs)
                self.pool_stats['total_created'] += 1
                
            return obj
        else:
            # 创建新对象
            obj = obj_type(*args, **kwargs)
            self.pool_stats['total_created'] += 1
            return obj
            
    def return_object(self, obj):
        """将对象返回到池中"""
        if not obj:
            return
            
        obj_type = obj.__class__.__name__
        
        # 跳过某些不适合池化的类型
        if obj_type in ['QMainWindow', 'QApplication', 'QDialog']:
            if hasattr(obj, 'cleanup'):
                obj.cleanup()
            self.pool_stats['total_discarded'] += 1
            return
        
        if obj_type not in self.pools:
            self.pools[obj_type] = []
            
        pool = self.pools[obj_type]
        
        if len(pool) < self.max_size:
            # 清理对象状态但保持可重用
            try:
                if hasattr(obj, 'cleanup_for_pool'):
                    # 专门的池清理方法
                    obj.cleanup_for_pool()
                elif hasattr(obj, 'clear'):
                    obj.clear()
                    
                pool.append(obj)
                self.pool_stats['total_returned'] += 1
            except Exception as e:
                print(f"对象池清理失败: {e}")
                if hasattr(obj, 'cleanup'):
                    obj.cleanup()
                self.pool_stats['total_discarded'] += 1
        else:
            # 池已满，直接丢弃
            if hasattr(obj, 'cleanup'):
                obj.cleanup()
            self.pool_stats['total_discarded'] += 1
                
    def clear_pool(self, obj_type: type = None):
        """清空指定类型的池，或清空所有池"""
        if obj_type:
            pool_key = obj_type.__name__
            if pool_key in self.pools:
                pool = self.pools[pool_key]
                for obj in pool:
                    if hasattr(obj, 'cleanup'):
                        obj.cleanup()
                pool.clear()
        else:
            # 清空所有池
            for pool in self.pools.values():
                for obj in pool:
                    if hasattr(obj, 'cleanup'):
                        obj.cleanup()
                pool.clear()
            self.pools.clear()
            
    def get_pool_stats(self) -> Dict[str, Any]:
        """获取池统计信息"""
        pool_sizes = {pool_key: len(pool) for pool_key, pool in self.pools.items()}
        
        # 计算内存效率
        total_operations = (self.pool_stats['total_created'] + 
                          self.pool_stats['total_reused'])
        reuse_rate = (self.pool_stats['total_reused'] / max(total_operations, 1)) * 100
        
        return {
            'pool_sizes': pool_sizes,
            'total_pools': len(self.pools),
            'reuse_rate': round(reuse_rate, 2),
            **self.pool_stats
        }
        
    def optimize_pools(self):
        """优化内存池 - 清理空池和过大的池"""
        empty_pools = []
        for pool_key, pool in self.pools.items():
            if not pool:
                empty_pools.append(pool_key)
            elif len(pool) > self.max_size * 1.5:
                # 如果池过大，清理一半对象
                excess_count = len(pool) - self.max_size
                for _ in range(excess_count):
                    if pool:
                        obj = pool.pop()
                        if hasattr(obj, 'cleanup'):
                            obj.cleanup()
                        self.pool_stats['total_discarded'] += 1
                        
        # 清理空池
        for pool_key in empty_pools:
            del self.pools[pool_key]


# 全局实例
memory_monitor = MemoryMonitor()
memory_pool = MemoryPool()


def register_widget_for_monitoring(widget: QWidget):
    """注册widget到内存监控"""
    memory_monitor.register_widget(widget)


def unregister_widget_from_monitoring(widget: QWidget):
    """从内存监控中移除widget"""
    memory_monitor.unregister_widget(widget)


def get_memory_report() -> str:
    """获取内存使用报告"""
    return memory_monitor.generate_memory_report()


def force_memory_cleanup():
    """强制清理内存"""
    memory_monitor._force_cleanup()
    memory_pool.optimize_pools()


def get_current_memory_usage() -> Dict[str, Any]:
    """获取当前内存使用情况"""
    return memory_monitor.get_memory_usage()


def get_pool_statistics() -> Dict[str, Any]:
    """获取内存池统计信息"""
    return memory_pool.get_pool_stats()


def create_pooled_widget(widget_class: type, *args, **kwargs):
    """从内存池创建widget"""
    return memory_pool.get_object(widget_class, *args, **kwargs)


def return_widget_to_pool(widget: QWidget):
    """将widget返回到内存池"""
    memory_pool.return_object(widget)


def clear_memory_pools():
    """清空所有内存池"""
    memory_pool.clear_pool()