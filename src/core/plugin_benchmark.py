"""
插件性能基准测试和监控系统
提供持续的性能监控、基准测试和性能报告功能
"""

import time
import threading
import asyncio
import psutil
import gc
import json
import statistics
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from collections import defaultdict, deque
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from .plugin_manager import PluginManager, PluginState
from .plugin_lifecycle import PluginLifecycleManager


class BenchmarkType(Enum):
    """基准测试类型"""
    LOAD_TIME = "load_time"
    STARTUP_TIME = "startup_time"
    MEMORY_USAGE = "memory_usage"
    CONCURRENT_LOAD = "concurrent_load"
    LIFECYCLE_PERFORMANCE = "lifecycle_performance"
    COMMUNICATION_LATENCY = "communication_latency"
    THROUGHPUT = "throughput"


@dataclass
class PerformanceMetric:
    """性能指标"""
    name: str
    value: float
    unit: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    benchmark_type: BenchmarkType
    success: bool
    duration: float
    metrics: List[PerformanceMetric] = field(default_factory=list)
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['benchmark_type'] = self.benchmark_type.value
        return result


@dataclass
class PerformanceBaseline:
    """性能基线"""
    load_time_threshold: float = 500.0  # ms
    memory_per_plugin_threshold: float = 1024.0  # KB
    concurrent_plugins_threshold: int = 50
    lifecycle_phase_threshold: float = 100.0  # ms
    communication_latency_threshold: float = 10.0  # ms
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PluginBenchmarkRunner:
    """插件基准测试运行器"""
    
    def __init__(self, plugin_manager: PluginManager, logger: Optional[logging.Logger] = None):
        self.plugin_manager = plugin_manager
        self._logger = logger or logging.getLogger(__name__)
        self.baseline = PerformanceBaseline()
        self._results: List[BenchmarkResult] = []
        self._running_benchmarks: Dict[str, bool] = {}
        self._lock = threading.RLock()
        
        # 性能监控
        self._performance_monitor = PerformanceMonitor()
        self._process = psutil.Process()
    
    def set_baseline(self, baseline: PerformanceBaseline):
        """设置性能基线"""
        self.baseline = baseline
    
    def run_single_plugin_load_benchmark(self, plugin_path: str, iterations: int = 10) -> BenchmarkResult:
        """运行单个插件加载基准测试"""
        benchmark_type = BenchmarkType.LOAD_TIME
        self._running_benchmarks[benchmark_type.value] = True
        
        try:
            start_time = time.time()
            load_times = []
            memory_usages = []
            
            for i in range(iterations):
                # 记录初始状态
                initial_memory = self._process.memory_info().rss
                
                # 加载插件
                load_start = time.time()
                plugin_id = f"benchmark_plugin_{i}"
                
                success = self._load_test_plugin(plugin_id, plugin_path)
                load_end = time.time()
                
                if success:
                    load_time = (load_end - load_start) * 1000  # 转换为毫秒
                    load_times.append(load_time)
                    
                    # 记录内存使用
                    final_memory = self._process.memory_info().rss
                    memory_usage = final_memory - initial_memory
                    memory_usages.append(memory_usage)
                    
                    # 清理
                    self.plugin_manager.stop_plugin(plugin_id)
                    self.plugin_manager.unload_plugin(plugin_id)
                    gc.collect()
                
                time.sleep(0.1)  # 避免过快的连续操作
            
            # 计算统计数据
            if load_times:
                avg_load_time = statistics.mean(load_times)
                max_load_time = max(load_times)
                min_load_time = min(load_times)
                std_load_time = statistics.stdev(load_times) if len(load_times) > 1 else 0
                
                avg_memory = statistics.mean(memory_usages) / 1024  # 转换为KB
                
                metrics = [
                    PerformanceMetric("avg_load_time", avg_load_time, "ms"),
                    PerformanceMetric("max_load_time", max_load_time, "ms"),
                    PerformanceMetric("min_load_time", min_load_time, "ms"),
                    PerformanceMetric("std_load_time", std_load_time, "ms"),
                    PerformanceMetric("avg_memory_usage", avg_memory, "KB"),
                    PerformanceMetric("success_rate", len(load_times) / iterations * 100, "%")
                ]
                
                # 检查是否满足基线要求
                success = (avg_load_time <= self.baseline.load_time_threshold and
                          avg_memory <= self.baseline.memory_per_plugin_threshold)
                
                duration = time.time() - start_time
                
                result = BenchmarkResult(
                    benchmark_type=benchmark_type,
                    success=success,
                    duration=duration,
                    metrics=metrics,
                    metadata={
                        "iterations": iterations,
                        "plugin_path": plugin_path,
                        "load_times": load_times
                    }
                )
            else:
                result = BenchmarkResult(
                    benchmark_type=benchmark_type,
                    success=False,
                    duration=time.time() - start_time,
                    error="所有插件加载尝试都失败了"
                )
            
            self._results.append(result)
            return result
            
        except Exception as e:
            self._logger.error(f"单个插件加载基准测试失败: {e}")
            result = BenchmarkResult(
                benchmark_type=benchmark_type,
                success=False,
                duration=time.time() - start_time if 'start_time' in locals() else 0,
                error=str(e)
            )
            self._results.append(result)
            return result
            
        finally:
            self._running_benchmarks[benchmark_type.value] = False
    
    def run_concurrent_load_benchmark(self, plugin_paths: List[str], max_workers: int = 20) -> BenchmarkResult:
        """运行并发插件加载基准测试"""
        benchmark_type = BenchmarkType.CONCURRENT_LOAD
        self._running_benchmarks[benchmark_type.value] = True
        
        try:
            start_time = time.time()
            plugin_count = len(plugin_paths)
            
            # 记录初始内存
            initial_memory = self._process.memory_info().rss
            
            # 并发加载插件
            successful_loads = 0
            failed_loads = 0
            load_times = []
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交加载任务
                future_to_plugin = {}
                for i, plugin_path in enumerate(plugin_paths):
                    plugin_id = f"concurrent_plugin_{i}"
                    future = executor.submit(self._timed_plugin_load, plugin_id, plugin_path)
                    future_to_plugin[future] = (plugin_id, plugin_path)
                
                # 收集结果
                for future in as_completed(future_to_plugin.keys()):
                    plugin_id, plugin_path = future_to_plugin[future]
                    try:
                        success, load_time = future.result()
                        if success:
                            successful_loads += 1
                            load_times.append(load_time)
                        else:
                            failed_loads += 1
                    except Exception as e:
                        self._logger.error(f"插件 {plugin_id} 加载失败: {e}")
                        failed_loads += 1
            
            # 记录最终内存
            final_memory = self._process.memory_info().rss
            total_memory_increase = (final_memory - initial_memory) / 1024  # KB
            
            # 计算指标
            duration = time.time() - start_time
            success_rate = successful_loads / plugin_count * 100 if plugin_count > 0 else 0
            
            if load_times:
                avg_load_time = statistics.mean(load_times)
                max_load_time = max(load_times)
                memory_per_plugin = total_memory_increase / successful_loads if successful_loads > 0 else 0
            else:
                avg_load_time = max_load_time = memory_per_plugin = 0
            
            metrics = [
                PerformanceMetric("successful_loads", successful_loads, "count"),
                PerformanceMetric("failed_loads", failed_loads, "count"),
                PerformanceMetric("success_rate", success_rate, "%"),
                PerformanceMetric("avg_load_time", avg_load_time, "ms"),
                PerformanceMetric("max_load_time", max_load_time, "ms"),
                PerformanceMetric("total_duration", duration * 1000, "ms"),
                PerformanceMetric("memory_per_plugin", memory_per_plugin, "KB"),
                PerformanceMetric("total_memory_increase", total_memory_increase, "KB")
            ]
            
            # 检查是否满足基线要求
            success = (successful_loads >= self.baseline.concurrent_plugins_threshold and
                      success_rate >= 90 and
                      memory_per_plugin <= self.baseline.memory_per_plugin_threshold)
            
            result = BenchmarkResult(
                benchmark_type=benchmark_type,
                success=success,
                duration=duration,
                metrics=metrics,
                metadata={
                    "plugin_count": plugin_count,
                    "max_workers": max_workers,
                    "load_times": load_times
                }
            )
            
            self._results.append(result)
            return result
            
        except Exception as e:
            self._logger.error(f"并发插件加载基准测试失败: {e}")
            result = BenchmarkResult(
                benchmark_type=benchmark_type,
                success=False,
                duration=time.time() - start_time if 'start_time' in locals() else 0,
                error=str(e)
            )
            self._results.append(result)
            return result
            
        finally:
            self._running_benchmarks[benchmark_type.value] = False
    
    def run_lifecycle_benchmark(self, plugin_path: str, cycles: int = 20) -> BenchmarkResult:
        """运行插件生命周期基准测试"""
        benchmark_type = BenchmarkType.LIFECYCLE_PERFORMANCE
        self._running_benchmarks[benchmark_type.value] = True
        
        try:
            start_time = time.time()
            
            phase_times = {
                'load': [],
                'initialize': [],
                'start': [],
                'stop': [],
                'unload': []
            }
            
            for i in range(cycles):
                plugin_id = f"lifecycle_plugin_{i}"
                
                # 加载
                load_start = time.time()
                load_success = self._load_test_plugin(plugin_id, plugin_path)
                load_time = (time.time() - load_start) * 1000
                if load_success:
                    phase_times['load'].append(load_time)
                
                if load_success:
                    # 初始化
                    init_start = time.time()
                    init_success = self.plugin_manager.initialize_plugin(plugin_id)
                    init_time = (time.time() - init_start) * 1000
                    if init_success:
                        phase_times['initialize'].append(init_time)
                    
                    if init_success:
                        # 启动
                        start_start = time.time()
                        start_success = self.plugin_manager.start_plugin(plugin_id)
                        start_time = (time.time() - start_start) * 1000
                        if start_success:
                            phase_times['start'].append(start_time)
                        
                        if start_success:
                            # 停止
                            stop_start = time.time()
                            stop_success = self.plugin_manager.stop_plugin(plugin_id)
                            stop_time = (time.time() - stop_start) * 1000
                            if stop_success:
                                phase_times['stop'].append(stop_time)
                    
                    # 卸载
                    unload_start = time.time()
                    unload_success = self.plugin_manager.unload_plugin(plugin_id)
                    unload_time = (time.time() - unload_start) * 1000
                    if unload_success:
                        phase_times['unload'].append(unload_time)
                
                time.sleep(0.05)  # 避免过快操作
            
            # 计算每个阶段的统计数据
            metrics = []
            all_phases_ok = True
            
            for phase, times in phase_times.items():
                if times:
                    avg_time = statistics.mean(times)
                    max_time = max(times)
                    min_time = min(times)
                    
                    metrics.extend([
                        PerformanceMetric(f"{phase}_avg_time", avg_time, "ms"),
                        PerformanceMetric(f"{phase}_max_time", max_time, "ms"),
                        PerformanceMetric(f"{phase}_min_time", min_time, "ms"),
                        PerformanceMetric(f"{phase}_success_rate", len(times) / cycles * 100, "%")
                    ])
                    
                    # 检查是否超过阈值
                    if avg_time > self.baseline.lifecycle_phase_threshold:
                        all_phases_ok = False
                else:
                    metrics.append(PerformanceMetric(f"{phase}_success_rate", 0, "%"))
                    all_phases_ok = False
            
            duration = time.time() - start_time
            
            result = BenchmarkResult(
                benchmark_type=benchmark_type,
                success=all_phases_ok,
                duration=duration,
                metrics=metrics,
                metadata={
                    "cycles": cycles,
                    "plugin_path": plugin_path,
                    "phase_times": {k: v for k, v in phase_times.items()}
                }
            )
            
            self._results.append(result)
            return result
            
        except Exception as e:
            self._logger.error(f"插件生命周期基准测试失败: {e}")
            result = BenchmarkResult(
                benchmark_type=benchmark_type,
                success=False,
                duration=time.time() - start_time if 'start_time' in locals() else 0,
                error=str(e)
            )
            self._results.append(result)
            return result
            
        finally:
            self._running_benchmarks[benchmark_type.value] = False
    
    def run_memory_benchmark(self, plugin_paths: List[str], duration_seconds: int = 60) -> BenchmarkResult:
        """运行内存使用基准测试"""
        benchmark_type = BenchmarkType.MEMORY_USAGE
        self._running_benchmarks[benchmark_type.value] = True
        
        try:
            start_time = time.time()
            
            # 记录初始内存
            initial_memory = self._process.memory_info().rss
            memory_samples = []
            loaded_plugins = []
            
            # 加载插件
            for i, plugin_path in enumerate(plugin_paths):
                plugin_id = f"memory_test_plugin_{i}"
                if self._load_test_plugin(plugin_id, plugin_path):
                    self.plugin_manager.initialize_plugin(plugin_id)
                    self.plugin_manager.start_plugin(plugin_id)
                    loaded_plugins.append(plugin_id)
            
            # 监控内存使用
            end_time = start_time + duration_seconds
            while time.time() < end_time:
                current_memory = self._process.memory_info().rss
                memory_samples.append(current_memory)
                time.sleep(1)  # 每秒采样一次
            
            # 卸载一半插件测试内存释放
            unloaded_count = 0
            for i, plugin_id in enumerate(loaded_plugins):
                if i % 2 == 0:  # 卸载偶数索引的插件
                    self.plugin_manager.stop_plugin(plugin_id)
                    self.plugin_manager.unload_plugin(plugin_id)
                    unloaded_count += 1
            
            # 强制垃圾回收
            gc.collect()
            time.sleep(2)
            
            # 记录卸载后内存
            after_unload_memory = self._process.memory_info().rss
            
            # 计算内存统计
            if memory_samples:
                max_memory = max(memory_samples)
                avg_memory = statistics.mean(memory_samples)
                memory_increase = max_memory - initial_memory
                memory_per_plugin = memory_increase / len(loaded_plugins) if loaded_plugins else 0
                memory_freed = max_memory - after_unload_memory
                
                metrics = [
                    PerformanceMetric("initial_memory", initial_memory / 1024 / 1024, "MB"),
                    PerformanceMetric("max_memory", max_memory / 1024 / 1024, "MB"),
                    PerformanceMetric("avg_memory", avg_memory / 1024 / 1024, "MB"),
                    PerformanceMetric("memory_increase", memory_increase / 1024 / 1024, "MB"),
                    PerformanceMetric("memory_per_plugin", memory_per_plugin / 1024, "KB"),
                    PerformanceMetric("memory_freed", memory_freed / 1024 / 1024, "MB"),
                    PerformanceMetric("plugins_loaded", len(loaded_plugins), "count"),
                    PerformanceMetric("plugins_unloaded", unloaded_count, "count")
                ]
                
                # 检查内存使用是否合理
                memory_per_plugin_kb = memory_per_plugin / 1024
                success = memory_per_plugin_kb <= self.baseline.memory_per_plugin_threshold
                
                duration = time.time() - start_time
                
                result = BenchmarkResult(
                    benchmark_type=benchmark_type,
                    success=success,
                    duration=duration,
                    metrics=metrics,
                    metadata={
                        "monitor_duration": duration_seconds,
                        "memory_samples": len(memory_samples),
                        "plugin_paths": plugin_paths
                    }
                )
            else:
                result = BenchmarkResult(
                    benchmark_type=benchmark_type,
                    success=False,
                    duration=time.time() - start_time,
                    error="无法收集内存样本"
                )
            
            # 清理剩余插件
            for plugin_id in loaded_plugins:
                try:
                    self.plugin_manager.stop_plugin(plugin_id)
                    self.plugin_manager.unload_plugin(plugin_id)
                except:
                    pass
            
            self._results.append(result)
            return result
            
        except Exception as e:
            self._logger.error(f"内存基准测试失败: {e}")
            result = BenchmarkResult(
                benchmark_type=benchmark_type,
                success=False,
                duration=time.time() - start_time if 'start_time' in locals() else 0,
                error=str(e)
            )
            self._results.append(result)
            return result
            
        finally:
            self._running_benchmarks[benchmark_type.value] = False
    
    def _load_test_plugin(self, plugin_id: str, plugin_path: str) -> bool:
        """加载测试插件的辅助方法"""
        try:
            # 这里应该根据实际的插件加载方式来实现
            # 暂时使用模拟实现
            return self.plugin_manager.load_plugin_from_path(plugin_path, plugin_id)
        except Exception as e:
            self._logger.error(f"加载插件 {plugin_id} 失败: {e}")
            return False
    
    def _timed_plugin_load(self, plugin_id: str, plugin_path: str) -> Tuple[bool, float]:
        """计时的插件加载"""
        start_time = time.time()
        success = self._load_test_plugin(plugin_id, plugin_path)
        if success:
            success = self.plugin_manager.initialize_plugin(plugin_id)
            if success:
                success = self.plugin_manager.start_plugin(plugin_id)
        load_time = (time.time() - start_time) * 1000  # 转换为毫秒
        return success, load_time
    
    def get_results(self, benchmark_type: Optional[BenchmarkType] = None) -> List[BenchmarkResult]:
        """获取基准测试结果"""
        with self._lock:
            if benchmark_type:
                return [r for r in self._results if r.benchmark_type == benchmark_type]
            return self._results.copy()
    
    def clear_results(self):
        """清除基准测试结果"""
        with self._lock:
            self._results.clear()
    
    def is_running(self, benchmark_type: Optional[BenchmarkType] = None) -> bool:
        """检查是否有基准测试正在运行"""
        if benchmark_type:
            return self._running_benchmarks.get(benchmark_type.value, False)
        return any(self._running_benchmarks.values())
    
    def generate_report(self) -> Dict[str, Any]:
        """生成性能报告"""
        with self._lock:
            if not self._results:
                return {"error": "没有基准测试结果"}
            
            report = {
                "timestamp": time.time(),
                "baseline": self.baseline.to_dict(),
                "summary": {
                    "total_benchmarks": len(self._results),
                    "passed": sum(1 for r in self._results if r.success),
                    "failed": sum(1 for r in self._results if not r.success)
                },
                "results_by_type": {},
                "overall_status": "PASS"
            }
            
            # 按类型分组结果
            by_type = defaultdict(list)
            for result in self._results:
                by_type[result.benchmark_type.value].append(result)
            
            # 分析每种类型的结果
            for bench_type, results in by_type.items():
                type_summary = {
                    "count": len(results),
                    "passed": sum(1 for r in results if r.success),
                    "failed": sum(1 for r in results if not r.success),
                    "latest_result": results[-1].to_dict() if results else None
                }
                
                # 如果有失败的测试，标记整体状态为失败
                if type_summary["failed"] > 0:
                    report["overall_status"] = "FAIL"
                
                report["results_by_type"][bench_type] = type_summary
            
            return report


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, max_samples: int = 1000):
        self.max_samples = max_samples
        self._cpu_samples = deque(maxlen=max_samples)
        self._memory_samples = deque(maxlen=max_samples)
        self._plugin_count_samples = deque(maxlen=max_samples)
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._process = psutil.Process()
    
    def start_monitoring(self, interval: float = 1.0):
        """开始监控"""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """停止监控"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
    
    def _monitor_loop(self, interval: float):
        """监控循环"""
        while self._monitoring:
            try:
                # 采集CPU使用率
                cpu_percent = self._process.cpu_percent()
                self._cpu_samples.append((time.time(), cpu_percent))
                
                # 采集内存使用
                memory_info = self._process.memory_info()
                self._memory_samples.append((time.time(), memory_info.rss))
                
                time.sleep(interval)
                
            except Exception as e:
                # 忽略监控错误，避免影响主程序
                pass
    
    def get_current_stats(self) -> Dict[str, Any]:
        """获取当前统计信息"""
        try:
            cpu_percent = self._process.cpu_percent()
            memory_info = self._process.memory_info()
            
            return {
                "cpu_percent": cpu_percent,
                "memory_rss": memory_info.rss,
                "memory_vms": memory_info.vms,
                "timestamp": time.time()
            }
        except:
            return {}
    
    def get_historical_stats(self, minutes: int = 60) -> Dict[str, List[Tuple[float, float]]]:
        """获取历史统计信息"""
        cutoff_time = time.time() - (minutes * 60)
        
        recent_cpu = [(t, v) for t, v in self._cpu_samples if t >= cutoff_time]
        recent_memory = [(t, v) for t, v in self._memory_samples if t >= cutoff_time]
        
        return {
            "cpu_samples": recent_cpu,
            "memory_samples": recent_memory
        }


# 便捷函数
def create_benchmark_runner(plugin_manager: PluginManager, logger: Optional[logging.Logger] = None) -> PluginBenchmarkRunner:
    """创建基准测试运行器"""
    return PluginBenchmarkRunner(plugin_manager, logger)


def run_full_benchmark_suite(plugin_manager: PluginManager, test_plugins: List[str], 
                           logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
    """运行完整的基准测试套件"""
    runner = create_benchmark_runner(plugin_manager, logger)
    
    try:
        # 运行各种基准测试
        if test_plugins:
            # 单个插件加载测试
            runner.run_single_plugin_load_benchmark(test_plugins[0])
            
            # 并发加载测试
            runner.run_concurrent_load_benchmark(test_plugins[:50] if len(test_plugins) >= 50 else test_plugins * 10)
            
            # 生命周期测试
            runner.run_lifecycle_benchmark(test_plugins[0])
            
            # 内存测试
            runner.run_memory_benchmark(test_plugins[:10])
        
        # 生成报告
        return runner.generate_report()
        
    except Exception as e:
        if logger:
            logger.error(f"基准测试套件运行失败: {e}")
        return {"error": str(e)}